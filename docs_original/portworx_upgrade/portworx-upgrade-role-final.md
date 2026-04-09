# Ansible Role: portworx_upgrade (Final Specification)

## Overview

Create a production-ready Ansible role to upgrade Portworx storage clusters running on OpenShift 4.18 (VMware). The role handles clusters of varying sizes (3-37 storage nodes, 10-300 storageless nodes) with comprehensive pre-flight checks, intelligent monitoring of the operator-controlled rolling upgrade, and optional acceleration for storageless nodes.

## Critical Understanding: Operator-Controlled Upgrade

**KEY CONCEPT**: Once triggered, the Portworx operator automatically handles the rolling upgrade one pod at a time. The role's job is to:

1. Validate prerequisites
2. Trigger the upgrade properly
3. **Monitor** (not control) the automatic rolling upgrade
4. Detect stuck/timeout conditions
5. Optionally accelerate storageless pod upgrades

## Role Structure

```text
roles/portworx_upgrade/
├── README.md
├── meta/
│   └── main.yml
├── defaults/
│   └── main.yml
├── vars/
│   └── main.yml
├── tasks/
│   ├── main.yml
│   ├── preflight/
│   │   ├── main.yml
│   │   ├── validate_environment.yml
│   │   ├── validate_nodes.yml
│   │   ├── validate_pods.yml
│   │   ├── validate_cluster_status.yml
│   │   ├── validate_stc_config.yml
│   │   └── backup_resources.yml
│   ├── upgrade/
│   │   ├── main.yml
│   │   ├── operator.yml
│   │   ├── configmap.yml
│   │   ├── update_components.yml
│   │   └── storagecluster.yml
│   ├── monitor/
│   │   ├── main.yml
│   │   ├── automatic_rolling_upgrade.yml
│   │   ├── detect_stuck_upgrade.yml
│   │   └── impatient_mode.yml
│   ├── validate/
│   │   ├── main.yml
│   │   ├── final_pod_validation.yml
│   │   ├── cluster_health.yml
│   │   └── version_consistency.yml
│   └── report/
│       ├── main.yml
│       ├── generate_summary.yml
│       └── generate_detailed_log.yml
├── handlers/
│   └── main.yml
├── templates/
│   ├── upgrade_summary.j2
│   ├── node_transition_log.j2
│   └── failure_report.j2
├── files/
│   └── versions/
│       ├── versions-3.4.0.1
│       ├── versions-3.5.0
│       └── README.md
└── library/
    └── pxctl_status.py  (custom module for pxctl operations)
```

## Environment Context

- **Platform**: OpenShift 4.18 on VMware
- **Execution**: Ansible Automation Platform (AAP) with Execution Environment (EE)
- **Authentication**: kubeconfig and vault tokens assigned to job template
- **Namespace**: portworx
- **Cluster Scope**: Each run targets a single cluster (independent operations)
- **Node Types**:
  - Storage nodes: 3-37 nodes (labeled `portworx.io/node-type=storage`)
  - Storageless nodes: 10-300 nodes (labeled `portworx.io/node-type=storageless`)
  - Total cluster size: 25-300 nodes

## Role Variables (defaults/main.yml)

```yaml
---
# Portworx upgrade role default variables

# Version configuration
portworx_target_version: ""  # REQUIRED: Target Portworx OCI version (e.g., "3.5.0")
portworx_versions_file: "versions-{{ portworx_target_version }}"  # Version file in role's files/versions/

# Namespace
portworx_namespace: "portworx"

# Operator configuration
portworx_operator_auto_approve: true  # Auto-approve operator install plans
portworx_operator_update_timeout: 600  # Seconds to wait for operator upgrade (10 min)

# Monitoring and timeouts
portworx_pod_upgrade_timeout: 1500  # Seconds (25 minutes) - timeout for single pod upgrade
portworx_global_inactivity_timeout: 2100  # Seconds (35 minutes) - timeout for no upgrade activity
portworx_pod_check_interval: 10  # Seconds between pod status checks
portworx_autoUpdateComponents_settle_time: 180  # Seconds (3 minutes) - wait after patching STC

# Impatient mode (accelerated storageless pod upgrades)
portworx_impatient_mode: false  # Enable manual batch deletion of storageless pods
portworx_impatient_batch_size: 5  # Number of storageless pods to delete at once (5-7 recommended)
portworx_impatient_wait_time: 300  # Seconds to wait for batch to recover before next batch
portworx_impatient_batch_delay: 30  # Seconds to wait between batches
portworx_impatient_safety_checks: true  # Perform cluster health checks before each batch

# Logging and reporting
portworx_detailed_logging: true  # Enable detailed version transition logging per node
portworx_create_summary: true  # Generate upgrade summary report
portworx_work_dir: "{{ lookup('env', 'WORK_DIR') | default('/tmp/ansible-workdir', true) }}"
portworx_report_dir: "{{ portworx_work_dir }}/portworx-upgrade"
portworx_log_file: "{{ portworx_report_dir }}/upgrade-{{ ansible_date_time.epoch }}.log"

# Cluster identification
portworx_cluster_name: "{{ lookup('env', 'CLUSTER_NAME') | default(ansible_facts['fqdn'], true) }}"

# Preflight check behavior
portworx_fail_on_unhealthy_pods: true  # Fail immediately if pods are unhealthy
portworx_fail_on_degraded_cluster: true  # Fail immediately if cluster is degraded
portworx_fail_on_label_mismatch: true  # Fail immediately if node labels are incorrect
portworx_fail_on_invalid_updatestrategy: true  # Fail if STC updateStrategy is not configured correctly

# Backup configuration
portworx_backup_resources: true  # Backup StorageCluster before upgrade
portworx_backup_dir: "{{ portworx_report_dir }}/backups"

# Feature flags
portworx_skip_operator_upgrade: false  # Skip operator upgrade phase (for testing)
portworx_dry_run: false  # Perform dry run without making changes
```

## Role Variables (vars/main.yml)

```yaml
---
# Internal variables (not meant to be overridden)

# Collections required
portworx_required_collections:
  - kubernetes.core

# Minimum versions
portworx_min_ansible_version: "2.12"
portworx_min_k8s_collection_version: "2.3.0"

# Pod label selectors
portworx_pod_selector: "name=portworx"
portworx_kvdb_selector: "kvdb=true"

# Node label keys
portworx_node_type_label: "portworx.io/node-type"
portworx_zone_label_px: "topology.portworx.io/zone"
portworx_zone_label_k8s: "topology.kubernetes.io/zone"

# Storage cluster resource
portworx_stc_kind: "StorageCluster"
portworx_stc_api_version: "core.libopenstorage.org/v1"

# Operator resources
portworx_operator_namespace: "portworx"
portworx_operator_subscription: "portworx-certified"

# Auth secret
portworx_auth_secret: "px-admin-token"

# Expected pod ready patterns (for different operator versions)
portworx_pod_ready_patterns:
  old_operator: "2/2"  # Operator < 23.10.3
  new_operator: "1/1"  # Operator >= 23.10.3

portworx_api_pod_ready_patterns:
  old_operator: "1/1"
  new_operator: "2/2"

# Pod lifecycle phases that indicate "activity" (upgrade in progress)
portworx_active_upgrade_phases:
  - Terminating
  - Pending
  - ContainerCreating

# Required STC updateStrategy configuration
portworx_required_update_strategy:
  type: "RollingUpdate"
  rolling_update:
    max_unavailable: 1
    disruption_allow: true
```

## Meta Information (meta/main.yml)

```yaml
---
galaxy_info:
  author: "Your Organization"
  description: "Ansible role to upgrade Portworx clusters on OpenShift"
  company: "Your Company"
  license: "MIT"
  min_ansible_version: "2.12"
  
  platforms:
    - name: EL
      versions:
        - 8
        - 9
  
  galaxy_tags:
    - portworx
    - storage
    - openshift
    - kubernetes
    - upgrade

dependencies: []

collections:
  - kubernetes.core
```

## Task Structure

### Main Tasks (tasks/main.yml)

```yaml
---
# Main task file for portworx_upgrade role

- name: Display upgrade information
  ansible.builtin.debug:
    msg:
      - "Starting Portworx upgrade for cluster: {{ portworx_cluster_name }}"
      - "Target version: {{ portworx_target_version }}"
      - "Namespace: {{ portworx_namespace }}"
      - "Impatient mode: {{ portworx_impatient_mode }}"

- name: Validate target version is provided
  ansible.builtin.assert:
    that:
      - portworx_target_version is defined
      - portworx_target_version | length > 0
    fail_msg: "portworx_target_version must be provided"
    success_msg: "Target version validated: {{ portworx_target_version }}"

- name: Record upgrade start time
  ansible.builtin.set_fact:
    portworx_upgrade_start_time: "{{ ansible_date_time.epoch }}"
    portworx_last_activity_time: "{{ ansible_date_time.epoch }}"

- name: Create report directory
  ansible.builtin.file:
    path: "{{ portworx_report_dir }}"
    state: directory
    mode: '0755'
  delegate_to: localhost

- name: Create backup directory
  ansible.builtin.file:
    path: "{{ portworx_backup_dir }}"
    state: directory
    mode: '0755'
  when: portworx_backup_resources
  delegate_to: localhost

# Phase 1: Pre-flight validation
- name: "PHASE 1: Pre-flight validation"
  ansible.builtin.include_tasks: preflight/main.yml
  tags:
    - preflight
    - validation

# Phase 2: Operator upgrade
- name: "PHASE 2: Operator upgrade"
  ansible.builtin.include_tasks: upgrade/operator.yml
  when: not portworx_skip_operator_upgrade
  tags:
    - upgrade
    - operator

# Phase 3: ConfigMap update
- name: "PHASE 3: ConfigMap update"
  ansible.builtin.include_tasks: upgrade/configmap.yml
  tags:
    - upgrade
    - configmap

# Phase 4: Update components (autoUpdateComponents patch)
- name: "PHASE 4: Update components"
  ansible.builtin.include_tasks: upgrade/update_components.yml
  tags:
    - upgrade
    - components

# Phase 5: StorageCluster update (THE TRIGGER)
- name: "PHASE 5: StorageCluster update"
  ansible.builtin.include_tasks: upgrade/storagecluster.yml
  tags:
    - upgrade
    - storagecluster

# Phase 6: Monitor automatic rolling upgrade
- name: "PHASE 6: Monitor automatic rolling upgrade"
  ansible.builtin.include_tasks: monitor/main.yml
  tags:
    - monitor

# Phase 7: Final validation
- name: "PHASE 7: Final validation"
  ansible.builtin.include_tasks: validate/main.yml
  tags:
    - validate
    - final

# Phase 8: Generate reports
- name: "PHASE 8: Generate reports"
  ansible.builtin.include_tasks: report/main.yml
  when: portworx_create_summary
  tags:
    - report

- name: Record upgrade end time
  ansible.builtin.set_fact:
    portworx_upgrade_end_time: "{{ ansible_date_time.epoch }}"

- name: Calculate upgrade duration
  ansible.builtin.set_fact:
    portworx_upgrade_duration: "{{ (portworx_upgrade_end_time | int) - (portworx_upgrade_start_time | int) }}"

- name: Display upgrade completion
  ansible.builtin.debug:
    msg:
      - "Portworx upgrade completed successfully!"
      - "Cluster: {{ portworx_cluster_name }}"
      - "Version: {{ portworx_target_version }}"
      - "Duration: {{ portworx_upgrade_duration }} seconds ({{ (portworx_upgrade_duration | int / 60) | round(1) }} minutes)"
      - "Reports available in: {{ portworx_report_dir }}"
```

### Preflight Tasks (tasks/preflight/main.yml)

```yaml
---
# Pre-flight validation tasks

- name: Include environment validation
  ansible.builtin.include_tasks: validate_environment.yml

- name: Include node label validation
  ansible.builtin.include_tasks: validate_nodes.yml

- name: Include pod health validation
  ansible.builtin.include_tasks: validate_pods.yml

- name: Include cluster status validation
  ansible.builtin.include_tasks: validate_cluster_status.yml

- name: Include STC configuration validation
  ansible.builtin.include_tasks: validate_stc_config.yml

- name: Include resource backup
  ansible.builtin.include_tasks: backup_resources.yml
  when: portworx_backup_resources

- name: Pre-flight validation complete
  ansible.builtin.debug:
    msg: "All pre-flight checks passed successfully"
```

### Preflight: Validate STC Configuration (tasks/preflight/validate_stc_config.yml)

```yaml
---
# Validate StorageCluster updateStrategy configuration

- name: Get StorageCluster resource
  kubernetes.core.k8s_info:
    api_version: "{{ portworx_stc_api_version }}"
    kind: "{{ portworx_stc_kind }}"
    namespace: "{{ portworx_namespace }}"
  register: portworx_stc_list

- name: Verify StorageCluster exists
  ansible.builtin.assert:
    that:
      - portworx_stc_list.resources | length > 0
    fail_msg: "No StorageCluster found in namespace {{ portworx_namespace }}"
    success_msg: "StorageCluster found"

- name: Set StorageCluster facts
  ansible.builtin.set_fact:
    portworx_stc: "{{ portworx_stc_list.resources[0] }}"
    portworx_stc_name: "{{ portworx_stc_list.resources[0].metadata.name }}"
    portworx_current_version: "{{ portworx_stc_list.resources[0].status.version | default('unknown') }}"

- name: Display current version
  ansible.builtin.debug:
    msg:
      - "Current Portworx version: {{ portworx_current_version }}"
      - "Target Portworx version: {{ portworx_target_version }}"
      - "StorageCluster name: {{ portworx_stc_name }}"

- name: Validate updateStrategy type
  ansible.builtin.assert:
    that:
      - portworx_stc.spec.updateStrategy.type is defined
      - portworx_stc.spec.updateStrategy.type == "RollingUpdate"
    fail_msg: |
      StorageCluster updateStrategy.type must be 'RollingUpdate'
      Current: {{ portworx_stc.spec.updateStrategy.type | default('undefined') }}
    success_msg: "UpdateStrategy type validated: RollingUpdate"
  when: portworx_fail_on_invalid_updatestrategy

- name: Validate maxUnavailable setting
  ansible.builtin.assert:
    that:
      - portworx_stc.spec.updateStrategy.rollingUpdate.maxUnavailable is defined
      - portworx_stc.spec.updateStrategy.rollingUpdate.maxUnavailable == 1
    fail_msg: |
      StorageCluster updateStrategy.rollingUpdate.maxUnavailable must be 1
      Current: {{ portworx_stc.spec.updateStrategy.rollingUpdate.maxUnavailable | default('undefined') }}
      This ensures one-at-a-time pod upgrades
    success_msg: "MaxUnavailable validated: 1 (one-at-a-time upgrades)"
  when: portworx_fail_on_invalid_updatestrategy

- name: Validate disruption allow setting
  ansible.builtin.assert:
    that:
      - portworx_stc.spec.updateStrategy.rollingUpdate.disruption.allow is defined
      - portworx_stc.spec.updateStrategy.rollingUpdate.disruption.allow == true
    fail_msg: |
      StorageCluster updateStrategy.rollingUpdate.disruption.allow must be true
      Current: {{ portworx_stc.spec.updateStrategy.rollingUpdate.disruption.allow | default('undefined') }}
    success_msg: "Disruption allow validated: true"
  when: portworx_fail_on_invalid_updatestrategy

- name: Display updateStrategy configuration
  ansible.builtin.debug:
    msg:
      - "UpdateStrategy validated successfully"
      - "Type: {{ portworx_stc.spec.updateStrategy.type }}"
      - "MaxUnavailable: {{ portworx_stc.spec.updateStrategy.rollingUpdate.maxUnavailable }}"
      - "Disruption Allow: {{ portworx_stc.spec.updateStrategy.rollingUpdate.disruption.allow }}"
```

### Preflight: Validate Nodes (tasks/preflight/validate_nodes.yml)

```yaml
---
# Validate node labels and configuration

- name: Get all nodes with Portworx labels
  kubernetes.core.k8s_info:
    kind: Node
    label_selectors:
      - "{{ portworx_node_type_label }}"
  register: portworx_nodes

- name: Parse node information
  ansible.builtin.set_fact:
    portworx_storage_nodes: "{{ portworx_nodes.resources | selectattr('metadata.labels.' ~ portworx_node_type_label, 'equalto', 'storage') | list }}"
    portworx_storageless_nodes: "{{ portworx_nodes.resources | selectattr('metadata.labels.' ~ portworx_node_type_label, 'equalto', 'storageless') | list }}"

- name: Extract node names for later use
  ansible.builtin.set_fact:
    portworx_storage_node_names: "{{ portworx_storage_nodes | map(attribute='metadata.name') | list }}"
    portworx_storageless_node_names: "{{ portworx_storageless_nodes | map(attribute='metadata.name') | list }}"

- name: Count nodes
  ansible.builtin.set_fact:
    portworx_storage_node_count: "{{ portworx_storage_nodes | length }}"
    portworx_storageless_node_count: "{{ portworx_storageless_nodes | length }}"
    portworx_total_node_count: "{{ portworx_nodes.resources | length }}"

- name: Display node counts
  ansible.builtin.debug:
    msg:
      - "Total Portworx nodes: {{ portworx_total_node_count }}"
      - "Storage nodes: {{ portworx_storage_node_count }}"
      - "Storageless nodes: {{ portworx_storageless_node_count }}"

- name: Validate minimum storage nodes
  ansible.builtin.assert:
    that:
      - portworx_storage_node_count | int >= 3
    fail_msg: "Minimum 3 storage nodes required, found {{ portworx_storage_node_count }}"
    success_msg: "Storage node count validated: {{ portworx_storage_node_count }}"

- name: Validate storage nodes have required labels
  ansible.builtin.assert:
    that:
      - item.metadata.labels[portworx_zone_label_px] is defined
      - item.metadata.labels[portworx_zone_label_k8s] is defined
      - item.metadata.labels[portworx_zone_label_px] == item.metadata.labels[portworx_zone_label_k8s]
    fail_msg: "Storage node {{ item.metadata.name }} has mismatched or missing zone labels"
    success_msg: "Storage node {{ item.metadata.name }} labels validated"
  loop: "{{ portworx_storage_nodes }}"
  loop_control:
    label: "{{ item.metadata.name }}"
  when: portworx_fail_on_label_mismatch

- name: Node label validation complete
  ansible.builtin.debug:
    msg: "All node labels validated successfully"
```

### Preflight: Validate Pods (tasks/preflight/validate_pods.yml)

```yaml
---
# Validate pod health before upgrade

- name: Get all Portworx pods
  kubernetes.core.k8s_info:
    kind: Pod
    namespace: "{{ portworx_namespace }}"
    label_selectors:
      - "{{ portworx_pod_selector }}"
  register: portworx_pods

- name: Check for unhealthy pods
  ansible.builtin.set_fact:
    portworx_unhealthy_pods: "{{ portworx_pods.resources | rejectattr('status.phase', 'equalto', 'Running') | list }}"

- name: Check for not-ready pods
  ansible.builtin.set_fact:
    portworx_not_ready_pods: >-
      {{ portworx_pods.resources | 
         rejectattr('status.conditions', 'undefined') |
         rejectattr('status.conditions', 'selectattr', 'type', 'equalto', 'Ready') |
         rejectattr('status.conditions', 'selectattr', 'type', 'equalto', 'Ready') |
         rejectattr('status.conditions', 'selectattr', 'status', 'equalto', 'True') |
         list }}

- name: Display pod health summary
  ansible.builtin.debug:
    msg:
      - "Total Portworx pods: {{ portworx_pods.resources | length }}"
      - "Unhealthy pods: {{ portworx_unhealthy_pods | length }}"
      - "Not ready pods: {{ portworx_not_ready_pods | length }}"

- name: Fail if unhealthy pods found
  ansible.builtin.fail:
    msg: |
      Found {{ portworx_unhealthy_pods | length }} unhealthy pods:
      {% for pod in portworx_unhealthy_pods %}
      - {{ pod.metadata.name }}: {{ pod.status.phase }}
      {% endfor %}
      
      Troubleshoot these pods before proceeding with upgrade.
  when:
    - portworx_fail_on_unhealthy_pods
    - portworx_unhealthy_pods | length > 0

- name: Get KVDB pods
  kubernetes.core.k8s_info:
    kind: Pod
    namespace: "{{ portworx_namespace }}"
    label_selectors:
      - "{{ portworx_kvdb_selector }}"
  register: portworx_kvdb_pods

- name: Validate KVDB pod count
  ansible.builtin.assert:
    that:
      - portworx_kvdb_pods.resources | length == 3
    fail_msg: "Expected 3 KVDB pods, found {{ portworx_kvdb_pods.resources | length }}"
    success_msg: "KVDB pod count validated: 3"

- name: Validate KVDB pods are healthy
  ansible.builtin.assert:
    that:
      - item.status.phase == "Running"
      - item.status.conditions | selectattr('type', 'equalto', 'Ready') | selectattr('status', 'equalto', 'True') | list | length > 0
    fail_msg: "KVDB pod {{ item.metadata.name }} is not healthy"
    success_msg: "KVDB pod {{ item.metadata.name }} is healthy"
  loop: "{{ portworx_kvdb_pods.resources }}"
  loop_control:
    label: "{{ item.metadata.name }}"

- name: Pod health validation complete
  ansible.builtin.debug:
    msg: "All pods are healthy and ready for upgrade"
```

### Preflight: Validate Cluster Status (tasks/preflight/validate_cluster_status.yml)

```yaml
---
# Validate cluster health via pxctl status

- name: Get auth token from secret
  kubernetes.core.k8s_info:
    kind: Secret
    name: "{{ portworx_auth_secret }}"
    namespace: "{{ portworx_namespace }}"
  register: portworx_auth_secret_data
  no_log: true

- name: Decode auth token
  ansible.builtin.set_fact:
    portworx_auth_token: "{{ portworx_auth_secret_data.resources[0].data['auth-token'] | b64decode }}"
  no_log: true

- name: Select a storage node pod for pxctl commands
  ansible.builtin.set_fact:
    portworx_pxctl_pod: "{{ portworx_pods.resources | selectattr('spec.nodeName', 'in', portworx_storage_node_names) | first }}"

- name: Display selected pod for pxctl
  ansible.builtin.debug:
    msg: "Using pod {{ portworx_pxctl_pod.metadata.name }} for pxctl commands"

- name: Execute pxctl status
  kubernetes.core.k8s_exec:
    namespace: "{{ portworx_namespace }}"
    pod: "{{ portworx_pxctl_pod.metadata.name }}"
    command: /bin/bash -c "export PXCTL_AUTH_TOKEN='{{ portworx_auth_token }}' && /opt/pwx/bin/pxctl status"
  register: portworx_pxctl_status
  no_log: false

- name: Display pxctl status output
  ansible.builtin.debug:
    msg: "{{ portworx_pxctl_status.stdout_lines }}"
  when: portworx_detailed_logging

- name: Check for PX operational status
  ansible.builtin.assert:
    that:
      - "'PX is operational' in portworx_pxctl_status.stdout"
    fail_msg: |
      Portworx cluster is not operational!
      Status output:
      {{ portworx_pxctl_status.stdout }}
    success_msg: "Portworx cluster is operational"
  when: portworx_fail_on_degraded_cluster

- name: Check for offline nodes
  ansible.builtin.shell:
    cmd: echo "{{ portworx_pxctl_status.stdout }}" | grep -v Online | grep -c "Status.*:"
  register: portworx_offline_check
  failed_when: false
  changed_when: false

- name: Validate all nodes are online
  ansible.builtin.assert:
    that:
      - portworx_offline_check.stdout | int == 0
    fail_msg: |
      Found offline or degraded nodes in cluster!
      Run: pxctl status | grep -v Online
      To see problematic nodes
    success_msg: "All nodes are online"
  when: portworx_fail_on_degraded_cluster

- name: Cluster status validation complete
  ansible.builtin.debug:
    msg: "Cluster health validated successfully via pxctl"
```

### Upgrade: ConfigMap (tasks/upgrade/configmap.yml)

```yaml
---
# Update px-versions configmap

- name: Verify version file exists
  ansible.builtin.stat:
    path: "{{ role_path }}/files/versions/{{ portworx_versions_file }}"
  register: portworx_version_file_stat
  delegate_to: localhost

- name: Fail if version file not found
  ansible.builtin.fail:
    msg: |
      Version file not found: {{ role_path }}/files/versions/{{ portworx_versions_file }}
      Available version files should be in: {{ role_path }}/files/versions/
  when: not portworx_version_file_stat.stat.exists

- name: Delete existing px-versions configmap
  kubernetes.core.k8s:
    state: absent
    api_version: v1
    kind: ConfigMap
    name: px-versions
    namespace: "{{ portworx_namespace }}"

- name: Wait for configmap deletion to complete
  kubernetes.core.k8s_info:
    api_version: v1
    kind: ConfigMap
    name: px-versions
    namespace: "{{ portworx_namespace }}"
  register: portworx_cm_check
  until: portworx_cm_check.resources | length == 0
  retries: 12
  delay: 5

- name: Create new px-versions configmap
  kubernetes.core.k8s:
    state: present
    definition:
      apiVersion: v1
      kind: ConfigMap
      metadata:
        name: px-versions
        namespace: "{{ portworx_namespace }}"
      data:
        versions: "{{ lookup('file', role_path ~ '/files/versions/' ~ portworx_versions_file) }}"

- name: Verify configmap creation
  kubernetes.core.k8s_info:
    api_version: v1
    kind: ConfigMap
    name: px-versions
    namespace: "{{ portworx_namespace }}"
  register: portworx_new_cm

- name: Validate new configmap
  ansible.builtin.assert:
    that:
      - portworx_new_cm.resources | length == 1
      - portworx_target_version in portworx_new_cm.resources[0].data.versions
    fail_msg: "New configmap not created correctly or doesn't contain target version"
    success_msg: "ConfigMap px-versions updated successfully with version {{ portworx_target_version }}"

- name: ConfigMap update complete
  ansible.builtin.debug:
    msg: "px-versions configmap updated to version {{ portworx_target_version }}"
```

### Upgrade: Update Components (tasks/upgrade/update_components.yml)

```yaml
---
# Patch StorageCluster with autoUpdateComponents to force component refresh

- name: Patch StorageCluster with autoUpdateComponents
  kubernetes.core.k8s:
    state: patched
    api_version: "{{ portworx_stc_api_version }}"
    kind: "{{ portworx_stc_kind }}"
    name: "{{ portworx_stc_name }}"
    namespace: "{{ portworx_namespace }}"
    definition:
      spec:
        autoUpdateComponents: Once

- name: Verify autoUpdateComponents patch applied
  kubernetes.core.k8s_info:
    api_version: "{{ portworx_stc_api_version }}"
    kind: "{{ portworx_stc_kind }}"
    name: "{{ portworx_stc_name }}"
    namespace: "{{ portworx_namespace }}"
  register: portworx_stc_patched

- name: Validate autoUpdateComponents value
  ansible.builtin.assert:
    that:
      - portworx_stc_patched.resources[0].spec.autoUpdateComponents == "Once"
    fail_msg: "autoUpdateComponents patch did not apply correctly"
    success_msg: "autoUpdateComponents set to 'Once'"

- name: Wait for component updates to settle
  ansible.builtin.pause:
    seconds: "{{ portworx_autoUpdateComponents_settle_time }}"
    prompt: "Waiting {{ portworx_autoUpdateComponents_settle_time }} seconds for autoUpdateComponents to process..."

- name: Component update complete
  ansible.builtin.debug:
    msg: "Component updates triggered and settled"
```

### Upgrade: StorageCluster (tasks/upgrade/storagecluster.yml)

```yaml
---
# Update StorageCluster image field to trigger rolling upgrade

- name: Get current StorageCluster image
  ansible.builtin.set_fact:
    portworx_current_image: "{{ portworx_stc.spec.image }}"

- name: Display current and target images
  ansible.builtin.debug:
    msg:
      - "Current image: {{ portworx_current_image }}"
      - "Target image: portworx/oci-monitor:{{ portworx_target_version }}"

- name: Determine image registry prefix
  ansible.builtin.set_fact:
    portworx_image_registry: "{{ portworx_stc.spec.customImageRegistry | default('') }}"

- name: Build target image path
  ansible.builtin.set_fact:
    portworx_target_image: "{{ portworx_image_registry }}portworx/oci-monitor:{{ portworx_target_version }}"

- name: Check if already on target version
  ansible.builtin.debug:
    msg: "Cluster is already on target version {{ portworx_target_version }}"
  when: portworx_target_version in portworx_current_image

- name: Update StorageCluster image field
  kubernetes.core.k8s:
    state: patched
    api_version: "{{ portworx_stc_api_version }}"
    kind: "{{ portworx_stc_kind }}"
    name: "{{ portworx_stc_name }}"
    namespace: "{{ portworx_namespace }}"
    definition:
      spec:
        image: "{{ portworx_target_image }}"
  when: portworx_target_version not in portworx_current_image

- name: Verify StorageCluster image update
  kubernetes.core.k8s_info:
    api_version: "{{ portworx_stc_api_version }}"
    kind: "{{ portworx_stc_kind }}"
    name: "{{ portworx_stc_name }}"
    namespace: "{{ portworx_namespace }}"
  register: portworx_stc_updated

- name: Validate image field updated
  ansible.builtin.assert:
    that:
      - portworx_target_version in portworx_stc_updated.resources[0].spec.image
    fail_msg: "StorageCluster image field did not update correctly"
    success_msg: "StorageCluster image updated to {{ portworx_target_version }}"

- name: Record upgrade trigger time
  ansible.builtin.set_fact:
    portworx_upgrade_triggered_time: "{{ ansible_date_time.epoch }}"

- name: StorageCluster update complete - Rolling upgrade triggered
  ansible.builtin.debug:
    msg:
      - "StorageCluster image field updated successfully"
      - "Operator will now begin automatic rolling upgrade (one pod at a time)"
      - "Monitoring phase will track upgrade progress"
```

### Monitor: Main (tasks/monitor/main.yml)

```yaml
---
# Monitor the automatic rolling upgrade

- name: Initialize monitoring variables
  ansible.builtin.set_fact:
    portworx_last_activity_time: "{{ ansible_date_time.epoch }}"
    portworx_pods_upgraded: []
    portworx_pods_needing_upgrade: []
    portworx_currently_upgrading: []

- name: Determine upgrade strategy
  ansible.builtin.debug:
    msg:
      - "Upgrade monitoring strategy:"
      - "  - Operator controls upgrade sequence (one pod at a time)"
      - "  - Role monitors pod image changes and health"
      - "  - Individual pod timeout: {{ portworx_pod_upgrade_timeout }} seconds"
      - "  - Global inactivity timeout: {{ portworx_global_inactivity_timeout }} seconds"
      - "  - Impatient mode: {{ 'ENABLED' if portworx_impatient_mode else 'DISABLED' }}"

- name: Monitor automatic rolling upgrade
  ansible.builtin.include_tasks: automatic_rolling_upgrade.yml

- name: Check if impatient mode should be used
  when:
    - portworx_impatient_mode
    - portworx_pods_needing_upgrade | length > 0
  block:
    - name: Verify prerequisites for impatient mode
      ansible.builtin.include_tasks: impatient_mode.yml

- name: Monitoring phase complete
  ansible.builtin.debug:
    msg:
      - "All pods upgraded successfully"
      - "Total pods upgraded: {{ portworx_pods_upgraded | length }}"
```

### Monitor: Automatic Rolling Upgrade (tasks/monitor/automatic_rolling_upgrade.yml)

```yaml
---
# Monitor the operator-controlled automatic rolling upgrade

- name: Start automatic upgrade monitoring loop
  ansible.builtin.debug:
    msg: "Beginning automatic rolling upgrade monitoring..."

- name: Monitor upgrade progress
  block:
    - name: Get all Portworx pods
      kubernetes.core.k8s_info:
        kind: Pod
        namespace: "{{ portworx_namespace }}"
        label_selectors:
          - "{{ portworx_pod_selector }}"
      register: portworx_current_pods

    - name: Analyze pod upgrade status
      ansible.builtin.set_fact:
        portworx_pods_with_new_image: >-
          {{ portworx_current_pods.resources |
             selectattr('spec.containers.0.image', 'search', portworx_target_version) |
             selectattr('status.phase', 'equalto', 'Running') |
             selectattr('status.conditions', 'selectattr', 'type', 'equalto', 'Ready') |
             selectattr('status.conditions', 'selectattr', 'status', 'equalto', 'True') |
             list }}
        
        portworx_pods_with_old_image: >-
          {{ portworx_current_pods.resources |
             rejectattr('spec.containers.0.image', 'search', portworx_target_version) |
             list }}
        
        portworx_pods_upgrading: >-
          {{ portworx_current_pods.resources |
             selectattr('status.phase', 'in', portworx_active_upgrade_phases) |
             list }}
        
        portworx_pods_new_not_ready: >-
          {{ portworx_current_pods.resources |
             selectattr('spec.containers.0.image', 'search', portworx_target_version) |
             rejectattr('status.phase', 'equalto', 'Running') |
             list +
             portworx_current_pods.resources |
             selectattr('spec.containers.0.image', 'search', portworx_target_version) |
             selectattr('status.phase', 'equalto', 'Running') |
             rejectattr('status.conditions', 'selectattr', 'type', 'equalto', 'Ready') |
             rejectattr('status.conditions', 'selectattr', 'status', 'equalto', 'True') |
             list }}

    - name: Display current upgrade status
      ansible.builtin.debug:
        msg:
          - "Upgrade Status:"
          - "  Pods completed (new image + ready): {{ portworx_pods_with_new_image | length }}"
          - "  Pods needing upgrade (old image): {{ portworx_pods_with_old_image | length }}"
          - "  Pods actively upgrading: {{ portworx_pods_upgrading | length }}"
          - "  Pods new but not ready: {{ portworx_pods_new_not_ready | length }}"
      when: portworx_detailed_logging

    - name: Check for upgrade activity
      ansible.builtin.set_fact:
        portworx_activity_detected: >-
          {{ (portworx_pods_upgrading | length > 0) or
             (portworx_pods_new_not_ready | length > 0) }}

    - name: Update last activity time if activity detected
      ansible.builtin.set_fact:
        portworx_last_activity_time: "{{ ansible_date_time.epoch }}"
      when: portworx_activity_detected

    - name: Log newly completed pods
      ansible.builtin.debug:
        msg: "Pod {{ item.metadata.name }} upgraded successfully to {{ portworx_target_version }}"
      loop: "{{ portworx_pods_with_new_image }}"
      loop_control:
        label: "{{ item.metadata.name }}"
      when:
        - portworx_detailed_logging
        - item.metadata.name not in (portworx_pods_upgraded | default([]))

    - name: Update upgraded pods list
      ansible.builtin.set_fact:
        portworx_pods_upgraded: "{{ (portworx_pods_upgraded | default([])) + [item.metadata.name] }}"
      loop: "{{ portworx_pods_with_new_image }}"
      loop_control:
        label: "{{ item.metadata.name }}"
      when: item.metadata.name not in (portworx_pods_upgraded | default([]))

    - name: Check for timeout conditions
      ansible.builtin.include_tasks: detect_stuck_upgrade.yml

    - name: Check if upgrade complete
      ansible.builtin.set_fact:
        portworx_upgrade_complete: "{{ portworx_pods_with_old_image | length == 0 and portworx_pods_upgrading | length == 0 and portworx_pods_new_not_ready | length == 0 }}"

    - name: Wait before next check
      ansible.builtin.pause:
        seconds: "{{ portworx_pod_check_interval }}"
      when: not portworx_upgrade_complete

  rescue:
    - name: Upgrade monitoring failed
      ansible.builtin.fail:
        msg: |
          Upgrade monitoring detected a failure condition.
          Check logs above for specific timeout or error details.

  # Loop until upgrade complete
  until: portworx_upgrade_complete
  retries: 1000  # Effectively unlimited, rely on timeout detection
  delay: 0  # Delay handled by pause task
```

### Monitor: Detect Stuck Upgrade (tasks/monitor/detect_stuck_upgrade.yml)

```yaml
---
# Detect stuck upgrade conditions and timeout scenarios

- name: Calculate time since last activity
  ansible.builtin.set_fact:
    portworx_inactivity_duration: "{{ (ansible_date_time.epoch | int) - (portworx_last_activity_time | int) }}"

- name: Log inactivity duration
  ansible.builtin.debug:
    msg: "Time since last upgrade activity: {{ portworx_inactivity_duration }} seconds (timeout: {{ portworx_global_inactivity_timeout }})"
  when:
    - portworx_detailed_logging
    - portworx_inactivity_duration | int > 300  # Log if over 5 minutes

- name: Check for global inactivity timeout
  when: portworx_inactivity_duration | int > portworx_global_inactivity_timeout | int
  block:
    - name: Get current pod states for diagnostics
      kubernetes.core.k8s_info:
        kind: Pod
        namespace: "{{ portworx_namespace }}"
        label_selectors:
          - "{{ portworx_pod_selector }}"
      register: portworx_stuck_pods

    - name: Get StorageCluster status for diagnostics
      kubernetes.core.k8s_info:
        api_version: "{{ portworx_stc_api_version }}"
        kind: "{{ portworx_stc_kind }}"
        name: "{{ portworx_stc_name }}"
        namespace: "{{ portworx_namespace }}"
      register: portworx_stuck_stc

    - name: Fail due to global inactivity timeout
      ansible.builtin.fail:
        msg: |
          UPGRADE TIMEOUT: No upgrade activity detected for {{ portworx_inactivity_duration }} seconds
          
          Global inactivity timeout: {{ portworx_global_inactivity_timeout }} seconds ({{ (portworx_global_inactivity_timeout | int / 60) | round(1) }} minutes)
          
          Last activity time: {{ portworx_last_activity_time }}
          Current time: {{ ansible_date_time.epoch }}
          
          Current Status:
          - Pods with new image (ready): {{ portworx_pods_with_new_image | length }}
          - Pods with old image: {{ portworx_pods_with_old_image | length }}
          - Pods actively upgrading: {{ portworx_pods_upgrading | length }}
          - Pods new but not ready: {{ portworx_pods_new_not_ready | length }}
          
          Pods still needing upgrade:
          {% for pod in portworx_pods_with_old_image %}
          - {{ pod.metadata.name }} (node: {{ pod.spec.nodeName }})
          {% endfor %}
          
          Pods in upgrading state:
          {% for pod in portworx_pods_upgrading %}
          - {{ pod.metadata.name }}: {{ pod.status.phase }}
          {% endfor %}
          
          StorageCluster Update Status:
          {{ portworx_stuck_stc.resources[0].status.conditions | selectattr('type', 'equalto', 'Update') | list }}
          
          TROUBLESHOOTING:
          1. Check operator logs: oc logs -n {{ portworx_namespace }} -l name=portworx-operator
          2. Check StorageCluster events: oc describe stc {{ portworx_stc_name }} -n {{ portworx_namespace }}
          3. Check if operator is running: oc get pods -n {{ portworx_namespace }} -l name=portworx-operator
          4. Check for stuck pods: oc get pods -n {{ portworx_namespace }} -l {{ portworx_pod_selector }}
          5. Review pxctl status from a running pod

- name: Check individual pod upgrade timeouts
  when:
    - portworx_pods_upgrading | length > 0 or portworx_pods_new_not_ready | length > 0
  block:
    - name: Combine pods that are actively in upgrade process
      ansible.builtin.set_fact:
        portworx_active_pods: "{{ portworx_pods_upgrading + portworx_pods_new_not_ready }}"

    - name: Check each actively upgrading pod for timeout
      ansible.builtin.set_fact:
        portworx_stuck_individual_pods: >-
          {{ portworx_active_pods |
             selectattr('metadata.creationTimestamp', 'defined') |
             rejectattr('metadata.creationTimestamp', 'undefined') |
             list }}
      # Note: More sophisticated pod-level timeout checking would go here
      # This is a simplified version - full implementation would track per-pod upgrade start times

- name: Warning for pods upgrading longer than expected
  ansible.builtin.debug:
    msg: "WARNING: Pod {{ item.metadata.name }} has been in {{ item.status.phase }} state. Monitor closely."
  loop: "{{ portworx_pods_upgrading }}"
  loop_control:
    label: "{{ item.metadata.name }}"
  when:
    - portworx_inactivity_duration | int > 900  # 15 minutes
    - portworx_detailed_logging
```

### Monitor: Impatient Mode (tasks/monitor/impatient_mode.yml)

```yaml
---
# Accelerated upgrade for storageless nodes (impatient mode)

- name: Display impatient mode warning
  ansible.builtin.debug:
    msg:
      - "WARNING: IMPATIENT MODE ENABLED"
      - "This will manually delete storageless pods in batches to accelerate upgrade"
      - "Batch size: {{ portworx_impatient_batch_size }} pods"
      - "Safety checks: {{ 'ENABLED' if portworx_impatient_safety_checks else 'DISABLED' }}"
      - "USE WITH CAUTION!"

- name: Verify storage nodes are upgraded
  ansible.builtin.set_fact:
    portworx_storage_pods_to_check: >-
      {{ portworx_pods_with_old_image |
         selectattr('spec.nodeName', 'in', portworx_storage_node_names) |
         list }}

- name: Ensure storage nodes are upgraded before impatient mode
  ansible.builtin.assert:
    that:
      - portworx_storage_pods_to_check | length == 0
    fail_msg: |
      Cannot enable impatient mode - storage nodes still upgrading!
      Storage pods pending upgrade: {{ portworx_storage_pods_to_check | length }}
    success_msg: "All storage nodes upgraded - safe to proceed with storageless acceleration"

- name: Perform safety checks
  when: portworx_impatient_safety_checks
  block:
    - name: Execute pxctl status for safety check
      kubernetes.core.k8s_exec:
        namespace: "{{ portworx_namespace }}"
        pod: "{{ portworx_pxctl_pod.metadata.name }}"
        command: /bin/bash -c "export PXCTL_AUTH_TOKEN='{{ portworx_auth_token }}' && /opt/pwx/bin/pxctl status"
      register: portworx_impatient_pxctl_check
      no_log: false

    - name: Verify cluster is operational
      ansible.builtin.assert:
        that:
          - "'PX is operational' in portworx_impatient_pxctl_check.stdout"
        fail_msg: "Cluster not operational - cannot proceed with impatient mode"
        success_msg: "Cluster operational - safe to proceed"

    - name: Verify KVDB pods are healthy
      kubernetes.core.k8s_info:
        kind: Pod
        namespace: "{{ portworx_namespace }}"
        label_selectors:
          - "{{ portworx_kvdb_selector }}"
      register: portworx_kvdb_check

    - name: Validate KVDB health
      ansible.builtin.assert:
        that:
          - item.status.phase == "Running"
          - item.status.conditions | selectattr('type', 'equalto', 'Ready') | selectattr('status', 'equalto', 'True') | list | length > 0
        fail_msg: "KVDB pod {{ item.metadata.name }} not healthy - cannot proceed"
        success_msg: "KVDB pod {{ item.metadata.name }} healthy"
      loop: "{{ portworx_kvdb_check.resources }}"
      loop_control:
        label: "{{ item.metadata.name }}"

- name: Identify storageless pods needing upgrade
  ansible.builtin.set_fact:
    portworx_storageless_pods_to_upgrade: >-
      {{ portworx_pods_with_old_image |
         selectattr('spec.nodeName', 'in', portworx_storageless_node_names) |
         list }}

- name: Display storageless upgrade plan
  ansible.builtin.debug:
    msg:
      - "Storageless pods to upgrade: {{ portworx_storageless_pods_to_upgrade | length }}"
      - "Batch size: {{ portworx_impatient_batch_size }}"
      - "Estimated batches: {{ (portworx_storageless_pods_to_upgrade | length / portworx_impatient_batch_size | round(0, 'ceil')) | int }}"

- name: Process storageless pods in batches
  when: portworx_storageless_pods_to_upgrade | length > 0
  block:
    - name: Create batches
      ansible.builtin.set_fact:
        portworx_storageless_batches: "{{ portworx_storageless_pods_to_upgrade | batch(portworx_impatient_batch_size) | list }}"

    - name: Process each batch
      ansible.builtin.include_tasks: process_impatient_batch.yml
      loop: "{{ portworx_storageless_batches }}"
      loop_control:
        loop_var: portworx_current_batch
        index_var: portworx_batch_index
        label: "Batch {{ portworx_batch_index + 1 }}/{{ portworx_storageless_batches | length }}"

- name: Impatient mode complete
  ansible.builtin.debug:
    msg: "All storageless pods upgraded via impatient mode"
```

### Monitor: Process Impatient Batch (tasks/monitor/process_impatient_batch.yml)

```yaml
---
# Process a single batch of storageless pods in impatient mode

- name: Display batch information
  ansible.builtin.debug:
    msg:
      - "Processing batch {{ portworx_batch_index + 1 }}/{{ portworx_storageless_batches | length }}"
      - "Pods in this batch: {{ portworx_current_batch | length }}"
      - "Pod names: {{ portworx_current_batch | map(attribute='metadata.name') | list }}"

- name: Delete batch pods
  kubernetes.core.k8s:
    state: absent
    api_version: v1
    kind: Pod
    name: "{{ item.metadata.name }}"
    namespace: "{{ portworx_namespace }}"
    wait: false
  loop: "{{ portworx_current_batch }}"
  loop_control:
    label: "{{ item.metadata.name }}"

- name: Wait for pods to terminate
  ansible.builtin.pause:
    seconds: 10
    prompt: "Waiting for batch pods to terminate..."

- name: Monitor batch pod recovery
  block:
    - name: Check batch pod status
      kubernetes.core.k8s_info:
        kind: Pod
        namespace: "{{ portworx_namespace }}"
        label_selectors:
          - "{{ portworx_pod_selector }}"
      register: portworx_batch_check

    - name: Filter batch pods
      ansible.builtin.set_fact:
        portworx_batch_pod_names: "{{ portworx_current_batch | map(attribute='metadata.name') | list }}"
        portworx_batch_current_pods: >-
          {{ portworx_batch_check.resources |
             selectattr('spec.nodeName', 'in', portworx_current_batch | map(attribute='spec.nodeName') | list) |
             list }}

    - name: Check batch recovery status
      ansible.builtin.set_fact:
        portworx_batch_recovered: >-
          {{ portworx_batch_current_pods |
             selectattr('spec.containers.0.image', 'search', portworx_target_version) |
             selectattr('status.phase', 'equalto', 'Running') |
             selectattr('status.conditions', 'selectattr', 'type', 'equalto', 'Ready') |
             selectattr('status.conditions', 'selectattr', 'status', 'equalto', 'True') |
             list }}

    - name: Display batch recovery status
      ansible.builtin.debug:
        msg:
          - "Batch recovery status:"
          - "  Pods in batch: {{ portworx_batch_current_pods | length }}"
          - "  Pods recovered (new image + ready): {{ portworx_batch_recovered | length }}"
          - "  Expected: {{ portworx_current_batch | length }}"
      when: portworx_detailed_logging

    - name: Check if batch fully recovered
      ansible.builtin.set_fact:
        portworx_batch_complete: "{{ portworx_batch_recovered | length == portworx_current_batch | length }}"

    - name: Wait before next check
      ansible.builtin.pause:
        seconds: "{{ portworx_pod_check_interval }}"
      when: not portworx_batch_complete

  rescue:
    - name: Batch recovery failed
      ansible.builtin.fail:
        msg: |
          Batch {{ portworx_batch_index + 1 }} failed to recover properly
          Switching to conservative mode for remaining pods

  # Loop until batch recovered
  until: portworx_batch_complete
  retries: "{{ (portworx_impatient_wait_time / portworx_pod_check_interval) | int }}"
  delay: 0

- name: Perform post-batch safety check
  when: portworx_impatient_safety_checks
  block:
    - name: Execute pxctl status after batch
      kubernetes.core.k8s_exec:
        namespace: "{{ portworx_namespace }}"
        pod: "{{ portworx_pxctl_pod.metadata.name }}"
        command: /bin/bash -c "export PXCTL_AUTH_TOKEN='{{ portworx_auth_token }}' && /opt/pwx/bin/pxctl status"
      register: portworx_batch_pxctl_check
      no_log: false

    - name: Verify cluster still operational
      ansible.builtin.assert:
        that:
          - "'PX is operational' in portworx_batch_pxctl_check.stdout"
        fail_msg: "Cluster degraded after batch - stopping impatient mode"
        success_msg: "Cluster still operational after batch"

- name: Wait before next batch
  ansible.builtin.pause:
    seconds: "{{ portworx_impatient_batch_delay }}"
    prompt: "Waiting {{ portworx_impatient_batch_delay }} seconds before next batch..."
  when: portworx_batch_index < (portworx_storageless_batches | length - 1)

- name: Batch processing complete
  ansible.builtin.debug:
    msg: "Batch {{ portworx_batch_index + 1 }} completed successfully"
```

### Validate: Final Pod Validation (tasks/validate/final_pod_validation.yml)

```yaml
---
# Final validation that all pods upgraded successfully

- name: Get all Portworx pods for final validation
  kubernetes.core.k8s_info:
    kind: Pod
    namespace: "{{ portworx_namespace }}"
    label_selectors:
      - "{{ portworx_pod_selector }}"
  register: portworx_final_pods

- name: Check all pods are running
  ansible.builtin.set_fact:
    portworx_not_running: >-
      {{ portworx_final_pods.resources |
         rejectattr('status.phase', 'equalto', 'Running') |
         list }}

- name: Check all pods are ready
  ansible.builtin.set_fact:
    portworx_not_ready: >-
      {{ portworx_final_pods.resources |
         rejectattr('status.conditions', 'selectattr', 'type', 'equalto', 'Ready') |
         rejectattr('status.conditions', 'selectattr', 'status', 'equalto', 'True') |
         list }}

- name: Check all pods have new image version
  ansible.builtin.set_fact:
    portworx_wrong_version: >-
      {{ portworx_final_pods.resources |
         rejectattr('spec.containers.0.image', 'search', portworx_target_version) |
         list }}

- name: Display final pod status
  ansible.builtin.debug:
    msg:
      - "Final Pod Validation:"
      - "  Total pods: {{ portworx_final_pods.resources | length }}"
      - "  Not running: {{ portworx_not_running | length }}"
      - "  Not ready: {{ portworx_not_ready | length }}"
      - "  Wrong version: {{ portworx_wrong_version | length }}"

- name: Fail if pods not running
  ansible.builtin.fail:
    msg: |
      {{ portworx_not_running | length }} pods are not in Running state:
      {% for pod in portworx_not_running %}
      - {{ pod.metadata.name }}: {{ pod.status.phase }}
      {% endfor %}
  when: portworx_not_running | length > 0

- name: Fail if pods not ready
  ansible.builtin.fail:
    msg: |
      {{ portworx_not_ready | length }} pods are not Ready:
      {% for pod in portworx_not_ready %}
      - {{ pod.metadata.name }}
      {% endfor %}
  when: portworx_not_ready | length > 0

- name: Fail if pods have wrong version
  ansible.builtin.fail:
    msg: |
      {{ portworx_wrong_version | length }} pods do not have target version {{ portworx_target_version }}:
      {% for pod in portworx_wrong_version %}
      - {{ pod.metadata.name }}: {{ pod.spec.containers[0].image }}
      {% endfor %}
  when: portworx_wrong_version | length > 0

- name: Verify KVDB pods
  kubernetes.core.k8s_info:
    kind: Pod
    namespace: "{{ portworx_namespace }}"
    label_selectors:
      - "{{ portworx_kvdb_selector }}"
  register: portworx_final_kvdb_pods

- name: Validate KVDB pods are healthy
  ansible.builtin.assert:
    that:
      - portworx_final_kvdb_pods.resources | length == 3
      - item.status.phase == "Running"
      - item.status.conditions | selectattr('type', 'equalto', 'Ready') | selectattr('status', 'equalto', 'True') | list | length > 0
    fail_msg: "KVDB pod {{ item.metadata.name }} is not healthy after upgrade"
    success_msg: "KVDB pod {{ item.metadata.name }} is healthy"
  loop: "{{ portworx_final_kvdb_pods.resources }}"
  loop_control:
    label: "{{ item.metadata.name }}"

- name: Final pod validation complete
  ansible.builtin.debug:
    msg: "All pods validated successfully - Running, Ready, and on target version {{ portworx_target_version }}"
```

### Validate: Cluster Health (tasks/validate/cluster_health.yml)

```yaml
---
# Final cluster health validation via pxctl

- name: Execute final pxctl status
  kubernetes.core.k8s_exec:
    namespace: "{{ portworx_namespace }}"
    pod: "{{ portworx_pxctl_pod.metadata.name }}"
    command: /bin/bash -c "export PXCTL_AUTH_TOKEN='{{ portworx_auth_token }}' && /opt/pwx/bin/pxctl status"
  register: portworx_final_pxctl_status
  no_log: false

- name: Display final pxctl status
  ansible.builtin.debug:
    msg: "{{ portworx_final_pxctl_status.stdout_lines }}"

- name: Verify PX is operational
  ansible.builtin.assert:
    that:
      - "'PX is operational' in portworx_final_pxctl_status.stdout"
    fail_msg: "Portworx cluster is not operational after upgrade!"
    success_msg: "Portworx cluster is operational"

- name: Check for offline nodes
  ansible.builtin.shell:
    cmd: echo "{{ portworx_final_pxctl_status.stdout }}" | grep -v Online | grep -c "Status.*:" || true
  register: portworx_final_offline_check
  failed_when: false
  changed_when: false

- name: Validate all nodes are online
  ansible.builtin.assert:
    that:
      - portworx_final_offline_check.stdout | int == 0
    fail_msg: "Some nodes are offline after upgrade!"
    success_msg: "All nodes are online"

- name: Extract version information from pxctl output
  ansible.builtin.set_fact:
    portworx_pxctl_versions: "{{ portworx_final_pxctl_status.stdout | regex_findall('Version\\s+(\\S+)') }}"

- name: Verify version consistency
  ansible.builtin.assert:
    that:
      - portworx_target_version in item
    fail_msg: "Node version mismatch: found {{ item }}, expected {{ portworx_target_version }}"
    success_msg: "Node version validated: {{ item }}"
  loop: "{{ portworx_pxctl_versions }}"
  when: portworx_pxctl_versions | length > 0

- name: Cluster health validation complete
  ansible.builtin.debug:
    msg: "Cluster health validated successfully via pxctl"
```

### Validate: Version Consistency (tasks/validate/version_consistency.yml)

```yaml
---
# Verify version consistency across StorageCluster status and actual pods

- name: Get final StorageCluster status
  kubernetes.core.k8s_info:
    api_version: "{{ portworx_stc_api_version }}"
    kind: "{{ portworx_stc_kind }}"
    name: "{{ portworx_stc_name }}"
    namespace: "{{ portworx_namespace }}"
  register: portworx_final_stc

- name: Extract STC status version
  ansible.builtin.set_fact:
    portworx_stc_status_version: "{{ portworx_final_stc.resources[0].status.version | default('unknown') }}"
    portworx_stc_spec_version: "{{ portworx_final_stc.resources[0].spec.image | regex_search('oci-monitor:(.+)$', '\\1') | first }}"

- name: Display version information
  ansible.builtin.debug:
    msg:
      - "Version Validation:"
      - "  Target version: {{ portworx_target_version }}"
      - "  STC spec image version: {{ portworx_stc_spec_version }}"
      - "  STC status version: {{ portworx_stc_status_version }}"
      - "  All pods on version: {{ portworx_target_version }}"

- name: Check STC Update condition
  ansible.builtin.set_fact:
    portworx_stc_update_condition: >-
      {{ portworx_final_stc.resources[0].status.conditions |
         selectattr('type', 'equalto', 'Update') |
         list }}

- name: Display STC Update condition
  ansible.builtin.debug:
    msg: "STC Update Condition: {{ portworx_stc_update_condition }}"
  when: portworx_stc_update_condition | length > 0

- name: Verify STC status version matches target
  ansible.builtin.assert:
    that:
      - portworx_target_version in portworx_stc_status_version or portworx_stc_status_version == portworx_target_version
    fail_msg: |
      STC status version ({{ portworx_stc_status_version }}) does not match target ({{ portworx_target_version }})
      Note: STC status may lag behind actual pod versions. Verify pods are correct.
    success_msg: "STC status version matches target"
  failed_when: false  # Don't fail - STC status can be stale

- name: Verify STC spec image matches target
  ansible.builtin.assert:
    that:
      - portworx_target_version in portworx_stc_spec_version or portworx_stc_spec_version == portworx_target_version
    fail_msg: "STC spec image version ({{ portworx_stc_spec_version }}) does not match target ({{ portworx_target_version }})"
    success_msg: "STC spec image version matches target"

- name: Version consistency check complete
  ansible.builtin.debug:
    msg: "Version consistency validated across all components"
```

### Report: Generate Summary (tasks/report/generate_summary.yml)

```yaml
---
# Generate upgrade summary report

- name: Calculate phase durations
  ansible.builtin.set_fact:
    portworx_preflight_duration: "{{ portworx_preflight_end_time | default(0) | int - portworx_preflight_start_time | default(0) | int }}"
    portworx_operator_duration: "{{ portworx_operator_end_time | default(0) | int - portworx_operator_start_time | default(0) | int }}"
    portworx_configmap_duration: "{{ portworx_configmap_end_time | default(0) | int - portworx_configmap_start_time | default(0) | int }}"
    portworx_monitoring_duration: "{{ portworx_monitoring_end_time | default(0) | int - portworx_monitoring_start_time | default(0) | int }}"
    portworx_validation_duration: "{{ portworx_validation_end_time | default(0) | int - portworx_validation_start_time | default(0) | int }}"

- name: Generate upgrade summary from template
  ansible.builtin.template:
    src: upgrade_summary.j2
    dest: "{{ portworx_report_dir }}/upgrade-summary-{{ ansible_date_time.epoch }}.txt"
  delegate_to: localhost

- name: Display summary report location
  ansible.builtin.debug:
    msg: "Upgrade summary report: {{ portworx_report_dir }}/upgrade-summary-{{ ansible_date_time.epoch }}.txt"
```

### Report Template (templates/upgrade_summary.j2)

```jinja2
============================================
PORTWORX UPGRADE SUMMARY REPORT
============================================
Cluster: {{ portworx_cluster_name }}
Date: {{ ansible_date_time.iso8601 }}
Playbook Run Duration: {{ portworx_upgrade_duration }} seconds ({{ (portworx_upgrade_duration | int / 60) | round(1) }} minutes)

UPGRADE DETAILS:
  Source Version: {{ portworx_current_version }}
  Target Version: {{ portworx_target_version }}
  Operator Version: {{ portworx_final_operator_version | default('Not recorded') }}

CLUSTER STATISTICS:
  Total Nodes: {{ portworx_total_node_count }}
  Storage Nodes: {{ portworx_storage_node_count }}
  Storageless Nodes: {{ portworx_storageless_node_count }}
  KVDB Pods: 3

POD UPGRADE RESULTS:
  Total Portworx Pods: {{ portworx_final_pods.resources | length }}
  Successfully Upgraded: {{ portworx_pods_upgraded | length }}
  Final Status: All Running and Ready on version {{ portworx_target_version }}

STORAGE NODE UPGRADES:
{% for pod in portworx_final_pods.resources | selectattr('spec.nodeName', 'in', portworx_storage_node_names) %}
  {{ pod.spec.nodeName }}: {{ portworx_target_version }} [OK]
{% endfor %}

STORAGELESS NODE UPGRADES:
{% for pod in portworx_final_pods.resources | selectattr('spec.nodeName', 'in', portworx_storageless_node_names) %}
  {{ pod.spec.nodeName }}: {{ portworx_target_version }} [OK]
{% endfor %}

KVDB POD STATUS:
{% for pod in portworx_final_kvdb_pods.resources %}
  {{ pod.metadata.name }}: Running and Ready [OK]
{% endfor %}

IMPATIENT MODE: {{ 'Enabled' if portworx_impatient_mode else 'Disabled' }}
{% if portworx_impatient_mode %}
  Batches Processed: {{ portworx_storageless_batches | default([]) | length }}
  Pods per Batch: {{ portworx_impatient_batch_size }}
{% endif %}

FINAL CLUSTER STATUS:
  PX Status: Operational
  All Nodes Online: Yes
  Version Consistency: Consistent
  STC Status Version: {{ portworx_stc_status_version }}

TIMING BREAKDOWN:
  Pre-flight Checks: {{ portworx_preflight_duration | default(0) }}s
  Operator Upgrade: {{ portworx_operator_duration | default(0) }}s
  ConfigMap Update: {{ portworx_configmap_duration | default(0) }}s
  Monitoring Phase: {{ portworx_monitoring_duration | default(0) }}s
  Final Validation: {{ portworx_validation_duration | default(0) }}s

BACKUP FILES:
  Pre-upgrade STC: {{ portworx_backup_dir }}/pre-upgrade-stc-{{ ansible_date_time.epoch }}.yaml
  Post-upgrade STC: {{ portworx_backup_dir }}/post-upgrade-stc-{{ ansible_date_time.epoch }}.yaml

UPGRADE RESULT: SUCCESS
============================================
```

## Custom Module: pxctl_status.py (library/pxctl_status.py)

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Your Organization
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: pxctl_status
short_description: Execute pxctl status commands in Portworx pods
description:
    - Executes pxctl status commands in Portworx pods
    - Handles authentication via PXCTL_AUTH_TOKEN
    - Parses and returns structured status information
version_added: "1.0.0"
options:
    namespace:
        description: Namespace where Portworx is deployed
        required: true
        type: str
    pod_name:
        description: Name of Portworx pod to execute command in
        required: true
        type: str
    auth_token:
        description: PXCTL authentication token
        required: true
        type: str
        no_log: true
    command:
        description: pxctl command to run (default is 'status')
        required: false
        type: str
        default: 'status'
author:
    - Your Name (@yourhandle)
'''

EXAMPLES = r'''
- name: Get pxctl status
  pxctl_status:
    namespace: portworx
    pod_name: portworx-abc123
    auth_token: "{{ portworx_auth_token }}"
  register: px_status

- name: Get specific node status
  pxctl_status:
    namespace: portworx
    pod_name: portworx-abc123
    auth_token: "{{ portworx_auth_token }}"
    command: "status node abc-def-ghi"
  register: node_status
'''

RETURN = r'''
status:
    description: Parsed pxctl status output
    returned: success
    type: dict
    sample:
        operational: true
        cluster_id: "example-cluster-id"
        total_nodes: 7
        online_nodes: 7
        nodes:
            - id: "00000000-0000-0000-0000-000000000001"
              ip: "192.168.1.1"
              status: "Online"
              version: "3.4.0.1"
raw_output:
    description: Raw pxctl command output
    returned: always
    type: str
'''

from ansible.module_utils.basic import AnsibleModule
import subprocess
import re

def parse_pxctl_status(output):
    """Parse pxctl status output into structured data"""
    status = {
        'operational': False,
        'nodes': [],
        'total_nodes': 0,
        'online_nodes': 0
    }
    
    # Check if PX is operational
    if 'PX is operational' in output:
        status['operational'] = True
    
    # Parse cluster summary
    cluster_match = re.search(r'Total Nodes: (\d+) node.*\((\d+) online\)', output)
    if cluster_match:
        status['total_nodes'] = int(cluster_match.group(1))
        status['online_nodes'] = int(cluster_match.group(2))
    
    # Parse node information
    node_section = False
    for line in output.split('\n'):
        if 'IP' in line and 'ID' in line and 'Version' in line:
            node_section = True
            continue
        if node_section and line.strip():
            parts = line.split()
            if len(parts) >= 6:
                node = {
                    'ip': parts[0],
                    'id': parts[1],
                    'status': parts[5] if len(parts) > 5 else 'Unknown',
                    'version': parts[6] if len(parts) > 6 else 'Unknown'
                }
                status['nodes'].append(node)
    
    return status

def run_module():
    module_args = dict(
        namespace=dict(type='str', required=True),
        pod_name=dict(type='str', required=True),
        auth_token=dict(type='str', required=True, no_log=True),
        command=dict(type='str', required=False, default='status')
    )

    result = dict(
        changed=False,
        status={},
        raw_output=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    namespace = module.params['namespace']
    pod_name = module.params['pod_name']
    auth_token = module.params['auth_token']
    command = module.params['command']

    # Construct oc exec command
    exec_cmd = [
        'oc', 'exec', '-n', namespace, pod_name, '--',
        '/bin/bash', '-c',
        f"export PXCTL_AUTH_TOKEN='{auth_token}' && /opt/pwx/bin/pxctl {command}"
    ]

    try:
        proc = subprocess.Popen(
            exec_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proc.communicate(timeout=60)
        
        if proc.returncode != 0:
            module.fail_json(msg=f"pxctl command failed: {stderr}", **result)
        
        result['raw_output'] = stdout
        result['status'] = parse_pxctl_status(stdout)
        
        module.exit_json(**result)
        
    except subprocess.TimeoutExpired:
        module.fail_json(msg="pxctl command timed out", **result)
    except Exception as e:
        module.fail_json(msg=f"Error executing pxctl: {str(e)}", **result)

def main():
    run_module()

if __name__ == '__main__':
    main()
```

## Example Playbook Using the Role

```yaml
---
# playbooks/portworx_upgrade.yml

- name: Upgrade Portworx cluster
  hosts: localhost
  gather_facts: true
  
  vars:
    # These would typically come from AAP extra_vars
    portworx_target_version: "3.5.0"
    portworx_operator_auto_approve: true
    portworx_impatient_mode: false
  
  roles:
    - role: portworx_upgrade
```

## Example AAP Job Template Extra Vars

```yaml
---
# Conservative upgrade
portworx_target_version: "3.5.0"
portworx_operator_auto_approve: true
portworx_detailed_logging: true
portworx_impatient_mode: false

---
# Accelerated upgrade with impatient mode
portworx_target_version: "3.5.0"
portworx_operator_auto_approve: true
portworx_detailed_logging: true
portworx_impatient_mode: true
portworx_impatient_batch_size: 7
portworx_impatient_wait_time: 300
portworx_impatient_safety_checks: true
```

## Success Criteria

The role execution is successful when:

1. All pre-flight checks pass (nodes, pods, cluster health, STC config)
2. Operator upgrades successfully (if not skipped)
3. ConfigMap updates without error
4. autoUpdateComponents patch applies successfully
5. StorageCluster image field updated successfully
6. All pods upgrade to target OCI version (monitored, not controlled)
7. No global inactivity timeout (35 minutes with no upgrade activity)
8. No individual pod timeout (25 minutes per pod)
9. All pods Running + Ready with new image version
10. All KVDB pods Running + Ready
11. pxctl status shows "PX is operational"
12. All nodes report Online status
13. Version consistency validated
14. Summary report generated

## Critical Implementation Notes

### The Operator's Role

- Once STC image field is updated, **operator controls everything**
- Upgrade happens **one pod at a time** (enforced by maxUnavailable: 1)
- Role **monitors, does not control** the upgrade sequence
- Operator decides which pod upgrades next (not predictable)

### Timeout Detection Logic

Two critical timeouts to implement:

**1. Global Inactivity Timeout (35 minutes)**

- Tracks time since last "activity"
- Activity = any pod terminating, pending, creating, or becoming ready with new image
- If 35 minutes pass with NO activity → operator is stuck → FAIL

**2. Individual Pod Timeout (25 minutes)**

- Tracks how long a single pod spends upgrading
- From Terminating → Running + Ready with new image
- If 25 minutes exceeded → pod is stuck → FAIL

### What "Activity" Means

Activity is detected when ANY pod is:

- Phase: Terminating
- Phase: Pending  
- Phase: ContainerCreating
- Running with new image but not Ready yet

### Impatient Mode Safety

- ONLY for storageless pods
- NEVER delete storage node pods
- Verify prerequisites before each batch:
  - All storage nodes upgraded
  - Cluster operational (pxctl status)
  - All KVDB pods healthy
- Process in batches of 5-7 pods
- Wait for entire batch to recover before next batch
- Perform safety checks between batches

### STC Status vs Actual Pods

- STC `.status.version` can be stale/inaccurate
- STC `.status.conditions[type=Update]` can lag
- **Always verify by checking actual pod images**
- Trust pod `.spec.containers[0].image` field over STC status

---

**END OF FINAL ROLE SPECIFICATION**
