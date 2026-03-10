#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, MasterControl <your.email@example.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
filter: example_filters
author: MasterControl (@yourgithub)
version_added: "1.0.0"
short_description: Example filter plugins demonstrating best practices
description:
  - Collection of example filters following enterprise Ansible standards
  - Demonstrates proper error handling, type validation, and documentation
  - Suitable for Ansible Automation Platform execution environments
options:
  _input:
    description: The input value to filter
    type: any
    required: true
notes:
  - All filters validate input types before processing
  - Filters raise AnsibleFilterError for invalid inputs or processing errors
  - Designed for use in AAP with Ansible Core 2.18.4
seealso:
  - module: ansible.builtin.set_fact
  - module: ansible.builtin.debug
"""

EXAMPLES = r"""
# String manipulation
- name: Sanitize cluster name for use in resource labels
  debug:
    msg: "{{ cluster_name | sanitize_k8s_label }}"

# List operations
- name: Extract node names from node status list
  debug:
    msg: "{{ node_list | extract_attribute('metadata.name') }}"

# Dictionary operations
- name: Merge default and custom configuration
  set_fact:
    final_config: "{{ default_config | safe_merge(custom_config) }}"

# Kubernetes resource processing
- name: Get container image from pod spec
  debug:
    msg: "{{ pod_spec | extract_container_image(0) }}"

# Data validation
- name: Validate version string format
  debug:
    msg: "{{ version_string | validate_semver }}"
"""

RETURN = r"""
_value:
  description: The filtered/transformed value
  type: any
  returned: always
"""

import re
from ansible.errors import AnsibleFilterError
from ansible.module_utils.common._collections_compat import Mapping, Sequence


class FilterModule(object):
    """Ansible filter plugin class for example filters"""

    def filters(self):
        """
        Return filter mapping dictionary

        Returns:
            dict: Mapping of filter names to filter methods
        """
        return {
            "sanitize_k8s_label": self.sanitize_k8s_label,
            "extract_attribute": self.extract_attribute,
            "safe_merge": self.safe_merge,
            "extract_container_image": self.extract_container_image,
            "validate_semver": self.validate_semver,
            "flatten_dict": self.flatten_dict,
            "chunk_list": self.chunk_list,
        }

    @staticmethod
    def sanitize_k8s_label(value, max_length=63):
        """
        Sanitize string for use as Kubernetes label or annotation

        Kubernetes labels must:
        - Start and end with alphanumeric character
        - Contain only alphanumeric, dash, underscore, or dot
        - Be 63 characters or less

        Args:
            value (str): Input string to sanitize
            max_length (int): Maximum length (default 63 for k8s labels)

        Returns:
            str: Sanitized string suitable for k8s label/annotation

        Raises:
            AnsibleFilterError: If value is not a string
        """
        if not isinstance(value, str):
            raise AnsibleFilterError(
                f"sanitize_k8s_label requires string, got {type(value).__name__}"
            )

        if not value:
            raise AnsibleFilterError("sanitize_k8s_label requires non-empty string")

        # Replace invalid characters with dash
        sanitized = re.sub(r"[^a-zA-Z0-9._-]", "-", value)

        # Ensure starts and ends with alphanumeric
        sanitized = re.sub(r"^[^a-zA-Z0-9]+", "", sanitized)
        sanitized = re.sub(r"[^a-zA-Z0-9]+$", "", sanitized)

        # Truncate to max length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
            # Re-check ending after truncation
            sanitized = re.sub(r"[^a-zA-Z0-9]+$", "", sanitized)

        if not sanitized:
            raise AnsibleFilterError(
                f"sanitize_k8s_label produced empty result from '{value}'"
            )

        return sanitized

    @staticmethod
    def extract_attribute(value, path, default=None):
        """
        Extract nested attribute from list of dictionaries using dot notation

        Similar to jq's map operation: .[] | .metadata.name

        Args:
            value (list): List of dictionaries to process
            path (str): Dot-separated attribute path (e.g., 'metadata.name')
            default: Default value if attribute not found (default None)

        Returns:
            list: List of extracted attribute values

        Raises:
            AnsibleFilterError: If value is not a list or path is invalid
        """
        if not isinstance(value, (list, tuple)):
            raise AnsibleFilterError(
                f"extract_attribute requires list, got {type(value).__name__}"
            )

        if not isinstance(path, str):
            raise AnsibleFilterError(
                f"extract_attribute path must be string, got {type(path).__name__}"
            )

        result = []
        path_parts = path.split(".")

        for item in value:
            current = item
            try:
                for part in path_parts:
                    if isinstance(current, dict):
                        current = current[part]
                    elif isinstance(current, (list, tuple)):
                        current = current[int(part)]
                    else:
                        current = default
                        break
                result.append(current)
            except (KeyError, IndexError, ValueError, TypeError):
                result.append(default)

        return result

    def safe_merge(self, base_dict, merge_dict, overwrite=True):
        """
        Safely merge two dictionaries with deep merge support

        Unlike dict update(), this preserves nested dictionaries unless overwrite=False

        Args:
            base_dict (dict): Base dictionary
            merge_dict (dict): Dictionary to merge into base
            overwrite (bool): Whether to overwrite existing values (default True)

        Returns:
            dict: Merged dictionary (new object, inputs unchanged)

        Raises:
            AnsibleFilterError: If inputs are not dictionaries
        """
        if not isinstance(base_dict, dict):
            raise AnsibleFilterError(
                f"safe_merge base must be dict, got {type(base_dict).__name__}"
            )

        if not isinstance(merge_dict, dict):
            raise AnsibleFilterError(
                f"safe_merge merge must be dict, got {type(merge_dict).__name__}"
            )

        result = base_dict.copy()

        for key, value in merge_dict.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursive merge for nested dicts
                result[key] = self.safe_merge(result[key], value, overwrite)
            elif key not in result or overwrite:
                result[key] = value

        return result

    @staticmethod
    def extract_container_image(pod_spec, container_index=0):
        """
        Extract container image from Kubernetes pod spec

        Handles both pod specs and full pod resource definitions

        Args:
            pod_spec (dict): Kubernetes pod specification or full pod resource
            container_index (int): Index of container to extract (default 0)

        Returns:
            str: Container image string (e.g., 'registry/image:tag')

        Raises:
            AnsibleFilterError: If pod_spec is invalid or container not found
        """
        if not isinstance(pod_spec, dict):
            raise AnsibleFilterError(
                f"extract_container_image requires dict, got {type(pod_spec).__name__}"
            )

        # Handle full pod resource (has 'spec' key) vs bare pod spec
        if "spec" in pod_spec:
            spec = pod_spec["spec"]
        else:
            spec = pod_spec

        # Validate spec structure
        if not isinstance(spec, dict):
            raise AnsibleFilterError("Invalid pod spec: 'spec' is not a dictionary")

        if "containers" not in spec:
            raise AnsibleFilterError("Invalid pod spec: missing 'containers' field")

        containers = spec["containers"]
        if not isinstance(containers, list):
            raise AnsibleFilterError("Invalid pod spec: 'containers' is not a list")

        if not containers:
            raise AnsibleFilterError("Invalid pod spec: 'containers' list is empty")

        if container_index >= len(containers):
            raise AnsibleFilterError(
                f"Container index {container_index} out of range "
                f"(pod has {len(containers)} containers)"
            )

        container = containers[container_index]
        if "image" not in container:
            raise AnsibleFilterError(
                f"Container at index {container_index} missing 'image' field"
            )

        return container["image"]

    @staticmethod
    def validate_semver(value, strict=True):
        """
        Validate semantic version string format

        Args:
            value (str): Version string to validate
            strict (bool): Require strict semver (default True)

        Returns:
            dict: Parsed version components {major, minor, patch, prerelease, build}

        Raises:
            AnsibleFilterError: If version string is invalid
        """
        if not isinstance(value, str):
            raise AnsibleFilterError(
                f"validate_semver requires string, got {type(value).__name__}"
            )

        # Strict semver: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
        if strict:
            pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
        else:
            # Relaxed: just MAJOR.MINOR.PATCH
            pattern = r"^(\d+)\.(\d+)\.(\d+)"

        match = re.match(pattern, value)
        if not match:
            raise AnsibleFilterError(
                f"Invalid semantic version '{value}' "
                f"(expected format: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD])"
            )

        groups = match.groups()
        return {
            "major": int(groups[0]),
            "minor": int(groups[1]),
            "patch": int(groups[2]),
            "prerelease": groups[3] if len(groups) > 3 else None,
            "build": groups[4] if len(groups) > 4 else None,
        }

    def flatten_dict(self, value, separator="_", parent_key=""):
        """
        Flatten nested dictionary into single-level dictionary

        Args:
            value (dict): Nested dictionary to flatten
            separator (str): Separator for flattened keys (default '_')
            parent_key (str): Parent key prefix (used in recursion)

        Returns:
            dict: Flattened dictionary

        Raises:
            AnsibleFilterError: If value is not a dictionary
        """
        if not isinstance(value, dict):
            raise AnsibleFilterError(
                f"flatten_dict requires dict, got {type(value).__name__}"
            )

        items = []
        for k, v in value.items():
            new_key = f"{parent_key}{separator}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, separator, new_key).items())
            else:
                items.append((new_key, v))

        return dict(items)

    @staticmethod
    def chunk_list(value, size):
        """
        Split list into chunks of specified size

        Useful for batch processing operations in AAP workflows

        Args:
            value (list): List to chunk
            size (int): Chunk size (must be positive)

        Returns:
            list: List of chunked sublists

        Raises:
            AnsibleFilterError: If value is not a list or size is invalid
        """
        if not isinstance(value, (list, tuple)):
            raise AnsibleFilterError(
                f"chunk_list requires list, got {type(value).__name__}"
            )

        if not isinstance(size, int) or size < 1:
            raise AnsibleFilterError(
                f"chunk_list size must be positive integer, got {size}"
            )

        return [value[i : i + size] for i in range(0, len(value), size)]
