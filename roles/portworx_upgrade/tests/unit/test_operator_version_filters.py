#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import pytest

# Add filter plugin directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../filter_plugins"))

from ansible.errors import AnsibleFilterError
from operator_version import FilterModule


class TestParseOperatorVersion:
    """Test parse_operator_version filter"""

    def setup_method(self):
        self.filters = FilterModule()
        self.parse = self.filters.filters()["parse_operator_version"]

    def test_parse_standard_csv_name(self):
        """Test parsing standard Portworx operator CSV name"""
        result = self.parse("portworx-operator.v25.5.0")
        assert result["major"] == 25
        assert result["minor"] == 5
        assert result["patch"] == 0
        assert result["tuple"] == (25, 5, 0)
        assert result["string"] == "25.5.0"

    def test_parse_with_prefix_v(self):
        """Test parsing version with v prefix"""
        result = self.parse("portworx-operator.v23.10.3")
        assert result["tuple"] == (23, 10, 3)
        assert result["string"] == "23.10.3"

    def test_parse_without_prefix(self):
        """Test parsing version without v prefix"""
        result = self.parse("portworx-operator.24.2.1")
        assert result["tuple"] == (24, 2, 1)

    def test_parse_old_version_format(self):
        """Test parsing old 1.x version format"""
        result = self.parse("portworx-operator.v1.10.5")
        assert result["tuple"] == (1, 10, 5)
        assert result["major"] == 1
        assert result["minor"] == 10
        assert result["patch"] == 5

    def test_parse_invalid_format(self):
        """Test error on invalid format"""
        with pytest.raises(AnsibleFilterError, match="Cannot parse"):
            self.parse("invalid-name")

    def test_parse_non_string_input(self):
        """Test error on non-string input"""
        with pytest.raises(AnsibleFilterError, match="requires a string"):
            self.parse(12345)

    def test_parse_missing_patch(self):
        """Test error on incomplete version"""
        with pytest.raises(AnsibleFilterError, match="Cannot parse"):
            self.parse("portworx-operator.v25.5")

    def test_parse_empty_string(self):
        """Test error on empty string"""
        with pytest.raises(AnsibleFilterError, match="Cannot parse"):
            self.parse("")

    def test_parse_none_input(self):
        """Test error on None input"""
        with pytest.raises(AnsibleFilterError, match="requires a string"):
            self.parse(None)

    def test_parse_dict_input(self):
        """Test error on dict input"""
        with pytest.raises(AnsibleFilterError, match="requires a string"):
            self.parse({"version": "25.5.0"})

    def test_parse_list_input(self):
        """Test error on list input"""
        with pytest.raises(AnsibleFilterError, match="requires a string"):
            self.parse([25, 5, 0])

    def test_parse_float_input(self):
        """Test error on float input"""
        with pytest.raises(AnsibleFilterError, match="requires a string"):
            self.parse(25.5)

    def test_parse_with_letters_after_version(self):
        """Test parsing version with letters after (regex stops at first non-digit)"""
        # The regex will match up to the letters and stop
        result = self.parse("portworx-operator.v25.5.0-beta")
        assert result["tuple"] == (25, 5, 0)
        assert result["string"] == "25.5.0"

    def test_parse_with_build_metadata(self):
        """Test parsing version with build metadata"""
        result = self.parse("portworx-operator.v25.5.0+build123")
        assert result["tuple"] == (25, 5, 0)

    def test_parse_with_dash_before_version(self):
        """Test parsing with dash before version (dash is ignored, digits parsed)"""
        # The regex searches for digits, ignoring the dash
        result = self.parse("portworx-operator.v-25.5.0")
        assert result["tuple"] == (25, 5, 0)

    def test_parse_four_part_version(self):
        """Test parsing with extra version part (regex captures first three only)"""
        result = self.parse("portworx-operator.v25.5.0.1")
        # Regex captures 25.5.0 and ignores .1
        assert result["tuple"] == (25, 5, 0)

    def test_parse_whitespace_in_version(self):
        """Test error on whitespace in version"""
        with pytest.raises(AnsibleFilterError, match="Cannot parse"):
            self.parse("portworx-operator.v25. 5.0")


class TestCompareVersions:
    """Test compare_versions filter"""

    def setup_method(self):
        self.filters = FilterModule()
        self.compare = self.filters.filters()["compare_versions"]

    def test_less_than_major(self):
        """Test version1 < version2 (major difference)"""
        assert self.compare((23, 10, 3), (25, 5, 0)) == -1

    def test_less_than_minor(self):
        """Test version1 < version2 (minor difference)"""
        assert self.compare((25, 4, 0), (25, 5, 0)) == -1

    def test_less_than_patch(self):
        """Test version1 < version2 (patch difference)"""
        assert self.compare((25, 5, 0), (25, 5, 1)) == -1

    def test_greater_than_major(self):
        """Test version1 > version2 (major difference)"""
        assert self.compare((25, 5, 0), (24, 2, 1)) == 1

    def test_greater_than_minor(self):
        """Test version1 > version2 (minor difference)"""
        assert self.compare((25, 5, 0), (25, 4, 0)) == 1

    def test_greater_than_patch(self):
        """Test version1 > version2 (patch difference)"""
        assert self.compare((25, 5, 1), (25, 5, 0)) == 1

    def test_equal(self):
        """Test version1 == version2"""
        assert self.compare((25, 5, 0), (25, 5, 0)) == 0

    def test_invalid_tuple_input(self):
        """Test error on non-tuple input"""
        with pytest.raises(
            AnsibleFilterError, match="requires both arguments to be tuples"
        ):
            self.compare([25, 5, 0], (24, 2, 1))

    def test_invalid_both_inputs(self):
        """Test error when both inputs are invalid"""
        with pytest.raises(
            AnsibleFilterError, match="requires both arguments to be tuples"
        ):
            self.compare([25, 5, 0], [24, 2, 1])

    def test_none_input_first(self):
        """Test error on None as first input"""
        with pytest.raises(
            AnsibleFilterError, match="requires both arguments to be tuples"
        ):
            self.compare(None, (24, 2, 1))

    def test_none_input_second(self):
        """Test error on None as second input"""
        with pytest.raises(
            AnsibleFilterError, match="requires both arguments to be tuples"
        ):
            self.compare((25, 5, 0), None)

    def test_string_input(self):
        """Test error on string input"""
        with pytest.raises(
            AnsibleFilterError, match="requires both arguments to be tuples"
        ):
            self.compare("25.5.0", (24, 2, 1))

    def test_dict_input(self):
        """Test error on dict input"""
        with pytest.raises(
            AnsibleFilterError, match="requires both arguments to be tuples"
        ):
            self.compare({"version": (25, 5, 0)}, (24, 2, 1))

    def test_empty_tuple(self):
        """Test handling of empty tuple"""
        # Empty tuples should still compare (Python allows it)
        result = self.compare((), ())
        assert result == 0

    def test_single_element_tuple(self):
        """Test handling of single element tuple"""
        result = self.compare((25,), (24,))
        assert result == 1

    def test_mismatched_tuple_lengths(self):
        """Test tuples with different lengths"""
        result = self.compare((25, 5), (24, 2, 1))
        assert result == 1  # 25 > 24

    def test_tuple_with_strings(self):
        """Test tuples containing strings instead of ints"""
        # This should work or fail gracefully depending on implementation
        result = self.compare(("25", "5", "0"), ("24", "2", "1"))
        assert result == 1  # String comparison "25" > "24"


class TestFilterGreaterVersions:
    """Test filter_greater_versions filter"""

    def setup_method(self):
        self.filters = FilterModule()
        self.filter_fn = self.filters.filters()["filter_greater_versions"]

    def test_filter_candidates(self):
        """Test filtering candidates greater than current"""
        candidates = [
            {"csv_name": "v23.10.3", "version_tuple": (23, 10, 3)},
            {"csv_name": "v24.1.0", "version_tuple": (24, 1, 0)},
            {"csv_name": "v24.2.1", "version_tuple": (24, 2, 1)},
            {"csv_name": "v25.5.0", "version_tuple": (25, 5, 0)},
        ]
        current = (24, 1, 0)

        result = self.filter_fn(candidates, current)

        assert len(result) == 2
        assert result[0]["version_tuple"] == (24, 2, 1)
        assert result[1]["version_tuple"] == (25, 5, 0)

    def test_no_greater_versions(self):
        """Test when no candidates are greater"""
        candidates = [
            {"version_tuple": (23, 10, 3)},
            {"version_tuple": (24, 1, 0)},
        ]
        current = (25, 5, 0)

        result = self.filter_fn(candidates, current)
        assert len(result) == 0

    def test_all_greater_versions(self):
        """Test when all candidates are greater"""
        candidates = [
            {"version_tuple": (24, 2, 1)},
            {"version_tuple": (25, 5, 0)},
        ]
        current = (23, 10, 3)

        result = self.filter_fn(candidates, current)
        assert len(result) == 2

    def test_filter_with_equal_version(self):
        """Test that equal version is NOT included"""
        candidates = [
            {"version_tuple": (24, 1, 0)},
            {"version_tuple": (24, 2, 1)},
        ]
        current = (24, 1, 0)

        result = self.filter_fn(candidates, current)
        assert len(result) == 1
        assert result[0]["version_tuple"] == (24, 2, 1)

    def test_invalid_list_input(self):
        """Test error on non-list input"""
        with pytest.raises(AnsibleFilterError, match="requires a list"):
            self.filter_fn("not a list", (24, 1, 0))

    def test_invalid_tuple_input(self):
        """Test error on non-tuple current version"""
        with pytest.raises(AnsibleFilterError, match="must be a tuple"):
            self.filter_fn([], [24, 1, 0])

    def test_empty_candidates_list(self):
        """Test with empty candidates list"""
        result = self.filter_fn([], (24, 1, 0))
        assert len(result) == 0

    def test_candidates_with_none_elements(self):
        """Test candidates list containing None"""
        candidates = [
            None,
            {"version_tuple": (24, 1, 0)},
        ]
        # Should handle None gracefully or raise error
        try:
            result = self.filter_fn(candidates, (23, 10, 3))
            # If it doesn't error, None should be filtered out or handled
            assert all(c is not None for c in result)
        except (AnsibleFilterError, AttributeError, TypeError):
            # Expected - should raise error on None element
            pass

    def test_candidates_missing_version_tuple(self):
        """Test candidates with missing version_tuple key"""
        candidates = [
            {"csv_name": "v24.1.0"},  # Missing version_tuple
        ]
        # Should error or handle gracefully
        try:
            self.filter_fn(candidates, (23, 10, 3))
        except (KeyError, AnsibleFilterError):
            pass  # Expected

    def test_current_version_none(self):
        """Test with None as current version"""
        candidates = [{"version_tuple": (24, 1, 0)}]
        with pytest.raises(AnsibleFilterError, match="must be a tuple"):
            self.filter_fn(candidates, None)

    def test_candidates_with_empty_dict(self):
        """Test candidates containing empty dict"""
        candidates = [
            {},
            {"version_tuple": (24, 1, 0)},
        ]
        try:
            result = self.filter_fn(candidates, (23, 10, 3))
            # Should handle or error on missing version_tuple
        except (KeyError, AnsibleFilterError):
            pass  # Expected


class TestSortVersions:
    """Test sort_versions filter"""

    def setup_method(self):
        self.filters = FilterModule()
        self.sort = self.filters.filters()["sort_versions"]

    def test_sort_ascending(self):
        """Test sorting versions in ascending order"""
        candidates = [
            {"csv_name": "v25.5.0", "version_tuple": (25, 5, 0)},
            {"csv_name": "v23.10.3", "version_tuple": (23, 10, 3)},
            {"csv_name": "v24.2.1", "version_tuple": (24, 2, 1)},
            {"csv_name": "v24.1.0", "version_tuple": (24, 1, 0)},
        ]

        result = self.sort(candidates)

        assert result[0]["version_tuple"] == (23, 10, 3)
        assert result[1]["version_tuple"] == (24, 1, 0)
        assert result[2]["version_tuple"] == (24, 2, 1)
        assert result[3]["version_tuple"] == (25, 5, 0)

    def test_sort_with_same_major(self):
        """Test sorting with same major version"""
        candidates = [
            {"version_tuple": (25, 5, 0)},
            {"version_tuple": (25, 2, 0)},
            {"version_tuple": (25, 3, 1)},
        ]

        result = self.sort(candidates)
        assert result[0]["version_tuple"] == (25, 2, 0)
        assert result[1]["version_tuple"] == (25, 3, 1)
        assert result[2]["version_tuple"] == (25, 5, 0)

    def test_sort_already_sorted(self):
        """Test sorting already sorted list"""
        candidates = [
            {"version_tuple": (23, 10, 3)},
            {"version_tuple": (24, 1, 0)},
            {"version_tuple": (25, 5, 0)},
        ]

        result = self.sort(candidates)
        assert result[0]["version_tuple"] == (23, 10, 3)
        assert result[1]["version_tuple"] == (24, 1, 0)
        assert result[2]["version_tuple"] == (25, 5, 0)

    def test_invalid_list_input(self):
        """Test error on non-list input"""
        with pytest.raises(AnsibleFilterError, match="requires a list"):
            self.sort("not a list")

    def test_empty_list(self):
        """Test sorting empty list"""
        result = self.sort([])
        assert len(result) == 0

    def test_single_element_list(self):
        """Test sorting single element list"""
        candidates = [{"version_tuple": (25, 5, 0)}]
        result = self.sort(candidates)
        assert len(result) == 1
        assert result[0]["version_tuple"] == (25, 5, 0)

    def test_none_input(self):
        """Test error on None input"""
        with pytest.raises(AnsibleFilterError, match="requires a list"):
            self.sort(None)

    def test_candidates_with_none_elements(self):
        """Test candidates containing None"""
        candidates = [
            None,
            {"version_tuple": (25, 5, 0)},
        ]
        # This will raise an error when trying to access .get() on None
        with pytest.raises((AttributeError, TypeError, AnsibleFilterError)):
            result = self.sort(candidates)

    def test_candidates_missing_version_tuple(self):
        """Test candidates with missing version_tuple"""
        candidates = [
            {"csv_name": "v25.5.0"},  # Missing version_tuple
        ]
        try:
            result = self.sort(candidates)
        except (KeyError, AttributeError):
            pass  # Expected


class TestCalculateUpgradePathLength:
    """Test calculate_upgrade_path_length filter"""

    def setup_method(self):
        self.filters = FilterModule()
        self.calc = self.filters.filters()["calculate_upgrade_path_length"]

    def test_valid_path_within_skew(self):
        """Test valid upgrade path within max skew"""
        candidates = [
            {"csv_name": "v23.10.3", "version_tuple": (23, 10, 3)},
            {"csv_name": "v24.1.0", "version_tuple": (24, 1, 0)},
            {"csv_name": "v24.2.1", "version_tuple": (24, 2, 1)},
            {"csv_name": "v25.5.0", "version_tuple": (25, 5, 0)},
        ]
        current = (23, 10, 3)
        target = (25, 5, 0)

        result = self.calc(candidates, current, target, 10)
        assert result == 3  # 24.1.0, 24.2.1, 25.5.0

    def test_path_with_no_intermediates(self):
        """Test direct path with no intermediate versions"""
        candidates = [
            {"version_tuple": (23, 10, 3)},
            {"version_tuple": (25, 5, 0)},
        ]
        current = (23, 10, 3)
        target = (25, 5, 0)

        result = self.calc(candidates, current, target, 10)
        assert result == 1  # Only target

    def test_path_exceeds_max_skew(self):
        """Test error when path exceeds max skew"""
        candidates = [{"version_tuple": (24, i, 0)} for i in range(15)]
        current = (24, 0, 0)
        target = (24, 14, 0)

        with pytest.raises(AnsibleFilterError, match="Version skew too large"):
            self.calc(candidates, current, target, 10)

    def test_path_at_max_skew_boundary(self):
        """Test path exactly at max skew boundary"""
        candidates = [{"version_tuple": (24, i, 0)} for i in range(1, 11)]
        current = (24, 0, 0)
        target = (24, 10, 0)

        result = self.calc(candidates, current, target, 10)
        assert result == 10

    def test_no_candidates_between_versions(self):
        """Test when no candidates exist between current and target"""
        candidates = [
            {"version_tuple": (23, 10, 3)},
            {"version_tuple": (25, 5, 0)},
        ]
        current = (24, 0, 0)
        target = (24, 5, 0)

        result = self.calc(candidates, current, target, 10)
        assert result == 0

    def test_invalid_candidates_input(self):
        """Test error on non-list candidates"""
        with pytest.raises(AnsibleFilterError, match="requires a list"):
            self.calc("not a list", (24, 0, 0), (25, 0, 0), 10)

    def test_invalid_current_tuple(self):
        """Test error on non-tuple current version"""
        with pytest.raises(AnsibleFilterError, match="must be a tuple"):
            self.calc([], [24, 0, 0], (25, 0, 0), 10)

    def test_invalid_target_tuple(self):
        """Test error on non-tuple target version"""
        with pytest.raises(AnsibleFilterError, match="must be a tuple"):
            self.calc([], (24, 0, 0), [25, 0, 0], 10)

    def test_invalid_max_skew(self):
        """Test error on invalid max_skew"""
        with pytest.raises(AnsibleFilterError, match="positive integer"):
            self.calc([], (24, 0, 0), (25, 0, 0), 0)

    def test_negative_max_skew(self):
        """Test error on negative max_skew"""
        with pytest.raises(AnsibleFilterError, match="positive integer"):
            self.calc([], (24, 0, 0), (25, 0, 0), -5)

    def test_empty_candidates_list(self):
        """Test with empty candidates list"""
        result = self.calc([], (24, 0, 0), (25, 0, 0), 10)
        assert result == 0

    def test_none_max_skew(self):
        """Test with None as max_skew"""
        with pytest.raises((AnsibleFilterError, TypeError)):
            self.calc([], (24, 0, 0), (25, 0, 0), None)

    def test_string_max_skew(self):
        """Test with string as max_skew"""
        with pytest.raises((AnsibleFilterError, TypeError)):
            self.calc([], (24, 0, 0), (25, 0, 0), "10")

    def test_float_max_skew(self):
        """Test with float as max_skew (isinstance check fails for float)"""
        # The isinstance check requires int, not float
        with pytest.raises((AnsibleFilterError, TypeError)):
            self.calc([], (24, 0, 0), (25, 0, 0), 10.5)

    def test_current_equals_target(self):
        """Test when current version equals target"""
        candidates = [{"version_tuple": (24, 1, 0)}]
        result = self.calc(candidates, (24, 1, 0), (24, 1, 0), 10)
        assert result == 0

    def test_current_greater_than_target(self):
        """Test when current version is greater than target (downgrade)"""
        candidates = [{"version_tuple": (24, 1, 0)}]
        result = self.calc(candidates, (25, 0, 0), (24, 1, 0), 10)
        assert result == 0  # No upgrade path exists

    def test_candidates_with_none_elements(self):
        """Test candidates containing None"""
        candidates = [
            None,
            {"version_tuple": (24, 1, 0)},
        ]
        # This will raise an error when trying to call .get() on None
        with pytest.raises((AttributeError, TypeError, AnsibleFilterError)):
            result = self.calc(candidates, (24, 0, 0), (25, 0, 0), 10)

    def test_candidates_missing_version_tuple(self):
        """Test candidates with missing version_tuple"""
        candidates = [{"csv_name": "v24.1.0"}]
        try:
            result = self.calc(candidates, (24, 0, 0), (25, 0, 0), 10)
        except (KeyError, AttributeError):
            pass  # Expected

    def test_extreme_version_numbers(self):
        """Test with very large version numbers"""
        candidates = [
            {"version_tuple": (999, 999, 999)},
        ]
        current = (0, 0, 0)
        target = (999, 999, 999)
        result = self.calc(candidates, current, target, 10)
        assert result == 1  # Only one version in path


# Integration test combining multiple filters
class TestFilterIntegration:
    """Test integration of multiple filters together"""

    def setup_method(self):
        self.filters = FilterModule()

    def test_discover_and_select_next_candidate(self):
        """Test full workflow of discovering next candidate"""
        # Mock data from OLM
        all_candidates = [
            {"csv_name": "v25.5.0", "version_tuple": (25, 5, 0)},
            {"csv_name": "v23.10.3", "version_tuple": (23, 10, 3)},
            {"csv_name": "v24.2.1", "version_tuple": (24, 2, 1)},
            {"csv_name": "v24.1.0", "version_tuple": (24, 1, 0)},
        ]
        current = (24, 0, 0)

        # Filter versions greater than current
        filter_fn = self.filters.filters()["filter_greater_versions"]
        greater = filter_fn(all_candidates, current)

        # Sort to find next
        sort_fn = self.filters.filters()["sort_versions"]
        sorted_candidates = sort_fn(greater)

        # Next candidate should be 24.1.0 (smallest > 24.0.0)
        next_candidate = sorted_candidates[0]
        assert next_candidate["version_tuple"] == (24, 1, 0)
        assert next_candidate["csv_name"] == "v24.1.0"

    def test_calculate_full_upgrade_path(self):
        """Test calculating full sequential upgrade path"""
        all_candidates = [
            {"csv_name": "v24.1.0", "version_tuple": (24, 1, 0)},
            {"csv_name": "v24.2.1", "version_tuple": (24, 2, 1)},
            {"csv_name": "v25.5.0", "version_tuple": (25, 5, 0)},
        ]
        current = (23, 10, 3)
        target = (25, 5, 0)

        filter_fn = self.filters.filters()["filter_greater_versions"]
        sort_fn = self.filters.filters()["sort_versions"]
        calc_fn = self.filters.filters()["calculate_upgrade_path_length"]

        # Calculate path length
        path_length = calc_fn(all_candidates, current, target, 10)
        assert path_length == 3

        # Get sequential path
        greater = filter_fn(all_candidates, current)
        path = sort_fn(greater)

        assert len(path) == 3
        assert path[0]["csv_name"] == "v24.1.0"
        assert path[1]["csv_name"] == "v24.2.1"
        assert path[2]["csv_name"] == "v25.5.0"
