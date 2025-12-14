#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, MasterControl <your.email@example.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
filter: pod_classifier
author: MasterControl (@yourgithub)
version_added: "1.0.0"
short_description: Efficient Portworx pod classification for large-scale clusters
description:
  - Classifies Portworx pods by upgrade status in a single pass
  - Separates storage and storageless pods based on pod labels
  - Determines pod readiness status
  - Optimized for large clusters (250+ nodes) replacing multiple Ansible loops
  - Provides significant performance improvement over Jinja2 filter chains
filters:
  classify_portworx_pods:
    description: Classify pods by upgrade status
    options:
      _input:
        description: List of pod dictionaries from kubernetes.core.k8s_info
        type: list
        required: true
      target_version:
        description: Target Portworx version string
        type: str
        required: true
      active_phases:
        description: Pod phases indicating active upgrade
        type: list
        required: false
        default: ['Terminating', 'Pending', 'ContainerCreating']
    returns:
      description: Dictionary with classified pod lists
      type: dict
      keys:
        upgraded:
          description: Pods with new image and Ready status
          type: list
        old_image:
          description: Pods still on old image version
          type: list
        upgrading:
          description: Pods in transition phases
          type: list
        new_not_ready:
          description: Pods with new image but not Ready
          type: list
  classify_pods_by_storage:
    description: Separate storage and storageless pods based on pod labels
    options:
      _input:
        description: List of pod dictionaries from kubernetes.core.k8s_info
        type: list
        required: true
    returns:
      description: Dictionary with storage classification
      type: dict
      keys:
        storage:
          description: Pods with storage="true" label
          type: list
        storageless:
          description: Pods without storage label
          type: list
  check_pod_ready:
    description: Check if a single pod has Ready=True condition
    options:
      _input:
        description: Single pod dictionary
        type: dict
        required: true
    returns:
      description: True if pod is Ready, False otherwise
      type: bool
  classify_pods_by_readiness:
    description: Separate pods into ready and not-ready lists
    options:
      _input:
        description: List of pod dictionaries
        type: list
        required: true
    returns:
      description: Dictionary with readiness classification
      type: dict
      keys:
        ready:
          description: Pods with Ready=True condition
          type: list
        not_ready:
          description: Pods not in Ready state
          type: list
notes:
  - Designed for use in AAP with Ansible Core 2.18.4
  - Replaces 250+ loop iterations with single Python function call
  - Pod names change during rolling upgrades (DaemonSet RollingUpdate strategy)
  - Storage vs storageless determined by pod label, not node annotations
  - Critical for impatient mode safety checks to prevent data loss
seealso:
  - module: kubernetes.core.k8s_info
  - module: kubernetes.core.k8s_exec
"""

EXAMPLES = r"""
# Classify pods during upgrade monitoring
- name: Classify all pods efficiently
  set_fact:
    classified_pods: >-
      {{ portworx_pods.resources |
         classify_portworx_pods(portworx_target_version, portworx_active_upgrade_phases) }}

# Check pod readiness status
- name: Check if pod is ready
  debug:
    msg: "Pod is ready: {{ my_pod | check_pod_ready }}"

# Separate pods by readiness
- name: Get not-ready pods
  set_fact:
    not_ready_pods: "{{ all_pods | classify_pods_by_readiness | json_query('not_ready') }}"

# Classify pods by storage type (storage vs storageless)
- name: Separate storage and storageless pods
  set_fact:
    pod_storage_classification: "{{ all_pods | classify_pods_by_storage }}"

# Get only storage pods
- name: Extract storage pods
  set_fact:
    storage_pods: "{{ all_pods | classify_pods_by_storage | json_query('storage') }}"

# Get only storageless pods for impatient mode
- name: Extract storageless pods
  set_fact:
    storageless_pods: "{{ all_pods | classify_pods_by_storage | json_query('storageless') }}"

# Verify storage pods upgraded before impatient mode
- name: Safety check for impatient mode
  set_fact:
    storage_pods_pending: >-
      {{ pods_with_old_image | classify_pods_by_storage | json_query('storage') }}

- name: Ensure safe to use impatient mode
  assert:
    that:
      - storage_pods_pending | length == 0
    fail_msg: "Cannot use impatient mode - storage pods still pending"
"""

RETURN = r"""
_value:
  description: Classification results or pod readiness status
  type: dict|bool
  returned: always
  sample:
    # classify_portworx_pods returns
    upgraded: [{metadata: {name: "portworx-1"}, ...}]
    old_image: [{metadata: {name: "portworx-2"}, ...}]
    upgrading: [{metadata: {name: "portworx-3"}, ...}]
    new_not_ready: [{metadata: {name: "portworx-4"}, ...}]

    # check_pod_ready returns
    true

    # classify_pods_by_readiness returns
    ready: [{metadata: {name: "portworx-1"}, ...}]
    not_ready: [{metadata: {name: "portworx-2"}, ...}]

    # classify_pods_by_storage returns
    storage: [{metadata: {name: "portworx-storage-1", labels: {storage: "true"}}, ...}]
    storageless: [{metadata: {name: "portworx-storageless-1"}, ...}]
"""

from ansible.errors import AnsibleFilterError


class FilterModule(object):
    """Ansible filter plugin for Portworx pod classification"""

    def filters(self):
        """
        Return filter mapping dictionary

        Returns:
            dict: Mapping of filter names to filter methods
        """
        return {
            "classify_portworx_pods": self.classify_portworx_pods,
            "check_pod_ready": self.check_pod_ready,
            "classify_pods_by_readiness": self.classify_pods_by_readiness,
            "classify_pods_by_storage": self.classify_pods_by_storage,
        }

    @staticmethod
    def classify_portworx_pods(pods, target_version, active_phases=None):  # noqa: C901
        """
        Classify Portworx pods by upgrade status in a single pass

        Replaces multiple Ansible loops and filter chains with a single
        Python function call, providing significant performance improvement
        for large clusters.

        Args:
            pods (list): List of pod dictionaries from kubernetes.core.k8s_info
            target_version (str): Target Portworx version (e.g., "3.1.0")
            active_phases (list, optional): Pod phases indicating active upgrade

        Returns:
            dict: Classification results with keys:
                - upgraded: Pods with new image and Ready
                - old_image: Pods still on old version
                - upgrading: Pods in active upgrade phases
                - new_not_ready: Pods with new image but not yet Ready

        Raises:
            AnsibleFilterError: If inputs are invalid
        """
        if not isinstance(pods, (list, tuple)):
            raise AnsibleFilterError(
                f"classify_portworx_pods requires list, got {type(pods).__name__}"
            )

        if not isinstance(target_version, str):
            raise AnsibleFilterError(
                f"classify_portworx_pods target_version must be string, "
                f"got {type(target_version).__name__}"
            )

        if not target_version:
            raise AnsibleFilterError(
                "classify_portworx_pods requires non-empty target_version"
            )

        if active_phases is None:
            active_phases = ["Terminating", "Pending", "ContainerCreating"]

        if not isinstance(active_phases, (list, tuple)):
            raise AnsibleFilterError(
                f"classify_portworx_pods active_phases must be list, "
                f"got {type(active_phases).__name__}"
            )

        result = {"upgraded": [], "old_image": [], "upgrading": [], "new_not_ready": []}

        for pod in pods:
            if not isinstance(pod, dict):
                continue

            # Extract pod attributes safely
            spec = pod.get("spec", {})
            status = pod.get("status", {})
            containers = spec.get("containers", [])

            if not containers:
                continue

            # Get image from first container (Portworx container)
            image = containers[0].get("image", "")
            phase = status.get("phase", "")
            conditions = status.get("conditions", [])

            # Check if pod has target version in image
            has_target_version = target_version in image

            # Check if pod is Running and Ready
            is_running = phase == "Running"
            is_ready = any(
                c.get("type") == "Ready" and c.get("status") == "True"
                for c in conditions
            )

            # Classify pod into appropriate category
            # Priority: active phases > upgraded > old image > new not ready
            if phase in active_phases:
                # Pod is actively upgrading (Terminating, Pending, etc.)
                result["upgrading"].append(pod)
            elif has_target_version and is_running and is_ready:
                # Pod has new image and is fully ready
                result["upgraded"].append(pod)
            elif not has_target_version:
                # Pod still has old image
                result["old_image"].append(pod)
            elif has_target_version:
                # Has new image but not Running+Ready
                result["new_not_ready"].append(pod)

        return result

    @staticmethod
    def check_pod_ready(pod):
        """
        Check if a single pod is Ready

        Args:
            pod (dict): Pod dictionary from kubernetes.core.k8s_info

        Returns:
            bool: True if pod has Ready=True condition, False otherwise

        Raises:
            AnsibleFilterError: If pod is not a dictionary
        """
        if not isinstance(pod, dict):
            raise AnsibleFilterError(
                f"check_pod_ready requires dict, got {type(pod).__name__}"
            )

        conditions = pod.get("status", {}).get("conditions", [])
        return any(
            c.get("type") == "Ready" and c.get("status") == "True" for c in conditions
        )

    def classify_pods_by_readiness(self, pods):
        """
        Separate pods into ready and not-ready lists

        Args:
            pods (list): List of pod dictionaries

        Returns:
            dict: Classification with keys 'ready' and 'not_ready'

        Raises:
            AnsibleFilterError: If pods is not a list
        """
        if not isinstance(pods, (list, tuple)):
            raise AnsibleFilterError(
                f"classify_pods_by_readiness requires list, got {type(pods).__name__}"
            )

        ready = []
        not_ready = []

        for pod in pods:
            if not isinstance(pod, dict):
                continue

            if self.check_pod_ready(pod):
                ready.append(pod)
            else:
                not_ready.append(pod)

        return {"ready": ready, "not_ready": not_ready}

    @staticmethod
    def classify_pods_by_storage(pods):
        """
        Separate pods into storage and storageless lists based on 'storage' label

        Storage pods have metadata.labels.storage="true"
        Storageless pods do not have the storage label

        Args:
            pods (list): List of pod dictionaries from kubernetes.core.k8s_info

        Returns:
            dict: Classification with keys 'storage' and 'storageless'
                - storage: List of pods with storage="true" label
                - storageless: List of pods without storage label

        Raises:
            AnsibleFilterError: If pods is not a list

        Examples:
            >>> pods = [
            ...     {"metadata": {"labels": {"storage": "true", "name": "portworx"}}},
            ...     {"metadata": {"labels": {"name": "portworx"}}}
            ... ]
            >>> classify_pods_by_storage(pods)
            {"storage": [pod1], "storageless": [pod2]}
        """
        if not isinstance(pods, (list, tuple)):
            raise AnsibleFilterError(
                f"classify_pods_by_storage requires list, got {type(pods).__name__}"
            )

        storage = []
        storageless = []

        for pod in pods:
            if not isinstance(pod, dict):
                continue

            labels = pod.get("metadata", {}).get("labels", {})

            # Storage pods have 'storage: "true"' label
            # Note: Check both presence AND value for safety
            if labels.get("storage") == "true":
                storage.append(pod)
            else:
                storageless.append(pod)

        return {"storage": storage, "storageless": storageless}
