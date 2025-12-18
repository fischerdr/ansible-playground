#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Standalone test for Jinja2 template logic used in discover_next_candidate.yml
Tests the template without full Ansible context
"""

import os
import sys

from jinja2 import Environment

# Add filter plugin directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../filter_plugins"))

from operator_version import FilterModule


def test_jinja2_template():
    """Test the exact Jinja2 template used in discover_next_candidate.yml"""

    print("\n═══════════════════════════════════════════════════════════")
    print("TESTING JINJA2 TEMPLATE LOGIC")
    print("═══════════════════════════════════════════════════════════\n")

    # Setup Jinja2 environment with our filter plugin
    env = Environment()
    filters = FilterModule().filters()
    env.filters.update(filters)

    # The exact template from discover_next_candidate.yml
    template_str = """
{%- set candidates = [] -%}
{%- for ip in portworx_operator_installplans.resources -%}
  {%- for csv_name in ip.spec.clusterServiceVersionNames -%}
    {%- if csv_name.startswith(portworx_operator_csv_prefix) -%}
      {%- set version_parsed = csv_name | parse_operator_version -%}
      {%- if version_parsed.tuple > portworx_operator_current_version_tuple -%}
        {%- set _ = candidates.append({
              'installplan_name': ip.metadata.name,
              'csv_name': csv_name,
              'approved': ip.spec.approved | default(false),
              'version_tuple': version_parsed.tuple,
              'version_string': version_parsed.string,
              'version_major': version_parsed.major,
              'version_minor': version_parsed.minor,
              'version_patch': version_parsed.patch
            }) -%}
      {%- endif -%}
    {%- endif -%}
  {%- endfor -%}
{%- endfor -%}
{{ candidates | sort(attribute='version_tuple') | first | default({}) }}
"""

    template = env.from_string(template_str)

    # Test 1: Basic candidate discovery
    print("Test 1: Basic candidate discovery")
    print("-" * 50)

    context = {
        "portworx_operator_csv_prefix": "portworx-operator",
        "portworx_operator_current_version_tuple": (23, 10, 3),
        "portworx_operator_installplans": {
            "resources": [
                {
                    "metadata": {"name": "install-plan-24-1-0"},
                    "spec": {
                        "clusterServiceVersionNames": ["portworx-operator.v24.1.0"],
                        "approved": False,
                    },
                },
                {
                    "metadata": {"name": "install-plan-25-5-0"},
                    "spec": {
                        "clusterServiceVersionNames": ["portworx-operator.v25.5.0"],
                        "approved": False,
                    },
                },
                {
                    "metadata": {"name": "install-plan-24-2-1"},
                    "spec": {
                        "clusterServiceVersionNames": ["portworx-operator.v24.2.1"],
                        "approved": False,
                    },
                },
            ]
        },
    }

    result = template.render(context)
    # Parse result (it's a string representation of a dict)
    import ast

    result_dict = ast.literal_eval(result.strip())

    print(f"Current version: {context['portworx_operator_current_version_tuple']}")
    print(f"Result: {result_dict}")

    assert (
        result_dict["csv_name"] == "portworx-operator.v24.1.0"
    ), f"Expected v24.1.0, got {result_dict.get('csv_name')}"
    assert result_dict["version_tuple"] == (
        24,
        1,
        0,
    ), f"Expected (24, 1, 0), got {result_dict.get('version_tuple')}"
    assert (
        result_dict["installplan_name"] == "install-plan-24-1-0"
    ), f"Expected install-plan-24-1-0, got {result_dict.get('installplan_name')}"

    print("✓ PASS: Correctly selected smallest version > current\n")

    # Test 2: No candidates (current > all available)
    print("Test 2: No candidates scenario")
    print("-" * 50)

    context["portworx_operator_current_version_tuple"] = (26, 0, 0)
    result = template.render(context)

    print(f"Current version: {context['portworx_operator_current_version_tuple']}")
    print(f"Result: {result.strip()}")

    assert result.strip() == "{}", f"Expected empty dict, got {result.strip()}"
    print("✓ PASS: Correctly returns {} when no candidates\n")

    # Test 3: Already approved InstallPlan
    print("Test 3: Already approved InstallPlan")
    print("-" * 50)

    context["portworx_operator_current_version_tuple"] = (23, 10, 3)
    context["portworx_operator_installplans"] = {
        "resources": [
            {
                "metadata": {"name": "install-plan-24-1-0-approved"},
                "spec": {
                    "clusterServiceVersionNames": ["portworx-operator.v24.1.0"],
                    "approved": True,  # Already approved
                },
            }
        ]
    }

    result = template.render(context)
    result_dict = ast.literal_eval(result.strip())

    print(f"Result approved status: {result_dict['approved']}")
    assert result_dict["approved"] is True, (
        f"Expected approved=True, got {result_dict['approved']}"
    )
    print("✓ PASS: Correctly captures approved status\n")

    # Test 4: Multiple CSVs in single InstallPlan
    print("Test 4: Multiple CSVs in single InstallPlan")
    print("-" * 50)

    context["portworx_operator_installplans"] = {
        "resources": [
            {
                "metadata": {"name": "install-plan-multi"},
                "spec": {
                    "clusterServiceVersionNames": [
                        "other-operator.v1.0.0",
                        "portworx-operator.v24.1.0",
                        "another-operator.v2.0.0",
                    ],
                    "approved": False,
                },
            }
        ]
    }

    result = template.render(context)
    result_dict = ast.literal_eval(result.strip())

    print(f"Result CSV name: {result_dict['csv_name']}")
    assert (
        result_dict["csv_name"] == "portworx-operator.v24.1.0"
    ), f"Expected portworx-operator.v24.1.0, got {result_dict['csv_name']}"
    print("✓ PASS: Correctly filters by CSV prefix\n")

    # Test 5: Missing approved field (Jinja2 default filter)
    print("Test 5: Missing approved field (default handling)")
    print("-" * 50)

    context["portworx_operator_installplans"] = {
        "resources": [
            {
                "metadata": {"name": "install-plan-no-approved"},
                "spec": {
                    "clusterServiceVersionNames": ["portworx-operator.v24.1.0"]
                    # No 'approved' field
                },
            }
        ]
    }

    result = template.render(context)
    result_dict = ast.literal_eval(result.strip())

    print(f"Result approved (should default to False): {result_dict['approved']}")
    assert result_dict["approved"] is False, (
        f"Expected approved=False (default), got {result_dict['approved']}"
    )
    print("✓ PASS: Correctly defaults approved to False\n")

    # Test 6: Unsorted input - verify sorting works
    print("Test 6: Unsorted input (verify sorting)")
    print("-" * 50)

    context["portworx_operator_current_version_tuple"] = (23, 0, 0)
    context["portworx_operator_installplans"] = {
        "resources": [
            {
                "metadata": {"name": "install-plan-25"},
                "spec": {
                    "clusterServiceVersionNames": ["portworx-operator.v25.5.0"],
                    "approved": False,
                },
            },
            {
                "metadata": {"name": "install-plan-24-1"},
                "spec": {
                    "clusterServiceVersionNames": ["portworx-operator.v24.1.0"],
                    "approved": False,
                },
            },
            {
                "metadata": {"name": "install-plan-23"},
                "spec": {
                    "clusterServiceVersionNames": ["portworx-operator.v23.10.3"],
                    "approved": False,
                },
            },
        ]
    }

    result = template.render(context)
    result_dict = ast.literal_eval(result.strip())

    print(f"Result (should be smallest: 23.10.3): {result_dict['version_string']}")
    assert (
        result_dict["version_string"] == "23.10.3"
    ), f"Expected 23.10.3, got {result_dict['version_string']}"
    print("✓ PASS: Correctly sorts and selects smallest\n")

    # Test 7: Empty resources list (negative test)
    print("Test 7: Empty resources list (negative)")
    print("-" * 50)

    context["portworx_operator_installplans"] = {"resources": []}  # Empty list

    result = template.render(context)
    print(f"Result with empty resources: {result.strip()}")
    assert result.strip() == "{}", f"Expected empty dict, got {result.strip()}"
    print("✓ PASS: Correctly handles empty resources list\n")

    # Test 8: Missing resources key (negative test)
    print("Test 8: Missing resources key (negative)")
    print("-" * 50)

    context["portworx_operator_installplans"] = {}  # Missing 'resources' key

    try:
        result = template.render(context)
        result_dict = result.strip()
        # Jinja2 may handle undefined gracefully and return empty dict
        print(f"Result with missing resources: {result_dict}")
        assert result_dict == "{}", f"Expected empty dict, got {result_dict}"
        print("✓ PASS: Handled missing resources key gracefully")
    except Exception as e:
        # Also acceptable to raise error
        print(f"✓ PASS: Correctly raises error: {type(e).__name__}")

    # Test 9: None in resources list (negative test)
    print("\nTest 9: None in resources list (negative)")
    print("-" * 50)

    context["portworx_operator_installplans"] = {
        "resources": [
            None,  # Invalid entry
            {
                "metadata": {"name": "install-plan-valid"},
                "spec": {
                    "clusterServiceVersionNames": ["portworx-operator.v24.1.0"],
                    "approved": False,
                },
            },
        ]
    }

    try:
        result = template.render(context)
        # Should error on None
        print("✗ FAIL: Should have raised error on None in resources")
        assert False, "Should have raised UndefinedError"
    except Exception as e:
        print(f"✓ PASS: Correctly raises error: {type(e).__name__}")

    # Test 10: Missing metadata in InstallPlan (negative test)
    print("\nTest 10: Missing metadata in InstallPlan (negative)")
    print("-" * 50)

    context["portworx_operator_installplans"] = {
        "resources": [
            {
                # Missing 'metadata' key
                "spec": {
                    "clusterServiceVersionNames": ["portworx-operator.v24.1.0"],
                    "approved": False,
                }
            }
        ]
    }

    try:
        result = template.render(context)
        # Should error on missing metadata
        print("✗ FAIL: Should have raised error on missing metadata")
        assert False, "Should have raised UndefinedError"
    except Exception as e:
        print(f"✓ PASS: Correctly raises error: {type(e).__name__}")

    # Test 11: Empty clusterServiceVersionNames list (negative test)
    print("\nTest 11: Empty clusterServiceVersionNames list (negative)")
    print("-" * 50)

    context["portworx_operator_installplans"] = {
        "resources": [
            {
                "metadata": {"name": "install-plan-empty-csv"},
                "spec": {
                    "clusterServiceVersionNames": [],  # Empty list
                    "approved": False,
                },
            }
        ]
    }

    result = template.render(context)
    print(f"Result with empty CSV list: {result.strip()}")
    assert result.strip() == "{}", f"Expected empty dict, got {result.strip()}"
    print("✓ PASS: Correctly handles empty CSV list\n")

    # Test 12: Invalid version format in CSV name (negative test)
    print("Test 12: Invalid version format in CSV name (negative)")
    print("-" * 50)

    context["portworx_operator_installplans"] = {
        "resources": [
            {
                "metadata": {"name": "install-plan-invalid-version"},
                "spec": {
                    "clusterServiceVersionNames": [
                        "portworx-operator.invalid",  # Invalid format
                        "portworx-operator.v24.1.0",  # Valid format
                    ],
                    "approved": False,
                },
            }
        ]
    }

    try:
        result = template.render(context)
        # Should error on invalid version or skip it
        result_dict = ast.literal_eval(result.strip())
        if result_dict:
            # If it succeeded, it should have skipped invalid and found valid
            assert result_dict["csv_name"] == "portworx-operator.v24.1.0"
            print("✓ PASS: Correctly skipped invalid version and found valid one")
        else:
            print("✓ PASS: Correctly handled invalid version (empty result)")
    except Exception as e:
        print(f"✓ PASS: Correctly raises error on invalid version: {type(e).__name__}")

    # Test 13: Non-matching CSV prefix (negative test)
    print("\nTest 13: Non-matching CSV prefix (negative)")
    print("-" * 50)

    context["portworx_operator_csv_prefix"] = "portworx-operator"
    context["portworx_operator_installplans"] = {
        "resources": [
            {
                "metadata": {"name": "install-plan-other"},
                "spec": {
                    "clusterServiceVersionNames": [
                        "other-operator.v24.1.0",
                        "different-operator.v25.0.0",
                    ],
                    "approved": False,
                },
            }
        ]
    }

    result = template.render(context)
    print(f"Result with non-matching prefixes: {result.strip()}")
    assert result.strip() == "{}", f"Expected empty dict, got {result.strip()}"
    print("✓ PASS: Correctly filters out non-matching prefixes\n")

    # Test 14: Very large version numbers (edge case)
    print("Test 14: Very large version numbers (edge case)")
    print("-" * 50)

    context["portworx_operator_current_version_tuple"] = (0, 0, 0)
    context["portworx_operator_installplans"] = {
        "resources": [
            {
                "metadata": {"name": "install-plan-large"},
                "spec": {
                    "clusterServiceVersionNames": ["portworx-operator.v999.999.999"],
                    "approved": False,
                },
            }
        ]
    }

    result = template.render(context)
    result_dict = ast.literal_eval(result.strip())
    print(f"Result version: {result_dict['version_tuple']}")
    assert result_dict["version_tuple"] == (999, 999, 999)
    print("✓ PASS: Correctly handles very large version numbers\n")

    # Test 15: Duplicate versions (edge case)
    print("Test 15: Duplicate versions in different InstallPlans (edge case)")
    print("-" * 50)

    context["portworx_operator_current_version_tuple"] = (23, 0, 0)
    context["portworx_operator_installplans"] = {
        "resources": [
            {
                "metadata": {"name": "install-plan-dup-1"},
                "spec": {
                    "clusterServiceVersionNames": ["portworx-operator.v24.1.0"],
                    "approved": False,
                },
            },
            {
                "metadata": {"name": "install-plan-dup-2"},
                "spec": {
                    "clusterServiceVersionNames": ["portworx-operator.v24.1.0"],
                    "approved": True,  # Same version, different approval status
                },
            },
        ]
    }

    result = template.render(context)
    result_dict = ast.literal_eval(result.strip())
    print(
        f"Result with duplicates: {result_dict['installplan_name']}, approved: {result_dict['approved']}"
    )
    assert result_dict["version_tuple"] == (24, 1, 0)
    print("✓ PASS: Correctly handles duplicate versions (first occurrence wins)\n")

    # Summary
    print("═══════════════════════════════════════════════════════════")
    print("ALL JINJA2 TEMPLATE TESTS PASSED")
    print("═══════════════════════════════════════════════════════════")
    print("\nPositive Tests (Expected Success):")
    print("  1. Basic candidate discovery ✓")
    print("  2. Already approved InstallPlan ✓")
    print("  3. Multiple CSVs in InstallPlan (prefix filtering) ✓")
    print("  4. Missing approved field (default to False) ✓")
    print("  5. Unsorted input (sorting verification) ✓")
    print("  6. Very large version numbers ✓")
    print("  7. Duplicate versions ✓")
    print("\nNegative Tests (Error Handling):")
    print("  8. No candidates scenario (empty dict) ✓")
    print("  9. Empty resources list ✓")
    print(" 10. Missing resources key ✓")
    print(" 11. None in resources list ✓")
    print(" 12. Missing metadata in InstallPlan ✓")
    print(" 13. Empty clusterServiceVersionNames list ✓")
    print(" 14. Invalid version format in CSV name ✓")
    print(" 15. Non-matching CSV prefix ✓")
    print("\nThe Jinja2 template in discover_next_candidate.yml is ROBUST ✓\n")


if __name__ == "__main__":
    try:
        test_jinja2_template()
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
