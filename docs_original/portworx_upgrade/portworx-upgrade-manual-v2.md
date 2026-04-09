# Portworx Upgrade Documentation

This document covers the manual steps needed for upgrading Portworx clusters on OpenShift 4.18.

**Note:** For automated upgrades using Ansible, see the `portworx_upgrade` role documentation in `roles/portworx_upgrade/README.md` or the quick start guide at `docs/portworx_upgrade/QUICKSTART.md`.

**Important:** These procedures apply to operator-managed Portworx upgrades where the operator controls the rolling upgrade process.

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [Pre-Upgrade Process](#pre-upgrade-process)
3. [Upgrade Process](#upgrade-process)
4. [Understanding the Upgrade Process](#understanding-the-upgrade-process)
5. [Monitoring the Upgrade](#monitoring-the-upgrade)
6. [Impatient Mode (Advanced)](#impatient-mode-advanced)
7. [Timing Expectations](#timing-expectations)
8. [Final Validation](#final-validation)

## Environment Setup

Grab the correct px-version files from PX site:

```bash
# Get versions file for install/upgrade
export PXVER=3.5.0
export KBVER=$(oc version --v=0 | awk -F'[v+_-]' '/Server Version: / {print $3}')
curl -o versions-${PXVER} "https://install.portworx.com/$PXVER/version?kbver=$KBVER"
```

Set up environment variables:

```bash
export PXSTC=`oc get stc -n portworx --no-headers -o name`
echo "export PXCTL_AUTH_TOKEN=`oc -n portworx get secrets px-admin-token -ojsonpath='{.data.auth-token}' | base64 -d`"
```

## Pre-Upgrade Process

### 1. Login to Jumphost

Login to the jumphost and choose the cluster you are working on.

### 2. Verify Node Labels

Verify that all storage and storageless nodes have the correct labels:

```bash
# Check node labels
oc get nodes -Ltopology.portworx.io/zone -Ltopology.kubernetes.io/zone -Lportworx.io/node-type -Lpx/service
```

**Example output:**

```
NAME                                             STATUS   ROLES    AGE      VERSION            ZONE                  ZONE                  NODE-TYPE     SERVICE
example-cluster-worker-abc123                    Ready    worker   79d      v1.25.11+c43ddea   example-zone-1        example-zone-1        storageless
```

**Validation:** In the above output, verify that `topology.kubernetes.io/zone` matches `topology.portworx.io/zone`. This means the labels are correct for this cluster.

### 3. Verify Cluster Health

#### a. Check Pod Health

Check the current pods to make sure there are no pods in a bad state:

```bash
oc get -nportworx po -lname=portworx -Lstorage -owide | grep -Ev "1/1|2/2"
```

**Expected output (good):**

```
NAME                        READY   STATUS    RESTARTS      AGE   IP             NODE                                             NOMINATED NODE   READINESS GATES   STORAGE
```

**WARNING - Failed pods:** If there are pods that are not in good order (showing in output), you must stop and troubleshoot the issues before proceeding.

#### b. Check PX KVDB Status

If the above shows no failed pods, exec into a storage node with discs and check PX kvdb:

1. Debug into the node and chroot /host
2. Copy the AUTH starting at "export PXCTL_AUTH_TOKEN" and paste
3. Run pxctl and show the current status, removing any good nodes:

```bash
pxctl status | grep -v Online
```

**Expected output (good):**

```
Status: PX is operational
Telemetry: Disabled or Unhealthy
Metering: Disabled or Unhealthy
License: PX-Enterprise (expires in 831 days)
Node ID: <node-uuid>
 IP: <node-ip-address>
  Local Storage Pool: 1 pool
 POOL IO_PRIORITY RAID_LEVEL USABLE USED STATUS ZONE   REGION
 Local Storage Devices: 1 device
 Device Path  Media Type  Size  Last-Scan
 0:1 /dev/sdb STORAGE_MEDIUM_MAGNETIC 1.6 TiB  19 Feb 24 16:45 UTC
 total   -   1.6 TiB
 Cache Devices:
  * No cache devices
Cluster Summary
 Cluster ID: <cluster-name>
 Cluster UUID: <cluster-uuid>
 Scheduler: kubernetes
 Total Nodes: 7 node(s) with storage (7 online), 19 node(s) without storage (19 online)
 IP  ID     SchedulerNodeName   Auth StorageNode Used Capacity Status StorageStatus Version  Kernel    OS
Global Storage Pool
 Total Used     :  1.0 TiB
 Total Capacity :  11 TiB
```

**WARNING - Bad nodes in cluster:** If there are nodes that are not in good order (showing in grep output), you must stop and troubleshoot the issues before proceeding.

## Upgrade Process

### Step 1: Update Operators to Latest Versions

The following script is used to update install plan from CLI - `upgradeoperator.sh`:

```bash
#!/bin/bash

OCPCLUSTER=$1
if [[ -r "${OCPCLUSTER}" ]]
then
export KUBECONFIG=${OCPCLUSTER}
export OC="oc"
CKHOST=`${OC} config view --minify -ojsonpath='{.clusters[0].cluster.server}' | cut -d '/' -f3 |cut -d ':' -f1`
nc -z -w5 ${CKHOST} 6443
status=$( echo $? )
if [[ $status == 0 ]] ; then
   PXNS=$(${OC} get namespace portworx --no-headers --output=go-template={{.metadata.name}} 2>/dev/null)
   if [[ -n ${PXNS} ]] ; then
      ##find which one need approval
      COPV=$(${OC} -n portworx get subs portworx-certified -ojsonpath='{.status.installedCSV}' 2>/dev/null)
OPIP=$(${OC} -n portworx get ip -o=jsonpath='{.items[?(@.spec.approved==false)].metadata.name}' 2>/dev/null)
      echo "Cluster: ${OCPCLUSTER} Operator Ver: ${COPV}  Installplan: ${OPIP} "
      #here how to approve all (if batch approval is desired
      if [ ! -z ${OPIP} ] ; then
      PATCHIP=$(${OC}$ -n portworx patch installplan $(${OC} get ip -n portworx -o=jsonpath='{.items[?(@.spec.approved==false)].metadata.name}') --type merge --patch '{"spec":{"approved":true}}' 2>/dev/null)
      #echo "Approved ${PATCHIP}"
      fi
   fi
fi
fi
```

**Usage:**

```bash
/path/to/scripts/upgradeoperator.sh <CLUSTERNAME>
# Example:
/path/to/scripts/upgradeoperator.sh example-cluster-01
```

**INFO - Operator changes:** PX operator past version 23.10.3 changes the way that pods for the storagecluster are handled:

- Storagecluster pods will change from "2/2" to "1/1"
- This is due to the CSI driver being moved into the portworx-api pod
- The portworx-api pod will go from "1/1" to "2/2"

**Note:** Pods will not update until there is a refresh started or the pods are deleted and allowed to be recreated.

### Step 2: Verify Cluster Health After Operator Update

Verify that the cluster is all green in "pxctl status" on one of the storagenodes with discs and verify that no pods aren't online (see pre-upgrade checks above).

### Step 3: Update px-versions ConfigMap

Script to update the configmap:

```bash
#!/bin/bash
OCPCLUSTER=$1
VERSION="templates/portworx/$2"
export KUBECONFIG=${OCPCLUSTER}
export OC="oc"
CKHOST=$(${OC} config view --minify -ojsonpath='{.clusters[0].cluster.server}' | cut -d '/' -f3 |cut -d ':' -f1)
nc -z -w5 "${CKHOST}" 6443
status="$?"
if [[ $status == 0 ]] ; then
PXNS=$(${OC} get namespace portworx --no-headers --output=go-template='{{.metadata.name}}' 2>/dev/null)
   if [[ -n ${PXNS} ]] ; then
         echo "Cluster: ${OCPCLUSTER} "
         ${OC} -n portworx delete configmap px-versions
         ${OC} -n portworx create configmap px-versions --from-file=versions="${VERSION}"
   fi
fi
```

**Usage:**

```bash
/path/to/scripts/addupdateVersions.sh <CLUSTERNAME> <pxversion>
# Example:
/path/to/scripts/addupdateVersions.sh example-cluster-01 3.5.0
```

### Step 4: Run updatecompo.sh

This script patches the StorageCluster with `autoUpdateComponents: Once` to force the operator to refresh component images from the px-versions configmap.

```bash
./updatecompo.sh <CLUSTERNAME>
```

**What this does:** The operator will re-read the px-versions configmap and update internal component versions. Wait for the operator to process this before proceeding (no fixed time - operator-dependent).

**Script location:** [Link to updatecompo.sh script]

### Step 5: Edit StorageCluster Image

Edit the STC and update the image line:

```bash
oc edit -nportworx stc <STC_CLUSTER_NAME>
```

In the VI editor:

1. Search for "oci-monitor:"
2. Replace the version with your target version (e.g., 3.5.0)
3. Save and exit

**Example change:**

```yaml
# Before
spec:
  image: portworx/oci-monitor:3.4.0.1

# After
spec:
  image: portworx/oci-monitor:3.5.0
```

### Step 6: Automatic Rolling Upgrade Begins

Once the above is saved, the operator will update its config and start a **slow roll** of all pods to the correct version.

**What happens:**

- The operator upgrades pods **one at a time** (controlled by `maxUnavailable: 1` in STC updateStrategy)
- The operator picks pods **randomly** - not in any specific order (storage vs storageless)
- Each pod goes through: Running(old) → Terminating → (deleted) → Pending → ContainerCreating → Running(new)
- The operator waits for each pod to reach Running + Ready before starting the next one

**You are now in the monitoring phase - see next section.**

## Understanding the Upgrade Process

### Operator Behavior

**Critical Understanding:** The Portworx operator controls the entire rolling upgrade sequence. Your role is to **monitor**, not control.

**Key Concepts:**

1. **Operator Control**
   - Operator decides which pod to upgrade next (random selection)
   - Operator upgrades **one pod at a time** only
   - Operator waits for pod to be Running + Ready before selecting next pod

2. **Pod Lifecycle During Upgrade**

   ```text
   Running (old image)
   ↓
   Terminating
   ↓
   (Pod deleted)
   ↓
   Pending (new pod created)
   ↓
   ContainerCreating
   ↓
   Running (new image, not ready)
   ↓
   Running (new image, Ready)
   ```

3. **Pod States You'll See**
   - **Running with old image**: Waiting to be upgraded
   - **Terminating**: Being shut down
   - **Pending**: New pod created, waiting for scheduling
   - **ContainerCreating**: Pod scheduled, container starting
   - **Running but not Ready**: Container running, readiness probe not passing
   - **Running and Ready**: Upgrade complete for this pod

4. **Storage vs Storageless Pods**
   - **Storage pods**: Have label `storage: "true"` - these pods have data disks attached
   - **Storageless pods**: No storage label - these pods have no data disks
   - **Both types upgrade the same way** - operator picks randomly from all pods

5. **Activity vs Progress**
   - **Activity**: Pods in Terminating, Pending, ContainerCreating states
   - **Progress**: Pods completing (reaching Running + Ready with new image)
   - **Critical distinction**: Activity without progress indicates a stuck upgrade

### Timing Guidelines

**Normal timing per pod:**

- **5-10 minutes**: Normal, healthy upgrade
- **11-15 minutes**: Concerning - watch closely
- **15+ minutes**: Problem - pod is stuck, requires investigation

**Total upgrade time examples:**

- **Small cluster** (20 storage + 100 storageless): ~20 hours with operator-only
- **Medium cluster** (30 storage + 200 storageless): ~38 hours with operator-only
- **Large cluster** (30 storage + 300 storageless): ~55 hours with operator-only

**With impatient mode:**

- Same clusters can be reduced to 6-18 hours depending on batch size and cluster health

### Two Critical Timeouts

**1. Per-Pod Timeout: 15 Minutes**

- Timer starts when pod enters **Pending** state (after deletion)
- If a single pod doesn't reach Running + Ready within 15 minutes → investigate
- Indicates pod-specific issue (scheduling, image pull, startup failure)

**2. Global Progress Timeout: 35 Minutes**

- Timer resets only when pods **complete** their upgrade (reach Running + Ready)
- If no pods complete for 35 minutes → operator is stuck or cluster has issues
- Indicates cluster-wide problem (operator failure, resource exhaustion)

**How to track manually:**

- Use a stopwatch or note the time
- Track last pod completion time
- If 35 minutes pass with no new completions → investigate

## Monitoring the Upgrade

### Two-Terminal Setup

Open two terminal windows for comprehensive monitoring:

**Terminal 1 - Pod Status Monitor:**

```bash
# Run this command continuously (manually refresh or use watch)
kubectl get pods -n portworx -l name=portworx -o custom-columns='POD:.metadata.name,NODE:.spec.nodeName,STORAGE:.metadata.labels.storage,IMAGE:.spec.containers[*].image,STATE:.status.containerStatuses[*].state'
```

**What you see:**

- **POD**: Pod name
- **NODE**: Node where pod is running
- **STORAGE**: "true" for storage pods, blank for storageless pods
- **IMAGE**: Current container image (shows version)
- **STATE**: Current pod state

**Example output:**

```text
POD                              NODE                                      STORAGE  IMAGE                              STATE
portworx-abc123                  example-worker-node-01                    <none>   portworx/oci-monitor:3.5.0         map[running:map[startedAt:2025-12-12T16:59:17Z]]
portworx-def456                  example-storage-node-01                   true     portworx/oci-monitor:3.5.0         map[running:map[startedAt:2025-12-12T16:51:25Z]]
```

**Terminal 2 - Cluster Health (Optional):**

```bash
# Exec into a storage pod
oc exec -it -n portworx <storage-pod-name> -- /bin/bash

# Inside the pod, run pxctl status
export PXCTL_AUTH_TOKEN='<token-from-setup>'
/opt/pwx/bin/pxctl status
```

**What you see:**

- Cluster operational status
- Nodes online/offline
- Node versions

**Note:** Terminal 2 is optional - Terminal 1 (pod monitoring) is the primary method.

### What to Watch For

#### 1. Identifying Pods Being Upgraded

**In Terminal 1, look for:**

- **Terminating pods**: Being shut down
- **Pending pods**: Waiting to start
- **ContainerCreating pods**: Starting up
- **Running pods with new image but not showing "running" in STATE**: Starting but not ready

#### 2. Tracking Completion Count

Manually count pods that have:

- **IMAGE** shows new version (e.g., `oci-monitor:3.5.0`)
- **STATE** shows `map[running:map[startedAt:...]]`

**Example tracking:**

```text
Time    | Completed Pods | Status
--------|---------------|------------------
14:00   | 5             | Progress
14:15   | 8             | Progress
14:30   | 8             | No progress (15 min)
14:45   | 8             | No progress (30 min) - CONCERNING
15:05   | 8             | No progress (35 min) - TIMEOUT
```

#### 3. Detecting Progress vs Stalled

**Progress = Completion count increases**

- Example: 5 completed → 6 completed = progress
- Reset your 35-minute timer

**Stalled = Completion count stays the same**

- Example: 8 completed → 8 completed (after 20 minutes) = stalled
- 35-minute timer is counting

**Even if pods are "upgrading" (Terminating, Pending), if completion count doesn't increase, there's no progress.**

#### 4. Identifying Storage vs Storageless Pods

**Using Terminal 1 output:**

```bash
# List only storage pods
kubectl get pods -n portworx -l name=portworx -o custom-columns='POD:.metadata.name,NODE:.spec.nodeName,STORAGE:.metadata.labels.storage,IMAGE:.spec.containers[*].image,STATE:.status.containerStatuses[*].state' | grep true

# List only storageless pods
kubectl get pods -n portworx -l name=portworx -o custom-columns='POD:.metadata.name,NODE:.spec.nodeName,STORAGE:.metadata.labels.storage,IMAGE:.spec.containers[*].image,STATE:.status.containerStatuses[*].state' | grep -v true
```

### Normal Upgrade Pattern

**What you should see:**

1. **Operator picks a pod** (could be storage or storageless)
2. **Pod shows Terminating** in Terminal 1
3. **Pod disappears** (deleted)
4. **New pod appears in Pending** (same node, new name)
5. **Pod transitions to ContainerCreating**
6. **Pod shows Running with new image**
7. **Completion count increases by 1** - reset your 35-minute timer
8. **Operator picks next pod** - repeat

**Typical timing:** 5-10 minutes per pod

### Warning Signs

**CRITICAL - Immediate concern:**

- Pod stuck in Pending for 10+ minutes
- Pod stuck in ContainerCreating for 10+ minutes
- Completion count hasn't increased in 30 minutes

**WARNING - Watch closely:**

- Pod taking 11-15 minutes (approaching timeout)
- Multiple pods in "upgrading" states but none completing
- Completion count hasn't increased in 20 minutes

**NORMAL - Expected behavior:**

- Pods completing every 5-10 minutes
- Only 1-2 pods in "upgrading" states at a time
- Completion count steadily increasing

### Troubleshooting Stuck Pods

**If a pod is stuck in Pending:**

1. Check node resources: `oc describe node <node-name>`
2. Check pod events: `oc get events --field-selector involvedObject.name=<pod-name> -n portworx`
3. Check scheduling issues: `oc describe pod <pod-name> -n portworx`

**If a pod is stuck in ContainerCreating:**

1. Check image pull status: `oc describe pod <pod-name> -n portworx | grep -A10 "Events:"`
2. Check node storage: Verify node has available disk space
3. Check pod logs (if available): `oc logs <pod-name> -n portworx`

**Important:** There is **no abort or rollback**. Portworx upgrades are "fix forward" - you must resolve issues and let the upgrade continue.

## Impatient Mode (Advanced)

**WARNING:** Impatient mode bypasses the operator's serial upgrade by manually deleting pods in batches. This accelerates upgrades but increases risk. Use only when:

- You are confident the cluster is healthy
- You understand the risks
- You can monitor closely during execution

### When to Use Impatient Mode

**Good candidates:**

- Large clusters (200+ storageless pods) where time is critical
- Clusters with proven stability
- Scheduled maintenance windows with tight timelines

**Do NOT use if:**

- Cluster has recent stability issues
- Pre-flight checks showed any warnings
- You are unfamiliar with the cluster
- This is a production cluster and you're risk-averse

### Prerequisites for Impatient Mode

**CRITICAL:** Before starting impatient mode, verify:

1. **All storage pods must be upgraded first**

   ```bash
   # Check storage pods - should all show new version
   kubectl get pods -n portworx -l name=portworx -o custom-columns='POD:.metadata.name,STORAGE:.metadata.labels.storage,IMAGE:.spec.containers[*].image' | grep true
   ```

2. **Cluster is healthy**

   ```bash
   # All nodes should show Online
   export PXCTL_AUTH_TOKEN='<token>'
   /opt/pwx/bin/pxctl status | grep -v Online
   # Output should only show headers, no Offline nodes
   ```

3. **KVDB pods are healthy**

   ```bash
   # All 3 KVDB pods should be Running
   oc get pods -n portworx -l kvdb=true
   ```

**If any of the above checks fail, DO NOT proceed with impatient mode.**

### Impatient Mode Procedure (Multiple Batches)

Impatient mode is a **multi-batch** process. You will delete batches of 5-7 storageless pods, wait for them to recover, then delete the next batch. Repeat until all storageless pods are upgraded.

#### Step 1: Identify Storageless Pods with Old Version

```bash
# Get list of storageless pods still on old version
kubectl get pods -n portworx -l name=portworx -o custom-columns='POD:.metadata.name,STORAGE:.metadata.labels.storage,IMAGE:.spec.containers[*].image' | grep -v true | grep <old-version>

# Example: Looking for pods still on 3.4.0.1
kubectl get pods -n portworx -l name=portworx -o custom-columns='POD:.metadata.name,STORAGE:.metadata.labels.storage,IMAGE:.spec.containers[*].image' | grep -v true | grep 3.4.0.1
```

**Output example:**

```text
portworx-abc12   <none>   portworx/oci-monitor:3.4.0.1
portworx-def34   <none>   portworx/oci-monitor:3.4.0.1
portworx-ghi56   <none>   portworx/oci-monitor:3.4.0.1
...
```

#### Step 2: Select First Batch (5-7 Pods)

From the list above, select 5-7 pod names for the first batch.

**Example batch:**

```text
portworx-abc12
portworx-def34
portworx-ghi56
portworx-jkl78
portworx-mno90
```

#### Step 3: Delete the Batch

```bash
# Delete all pods in batch (space-separated)
oc delete -nportworx pod portworx-abc12 portworx-def34 portworx-ghi56 portworx-jkl78 portworx-mno90
```

**What happens:**

- All 5 pods are deleted simultaneously
- Operator recreates them with new image
- Pods go through: Pending → ContainerCreating → Running

#### Step 4: Monitor Batch Recovery

**In Terminal 1, watch for:**

- New pods appearing in Pending (on the same nodes)
- Pods transitioning to ContainerCreating
- Pods reaching Running with new image
- All pods in batch showing Running + Ready

**Track timing:**

- Start timer when you delete the batch
- **All pods in batch must recover within 15 minutes**
- If any pod exceeds 15 minutes → stop impatient mode, investigate

**How to verify all pods recovered:**

```bash
# Run the monitoring command and manually verify all 5-7 pods show:
# - New image version
# - Running state
kubectl get pods -n portworx -l name=portworx -o custom-columns='POD:.metadata.name,NODE:.spec.nodeName,STORAGE:.metadata.labels.storage,IMAGE:.spec.containers[*].image,STATE:.status.containerStatuses[*].state'
```

#### Step 5: Wait for Cluster to Settle

**Before deleting next batch, verify:**

1. **All pods from previous batch are Running + Ready**
2. **Operator may have upgraded 1-2 additional pods** (slow roll continues in parallel)
3. **Cluster is healthy** (optional: run `pxctl status | grep -v Online`)

**How long to wait:**

- No fixed time
- Wait until all batch pods are Running + Ready
- Additional 30-60 seconds for cluster to stabilize (optional)

#### Step 6: Check if More Work Remains

```bash
# Check how many storageless pods still need upgrade
kubectl get pods -n portworx -l name=portworx -o custom-columns='POD:.metadata.name,STORAGE:.metadata.labels.storage,IMAGE:.spec.containers[*].image' | grep -v true | grep <old-version> | wc -l
```

**If count > 0:** More storageless pods need upgrade → go to Step 2 (next batch)

**If count = 0:** All storageless pods upgraded → impatient mode complete, let operator finish any remaining pods

#### Step 7: Repeat Until Complete

Continue the cycle:

1. Select next batch of 5-7 pods
2. Delete batch
3. Monitor recovery (all must recover in 15 min)
4. Wait for cluster to settle
5. Check remaining work
6. Repeat

**You can stop at any time:**

- If you have other tasks, you can stop deleting batches
- Operator will continue upgrading remaining pods via slow roll
- Come back later and resume impatient mode if desired
- Always check current status with kubectl command before resuming

### Impatient Mode Risks

**What can go wrong:**

1. **Too many pods deleted → cluster degraded**
   - Symptom: Multiple pods stuck in ContainerCreating
   - Action: Stop deleting, wait for recovery, investigate

2. **Pod startup failures**
   - Symptom: Pods crash-looping or failing to reach Ready
   - Action: Stop deleting, investigate pod logs and events

3. **Resource exhaustion**
   - Symptom: Pods stuck in Pending (cannot schedule)
   - Action: Stop deleting, check node resources

4. **Network issues during batch recovery**
   - Symptom: Pods Running but pxctl shows nodes Offline
   - Action: Stop deleting, verify network connectivity

**If you encounter any of these, stop impatient mode immediately and let the operator finish via slow roll.**

### Impatient Mode Example Timeline

**Scenario: 300 storageless + 30 storage pods**

**Without impatient mode:**

- 330 pods × 10 min avg = 55 hours

**With impatient mode (batches of 6):**

```text
Storage pods (operator): 30 × 10 min = 5 hours
Storageless batches: 300 ÷ 6 = 50 batches
Batch cycle time: ~15 min (delete + recovery + settle)
Total storageless time: 50 × 15 min = 12.5 hours
Total upgrade time: 5 + 12.5 = 17.5 hours
Time saved: 37.5 hours (67% faster)
```

## Timing Expectations

### Per-Pod Timing

**Normal (healthy):**

- 5-8 minutes: Excellent
- 8-10 minutes: Good

**Concerning:**

- 11-13 minutes: Watch closely, but still acceptable
- 13-15 minutes: Approaching timeout, monitor pod events

**Problem:**

- 15+ minutes: Pod is stuck, requires investigation
- Action: Check pod describe, events, logs

### Completion Rate Expectations

**Healthy cluster:**

- Completion count increases every 5-10 minutes
- Steady progress throughout upgrade

**Concerning:**

- No completions for 20-25 minutes
- Check for stuck pods

**Problem:**

- No completions for 30+ minutes
- Check operator logs and pod states
- Approaching 35-minute global timeout

### Total Upgrade Time

**Small cluster (3 storage + 20 storageless):**

- Operator-only: ~4 hours
- With impatient mode: ~2 hours

**Medium cluster (8 storage + 100 storageless):**

- Operator-only: ~18 hours
- With impatient mode: ~5 hours

**Large cluster (20 storage + 300 storageless):**

- Operator-only: ~53 hours
- With impatient mode: ~12 hours

**Very large cluster (30 storage + 500 storageless):**

- Operator-only: ~88 hours
- With impatient mode: ~20 hours

## Final Validation

### Completion Criteria

The upgrade is complete when:

1. **All pods show new version**

   ```bash
   kubectl get pods -n portworx -l name=portworx -o custom-columns='POD:.metadata.name,IMAGE:.spec.containers[*].image'
   # All should show new version (e.g., oci-monitor:3.5.0)
   ```

2. **All pods are Running**

   ```bash
   oc get pods -n portworx -l name=portworx
   # All should show Running and 1/1 or 2/2
   ```

3. **pxctl status shows all nodes Online**

   ```bash
   export PXCTL_AUTH_TOKEN='<token>'
   /opt/pwx/bin/pxctl status | grep -v Online
   # Should only show headers, no Offline nodes
   ```

4. **pxctl status shows all nodes on new version**

   ```bash
   /opt/pwx/bin/pxctl status
   # Check Version column in node list - all should match target version
   ```

### Post-Upgrade Verification

**Recommended checks:**

1. **Verify cluster operational:**

   ```bash
   /opt/pwx/bin/pxctl status
   # Should show "Status: PX is operational"
   ```

2. **Check KVDB health:**

   ```bash
   oc get pods -n portworx -l kvdb=true
   # All 3 KVDB pods should be Running
   ```

3. **Verify no pods in bad state:**

   ```bash
   oc get pods -n portworx -l name=portworx | grep -Ev "Running.*1/1|Running.*2/2"
   # Should return no results
   ```

4. **Check for any warnings/errors:**

   ```bash
   oc get events -n portworx --sort-by='.lastTimestamp' | tail -20
   # Review recent events for any issues
   ```

### Success Confirmation

**The upgrade is successful when:**

- All pods Running + Ready
- All pods on new image version
- pxctl status shows all nodes Online
- pxctl status shows all nodes on new version
- Cluster operational (pxctl status)
- KVDB healthy (3 pods Running)
- No error events in past hour

**Document for records:**

- Start time and end time
- Total duration
- Any issues encountered and resolutions
- Whether impatient mode was used
- Final pod count and versions

---

## Appendix: Quick Reference

### Essential Commands

```bash
# Monitor pod status (primary monitoring command)
kubectl get pods -n portworx -l name=portworx -o custom-columns='POD:.metadata.name,NODE:.spec.nodeName,STORAGE:.metadata.labels.storage,IMAGE:.spec.containers[*].image,STATE:.status.containerStatuses[*].state'

# Check cluster health
export PXCTL_AUTH_TOKEN='<token>'
/opt/pwx/bin/pxctl status

# List storage pods only
kubectl get pods -n portworx -l name=portworx -o custom-columns='POD:.metadata.name,STORAGE:.metadata.labels.storage,IMAGE:.spec.containers[*].image' | grep true

# List storageless pods only  
kubectl get pods -n portworx -l name=portworx -o custom-columns='POD:.metadata.name,STORAGE:.metadata.labels.storage,IMAGE:.spec.containers[*].image' | grep -v true

# Count pods on old version
kubectl get pods -n portworx -l name=portworx -o custom-columns='IMAGE:.spec.containers[*].image' | grep <old-version> | wc -l

# Delete batch of storageless pods (impatient mode)
oc delete -nportworx pod <pod1> <pod2> <pod3> <pod4> <pod5>
```

### Troubleshooting Quick Reference

| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| Pod stuck in Pending 15+ min | Scheduling issue, node resources | Check node: `oc describe node <node>` |
| Pod stuck in ContainerCreating 15+ min | Image pull, storage mount | Check pod: `oc describe pod <pod> -n portworx` |
| No completions for 35+ min | Operator stuck, cluster issue | Check operator logs, STC status |
| Multiple pods crash-looping | Bad image, config issue | Check pod logs, check version file |
| pxctl shows node Offline but pod Running | Network delay (normal <5min) | Wait, verify after 5 minutes |

### Timing Cheat Sheet

- **Per-pod normal:** 5-10 minutes
- **Per-pod concerning:** 11-15 minutes
- **Per-pod timeout:** 15 minutes
- **Global progress timeout:** 35 minutes
- **Impatient batch size:** 5-7 pods
- **Batch recovery time:** ~15 minutes
- **Wait between batches:** Until all recovered + 30-60s

### Key Reminders

- Operator controls the upgrade - you monitor
- Progress = completion count increasing
- Activity without progress = stuck upgrade
- Storage pods must upgrade before impatient mode
- There is no rollback - fix forward only
- Track time manually (35-min and 15-min timeouts)
- Impatient mode = multiple batches, not one-time
- Can pause/resume impatient mode anytime
