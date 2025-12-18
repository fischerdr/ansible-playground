#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Portworx Upgrade Team
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
filter: operator_version_filters
author: Portworx Upgrade Team
version_added: "1.0.0"
short_description: Semantic version parsing and comparison for operator upgrades
description:
  - Parse semantic version strings from ClusterServiceVersion names
  - Compare operator versions for sequential upgrade discovery
  - Filter and sort operator version candidates
  - Supports Portworx operator version format (portworx-operator.v25.5.0)
filters:
  parse_operator_version:
    description: Extract semantic version from CSV name
    options:
      _input:
        description: CSV name like "portworx-operator.v25.5.0"
        type: str
        required: true
      pattern:
        description: Optional custom regex pattern
        type: str
        required: false
  compare_versions:
    description: Compare two version tuples
    options:
      version1_tuple:
        description: First version as tuple (major, minor, patch)
        type: tuple
        required: true
      version2_tuple:
        description: Second version as tuple (major, minor, patch)
        type: tuple
        required: true
  filter_greater_versions:
    description: Filter candidates greater than current version
    options:
      candidates:
        description: List of dicts with 'version_tuple' key
        type: list
        required: true
      current_version_tuple:
        description: Current version as tuple
        type: tuple
        required: true
  sort_versions:
    description: Sort candidates by version_tuple ascending
    options:
      candidates:
        description: List of dicts with 'version_tuple' key
        type: list
        required: true
  calculate_upgrade_path_length:
    description: Calculate number of versions in upgrade path
    options:
      candidates:
        description: List of dicts with 'version_tuple' key
        type: list
        required: true
      current_version_tuple:
        description: Current version as tuple
        type: tuple
        required: true
      target_version_tuple:
        description: Target version as tuple
        type: tuple
        required: true
      max_skew:
        description: Maximum allowed version skew (default 10)
        type: int
        required: false
notes:
  - All filters perform type validation before processing
  - Filters raise AnsibleFilterError for invalid input
  - Version skew validation prevents unsafe multi-version jumps
  - Based on docs/examples/filter_plugin_example.py structure
"""

EXAMPLES = r"""
# Parse operator version from CSV name
- name: Parse current operator version
  set_fact:
    current_version: "{{ current_csv.metadata.name | parse_operator_version }}"
  # Returns: {'major': 25, 'minor': 5, 'patch': 0, 'tuple': (25, 5, 0), 'string': '25.5.0'}

# Compare two versions
- name: Check if version1 is less than version2
  set_fact:
    is_older: "{{ version1_tuple | compare_versions(version2_tuple) == -1 }}"

# Filter candidates greater than current
- name: Get upgrade candidates
  set_fact:
    valid_candidates: "{{ all_candidates | filter_greater_versions(current_version_tuple) }}"

# Sort candidates by version
- name: Sort and select next candidate
  set_fact:
    next_candidate: "{{ valid_candidates | sort_versions | first }}"

# Chained operations for sequential upgrade discovery
- name: Discover next upgrade step
  set_fact:
    next_step: >-
      {{
        installplan_candidates
        | filter_greater_versions(current_tuple)
        | sort_versions
        | first
        | default({})
      }}

# Calculate upgrade path length and validate skew
- name: Validate version skew
  set_fact:
    path_length: >-
      {{
        all_candidates
        | calculate_upgrade_path_length(current_tuple, target_tuple, 10)
      }}
  # Raises error if path requires more than 10 version steps
"""

RETURN = r"""
_value:
  description: The parsed, filtered, or sorted value
  type: any
  returned: always
"""

import re

from ansible.errors import AnsibleFilterError


class FilterModule(object):
    """Ansible filter plugin for operator version operations"""

    def filters(self):
        """
        Return filter mapping dictionary

        Returns:
            dict: Mapping of filter names to methods
        """
        return {
            "parse_operator_version": self.parse_operator_version,
            "compare_versions": self.compare_versions,
            "filter_greater_versions": self.filter_greater_versions,
            "sort_versions": self.sort_versions,
            "calculate_upgrade_path_length": self.calculate_upgrade_path_length,
        }

    @staticmethod
    def parse_operator_version(csv_name, pattern=r"v?([0-9]+)\.([0-9]+)\.([0-9]+)"):
        """
        Parse operator version from CSV name

        Args:
            csv_name: CSV name like "portworx-operator.v25.5.0"
            pattern: Optional custom regex pattern for version extraction

        Returns:
            dict: {
                'major': int - Major version number
                'minor': int - Minor version number
                'patch': int - Patch version number
                'tuple': tuple - (major, minor, patch) for comparison
                'string': str - "major.minor.patch" string representation
            }

        Raises:
            AnsibleFilterError: If input is not a string or version cannot be parsed

        Examples:
            >>> parse_operator_version("portworx-operator.v25.5.0")
            {'major': 25, 'minor': 5, 'patch': 0, 'tuple': (25, 5, 0), 'string': '25.5.0'}
        """
        if not isinstance(csv_name, str):
            raise AnsibleFilterError(
                f"parse_operator_version requires a string, got {type(csv_name).__name__}"
            )

        try:
            match = re.search(pattern, csv_name)
            if not match or len(match.groups()) != 3:
                raise AnsibleFilterError(
                    f"Cannot parse semantic version from CSV name: {csv_name}"
                )

            major = int(match.group(1))
            minor = int(match.group(2))
            patch = int(match.group(3))

            return {
                "major": major,
                "minor": minor,
                "patch": patch,
                "tuple": (major, minor, patch),
                "string": f"{major}.{minor}.{patch}",
            }
        except ValueError as e:
            raise AnsibleFilterError(
                f"Error parsing version numbers from {csv_name}: {str(e)}"
            )
        except Exception as e:
            raise AnsibleFilterError(
                f"Unexpected error parsing version from {csv_name}: {str(e)}"
            )

    @staticmethod
    def compare_versions(version1_tuple, version2_tuple):
        """
        Compare two version tuples

        Args:
            version1_tuple: First version as tuple (major, minor, patch)
            version2_tuple: Second version as tuple (major, minor, patch)

        Returns:
            int: -1 if version1 < version2, 0 if equal, 1 if version1 > version2

        Raises:
            AnsibleFilterError: If inputs are not tuples

        Examples:
            >>> compare_versions((23, 10, 3), (25, 5, 0))
            -1
            >>> compare_versions((25, 5, 0), (25, 5, 0))
            0
            >>> compare_versions((25, 5, 0), (24, 2, 1))
            1
        """
        if not isinstance(version1_tuple, tuple) or not isinstance(
            version2_tuple, tuple
        ):
            raise AnsibleFilterError(
                "compare_versions requires both arguments to be tuples"
            )

        try:
            if version1_tuple < version2_tuple:
                return -1
            elif version1_tuple > version2_tuple:
                return 1
            return 0
        except Exception as e:
            raise AnsibleFilterError(f"Error comparing versions: {str(e)}")

    @staticmethod
    def filter_greater_versions(candidates, current_version_tuple):
        """
        Filter candidates to only those greater than current version

        Args:
            candidates: List of dicts with 'version_tuple' key
            current_version_tuple: Current version as tuple (major, minor, patch)

        Returns:
            list: Filtered candidates with version > current

        Raises:
            AnsibleFilterError: If candidates is not a list or current_version_tuple is not a tuple

        Examples:
            >>> candidates = [
            ...     {'csv_name': 'v23.10.3', 'version_tuple': (23, 10, 3)},
            ...     {'csv_name': 'v25.5.0', 'version_tuple': (25, 5, 0)},
            ... ]
            >>> filter_greater_versions(candidates, (24, 1, 0))
            [{'csv_name': 'v25.5.0', 'version_tuple': (25, 5, 0)}]
        """
        if not isinstance(candidates, list):
            raise AnsibleFilterError(
                f"filter_greater_versions requires a list, got {type(candidates).__name__}"
            )

        if not isinstance(current_version_tuple, tuple):
            raise AnsibleFilterError(
                f"current_version_tuple must be a tuple, got {type(current_version_tuple).__name__}"
            )

        try:
            return [
                c
                for c in candidates
                if c.get("version_tuple", (0, 0, 0)) > current_version_tuple
            ]
        except Exception as e:
            raise AnsibleFilterError(f"Error filtering versions: {str(e)}")

    @staticmethod
    def sort_versions(candidates):
        """
        Sort candidates by version_tuple in ascending order

        Args:
            candidates: List of dicts with 'version_tuple' key

        Returns:
            list: Sorted list of candidates (ascending by version)

        Raises:
            AnsibleFilterError: If candidates is not a list

        Examples:
            >>> candidates = [
            ...     {'csv_name': 'v25.5.0', 'version_tuple': (25, 5, 0)},
            ...     {'csv_name': 'v23.10.3', 'version_tuple': (23, 10, 3)},
            ... ]
            >>> sort_versions(candidates)
            [{'csv_name': 'v23.10.3', ...}, {'csv_name': 'v25.5.0', ...}]
        """
        if not isinstance(candidates, list):
            raise AnsibleFilterError(
                f"sort_versions requires a list, got {type(candidates).__name__}"
            )

        try:
            return sorted(candidates, key=lambda x: x.get("version_tuple", (0, 0, 0)))
        except Exception as e:
            raise AnsibleFilterError(f"Error sorting versions: {str(e)}")

    @staticmethod
    def calculate_upgrade_path_length(
        candidates, current_version_tuple, target_version_tuple, max_skew=10
    ):
        """
        Calculate upgrade path length and validate version skew

        Filters candidates between current and target versions, then counts
        the number of intermediate steps required. Raises an error if the
        path exceeds the maximum allowed version skew.

        Args:
            candidates: List of dicts with 'version_tuple' key
            current_version_tuple: Current version as tuple (major, minor, patch)
            target_version_tuple: Target version as tuple (major, minor, patch)
            max_skew: Maximum allowed version steps (default: 10)

        Returns:
            int: Number of upgrade steps required (including target)

        Raises:
            AnsibleFilterError: If path length exceeds max_skew or invalid inputs

        Examples:
            >>> candidates = [
            ...     {'version_tuple': (23, 10, 3)},
            ...     {'version_tuple': (24, 1, 0)},
            ...     {'version_tuple': (24, 2, 1)},
            ...     {'version_tuple': (25, 5, 0)},
            ... ]
            >>> calculate_upgrade_path_length(candidates, (23, 10, 3), (25, 5, 0), 10)
            3  # Three steps: 24.1.0 -> 24.2.1 -> 25.5.0
        """
        if not isinstance(candidates, list):
            raise AnsibleFilterError(
                f"calculate_upgrade_path_length requires a list, got {type(candidates).__name__}"
            )

        if not isinstance(current_version_tuple, tuple):
            raise AnsibleFilterError(
                f"current_version_tuple must be a tuple, got {type(current_version_tuple).__name__}"
            )

        if not isinstance(target_version_tuple, tuple):
            raise AnsibleFilterError(
                f"target_version_tuple must be a tuple, got {type(target_version_tuple).__name__}"
            )

        if not isinstance(max_skew, int) or max_skew < 1:
            raise AnsibleFilterError(
                f"max_skew must be a positive integer, got {max_skew}"
            )

        try:
            # Filter candidates between current and target (exclusive of current)
            upgrade_path = [
                c
                for c in candidates
                if current_version_tuple
                < c.get("version_tuple", (0, 0, 0))
                <= target_version_tuple
            ]

            # Sort by version to get sequential path
            upgrade_path = sorted(
                upgrade_path, key=lambda x: x.get("version_tuple", (0, 0, 0))
            )

            path_length = len(upgrade_path)

            # Validate version skew
            if path_length > max_skew:
                current_str = ".".join(map(str, current_version_tuple))
                target_str = ".".join(map(str, target_version_tuple))
                raise AnsibleFilterError(
                    f"Version skew too large: upgrade from {current_str} to {target_str} "
                    f"requires {path_length} steps, but maximum allowed is {max_skew}. "
                    f"This upgrade path is too long and may be unsafe. "
                    f"Consider upgrading in smaller increments or verify the target version is correct."
                )

            return path_length

        except AnsibleFilterError:
            # Re-raise our own errors
            raise
        except Exception as e:
            raise AnsibleFilterError(f"Error calculating upgrade path length: {str(e)}")


# Standalone testing (for development/debugging)
if __name__ == "__main__":
    # This section is for testing the filters outside of Ansible
    filters = FilterModule()

    # Test parse_operator_version
    print("Testing parse_operator_version:")
    result = filters.parse_operator_version("portworx-operator.v25.5.0")
    print(f"  portworx-operator.v25.5.0 -> {result}")

    result = filters.parse_operator_version("portworx-operator.v23.10.3")
    print(f"  portworx-operator.v23.10.3 -> {result}")

    # Test compare_versions
    print("\nTesting compare_versions:")
    result = filters.compare_versions((23, 10, 3), (25, 5, 0))
    print(f"  (23, 10, 3) vs (25, 5, 0) -> {result} (expected: -1)")

    result = filters.compare_versions((25, 5, 0), (24, 2, 1))
    print(f"  (25, 5, 0) vs (24, 2, 1) -> {result} (expected: 1)")

    # Test filter_greater_versions
    print("\nTesting filter_greater_versions:")
    candidates = [
        {"csv_name": "v23.10.3", "version_tuple": (23, 10, 3)},
        {"csv_name": "v24.1.0", "version_tuple": (24, 1, 0)},
        {"csv_name": "v25.5.0", "version_tuple": (25, 5, 0)},
    ]
    result = filters.filter_greater_versions(candidates, (24, 1, 0))
    print(f"  Filtered > (24, 1, 0): {[c['csv_name'] for c in result]}")

    # Test sort_versions
    print("\nTesting sort_versions:")
    unsorted = [
        {"csv_name": "v25.5.0", "version_tuple": (25, 5, 0)},
        {"csv_name": "v23.10.3", "version_tuple": (23, 10, 3)},
        {"csv_name": "v24.1.0", "version_tuple": (24, 1, 0)},
    ]
    result = filters.sort_versions(unsorted)
    print(f"  Sorted: {[c['csv_name'] for c in result]}")

    # Test calculate_upgrade_path_length
    print("\nTesting calculate_upgrade_path_length:")
    all_candidates = [
        {"csv_name": "v23.10.3", "version_tuple": (23, 10, 3)},
        {"csv_name": "v24.1.0", "version_tuple": (24, 1, 0)},
        {"csv_name": "v24.2.1", "version_tuple": (24, 2, 1)},
        {"csv_name": "v25.5.0", "version_tuple": (25, 5, 0)},
    ]

    # Test valid path (3 steps from 23.10.3 to 25.5.0)
    result = filters.calculate_upgrade_path_length(
        all_candidates, (23, 10, 3), (25, 5, 0), 10
    )
    print(f"  Path length from 23.10.3 to 25.5.0: {result} steps (expected: 3)")

    # Test path with 5 steps (should pass with max_skew=10)
    extended_candidates = all_candidates + [
        {"csv_name": "v24.3.0", "version_tuple": (24, 3, 0)},
        {"csv_name": "v24.4.0", "version_tuple": (24, 4, 0)},
    ]
    result = filters.calculate_upgrade_path_length(
        extended_candidates, (23, 10, 3), (25, 5, 0), 10
    )
    print(f"  Path length with 5 steps: {result} (expected: 5)")

    # Test version skew validation failure (should raise error)
    print("\nTesting version skew validation (expecting error):")
    many_candidates = [{"version_tuple": (24, i, 0)} for i in range(15)]
    try:
        result = filters.calculate_upgrade_path_length(
            many_candidates, (24, 0, 0), (24, 14, 0), 10
        )
        print(f"  ERROR: Should have raised AnsibleFilterError but got: {result}")
    except Exception as e:
        print(f"  ✓ Correctly raised error: {str(e)[:80]}...")
