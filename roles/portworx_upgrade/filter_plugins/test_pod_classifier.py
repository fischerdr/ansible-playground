#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for pod_classifier.py filter plugin

This script validates the filter plugin logic with mock pod data
before integration into the Ansible role.
"""

import sys

from pod_classifier import FilterModule


def create_mock_pod(name, image, phase, ready_status):
    """
    Create a mock pod dictionary matching Kubernetes pod resource structure

    Args:
        name (str): Pod name
        image (str): Container image
        phase (str): Pod phase (Running, Pending, etc.)
        ready_status (str): Ready condition status ("True" or "False")

    Returns:
        dict: Mock pod resource
    """
    pod = {
        "metadata": {"name": name},
        "spec": {"containers": [{"image": image}]},
        "status": {"phase": phase},
    }

    if ready_status:
        pod["status"]["conditions"] = [{"type": "Ready", "status": ready_status}]

    return pod


def test_classify_portworx_pods():
    """Test the classify_portworx_pods filter function"""
    print("\n=== Testing classify_portworx_pods ===")

    # Create mock pod data
    pods = [
        # Upgraded pods (new image, Running, Ready)
        create_mock_pod(
            "portworx-abc01", "portworx/oci-monitor:3.1.0", "Running", "True"
        ),
        create_mock_pod(
            "portworx-abc02", "portworx/oci-monitor:3.1.0", "Running", "True"
        ),
        # Old image pods
        create_mock_pod(
            "portworx-old01", "portworx/oci-monitor:3.0.0", "Running", "True"
        ),
        create_mock_pod(
            "portworx-old02", "portworx/oci-monitor:3.0.0", "Running", "True"
        ),
        # Actively upgrading pods (phase takes priority)
        create_mock_pod(
            "portworx-term01", "portworx/oci-monitor:3.0.0", "Terminating", None
        ),
        create_mock_pod(
            "portworx-pend01", "portworx/oci-monitor:3.1.0", "Pending", None
        ),
        create_mock_pod(
            "portworx-cont01", "portworx/oci-monitor:3.1.0", "ContainerCreating", None
        ),
        # New but not ready pods (new image, Running, but not Ready)
        create_mock_pod(
            "portworx-new01", "portworx/oci-monitor:3.1.0", "Running", "False"
        ),
        create_mock_pod(
            "portworx-new02", "portworx/oci-monitor:3.1.0", "Init:0/1", "False"
        ),
    ]

    target_version = "3.1.0"
    active_phases = ["Terminating", "Pending", "ContainerCreating"]

    # Run classification
    filter_module = FilterModule()
    classify_func = filter_module.filters()["classify_portworx_pods"]
    result = classify_func(pods, target_version, active_phases)

    # Validate results
    # Note: Filter plugin uses priority-based classification (phase > ready > image)
    # Pods in active_phases are ALWAYS classified as "upgrading" regardless of image
    assert (
        len(result["upgraded"]) == 2
    ), f"Expected 2 upgraded pods, got {len(result['upgraded'])}"
    assert (
        len(result["old_image"]) == 2
    ), f"Expected 2 old_image pods, got {len(result['old_image'])}"
    assert (
        len(result["upgrading"]) == 3
    ), f"Expected 3 upgrading pods, got {len(result['upgrading'])}"
    assert (
        len(result["new_not_ready"]) == 2
    ), f"Expected 2 new_not_ready pods, got {len(result['new_not_ready'])}"

    print("✓ classify_portworx_pods: All pods classified correctly")

    # Verify specific pod names
    upgraded_names = [p["metadata"]["name"] for p in result["upgraded"]]
    assert "portworx-abc01" in upgraded_names
    assert "portworx-abc02" in upgraded_names

    old_names = [p["metadata"]["name"] for p in result["old_image"]]
    assert "portworx-old01" in old_names
    assert "portworx-old02" in old_names

    upgrading_names = [p["metadata"]["name"] for p in result["upgrading"]]
    assert "portworx-term01" in upgrading_names
    assert "portworx-pend01" in upgrading_names
    assert "portworx-cont01" in upgrading_names

    new_not_ready_names = [p["metadata"]["name"] for p in result["new_not_ready"]]
    assert "portworx-new01" in new_not_ready_names
    assert "portworx-new02" in new_not_ready_names

    print("✓ classify_portworx_pods: Pod names verified in correct categories")


def test_check_pod_ready():
    """Test the check_pod_ready filter function"""
    print("\n=== Testing check_pod_ready ===")

    filter_module = FilterModule()
    check_func = filter_module.filters()["check_pod_ready"]

    # Test ready pod
    ready_pod = create_mock_pod(
        "ready-pod", "portworx/oci-monitor:3.1.0", "Running", "True"
    )
    assert check_func(ready_pod) is True, "Expected ready pod to return True"
    print("✓ check_pod_ready: Ready pod detected correctly")

    # Test not ready pod
    not_ready_pod = create_mock_pod(
        "not-ready-pod", "portworx/oci-monitor:3.1.0", "Running", "False"
    )
    assert check_func(not_ready_pod) is False, "Expected not-ready pod to return False"
    print("✓ check_pod_ready: Not-ready pod detected correctly")

    # Test pod without conditions
    no_conditions_pod = create_mock_pod(
        "no-cond-pod", "portworx/oci-monitor:3.1.0", "Pending", None
    )
    assert (
        check_func(no_conditions_pod) is False
    ), "Expected pod without conditions to return False"
    print("✓ check_pod_ready: Pod without conditions detected correctly")


def test_classify_pods_by_readiness():
    """Test the classify_pods_by_readiness filter function"""
    print("\n=== Testing classify_pods_by_readiness ===")

    # Create mixed pod data
    pods = [
        create_mock_pod("ready-01", "portworx/oci-monitor:3.1.0", "Running", "True"),
        create_mock_pod("ready-02", "portworx/oci-monitor:3.1.0", "Running", "True"),
        create_mock_pod("ready-03", "portworx/oci-monitor:3.1.0", "Running", "True"),
        create_mock_pod(
            "not-ready-01", "portworx/oci-monitor:3.1.0", "Running", "False"
        ),
        create_mock_pod("not-ready-02", "portworx/oci-monitor:3.1.0", "Pending", None),
    ]

    filter_module = FilterModule()
    classify_func = filter_module.filters()["classify_pods_by_readiness"]
    result = classify_func(pods)

    assert (
        len(result["ready"]) == 3
    ), f"Expected 3 ready pods, got {len(result['ready'])}"
    assert (
        len(result["not_ready"]) == 2
    ), f"Expected 2 not-ready pods, got {len(result['not_ready'])}"

    print("✓ classify_pods_by_readiness: Pods separated correctly")

    # Verify specific pod names
    ready_names = [p["metadata"]["name"] for p in result["ready"]]
    assert all(name.startswith("ready-") for name in ready_names)

    not_ready_names = [p["metadata"]["name"] for p in result["not_ready"]]
    assert all(name.startswith("not-ready-") for name in not_ready_names)

    print("✓ classify_pods_by_readiness: Pod names verified in correct categories")


def test_error_handling():  # noqa: C901
    """Test error handling in filter functions"""
    print("\n=== Testing Error Handling ===")

    filter_module = FilterModule()
    classify_func = filter_module.filters()["classify_portworx_pods"]
    check_func = filter_module.filters()["check_pod_ready"]
    readiness_func = filter_module.filters()["classify_pods_by_readiness"]

    # Test classify_portworx_pods with invalid inputs
    try:
        classify_func("not a list", "3.1.0")
        assert False, "Should have raised AnsibleFilterError for non-list pods"
    except Exception as e:
        assert "requires list" in str(e)
        print("✓ classify_portworx_pods: Raises error for non-list input")

    try:
        classify_func([], "")
        assert False, "Should have raised AnsibleFilterError for empty target_version"
    except Exception as e:
        assert "non-empty" in str(e)
        print("✓ classify_portworx_pods: Raises error for empty target_version")

    try:
        classify_func([], 123)
        assert (
            False
        ), "Should have raised AnsibleFilterError for non-string target_version"
    except Exception as e:
        assert "string" in str(e)
        print("✓ classify_portworx_pods: Raises error for non-string target_version")

    # Test check_pod_ready with invalid input
    try:
        check_func("not a dict")
        assert False, "Should have raised AnsibleFilterError for non-dict pod"
    except Exception as e:
        assert "requires dict" in str(e)
        print("✓ check_pod_ready: Raises error for non-dict input")

    # Test classify_pods_by_readiness with invalid input
    try:
        readiness_func("not a list")
        assert False, "Should have raised AnsibleFilterError for non-list pods"
    except Exception as e:
        assert "requires list" in str(e)
        print("✓ classify_pods_by_readiness: Raises error for non-list input")


def test_edge_cases():
    """Test edge cases and unusual pod states"""
    print("\n=== Testing Edge Cases ===")

    filter_module = FilterModule()
    classify_func = filter_module.filters()["classify_portworx_pods"]

    # Test with empty pod list
    result = classify_func([], "3.1.0")
    assert len(result["upgraded"]) == 0
    assert len(result["old_image"]) == 0
    assert len(result["upgrading"]) == 0
    assert len(result["new_not_ready"]) == 0
    print("✓ classify_portworx_pods: Handles empty pod list")

    # Test with pods missing containers
    pods_no_containers = [
        {"metadata": {"name": "broken-pod"}, "spec": {}, "status": {"phase": "Running"}}
    ]
    result = classify_func(pods_no_containers, "3.1.0")
    assert len(result["upgraded"]) == 0
    assert len(result["old_image"]) == 0
    assert len(result["upgrading"]) == 0
    assert len(result["new_not_ready"]) == 0
    print("✓ classify_portworx_pods: Handles pods without containers")

    # Test with non-dict items in list (should skip them)
    mixed_list = [
        create_mock_pod("good-pod", "portworx/oci-monitor:3.1.0", "Running", "True"),
        "bad item",
        None,
        create_mock_pod("good-pod-2", "portworx/oci-monitor:3.0.0", "Running", "True"),
    ]
    result = classify_func(mixed_list, "3.1.0")
    assert len(result["upgraded"]) == 1
    assert len(result["old_image"]) == 1
    print("✓ classify_portworx_pods: Skips non-dict items in list")

    # Test with custom active_phases
    pods = [
        create_mock_pod(
            "custom-phase", "portworx/oci-monitor:3.1.0", "CustomPhase", None
        )
    ]
    result = classify_func(pods, "3.1.0", ["CustomPhase"])
    assert len(result["upgrading"]) == 1
    print("✓ classify_portworx_pods: Respects custom active_phases")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Pod Classifier Filter Plugin Test Suite")
    print("=" * 60)

    try:
        test_classify_portworx_pods()
        test_check_pod_ready()
        test_classify_pods_by_readiness()
        test_error_handling()
        test_edge_cases()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
