#!/usr/bin/python

import subprocess
import time
import warnings

warnings.filterwarnings("ignore", message="Unverified HTTPS request")
from ansible.module_utils.basic import *

results = dict(results=[], failed=False, changed=False)


class DefragController(object):

    def __init__(self, paas_cluster_name, etcd_cmd_timeout, member_list):
        self.paas_cluster_name = paas_cluster_name
        self.etcd_cmd_timeout = etcd_cmd_timeout
        self.member_list = member_list

    def run(self, cmd):
        oc_cmd = (
            "timeout {} /root/clusters/{}/oc --kubeconfig=/root/clusters/{}/install/auth/kubeconfig ".format(
                self.etcd_cmd_timeout, self.paas_cluster_name, self.paas_cluster_name
            )
            + cmd
        )
        return subprocess.check_output(
            oc_cmd, cwd="/root/clusters/{}/".format(self.paas_cluster_name), shell=True
        )

    def defrag_etcd_member(self, member):
        if not self.run(
            "rsh -n openshift-etcd {} bash -c 'unset ETCDCTL_ENDPOINTS && etcdctl --endpoints=https://localhost:2379 defrag --command-timeout={}s' 2>/dev/null".format(
                member, self.etcd_cmd_timeout
            )
        ):
            raise Exception("Defragmentation failed for {}".format(self.member))
        else:
            time.sleep(60)
            return member

    def defrag_non_leader(self, member):
        leader_id = self.run(
            "rsh -n openshift-etcd {} etcdctl endpoint status --command-timeout={}s 2>/dev/null | tr -d '' | tr -d ',' | awk '$6 == \"true\" {{print $2}}'".format(
                member, self.etcd_cmd_timeout
            )
        )
        leader_name = self.run(
            "rsh -n openshift-etcd {} etcdctl member list --command-timeout={}s 2>/dev/null  | grep {} | awk '{{print $3}}' | tr -d ','".format(
                member, self.etcd_cmd_timeout, leader_id.strip("\n")
            )
        )
        enriched_leader_name = leader_name.strip("\n")
        if enriched_leader_name not in member:
            successful_member = self.defrag_etcd_member(member)
            if successful_member == member:
                return member

    def defrag_etcd_db(self):
        etcd_member_list = []
        if len(self.member_list) > 1:
            for solo_member in self.member_list.split(","):
                etcd_member_list.append(solo_member)
        else:
            etcd_pod_list = self.run(
                "get pods -n openshift-etcd -l app=etcd --no-headers | awk '{print $1}'"
            )
            for member in etcd_pod_list.strip().split("\n"):
                etcd_member_list.append(member)

        # Defrag non-leader members
        member_count = len(etcd_member_list)
        retry_count = 1
        non_leader_baseline = member_count - 1
        completed_members_list = []

        while len(completed_members_list) < non_leader_baseline:
            if retry_count > member_count:
                raise Exception(
                    "ETCD defragmentation exceeded maximum retries. Please check ETCD health."
                )

            for member in etcd_member_list:
                if member not in completed_members_list:
                    completed_member = self.defrag_non_leader(member)
                    if completed_member == member:
                        completed_members_list.append(completed_member)

            retry_count = retry_count + 1

        # Defrag leader or solo member
        for leader in etcd_member_list:
            if leader not in completed_members_list:
                completed_leader = self.defrag_etcd_member(leader)
                if completed_leader == leader:
                    completed_members_list.append(completed_leader)

        if len(completed_members_list) == member_count:
            results["results"].append(format("Defragmentation is done."))
        else:
            raise Exception(
                "Defrag not done for all members. Completed members: {}".format(
                    completed_members_list
                )
            )


def main():
    module = AnsibleModule(
        argument_spec={
            "paas_cluster_name": dict(type="str", required=True),
            "etcd_cmd_timeout": dict(type="str", required=True),
            "member_list": dict(type="str"),
        }
    )

    paas_cluster_name = module.params["paas_cluster_name"]
    etcd_cmd_timeout = module.params["etcd_cmd_timeout"]
    member_list = module.params["member_list"]

    controller = DefragController(paas_cluster_name, etcd_cmd_timeout, member_list)
    controller.defrag_etcd_db()

    if results["results"]:
        results["changed"] = True
    module.exit_json(**results)


if __name__ == "__main__":
    main()
