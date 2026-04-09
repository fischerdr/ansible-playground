# Portworx Upgrade Monitoring Flow

This document describes the logical flow of the monitoring tasks during a Portworx cluster upgrade.

## Overview

The monitoring phase continuously tracks the operator-controlled rolling upgrade, detecting activity, checking for timeout conditions, and optionally accelerating storageless pod upgrades through impatient mode.

## High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                    MONITORING PHASE START                        │
│                  (monitor/main.yml lines 1-42)                   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  INITIALIZATION (main.yml lines 4-15)                           │
│  - Record start time                                            │
│  - Set last_activity_time = now                                 │
│  - Initialize tracking lists (upgraded, needing_upgrade, etc.)  │
│  - Set last_completed_count = 0                                 │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  MONITORING LOOP START                                          │
│  (automatic_rolling_upgrade.yml lines 8-106)                    │
│  - Loop until: portworx_upgrade_complete = true                 │
│  - Max retries: 1000 (effectively unlimited)                    │
│  - Delay: Managed by pause task at end of loop                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
        ╔══════════════════════════════════════════════════╗
        ║         CYCLE ITERATION (repeats)                ║
        ╚══════════════════════════════════════════════════╝
                               │
     ┌─────────────────────────┴─────────────────────────┐
     │                                                     │
     ▼                                                     ▼
┌─────────────────────────┐                 ┌──────────────────────────┐
│ 1. GET POD STATE        │                 │ 2. CLASSIFY PODS         │
│ (lines 13-19)           │────────────────>│ (lines 21-32)            │
│                         │                 │                          │
│ k8s_info: Get all pods  │                 │ Filter plugin:           │
│ in portworx namespace   │                 │ classify_portworx_pods() │
└─────────────────────────┘                 │                          │
                                            │ Returns 4 categories:    │
                                            │ - upgraded (new+ready)   │
                                            │ - old_image              │
                                            │ - upgrading (new phases) │
                                            │ - new_not_ready          │
                                            └─────────┬────────────────┘
                                                      │
                                                      ▼
                                            ┌─────────────────────────┐
                                            │ 3. DISPLAY STATUS       │
                                            │ (lines 34-42)           │
                                            │                         │
                                            │ Log pod counts if       │
                                            │ detailed_logging=true   │
                                            └─────────┬───────────────┘
                                                      │
                                                      ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. DETECT ACTIVITY (lines 44-54)                                      │
│                                                                        │
│ Progress check:                                                        │
│ - current_completed_count = pods_with_new_image.length                │
│ - progress_made = current_completed > last_completed                  │
│                                                                        │
│ IF progress_made:                                                     │
│   - UPDATE last_activity_time = NOW (RESETS GLOBAL TIMEOUT)          │
│   - UPDATE last_completed_count = current_completed_count            │
│                                                                        │
│ CRITICAL: Activity = completions increasing, NOT transitions          │
└────────────────────────────┬───────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. UPDATE TRACKING LISTS (lines 66-87)                             │
│                                                                     │
│ - Log newly completed pods (detailed_logging)                      │
│ - Add new completions to pods_upgraded list                        │
│ - Update pods_needing_upgrade = pods_with_old_image                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
        ╔════════════════════════════════════════════════════╗
        ║  6. TIMEOUT DETECTION (detect_stuck_upgrade.yml)   ║
        ║             (lines 88-89)                          ║
        ╚═══════════════════════┬════════════════════════════╝
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐   ┌──────────────────┐   ┌─────────────────────┐
│ PER-POD       │   │ IMPATIENT MODE   │   │ GLOBAL TIMEOUT      │
│ TIMEOUT       │   │ (USER-TRIGGERED) │   │ CHECK               │
│ (lines 17-58) │   │ (lines 60-176)   │   │ (lines 178-250)     │
└───────┬───────┘   └────────┬─────────┘   └──────────┬──────────┘
        │                    │                         │
        │                    │                         │
        ▼                    ▼                         ▼

┌────────────────────────────────────────────────────────────────────┐
│ PER-POD TIMEOUT LOGIC (detect_stuck_upgrade.yml lines 17-58)      │
│                                                                    │
│ FOR EACH pod in (upgrading + new_not_ready):                      │
│   age = NOW - pod.creationTimestamp.strftime('%s')                │
│   IF age > portworx_pod_upgrade_timeout (15-25 min):              │
│     stuck_pod_detected = true                                     │
│     FAIL with detailed diagnostics                                │
│                                                                    │
│ PURPOSE: Catch individual pods failing to start (image pull,      │
│          resource issues, etc.)                                   │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│ IMPATIENT MODE (detect_stuck_upgrade.yml lines 60-176)            │
│                                                                    │
│ IF portworx_impatient_mode AND pods_with_old_image > 0:           │
│                                                                    │
│   SAFETY CHECK:                                                   │
│   - Verify ALL storage pods upgraded (prevents data loss)         │
│   - FAIL if any storage pods have old image                       │
│                                                                    │
│   BATCH DELETION (RUNS MULTIPLE TIMES):                           │
│   - Identify storageless pods with old image                      │
│   - Create batch (5-7 pods by default)                            │
│   - Delete batch (k8s state=absent)                               │
│   - Increment batch counter                                       │
│   - Wait for operator to recreate with new image                  │
│   - Continue monitoring (loop repeats until all upgraded)         │
│                                                                    │
│ PURPOSE: Accelerate storageless pod upgrades after storage pods   │
│          complete (can save hours on large clusters)              │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│ GLOBAL TIMEOUT (detect_stuck_upgrade.yml lines 178-250)           │
│                                                                    │
│ inactivity_duration = NOW - last_activity_time                    │
│                                                                    │
│ IF inactivity_duration > portworx_global_inactivity_timeout       │
│    (default: 35 minutes):                                         │
│                                                                    │
│   - Get diagnostic info (pods, STC status)                        │
│   - FAIL with comprehensive diagnostics:                          │
│     - Current pod states                                          │
│     - Pods still needing upgrade                                  │
│     - Pods stuck in upgrading state (with ages)                   │
│     - StorageCluster update status                                │
│     - Troubleshooting steps                                       │
│                                                                    │
│ PURPOSE: Detect operator/cluster-level issues preventing progress │
└────────────────────────────────────────────────────────────────────┘

                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. CHECK COMPLETION (lines 91-93)                              │
│                                                                 │
│ upgrade_complete = (pods_with_old_image == 0 AND               │
│                     pods_upgrading == 0 AND                    │
│                     pods_new_not_ready == 0)                   │
│                                                                 │
│ IF upgrade_complete: EXIT LOOP (success)                       │
│ ELSE: Continue to wait step                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────────┐
                    │ 8. WAIT            │
                    │ (lines 95-98)      │
                    │                    │
                    │ pause:             │
                    │   seconds: 30      │
                    │ (pod_check_        │
                    │  interval)         │
                    └─────────┬──────────┘
                              │
                              │ Loop back to step 1
                              │ (next cycle)
                              ▼
        ╔══════════════════════════════════════════════════╗
        ║         RETURN TO CYCLE START                    ║
        ╚══════════════════════════════════════════════════╝


┌─────────────────────────────────────────────────────────────────┐
│                    MONITORING COMPLETE                           │
│                  (main.yml lines 33-42)                          │
│                                                                  │
│ - Record end time                                               │
│ - Log success message                                           │
│ - Report total pods upgraded                                    │
└──────────────────────────────────────────────────────────────────┘
```

## Key Data Flow Points

### Pod Classification (Critical Path)

```text
K8s API → raw pod list → classify_portworx_pods() filter →
  {upgraded, old_image, upgrading, new_not_ready} → timeout checks
```

**Pod Categories:**

1. **upgraded**: Pods with new image AND Ready condition = True
2. **old_image**: Pods still running old image version
3. **upgrading**: Pods with new image in active upgrade phases (Pending, ContainerCreating, etc.)
4. **new_not_ready**: Pods with new image but Ready = False

### Activity Detection (Progress Tracking)

```text
completed_count increases → last_activity_time = NOW →
  RESETS global timeout → allows more time for remaining pods
```

**Critical Behavior:**

- Activity is based on **completions** (upgraded pod count increasing)
- NOT based on transitions (pod phase changes)
- This ensures timeout only triggers when actual progress stops

### Timeout Hierarchy

```text
1. Per-pod timeout (15-25 min):    Pod-level issues (fast fail)
2. Global timeout (35 min):         Cluster/operator issues (slow fail)
3. Impatient mode:                  User-controlled acceleration (optional)
```

**Timeout Relationships:**

- Per-pod timeout: Individual pod age from creation to Running+Ready
- Global timeout: Time since last completion (any pod finishing upgrade)
- Impatient mode: Triggered by user flag, not automatic

### Impatient Mode Multi-Batch Flow

```text
Cycle 1: Delete 5 storageless pods → operator recreates → monitoring tracks
Cycle 2: Delete next 5 storageless → operator recreates → monitoring tracks
Cycle N: Repeat until all storageless upgraded
```

**Safety Guarantees:**

1. ALL storage pods must complete before impatient mode activates
2. Only storageless pods (without `storage="true"` label) are batch-deleted
3. Operator recreates pods automatically with new image
4. Per-pod timeout still applies to recreated pods
5. Batch counter increments to track multi-batch execution

## Pod Classification Filter Plugin

The `classify_portworx_pods` filter plugin provides 99.6% performance improvement over native Jinja2 filters.

**Location:** [roles/portworx_upgrade/filter_plugins/pod_classifier.py](../../roles/portworx_upgrade/filter_plugins/pod_classifier.py)

**Input:**

- `pods`: List of pod resources from k8s_info
- `target_version`: Expected image version after upgrade
- `active_phases`: List of pod phases indicating active upgrade

**Output:**

```python
{
    "upgraded": [],       # Pods with new image + Ready
    "old_image": [],      # Pods with old image
    "upgrading": [],      # Pods with new image in active phases
    "new_not_ready": []   # Pods with new image but not Ready
}
```

**Classification Logic:**

```python
current_image = pod.spec.containers[0].image
ready_status = pod.status.conditions[type='Ready'].status

IF current_image == target_version:
    IF pod.status.phase in active_phases:
        → upgrading
    ELIF ready_status == "True":
        → upgraded
    ELSE:
        → new_not_ready
ELSE:
    → old_image
```

## Monitoring Variables

### Tracking Variables

| Variable | Type | Purpose |
|----------|------|---------|
| `portworx_last_activity_time` | epoch | Last time a pod completed upgrade |
| `portworx_last_completed_count` | int | Count of completed pods last cycle |
| `portworx_pods_upgraded` | list | Names of all pods that completed |
| `portworx_pods_needing_upgrade` | list | Current pods with old image |
| `portworx_upgrade_complete` | bool | True when all pods upgraded |
| `portworx_impatient_batch_count` | int | Number of batches executed |

### Configuration Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `portworx_pod_upgrade_timeout` | 900-1500s | Per-pod timeout (15-25 min) |
| `portworx_global_inactivity_timeout` | 2100s | Global timeout (35 min) |
| `portworx_pod_check_interval` | 30s | Delay between monitoring cycles |
| `portworx_impatient_mode` | false | Enable batch deletion acceleration |
| `portworx_impatient_batch_size` | 5 | Pods per batch in impatient mode |
| `portworx_detailed_logging` | false | Enable verbose logging |

## Timeout Detection Details

### Per-Pod Timeout

**File:** [roles/portworx_upgrade/tasks/monitor/detect_stuck_upgrade.yml](../../roles/portworx_upgrade/tasks/monitor/detect_stuck_upgrade.yml) (lines 17-58)

**Trigger Condition:**

```yaml
age = NOW - pod.creationTimestamp.strftime('%s')
IF age > portworx_pod_upgrade_timeout:
  FAIL
```

**Timestamp Parsing (CRITICAL):**

```yaml
# CORRECT METHOD
age = (ansible_date_time.epoch | int) -
      ((pod.creationTimestamp | to_datetime('%Y-%m-%dT%H:%M:%SZ')).strftime('%s') | int)

# BROKEN METHOD (DO NOT USE)
age = (ansible_date_time.epoch | int) -
      (pod.creationTimestamp | to_datetime('%Y-%m-%dT%H:%M:%SZ') | int)
# Returns 0, not Unix timestamp!
```

**Diagnostics Provided:**

- Stuck pod name and age
- Per-pod timeout threshold
- Pod describe instructions
- Event checking commands
- Node resource verification steps

### Global Timeout (Sliding Window)

**File:** [roles/portworx_upgrade/tasks/monitor/detect_stuck_upgrade.yml](../../roles/portworx_upgrade/tasks/monitor/detect_stuck_upgrade.yml)

**Trigger Condition (Dual-Mode):**

```yaml
# Mode 1: Active pods exist (sliding window)
IF (upgrading + new_not_ready).length > 0:
  oldest_pod_age = NOW - MIN(pod.creationTimestamp for all active pods)
  IF oldest_pod_age > portworx_global_inactivity_timeout:
    FAIL

# Mode 2: No active pods (operator stall detection)
ELSE:
  inactivity_duration = NOW - last_activity_time
  IF inactivity_duration > portworx_global_inactivity_timeout:
    FAIL
```

**How It Works:**

**Sliding Window (Active Pods Exist):**

- Finds the oldest pod in `upgrading` or `new_not_ready` state
- Calculates age: `NOW - oldest_pod.creationTimestamp`
- Fails if oldest pod exceeds timeout
- Works correctly in both modes:
  - **Non-impatient:** 1 pod active (operator serial upgrade)
  - **Impatient:** Multiple pods active (batch + operator)

**Inactivity Detection (No Active Pods):**

- Triggers when all pods are either `upgraded` or `old_image`
- Uses completion-based timeout: `NOW - last_activity_time`
- Detects operator stuck between pods
- `last_activity_time` resets when pods complete

**Example Scenarios:**

**Scenario A: Impatient Mode - Sliding Window Prevents False Negative**

```text
T0: Impatient mode deletes 5 storageless pods
T0+30s: Operator recreates all 5 (Pod-A, Pod-B, Pod-C, Pod-D, Pod-E)
T0+5min: Pod-A completes (age: 4.5min)
T0+10min: Pod-B completes (age: 9.5min)
T0+15min: Pod-C completes (age: 14.5min)
T0+20min: Pod-D completes (age: 19.5min)
T0+40min: Pod-E STUCK in Pending (age: 39.5min)

Old logic (BROKEN):
- last_activity_time reset at T0+20min (Pod-D completed)
- inactivity_duration = T0+40min - T0+20min = 20 minutes
- 20min < 35min → NO FAILURE (Bug!)

New logic (CORRECT):
- oldest_pod = Pod-E (created T0+30s)
- oldest_pod_age = T0+40min - T0+30s = 39.5 minutes
- 39.5min > 35min → FAIL "Pod-E stuck for 39.5 minutes" (Correct!)
```

**Scenario B: Non-Impatient - Operator Stall Detection**

```text
T0: All pods upgraded except 5 with old image
T0+5min: Operator upgrades 1 pod, completes
T0+10min: Operator upgrades 1 pod, completes
T0+15min: Operator upgrades 1 pod, completes
T0+50min: Operator STALLED - no new pods created

Active pods: 0 (all upgraded or old_image)

Inactivity detection:
- last_activity_time = T0+15min (last completion)
- inactivity_duration = T0+50min - T0+15min = 35 minutes
- 35min >= 35min → FAIL "No progress for 35 minutes" (Correct!)
```

**Diagnostics Provided:**

- Dual-mode indication (sliding window vs inactivity)
- Oldest pod name and age (sliding window mode)
- Inactivity duration vs timeout threshold (inactivity mode)
- Current pod counts (upgraded, old, upgrading, new_not_ready)
- List of pods still needing upgrade
- List of pods in upgrading state with ages
- List of pods new but not ready
- StorageCluster update status
- Operator log commands
- Oldest pod diagnostics (when applicable)
- Troubleshooting steps

## Impatient Mode Details

**File:** [roles/portworx_upgrade/tasks/monitor/detect_stuck_upgrade.yml](../../roles/portworx_upgrade/tasks/monitor/detect_stuck_upgrade.yml) (lines 60-176)

### Activation Conditions

```yaml
IF portworx_impatient_mode == true AND
   pods_with_old_image.length > 0:

  # Safety check
  IF storage_pods_with_old_image.length > 0:
    FAIL "Cannot use impatient mode - storage pods not upgraded"

  # Execute batch deletion
  DELETE storageless_pods[:batch_size]
```

### Safety Guarantees

1. **Storage Pod Protection:**
   - ALL storage pods (with `storage="true"` label) must be upgraded first
   - Role FAILS if impatient mode attempted with storage pods pending
   - Prevents data loss from simultaneous storage pod restarts

2. **Batch Size Limit:**
   - Default: 5 pods per batch
   - Configurable via `portworx_impatient_batch_size`
   - Prevents overwhelming operator with deletions

3. **Multi-Batch Execution:**
   - NOT a one-time operation
   - Executes on every monitoring cycle while storageless pods remain
   - Batch counter increments: `portworx_impatient_batch_count`

### Expected Time Savings

**Scenario:** 300-node cluster with 300 Portworx pods

**Without Impatient Mode:**

- Operator upgrades 1 pod at a time serially
- Avg time per pod: 5 minutes
- Total time: 300 × 5 = 1500 minutes (25 hours)

**With Impatient Mode (after storage pods complete):**

- Storage pods (assume 60): 60 × 5 = 300 minutes (5 hours) serial
- Storageless pods (240): 240 ÷ 5 per batch = 48 batches
- Batch processing: ~10 minutes per batch
- Storageless time: 48 × 10 = 480 minutes (8 hours)
- Total time: 5 + 8 = 13 hours (saves 12 hours)

## Complete Monitoring Cycle Example

### Initial State

```text
Pods: 10 total
- 0 upgraded (new image + ready)
- 10 old_image
- 0 upgrading
- 0 new_not_ready

last_activity_time: T0 (monitoring start)
last_completed_count: 0
```

### Cycle 1 (T0 + 30s)

```text
Get pods → Classify:
- 1 upgraded (operator upgraded first pod)
- 9 old_image
- 0 upgrading
- 0 new_not_ready

Progress check:
- current_completed = 1
- last_completed = 0
- progress_made = TRUE
- last_activity_time = T0+30s (RESET)
- last_completed_count = 1

Timeout checks:
- Per-pod: No pods in upgrading/new_not_ready
- Global: inactivity = 30s < 2100s (OK)
- Impatient: disabled

Completion: FALSE (9 pods remain)
Wait 30s → Next cycle
```

### Cycle 2 (T0 + 60s)

```text
Get pods → Classify:
- 1 upgraded
- 8 old_image
- 1 upgrading (new pod created, not ready yet)
- 0 new_not_ready

Progress check:
- current_completed = 1
- last_completed = 1
- progress_made = FALSE
- last_activity_time = T0+30s (no change)

Timeout checks:
- Per-pod: upgrading pod age = 20s < 900s (OK)
- Global: inactivity = 30s < 2100s (OK)

Completion: FALSE
Wait 30s → Next cycle
```

### Cycle 3 (T0 + 90s)

```text
Get pods → Classify:
- 2 upgraded (second pod completed)
- 8 old_image
- 0 upgrading
- 0 new_not_ready

Progress check:
- current_completed = 2
- last_completed = 1
- progress_made = TRUE
- last_activity_time = T0+90s (RESET)
- last_completed_count = 2

Continue until all 10 pods upgraded...
```

### Final Cycle

```text
Get pods → Classify:
- 10 upgraded
- 0 old_image
- 0 upgrading
- 0 new_not_ready

Completion check:
- upgrade_complete = TRUE
- EXIT LOOP (success)

Monitoring complete:
- Total pods upgraded: 10
- Total time: elapsed time since T0
```

## Error Scenarios

### Scenario 1: Pod Stuck in ImagePullBackOff

```text
Cycle N:
- 5 upgraded
- 4 old_image
- 1 upgrading (age: 1000s, phase: Pending)

Per-pod timeout check:
- pod age (1000s) > timeout (900s)
- stuck_pod_detected = TRUE
- FAIL with diagnostics:
  "Pod portworx-abc123 stuck in Pending for 1000s"
  "Check: oc describe pod portworx-abc123"
```

### Scenario 2: Operator Stopped Processing

```text
Cycle N (T0 + 2130s):
- 5 upgraded
- 5 old_image
- 0 upgrading
- 0 new_not_ready

last_activity_time: T0+30s (35 minutes ago)

Global timeout check:
- inactivity (2130s) > timeout (2100s)
- FAIL with diagnostics:
  "No progress for 2130s (35.5 minutes)"
  "5 pods still need upgrade"
  "Check operator: oc logs -l name=portworx-operator"
```

### Scenario 3: Impatient Mode with Storage Pods Remaining

```text
Config: portworx_impatient_mode = true

Cycle N:
- 100 upgraded
- 200 old_image (150 storageless + 50 storage)

Impatient mode check:
- storage_pods_pending = 50
- FAIL: "Cannot use impatient mode - storage pods still on old version"
- Safety check prevents data loss
```

## Performance Considerations

### Filter Plugin Performance

**Before (native Jinja2):**

- Time: 23.45 seconds for 300 pods
- Method: selectattr + rejectattr filters in templates

**After (Python filter plugin):**

- Time: 0.09 seconds for 300 pods
- Method: Single-pass classification in Python
- Improvement: 99.6% reduction in processing time

**Impact:**

- Monitoring cycle: 30s interval
- Classification time now negligible
- Most time spent in k8s API calls and pause

### Monitoring Frequency

**Default: 30 seconds**

Considerations:

- Faster (10s): More API load, quicker timeout detection
- Slower (60s): Less API load, slower timeout detection
- 30s: Balanced for typical upgrade duration (5-10 min per pod)

Adjust via `portworx_pod_check_interval` variable.

## Related Files

### Task Files

- [roles/portworx_upgrade/tasks/monitor/main.yml](../../roles/portworx_upgrade/tasks/monitor/main.yml) - Monitoring initialization and completion
- [roles/portworx_upgrade/tasks/monitor/automatic_rolling_upgrade.yml](../../roles/portworx_upgrade/tasks/monitor/automatic_rolling_upgrade.yml) - Main monitoring loop
- [roles/portworx_upgrade/tasks/monitor/detect_stuck_upgrade.yml](../../roles/portworx_upgrade/tasks/monitor/detect_stuck_upgrade.yml) - Timeout and impatient mode logic

### Filter Plugins

- [roles/portworx_upgrade/filter_plugins/pod_classifier.py](../../roles/portworx_upgrade/filter_plugins/pod_classifier.py) - Pod classification filter

### Tests

- [roles/portworx_upgrade/tests/test_storage_detection.yml](../../roles/portworx_upgrade/tests/test_storage_detection.yml) - Storage vs storageless detection tests
- [roles/portworx_upgrade/tests/test_activity_detection.yml](../../roles/portworx_upgrade/tests/test_activity_detection.yml) - Activity detection logic tests
- [roles/portworx_upgrade/tests/test_impatient_mode.yml](../../roles/portworx_upgrade/tests/test_impatient_mode.yml) - Impatient mode multi-batch tests
- [roles/portworx_upgrade/tests/test_per_pod_timeout.yml](../../roles/portworx_upgrade/tests/test_per_pod_timeout.yml) - Per-pod timeout logic tests

## Configuration Examples

### Standard Production Configuration

```yaml
# Conservative timeouts for production
portworx_pod_upgrade_timeout: 1500          # 25 minutes per pod
portworx_global_inactivity_timeout: 2100    # 35 minutes total inactivity
portworx_pod_check_interval: 30             # Check every 30 seconds
portworx_impatient_mode: false              # Disabled for safety
portworx_detailed_logging: true             # Enable for audit trail
```

### Accelerated Upgrade Configuration

```yaml
# Faster timeouts + impatient mode for large clusters
portworx_pod_upgrade_timeout: 900           # 15 minutes per pod
portworx_global_inactivity_timeout: 2100    # 35 minutes total inactivity
portworx_pod_check_interval: 20             # Check every 20 seconds
portworx_impatient_mode: true               # Enable batch acceleration
portworx_impatient_batch_size: 7            # Larger batches
portworx_detailed_logging: false            # Reduce log volume
```

### Development/Testing Configuration

```yaml
# Quick timeouts for testing
portworx_pod_upgrade_timeout: 300           # 5 minutes per pod
portworx_global_inactivity_timeout: 600     # 10 minutes total inactivity
portworx_pod_check_interval: 10             # Check every 10 seconds
portworx_impatient_mode: true               # Test batch behavior
portworx_impatient_batch_size: 3            # Smaller batches
portworx_detailed_logging: true             # Verbose output
```

## Troubleshooting

### Monitoring Loop Not Progressing

**Symptom:** Loop cycles but no pods complete upgrade

**Check:**

1. Operator status: `oc get pods -n kube-system -l name=portworx-operator`
2. Operator logs: `oc logs -n kube-system -l name=portworx-operator`
3. STC status: `oc describe stc px-cluster -n kube-system`
4. Pod events: `oc get events -n kube-system --sort-by='.lastTimestamp'`

**Common Causes:**

- Operator not running
- STC update not started
- Network issues preventing pod creation
- Node resource constraints

### Per-Pod Timeout Firing Immediately

**Symptom:** Pods fail timeout check with very high age values

**Likely Cause:** Timestamp parsing bug

**Check:**

```yaml
# Verify correct pattern is used:
age: "{{ (ansible_date_time.epoch | int) - ((pod.creationTimestamp | to_datetime('%Y-%m-%dT%H:%M:%SZ')).strftime('%s') | int) }}"

# NOT this (returns 0):
age: "{{ (ansible_date_time.epoch | int) - (pod.creationTimestamp | to_datetime('%Y-%m-%dT%H:%M:%SZ') | int) }}"
```

**Fix:** Ensure `.strftime('%s')` is used before `| int`

### Impatient Mode Not Activating

**Symptom:** Impatient mode enabled but no batch deletions occur

**Check:**

1. Storage pod status: Are all storage pods upgraded?
2. Variable value: `portworx_impatient_mode` actually set to `true`?
3. Pods remaining: Are there storageless pods with old image?

**Debug:**

```yaml
- name: Debug impatient mode state
  debug:
    msg:
      - "Impatient mode: {{ portworx_impatient_mode }}"
      - "Pods with old image: {{ portworx_pods_with_old_image | length }}"
      - "Storage pods pending: {{ portworx_storage_pods_pending | length }}"
```

### Global Timeout Firing Too Early

**Symptom:** Global timeout fires but pods are still progressing

**Likely Cause:** Activity detection not resetting timer

**Check:**

```yaml
# Ensure completion count is increasing
- debug:
    msg:
      - "Current completed: {{ portworx_current_completed_count }}"
      - "Last completed: {{ portworx_last_completed_count }}"
      - "Progress made: {{ portworx_progress_made }}"
```

**Fix:** Verify activity detection logic at [automatic_rolling_upgrade.yml:44-54](../../roles/portworx_upgrade/tasks/monitor/automatic_rolling_upgrade.yml)

## Summary

The Portworx upgrade monitoring system provides:

1. **Continuous tracking** of operator-controlled rolling upgrades
2. **Three-tier timeout detection** (per-pod, global, impatient mode)
3. **Activity-based progress tracking** (completions, not transitions)
4. **Optional acceleration** via impatient mode batch deletions
5. **Comprehensive diagnostics** for all failure scenarios
6. **High performance** classification via Python filter plugin

The monitoring loop continues until all pods successfully upgrade or a timeout condition is detected, providing robust oversight of the entire upgrade process.
