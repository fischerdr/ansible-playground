# Sequential Operator Upgrade - Architecture and Implementation

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Execution Flow](#execution-flow)
- [Configuration](#configuration)
- [Error Handling](#error-handling)
- [Testing and Validation](#testing-and-validation)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)

---

## Overview

The sequential operator upgrade implementation performs **OLM-compliant version-stepping** through OpenShift's OperatorHub upgrade path. Unlike simple bulk-approval approaches, this implementation discovers and approves one version at a time, tracking state and validating safety constraints.

### Key Features

- **Sequential Version-Stepping**: Discovers smallest version > current, approves, waits for success, repeats
- **Version Skew Safety**: Maximum 10-version jump limit enforced with `calculate_upgrade_path_length` filter
- **Flexible Targeting**: Support for explicit target version OR auto-upgrade to latest available
- **State Persistence**: JSON tracking for recovery after failures
- **Comprehensive Error Handling**: Block/rescue/always with detailed troubleshooting guidance
- **Full Test Coverage**: 38 unit tests + 9 integration scenarios (100% pass rate)

### Why Sequential Stepping?

OpenShift's Operator Lifecycle Manager (OLM) creates InstallPlans for **each intermediate version** in the upgrade path. The operator must be upgraded sequentially through these versions:

```text
Current: v23.10.3
Target:  v25.5.0

OLM Creates:
  1. InstallPlan for v24.1.0
  2. InstallPlan for v24.2.1  (after v24.1.0 succeeds)
  3. InstallPlan for v25.5.0  (after v24.2.1 succeeds)

Sequential Path: 23.10.3 → 24.1.0 → 24.2.1 → 25.5.0
```

---

## Architecture

### File Structure

```text
roles/portworx_upgrade/tasks/upgrade/operator/
├── main.yml                        # Main orchestrator (entry point)
├── enforce_manual_mode.yml         # Set Subscription to Manual approval
├── discover_current_version.yml    # Parse current CSV version
├── determine_target.yml            # Decide: explicit/latest/skip
├── sequential_upgrade_loop.yml     # Loop controller (max 200 iterations)
├── process_single_step.yml         # Single upgrade step logic
├── discover_next_candidate.yml     # Find smallest version > current
├── wait_for_csv.yml               # Wait for CSV "Succeeded" phase
├── update_version_state.yml       # Update version facts & state file
└── finalize_upgrade.yml           # Final validation & health check
```

### Filter Plugin Functions

Location: `roles/portworx_upgrade/filter_plugins/operator_version.py`

#### 1. `parse_operator_version(csv_name)`

Extracts semantic version from ClusterServiceVersion name.

```yaml
Input:  "portworx-operator.v25.5.0"
Output: {
  'major': 25,
  'minor': 5,
  'patch': 0,
  'tuple': (25, 5, 0),
  'string': '25.5.0'
}
```

#### 2. `compare_versions(version1_tuple, version2_tuple)`

Compares two version tuples.

```yaml
Returns:
  -1  # version1 < version2
   0  # version1 == version2
   1  # version1 > version2
```

#### 3. `filter_greater_versions(candidates, current_version_tuple)`

Filters candidates to only those greater than current version.

```yaml
Input:
  candidates: [
    {'version_tuple': (23, 10, 3)},
    {'version_tuple': (24, 1, 0)},
    {'version_tuple': (25, 5, 0)}
  ]
  current: (24, 0, 0)

Output: [
  {'version_tuple': (24, 1, 0)},
  {'version_tuple': (25, 5, 0)}
]
```

#### 4. `sort_versions(candidates)`

Sorts candidates by version_tuple in ascending order.

```yaml
Input:  [v25.5.0, v23.10.3, v24.1.0]
Output: [v23.10.3, v24.1.0, v25.5.0]
```

#### 5. `calculate_upgrade_path_length(candidates, current, target, max_skew)`

Validates version skew doesn't exceed maximum allowed steps.

```yaml
Input:
  candidates: [all available versions]
  current: (23, 10, 3)
  target: (25, 5, 0)
  max_skew: 10

Output: 3  # Number of steps required

Raises AnsibleFilterError if path_length > max_skew
```

---

## Execution Flow

### Phase 1: Initialization (main.yml)

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. Record Operation Start Time                              │
│    - portworx_operator_operation_start = ISO8601 timestamp  │
│    - portworx_operator_iteration_count = 0                  │
│    - portworx_operator_steps_completed = []                 │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Display Upgrade Configuration                            │
│    - Target version (explicit or "latest available")        │
│    - Max version skew: 10                                   │
│    - Max iterations: 200                                    │
│    - Per-step timeout: 900s (15 min)                        │
│    - State tracking: enabled/disabled                       │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Enforce Manual Approval Mode                             │
│    └─> enforce_manual_mode.yml                              │
│                                                              │
│    Actions:                                                 │
│    - Get Subscription resource (portworx-certified)         │
│    - Check current installPlanApproval setting              │
│    - Patch to Manual if not already set                     │
│                                                              │
│    Why: Ensures controlled upgrades with explicit approval  │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Discover Current Operator Version                        │
│    └─> discover_current_version.yml                         │
│                                                              │
│    Steps:                                                   │
│    a. Query ClusterServiceVersions:                         │
│       kind: ClusterServiceVersion                           │
│       namespace: portworx                                   │
│       label: operators.coreos.com/portworx-certified        │
│                                                              │
│    b. Filter for Succeeded phase:                           │
│       status.phase == "Succeeded"                           │
│                                                              │
│    c. Parse CSV name:                                       │
│       "portworx-operator.v23.10.3"                          │
│       ↓ parse_operator_version filter                       │
│       {'tuple': (23, 10, 3), 'string': '23.10.3'}           │
│                                                              │
│    d. Set current version facts:                            │
│       - portworx_operator_current_version_tuple             │
│       - portworx_operator_current_version_string            │
│       - portworx_operator_initial_version_string (saved)    │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Determine Target Upgrade Strategy                        │
│    └─> determine_target.yml                                 │
│                                                              │
│    Decision Tree:                                           │
│                                                              │
│    IF portworx_operator_target_version != "":               │
│       Strategy: EXPLICIT                                    │
│       ├─ Parse target version string                        │
│       ├─ Get all InstallPlans from namespace                │
│       ├─ Build candidate list with version_tuples           │
│       ├─ Calculate upgrade path length                      │
│       │  └─> calculate_upgrade_path_length filter           │
│       │      (validates <= 10 steps, raises error if not)   │
│       ├─ Check if already at target:                        │
│       │  └─> IF current == target: Strategy = SKIP          │
│       └─ Set target_version_tuple                           │
│                                                              │
│    ELIF portworx_operator_auto_upgrade_to_latest:           │
│       Strategy: LATEST                                      │
│       ├─ Set target_version_string = "latest available"     │
│       ├─ Set target_version_tuple = [] (no specific target) │
│       └─ Upgrade until no more candidates found             │
│                                                              │
│    ELSE:                                                     │
│       Strategy: SKIP                                        │
│       └─> End operator upgrade phase                        │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Execute Sequential Upgrade Loop                          │
│    └─> sequential_upgrade_loop.yml                          │
│        [See Phase 2 below]                                  │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. Finalize Upgrade                                         │
│    └─> finalize_upgrade.yml                                 │
│                                                              │
│    Validation:                                              │
│    - Assert target_reached == true                          │
│    - Assert upgrade_failed == false                         │
│                                                              │
│    Display Summary:                                         │
│    ═══════════════════════════════════════════════════      │
│    OPERATOR UPGRADE COMPLETED                               │
│    Initial version: 23.10.3                                 │
│    Final version: 25.5.0                                    │
│    Total steps: 3                                           │
│    Steps completed:                                         │
│      1. 24.1.0 (300s)                                       │
│      2. 24.2.1 (240s)                                       │
│      3. 25.5.0 (360s)                                       │
│    ═══════════════════════════════════════════════════      │
│                                                              │
│    Final Health Check:                                      │
│    - Get final CSV status                                   │
│    - Verify phase == "Succeeded"                            │
└─────────────────────────────────────────────────────────────┘
```

### Phase 2: Sequential Upgrade Loop (sequential_upgrade_loop.yml)

```text
┌─────────────────────────────────────────────────────────────┐
│ Loop Control:                                               │
│   - range(0, 200) iterations (max 200 steps)                │
│   - Continue while:                                         │
│     • NOT portworx_operator_target_reached                  │
│     • NOT portworx_operator_upgrade_failed                  │
│                                                              │
│ Each iteration:                                             │
│   └─> process_single_step.yml [See Phase 3 below]          │
└─────────────────────────────────────────────────────────────┘
```

### Phase 3: Single Upgrade Step (process_single_step.yml)

This is the **core logic** that processes one version upgrade:

```text
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Record Step Start Time                              │
│   portworx_operator_step_start_time = ansible_date_time.epoch│
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Discover Next Upgrade Candidate                     │
│   └─> discover_next_candidate.yml                           │
│                                                              │
│   A. Get All InstallPlans:                                  │
│      kubernetes.core.k8s_info:                              │
│        kind: InstallPlan                                    │
│        namespace: portworx                                  │
│                                                              │
│   B. Build Candidate List (Inline Jinja2):                  │
│      {%- set candidates = [] -%}                            │
│      {%- for ip in installplans.resources -%}               │
│        {%- for csv_name in ip.spec.clusterServiceVersionNames -%}│
│          {%- if csv_name.startswith('portworx-operator') -%}│
│            {%- set parsed = csv_name | parse_operator_version -%}│
│            {%- if parsed.tuple > current_tuple -%}          │
│              {%- set _ = candidates.append({               │
│                    'installplan_name': ip.metadata.name,    │
│                    'csv_name': csv_name,                    │
│                    'approved': ip.spec.approved,            │
│                    'version_tuple': parsed.tuple,           │
│                    'version_string': parsed.string          │
│                  }) -%}                                     │
│            {%- endif -%}                                    │
│          {%- endif -%}                                      │
│        {%- endfor -%}                                       │
│      {%- endfor -%}                                         │
│                                                              │
│   C. Sort and Select Smallest:                              │
│      {{ candidates                                          │
│         | sort(attribute='version_tuple')                   │
│         | first                                             │
│         | default({}) }}                                    │
│                                                              │
│   Result: portworx_operator_next_candidate                  │
│     {                                                       │
│       'installplan_name': 'install-plan-24-1-0',            │
│       'csv_name': 'portworx-operator.v24.1.0',              │
│       'version_tuple': (24, 1, 0),                          │
│       'version_string': '24.1.0',                           │
│       'approved': false                                     │
│     }                                                       │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Check If Candidates Found                           │
│                                                              │
│   IF no candidates (empty dict):                            │
│     - Set portworx_operator_target_reached = true           │
│     - Exit loop (no more versions available)                │
│     - Skip remaining steps                                  │
│                                                              │
│   ELSE:                                                      │
│     - Continue to STEP 4                                    │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Display Upgrade Step Information                    │
│                                                              │
│   ═══════════════════════════════════════════════════════   │
│   OPERATOR UPGRADE STEP 1                                   │
│   ═══════════════════════════════════════════════════════   │
│   From: 23.10.3                                             │
│   To:   24.1.0                                              │
│   InstallPlan: install-plan-24-1-0                          │
│   ═══════════════════════════════════════════════════════   │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Approve InstallPlan                                 │
│                                                              │
│   IF next_candidate.approved == false:                      │
│     kubernetes.core.k8s:                                    │
│       kind: InstallPlan                                     │
│       namespace: portworx                                   │
│       name: install-plan-24-1-0                             │
│       definition:                                           │
│         spec:                                               │
│           approved: true                                    │
│                                                              │
│   ELSE:                                                      │
│     Skip (already approved)                                 │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Wait for CSV to Reach "Succeeded" Phase             │
│   └─> wait_for_csv.yml                                      │
│                                                              │
│   kubernetes.core.k8s_info:                                 │
│     kind: ClusterServiceVersion                             │
│     name: portworx-operator.v24.1.0                         │
│     namespace: portworx                                     │
│   until:                                                    │
│     - resources | length > 0                                │
│     - resources[0].status.phase == "Succeeded"              │
│   retries: 90  (15 min timeout ÷ 10s delay)                │
│   delay: 10                                                 │
│                                                              │
│   CSV Phase Progression:                                    │
│   None → Pending → Installing → Succeeded                   │
│   (or → Failed if error occurs)                             │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: Update Version State                                │
│   └─> update_version_state.yml                              │
│                                                              │
│   A. Parse New CSV Version:                                 │
│      portworx-operator.v24.1.0 → (24, 1, 0)                 │
│                                                              │
│   B. Update Current Version Facts:                          │
│      current_version_tuple: (23,10,3) → (24,1,0)            │
│      current_version_string: "23.10.3" → "24.1.0"           │
│                                                              │
│   C. Calculate Step Duration:                               │
│      duration = now - step_start_time                       │
│      Example: 300 seconds (5 minutes)                       │
│                                                              │
│   D. Add to Completion History:                             │
│      steps_completed += [{                                  │
│        'csv_name': 'portworx-operator.v24.1.0',             │
│        'version': '24.1.0',                                 │
│        'installplan': 'install-plan-24-1-0',                │
│        'completed_at': '2025-12-17T10:35:00Z',              │
│        'duration_seconds': 300                              │
│      }]                                                     │
│                                                              │
│   E. Increment Iteration Counter:                           │
│      iteration_count: 0 → 1                                 │
│                                                              │
│   F. Check If Target Reached:                               │
│      IF explicit target:                                    │
│        target_reached = (current_tuple == target_tuple)     │
│      IF latest:                                             │
│        target_reached = false (continue to next)            │
│                                                              │
│   G. Save State to JSON File:                               │
│      File: /tmp/.../operator_upgrade_state.json             │
│      {                                                      │
│        "operation_start": "2025-12-17T10:30:00Z",           │
│        "initial_version": "23.10.3",                        │
│        "current_version": "24.1.0",                         │
│        "target_version": "25.5.0",                          │
│        "steps_completed": [{...}],                          │
│        "total_steps": 1,                                    │
│        "target_reached": false,                             │
│        "failed": false                                      │
│      }                                                      │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 8: Check If Should Continue                            │
│                                                              │
│   IF target_reached:                                        │
│     - Exit loop                                             │
│     - Proceed to finalization                               │
│                                                              │
│   ELSE:                                                      │
│     - Pause 120 seconds                                     │
│       (Wait for OLM to create next InstallPlan)             │
│     - Display progress summary:                             │
│       "Step 1 completed successfully"                       │
│       "Current: 24.1.0"                                     │
│       "Target: 25.5.0"                                      │
│       "Continuing to next step..."                          │
│     - Return to STEP 1 (next iteration)                     │
└─────────────────────────────────────────────────────────────┘
```

### Error Handling (Rescue Block)

If any step fails (CSV timeout, InstallPlan approval failure, etc.):

```text
┌─────────────────────────────────────────────────────────────┐
│ RESCUE BLOCK                                                │
│                                                              │
│ 1. Set Failure Flags:                                       │
│    - portworx_operator_upgrade_failed = true                │
│    - portworx_operator_failure_csv = current CSV name       │
│    - portworx_operator_failure_installplan = InstallPlan    │
│    - portworx_operator_failure_reason = error description   │
│                                                              │
│ 2. Display Failure Information:                             │
│    ═══════════════════════════════════════════════════      │
│    OPERATOR UPGRADE STEP FAILED                             │
│    Failed CSV: portworx-operator.v24.1.0                    │
│    InstallPlan: install-plan-24-1-0                         │
│    Error: CSV upgrade failed or timed out                   │
│    ═══════════════════════════════════════════════════      │
│                                                              │
│ 3. Provide Troubleshooting Steps:                           │
│    TROUBLESHOOTING:                                         │
│    1. Check CSV status:                                     │
│       oc get csv portworx-operator.v24.1.0 -n portworx -o yaml│
│                                                              │
│    2. Check CSV events:                                     │
│       oc describe csv portworx-operator.v24.1.0 -n portworx │
│                                                              │
│    3. Check InstallPlan:                                    │
│       oc get installplan install-plan-24-1-0 -n portworx -o yaml│
│                                                              │
│    4. Check operator logs:                                  │
│       oc logs -n openshift-operator-lifecycle-manager \     │
│         -l app=olm-operator --tail=100                      │
│                                                              │
│    5. Check catalog-operator logs:                          │
│       oc logs -n openshift-operator-lifecycle-manager \     │
│         -l app=catalog-operator --tail=100                  │
│                                                              │
│ 4. Save Failure State to JSON                               │
│                                                              │
│ 5. Fail with Detailed Message                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuration

### User-Facing Variables (defaults/main.yml)

#### Version Targeting

```yaml
# Explicit target version (e.g., "25.5.0")
# Leave empty for auto-upgrade to latest
portworx_operator_target_version: ""

# Auto-upgrade to latest available version if target not specified
portworx_operator_auto_upgrade_to_latest: true
```

#### Safety Limits

```yaml
# Maximum allowed version steps in single upgrade run
# Prevents unsafe multi-version jumps (e.g., v1.x to v25.x)
portworx_operator_max_version_skew: 10

# Maximum loop iterations to prevent infinite loops
portworx_operator_max_iterations: 200
```

#### Timeouts

```yaml
# Timeout per CSV upgrade step (seconds)
# Default: 900s (15 minutes)
portworx_operator_per_step_timeout: 900

# Wait time between steps for OLM to create next InstallPlan (seconds)
# Default: 120s (2 minutes)
portworx_operator_installplan_poll_interval: 120
```

#### State Tracking

```yaml
# Enable state persistence to JSON file
portworx_operator_save_state: true

# Location of state file
portworx_operator_state_file: "{{ portworx_report_dir }}/operator_upgrade_state.json"
```

#### Approval Mode

```yaml
# Force Manual approval mode for controlled upgrades
# Recommended: true for production environments
portworx_operator_enforce_manual_approval: true
```

### Internal Variables (vars/main.yml)

```yaml
# Regex pattern for semantic version extraction
portworx_operator_semver_regex: 'v?([0-9]+)\.([0-9]+)\.([0-9]+)'

# CSV name prefix for Portworx operator
portworx_operator_csv_prefix: "portworx-operator"
```

---

## Error Handling

### CSV Timeout Failure

**Scenario:** CSV doesn't reach "Succeeded" phase within 15 minutes

**Error Message:**

```text
OPERATOR UPGRADE STEP FAILED

Step: 1
Target CSV: portworx-operator.v24.1.0
InstallPlan: install-plan-24-1-0
Reason: CSV upgrade failed or timed out

TROUBLESHOOTING:
1. Check CSV status:
   oc get csv portworx-operator.v24.1.0 -n portworx -o yaml

2. Check CSV events:
   oc describe csv portworx-operator.v24.1.0 -n portworx

3. Check InstallPlan:
   oc get installplan install-plan-24-1-0 -n portworx -o yaml

4. Check operator logs:
   oc logs -n openshift-operator-lifecycle-manager -l app=olm-operator --tail=100

5. Check catalog-operator logs:
   oc logs -n openshift-operator-lifecycle-manager -l app=catalog-operator --tail=100

State file saved at: /tmp/.../operator_upgrade_state.json
```

**Recovery Steps:**

1. Check state file to see which version was reached
2. Fix underlying issue (image pull, resource constraints, etc.)
3. Re-run upgrade from current version

### Version Skew Rejection

**Scenario:** Upgrade path exceeds 10 version steps

**Error Message:**

```text
Version skew too large: upgrade from 23.10.3 to 35.5.0
requires 15 steps, but maximum allowed is 10.

This upgrade path is too long and may be unsafe.
Consider upgrading in smaller increments or verify the target version is correct.
```

**Resolution:**

1. Upgrade to intermediate version first (e.g., v30.0.0)
2. Then upgrade from v30.0.0 to v35.5.0
3. Or increase `portworx_operator_max_version_skew` if validated safe

### No Candidates Found

**Scenario:** OLM doesn't provide next InstallPlan

**Possible Causes:**

- OLM catalog not synchronized
- Channel configuration incorrect
- Subscription in wrong state
- Target version not available in catalog

**Troubleshooting:**

```bash
# Check Subscription
oc get subscription portworx-certified -n portworx -o yaml

# Check CatalogSource
oc get catalogsource -n openshift-marketplace

# Check available versions in catalog
oc get packagemanifest portworx-certified -o yaml

# Force catalog refresh
oc delete pod -n openshift-marketplace -l olm.catalogSource=certified-operators
```

### InstallPlan Approval Failure

**Scenario:** Kubernetes API rejects InstallPlan patch

**Error Message:**

```text
Failed to approve InstallPlan install-plan-24-1-0
Error: <kubernetes API error>
```

**Troubleshooting:**

```bash
# Check InstallPlan status
oc get installplan install-plan-24-1-0 -n portworx -o yaml

# Check RBAC permissions
oc auth can-i patch installplan -n portworx

# Manual approval
oc patch installplan install-plan-24-1-0 -n portworx \
  --type merge -p '{"spec":{"approved":true}}'
```

---

## Testing and Validation

### Unit Tests

Location: `roles/portworx_upgrade/tests/unit/test_operator_version_filters.py`

#### **Coverage: 38 tests across 6 test classes**

```bash
# Run unit tests
.venv/bin/pytest roles/portworx_upgrade/tests/unit/test_operator_version_filters.py -v

# Expected output:
# 38 passed in 0.07s
```

**Test Categories:**

- Parse operator version (7 tests)
- Compare versions (9 tests)
- Filter greater versions (6 tests)
- Sort versions (4 tests)
- Calculate upgrade path length (9 tests)
- Integration tests (3 tests)

### Integration Tests

Location: `roles/portworx_upgrade/tests/integration/test_logic_standalone.py`

#### **Coverage: 9 integration scenarios**

```bash
# Run integration tests
.venv/bin/python roles/portworx_upgrade/tests/integration/test_logic_standalone.py

# Expected output:
# ALL INTEGRATION TESTS PASSED
```

**Test Scenarios:**

1. Parse current version
2. Parse target version
3. Build candidate list from InstallPlans
4. Filter candidates > current version
5. Sort and discover next candidate
6. Calculate sequential upgrade path
7. Validate version skew (max 10)
8. Test version skew rejection (>10)
9. Simulate reaching target version

### Linting

```bash
# Run ansible-lint
.venv/bin/ansible-lint roles/portworx_upgrade/tasks/upgrade/operator/*.yml

# Expected output:
# Passed: 0 failure(s), 0 warning(s) in 10 files processed
```

---

## Usage Examples

### Example 1: Upgrade to Specific Version

```yaml
# inventory/group_vars/all.yml or playbook vars
portworx_operator_target_version: "25.5.0"
portworx_operator_auto_upgrade_to_latest: false

# Run upgrade
ansible-playbook playbooks/px_upgrade.yml -i inventory/production
```

**Expected Behavior:**

- Discovers current version (e.g., 23.10.3)
- Validates path length (3 steps <= 10) ✓
- Sequentially upgrades: 23.10.3 → 24.1.0 → 24.2.1 → 25.5.0
- Stops when target reached

### Example 2: Auto-Upgrade to Latest

```yaml
# Leave target empty, enable auto-upgrade
portworx_operator_target_version: ""
portworx_operator_auto_upgrade_to_latest: true

# Run upgrade
ansible-playbook playbooks/px_upgrade.yml -i inventory/production
```

**Expected Behavior:**

- Discovers current version
- Upgrades sequentially through all available versions
- Stops when no more candidates found (latest reached)

### Example 3: Operator Upgrade Only (Skip Other Phases)

```yaml
# Skip all phases except operator upgrade
portworx_skip_operator_upgrade: false

# Run with operator tag only
ansible-playbook playbooks/px_upgrade.yml \
  -i inventory/production \
  --tags operator
```

**What Runs:**

- Pre-flight validation (always runs, checks STC config)
- Operator upgrade (Phase 2)
- **Skips:** ConfigMap, components, StorageCluster, monitoring, validation

### Example 4: Preflight + Operator Only

```yaml
# Run preflight checks and operator upgrade only
ansible-playbook playbooks/px_upgrade.yml \
  -i inventory/production \
  --tags preflight,operator
```

**What Runs:**

- Phase 1: Pre-flight validation
  - Environment checks
  - STC configuration validation
  - Node label validation
  - Pod health validation
  - Cluster status validation
- Phase 2: Operator upgrade
  - Sequential version-stepping
- **Skips:** ConfigMap, components, StorageCluster, monitoring, validation, reports

### Example 5: Skip Operator Upgrade (Test Other Phases)

```yaml
# Test other phases without touching operator
portworx_skip_operator_upgrade: true

# Run upgrade
ansible-playbook playbooks/px_upgrade.yml -i inventory/production
```

**What Runs:**

- Pre-flight validation
- ConfigMap update
- Update components
- StorageCluster update
- Monitoring
- Final validation
- **Skips:** Operator upgrade (Phase 2)

### Example 6: Increase Version Skew Limit

```yaml
# Allow up to 20 version steps (use with caution!)
portworx_operator_max_version_skew: 20

# Upgrade to distant version
portworx_operator_target_version: "30.0.0"

# Run upgrade
ansible-playbook playbooks/px_upgrade.yml -i inventory/production
```

**Warning:** Only increase version skew if validated safe for your environment. Large version jumps may have compatibility issues.

### Example 7: Dry Run Mode

```yaml
# Preview what would happen without making changes
portworx_dry_run: true

# Run upgrade
ansible-playbook playbooks/px_upgrade.yml \
  -i inventory/production \
  --check
```

**Behavior:**

- Discovers current version
- Calculates upgrade path
- Displays what would be done
- **Does not** approve InstallPlans or modify resources

---

## Troubleshooting

### Issue: Upgrade Stuck on Single Step

**Symptoms:**

- CSV remains in "Installing" phase for > 15 minutes
- Step times out and fails

**Diagnosis:**

```bash
# Check CSV status
oc get csv portworx-operator.v24.1.0 -n portworx -o yaml

# Check CSV phase and reason
oc get csv -n portworx -o jsonpath='{.items[*].status.phase}{"\n"}{.items[*].status.reason}'

# Check pod logs
oc logs -n portworx -l name=portworx-operator --tail=100

# Check OLM operator logs
oc logs -n openshift-operator-lifecycle-manager -l app=olm-operator --tail=200
```

**Common Causes:**

1. **Image pull failure** - Check imagePullPolicy and registry access
2. **Resource constraints** - Check node resources (CPU/memory)
3. **RBAC issues** - Verify operator ServiceAccount permissions
4. **Pod stuck** - Check pod events: `oc describe pod <pod-name> -n portworx`

**Resolution:**

1. Fix underlying issue
2. Check state file for current version
3. Re-run upgrade (will resume from current version)

### Issue: Version Skew Rejection

**Symptoms:**

- Error: "Version skew too large"
- Upgrade fails during determine_target phase

**Example:**

```text
Version skew too large: upgrade from 1.10.5 to 25.5.0
requires 30 steps, but maximum allowed is 10.
```

**Resolution Options:**

#### **Option 1: Incremental Upgrades (Recommended)**

```yaml
# First upgrade: 1.10.5 → 10.0.0
portworx_operator_target_version: "10.0.0"
# Run upgrade

# Second upgrade: 10.0.0 → 20.0.0
portworx_operator_target_version: "20.0.0"
# Run upgrade

# Third upgrade: 20.0.0 → 25.5.0
portworx_operator_target_version: "25.5.0"
# Run upgrade
```

#### **Option 2: Increase Limit (Use with Caution)**

```yaml
# Only if validated safe for your versions
portworx_operator_max_version_skew: 35
portworx_operator_target_version: "25.5.0"
```

### Issue: No Candidates Found

**Symptoms:**

- Loop exits immediately with "No candidates found"
- Target not reached

**Diagnosis:**

```bash
# Check available InstallPlans
oc get installplan -n portworx

# Check Subscription channel
oc get subscription portworx-certified -n portworx \
  -o jsonpath='{.spec.channel}'

# Check available versions in catalog
oc get packagemanifest portworx-certified \
  -o jsonpath='{.status.channels[*].name}'

# Check catalog health
oc get catalogsource -n openshift-marketplace
oc get pods -n openshift-marketplace
```

**Common Causes:**

1. **Wrong channel** - Subscription on different channel than expected
2. **Catalog not synced** - CatalogSource pod not running or failed
3. **Target version not in catalog** - Requested version doesn't exist
4. **Already at latest** - No higher versions available

**Resolution:**

```bash
# Force catalog refresh
oc delete pod -n openshift-marketplace \
  -l olm.catalogSource=certified-operators

# Wait for catalog to sync
oc wait --for=condition=ready pod \
  -l olm.catalogSource=certified-operators \
  -n openshift-marketplace \
  --timeout=300s

# Verify catalog is healthy
oc get catalogsource certified-operators \
  -n openshift-marketplace \
  -o jsonpath='{.status.connectionState.lastObservedState}'
# Should output: READY
```

### Issue: State File Recovery

**Scenario:** Upgrade failed mid-way, need to resume

**Check State File:**

```bash
# View current state
cat /tmp/ansible-workdir/portworx-upgrade/operator_upgrade_state.json

# Example output:
{
  "operation_start": "2025-12-17T10:30:00Z",
  "initial_version": "23.10.3",
  "current_version": "24.2.1",  # ← Resume from here
  "target_version": "25.5.0",
  "steps_completed": [
    {"version": "24.1.0", "duration_seconds": 300},
    {"version": "24.2.1", "duration_seconds": 240}
  ],
  "failed": true,
  "failure_reason": "CSV upgrade failed or timed out"
}
```

**Resume Upgrade:**

1. Fix the issue that caused failure
2. Re-run the same ansible-playbook command
3. Role will discover current version (24.2.1) and continue from there
4. Remaining path: 24.2.1 → 25.5.0

### Issue: Manual Approval Mode Not Set

**Symptoms:**

- InstallPlans auto-approved despite manual mode setting
- Subscription still in Automatic mode

**Diagnosis:**

```bash
# Check Subscription approval mode
oc get subscription portworx-certified -n portworx \
  -o jsonpath='{.spec.installPlanApproval}'
# Expected: Manual
```

**Resolution:**

```bash
# Manually set to Manual mode
oc patch subscription portworx-certified -n portworx \
  --type merge \
  -p '{"spec":{"installPlanApproval":"Manual"}}'

# Verify
oc get subscription portworx-certified -n portworx -o yaml | grep installPlanApproval
```

### Issue: Subscription Label Selector Mismatch

**Symptoms:**

- Error: "No Portworx operator Subscription found"
- Subscription exists but not detected

**Diagnosis:**

```bash
# Check actual Subscription labels
oc get subscription -n portworx --show-labels

# Check what role is looking for
# Expected label: operators.coreos.com/portworx-certified.portworx
```

**Resolution:**

If your Subscription has different labels, update `enforce_manual_mode.yml`:

```yaml
# roles/portworx_upgrade/tasks/upgrade/operator/enforce_manual_mode.yml
- name: Get Portworx operator Subscription
  kubernetes.core.k8s_info:
    api_version: operators.coreos.com/v1alpha1
    kind: Subscription
    namespace: "{{ portworx_operator_namespace }}"
    # Update label selector to match your environment
    label_selectors:
      - "operators.coreos.com/<YOUR-OPERATOR-NAME>.{{ portworx_operator_namespace }}"
```

---

## Best Practices

### Production Environments

1. **Always Use Manual Approval Mode**

   ```yaml
   portworx_operator_enforce_manual_approval: true
   ```

2. **Set Explicit Target Version**

   ```yaml
   # Avoid surprises, know exactly what you're upgrading to
   portworx_operator_target_version: "25.5.0"
   ```

3. **Test in Non-Production First**
   - Run full upgrade in dev/staging environment
   - Validate functionality after upgrade
   - Document any issues or workarounds

4. **Backup Before Upgrade**

   ```yaml
   portworx_backup_resources: true
   ```

5. **Monitor State File**
   - Check state file location: `{{ portworx_report_dir }}/operator_upgrade_state.json`
   - Keep for audit trail
   - Use for recovery if needed

6. **Review Version Skew**

   ```yaml
   # Keep default conservative limit
   portworx_operator_max_version_skew: 10
   ```

### Development/Testing Environments

1. **Use Auto-Upgrade to Latest**

   ```yaml
   portworx_operator_auto_upgrade_to_latest: true
   ```

2. **Increase Timeouts for Slow Clusters**

   ```yaml
   portworx_operator_per_step_timeout: 1800  # 30 minutes
   ```

3. **Enable Detailed Logging**

   ```yaml
   portworx_detailed_logging: true
   ```

4. **Test Specific Phases**

   ```bash
   # Test operator upgrade only
   ansible-playbook playbooks/px_upgrade.yml --tags operator

   # Test preflight only
   ansible-playbook playbooks/px_upgrade.yml --tags preflight
   ```

---

## Comparison with Old Implementation

### Old Implementation (`upgrade/operator.yml`)

**Approach:**

```yaml
# Get ALL InstallPlans
- Get all InstallPlans
# Approve ALL at once
- Approve all InstallPlans
# Wait for final CSV
- Wait for final CSV
```

**Problems:**

- No sequential stepping (violates OLM workflow)
- No version tracking
- No recovery capability
- No safety limits (version skew)
- No state persistence
- Poor error messages

### New Implementation (`upgrade/operator/main.yml`)

**Approach:**

```yaml
# Loop:
while not target_reached:
  # Discover NEXT version only (smallest > current)
  - Discover next candidate
  # Approve SINGLE InstallPlan
  - Approve that InstallPlan
  # Wait for CSV "Succeeded"
  - Wait for CSV
  # Update state
  - Update version facts
  - Save state to JSON
  # Check if done
  - Check if target reached
```

**Improvements:**

- Sequential version-stepping (OLM-compliant)
- Version skew validation (max 10 steps)
- State persistence for recovery
- Detailed progress tracking
- Clear error messages with troubleshooting
- Comprehensive testing (38 unit + 9 integration tests)
- Flexible targeting (explicit or latest)
- Safety limits and validation

---

## State File Reference

### Structure

```json
{
  "operation_start": "<ISO8601 timestamp>",
  "operation_end": "<ISO8601 timestamp>",
  "operation_duration_seconds": 900,
  "initial_version": "<version string>",
  "current_version": "<version string>",
  "target_version": "<version string or 'latest'>",
  "steps_completed": [
    {
      "csv_name": "<full CSV name>",
      "version": "<version string>",
      "installplan": "<InstallPlan name>",
      "completed_at": "<ISO8601 timestamp>",
      "duration_seconds": 300
    }
  ],
  "total_steps": 3,
  "target_reached": true,
  "failed": false,
  "failure_reason": "",
  "failure_csv": "",
  "failure_installplan": ""
}
```

### Example Success State

```json
{
  "operation_start": "2025-12-17T10:30:00Z",
  "operation_end": "2025-12-17T10:45:00Z",
  "operation_duration_seconds": 900,
  "initial_version": "23.10.3",
  "current_version": "25.5.0",
  "target_version": "25.5.0",
  "steps_completed": [
    {
      "csv_name": "portworx-operator.v24.1.0",
      "version": "24.1.0",
      "installplan": "install-plan-24-1-0",
      "completed_at": "2025-12-17T10:35:00Z",
      "duration_seconds": 300
    },
    {
      "csv_name": "portworx-operator.v24.2.1",
      "version": "24.2.1",
      "installplan": "install-plan-24-2-1",
      "completed_at": "2025-12-17T10:39:00Z",
      "duration_seconds": 240
    },
    {
      "csv_name": "portworx-operator.v25.5.0",
      "version": "25.5.0",
      "installplan": "install-plan-25-5-0",
      "completed_at": "2025-12-17T10:45:00Z",
      "duration_seconds": 360
    }
  ],
  "total_steps": 3,
  "target_reached": true,
  "failed": false,
  "failure_reason": "",
  "failure_csv": "",
  "failure_installplan": ""
}
```

### Example Failure State

```json
{
  "operation_start": "2025-12-17T10:30:00Z",
  "operation_end": "2025-12-17T10:50:00Z",
  "operation_duration_seconds": 1200,
  "initial_version": "23.10.3",
  "current_version": "24.2.1",
  "target_version": "25.5.0",
  "steps_completed": [
    {
      "csv_name": "portworx-operator.v24.1.0",
      "version": "24.1.0",
      "installplan": "install-plan-24-1-0",
      "completed_at": "2025-12-17T10:35:00Z",
      "duration_seconds": 300
    },
    {
      "csv_name": "portworx-operator.v24.2.1",
      "version": "24.2.1",
      "installplan": "install-plan-24-2-1",
      "completed_at": "2025-12-17T10:39:00Z",
      "duration_seconds": 240
    }
  ],
  "total_steps": 2,
  "target_reached": false,
  "failed": true,
  "failure_reason": "CSV upgrade failed or timed out",
  "failure_csv": "portworx-operator.v25.5.0",
  "failure_installplan": "install-plan-25-5-0"
}
```

---

## Summary

The sequential operator upgrade implementation provides production-ready, OLM-compliant operator upgrades with comprehensive safety features:

- **Sequential Stepping**: One version at a time through OLM's upgrade path
- **Version Skew Safety**: Maximum 10-version jump limit
- **Flexible Targeting**: Explicit version or auto-upgrade to latest
- **State Tracking**: JSON persistence for recovery
- **Error Handling**: Comprehensive troubleshooting guidance
- **Testing**: 38 unit tests + 9 integration scenarios (100% pass)

The implementation is ready for real-world testing with OperatorHub/OLM environments.
