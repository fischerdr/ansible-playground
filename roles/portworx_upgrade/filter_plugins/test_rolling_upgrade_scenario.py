#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script simulating a rolling upgrade scenario

This test validates that the filter plugin correctly handles the pod
lifecycle during a DaemonSet rolling upgrade where:
1. Old pods with old image are Running+Ready
2. Old pods transition to Terminating phase
3. New pods are created with new names in Pending phase
4. New pods transition to ContainerCreating
5. New pods transition to Running but not Ready
6. New pods become Running+Ready (upgrade complete for that pod)
"""

import sys

from pod_classifier import FilterModule


def create_pod(name, image, phase, ready_status):
    """Create a mock Kubernetes pod resource"""
    pod = {
        "metadata": {"name": name},
        "spec": {"containers": [{"image": image}]},
        "status": {"phase": phase},
    }

    if ready_status:
        pod["status"]["conditions"] = [{"type": "Ready", "status": ready_status}]

    return pod


def test_initial_state():
    """
    Test Cycle 0: All pods on old version, all ready
    This is the starting state before upgrade begins
    """
    print("\n=== Cycle 0: Pre-Upgrade (All pods old version) ===")

    pods = [
        create_pod(
            "portworx-node1-abc123", "portworx/oci-monitor:3.0.0", "Running", "True"
        ),
        create_pod(
            "portworx-node2-def456", "portworx/oci-monitor:3.0.0", "Running", "True"
        ),
        create_pod(
            "portworx-node3-ghi789", "portworx/oci-monitor:3.0.0", "Running", "True"
        ),
    ]

    fm = FilterModule()
    result = fm.filters()["classify_portworx_pods"](
        pods, "3.1.0", ["Terminating", "Pending", "ContainerCreating"]
    )

    assert len(result["upgraded"]) == 0, "No pods should be upgraded yet"
    assert len(result["old_image"]) == 3, "All 3 pods should have old image"
    assert len(result["upgrading"]) == 0, "No pods should be upgrading"
    assert len(result["new_not_ready"]) == 0, "No new pods yet"

    print(f"✓ Upgraded: {len(result['upgraded'])}")
    print(f"✓ Old image: {len(result['old_image'])}")
    print(f"✓ Upgrading: {len(result['upgrading'])}")
    print(f"✓ New not ready: {len(result['new_not_ready'])}")


def test_first_pod_terminating():
    """
    Test Cycle 1: First pod starts terminating
    Kubernetes begins the rolling update by terminating first pod
    """
    print("\n=== Cycle 1: First pod terminating ===")

    pods = [
        create_pod(
            "portworx-node1-abc123", "portworx/oci-monitor:3.0.0", "Terminating", None
        ),
        create_pod(
            "portworx-node2-def456", "portworx/oci-monitor:3.0.0", "Running", "True"
        ),
        create_pod(
            "portworx-node3-ghi789", "portworx/oci-monitor:3.0.0", "Running", "True"
        ),
    ]

    fm = FilterModule()
    result = fm.filters()["classify_portworx_pods"](
        pods, "3.1.0", ["Terminating", "Pending", "ContainerCreating"]
    )

    assert len(result["upgraded"]) == 0, "No pods upgraded yet"
    assert len(result["old_image"]) == 2, "Two pods still have old image"
    assert len(result["upgrading"]) == 1, "One pod is terminating"
    assert len(result["new_not_ready"]) == 0, "No new pods yet"

    print(f"✓ Upgraded: {len(result['upgraded'])}")
    print(f"✓ Old image: {len(result['old_image'])}")
    print(
        f"✓ Upgrading: {len(result['upgrading'])} (portworx-node1-abc123 Terminating)"
    )
    print(f"✓ New not ready: {len(result['new_not_ready'])}")


def test_new_pod_pending():
    """
    Test Cycle 2: Old pod gone, new pod created in Pending state
    DaemonSet creates new pod with NEW NAME
    """
    print("\n=== Cycle 2: New pod created (Pending) ===")

    pods = [
        # Old pod deleted, new pod created with different name!
        create_pod(
            "portworx-node1-xyz999", "portworx/oci-monitor:3.1.0", "Pending", None
        ),
        create_pod(
            "portworx-node2-def456", "portworx/oci-monitor:3.0.0", "Running", "True"
        ),
        create_pod(
            "portworx-node3-ghi789", "portworx/oci-monitor:3.0.0", "Running", "True"
        ),
    ]

    fm = FilterModule()
    result = fm.filters()["classify_portworx_pods"](
        pods, "3.1.0", ["Terminating", "Pending", "ContainerCreating"]
    )

    assert len(result["upgraded"]) == 0, "No pods fully upgraded yet"
    assert len(result["old_image"]) == 2, "Two pods still on old version"
    assert len(result["upgrading"]) == 1, "One pod in Pending phase"
    assert len(result["new_not_ready"]) == 0, "Pending pods classified as upgrading"

    print(f"✓ Upgraded: {len(result['upgraded'])}")
    print(f"✓ Old image: {len(result['old_image'])}")
    print(f"✓ Upgrading: {len(result['upgrading'])} (portworx-node1-xyz999 Pending)")
    print(f"✓ New not ready: {len(result['new_not_ready'])}")


def test_new_pod_container_creating():
    """
    Test Cycle 3: New pod transitions to ContainerCreating
    """
    print("\n=== Cycle 3: New pod ContainerCreating ===")

    pods = [
        create_pod(
            "portworx-node1-xyz999",
            "portworx/oci-monitor:3.1.0",
            "ContainerCreating",
            None,
        ),
        create_pod(
            "portworx-node2-def456", "portworx/oci-monitor:3.0.0", "Running", "True"
        ),
        create_pod(
            "portworx-node3-ghi789", "portworx/oci-monitor:3.0.0", "Running", "True"
        ),
    ]

    fm = FilterModule()
    result = fm.filters()["classify_portworx_pods"](
        pods, "3.1.0", ["Terminating", "Pending", "ContainerCreating"]
    )

    assert len(result["upgraded"]) == 0
    assert len(result["old_image"]) == 2
    assert len(result["upgrading"]) == 1
    assert len(result["new_not_ready"]) == 0

    print(f"✓ Upgraded: {len(result['upgraded'])}")
    print(f"✓ Old image: {len(result['old_image'])}")
    print(f"✓ Upgrading: {len(result['upgrading'])} (ContainerCreating)")
    print(f"✓ New not ready: {len(result['new_not_ready'])}")


def test_new_pod_running_not_ready():
    """
    Test Cycle 4: New pod Running but not Ready
    Container started but readiness probe not passing yet
    """
    print("\n=== Cycle 4: New pod Running but not Ready ===")

    pods = [
        create_pod(
            "portworx-node1-xyz999", "portworx/oci-monitor:3.1.0", "Running", "False"
        ),
        create_pod(
            "portworx-node2-def456", "portworx/oci-monitor:3.0.0", "Running", "True"
        ),
        create_pod(
            "portworx-node3-ghi789", "portworx/oci-monitor:3.0.0", "Running", "True"
        ),
    ]

    fm = FilterModule()
    result = fm.filters()["classify_portworx_pods"](
        pods, "3.1.0", ["Terminating", "Pending", "ContainerCreating"]
    )

    assert len(result["upgraded"]) == 0, "Pod not ready yet"
    assert len(result["old_image"]) == 2, "Two pods still on old version"
    assert len(result["upgrading"]) == 0, "Not in active upgrade phase anymore"
    assert (
        len(result["new_not_ready"]) == 1
    ), "One pod Running with new image but not Ready"

    print(f"✓ Upgraded: {len(result['upgraded'])}")
    print(f"✓ Old image: {len(result['old_image'])}")
    print(f"✓ Upgrading: {len(result['upgrading'])}")
    print(f"✓ New not ready: {len(result['new_not_ready'])} (Running but Ready=False)")


def test_first_pod_upgraded():
    """
    Test Cycle 5: First pod fully upgraded (Running + Ready)
    This is the successful completion of one pod's upgrade
    """
    print("\n=== Cycle 5: First pod fully upgraded ===")

    pods = [
        create_pod(
            "portworx-node1-xyz999", "portworx/oci-monitor:3.1.0", "Running", "True"
        ),
        create_pod(
            "portworx-node2-def456", "portworx/oci-monitor:3.0.0", "Running", "True"
        ),
        create_pod(
            "portworx-node3-ghi789", "portworx/oci-monitor:3.0.0", "Running", "True"
        ),
    ]

    fm = FilterModule()
    result = fm.filters()["classify_portworx_pods"](
        pods, "3.1.0", ["Terminating", "Pending", "ContainerCreating"]
    )

    assert len(result["upgraded"]) == 1, "One pod fully upgraded"
    assert len(result["old_image"]) == 2, "Two pods still on old version"
    assert len(result["upgrading"]) == 0, "No active upgrades"
    assert len(result["new_not_ready"]) == 0, "New pod is ready"

    upgraded_names = [p["metadata"]["name"] for p in result["upgraded"]]
    assert (
        "portworx-node1-xyz999" in upgraded_names
    ), "New pod name should be in upgraded list"

    print(f"✓ Upgraded: {len(result['upgraded'])} (portworx-node1-xyz999)")
    print(f"✓ Old image: {len(result['old_image'])}")
    print(f"✓ Upgrading: {len(result['upgrading'])}")
    print(f"✓ New not ready: {len(result['new_not_ready'])}")


def test_multiple_pods_upgrading():
    """
    Test Cycle 6: Multiple pods upgrading simultaneously
    Rolling update continues with next pod while maintaining cluster health
    """
    print("\n=== Cycle 6: Multiple pods in different upgrade stages ===")

    pods = [
        # Node 1: Already upgraded (new name, new image, ready)
        create_pod(
            "portworx-node1-xyz999", "portworx/oci-monitor:3.1.0", "Running", "True"
        ),
        # Node 2: Old pod terminating
        create_pod(
            "portworx-node2-def456", "portworx/oci-monitor:3.0.0", "Terminating", None
        ),
        # Node 2: New pod starting (same node, new name)
        create_pod(
            "portworx-node2-aaa111", "portworx/oci-monitor:3.1.0", "Pending", None
        ),
        # Node 3: Still on old version, waiting
        create_pod(
            "portworx-node3-ghi789", "portworx/oci-monitor:3.0.0", "Running", "True"
        ),
    ]

    fm = FilterModule()
    result = fm.filters()["classify_portworx_pods"](
        pods, "3.1.0", ["Terminating", "Pending", "ContainerCreating"]
    )

    assert len(result["upgraded"]) == 1, "One pod fully upgraded"
    assert len(result["old_image"]) == 1, "One pod still on old version"
    assert (
        len(result["upgrading"]) == 2
    ), "Two pods actively upgrading (Terminating + Pending)"
    assert (
        len(result["new_not_ready"]) == 0
    ), "No new pods in Running but not Ready state"

    print(f"✓ Upgraded: {len(result['upgraded'])} (portworx-node1-xyz999)")
    print(f"✓ Old image: {len(result['old_image'])} (portworx-node3-ghi789)")
    print(f"✓ Upgrading: {len(result['upgrading'])} (Terminating + Pending)")
    print(f"✓ New not ready: {len(result['new_not_ready'])}")


def test_upgrade_complete():
    """
    Test Cycle N: All pods upgraded
    Final state - all pods have new image and are ready
    """
    print("\n=== Cycle N: Upgrade complete ===")

    pods = [
        # All new pods with new names, new image, all ready
        create_pod(
            "portworx-node1-xyz999", "portworx/oci-monitor:3.1.0", "Running", "True"
        ),
        create_pod(
            "portworx-node2-aaa111", "portworx/oci-monitor:3.1.0", "Running", "True"
        ),
        create_pod(
            "portworx-node3-bbb222", "portworx/oci-monitor:3.1.0", "Running", "True"
        ),
    ]

    fm = FilterModule()
    result = fm.filters()["classify_portworx_pods"](
        pods, "3.1.0", ["Terminating", "Pending", "ContainerCreating"]
    )

    assert len(result["upgraded"]) == 3, "All pods upgraded"
    assert len(result["old_image"]) == 0, "No pods with old image"
    assert len(result["upgrading"]) == 0, "No pods actively upgrading"
    assert len(result["new_not_ready"]) == 0, "All new pods ready"

    print(f"✓ Upgraded: {len(result['upgraded'])} (ALL PODS)")
    print(f"✓ Old image: {len(result['old_image'])}")
    print(f"✓ Upgrading: {len(result['upgrading'])}")
    print(f"✓ New not ready: {len(result['new_not_ready'])}")
    print("\n✅ UPGRADE COMPLETE - All pods on new version!")


def test_edge_case_stuck_pod():
    """
    Test edge case: Pod stuck in Running but not Ready for extended time
    This should be detected as new_not_ready
    """
    print("\n=== Edge Case: Pod stuck in Running but not Ready ===")

    pods = [
        create_pod(
            "portworx-node1-xyz999", "portworx/oci-monitor:3.1.0", "Running", "True"
        ),
        create_pod(
            "portworx-node2-aaa111", "portworx/oci-monitor:3.1.0", "Running", "False"
        ),  # Stuck
        create_pod(
            "portworx-node3-ghi789", "portworx/oci-monitor:3.0.0", "Running", "True"
        ),
    ]

    fm = FilterModule()
    result = fm.filters()["classify_portworx_pods"](
        pods, "3.1.0", ["Terminating", "Pending", "ContainerCreating"]
    )

    assert len(result["upgraded"]) == 1
    assert len(result["old_image"]) == 1
    assert len(result["upgrading"]) == 0
    assert len(result["new_not_ready"]) == 1, "Stuck pod should be in new_not_ready"

    print(f"✓ Upgraded: {len(result['upgraded'])}")
    print(f"✓ Old image: {len(result['old_image'])}")
    print(f"✓ Upgrading: {len(result['upgrading'])}")
    print(f"✓ New not ready: {len(result['new_not_ready'])} (Stuck pod detected)")


def main():
    """Run all rolling upgrade scenario tests"""
    print("=" * 70)
    print("Rolling Upgrade Scenario Test Suite")
    print("Simulating DaemonSet rolling update with pod name changes")
    print("=" * 70)

    try:
        test_initial_state()
        test_first_pod_terminating()
        test_new_pod_pending()
        test_new_pod_container_creating()
        test_new_pod_running_not_ready()
        test_first_pod_upgraded()
        test_multiple_pods_upgrading()
        test_upgrade_complete()
        test_edge_case_stuck_pod()

        print("\n" + "=" * 70)
        print("✓ ALL ROLLING UPGRADE SCENARIO TESTS PASSED")
        print("=" * 70)
        print("\nKey Validations:")
        print("  ✓ Pod name changes during rolling update handled correctly")
        print("  ✓ Pod phase transitions classified properly")
        print("  ✓ Multiple simultaneous upgrades tracked accurately")
        print("  ✓ Stuck pods detected in new_not_ready category")
        print("  ✓ Upgrade completion detected when all pods Ready")
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
