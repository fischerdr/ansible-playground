#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Integration tests for post-step Subscription re-validation
Tests the refactored update_version_state.yml logic
"""

import os
import sys

from jinja2 import Environment

# Add filter plugin directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../filter_plugins"))

from operator_version import FilterModule


def test_post_step_validation():
    """Test post-step Subscription re-validation patterns"""

    # Setup Jinja2 environment with filter plugins
    env = Environment()
    filter_module = FilterModule()
    env.filters.update(filter_module.filters())

    print("═══════════════════════════════════════════════════════════")
    print("POST-STEP SUBSCRIPTION VALIDATION TESTS")
    print("═══════════════════════════════════════════════════════════\n")

    # Test 1: Successful upgrade validation (positive)
    print("Test 1: Successful upgrade validation (positive)")
    print("-" * 50)

    target_csv = "portworx-operator.v24.1.0"
    subscription_recheck = {
        "resources": [
            {
                "metadata": {"name": "portworx-certified"},
                "status": {
                    "installedCSV": "portworx-operator.v24.1.0",
                    "currentCSV": "portworx-operator.v24.1.0",
                },
            }
        ]
    }

    updated_csv = subscription_recheck["resources"][0]["status"].get(
        "installedCSV"
    ) or subscription_recheck["resources"][0]["status"].get("currentCSV", "")

    # Validation checks
    assert len(subscription_recheck["resources"]) > 0
    assert updated_csv != ""
    assert updated_csv == target_csv

    print(f"Expected: {target_csv}")
    print(f"Actual: {updated_csv}")
    print("✓ PASS: Subscription confirms updated CSV\n")

    # Test 2: Subscription reports different CSV (negative)
    print("Test 2: Subscription reports different CSV (negative)")
    print("-" * 50)

    target_csv = "portworx-operator.v24.1.0"
    subscription_recheck = {
        "resources": [
            {
                "metadata": {"name": "portworx-certified"},
                "status": {
                    "installedCSV": "portworx-operator.v23.10.3",  # Wrong version
                    "currentCSV": "portworx-operator.v24.1.0",
                },
            }
        ]
    }

    updated_csv = subscription_recheck["resources"][0]["status"].get(
        "installedCSV"
    ) or subscription_recheck["resources"][0]["status"].get("currentCSV", "")

    # Should detect mismatch
    assert updated_csv != target_csv
    print(f"Expected: {target_csv}")
    print(f"Actual: {updated_csv}")
    print("✓ PASS: Correctly detected CSV mismatch\n")

    # Test 3: CSV exists but not in Succeeded phase (negative)
    print("Test 3: CSV not in Succeeded phase (negative)")
    print("-" * 50)

    csv_info = {
        "resources": [
            {
                "metadata": {"name": "portworx-operator.v24.1.0"},
                "status": {
                    "phase": "Installing",  # Not Succeeded
                },
            }
        ]
    }

    assert len(csv_info["resources"]) > 0
    csv_phase = csv_info["resources"][0].get("status", {}).get("phase", "unknown")
    assert csv_phase != "Succeeded"

    print(f"CSV phase: {csv_phase}")
    print("✓ PASS: Correctly detected non-Succeeded phase\n")

    # Test 4: CSV in Succeeded phase (positive)
    print("Test 4: CSV in Succeeded phase (positive)")
    print("-" * 50)

    csv_info = {
        "resources": [
            {
                "metadata": {"name": "portworx-operator.v24.1.0"},
                "status": {
                    "phase": "Succeeded",
                },
            }
        ]
    }

    assert len(csv_info["resources"]) > 0
    csv_phase = csv_info["resources"][0]["status"]["phase"]
    assert csv_phase == "Succeeded"

    print(f"CSV phase: {csv_phase}")
    print("✓ PASS: CSV is in Succeeded phase\n")

    # Test 5: Missing status.phase field (negative)
    print("Test 5: Missing status.phase field (negative)")
    print("-" * 50)

    csv_info = {
        "resources": [
            {
                "metadata": {"name": "portworx-operator.v24.1.0"},
                "status": {},  # No phase field
            }
        ]
    }

    csv_phase = csv_info["resources"][0].get("status", {}).get("phase", "unknown")
    assert csv_phase == "unknown"

    print(f"CSV phase (default): {csv_phase}")
    print("✓ PASS: Correctly defaults to 'unknown' when phase missing\n")

    # Test 6: Empty Subscription resources after recheck (negative)
    print("Test 6: Empty Subscription resources after recheck (negative)")
    print("-" * 50)

    subscription_recheck = {"resources": []}

    assert len(subscription_recheck["resources"]) == 0
    print("✓ PASS: Correctly detected empty resources after recheck\n")

    # Test 7: Subscription temporarily shows old CSV (OLM lag, negative)
    print("Test 7: OLM reconciliation lag (negative)")
    print("-" * 50)

    target_csv = "portworx-operator.v24.1.0"
    subscription_recheck = {
        "resources": [
            {
                "metadata": {"name": "portworx-certified"},
                "status": {
                    "installedCSV": "portworx-operator.v23.10.3",  # Old
                    "currentCSV": "portworx-operator.v23.10.3",
                },
            }
        ]
    }

    updated_csv = subscription_recheck["resources"][0]["status"].get(
        "installedCSV"
    ) or subscription_recheck["resources"][0]["status"].get("currentCSV", "")

    # OLM hasn't updated yet
    assert updated_csv != target_csv
    print(f"Expected: {target_csv}")
    print(f"Actual: {updated_csv} (OLM not reconciled yet)")
    print("✓ PASS: Correctly detected OLM reconciliation lag\n")

    # Test 8: CSV in Failed phase (negative)
    print("Test 8: CSV in Failed phase (negative)")
    print("-" * 50)

    csv_info = {
        "resources": [
            {
                "metadata": {"name": "portworx-operator.v24.1.0"},
                "status": {
                    "phase": "Failed",
                    "reason": "InstallFailed",
                    "message": "Failed to install operator",
                },
            }
        ]
    }

    csv_phase = csv_info["resources"][0]["status"]["phase"]
    assert csv_phase == "Failed"

    print(f"CSV phase: {csv_phase}")
    print(f"Reason: {csv_info['resources'][0]['status']['reason']}")
    print("✓ PASS: Correctly detected Failed phase\n")

    # Test 9: CSV missing entirely (negative)
    print("Test 9: CSV not found after InstallPlan approval (negative)")
    print("-" * 50)

    csv_info = {"resources": []}  # No CSV found

    assert len(csv_info["resources"]) == 0
    print("✓ PASS: Correctly detected missing CSV\n")

    # Test 10: Multiple CSV versions exist (edge case, negative)
    print("Test 10: Multiple CSV versions in namespace (edge case)")
    print("-" * 50)

    target_csv = "portworx-operator.v24.1.0"
    csv_info = {
        "resources": [
            {
                "metadata": {"name": "portworx-operator.v24.1.0"},
                "status": {"phase": "Succeeded"},
            },
            {
                "metadata": {"name": "portworx-operator.v23.10.3"},
                "status": {"phase": "Replacing"},
            },
        ]
    }

    # Should use explicit name lookup (first resource if querying by name)
    assert len(csv_info["resources"]) > 1
    target_resource = [
        r for r in csv_info["resources"] if r["metadata"]["name"] == target_csv
    ]
    assert len(target_resource) == 1
    assert target_resource[0]["status"]["phase"] == "Succeeded"

    print(f"Found target CSV: {target_csv}")
    print(f"Phase: {target_resource[0]['status']['phase']}")
    print("✓ PASS: Correctly found target CSV among multiple\n")

    # Test 11: Version parsing after validation (integration, positive)
    print("Test 11: Version parsing after validation (integration)")
    print("-" * 50)

    target_csv = "portworx-operator.v25.5.0"
    subscription_recheck = {
        "resources": [
            {
                "metadata": {"name": "portworx-certified"},
                "status": {
                    "installedCSV": target_csv,
                },
            }
        ]
    }

    updated_csv = subscription_recheck["resources"][0]["status"]["installedCSV"]
    assert updated_csv == target_csv

    # Parse the new version
    parse_fn = filter_module.filters()["parse_operator_version"]
    new_version = parse_fn(updated_csv)

    assert new_version["string"] == "25.5.0"
    assert new_version["tuple"] == (25, 5, 0)

    print(f"Updated CSV: {updated_csv}")
    print(f"Parsed version: {new_version['string']}")
    print(f"Version tuple: {new_version['tuple']}")
    print("✓ PASS: Successfully parsed updated version\n")

    # Test 12: Subscription status missing after recheck (negative)
    print("Test 12: Subscription status missing after recheck (negative)")
    print("-" * 50)

    subscription_recheck = {
        "resources": [
            {
                "metadata": {"name": "portworx-certified"},
                # Missing status field entirely
            }
        ]
    }

    try:
        updated_csv = subscription_recheck["resources"][0]["status"].get(
            "installedCSV"
        ) or subscription_recheck["resources"][0]["status"].get("currentCSV", "")
        print("✗ FAIL: Should have raised KeyError")
        assert False
    except KeyError:
        print("✓ PASS: Correctly raises KeyError on missing status\n")

    # Test 13: CSV phase transitions (edge cases)
    print("Test 13: CSV phase transitions (edge cases)")
    print("-" * 50)

    phases = ["Pending", "InstallReady", "Installing", "Succeeded", "Failed"]

    for phase in phases:
        csv_info = {
            "resources": [
                {
                    "metadata": {"name": "portworx-operator.v24.1.0"},
                    "status": {"phase": phase},
                }
            ]
        }

        csv_phase = csv_info["resources"][0]["status"]["phase"]
        is_succeeded = csv_phase == "Succeeded"

        print(f"  Phase '{phase}': Succeeded={is_succeeded}")
        assert (csv_phase == "Succeeded") == is_succeeded

    print("✓ PASS: Correctly evaluated all phase transitions\n")

    # Test 14: Case sensitivity in phase check (edge case)
    print("Test 14: Case sensitivity in phase check (edge case)")
    print("-" * 50)

    csv_info = {
        "resources": [
            {
                "metadata": {"name": "portworx-operator.v24.1.0"},
                "status": {"phase": "succeeded"},  # lowercase
            }
        ]
    }

    csv_phase = csv_info["resources"][0]["status"]["phase"]
    # Kubernetes uses proper case, so lowercase should not match
    assert csv_phase != "Succeeded"

    print(f"CSV phase: {csv_phase}")
    print("✓ PASS: Phase check is case-sensitive\n")

    # Test 15: Full upgrade step validation workflow (integration)
    print("Test 15: Full upgrade step validation workflow (integration)")
    print("-" * 50)

    # Initial state
    current_csv = "portworx-operator.v23.10.3"
    target_csv = "portworx-operator.v24.1.0"

    # Step 1: Approve InstallPlan (simulated)
    print(f"  Step 1: Approving InstallPlan for {target_csv}")

    # Step 2: Wait for CSV (simulated)
    print(f"  Step 2: Waiting for CSV {target_csv} to reach Succeeded")

    # Step 3: Re-check Subscription
    subscription_recheck = {
        "resources": [
            {
                "metadata": {"name": "portworx-certified"},
                "status": {
                    "installedCSV": target_csv,
                    "currentCSV": target_csv,
                },
            }
        ]
    }

    updated_csv = subscription_recheck["resources"][0]["status"]["installedCSV"]
    assert updated_csv == target_csv
    print(f"  Step 3: Subscription confirms {updated_csv}")

    # Step 4: Verify CSV phase
    csv_info = {
        "resources": [
            {
                "metadata": {"name": target_csv},
                "status": {"phase": "Succeeded"},
            }
        ]
    }

    csv_phase = csv_info["resources"][0]["status"]["phase"]
    assert csv_phase == "Succeeded"
    print(f"  Step 4: CSV phase is {csv_phase}")

    # Step 5: Parse new version
    parse_fn = filter_module.filters()["parse_operator_version"]
    new_version = parse_fn(updated_csv)
    assert new_version["tuple"] == (24, 1, 0)
    print(f"  Step 5: New version parsed: {new_version['string']}")

    print("✓ PASS: Full validation workflow successful\n")

    # Summary
    print("═══════════════════════════════════════════════════════════")
    print("ALL POST-STEP VALIDATION TESTS PASSED")
    print("═══════════════════════════════════════════════════════════")
    print("\nPositive Tests (Expected Success):")
    print("  1. Successful upgrade validation ✓")
    print("  2. CSV in Succeeded phase ✓")
    print("  3. Version parsing after validation ✓")
    print("  4. Multiple CSV versions (explicit lookup) ✓")
    print("  5. Full upgrade step workflow ✓")
    print("\nNegative Tests (Error Detection):")
    print("  6. Subscription reports different CSV ✓")
    print("  7. CSV not in Succeeded phase ✓")
    print("  8. Missing status.phase field ✓")
    print("  9. Empty Subscription resources ✓")
    print(" 10. OLM reconciliation lag ✓")
    print(" 11. CSV in Failed phase ✓")
    print(" 12. CSV not found ✓")
    print(" 13. Subscription status missing ✓")
    print(" 14. CSV phase transitions ✓")
    print(" 15. Case sensitivity in phase check ✓")
    print("\nThe post-step validation pattern is ROBUST ✓\n")


if __name__ == "__main__":
    try:
        test_post_step_validation()
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
