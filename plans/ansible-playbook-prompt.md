# Ansible Role Implementation Prompt

## OpenShift Zone Label Updater

## Objective

Create the Ansible role `roles/ocp_zone_label_updater/` that:

- Discovers vSphere MachineSets in the `openshift-machine-api` namespace
- Extracts the ESXi cluster name (zone) from each MachineSet's `resourcePool` path
- Propagates a configurable zone label to MachineSets, their owned Machines,
  and the corresponding Nodes, in that order
- Supports dry-run via Ansible `--check` mode (`kubernetes.core.k8s` respects
  check mode natively; no extra task-level directives required)
- Retries on 409 conflict errors
- Is invoked from a thin playbook at `playbooks/ocp_zone_label_updater.yml`

The role follows the modular orchestrator pattern established by `roles/hydra_thin_csi/`
and all project standards in `CLAUDE.md` and `docs/DEVELOPMENT_STANDARDS.md`.

The `ocp_zone_label_updater_label_key` variable has no default — callers must supply it
explicitly so the role can serve multiple use cases (e.g., `topology.portworx.io/zone`,
`topology.kubernetes.io/zone`, custom thin-csi labels).

---

## Phase 1: Role Skeleton

### Task 1.1: Create Role Directory Structure and Stubs

**Priority**: CRITICAL
**Effort**: 0.5 hours
**Status**: Not started

**Goal**: Establish the complete directory layout with all stub files so `ansible-lint`
and `--syntax-check` pass before any logic is written.

**Prerequisites Checklist**:

- [ ] Branch `feature/ocp-zone-label-updater` created and active
- [ ] Virtual environment active (`.venv`)
- [ ] `roles/hydra_thin_csi/` reviewed as reference

**Target Structure**:

```text
roles/ocp_zone_label_updater/
├── defaults/
│   └── main.yml
├── vars/
│   └── main.yml
├── tasks/
│   ├── main.yml
│   ├── preflight.yml
│   ├── validate.yml
│   ├── execute.yml
│   ├── verify.yml
│   └── report.yml
└── meta/
    └── main.yml
```

**Sub-tasks**:

1. Create directory skeleton
2. Create `defaults/main.yml` with all optional variables and defaults
3. Create `vars/main.yml` placeholder documenting runtime-set facts
4. Create `meta/main.yml` with role metadata
5. Create stub task files (each with `---` and a single comment line)
6. Create `tasks/main.yml` orchestrator (full content, all 5 phases)
7. Create `playbooks/ocp_zone_label_updater.yml`

**defaults/main.yml**:

```yaml
---
# ocp_zone_label_updater default variables

# Kubernetes configuration
ocp_zone_label_updater_namespace: "openshift-machine-api"  # Namespace for MachineSets and Machines

# ocp_zone_label_updater_label_key: REQUIRED - no default.
# Callers must supply the label key explicitly. Examples:
#   topology.portworx.io/zone
#   topology.kubernetes.io/zone

# Retry configuration (for 409 conflict errors)
ocp_zone_label_updater_max_retries: 5  # Maximum retries per patch operation
ocp_zone_label_updater_retry_delay: 2  # Delay in seconds between retries

# Behavior controls
ocp_zone_label_updater_fail_on_error: true  # Fail role if any label update fails

# Feature flags
ocp_zone_label_updater_enable_verification: true  # Run verify.yml after execute
ocp_zone_label_updater_enable_reporting: true     # Run report.yml at end
```

**vars/main.yml**:

```yaml
---
# Internal variables set at runtime via set_fact.
# Do not set these directly; they are populated during role execution.
#
# ocp_zone_label_updater_vsphere_machinesets  - filtered list of vSphere MachineSets
# ocp_zone_label_updater_zone_map             - list of {name, zone, resource_pool} dicts
# ocp_zone_label_updater_valid_machines       - list of {machine_name, node_name, zone} dicts
# ocp_zone_label_updater_machines_updated     - count of Machines patched
# ocp_zone_label_updater_nodes_updated        - count of Nodes patched
```

**meta/main.yml**:

```yaml
---
galaxy_info:
  role_name: ocp_zone_label_updater
  description: >
    Propagates a configurable zone label to MachineSets, Machines, and Nodes in an
    OpenShift cluster by extracting ESXi cluster names from MachineSet resourcePool paths.
  min_ansible_version: "2.12.0"
  platforms:
    - name: EL
      versions:
        - "9"

dependencies: []
```

**tasks/main.yml** (complete orchestrator):

```yaml
---
# ocp_zone_label_updater role orchestrator

- name: "Phase 1: Pre-flight checks"
  ansible.builtin.import_tasks: preflight.yml
  tags:
    - always
    - preflight
    - ocp_zone_label_updater

- name: "Phase 2: Input validation"
  ansible.builtin.import_tasks: validate.yml
  tags:
    - always
    - validate
    - ocp_zone_label_updater

- name: "Phase 3: Execute zone label updates"
  ansible.builtin.import_tasks: execute.yml
  tags:
    - execute
    - ocp_zone_label_updater

- name: "Phase 4: Verify label propagation"
  ansible.builtin.import_tasks: verify.yml
  when: ocp_zone_label_updater_enable_verification | bool
  tags:
    - verify
    - ocp_zone_label_updater

- name: "Phase 5: Report"
  ansible.builtin.import_tasks: report.yml
  when: ocp_zone_label_updater_enable_reporting | bool
  tags:
    - report
    - ocp_zone_label_updater
```

**playbooks/ocp_zone_label_updater.yml**:

```yaml
---
# OpenShift Zone Label Updater
#
# Propagates a configurable zone label to MachineSets, Machines, and Nodes
# based on ESXi cluster names derived from MachineSet resourcePool paths.
#
# Required variable (no default):
#   ocp_zone_label_updater_label_key: "topology.portworx.io/zone"
#
# Usage:
#   ansible-playbook playbooks/ocp_zone_label_updater.yml \
#     -e ocp_zone_label_updater_label_key=topology.portworx.io/zone
#   ansible-playbook playbooks/ocp_zone_label_updater.yml \
#     -e ocp_zone_label_updater_label_key=topology.portworx.io/zone --check
#   ansible-playbook playbooks/ocp_zone_label_updater.yml \
#     -e ocp_zone_label_updater_label_key=topology.portworx.io/zone --tags preflight

- name: OpenShift Zone Label Updater
  hosts: localhost
  gather_facts: false
  roles:
    - role: ocp_zone_label_updater
```

**Testing Requirements**:

```bash
.venv/bin/ansible-playbook --syntax-check playbooks/ocp_zone_label_updater.yml
.venv/bin/ansible-lint roles/ocp_zone_label_updater/
```

**Git Commit**:

```text
feat(ocp_zone_label_updater): add role skeleton, defaults, and orchestrator

Creates directory structure, defaults/main.yml, vars/main.yml, meta/main.yml,
stub task files, orchestrating tasks/main.yml, and thin invoking playbook.
```

**STOP and Report**:

```bash
echo "=== TASK 1.1 COMPLETE ==="
find roles/ocp_zone_label_updater -type f | sort
.venv/bin/ansible-lint roles/ocp_zone_label_updater/
git log -1 --oneline
echo "Ready for Task 2.1?"
```

**STOP HERE. Do not proceed without approval.**

**Success Criteria**:

- [ ] All files exist in correct locations
- [ ] `ansible-playbook --syntax-check` passes
- [ ] `ansible-lint` passes (zero errors)
- [ ] Git committed

---

## Phase 2: Preflight and Validation

### Task 2.1: Implement preflight.yml and validate.yml

**Priority**: CRITICAL
**Effort**: 1 hour
**Status**: Not started

**Goal**: Verify the environment is ready (Ansible version, cluster connectivity, MachineSet
presence) and all required role variables are defined before any mutation runs.

**Prerequisites Checklist**:

- [ ] Task 1.1 complete and committed
- [ ] `ansible-lint` passing on skeleton

**preflight.yml sub-tasks**:

1. Assert `ansible_version.full >= 2.12.0`
2. Query all MachineSets with `kubernetes.core.k8s_info`; register as
   `ocp_zone_label_updater_all_machinesets`; set `changed_when: false`
3. Fail with descriptive message if no MachineSets found
4. Filter for vSphere MachineSets: those where
   `spec.template.spec.providerSpec.value.workspace` is defined; store in
   `ocp_zone_label_updater_vsphere_machinesets` via `set_fact`
5. Fail with descriptive message if no vSphere MachineSets found

All tasks tagged `preflight` and `ocp_zone_label_updater`.

**validate.yml sub-tasks**:

1. Assert `ocp_zone_label_updater_namespace` is defined and `| length > 0`
2. Assert `ocp_zone_label_updater_label_key` is defined and `| length > 0`
   (this is the required variable with no default)

All tasks tagged `validate` and `ocp_zone_label_updater`.

**Fail message convention**: All `fail_msg` values must begin with the role name prefix
(`ocp_zone_label_updater`) so operators can identify the source in multi-role plays.

**Example preflight task pattern**:

```yaml
- name: Validate minimum Ansible version for ocp_zone_label_updater
  ansible.builtin.assert:
    that:
      - ansible_version.full is version('2.12.0', '>=')
    fail_msg: >
      ocp_zone_label_updater requires Ansible 2.12.0 or higher.
      Current version: {{ ansible_version.full }}
    quiet: true
  tags:
    - preflight
    - ocp_zone_label_updater

- name: Query MachineSets in {{ ocp_zone_label_updater_namespace }}
  kubernetes.core.k8s_info:
    api_version: "machine.openshift.io/v1beta1"
    kind: MachineSet
    namespace: "{{ ocp_zone_label_updater_namespace }}"
  register: ocp_zone_label_updater_all_machinesets
  changed_when: false
  tags:
    - preflight
    - ocp_zone_label_updater
```

**Testing Requirements**:

```bash
.venv/bin/ansible-playbook --syntax-check playbooks/ocp_zone_label_updater.yml
.venv/bin/ansible-lint roles/ocp_zone_label_updater/
.venv/bin/ansible-playbook playbooks/ocp_zone_label_updater.yml \
  -e ocp_zone_label_updater_label_key=topology.portworx.io/zone --tags preflight --check
.venv/bin/ansible-playbook playbooks/ocp_zone_label_updater.yml \
  -e ocp_zone_label_updater_label_key=topology.portworx.io/zone --tags validate --check
```

**Git Commit**:

```text
feat(ocp_zone_label_updater): implement preflight and validation phases

preflight.yml verifies Ansible version and discovers vSphere MachineSets.
validate.yml asserts required variables are defined and non-empty.
```

**STOP and Report**:

```bash
echo "=== TASK 2.1 COMPLETE ==="
cat roles/ocp_zone_label_updater/tasks/preflight.yml
echo "---"
cat roles/ocp_zone_label_updater/tasks/validate.yml
.venv/bin/ansible-lint roles/ocp_zone_label_updater/
git log -1 --oneline
echo "Ready for Task 3.1?"
```

**STOP HERE. Do not proceed without approval.**

**Success Criteria**:

- [ ] `preflight.yml` queries MachineSets, filters for vSphere, fails descriptively if absent
- [ ] `validate.yml` asserts `ocp_zone_label_updater_label_key` and namespace are defined
- [ ] All `k8s_info` tasks have `changed_when: false`
- [ ] All tasks use FQCN
- [ ] All tasks tagged `preflight`/`validate` and `ocp_zone_label_updater`
- [ ] `ansible-lint` passes

---

## Phase 3: Execute — Zone Extraction and Label Updates

### Task 3.1: Implement execute.yml

**Priority**: CRITICAL
**Effort**: 3 hours
**Status**: Not started

**Goal**: Extract zone names from MachineSet resourcePool paths, then propagate the zone
label to MachineSets, their owned Running Machines, and corresponding Nodes in order.

**Prerequisites Checklist**:

- [ ] Task 2.1 complete and committed
- [ ] preflight and validate passing in `--check` mode

**resourcePool path format**: `/datacenter/host/<cluster_name>/Resources`

Zone = path segment at index 2 (zero-indexed) after splitting on `/`.

**execute.yml sub-tasks** (all within a `block`/`rescue`):

#### A: Build Zone Map

1. Initialise `ocp_zone_label_updater_zone_map: []` via `set_fact`
2. Loop over `ocp_zone_label_updater_vsphere_machinesets` (registered in preflight):
   - Extract `resource_pool = item.spec.template.spec.providerSpec.value.workspace.resourcePool`
   - Skip (debug message) if `resource_pool` is undefined or `split('/') | length < 4`
   - Append `{name: item.metadata.name, zone: path[2], resource_pool: resource_pool}` to
     `ocp_zone_label_updater_zone_map`
3. Fail if `ocp_zone_label_updater_zone_map | length == 0`

#### B: Update MachineSet Labels

```yaml
- name: Patch zone label on MachineSet {{ item.name }}
  kubernetes.core.k8s:
    state: patched
    api_version: "machine.openshift.io/v1beta1"
    kind: MachineSet
    name: "{{ item.name }}"
    namespace: "{{ ocp_zone_label_updater_namespace }}"
    definition:
      spec:
        template:
          spec:
            metadata:
              labels:
                "{{ ocp_zone_label_updater_label_key }}": "{{ item.zone }}"
  loop: "{{ ocp_zone_label_updater_zone_map }}"
  loop_control:
    label: "{{ item.name }}"
  register: ocp_zone_label_updater_ms_patch_results
  retries: "{{ ocp_zone_label_updater_max_retries }}"
  delay: "{{ ocp_zone_label_updater_retry_delay }}"
  until: ocp_zone_label_updater_ms_patch_results is not failed
  tags:
    - execute
    - ocp_zone_label_updater
```

#### C: Discover and Update Machines

1. For each entry in `ocp_zone_label_updater_zone_map`, query Machines using label selector
   `machine.openshift.io/cluster-api-machineset={{ item.name }}`; `changed_when: false`
2. Build `ocp_zone_label_updater_valid_machines`: filter for `status.phase == "Running"` and
   `spec.nodeRef` defined — list of `{machine_name, node_name, zone}` dicts
3. Log skipped Machines with `ansible.builtin.debug` (name and skip reason)
4. Patch each valid Machine's `metadata.labels` with zone label; same retry pattern
5. Set `ocp_zone_label_updater_machines_updated` count via `set_fact`

#### D: Update Nodes

1. For each entry in `ocp_zone_label_updater_valid_machines`, patch Node `metadata.labels`
   using `node_name`; same retry pattern
2. Set `ocp_zone_label_updater_nodes_updated` count via `set_fact`

**Error handling wrapper**:

```yaml
- name: Execute zone label updates
  block:
    # ... sub-tasks A through D ...
  rescue:
    - name: Report execute phase failure
      ansible.builtin.fail:
        msg: >
          ocp_zone_label_updater execute phase failed. Review task output above.
          To continue on failure set ocp_zone_label_updater_fail_on_error=false.
      when: ocp_zone_label_updater_fail_on_error | bool
  tags:
    - execute
    - ocp_zone_label_updater
```

**Idempotency**: `kubernetes.core.k8s` with `state: patched` reports `changed` only when the
resource actually differs. Running the role twice with the same inputs produces no changes on
the second run.

**Testing Requirements**:

```bash
.venv/bin/ansible-playbook --syntax-check playbooks/ocp_zone_label_updater.yml
.venv/bin/ansible-lint roles/ocp_zone_label_updater/
.venv/bin/ansible-playbook playbooks/ocp_zone_label_updater.yml \
  -e ocp_zone_label_updater_label_key=topology.portworx.io/zone --check
.venv/bin/ansible-playbook playbooks/ocp_zone_label_updater.yml \
  -e ocp_zone_label_updater_label_key=topology.portworx.io/zone --tags execute --check
```

**Git Commit**:

```text
feat(ocp_zone_label_updater): implement execute phase

Builds zone map from MachineSet resourcePool paths, then patches the
configured zone label on MachineSets, Running Machines, and their Nodes.
Includes retry logic and block/rescue error handling.
```

**STOP and Report**:

```bash
echo "=== TASK 3.1 COMPLETE ==="
wc -l roles/ocp_zone_label_updater/tasks/execute.yml
.venv/bin/ansible-lint roles/ocp_zone_label_updater/
.venv/bin/ansible-playbook --syntax-check playbooks/ocp_zone_label_updater.yml
git log -1 --oneline
echo "Ready for Task 4.1?"
```

**STOP HERE. Do not proceed without approval.**

**Success Criteria**:

- [ ] Zone extraction skips (with debug) MachineSets with missing or malformed resourcePool
- [ ] MachineSet, Machine, Node updates use `state: patched` with retry
- [ ] Non-Running Machines are skipped with a debug message logged
- [ ] `block`/`rescue` wraps all update tasks
- [ ] All `k8s_info` tasks have `changed_when: false`
- [ ] All tasks tagged `execute` and `ocp_zone_label_updater`
- [ ] `ansible-lint` passes, `--check` dry-run completes without error

---

## Phase 4: Verify and Report

### Task 4.1: Implement verify.yml and report.yml

**Priority**: HIGH
**Effort**: 1.5 hours
**Status**: Not started

**Goal**: Confirm all labels were applied correctly and emit a structured operation summary.

**Prerequisites Checklist**:

- [ ] Task 3.1 complete and committed
- [ ] execute phase passing in `--check` mode

**verify.yml sub-tasks**:

1. Re-query each MachineSet from `ocp_zone_label_updater_zone_map`; `changed_when: false`
2. Assert `ocp_zone_label_updater_label_key` is present with expected zone value in
   `spec.template.spec.metadata.labels`
3. Re-query each Machine in `ocp_zone_label_updater_valid_machines`; `changed_when: false`
4. Assert label present on Machine `metadata.labels`
5. Re-query each Node by name; `changed_when: false`
6. Assert label present on Node `metadata.labels`

All tasks tagged `verify` and `ocp_zone_label_updater`.

**report.yml** (match `hydra_thin_csi/tasks/report.yml` style):

```yaml
---
# ocp_zone_label_updater: operation summary

- name: Report ocp_zone_label_updater results
  ansible.builtin.debug:
    msg: |
      ============================================================
      OpenShift Zone Label Updater - Operation Summary
      ============================================================
      Namespace  : {{ ocp_zone_label_updater_namespace }}
      Label Key  : {{ ocp_zone_label_updater_label_key }}

      MachineSets processed : {{ ocp_zone_label_updater_zone_map | length }}
      Machines updated      : {{ ocp_zone_label_updater_machines_updated | default(0) }}
      Nodes updated         : {{ ocp_zone_label_updater_nodes_updated | default(0) }}

      Zone Mapping:
      {% for entry in ocp_zone_label_updater_zone_map %}
        {{ entry.name }} -> {{ entry.zone }}
      {% endfor %}
      ============================================================
  tags:
    - report
    - ocp_zone_label_updater
```

**Testing Requirements**:

```bash
.venv/bin/ansible-playbook --syntax-check playbooks/ocp_zone_label_updater.yml
.venv/bin/ansible-lint roles/ocp_zone_label_updater/
# Full dry-run all phases:
.venv/bin/ansible-playbook playbooks/ocp_zone_label_updater.yml \
  -e ocp_zone_label_updater_label_key=topology.portworx.io/zone --check
# Idempotency against live cluster: run twice, second run must show 0 changed tasks
```

**Git Commit**:

```text
feat(ocp_zone_label_updater): implement verify and report phases

verify.yml re-queries all patched resources and asserts labels are present,
confirming idempotency. report.yml emits a structured operation summary.
```

**STOP and Report**:

```bash
echo "=== TASK 4.1 COMPLETE ==="
.venv/bin/ansible-lint roles/ocp_zone_label_updater/
.venv/bin/ansible-playbook --syntax-check playbooks/ocp_zone_label_updater.yml
git log --oneline -4
echo "Role implementation complete. Ready for final review?"
```

**STOP HERE. Do not proceed without approval.**

**Success Criteria**:

- [ ] `verify.yml` asserts labels on all 3 resource types with expected values
- [ ] All `k8s_info` tasks in verify.yml have `changed_when: false`
- [ ] `report.yml` emits structured summary with per-machineset zone mapping
- [ ] `ansible-lint` passes with zero warnings
- [ ] `--syntax-check` passes
- [ ] Idempotency confirmed (second run: 0 changed tasks)
- [ ] Git committed

---

## Standards Compliance Checklist

### CLAUDE.md

- [ ] All modules use FQCN (`kubernetes.core.k8s`, `ansible.builtin.assert`, etc.)
- [ ] All boolean values lowercase (`true`/`false`)
- [ ] `block`/`rescue` used in execute.yml
- [ ] `changed_when: false` on all `k8s_info` (read-only) tasks
- [ ] `register` used only where output is consumed downstream
- [ ] All variables prefixed `ocp_zone_label_updater_`
- [ ] All configurable defaults in `defaults/main.yml`; `label_key` intentionally absent
- [ ] Modular orchestrator pattern: `tasks/main.yml` delegates to phase files
- [ ] Tags: `always` on preflight/validate, phase-specific, `ocp_zone_label_updater` on all

### docs/DEVELOPMENT_STANDARDS.md

- [ ] Every phase has a clear single-sentence goal
- [ ] Every phase has a prerequisites checklist
- [ ] Every phase has exact test commands
- [ ] Every phase ends with a STOP point with evidence
- [ ] `ansible-lint` run after every task completion
- [ ] No deferred issues (fix immediately)

---

## Quality Gates (run after every task)

```bash
.venv/bin/ansible-playbook --syntax-check playbooks/ocp_zone_label_updater.yml
.venv/bin/ansible-lint roles/ocp_zone_label_updater/
```

---

## Reference Files

| Purpose | Path |
|---------|------|
| Primary reference role | `roles/hydra_thin_csi/` |
| Orchestrator reference | `roles/must_gather_log/tasks/main.yml` |
| Standards | `docs/DEVELOPMENT_STANDARDS.md`, `CLAUDE.md` |

---

## RBAC Requirements

The identity running the playbook requires:

- `get`, `list`, `watch`, `patch` on `machinesets` and `machines` (`machine.openshift.io/v1beta1`)
- `get`, `list`, `patch` on `nodes` (`v1`)

---

**END OF IMPLEMENTATION PROMPT**
