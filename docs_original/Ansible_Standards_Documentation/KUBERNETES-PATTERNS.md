# Kubernetes/OpenShift Automation Patterns

**Document Version:** 1.0.0  
**Last Updated:** 2025-02-10  
**Target Audience:** Engineers automating Kubernetes/OpenShift with Ansible  
**Purpose:** Comprehensive guide to Kubernetes-native Ansible automation patterns

---

## Table of Contents

1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [Resource Management Patterns](#resource-management-patterns)
4. [Pod Lifecycle Patterns](#pod-lifecycle-patterns)
5. [Operator-Based Automation](#operator-based-automation)
6. [CRD Interaction Patterns](#crd-interaction-patterns)
7. [Multi-Cluster Patterns](#multi-cluster-patterns)
8. [Monitoring and Observability](#monitoring-and-observability)
9. [Troubleshooting Patterns](#troubleshooting-patterns)
10. [Performance Optimization](#performance-optimization)

---

## Introduction

### Why Native Kubernetes Modules Matter

**The Problem with Shell Commands:**

```yaml
# Fragile - breaks with formatting changes
- name: Count pods
  shell: oc get pods -n {{ ns }} | grep Running | wc -l
  register: count

# What happens when:
# - Column order changes?
# - Pod names contain "Running"?
# - Terminal width changes output?
# - Need to filter by label?
# - Need container status?
```

**The Solution with Native Modules:**

```yaml
# Robust - uses API directly
- name: Get pod information
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: "{{ ns }}"
    label_selectors:
      - "app=myapp"
  register: pods

- name: Count running pods
  ansible.builtin.set_fact:
    running_count: "{{ pods.resources | selectattr('status.phase', 'equalto', 'Running') | list | length }}"

# Benefits:
# - Never breaks from formatting
# - Access any pod field
# - Complex filtering possible
# - Works across K8s versions
```

### Module Overview

**Primary modules for Kubernetes automation:**

| Module | Purpose | Use For |
|--------|---------|---------|
| `kubernetes.core.k8s` | Create/Update/Delete resources | Applying manifests, updating resources |
| `kubernetes.core.k8s_info` | Query resources | Getting current state, checking status |
| `kubernetes.core.k8s_exec` | Execute commands in pods | Running commands, getting pod output |
| `kubernetes.core.k8s_scale` | Scale workloads | Scaling deployments/statefulsets |
| `kubernetes.core.k8s_drain` | Drain nodes | Node maintenance operations |
| `kubernetes.core.k8s_cp` | Copy files to/from pods | File transfers |
| `kubernetes.core.helm` | Helm chart operations | Installing/upgrading charts |

---

## Core Concepts

### Understanding the Kubernetes API

**Resource Structure:**

```yaml
# Every Kubernetes resource has this structure
apiVersion: <group>/<version>  # e.g., apps/v1, v1
kind: <ResourceType>            # e.g., Pod, Deployment
metadata:
  name: <resource-name>
  namespace: <namespace>
  labels:
    key: value
  annotations:
    key: value
spec:
  # Resource-specific specification
status:
  # Current state (read-only)
```

**Accessing Resource Fields:**

```yaml
# Get a deployment
- kubernetes.core.k8s_info:
    api_version: apps/v1
    kind: Deployment
    name: myapp
    namespace: production
  register: deploy

# Access fields
- debug:
    msg: |
      Name: {{ deploy.resources[0].metadata.name }}
      Namespace: {{ deploy.resources[0].metadata.namespace }}
      Replicas: {{ deploy.resources[0].spec.replicas }}
      Ready: {{ deploy.resources[0].status.readyReplicas | default(0) }}
      Image: {{ deploy.resources[0].spec.template.spec.containers[0].image }}
      Labels: {{ deploy.resources[0].metadata.labels }}
```

### Label Selectors

**Understanding label selectors:**

```yaml
# Equality-based selectors
label_selectors:
  - "app=myapp"
  - "environment=production"
  - "tier=frontend"
# Matches: app=myapp AND environment=production AND tier=frontend

# Set-based selectors
label_selectors:
  - "app in (myapp, yourapp)"
  - "tier notin (cache, temp)"
  - "environment"  # Key exists
  - "!deprecated"  # Key does not exist

# Common patterns
label_selectors:
  - "app={{ app_name }}"
  - "release={{ release_name }}"
```

**Real-world example:**

```yaml
- name: Get all application pods across all tiers
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: production
    label_selectors:
      - "app=myapp"
      - "tier in (frontend, backend, worker)"
      - "!canary"  # Exclude canary deployments
  register: app_pods

- name: Categorize pods by tier
  ansible.builtin.set_fact:
    frontend_pods: "{{ app_pods.resources | selectattr('metadata.labels.tier', 'equalto', 'frontend') | list }}"
    backend_pods: "{{ app_pods.resources | selectattr('metadata.labels.tier', 'equalto', 'backend') | list }}"
    worker_pods: "{{ app_pods.resources | selectattr('metadata.labels.tier', 'equalto', 'worker') | list }}"
```

### Field Selectors

**Filtering by resource fields:**

```yaml
# Field selectors (supported fields vary by resource type)
- name: Get running pods only
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: production
    field_selectors:
      - "status.phase=Running"

- name: Get pods on specific node
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    field_selectors:
      - "spec.nodeName={{ node_name }}"

- name: Combine label and field selectors
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: production
    label_selectors:
      - "app=myapp"
    field_selectors:
      - "status.phase!=Failed"
```

---

## Resource Management Patterns

### Pattern 1: Creating Resources

**From inline definition:**

```yaml
- name: Create namespace
  kubernetes.core.k8s:
    state: present
    definition:
      apiVersion: v1
      kind: Namespace
      metadata:
        name: myapp-production
        labels:
          environment: production
          managed-by: ansible

- name: Create deployment
  kubernetes.core.k8s:
    state: present
    definition:
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: myapp
        namespace: myapp-production
        labels:
          app: myapp
          version: v1.2.3
      spec:
        replicas: 3
        selector:
          matchLabels:
            app: myapp
        template:
          metadata:
            labels:
              app: myapp
              version: v1.2.3
          spec:
            containers:
              - name: myapp
                image: "myapp:{{ app_version }}"
                ports:
                  - containerPort: 8080
                    name: http
                env:
                  - name: ENVIRONMENT
                    value: production
                resources:
                  requests:
                    memory: "256Mi"
                    cpu: "100m"
                  limits:
                    memory: "512Mi"
                    cpu: "500m"
```

**From template file:**

```yaml
# templates/deployment.j2
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ app_name }}
  namespace: {{ app_namespace }}
spec:
  replicas: {{ app_replicas }}
  selector:
    matchLabels:
      app: {{ app_name }}
  template:
    metadata:
      labels:
        app: {{ app_name }}
    spec:
      containers:
        - name: {{ app_name }}
          image: {{ app_image }}:{{ app_version }}
          ports:
            - containerPort: {{ app_port }}

# Playbook
- name: Create deployment from template
  kubernetes.core.k8s:
    state: present
    definition: "{{ lookup('template', 'deployment.j2') | from_yaml }}"
```

**From file:**

```yaml
- name: Apply manifest from file
  kubernetes.core.k8s:
    state: present
    src: /path/to/manifest.yaml
    namespace: production

- name: Apply multiple manifests
  kubernetes.core.k8s:
    state: present
    src: "{{ item }}"
  loop:
    - /manifests/namespace.yaml
    - /manifests/deployment.yaml
    - /manifests/service.yaml
```

### Pattern 2: Updating Resources

**Patch existing resource:**

```yaml
- name: Update deployment image
  kubernetes.core.k8s:
    api_version: apps/v1
    kind: Deployment
    name: myapp
    namespace: production
    definition:
      spec:
        template:
          spec:
            containers:
              - name: myapp
                image: "myapp:{{ new_version }}"

- name: Add label to existing resource
  kubernetes.core.k8s:
    api_version: v1
    kind: Service
    name: myapp
    namespace: production
    definition:
      metadata:
        labels:
          monitoring: "enabled"
          team: "platform"

- name: Update environment variable
  kubernetes.core.k8s:
    api_version: apps/v1
    kind: Deployment
    name: myapp
    namespace: production
    definition:
      spec:
        template:
          spec:
            containers:
              - name: myapp
                env:
                  - name: LOG_LEVEL
                    value: debug
```

**Strategic merge patch:**

```yaml
- name: Scale deployment
  kubernetes.core.k8s:
    api_version: apps/v1
    kind: Deployment
    name: myapp
    namespace: production
    merge_type: strategic-merge
    definition:
      spec:
        replicas: "{{ new_replica_count }}"

- name: Update resource requests
  kubernetes.core.k8s:
    api_version: apps/v1
    kind: Deployment
    name: myapp
    namespace: production
    merge_type: strategic-merge
    definition:
      spec:
        template:
          spec:
            containers:
              - name: myapp
                resources:
                  requests:
                    memory: "512Mi"
                    cpu: "200m"
```

### Pattern 3: Deleting Resources

**Delete specific resource:**

```yaml
- name: Delete deployment
  kubernetes.core.k8s:
    api_version: apps/v1
    kind: Deployment
    name: myapp
    namespace: production
    state: absent
    wait: true
    wait_timeout: 300

- name: Delete multiple resources
  kubernetes.core.k8s:
    api_version: v1
    kind: "{{ item.kind }}"
    name: "{{ item.name }}"
    namespace: production
    state: absent
  loop:
    - {kind: Deployment, name: myapp}
    - {kind: Service, name: myapp}
    - {kind: ConfigMap, name: myapp-config}
```

**Delete by label selector:**

```yaml
- name: Delete all canary deployments
  kubernetes.core.k8s:
    api_version: apps/v1
    kind: Deployment
    namespace: production
    state: absent
    label_selectors:
      - "canary=true"
      - "app={{ app_name }}"

- name: Cleanup old jobs
  kubernetes.core.k8s:
    api_version: batch/v1
    kind: Job
    namespace: production
    state: absent
    label_selectors:
      - "job-type=migration"
      - "!keep"
```

### Pattern 4: Conditional Resource Creation

**Create only if doesn't exist:**

```yaml
- name: Check if namespace exists
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Namespace
    name: "{{ app_namespace }}"
  register: namespace_check

- name: Create namespace if missing
  kubernetes.core.k8s:
    state: present
    definition:
      apiVersion: v1
      kind: Namespace
      metadata:
        name: "{{ app_namespace }}"
  when: namespace_check.resources | length == 0

- name: Ensure namespace exists (simpler approach)
  kubernetes.core.k8s:
    state: present
    definition:
      apiVersion: v1
      kind: Namespace
      metadata:
        name: "{{ app_namespace }}"
  # kubernetes.core.k8s is idempotent - safe to always run
```

**Create based on existing state:**

```yaml
- name: Get current deployment
  kubernetes.core.k8s_info:
    api_version: apps/v1
    kind: Deployment
    name: myapp
    namespace: production
  register: current_deployment

- name: Determine if rolling update needed
  ansible.builtin.set_fact:
    update_needed: "{{ current_deployment.resources | length > 0 and current_deployment.resources[0].spec.template.spec.containers[0].image != target_image }}"

- name: Perform rolling update
  kubernetes.core.k8s:
    api_version: apps/v1
    kind: Deployment
    name: myapp
    namespace: production
    definition:
      spec:
        template:
          spec:
            containers:
              - name: myapp
                image: "{{ target_image }}"
  when: update_needed
```

---

## Pod Lifecycle Patterns

### Pattern 1: Waiting for Pods to be Ready

**Basic wait:**

```yaml
- name: Wait for deployment to be ready
  kubernetes.core.k8s_info:
    api_version: apps/v1
    kind: Deployment
    name: myapp
    namespace: production
  register: deployment
  until:
    - deployment.resources[0].status.readyReplicas is defined
    - deployment.resources[0].status.readyReplicas == deployment.resources[0].spec.replicas
  retries: 60
  delay: 5
```

**Advanced wait with conditions:**

```yaml
- name: Wait for pod to be fully ready
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    name: "{{ pod_name }}"
    namespace: production
  register: pod
  until:
    - pod.resources | length > 0
    - pod.resources[0].status.phase == 'Running'
    - pod.resources[0].status.conditions | selectattr('type', 'equalto', 'Ready') | selectattr('status', 'equalto', 'True') | list | length > 0
    - pod.resources[0].status.conditions | selectattr('type', 'equalto', 'ContainersReady') | selectattr('status', 'equalto', 'True') | list | length > 0
  retries: 60
  delay: 10
```

**Wait for multiple pods:**

```yaml
- name: Wait for all application pods to be ready
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: production
    label_selectors:
      - "app=myapp"
  register: app_pods
  until:
    - app_pods.resources | length >= expected_pod_count
    - app_pods.resources | selectattr('status.phase', 'equalto', 'Running') | list | length == app_pods.resources | length
    - app_pods.resources | map(attribute='status.conditions') | select('defined') | list | selectattr('0.type', 'equalto', 'Ready') | selectattr('0.status', 'equalto', 'True') | list | length == app_pods.resources | length
  retries: 120
  delay: 5
```

### Pattern 2: Monitoring Pod State Transitions

**Track pod lifecycle:**

```yaml
- name: Monitor pod state transitions
  block:
    - name: Get pod current state
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Pod
        name: "{{ pod_name }}"
        namespace: production
      register: pod_state
    
    - name: Analyze pod status
      ansible.builtin.set_fact:
        pod_phase: "{{ pod_state.resources[0].status.phase }}"
        container_statuses: "{{ pod_state.resources[0].status.containerStatuses | default([]) }}"
        pod_conditions: "{{ pod_state.resources[0].status.conditions | default([]) }}"
    
    - name: Check for specific conditions
      ansible.builtin.set_fact:
        is_scheduled: "{{ pod_conditions | selectattr('type', 'equalto', 'PodScheduled') | selectattr('status', 'equalto', 'True') | list | length > 0 }}"
        is_initialized: "{{ pod_conditions | selectattr('type', 'equalto', 'Initialized') | selectattr('status', 'equalto', 'True') | list | length > 0 }}"
        is_ready: "{{ pod_conditions | selectattr('type', 'equalto', 'Ready') | selectattr('status', 'equalto', 'True') | list | length > 0 }}"
        containers_ready: "{{ pod_conditions | selectattr('type', 'equalto', 'ContainersReady') | selectattr('status', 'equalto', 'True') | list | length > 0 }}"
    
    - name: Display pod lifecycle state
      ansible.builtin.debug:
        msg: |
          Pod: {{ pod_name }}
          Phase: {{ pod_phase }}
          Scheduled: {{ is_scheduled }}
          Initialized: {{ is_initialized }}
          ContainersReady: {{ containers_ready }}
          Ready: {{ is_ready }}
```

Continue in next response with more patterns...

### Pattern 3: Handling Pod Failures

**Detect and respond to failures:**

```yaml
- name: Check for failed pods
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: production
    label_selectors:
      - "app=myapp"
  register: pods

- name: Identify problem pods
  ansible.builtin.set_fact:
    failed_pods: "{{ pods.resources | selectattr('status.phase', 'in', ['Failed', 'Unknown']) | list }}"
    crash_loop_pods: "{{ pods.resources | selectattr('status.containerStatuses', 'defined') | selectattr('status.containerStatuses.0.state.waiting.reason', 'defined') | selectattr('status.containerStatuses.0.state.waiting.reason', 'equalto', 'CrashLoopBackOff') | list }}"

- name: Get logs from failed pods
  kubernetes.core.k8s_exec:
    namespace: production
    pod: "{{ item.metadata.name }}"
    command: cat /var/log/app.log
  loop: "{{ failed_pods }}"
  loop_control:
    label: "{{ item.metadata.name }}"
  register: failed_logs
  ignore_errors: true

- name: Delete failed pods to trigger recreation
  kubernetes.core.k8s:
    api_version: v1
    kind: Pod
    name: "{{ item.metadata.name }}"
    namespace: production
    state: absent
  loop: "{{ failed_pods }}"
  loop_control:
    label: "{{ item.metadata.name }}"
  when: auto_restart_failed | default(false)
```

---

## Operator-Based Automation

### Understanding Operator Pattern

**Operator-controlled resources:**
- Operator watches Custom Resources
- Operator reconciles desired vs actual state
- Ansible monitors, doesn't control directly

**Example: Storage Cluster Operator**

```yaml
# StorageCluster is the desired state
apiVersion: core.libopenstorage.org/v1
kind: StorageCluster
metadata:
  name: px-cluster
spec:
  image: portworx/oci-monitor:2.13.0  # Desired version

# Operator creates/manages these pods:
# - portworx-abc123 (image: 2.12.0) <- being upgraded
# - portworx-def456 (image: 2.13.0) <- upgraded
# - portworx-ghi789 (image: 2.12.0) <- waiting
```

### Pattern: Monitoring Operator-Controlled Upgrades

**Don't try to control - monitor instead:**

```yaml
---
# roles/storage_upgrade/tasks/monitor.yml
# Monitor operator-controlled rolling upgrade

- name: Initialize monitoring
  ansible.builtin.set_fact:
    upgrade_start_time: "{{ ansible_date_time.epoch }}"
    last_activity_time: "{{ ansible_date_time.epoch }}"
    pod_tracking: {}
    global_timeout: 2100  # 35 minutes
    inactivity_timeout: 2100

- name: Monitor upgrade progress
  block:
    # Get current state from operator-managed pods
    - name: Get storage pods
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Pod
        namespace: kube-system
        label_selectors:
          - "name=portworx"
      register: storage_pods
    
    # Check pod images (operator changes these)
    - name: Analyze upgrade progress
      ansible.builtin.set_fact:
        target_image: "portworx/oci-monitor:{{ target_version }}"
        upgraded_pods: "{{ storage_pods.resources | selectattr('spec.containers[0].image', 'equalto', 'portworx/oci-monitor:' + target_version) | list }}"
        upgrading_pods: "{{ storage_pods.resources | rejectattr('spec.containers[0].image', 'equalto', 'portworx/oci-monitor:' + target_version) | list }}"
    
    # Detect activity (any change in upgraded count)
    - name: Check for activity
      ansible.builtin.set_fact:
        has_activity: "{{ upgraded_pods | length != pod_tracking.get('upgraded_count', 0) }}"
    
    # Update activity timestamp
    - name: Update activity time if progress made
      ansible.builtin.set_fact:
        last_activity_time: "{{ ansible_date_time.epoch }}"
        pod_tracking: "{{ pod_tracking | combine({'upgraded_count': upgraded_pods | length}) }}"
      when: has_activity
    
    # Check timeouts
    - name: Verify timeouts not exceeded
      ansible.builtin.assert:
        that:
          - (ansible_date_time.epoch | int) - (upgrade_start_time | int) <= global_timeout
          - (ansible_date_time.epoch | int) - (last_activity_time | int) <= inactivity_timeout
        fail_msg: |
          Upgrade timeout exceeded
          Global: {{ (ansible_date_time.epoch | int) - (upgrade_start_time | int) }}s / {{ global_timeout }}s
          Inactivity: {{ (ansible_date_time.epoch | int) - (last_activity_time | int) }}s / {{ inactivity_timeout }}s
    
    # Progress reporting
    - name: Display upgrade status
      ansible.builtin.debug:
        msg: |
          Progress: {{ upgraded_pods | length }}/{{ storage_pods.resources | length }} pods upgraded
          Elapsed: {{ (ansible_date_time.epoch | int) - (upgrade_start_time | int) }}s
          Last activity: {{ (ansible_date_time.epoch | int) - (last_activity_time | int) }}s ago
    
    # Wait before next check
    - name: Pause between checks
      ansible.builtin.pause:
        seconds: 15
      when: upgraded_pods | length < storage_pods.resources | length
  
  until: upgraded_pods | length == storage_pods.resources | length
  retries: "{{ (global_timeout / 15) | int }}"
  delay: 15
```

**Key principles:**
1. **Monitor pod images** - Operator controls when images change
2. **Track activity** - Any change in completion count
3. **Don't restart pods** - Operator controls sequence
4. **Dual timeouts** - Global and inactivity

---

## CRD Interaction Patterns

### Pattern: Working with Custom Resources

**Get CRD:**

```yaml
- name: Get custom resource definition
  kubernetes.core.k8s_info:
    api_version: apiextensions.k8s.io/v1
    kind: CustomResourceDefinition
    name: storageclusters.core.libopenstorage.org
  register: crd

- name: Verify CRD exists
  ansible.builtin.assert:
    that:
      - crd.resources | length > 0
    fail_msg: "StorageCluster CRD not installed"

- name: Display CRD version
  ansible.builtin.debug:
    msg: "CRD version: {{ crd.resources[0].spec.versions | map(attribute='name') | list }}"
```

**Create/Update custom resource:**

```yaml
- name: Update StorageCluster
  kubernetes.core.k8s:
    api_version: core.libopenstorage.org/v1
    kind: StorageCluster
    name: px-cluster
    namespace: kube-system
    definition:
      spec:
        image: "portworx/oci-monitor:{{ new_version }}"
        cloudStorage:
          deviceSpecs:
            - "type=gp3,size=150"
        kvdb:
          internal: true
        network:
          dataInterface: eth0
          mgmtInterface: eth0

- name: Verify StorageCluster updated
  kubernetes.core.k8s_info:
    api_version: core.libopenstorage.org/v1
    kind: StorageCluster
    name: px-cluster
    namespace: kube-system
  register: cluster
  until:
    - cluster.resources[0].spec.image == 'portworx/oci-monitor:' + new_version
  retries: 5
  delay: 2
```

### Pattern: Validating CRD Spec

**Check updateStrategy before modification:**

```yaml
- name: Get StorageCluster current config
  kubernetes.core.k8s_info:
    api_version: core.libopenstorage.org/v1
    kind: StorageCluster
    name: px-cluster
    namespace: kube-system
  register: storage_cluster

- name: Validate updateStrategy configuration
  ansible.builtin.assert:
    that:
      - storage_cluster.resources[0].spec.updateStrategy is defined
      - storage_cluster.resources[0].spec.updateStrategy.type == "RollingUpdate"
      - storage_cluster.resources[0].spec.updateStrategy.rollingUpdate.maxUnavailable == 1
    fail_msg: |
      Invalid updateStrategy for safe upgrades
      Current: {{ storage_cluster.resources[0].spec.updateStrategy | default('undefined') }}
      Required: RollingUpdate with maxUnavailable=1

- name: Update updateStrategy if incorrect
  kubernetes.core.k8s:
    api_version: core.libopenstorage.org/v1
    kind: StorageCluster
    name: px-cluster
    namespace: kube-system
    definition:
      spec:
        updateStrategy:
          type: RollingUpdate
          rollingUpdate:
            maxUnavailable: 1
  when: storage_cluster.resources[0].spec.updateStrategy.type != "RollingUpdate"
```

---

## Multi-Cluster Patterns

### Pattern: Sequential Cluster Operations

**Process clusters one at a time:**

```yaml
---
- name: Multi-cluster configuration update
  hosts: k8s_clusters
  gather_facts: false
  serial: 1  # One cluster at a time
  
  vars:
    config_version: "2.0.1"
  
  tasks:
    - name: Display target cluster
      ansible.builtin.debug:
        msg: "Processing cluster: {{ inventory_hostname }}"
    
    - name: Verify cluster connectivity
      kubernetes.core.k8s_cluster_info:
      register: cluster_info
      failed_when: cluster_info is failed
    
    - name: Apply configuration
      kubernetes.core.k8s:
        state: present
        definition: "{{ lookup('template', 'config.j2') }}"
      register: config_result
    
    - name: Wait for rollout complete
      kubernetes.core.k8s_info:
        api_version: apps/v1
        kind: Deployment
        name: "{{ item }}"
        namespace: production
      register: deployment
      until:
        - deployment.resources[0].status.updatedReplicas | default(0) == deployment.resources[0].spec.replicas
        - deployment.resources[0].status.readyReplicas | default(0) == deployment.resources[0].spec.replicas
      retries: 60
      delay: 10
      loop:
        - frontend
        - backend
        - worker
    
    - name: Verify health checks
      ansible.builtin.uri:
        url: "{{ cluster_health_url }}"
        method: GET
        status_code: 200
      retries: 5
      delay: 10
    
    - name: Record successful update
      ansible.builtin.set_fact:
        cluster_update_result:
          cluster: "{{ inventory_hostname }}"
          version: "{{ config_version }}"
          status: "success"
          timestamp: "{{ ansible_date_time.iso8601 }}"
        cacheable: true
    
    # Wait between clusters for monitoring
    - name: Pause before next cluster
      ansible.builtin.pause:
        minutes: 5
        prompt: "Monitoring {{ inventory_hostname }} for issues before proceeding"
      when: inventory_hostname != groups['k8s_clusters'][-1]
```

### Pattern: Parallel with Canary

**Update canary first, then parallel:**

```yaml
---
- name: Canary deployment
  hosts: canary_clusters
  gather_facts: false
  
  tasks:
    - name: Deploy to canary cluster
      ansible.builtin.include_role:
        name: deploy_application
    
    - name: Monitor canary for issues
      ansible.builtin.include_role:
        name: monitor_health
      vars:
        monitoring_duration: 1800  # 30 minutes

- name: Production rollout
  hosts: production_clusters
  gather_facts: false
  serial: 3  # 3 clusters at a time
  
  tasks:
    - name: Verify canary success
      ansible.builtin.assert:
        that:
          - hostvars[groups['canary_clusters'][0]].deployment_status == "success"
        fail_msg: "Canary deployment failed, aborting production rollout"
    
    - name: Deploy to production cluster
      ansible.builtin.include_role:
        name: deploy_application
```

### Pattern: Multi-Cluster Resource Sync

**Ensure identical resources across clusters:**

```yaml
- name: Sync ConfigMap across clusters
  hosts: all_clusters
  gather_facts: false
  
  tasks:
    - name: Get source ConfigMap
      kubernetes.core.k8s_info:
        api_version: v1
        kind: ConfigMap
        name: global-config
        namespace: config
      delegate_to: "{{ groups['primary_cluster'][0] }}"
      register: source_config
      run_once: true
    
    - name: Apply ConfigMap to all clusters
      kubernetes.core.k8s:
        state: present
        definition: "{{ source_config.resources[0] }}"
      register: sync_result
    
    - name: Verify sync completed
      kubernetes.core.k8s_info:
        api_version: v1
        kind: ConfigMap
        name: global-config
        namespace: config
      register: target_config
    
    - name: Compare checksums
      ansible.builtin.assert:
        that:
          - target_config.resources[0].data == source_config.resources[0].data
        fail_msg: "ConfigMap sync failed on {{ inventory_hostname }}"
```

---

## Monitoring and Observability

### Pattern: Event Monitoring

**Collect and analyze events:**

```yaml
- name: Monitor deployment events
  block:
    - name: Get all events in namespace
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Event
        namespace: production
      register: all_events
    
    - name: Filter deployment-related events
      ansible.builtin.set_fact:
        deployment_events: "{{ all_events.resources | selectattr('involvedObject.kind', 'equalto', 'Deployment') | selectattr('involvedObject.name', 'equalto', deployment_name) | list }}"
    
    - name: Categorize events by type
      ansible.builtin.set_fact:
        warning_events: "{{ deployment_events | selectattr('type', 'equalto', 'Warning') | list }}"
        normal_events: "{{ deployment_events | selectattr('type', 'equalto', 'Normal') | list }}"
    
    - name: Display recent warnings
      ansible.builtin.debug:
        msg: |
          Warning Events (last 10):
          {% for event in warning_events | sort(attribute='lastTimestamp', reverse=true) | list[:10] %}
          - {{ event.lastTimestamp }}: {{ event.message }}
          {% endfor %}
      when: warning_events | length > 0
    
    - name: Check for concerning patterns
      ansible.builtin.set_fact:
        has_oom_kills: "{{ warning_events | selectattr('reason', 'equalto', 'OOMKilled') | list | length > 0 }}"
        has_image_pull_errors: "{{ warning_events | selectattr('reason', 'in', ['ErrImagePull', 'ImagePullBackOff']) | list | length > 0 }}"
        has_scheduling_issues: "{{ warning_events | selectattr('reason', 'equalto', 'FailedScheduling') | list | length > 0 }}"
    
    - name: Alert on critical issues
      ansible.builtin.fail:
        msg: |
          Critical issues detected:
          OOM Kills: {{ has_oom_kills }}
          Image Pull Errors: {{ has_image_pull_errors }}
          Scheduling Issues: {{ has_scheduling_issues }}
      when: has_oom_kills or has_image_pull_errors or has_scheduling_issues
```

### Pattern: Resource Usage Monitoring

**Track resource consumption:**

```yaml
- name: Monitor resource usage
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: production
    label_selectors:
      - "app=myapp"
  register: app_pods

- name: Calculate resource requests
  ansible.builtin.set_fact:
    total_memory_requests: "{{ app_pods.resources | map(attribute='spec.containers') | flatten | map(attribute='resources.requests.memory') | select('defined') | map('regex_replace', 'Mi$', '') | map('int') | sum }}"
    total_cpu_requests: "{{ app_pods.resources | map(attribute='spec.containers') | flatten | map(attribute='resources.requests.cpu') | select('defined') | map('regex_replace', 'm$', '') | map('int') | sum }}"

- name: Get node capacity
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Node
  register: nodes

- name: Calculate cluster capacity
  ansible.builtin.set_fact:
    cluster_memory_capacity: "{{ nodes.resources | map(attribute='status.capacity.memory') | map('regex_replace', 'Ki$', '') | map('int') | sum }}"
    cluster_cpu_capacity: "{{ nodes.resources | map(attribute='status.capacity.cpu') | map('int') | sum }}"

- name: Calculate usage percentages
  ansible.builtin.set_fact:
    memory_usage_pct: "{{ ((total_memory_requests * 1024 / cluster_memory_capacity) * 100) | int }}"
    cpu_usage_pct: "{{ ((total_cpu_requests / (cluster_cpu_capacity * 1000)) * 100) | int }}"

- name: Display resource usage
  ansible.builtin.debug:
    msg: |
      Resource Usage:
      Memory: {{ memory_usage_pct }}% ({{ total_memory_requests }}Mi / {{ (cluster_memory_capacity / 1024) | int }}Mi)
      CPU: {{ cpu_usage_pct }}% ({{ total_cpu_requests }}m / {{ cluster_cpu_capacity * 1000 }}m)

- name: Alert if usage high
  ansible.builtin.debug:
    msg: "WARNING: High resource usage detected"
  when: memory_usage_pct > 80 or cpu_usage_pct > 80
```

---

## Troubleshooting Patterns

### Pattern: Debugging Failed Deployments

**Comprehensive failure analysis:**

```yaml
- name: Debug failed deployment
  block:
    # 1. Get deployment status
    - name: Get deployment
      kubernetes.core.k8s_info:
        api_version: apps/v1
        kind: Deployment
        name: myapp
        namespace: production
      register: deployment
    
    # 2. Get replica sets
    - name: Get replica sets
      kubernetes.core.k8s_info:
        api_version: apps/v1
        kind: ReplicaSet
        namespace: production
        label_selectors:
          - "app=myapp"
      register: replicasets
    
    # 3. Get pods
    - name: Get pods
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Pod
        namespace: production
        label_selectors:
          - "app=myapp"
      register: pods
    
    # 4. Identify problem pods
    - name: Find failed pods
      ansible.builtin.set_fact:
        problem_pods: "{{ pods.resources | rejectattr('status.phase', 'equalto', 'Running') | list }}"
    
    # 5. Get logs from problem pods
    - name: Get logs from failed containers
      kubernetes.core.k8s_exec:
        namespace: production
        pod: "{{ item.metadata.name }}"
        container: "{{ item.spec.containers[0].name }}"
        command: sh -c "tail -100 /var/log/* 2>/dev/null || echo 'No logs found'"
      loop: "{{ problem_pods }}"
      loop_control:
        label: "{{ item.metadata.name }}"
      register: pod_logs
      ignore_errors: true
    
    # 6. Get events
    - name: Get deployment events
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Event
        namespace: production
      register: events
    
    - name: Filter relevant events
      ansible.builtin.set_fact:
        deployment_events: "{{ events.resources | selectattr('involvedObject.name', 'in', [deployment.resources[0].metadata.name] + (replicasets.resources | map(attribute='metadata.name') | list) + (pods.resources | map(attribute='metadata.name') | list)) | list }}"
    
    # 7. Generate diagnostic report
    - name: Create diagnostic report
      ansible.builtin.copy:
        content: |
          Deployment Diagnostic Report
          ===========================
          
          Deployment: {{ deployment.resources[0].metadata.name }}
          Namespace: {{ deployment.resources[0].metadata.namespace }}
          Desired Replicas: {{ deployment.resources[0].spec.replicas }}
          Available Replicas: {{ deployment.resources[0].status.availableReplicas | default(0) }}
          
          Deployment Conditions:
          {% for condition in deployment.resources[0].status.conditions | default([]) %}
          - {{ condition.type }}: {{ condition.status }} ({{ condition.reason }})
            Message: {{ condition.message }}
          {% endfor %}
          
          Problem Pods:
          {% for pod in problem_pods %}
          - {{ pod.metadata.name }}:
            Phase: {{ pod.status.phase }}
            Reason: {{ pod.status.reason | default('N/A') }}
            Container Statuses:
            {% for container in pod.status.containerStatuses | default([]) %}
              {{ container.name }}: {{ container.state }}
            {% endfor %}
          {% endfor %}
          
          Recent Events:
          {% for event in deployment_events | sort(attribute='lastTimestamp', reverse=true) | list[:20] %}
          - [{{ event.type }}] {{ event.lastTimestamp }}: {{ event.message }}
          {% endfor %}
          
          Pod Logs:
          {% for log in pod_logs.results %}
          
          === {{ log.item.metadata.name }} ===
          {{ log.stdout | default('No output') }}
          {% endfor %}
        dest: "/tmp/diagnostic-{{ deployment.resources[0].metadata.name }}-{{ ansible_date_time.epoch }}.txt"
      delegate_to: localhost
    
    - name: Display diagnostic summary
      ansible.builtin.debug:
        msg: |
          Deployment {{ deployment.resources[0].metadata.name }} has issues
          Problem pods: {{ problem_pods | length }}
          Recent warnings: {{ deployment_events | selectattr('type', 'equalto', 'Warning') | list | length }}
          
          Diagnostic report: /tmp/diagnostic-{{ deployment.resources[0].metadata.name }}-{{ ansible_date_time.epoch }}.txt
```

---

## Performance Optimization

### Pattern: Batch Operations

**Process resources in batches:**

```yaml
- name: Get all pods to process
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: production
    label_selectors:
      - "batch-process=true"
  register: all_pods

- name: Create batches
  ansible.builtin.set_fact:
    pod_batches: "{{ all_pods.resources | batch(batch_size) | list }}"
  vars:
    batch_size: 10

- name: Process each batch
  block:
    - name: Process pods in batch
      kubernetes.core.k8s:
        api_version: v1
        kind: Pod
        name: "{{ item.metadata.name }}"
        namespace: production
        definition:
          metadata:
            labels:
              processed: "true"
              batch: "{{ batch_index }}"
      loop: "{{ batch }}"
      loop_control:
        label: "{{ item.metadata.name }}"
    
    - name: Wait between batches
      ansible.builtin.pause:
        seconds: 30
      when: batch_index < (pod_batches | length - 1)
  
  loop: "{{ pod_batches }}"
  loop_control:
    loop_var: batch
    index_var: batch_index
    label: "Batch {{ batch_index + 1 }}/{{ pod_batches | length }}"
```

### Pattern: Async Operations

**Run operations in parallel:**

```yaml
- name: Start deployment updates asynchronously
  kubernetes.core.k8s:
    api_version: apps/v1
    kind: Deployment
    name: "{{ item }}"
    namespace: production
    definition:
      spec:
        template:
          spec:
            containers:
              - name: "{{ item }}"
                image: "{{ item }}:{{ new_version }}"
  loop:
    - frontend
    - backend
    - worker
    - api
  async: 1800  # 30 minutes
  poll: 0
  register: async_updates

- name: Do other work while updates run
  ansible.builtin.debug:
    msg: "Updates running in background, continuing with other tasks..."

- name: Check async operation status
  ansible.builtin.async_status:
    jid: "{{ item.ansible_job_id }}"
  loop: "{{ async_updates.results }}"
  loop_control:
    label: "{{ item.item }}"
  register: update_results
  until: update_results.finished
  retries: 180
  delay: 10

- name: Verify all updates succeeded
  ansible.builtin.assert:
    that:
      - item.rc == 0
    fail_msg: "Update failed for {{ item.item }}"
  loop: "{{ update_results.results }}"
  loop_control:
    label: "{{ item.item }}"
```

---

## Quick Reference

### Common Command Translations

| Shell Command | Native Module |
|--------------|---------------|
| `oc get pods` | `kubernetes.core.k8s_info: kind: Pod` |
| `oc get deploy -o json` | `kubernetes.core.k8s_info: kind: Deployment` |
| `oc apply -f file.yaml` | `kubernetes.core.k8s: src: file.yaml` |
| `oc delete pod` | `kubernetes.core.k8s: kind: Pod, state: absent` |
| `oc scale deploy --replicas=3` | `kubernetes.core.k8s_scale` or k8s with definition |
| `oc rsh pod command` | `kubernetes.core.k8s_exec` |
| `oc logs pod` | `kubernetes.core.k8s_log` |
| `oc cp file pod:/path` | `kubernetes.core.k8s_cp` |

### Jinja2 Filters for Kubernetes

```yaml
# Filter pods by phase
running_pods: "{{ pods.resources | selectattr('status.phase', 'equalto', 'Running') | list }}"

# Get pod names
pod_names: "{{ pods.resources | map(attribute='metadata.name') | list }}"

# Filter by label
labeled_pods: "{{ pods.resources | selectattr('metadata.labels.app', 'equalto', 'myapp') | list }}"

# Count ready pods
ready_count: "{{ pods.resources | selectattr('status.conditions', 'defined') | selectattr('status.conditions.0.type', 'equalto', 'Ready') | selectattr('status.conditions.0.status', 'equalto', 'True') | list | length }}"

# Get container images
images: "{{ pods.resources | map(attribute='spec.containers') | flatten | map(attribute='image') | list | unique }}"
```

---

## Best Practices Summary

1. **Always use native modules** over shell commands
2. **Use label selectors** for flexible resource selection
3. **Monitor operator-controlled** resources, don't try to control them
4. **Implement dual timeouts** (global + inactivity)
5. **Validate before operating** on CRDs
6. **Use structured data** instead of text parsing
7. **Process clusters sequentially** unless you have good reason not to
8. **Collect events** for troubleshooting
9. **Batch operations** to avoid overwhelming clusters
10. **Use async operations** for parallelism

---

**Document Version:** 1.0.0  
**Last Updated:** 2025-02-10  
**Maintained By:** Platform Engineering Team

**Related Documents:**
- [Ansible Development Standards](../../ANSIBLE-DEVELOPMENT-STANDARDS.md)
- [Comprehensive Guide](COMPREHENSIVE-GUIDE.md)
- [Migration Guide](MIGRATION-GUIDE.md)

