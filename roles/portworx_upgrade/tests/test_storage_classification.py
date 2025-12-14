#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for classify_pods_by_storage filter plugin

Tests the critical storage pod detection logic to prevent data loss
during impatient mode batch deletions.
"""

import sys
import os

# Add filter_plugins to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../filter_plugins'))

from pod_classifier import FilterModule


def test_storage_pod_detection():
    """Test that storage pods are correctly identified by label"""
    filter_module = FilterModule()

    pods = [
        {
            "metadata": {
                "name": "portworx-storage-1",
                "labels": {
                    "storage": "true",
                    "name": "portworx"
                }
            }
        },
        {
            "metadata": {
                "name": "portworx-storage-2",
                "labels": {
                    "storage": "true",
                    "name": "portworx"
                }
            }
        },
        {
            "metadata": {
                "name": "portworx-storageless-1",
                "labels": {
                    "name": "portworx"
                    # No storage label
                }
            }
        },
        {
            "metadata": {
                "name": "portworx-storageless-2",
                "labels": {
                    "name": "portworx"
                    # No storage label
                }
            }
        }
    ]

    result = filter_module.classify_pods_by_storage(pods)

    # Verify storage pods
    assert len(result['storage']) == 2, \
        f"Expected 2 storage pods, got {len(result['storage'])}"
    assert result['storage'][0]['metadata']['name'] == 'portworx-storage-1'
    assert result['storage'][1]['metadata']['name'] == 'portworx-storage-2'

    # Verify storageless pods
    assert len(result['storageless']) == 2, \
        f"Expected 2 storageless pods, got {len(result['storageless'])}"
    assert result['storageless'][0]['metadata']['name'] == 'portworx-storageless-1'
    assert result['storageless'][1]['metadata']['name'] == 'portworx-storageless-2'

    print("✓ Storage pod detection test passed")


def test_all_storage_pods():
    """Test with all storage pods"""
    filter_module = FilterModule()

    pods = [
        {
            "metadata": {
                "name": f"portworx-storage-{i}",
                "labels": {"storage": "true", "name": "portworx"}
            }
        }
        for i in range(10)
    ]

    result = filter_module.classify_pods_by_storage(pods)

    assert len(result['storage']) == 10
    assert len(result['storageless']) == 0

    print("✓ All storage pods test passed")


def test_all_storageless_pods():
    """Test with all storageless pods"""
    filter_module = FilterModule()

    pods = [
        {
            "metadata": {
                "name": f"portworx-storageless-{i}",
                "labels": {"name": "portworx"}
            }
        }
        for i in range(10)
    ]

    result = filter_module.classify_pods_by_storage(pods)

    assert len(result['storage']) == 0
    assert len(result['storageless']) == 10

    print("✓ All storageless pods test passed")


def test_storage_label_false_is_storageless():
    """Test that storage="false" is treated as storageless"""
    filter_module = FilterModule()

    pods = [
        {
            "metadata": {
                "name": "portworx-1",
                "labels": {"storage": "false", "name": "portworx"}
            }
        }
    ]

    result = filter_module.classify_pods_by_storage(pods)

    # storage label must be exactly "true" to be storage pod
    assert len(result['storage']) == 0
    assert len(result['storageless']) == 1

    print("✓ Storage label false test passed")


def test_empty_list():
    """Test with empty pod list"""
    filter_module = FilterModule()

    result = filter_module.classify_pods_by_storage([])

    assert len(result['storage']) == 0
    assert len(result['storageless']) == 0

    print("✓ Empty list test passed")


def test_mixed_large_cluster():
    """Test with large cluster (300 storageless + 30 storage)"""
    filter_module = FilterModule()

    storage_pods = [
        {
            "metadata": {
                "name": f"portworx-storage-{i}",
                "labels": {"storage": "true", "name": "portworx"}
            }
        }
        for i in range(30)
    ]

    storageless_pods = [
        {
            "metadata": {
                "name": f"portworx-storageless-{i}",
                "labels": {"name": "portworx"}
            }
        }
        for i in range(300)
    ]

    all_pods = storage_pods + storageless_pods

    result = filter_module.classify_pods_by_storage(all_pods)

    assert len(result['storage']) == 30
    assert len(result['storageless']) == 300
    assert len(result['storage']) + len(result['storageless']) == 330

    print("✓ Large cluster test passed (30 storage + 300 storageless)")


if __name__ == '__main__':
    print("\n=== Testing classify_pods_by_storage Filter ===\n")

    test_storage_pod_detection()
    test_all_storage_pods()
    test_all_storageless_pods()
    test_storage_label_false_is_storageless()
    test_empty_list()
    test_mixed_large_cluster()

    print("\n=== All Filter Plugin Tests Passed! ===\n")
