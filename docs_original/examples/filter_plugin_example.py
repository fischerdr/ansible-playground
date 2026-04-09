#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Your Name <your.email@example.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
filter: data_transformation_filters
author: Your Name (@github_handle)
version_added: "1.0.0"
short_description: Custom data transformation filters for Ansible
description:
  - Provides multiple filter functions for data manipulation
  - Handles string processing, list filtering, and dictionary transformations
  - Implements recursive operations for nested data structures
  - Includes comprehensive type validation and error handling
filters:
  extract_field:
    description: Extract a specific field from a list of dictionaries
    options:
      _input:
        description: List of dictionaries to process
        type: list
        required: true
      field:
        description: Field name to extract
        type: str
        required: true
  filter_by_status:
    description: Filter list of items by status field
    options:
      _input:
        description: List of items to filter
        type: list
        required: true
      status:
        description: Status value to filter by
        type: str
        required: true
  transform_keys:
    description: Transform dictionary keys using a mapping
    options:
      _input:
        description: Dictionary to transform
        type: dict
        required: true
      key_map:
        description: Mapping of old keys to new keys
        type: dict
        required: false
  normalize_list:
    description: Normalize and deduplicate a list
    options:
      _input:
        description: List to normalize
        type: list
        required: true
  deep_merge:
    description: Recursively merge two dictionaries
    options:
      _input:
        description: Base dictionary
        type: dict
        required: true
      other:
        description: Dictionary to merge into base
        type: dict
        required: true
notes:
  - All filters perform type validation before processing
  - Filters raise AnsibleFilterError for invalid input
  - Use for data transformation in playbooks and roles
seealso:
  - name: Ansible Filter Plugins
    link: https://docs.ansible.com/ansible/latest/dev_guide/developing_plugins.html#filter-plugins
"""

EXAMPLES = r"""
# Extract field from list of dictionaries
- name: Extract pod names from pod list
  debug:
    msg: "{{ pods | extract_field('name') }}"
  vars:
    pods:
      - name: pod-1
        status: Running
      - name: pod-2
        status: Pending

# Filter list by status
- name: Get only running pods
  debug:
    msg: "{{ pods | filter_by_status('Running') }}"
  vars:
    pods:
      - name: pod-1
        status: Running
      - name: pod-2
        status: Pending
      - name: pod-3
        status: Running

# Transform dictionary keys
- name: Rename configuration keys
  debug:
    msg: "{{ config | transform_keys(key_mapping) }}"
  vars:
    config:
      old_name: value1
      old_port: 8080
    key_mapping:
      old_name: new_name
      old_port: new_port

# Normalize and deduplicate list
- name: Clean up list
  debug:
    msg: "{{ items | normalize_list }}"
  vars:
    items:
      - apple
      - banana
      - apple
      - cherry
      - banana

# Deep merge dictionaries
- name: Merge configurations
  debug:
    msg: "{{ base_config | deep_merge(override_config) }}"
  vars:
    base_config:
      database:
        host: localhost
        port: 5432
      cache:
        enabled: true
    override_config:
      database:
        port: 3306
      logging:
        level: debug

# Chained filter operations
- name: Complex transformation
  set_fact:
    result: "{{ pods | filter_by_status('Running') | extract_field('name') | normalize_list }}"
  vars:
    pods:
      - name: pod-1
        status: Running
      - name: pod-2
        status: Pending
      - name: pod-1
        status: Running

# Error handling example
- name: Safe filter usage with validation
  block:
    - name: Apply filter with error checking
      set_fact:
        extracted: "{{ data | extract_field('field_name') }}"
  rescue:
    - name: Handle filter error
      debug:
        msg: "Filter failed - check input data format"
"""

RETURN = r"""
_value:
  description: The filtered/transformed value
  type: any
  returned: always
"""

from ansible.errors import AnsibleFilterError


class FilterModule(object):
    """Ansible filter plugin for data transformation operations"""

    def filters(self):
        """
        Return filter mapping dictionary

        Returns:
            dict: Mapping of filter names to methods
        """
        return {
            "extract_field": self.extract_field,
            "filter_by_status": self.filter_by_status,
            "transform_keys": self.transform_keys,
            "normalize_list": self.normalize_list,
            "deep_merge": self.deep_merge,
            "safe_get": self.safe_get,
            "to_key_value_pairs": self.to_key_value_pairs,
        }

    @staticmethod
    def extract_field(value, field):
        """
        Extract a specific field from a list of dictionaries

        Args:
            value: List of dictionaries to process
            field: Field name to extract

        Returns:
            list: List of extracted field values

        Raises:
            AnsibleFilterError: If input is not a list or items are not dicts
        """
        if not isinstance(value, (list, tuple)):
            raise AnsibleFilterError(
                f"extract_field requires a list, got {type(value).__name__}"
            )

        if not field:
            raise AnsibleFilterError("extract_field requires a field name")

        result = []
        for item in value:
            if not isinstance(item, dict):
                raise AnsibleFilterError(
                    f"extract_field requires list of dicts, found {type(item).__name__}"
                )

            if field in item:
                result.append(item[field])

        return result

    @staticmethod
    def filter_by_status(value, status):
        """
        Filter list of items by status field

        Args:
            value: List of dictionaries with status field
            status: Status value to filter by

        Returns:
            list: Filtered list of items

        Raises:
            AnsibleFilterError: If input is not a list or status is missing
        """
        if not isinstance(value, (list, tuple)):
            raise AnsibleFilterError(
                f"filter_by_status requires a list, got {type(value).__name__}"
            )

        if not status:
            raise AnsibleFilterError("filter_by_status requires a status value")

        try:
            return [
                item
                for item in value
                if isinstance(item, dict) and item.get("status") == status
            ]
        except Exception as e:
            raise AnsibleFilterError(f"Error filtering by status: {str(e)}")

    @staticmethod
    def transform_keys(value, key_map=None):
        """
        Transform dictionary keys using a mapping

        Args:
            value: Dictionary to transform
            key_map: Optional mapping of old keys to new keys

        Returns:
            dict: Dictionary with transformed keys

        Raises:
            AnsibleFilterError: If input is not a dict
        """
        if not isinstance(value, dict):
            raise AnsibleFilterError(
                f"transform_keys requires a dict, got {type(value).__name__}"
            )

        key_map = key_map or {}

        if not isinstance(key_map, dict):
            raise AnsibleFilterError(
                f"key_map must be a dict, got {type(key_map).__name__}"
            )

        try:
            return {key_map.get(k, k): v for k, v in value.items()}
        except Exception as e:
            raise AnsibleFilterError(f"Error transforming keys: {str(e)}")

    @staticmethod
    def normalize_list(value):
        """
        Normalize and deduplicate a list while preserving order

        Args:
            value: List to normalize

        Returns:
            list: Normalized list with duplicates removed

        Raises:
            AnsibleFilterError: If input is not a list
        """
        if not isinstance(value, (list, tuple)):
            raise AnsibleFilterError(
                f"normalize_list requires a list, got {type(value).__name__}"
            )

        try:
            # Preserve order while removing duplicates
            seen = set()
            result = []
            for item in value:
                # Handle unhashable types
                try:
                    if item not in seen:
                        seen.add(item)
                        result.append(item)
                except TypeError:
                    # For unhashable types (like dicts), just append
                    if item not in result:
                        result.append(item)

            return result
        except Exception as e:
            raise AnsibleFilterError(f"Error normalizing list: {str(e)}")

    def deep_merge(self, value, other):
        """
        Recursively merge two dictionaries

        Args:
            value: Base dictionary
            other: Dictionary to merge into base

        Returns:
            dict: Merged dictionary

        Raises:
            AnsibleFilterError: If inputs are not dicts
        """
        if not isinstance(value, dict):
            raise AnsibleFilterError(
                f"deep_merge requires a dict, got {type(value).__name__}"
            )

        if not isinstance(other, dict):
            raise AnsibleFilterError(
                f"deep_merge second argument must be a dict, got {type(other).__name__}"
            )

        try:
            result = value.copy()

            for key, value_other in other.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value_other, dict)
                ):
                    # Recursively merge nested dicts
                    result[key] = self.deep_merge(result[key], value_other)
                else:
                    # Overwrite with new value
                    result[key] = value_other

            return result
        except Exception as e:
            raise AnsibleFilterError(f"Error in deep_merge: {str(e)}")

    @staticmethod
    def safe_get(value, path, default=None):
        """
        Safely get a value from nested dict using dot notation

        Args:
            value: Dictionary to query
            path: Dot-separated path (e.g., 'a.b.c')
            default: Default value if path not found

        Returns:
            any: Value at path or default

        Raises:
            AnsibleFilterError: If input is not a dict
        """
        if not isinstance(value, dict):
            raise AnsibleFilterError(
                f"safe_get requires a dict, got {type(value).__name__}"
            )

        if not isinstance(path, str):
            raise AnsibleFilterError(
                f"safe_get path must be a string, got {type(path).__name__}"
            )

        try:
            keys = path.split(".")
            result = value

            for key in keys:
                if isinstance(result, dict):
                    result = result.get(key)
                    if result is None:
                        return default
                else:
                    return default

            return result if result is not None else default
        except Exception as e:
            raise AnsibleFilterError(f"Error in safe_get: {str(e)}")

    @staticmethod
    def to_key_value_pairs(value, key_name="key", value_name="value"):
        """
        Convert dictionary to list of key-value pair dictionaries

        Args:
            value: Dictionary to convert
            key_name: Name for key field in output
            value_name: Name for value field in output

        Returns:
            list: List of dictionaries with key-value pairs

        Raises:
            AnsibleFilterError: If input is not a dict
        """
        if not isinstance(value, dict):
            raise AnsibleFilterError(
                f"to_key_value_pairs requires a dict, got {type(value).__name__}"
            )

        try:
            return [{key_name: k, value_name: v} for k, v in value.items()]
        except Exception as e:
            raise AnsibleFilterError(f"Error converting to key-value pairs: {str(e)}")


# Example usage in Python (for testing)
if __name__ == "__main__":
    # This section is for testing the filters outside of Ansible
    filters = FilterModule()

    # Test extract_field
    pods = [
        {"name": "pod-1", "status": "Running"},
        {"name": "pod-2", "status": "Pending"},
        {"name": "pod-3", "status": "Running"},
    ]
    print("Extract field:", filters.extract_field(pods, "name"))

    # Test filter_by_status
    print("Filter by status:", filters.filter_by_status(pods, "Running"))

    # Test transform_keys
    config = {"old_name": "value1", "old_port": 8080}
    key_map = {"old_name": "new_name", "old_port": "new_port"}
    print("Transform keys:", filters.transform_keys(config, key_map))

    # Test normalize_list
    items = ["apple", "banana", "apple", "cherry", "banana"]
    print("Normalize list:", filters.normalize_list(items))

    # Test deep_merge
    base = {"a": {"b": 1, "c": 2}, "d": 3}
    override = {"a": {"c": 3, "e": 4}, "f": 5}
    print("Deep merge:", filters.deep_merge(base, override))

    # Test safe_get
    data = {"a": {"b": {"c": "value"}}}
    print("Safe get:", filters.safe_get(data, "a.b.c"))
    print("Safe get (missing):", filters.safe_get(data, "a.x.y", "default"))

    # Test to_key_value_pairs
    settings = {"timeout": 30, "retries": 3}
    print("To key-value pairs:", filters.to_key_value_pairs(settings))
