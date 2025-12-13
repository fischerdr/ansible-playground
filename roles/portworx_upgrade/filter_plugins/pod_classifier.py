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
  - Optimized for large clusters (250+ nodes) replacing multiple Ansible loops
  - Provides significant performance improvement over Jinja2 filter chains
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
notes:
  - Designed for use in AAP with Ansible Core 2.18.4
  - Replaces 250+ loop iterations with single Python function call
  - Pod names change during rolling upgrades (DaemonSet RollingUpdate strategy)
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
"""

RETURN = r"""
_value:
  description: Classification results or pod readiness status
  type: dict|bool
  returned: always
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
