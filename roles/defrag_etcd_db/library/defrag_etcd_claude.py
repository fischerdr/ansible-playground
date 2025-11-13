#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Your Organization
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: etcd_defrag
short_description: Defragment etcd database members
version_added: "1.0.0"
description:
    - This module defragments etcd database members in an OpenShift cluster.
    - It ensures non-leader members are defragmented first, with the leader defragmented last.
    - Uses the Kubernetes Python client for API interactions.
options:
    kubeconfig:
        description:
            - Path to the kubeconfig file
            - If not provided, will attempt to use in-cluster config or default kubeconfig
        required: false
        type: path
    context:
        description:
            - The name of a context found in the kubeconfig file
        required: false
        type: str
    etcd_cmd_timeout:
        description:
            - Timeout in seconds for etcd commands
        required: true
        type: int
    member_list:
        description:
            - Comma-separated list of etcd member pod names to defragment
            - If not provided, all etcd pods will be discovered and defragmented
        required: false
        type: str
    namespace:
        description:
            - Namespace where etcd pods are running
        required: false
        type: str
        default: openshift-etcd
author:
    - Your Name (@yourhandle)
requirements:
    - python >= 3.6
    - kubernetes >= 12.0.0
"""

EXAMPLES = r"""
- name: Defragment all etcd members
  etcd_defrag:
    kubeconfig: /root/clusters/my-cluster/install/auth/kubeconfig
    etcd_cmd_timeout: 30

- name: Defragment specific etcd members
  etcd_defrag:
    kubeconfig: /root/clusters/my-cluster/install/auth/kubeconfig
    etcd_cmd_timeout: 30
    member_list: "etcd-0,etcd-1,etcd-2"

- name: Defragment with custom context
  etcd_defrag:
    kubeconfig: /root/clusters/my-cluster/install/auth/kubeconfig
    context: my-context
    etcd_cmd_timeout: 30
    namespace: openshift-etcd
"""

RETURN = r"""
msg:
    description: Status message about the defragmentation process
    type: str
    returned: always
    sample: "Defragmentation completed for 3 members"
completed_members:
    description: List of successfully defragmented members
    type: list
    returned: always
    sample: ["etcd-0", "etcd-1", "etcd-2"]
"""

import time

from ansible.module_utils.basic import AnsibleModule

try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
    from kubernetes.stream import stream

    HAS_KUBERNETES = True
except ImportError:
    HAS_KUBERNETES = False


class EtcdDefragController:
    """Controller for managing etcd defragmentation operations."""

    def __init__(self, module):
        self.module = module
        self.etcd_cmd_timeout = module.params["etcd_cmd_timeout"]
        self.member_list = module.params.get("member_list")
        self.namespace = module.params["namespace"]

        # Initialize Kubernetes client
        self._init_k8s_client()

        self.core_v1 = client.CoreV1Api()

    def _init_k8s_client(self):
        """Initialize Kubernetes client with provided or default configuration."""
        kubeconfig = self.module.params.get("kubeconfig")
        context = self.module.params.get("context")

        try:
            if kubeconfig:
                config.load_kube_config(config_file=kubeconfig, context=context)
            else:
                # Try in-cluster config first, then default kubeconfig
                try:
                    config.load_incluster_config()
                except config.ConfigException:
                    config.load_kube_config(context=context)
        except Exception as e:
            self.module.fail_json(
                msg=f"Failed to load Kubernetes configuration: {str(e)}"
            )

    def exec_in_pod(self, pod_name, command):
        """Execute a command in a pod and return the output."""
        try:
            resp = stream(
                self.core_v1.connect_get_namespaced_pod_exec,
                pod_name,
                self.namespace,
                command=command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
                _preload_content=False,
            )

            output = ""
            error = ""

            # Read the response
            while resp.is_open():
                resp.update(timeout=self.etcd_cmd_timeout)
                if resp.peek_stdout():
                    output += resp.read_stdout()
                if resp.peek_stderr():
                    error += resp.read_stderr()

            resp.close()

            # Check if command failed based on exit code
            if error and "error" in error.lower():
                raise Exception(f"Command error: {error}")

            return output.strip()

        except ApiException as e:
            self.module.fail_json(
                msg=f"Failed to execute command in pod {pod_name}",
                error=str(e),
                command=command,
            )
        except Exception as e:
            self.module.fail_json(
                msg=f"Error executing command in pod {pod_name}",
                error=str(e),
                command=command,
            )

    def get_etcd_member_list(self):
        """Get list of etcd pod names."""
        if self.member_list:
            return [m.strip() for m in self.member_list.split(",") if m.strip()]

        try:
            # List pods with label selector
            pods = self.core_v1.list_namespaced_pod(
                namespace=self.namespace, label_selector="app=etcd"
            )

            if not pods.items:
                self.module.fail_json(
                    msg=f"No etcd pods found in namespace {self.namespace}"
                )

            return [pod.metadata.name for pod in pods.items]

        except ApiException as e:
            self.module.fail_json(
                msg=f"Failed to list etcd pods in namespace {self.namespace}",
                error=str(e),
            )

    def get_leader_name(self, member):
        """Identify the current etcd leader name."""
        try:
            # Get endpoint status in JSON format to find leader ID
            status_cmd = [
                "/bin/sh",
                "-c",
                f"etcdctl endpoint status -w json --command-timeout={self.etcd_cmd_timeout}s 2>/dev/null",
            ]
            status_output = self.exec_in_pod(member, status_cmd)

            if not status_output:
                return None

            # Parse JSON output to find leader ID
            import json

            status_data = json.loads(status_output)

            # Get leader ID from any endpoint (they all report the same leader)
            leader_id = None
            if isinstance(status_data, list) and len(status_data) > 0:
                leader_id = status_data[0].get("Status", {}).get("leader")

            if not leader_id:
                return None

            # Get member list in JSON format to find leader name
            member_cmd = [
                "/bin/sh",
                "-c",
                f"etcdctl member list -w json --command-timeout={self.etcd_cmd_timeout}s 2>/dev/null",
            ]
            member_output = self.exec_in_pod(member, member_cmd)

            if not member_output:
                return None

            # Parse JSON to find the member name matching the leader ID
            member_data = json.loads(member_output)
            members = member_data.get("members", [])

            for m in members:
                if m.get("ID") == leader_id:
                    return m.get("name")

            return None

        except Exception as e:
            self.module.warn(
                f"Could not determine leader status for {member}: {str(e)}"
            )
            return None

    def is_leader(self, member):
        """Check if a member is the current leader."""
        try:
            leader_name = self.get_leader_name(member)
            return leader_name and leader_name in member
        except Exception as e:
            self.module.warn(
                f"Could not determine leader status for {member}: {str(e)}"
            )
            return False

    def defrag_member(self, member):
        """Defragment a single etcd member."""
        defrag_cmd = [
            "/bin/sh",
            "-c",
            f"unset ETCDCTL_ENDPOINTS && "
            f"etcdctl --endpoints=https://localhost:2379 defrag "
            f"--command-timeout={self.etcd_cmd_timeout}s 2>/dev/null",
        ]

        try:
            self.exec_in_pod(member, defrag_cmd)
            time.sleep(60)  # Wait for cluster to stabilize
            return True
        except Exception as e:
            self.module.fail_json(
                msg=f"Defragmentation failed for {member}", error=str(e)
            )
            return False

    def defrag_non_leader(self, member):
        """Defragment a member only if it's not the leader."""
        if not self.is_leader(member):
            return self.defrag_member(member)
        return False

    def defrag_all_members(self):
        """Defragment all etcd members with leader last."""
        etcd_members = self.get_etcd_member_list()
        member_count = len(etcd_members)

        if member_count == 0:
            self.module.fail_json(msg="No etcd members found to defragment")

        completed_members = []
        non_leader_target = member_count - 1
        max_retries = member_count * 2
        retry_count = 0

        # Phase 1: Defragment non-leader members
        while len(completed_members) < non_leader_target and retry_count < max_retries:
            retry_count += 1

            for member in etcd_members:
                if member not in completed_members:
                    if self.defrag_non_leader(member):
                        completed_members.append(member)

                    # Break early if we've completed all non-leaders
                    if len(completed_members) >= non_leader_target:
                        break

        if len(completed_members) < non_leader_target:
            self.module.fail_json(
                msg="Failed to defragment all non-leader members within retry limit",
                completed_members=completed_members,
                expected=non_leader_target,
            )

        # Phase 2: Defragment the leader (or remaining member)
        for member in etcd_members:
            if member not in completed_members:
                if self.defrag_member(member):
                    completed_members.append(member)

        # Verify all members were defragmented
        if len(completed_members) != member_count:
            self.module.fail_json(
                msg="Not all members were defragmented",
                completed_members=completed_members,
                expected=member_count,
            )

        return completed_members


def main():
    module = AnsibleModule(
        argument_spec=dict(
            kubeconfig=dict(type="path", required=False),
            context=dict(type="str", required=False),
            etcd_cmd_timeout=dict(type="int", required=True),
            member_list=dict(type="str", required=False, default=None),
            namespace=dict(type="str", required=False, default="openshift-etcd"),
        ),
        supports_check_mode=False,
    )

    if not HAS_KUBERNETES:
        module.fail_json(
            msg="The kubernetes python module is required. "
            "Install it with: pip install kubernetes"
        )

    controller = EtcdDefragController(module)

    try:
        completed_members = controller.defrag_all_members()

        module.exit_json(
            changed=True,
            msg=f"Defragmentation completed for {len(completed_members)} members",
            completed_members=completed_members,
        )
    except Exception as e:
        module.fail_json(msg=f"Defragmentation failed: {str(e)}")


if __name__ == "__main__":
    main()
