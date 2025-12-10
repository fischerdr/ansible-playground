# Portworx Upgrade to Version 3.4.0.1

This document covers the steps needed for upgrading Portworx to version 3.4.0.1.

These steps are specific to this version upgrade.

## Environment Setup

Retrieve the correct px-version files from the Portworx installation site:

```bash
# Get versions file for install/upgrade
export PXVER=3.4.0.1
export KBVER=$(oc version --v=0 | awk -F'[v+_-]' '/Server Version: / {print $3}')
curl -o versions-${PXVER} "https://install.portworx.com/$PXVER/version?kbver=$KBVER"
```

Set environment variables for StorageCluster and authentication:

```bash
export PXSTC=$(oc get stc -n portworx --no-headers -o name)
export PXCTL_AUTH_TOKEN=$(oc -n portworx get secrets px-admin-token -ojsonpath='{.data.auth-token}' | base64 -d)
```

## Pre-Upgrade Process

1. Login to the management host and select the target cluster

2. Verify that all storage and storageless nodes have the correct labels

   ```bash
   oc get nodes -Ltopology.portworx.io/zone -Ltopology.kubernetes.io/zone -Lportworx.io/node-type -Lpx/service
   ```

   Expected output format:

   ```text
   NAME                      STATUS   ROLES    AGE   VERSION        ZONE        ZONE        NODE-TYPE     SERVICE
   worker-node-1             Ready    worker   79d   v1.25.11       zone-1      zone-1      storageless
   ```

   Verify that `topology.kubernetes.io/zone` and `topology.portworx.io/zone` labels match for each node.

3. Verify all nodes are green in "pxctl status"

   a. Check the current pods to ensure there are no pods in a bad state

      ```bash
      oc get -nportworx po -lname=portworx -Lstorage -owide | grep -Ev "1\/1|2\/2"
      ```

      Expected output (empty result indicates all pods are healthy):

      ```text
      NAME                        READY   STATUS    RESTARTS      AGE   IP             NODE               NOMINATED NODE   READINESS GATES   STORAGE
      ```

      **WARNING - Failed pods:** If there are any pods that are not in a ready state, stop and troubleshoot the issues before proceeding.

   b. If the above shows no failed pods, access a storage node with disks and check Portworx status

   c. Debug into a Portworx pod and run pxctl commands:

      ```bash
      # Get a Portworx storage pod
      POD=$(oc get pods -n portworx -l name=portworx -o jsonpath='{.items[0].metadata.name}')

      # Exec into the pod
      oc exec -n portworx -it $POD -- /bin/bash

      # Once inside the pod
      chroot /host

      # Set the auth token
      export PXCTL_AUTH_TOKEN=$(oc -n portworx get secrets px-admin-token -ojsonpath='{.data.auth-token}' | base64 -d)
      ```

   d. Run pxctl status and verify all nodes are Online:

      ```bash
      pxctl status | grep -v Online
      ```

      Expected output (all nodes should be "Online", this command filters them out):

      ```text
      Status: PX is operational
      Telemetry: Disabled or Unhealthy
      Metering: Disabled or Unhealthy
      License: PX-Enterprise (expires in 831 days)
      Node ID: <node-id>
       IP: <node-ip>
        Local Storage Pool: 1 pool
       POOL IO_PRIORITY RAID_LEVEL USABLE USED STATUS ZONE   REGION
       Local Storage Devices: 1 device
       Device Path  Media Type                      Size     Last-Scan
       0:1 /dev/sdb STORAGE_MEDIUM_MAGNETIC         1.6 TiB  19 Feb 24 16:45 UTC
       total   -                                    1.6 TiB
       Cache Devices:
        * No cache devices
      Cluster Summary
       Cluster ID: <cluster-name>
       Cluster UUID: <cluster-uuid>
       Scheduler: kubernetes
       Total Nodes: X node(s) with storage (X online), Y node(s) without storage (Y online)
       IP  ID     SchedulerNodeName   Auth StorageNode Used Capacity Status StorageStatus Version  Kernel    OS
      Global Storage Pool
       Total Used     :  1.0 TiB
       Total Capacity :  11 TiB
      ```

      **WARNING - Bad nodes in cluster:** If any nodes are not "Online", stop and troubleshoot the issues before proceeding.

## Upgrade Process

1. Update the Portworx operator to the latest version

   a. Approve pending install plans for the Portworx operator:

      ```bash
      # Check current operator version
      oc -n portworx get subscription portworx-certified -ojsonpath='{.status.installedCSV}'

      # Check for pending install plans
      oc -n portworx get installplan -o=jsonpath='{.items[?(@.spec.approved==false)].metadata.name}'

      # Approve pending install plans
      PENDING_PLAN=$(oc get installplan -n portworx -o=jsonpath='{.items[?(@.spec.approved==false)].metadata.name}')
      if [ -n "$PENDING_PLAN" ]; then
        oc -n portworx patch installplan $PENDING_PLAN --type merge --patch '{"spec":{"approved":true}}'
      fi
      ```

      **INFO - Operator changes:** Portworx operator version 23.10.3 and later changes pod container counts. StorageCluster pods will change from "2/2" to "1/1" ready status because the CSI driver is moved into the portworx-api pod. The portworx-api pod will change from "1/1" to "2/2" ready status.

   b. Pods will not update until a StorageCluster refresh is triggered or the pods are deleted and recreated

2. Verify that the cluster is healthy via "pxctl status" on a storage node and confirm all pods are online (see pre-upgrade checks above)

3. Update the px-versions ConfigMap to the target version

   ```bash
   # Delete the existing px-versions ConfigMap
   oc -n portworx delete configmap px-versions

   # Create new px-versions ConfigMap from the versions file downloaded earlier
   oc -n portworx create configmap px-versions --from-file=versions=versions-3.4.0.1
   ```

4. Enable autoUpdateComponents in the StorageCluster

   ```bash
   # Patch StorageCluster to enable autoUpdateComponents
   oc -n portworx patch storagecluster $(oc get stc -n portworx --no-headers -o name) \
     --type merge \
     --patch '{"spec":{"autoUpdateComponents":"Always"}}'
   ```

5. Update the StorageCluster image version

   ```bash
   # Edit the StorageCluster resource
   oc edit -n portworx storagecluster

   # In the editor, locate the image field (search for "oci-monitor:")
   # Update the version tag to 3.4.0.1
   # Example: portworx/oci-monitor:3.4.0.1
   ```

6. Monitor the rolling upgrade process

   The operator will automatically perform a rolling upgrade of all Portworx pods. This is a controlled process managed by the operator.

7. Monitor node upgrade progress using pxctl status

   ```bash
   # Periodically check pxctl status to verify nodes are upgrading
   pxctl status
   ```

   a. During the upgrade, nodes will temporarily show as offline or in a degraded state as they update. This is expected behavior. Nodes should return to "Online" status within 5-15 minutes.

   b. If any pods do not return to online status after 5-8 minutes, check the pod logs for issues:

      ```bash
      # Check pod logs
      oc logs -n portworx <pod-name>

      # Describe pod for events
      oc describe pod -n portworx <pod-name>
      ```

## Accelerated Upgrade for Storageless Nodes

**WARNING - Use with Caution:** The operator performs a controlled rolling upgrade automatically. However, if you are confident the cluster is healthy and stable, you can accelerate the upgrade of storageless nodes by manually deleting them in small batches.

**Procedure:**

1. Only delete storageless node pods (NEVER delete storage node pods)
2. Delete pods in small groups of 5-7 at a time
3. Wait for each group to return to "Ready" status before proceeding to the next group
4. Monitor cluster health continuously during this process

**Example:**

```bash
# Get storageless pods
oc get pods -n portworx -l name=portworx -o json | \
  jq -r '.items[] | select(.metadata.labels.storage!="true") | .metadata.name'

# Delete a batch (example for first 5 pods)
oc delete pod -n portworx <pod-1> <pod-2> <pod-3> <pod-4> <pod-5>

# Wait for pods to be ready before continuing
oc get pods -n portworx -w
```

**CRITICAL WARNING:** Deleting too many pods simultaneously can impact cluster stability. Always:

- Delete only storageless pods
- Delete in small batches (5-7 pods maximum)
- Wait for each batch to fully recover before continuing
- Monitor the cluster for any signs of degradation
- Be prepared to stop and troubleshoot if issues arise
