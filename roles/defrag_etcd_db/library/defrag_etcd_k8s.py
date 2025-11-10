#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# defrag_etcd_k8s.py
# Ansible module to defragment etcd members by executing etcdctl inside etcd pods (OpenShift)
# Updated for Ansible 2.18 and Python 3.11 with leader-aware ordering
# Uses Kubernetes Python client instead of oc commands
#
# Author: Senior Systems Automation Engineer
# License: Apache-2.0 (adjust as required)

from __future__ import annotations

import json
import time
from typing import List, Optional, Tuple, Dict

from ansible.module_utils.basic import AnsibleModule
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream

DOCUMENTATION = r"""
---
module: defrag_etcd_k8s
short_description: Defragment etcd DBs by executing etcdctl inside etcd pods (OpenShift)
description:
  - Run etcdctl defrag inside etcd pods using Kubernetes Python client.
  - The module attempts to defragment non-leader members first and the leader last.
  - Intended to run inside Ansible Execution Environments (EEs).
options:
  paas_cluster_name:
    description:
      - Optional cluster name (for logging/operational context).
    required: false
    type: str
    default: ""
  etcd_cmd_timeout:
    description:
      - Timeout in seconds for etcdctl commands executed inside pods.
    required: false
    type: int
    default: 20
  member_list:
    description:
      - List of etcd pod names to target. Can be provided as comma-separated string or Python list.
      - If omitted or empty, discovers pods in 'openshift-etcd' namespace automatically.
      - "Examples: 'etcd-0,etcd-1,etcd-2' or ['etcd-0', 'etcd-1', 'etcd-2']"
    required: false
    type: str
    default: ""
  kubeconfig:
    description:
      - Optional kubeconfig file path to use for Kubernetes connection.
      - If omitted, will try to use in-cluster configuration.
    required: false
    type: str
  wait_between_members:
    description:
      - Seconds to wait after a successful defrag of a member to allow the cluster to settle.
    required: false
    type: int
    default: 60
  max_retry_multiplier:
    description:
      - Multiplier to compute max_retries = max(3, member_count * max_retry_multiplier).
      - Prevents infinite retry loops while allowing some retries.
    required: false
    type: int
    default: 2
  debug:
    description:
      - If true, enable more verbose logging (module.log messages).
    required: false
    type: bool
    default: false
author:
  - Senior Systems Automation Engineer
"""

EXAMPLES = r"""
- name: Defrag etcd cluster (auto-discover pods)
  defrag_etcd_k8s:
    kubeconfig: /etc/kubeconfigs/prod.kubeconfig
    etcd_cmd_timeout: 30
    wait_between_members: 30

- name: Defrag explicit pods using comma-separated string
  defrag_etcd_k8s:
    member_list: "etcd-0,etcd-1,etcd-2"

- name: Defrag explicit pods using list (also supported)
  defrag_etcd_k8s:
    member_list: ["etcd-0", "etcd-1", "etcd-2"]

- name: Defrag with variable expansion (list from inventory)
  defrag_etcd_k8s:
    member_list: "{{ etcd_pods }}"
"""

RETURN = r"""
results:
  description: Per-member defragmentation results and summary.
  returned: always
  type: list
  elements: dict
changed:
  description: Whether any defragmentation operation changed state.
  returned: always
  type: bool
"""


class DefragController:
    def __init__(
        self,
        module: AnsibleModule,
        paas_cluster_name: Optional[str],
        etcd_cmd_timeout: int = 20,
        member_list: Optional[str] = None,
        kubeconfig: Optional[str] = None,
        wait_between_members: int = 60,
        max_retry_multiplier: int = 2,
        debug: bool = False,
    ):
        self.module = module
        self.paas_cluster_name = paas_cluster_name or ""
        self.etcd_cmd_timeout = int(etcd_cmd_timeout)

        # Handle both string (comma-separated) and list inputs for member_list
        self.member_list_param = member_list or ""
        if isinstance(self.member_list_param, list):
            # Input is already a list - use directly after stripping whitespace
            self.member_list = [str(m).strip() for m in self.member_list_param if m and str(m).strip()]
        elif isinstance(self.member_list_param, str):
            # Input is a string - split on comma
            self.member_list = [
                m.strip() for m in self.member_list_param.split(",") if m.strip()
            ]
        else:
            # Unexpected type - attempt string conversion and split
            self.member_list = [
                m.strip() for m in str(self.member_list_param).split(",") if m.strip()
            ]
        self.kubeconfig = kubeconfig
        self.wait_between_members = int(wait_between_members)
        self.max_retry_multiplier = int(max_retry_multiplier)
        self.debug = bool(debug)

        # results list of dicts
        self.results: List[Dict] = []
        
        # Initialize Kubernetes client
        self._init_k8s_client()
        
        if module.check_mode:
            module.exit_json(changed=False, results=[], skipped=True)

    def _init_k8s_client(self):
        """Initialize Kubernetes client based on kubeconfig or in-cluster config."""
        try:
            if self.kubeconfig:
                config.load_kube_config(config_file=self.kubeconfig)
            else:
                # Try to use in-cluster config
                config.load_incluster_config()
        except Exception as e:
            self.module.warn(f"Failed to initialize Kubernetes client: {str(e)}")
            # This will be handled later when trying to make requests

    # -------------------------
    # Discovery helpers
    # -------------------------
    def _discover_etcd_pods(self) -> List[str]:
        """Discover etcd pods in openshift-etcd namespace."""
        try:
            v1 = client.CoreV1Api()
            pods = v1.list_namespaced_pod(
                namespace="openshift-etcd",
                label_selector="app=etcd"
            )
            
            pod_names = [pod.metadata.name for pod in pods.items]
            if self.debug:
                self.module.log(msg=f"Discovered etcd pods: {pod_names}")
            return pod_names
        except ApiException as e:
            self.module.warn(f"Failed to list etcd pods: {e}")
            return []
        except Exception as e:
            self.module.warn(f"Unexpected error discovering pods: {e}")
            return []

    # -------------------------
    # Pod execution helpers
    # -------------------------
    def _execute_in_pod(self, pod_name: str, command: List[str], timeout_seconds: int = 30) -> Tuple[int, str, str]:
        """
        Execute command inside a pod using the Kubernetes Python client.
        Returns (return_code, stdout, stderr)
        """
        try:
            # Create the API instance
            v1 = client.CoreV1Api()
            
            # Use stream to execute the command
            resp = stream(
                v1.connect_get_namespaced_pod_exec,
                pod_name,
                "openshift-etcd",
                command=command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
                _request_timeout=timeout_seconds
            )
            
            # Return successful result - the response is already the stdout
            return 0, resp, ""
        except ApiException as e:
            if e.status == 404:
                return 1, "", f"Pod {pod_name} not found"
            elif e.status == 400:
                return 1, "", f"Bad request executing command in pod {pod_name}: {e.reason}"
            else:
                return 1, "", f"API error executing command in pod {pod_name}: {e}"
        except Exception as e:
            return 1, "", f"Unexpected error executing command in pod {pod_name}: {str(e)}"

    # -------------------------
    # Member list / endpoint status parsers
    # -------------------------
    def _get_member_list_via_etcdctl(self, pod: str) -> List[Dict]:
        """
        Call `etcdctl member list --write-out=json` inside the pod and return normalized list of dicts:
          [{'id': '123', 'name': 'etcd-0', 'peerURLs': [...], 'raw': {...}}, ...]
        Returns [] on any parse or execution failure.
        """
        command = ["/bin/sh", "-c", "etcdctl member list --write-out=json"]
        rc, out, err = self._execute_in_pod(pod, command, self.etcd_cmd_timeout)
        
        if rc != 0:
            # Older etcdctl variants might not support json output; warn and return empty list
            self.module.warn(
                f"member list (json) failed on {pod}: rc={rc} stderr={err.strip()}"
            )
            return []

        try:
            parsed = json.loads(out)
        except Exception:
            self.module.warn(
                f"Failed to parse JSON from 'etcdctl member list' on {pod}"
            )
            return []

        members_raw = []
        if isinstance(parsed, dict) and "members" in parsed:
            members_raw = parsed.get("members") or []
        elif isinstance(parsed, list):
            members_raw = parsed
        else:
            self.module.warn(
                "Unexpected structure from member list JSON; expected dict with 'members' or list."
            )
            return []

        normalized_members: List[Dict] = []
        for m in members_raw:
            try:
                # ID field variants
                raw_id = None
                for key in ("ID", "id", "Id", "member_id", "memberId"):
                    if key in m:
                        raw_id = m.get(key)
                        break
                norm_id = str(raw_id) if raw_id is not None else ""
                name = m.get("name") or m.get("Name") or ""
                peer_urls = (
                    m.get("peerURLs") or m.get("PeerURLs") or m.get("peerurls") or []
                )
                normalized_members.append(
                    {
                        "id": norm_id,
                        "name": name,
                        "peerURLs": peer_urls,
                        "raw": m,
                    }
                )
            except Exception:
                # don't fail on a single bad entry; continue parsing others
                continue

        if self.debug:
            self.module.log(
                msg=f"Normalized member list from {pod}: {normalized_members}"
            )
        return normalized_members

    def _get_endpoint_status_json(self, pod: str) -> List[Dict]:
        """
        Run `etcdctl endpoint status --write-out=json` inside pod and return parsed JSON list.
        Returns [] on failure or parse error.
        """
        command = ["/bin/sh", "-c", "etcdctl endpoint status --write-out=json"]
        rc, out, err = self._execute_in_pod(pod, command, self.etcd_cmd_timeout)
        
        if rc != 0:
            self.module.warn(
                f"endpoint status json failed on {pod}: rc={rc} stderr={err.strip()}"
            )
            return []
        try:
            parsed = json.loads(out)
            if isinstance(parsed, list):
                if self.debug:
                    self.module.log(
                        msg=f"Endpoint status from {pod}: entries={len(parsed)}"
                    )
                return parsed
        except Exception:
            self.module.warn(f"Failed to parse endpoint status json on {pod}")
        return []

    # -------------------------
    # Leader detection (robust)
    # -------------------------
    def _detect_leader(self, pods: List[str]) -> Optional[str]:
        """
        Attempt to detect the leader pod name.
        Strategy:
          - Fetch member list (id->name) from first responsive pod.
          - Fetch endpoint status (json) from first responsive pod.
          - Extract Status.leader and map to member name using member list.
          - Correlate member name to pod by substring match. If not found, use header.member_id -> endpoint -> pod, then peerURLs fallback.
          - Return pod name or None when detection fails.
        """
        if not pods:
            return None

        # 1) obtain member list (id->name)
        member_map: Dict[str, str] = {}
        members_data: List[Dict] = []
        for probe in pods:
            members_data = self._get_member_list_via_etcdctl(probe)
            if members_data:
                break

        for m in members_data:
            mid = m.get("id") or ""
            name = m.get("name") or ""
            if mid:
                member_map[str(mid)] = name

        if self.debug:
            self.module.log(msg=f"Member id->name map: {member_map}")

        # 2) obtain endpoint status
        endpoint_status: List[Dict] = []
        for probe in pods:
            endpoint_status = self._get_endpoint_status_json(probe)
            if endpoint_status:
                break

        # 3) extract leader id
        leader_id: Optional[str] = None
        for entry in endpoint_status:
            st = entry.get("Status") or {}
            leader_candidate = (
                st.get("leader") if "leader" in st else st.get("Leader", None)
            )
            if leader_candidate not in (None, "", 0):
                leader_id = str(leader_candidate)
                break

        if self.debug:
            self.module.log(
                msg=f"Detected leader_id={leader_id} from endpoint status probe."
            )

        # 4) map leader_id -> member_name -> pod
        if leader_id:
            leader_name = member_map.get(leader_id)
            if leader_name:
                # match member name to pod by substring or exact
                for p in pods:
                    if leader_name in p or p in leader_name:
                        if self.debug:
                            self.module.log(
                                msg=f"Leader mapping: leader_id {leader_id} -> member {leader_name} -> pod {p}"
                            )
                        return p
                # return member name as fallback (caller may accept)
                self.module.log(
                    msg=f"Leader id {leader_id} maps to member '{leader_name}' but no matching pod found; returning member name."
                )
                return leader_name

            # 5) header.member_id correlation -> endpoint -> pod
            for entry in endpoint_status:
                st = entry.get("Status") or {}
                header = st.get("header") or {}
                header_id = (
                    header.get("member_id")
                    or header.get("memberID")
                    or header.get("MemberID")
                    or None
                )
                if header_id and str(header_id) == leader_id:
                    endpoint = entry.get("Endpoint") or ""
                    for p in pods:
                        if p in endpoint or endpoint in p:
                            if self.debug:
                                self.module.log(
                                    msg=f"Leader mapped via header.member_id to pod {p}"
                                )
                            return p
                    # try peerURLs in members_data
                    for m in members_data:
                        urls = m.get("peerURLs") or []
                        for u in urls:
                            for p in pods:
                                if p in u or u in p:
                                    if self.debug:
                                        self.module.log(
                                            msg=f"Leader mapped via peerURL to pod {p}"
                                        )
                                    return p

        # 6) last-resort: match any member name to pod
        for m in members_data:
            name = m.get("name") or ""
            if not name:
                continue
            for p in pods:
                if name in p or p in name:
                    self.module.log(
                        msg=f"Leader detection fallback: using member '{name}' matching pod '{p}'"
                    )
                    return p

        # 7) final attempt: match peerURLs to pods
        for m in members_data:
            for url in m.get("peerURLs") or []:
                for p in pods:
                    if p in url or url in p:
                        self.module.log(
                            msg=f"Leader detection fallback via peerURL matched pod '{p}'"
                        )
                        return p

        # nothing found
        self.module.warn(
            "Leader detection heuristics could not map a leader to a pod name; proceeding with conservative ordering."
        )
        return None

    # -------------------------
    # Defrag operations
    # -------------------------
    def defrag_member(self, pod: str) -> dict:
        """
        Perform defrag on the named pod. Returns a dict describing the result and appends it to self.results.
        """
        try:
            # First, check health
            command = ["/bin/sh", "-c", "etcdctl endpoint status --write-out=table"]
            rc_check, out_check, err_check = self._execute_in_pod(pod, command, self.etcd_cmd_timeout)
            if rc_check != 0:
                res = {
                    "member": pod,
                    "changed": False,
                    "rc": rc_check,
                    "msg": f"health check failed: stderr={err_check.strip()}",
                }
                self.results.append(res)
                return res

            # Now perform defrag
            command = ["/bin/sh", "-c", "etcdctl defrag"]
            rc, out, err = self._execute_in_pod(pod, command, self.etcd_cmd_timeout)
            if rc != 0:
                res = {
                    "member": pod,
                    "changed": False,
                    "rc": rc,
                    "msg": f"defrag failed: {err.strip() or out.strip()}",
                }
                self.results.append(res)
                return res

            if self.wait_between_members and self.wait_between_members > 0:
                time.sleep(self.wait_between_members)

            res = {
                "member": pod,
                "changed": True,
                "rc": rc,
                "msg": "defrag succeeded",
                "stdout": out.strip(),
            }
            self.results.append(res)
            return res
        except Exception as exc:
            res = {
                "member": pod,
                "changed": False,
                "rc": 255,
                "msg": f"unexpected error: {str(exc)}",
            }
            self.results.append(res)
            return res

    def defrag_non_leader(self, pod: str) -> Optional[str]:
        """
        Attempt to defrag non-leader member; returns pod name on success, None on failure.
        """
        res = self.defrag_member(pod)
        if res.get("changed") and res.get("rc", 0) == 0:
            return pod
        self.module.warn(
            f"Non-leader defrag for {pod} failed or not changed: {res.get('msg')}"
        )
        return None

    def defrag_etcd_member(self, pod: str) -> Optional[str]:
        """
        Defrag candidate used for leader or final pass. Returns pod name on success.
        """
        res = self.defrag_member(pod)
        if res.get("changed") and res.get("rc", 0) == 0:
            return pod
        self.module.warn(f"Defrag for {pod} failed or not changed: {res.get('msg')}")
        return None

    # -------------------------
    # Orchestration: leader-aware defrag
    # -------------------------
    def defrag_etcd_db(self) -> List[dict]:
        """
        Orchestrate defragmentation:
          - discover targets,
          - detect leader (best-effort),
          - defrag non-leaders first with bounded retries,
          - defrag leader last (or solo member if single-node cluster).
        """
        if self.member_list:
            targets = list(self.member_list)
        else:
            targets = self._discover_etcd_pods()

        if not targets:
            self.module.fail_json(
                msg="No etcd pods found or provided in member_list; aborting",
                results=[],
            )

        member_count = len(targets)
        if self.debug:
            self.module.log(msg=f"Target etcd pods: {targets}")

        # Detect leader
        leader_pod = self._detect_leader(targets)
        if leader_pod:
            self.module.log(msg=f"Detected leader pod: {leader_pod}")
        else:
            self.module.warn(
                "Leader pod could not be determined; module will attempt conservative ordering."
            )

        # Build non-leader list
        if leader_pod and leader_pod in targets:
            non_leaders = [p for p in targets if p != leader_pod]
        else:
            # Unknown leader: treat all as candidates for non-leader phase but only escalate to leader phase later
            non_leaders = list(targets)

        retry_count = 1
        non_leader_baseline = max(0, member_count - 1)
        completed_members_list: List[str] = []

        # Single-member cluster: no non-leader phase
        if member_count == 1:
            self.module.log(
                msg=f"Single-member cluster detected ({targets[0]}). Skipping non-leader phase."
            )
        else:
            max_retries = max(3, member_count * self.max_retry_multiplier)
            while len(completed_members_list) < non_leader_baseline:
                if retry_count > max_retries:
                    self.module.fail_json(
                        msg="ETCD defragmentation exceeded maximum retries. Please check ETCD health.",
                        results=self.results,
                    )
                for member in non_leaders:
                    if member in completed_members_list:
                        continue
                    completed_member = self.defrag_non_leader(member)
                    if completed_member == member:
                        completed_members_list.append(completed_member)
                        if self.debug:
                            self.module.log(
                                msg=f"Completed non-leader defrag for {member}. Completed list: {completed_members_list}"
                            )
                retry_count += 1

        # Leader (or remaining) phase
        # If leader known -> attempt only leader here; otherwise attempt any remaining members not in completed list
        if leader_pod and leader_pod not in completed_members_list:
            candidate_list = [leader_pod]
        else:
            candidate_list = [p for p in targets if p not in completed_members_list]

        for candidate in candidate_list:
            completed_leader = self.defrag_etcd_member(candidate)
            if completed_leader == candidate:
                completed_members_list.append(completed_leader)
            else:
                # If leader defrag failed, record failure and fail the module
                self.module.fail_json(
                    msg=f"Defrag failed for leader/last-phase member {candidate}",
                    results=self.results,
                )

        # Final verification
        if len(completed_members_list) == member_count:
            # Append a summary entry and return results
            self.results.append(
                {
                    "summary": "Defragmentation is done.",
                    "completed_members": completed_members_list,
                }
            )
            return self.results
        else:
            self.module.fail_json(
                msg=f"Defrag not done for all members. Completed members: {completed_members_list}",
                results=self.results,
            )


# -------------------------
# Module entrypoint
# -------------------------


def main():
    argument_spec = dict(
        paas_cluster_name=dict(type="str", required=False, default=""),
        etcd_cmd_timeout=dict(type="int", required=False, default=20),
        member_list=dict(type="str", required=False, default=""),
        kubeconfig=dict(type="str", required=False, default=None),
        wait_between_members=dict(type="int", required=False, default=60),
        max_retry_multiplier=dict(type="int", required=False, default=2),
        debug=dict(type="bool", required=False, default=False),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    controller = DefragController(
        module=module,
        paas_cluster_name=module.params["paas_cluster_name"],
        etcd_cmd_timeout=module.params["etcd_cmd_timeout"],
        member_list=module.params["member_list"],
        kubeconfig=module.params["kubeconfig"],
        wait_between_members=module.params["wait_between_members"],
        max_retry_multiplier=module.params["max_retry_multiplier"],
        debug=module.params["debug"],
    )

    try:
        results = controller.defrag_etcd_db()
        changed = any(isinstance(r, dict) and r.get("changed") for r in results)
        module.exit_json(changed=bool(changed), results=results, failed=False)
    except Exception as exc:
        module.fail_json(msg=f"module failed: {str(exc)}", failed=True)


if __name__ == "__main__":
    main()
