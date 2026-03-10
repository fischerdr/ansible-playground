# Ansible Development Comprehensive Guide

**Document Version:** 1.0.0  
**Last Updated:** 2025-02-10  
**Target Audience:** Mid-level engineers developing enterprise Ansible automation  
**Purpose:** Detailed examples, deep dives, and real-world patterns for production automation

---

## Document Overview

This comprehensive guide provides detailed explanations, extensive examples, and real-world patterns to complement the [Ansible Development Standards](../../ANSIBLE-DEVELOPMENT-STANDARDS.md) reference document.

**How to use this guide:**

- **Reference the Standards document** for quick lookups
- **Use this guide** for detailed explanations and examples
- **Read sections relevant to your current task**
- **Study anti-patterns** to avoid common mistakes

---

## Table of Contents

1. [The Ansible Mindset: From Shell Scripts to Declarative Automation](#the-ansible-mindset)
2. [Development Environment Deep Dive](#development-environment-deep-dive)
3. [Role Architecture Patterns](#role-architecture-patterns)
4. [Advanced Task Patterns](#advanced-task-patterns)
5. [Kubernetes/OpenShift Native Automation](#kubernetes-openshift-native-automation)
6. [Custom Module Development Guide](#custom-module-development-guide)
7. [Error Handling and Recovery](#error-handling-and-recovery)
8. [Complex Variable Management](#complex-variable-management)
9. [Multi-Cluster Operations](#multi-cluster-operations)
10. [Performance Optimization](#performance-optimization)
11. [Testing Strategies](#testing-strategies)
12. [Real-World Case Studies](#real-world-case-studies)
13. [Troubleshooting Guide](#troubleshooting-guide)
14. [Best Practices Compendium](#best-practices-compendium)

---

## The Ansible Mindset

### Understanding the Paradigm Shift

The transition from shell script thinking to Ansible thinking is the most critical skill for writing quality automation. This section provides deep insight into this mindset shift.

#### Shell Script Thinking: The Imperative Approach

Shell scripts are **imperative** - you tell the computer exactly what steps to execute:

```bash
#!/bin/bash
# Shell script approach - imperative

# Step 1: Check if directory exists
if [ ! -d "/opt/myapp" ]; then
    # Step 2: Create it if missing
    mkdir -p /opt/myapp
    chmod 755 /opt/myapp
fi

# Step 3: Check if config file exists
if [ ! -f "/opt/myapp/config.conf" ]; then
    # Step 4: Create it if missing
    cat > /opt/myapp/config.conf << EOF
setting1=value1
setting2=value2
EOF
    chmod 644 /opt/myapp/config.conf
fi

# Step 5: Check if service is running
if ! systemctl is-active myapp >/dev/null 2>&1; then
    # Step 6: Start it if not running
    systemctl start myapp
fi

# Step 7: Verify service started
sleep 5
if systemctl is-active myapp >/dev/null 2>&1; then
    echo "Service started successfully"
else
    echo "Service failed to start"
    exit 1
fi
```

**Problems with this approach:**

1. **Error-prone**: Must manually check every condition
2. **Not idempotent**: Running twice may cause issues
3. **Hard to maintain**: Logic is mixed with implementation
4. **No rollback**: Failures leave partial state
5. **Manual change detection**: Must track what changed

#### Ansible Thinking: The Declarative Approach

Ansible is **declarative** - you describe the desired end state:

```yaml
---
# Ansible approach - declarative

- name: Ensure application directory exists
  ansible.builtin.file:
    path: /opt/myapp
    state: directory
    mode: '0755'

- name: Ensure application configuration exists
  ansible.builtin.copy:
    dest: /opt/myapp/config.conf
    content: |
      setting1=value1
      setting2=value2
    mode: '0644'

- name: Ensure application service is running
  ansible.builtin.systemd:
    name: myapp
    state: started
    enabled: true
```

**Benefits of declarative approach:**

1. **Self-documenting**: Clear intent from reading tasks
2. **Idempotent**: Safe to run multiple times
3. **Change detection**: Ansible reports what changed
4. **Error handling**: Built into modules
5. **Rollback possible**: Can revert to previous state

### The Five Principles of Ansible Thinking

#### Principle 1: Describe State, Not Steps

**Shell Script Thinking:**

```yaml
# DON'T: Describe steps
- name: Check if user exists
  shell: id myuser
  register: user_check
  failed_when: false

- name: Create user if missing
  shell: useradd myuser
  when: user_check.rc != 0

- name: Set user's shell
  shell: usermod -s /bin/bash myuser

- name: Add user to groups
  shell: usermod -aG docker,admin myuser
```

**Ansible Thinking:**

```yaml
# DO: Describe desired state
- name: Ensure user exists with correct configuration
  ansible.builtin.user:
    name: myuser
    shell: /bin/bash
    groups: [docker, admin]
    state: present
```

**Why this matters:**

- The module handles all the "check if exists" logic
- Idempotent - safe to run repeatedly
- Handles edge cases (user exists but wrong shell, etc.)
- Reports what actually changed

#### Principle 2: Let Modules Do the Work

**Shell Script Thinking:**

```yaml
# DON'T: Parse text output
- name: Get running pods
  shell: oc get pods -n {{ namespace }} | grep Running | wc -l
  register: running_count

- name: Check if enough pods running
  fail:
    msg: "Not enough pods running"
  when: running_count.stdout | int < 3
```

**Ansible Thinking:**

```yaml
# DO: Use structured data from modules
- name: Get pod information
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: "{{ namespace }}"
  register: pods

- name: Count running pods
  ansible.builtin.set_fact:
    running_pods: "{{ pods.resources | selectattr('status.phase', 'equalto', 'Running') | list }}"

- name: Verify sufficient pods running
  ansible.builtin.assert:
    that:
      - running_pods | length >= 3
    fail_msg: "Expected 3+ running pods, found {{ running_pods | length }}"
    success_msg: "{{ running_pods | length }} pods running"
```

**Why this matters:**

- Structured data is easier to work with than text
- No text parsing errors (whitespace, formatting changes)
- Can access any field from the API
- Clear error messages with actual values

#### Principle 3: Embrace Idempotency

**Shell Script Thinking:**

```yaml
# DON'T: Always report as changed
- name: Configure setting
  shell: |
    sed -i 's/old_value/new_value/' /etc/config
  register: result
  # Always shows as "changed" even if value already correct
```

**Ansible Thinking:**

```yaml
# DO: Only change when necessary
- name: Configure setting
  ansible.builtin.lineinfile:
    path: /etc/config
    regexp: '^setting='
    line: 'setting=new_value'
  # Only shows "changed" if line was actually modified
```

**Real-world example - Config file management:**

```yaml
# Shell script approach - always overwrites
- name: Update configuration
  shell: |
    cat > /etc/myapp.conf << EOF
    port=8080
    host=localhost
    debug=false
    EOF
  # Shows "changed" every time, even if content identical

# Ansible approach - only updates if different
- name: Ensure configuration is correct
  ansible.builtin.copy:
    dest: /etc/myapp.conf
    content: |
      port=8080
      host=localhost
      debug=false
  # Only shows "changed" if file content differs
```

#### Principle 4: Use Structured Data Over Text Parsing

**Shell Script Thinking:**

```yaml
# DON'T: Parse text with grep/awk/sed
- name: Get storage nodes
  shell: |
    oc get nodes | grep storage | awk '{print $1}'
  register: nodes_raw

- name: Parse node names
  shell: echo "{{ nodes_raw.stdout }}"
  register: node_names
  # Fragile: breaks if output format changes
```

**Ansible Thinking:**

```yaml
# DO: Work with structured JSON/YAML data
- name: Get storage nodes
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Node
    label_selectors:
      - "node-role.kubernetes.io/storage="
  register: storage_nodes

- name: Extract node names
  ansible.builtin.set_fact:
    node_names: "{{ storage_nodes.resources | map(attribute='metadata.name') | list }}"
  # Reliable: uses API structure, not text formatting
```

**Complex example - Getting pod details:**

```yaml
# Shell script approach - text parsing nightmare
- name: Get pod details
  shell: |
    oc get pod {{ pod_name }} -n {{ namespace }} -o wide | tail -n +2
  register: pod_info

- name: Extract IP address
  shell: echo "{{ pod_info.stdout }}" | awk '{print $6}'
  register: pod_ip
  # Breaks if: column order changes, extra spaces, wide terminal

- name: Extract node name
  shell: echo "{{ pod_info.stdout }}" | awk '{print $7}'
  register: pod_node
  # What if node name has spaces?

# Ansible approach - structured data
- name: Get pod details
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: "{{ namespace }}"
    name: "{{ pod_name }}"
  register: pod_info

- name: Extract pod details
  ansible.builtin.set_fact:
    pod_ip: "{{ pod_info.resources[0].status.podIP }}"
    pod_node: "{{ pod_info.resources[0].spec.nodeName }}"
    pod_phase: "{{ pod_info.resources[0].status.phase }}"
    container_statuses: "{{ pod_info.resources[0].status.containerStatuses }}"
  # Access any field directly, no parsing needed
```

#### Principle 5: Handle Errors Properly

**Shell Script Thinking:**

```yaml
# DON'T: Ignore errors or use crude checks
- name: Update deployment
  shell: oc apply -f /tmp/deployment.yaml
  # If this fails, playbook continues blindly

- name: Wait for deployment
  shell: sleep 30
  # Hope it's ready after 30 seconds

- name: Check deployment
  shell: oc get deployment {{ deploy_name }} -n {{ namespace }}
  # Even if deployment is failing, this succeeds
```

**Ansible Thinking:**

```yaml
# DO: Use proper error handling and verification
- name: Update deployment with proper error handling
  block:
    - name: Apply deployment configuration
      kubernetes.core.k8s:
        state: present
        definition: "{{ lookup('file', '/tmp/deployment.yaml') | from_yaml }}"
        wait: true
        wait_timeout: 300
        wait_condition:
          type: Available
          status: "True"
      register: deployment_result
    
    - name: Verify deployment is healthy
      kubernetes.core.k8s_info:
        api_version: apps/v1
        kind: Deployment
        name: "{{ deploy_name }}"
        namespace: "{{ namespace }}"
      register: deployment_status
      until:
        - deployment_status.resources[0].status.availableReplicas is defined
        - deployment_status.resources[0].status.availableReplicas == deployment_status.resources[0].spec.replicas
      retries: 30
      delay: 10
    
    - name: Log successful deployment
      ansible.builtin.debug:
        msg: "Deployment {{ deploy_name }} updated successfully with {{ deployment_status.resources[0].status.availableReplicas }} replicas"
  
  rescue:
    - name: Get deployment events on failure
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Event
        namespace: "{{ namespace }}"
      register: events
    
    - name: Filter deployment-related events
      ansible.builtin.set_fact:
        deploy_events: "{{ events.resources | selectattr('involvedObject.name', 'equalto', deploy_name) | list }}"
    
    - name: Display failure information
      ansible.builtin.debug:
        msg: |
          Deployment failed
          Status: {{ deployment_result.result.status | default('Unknown') }}
          Recent events: {{ deploy_events | map(attribute='message') | list | join(', ') }}
    
    - name: Fail with detailed message
      ansible.builtin.fail:
        msg: "Deployment update failed. See debug output for details."
  
  always:
    - name: Record deployment attempt
      ansible.builtin.lineinfile:
        path: /var/log/ansible-deployments.log
        line: "{{ ansible_date_time.iso8601 }} - {{ deploy_name }} - {{ deployment_result.result.status | default('failed') }}"
        create: true
```

### Comparison: Complete Real-World Example

Let's see a complete example showing both approaches for a common task: "Update Portworx storage cluster image version"

#### Shell Script Approach

```yaml
---
# Shell script thinking - imperative approach

- name: Bad example - shell script style
  hosts: localhost
  tasks:
    - name: Get current image version
      shell: |
        oc get storagecluster px-cluster -n kube-system -o jsonpath='{.spec.image}' | cut -d: -f2
      register: current_version
    
    - name: Check if update needed
      shell: |
        if [ "{{ current_version.stdout }}" != "{{ target_version }}" ]; then
          echo "update_needed"
        else
          echo "already_updated"
        fi
      register: update_check
    
    - name: Update StorageCluster if needed
      shell: |
        oc patch storagecluster px-cluster -n kube-system \
          --type merge \
          --patch '{"spec":{"image":"portworx/oci-monitor:{{ target_version }}"}}'
      when: update_check.stdout == "update_needed"
    
    - name: Wait for update to start
      shell: sleep 30
    
    - name: Check if pods are updating
      shell: |
        oc get pods -n kube-system -l name=portworx --no-headers | wc -l
      register: pod_count
      until: pod_count.stdout | int > 0
      retries: 10
      delay: 30
    
    - name: Wait for all pods to update
      shell: |
        TOTAL=$(oc get pods -n kube-system -l name=portworx --no-headers | wc -l)
        UPDATED=$(oc get pods -n kube-system -l name=portworx -o json | \
          jq -r '.items[].spec.containers[0].image' | \
          grep "{{ target_version }}" | wc -l)
        
        if [ "$TOTAL" -eq "$UPDATED" ]; then
          echo "complete"
        else
          echo "in_progress"
        fi
      register: update_status
      until: update_status.stdout == "complete"
      retries: 100
      delay: 15
      # What if it never completes? No timeout!
      # What if update fails? We keep waiting!
    
    - name: Check cluster status
      shell: |
        oc get storagecluster px-cluster -n kube-system -o jsonpath='{.status.phase}'
      register: cluster_status
      # Even if phase is "Failed", this task succeeds

    - name: Display result
      debug:
        msg: "Update complete, cluster status: {{ cluster_status.stdout }}"
      # No verification that status is actually "Running"
```

**Problems with this approach:**

1. **Text parsing fragility**: Using `cut`, `grep`, `jq` on command output
2. **No proper error handling**: Failures in one step don't stop execution
3. **Arbitrary timeouts**: `sleep 30` with no verification
4. **Infinite retry risk**: `retries: 100` with no global timeout
5. **No change detection**: Can't tell if anything actually changed
6. **Manual state tracking**: Must manually check update progress
7. **No diagnostic information**: If it fails, no context why
8. **Not idempotent**: Running twice might cause issues

#### Ansible Native Approach

```yaml
---
# Ansible thinking - declarative approach

- name: Good example - Ansible native approach
  hosts: localhost
  
  vars:
    px_namespace: "kube-system"
    px_cluster_name: "px-cluster"
    target_version: "2.13.0"
    global_timeout: 2100  # 35 minutes
    per_pod_timeout: 1500  # 25 minutes
  
  tasks:
    - name: Get current StorageCluster configuration
      kubernetes.core.k8s_info:
        api_version: core.libopenstorage.org/v1
        kind: StorageCluster
        name: "{{ px_cluster_name }}"
        namespace: "{{ px_namespace }}"
      register: storage_cluster
      failed_when: storage_cluster.resources | length == 0
    
    - name: Extract current version
      ansible.builtin.set_fact:
        current_image: "{{ storage_cluster.resources[0].spec.image }}"
        current_version: "{{ storage_cluster.resources[0].spec.image.split(':')[1] }}"
    
    - name: Display current state
      ansible.builtin.debug:
        msg: |
          Current image: {{ current_image }}
          Current version: {{ current_version }}
          Target version: {{ target_version }}
          Update needed: {{ current_version != target_version }}
    
    - name: Update StorageCluster if needed
      block:
        - name: Verify cluster is healthy before upgrade
          ansible.builtin.assert:
            that:
              - storage_cluster.resources[0].status.phase == "Running"
              - storage_cluster.resources[0].status.conditions | selectattr('type', 'equalto', 'Available') | selectattr('status', 'equalto', 'True') | list | length > 0
            fail_msg: "Cluster is not healthy. Current phase: {{ storage_cluster.resources[0].status.phase }}"
            success_msg: "Cluster is healthy, proceeding with upgrade"
        
        - name: Update StorageCluster image
          kubernetes.core.k8s:
            api_version: core.libopenstorage.org/v1
            kind: StorageCluster
            name: "{{ px_cluster_name }}"
            namespace: "{{ px_namespace }}"
            definition:
              spec:
                image: "portworx/oci-monitor:{{ target_version }}"
          register: update_result
          when: current_version != target_version
        
        - name: Initialize upgrade monitoring
          ansible.builtin.set_fact:
            upgrade_start_time: "{{ ansible_date_time.epoch }}"
            last_activity_time: "{{ ansible_date_time.epoch }}"
            pod_tracking: {}
          when: current_version != target_version
        
        - name: Monitor upgrade progress
          block:
            - name: Get current pod states
              kubernetes.core.k8s_info:
                api_version: v1
                kind: Pod
                namespace: "{{ px_namespace }}"
                label_selectors:
                  - "name=portworx"
              register: portworx_pods
            
            - name: Analyze pod states
              ansible.builtin.set_fact:
                total_pods: "{{ portworx_pods.resources | length }}"
                upgraded_pods: "{{ portworx_pods.resources | selectattr('spec.containers[0].image', 'search', target_version) | list }}"
                upgrading_pods: "{{ portworx_pods.resources | rejectattr('spec.containers[0].image', 'search', target_version) | list }}"
            
            - name: Check for activity
              ansible.builtin.set_fact:
                has_activity: "{{ upgraded_pods | length != pod_tracking.get('upgraded_count', 0) }}"
            
            - name: Update activity timestamp
              ansible.builtin.set_fact:
                last_activity_time: "{{ ansible_date_time.epoch }}"
                pod_tracking: "{{ pod_tracking | combine({'upgraded_count': upgraded_pods | length}) }}"
              when: has_activity
            
            - name: Check timeouts
              ansible.builtin.assert:
                that:
                  - (ansible_date_time.epoch | int) - (upgrade_start_time | int) <= global_timeout
                  - (ansible_date_time.epoch | int) - (last_activity_time | int) <= global_timeout
                fail_msg: |
                  Upgrade timeout exceeded
                  Global timeout: {{ global_timeout }}s
                  Elapsed: {{ (ansible_date_time.epoch | int) - (upgrade_start_time | int) }}s
                  Last activity: {{ (ansible_date_time.epoch | int) - (last_activity_time | int) }}s ago
            
            - name: Display progress
              ansible.builtin.debug:
                msg: |
                  Upgrade progress: {{ upgraded_pods | length }}/{{ total_pods }} pods upgraded
                  Elapsed time: {{ (ansible_date_time.epoch | int) - (upgrade_start_time | int) }}s
            
            - name: Wait before next check
              ansible.builtin.pause:
                seconds: 15
              when: upgraded_pods | length < total_pods
          
          until: upgraded_pods | length == total_pods
          retries: "{{ (global_timeout / 15) | int }}"
          delay: 15
          when: current_version != target_version
        
        - name: Verify cluster health after upgrade
          kubernetes.core.k8s_info:
            api_version: core.libopenstorage.org/v1
            kind: StorageCluster
            name: "{{ px_cluster_name }}"
            namespace: "{{ px_namespace }}"
          register: final_cluster_state
          until:
            - final_cluster_state.resources[0].status.phase == "Running"
            - final_cluster_state.resources[0].status.conditions | selectattr('type', 'equalto', 'Available') | selectattr('status', 'equalto', 'True') | list | length > 0
          retries: 30
          delay: 10
          when: current_version != target_version
        
        - name: Display upgrade success
          ansible.builtin.debug:
            msg: |
              Upgrade completed successfully
              Previous version: {{ current_version }}
              New version: {{ target_version }}
              Total time: {{ (ansible_date_time.epoch | int) - (upgrade_start_time | int) }}s
              Pods upgraded: {{ total_pods }}
          when: current_version != target_version
        
        - name: Display no-op message
          ansible.builtin.debug:
            msg: "Cluster already at version {{ target_version }}, no upgrade needed"
          when: current_version == target_version
      
      rescue:
        - name: Get cluster events on failure
          kubernetes.core.k8s_info:
            api_version: v1
            kind: Event
            namespace: "{{ px_namespace }}"
          register: cluster_events
        
        - name: Filter StorageCluster events
          ansible.builtin.set_fact:
            relevant_events: "{{ cluster_events.resources | selectattr('involvedObject.name', 'equalto', px_cluster_name) | list | sort(attribute='lastTimestamp', reverse=true) }}"
        
        - name: Get failed pod details
          kubernetes.core.k8s_info:
            api_version: v1
            kind: Pod
            namespace: "{{ px_namespace }}"
            label_selectors:
              - "name=portworx"
          register: failed_pods_info
        
        - name: Identify problem pods
          ansible.builtin.set_fact:
            problem_pods: "{{ failed_pods_info.resources | rejectattr('status.phase', 'equalto', 'Running') | list }}"
        
        - name: Display failure diagnostics
          ansible.builtin.debug:
            msg: |
              Upgrade failed
              Error: {{ ansible_failed_result.msg | default('Unknown error') }}
              
              Recent events:
              {{ relevant_events[:5] | map(attribute='message') | list | join('\n') }}
              
              Problem pods: {{ problem_pods | map(attribute='metadata.name') | list | join(', ') }}
              
              Pod phases:
              {% for pod in problem_pods %}
              - {{ pod.metadata.name }}: {{ pod.status.phase }}
              {% endfor %}
        
        - name: Fail with diagnostic information
          ansible.builtin.fail:
            msg: "Upgrade failed. See debug output above for details."
      
      always:
        - name: Record upgrade attempt
          ansible.builtin.copy:
            content: |
              Timestamp: {{ ansible_date_time.iso8601 }}
              Cluster: {{ px_cluster_name }}
              Namespace: {{ px_namespace }}
              Previous Version: {{ current_version }}
              Target Version: {{ target_version }}
              Status: {{ 'success' if upgraded_pods | default([]) | length == total_pods | default(0) else 'failed' }}
              Duration: {{ (ansible_date_time.epoch | int) - (upgrade_start_time | default(ansible_date_time.epoch) | int) }}s
            dest: "/tmp/px-upgrade-{{ ansible_date_time.epoch }}.log"
          delegate_to: localhost
```

**Benefits of Ansible approach:**

1. **Structured data**: Working with API objects, not text
2. **Proper error handling**: Block/rescue/always structure
3. **Intelligent monitoring**: Tracks activity, not just time
4. **Multiple timeouts**: Global and per-component timeouts
5. **Change detection**: Only acts if update needed
6. **Automatic state tracking**: Monitors upgrade progress automatically
7. **Comprehensive diagnostics**: Events, pod states, error details
8. **Idempotent**: Safe to run multiple times
9. **Observable**: Clear progress reporting
10. **Recoverable**: Detailed failure information for troubleshooting

### Key Takeaways

**Stop asking "How do I run this command?"**  
Start asking "What state do I want to achieve?"

**Stop parsing text output**  
Start using structured data from modules

**Stop writing complex shell scripts**  
Start using Ansible modules and filters

**Stop thinking sequentially**  
Start thinking declaratively

**Remember:** Ansible modules are extensively tested, handle edge cases, and provide idempotency. Use them instead of reinventing the wheel with shell commands.

---

## Development Environment Deep Dive

### Virtual Environment Architecture

Understanding why and how to properly use Python virtual environments is critical for consistent, reproducible automation.

#### Why Virtual Environments Matter

**The Problem Without Virtual Environments:**

```bash
# System-wide installations cause problems:

# Developer A installs ansible 2.12
sudo pip install ansible-core==2.12.0

# Developer B needs ansible 2.15 for a different project
sudo pip install ansible-core==2.15.0  # Overwrites A's version

# Developer A's playbooks now break due to version mismatch
# CI/CD might use yet another version
# AAP Execution Environment uses a different version
```

**The Solution: Project-Specific Virtual Environments:**

```bash
# Each project has isolated dependencies

# Project 1
cd /path/to/project1
python3.11 -m venv .venv
source .venv/bin/activate
pip install ansible-core==2.12.0

# Project 2
cd /path/to/project2
python3.11 -m venv .venv
source .venv/bin/activate
pip install ansible-core==2.15.0

# No conflicts - each project isolated
```

#### Proper Virtual Environment Setup

**Step 1: Create virtual environment**

```bash
# Use Python 3.11 specifically (matches AAP EE)
python3.11 -m venv .venv

# Verify creation
ls -la .venv/
# Should see: bin/, include/, lib/, pyvenv.cfg
```

**Step 2: Activate virtual environment**

```bash
# Activate (Linux/Mac)
source .venv/bin/activate

# Your prompt changes to show activation:
# (.venv) user@host:~/project$

# Verify you're in venv
which python
# Should show: /path/to/project/.venv/bin/python

which pip
# Should show: /path/to/project/.venv/bin/pip

python --version
# Should show: Python 3.11.x
```

**Step 3: Install dependencies**

```bash
# Upgrade pip first
pip install --upgrade pip

# Install from requirements
pip install -r requirements.txt

# Or install individual packages
pip install ansible-core==2.18.4
pip install ansible-lint==24.2.0
pip install yamllint
pip install black isort flake8 mypy
pip install pymarkdownlnt
```

**Step 4: Verify installation**

```bash
# Check installed packages
pip list

# Verify Ansible
ansible --version
# Should show version from venv, not system

# Verify tools
ansible-lint --version
black --version
```

#### Common Virtual Environment Mistakes

**Mistake 1: Not activating venv**

```bash
# WRONG - using system Python
python playbook.py
ansible-playbook playbook.yml

# RIGHT - using venv Python
source .venv/bin/activate
python playbook.py
# OR explicitly use venv binary
.venv/bin/python playbook.py
.venv/bin/ansible-playbook playbook.yml
```

**Mistake 2: Installing globally instead of in venv**

```bash
# WRONG - installs to system
sudo pip install ansible-lint

# RIGHT - installs to venv
source .venv/bin/activate
pip install ansible-lint
# OR
.venv/bin/pip install ansible-lint
```

**Mistake 3: Mixing system and venv packages**

```bash
# WRONG - confusing which Python is used
source .venv/bin/activate
python script.py  # Uses venv
deactivate
python script.py  # Uses system - different packages!

# RIGHT - always be explicit
.venv/bin/python script.py  # Always uses venv
```

### Pre-commit Hooks Deep Dive

Pre-commit hooks catch issues before they enter the repository. Here's how to set them up properly.

#### Basic Pre-commit Configuration

**Create `.pre-commit-config.yaml`:**

```yaml
# .pre-commit-config.yaml
repos:
  # Ansible linting
  - repo: https://github.com/ansible/ansible-lint
    rev: v24.2.0
    hooks:
      - id: ansible-lint
        name: Ansible Lint
        description: Lint Ansible playbooks and roles
        entry: ansible-lint
        language: python
        files: \.(yaml|yml)$
        args:
          - --profile=production
          - --force-color
        additional_dependencies:
          - 'ansible-core>=2.18'
  
  # YAML linting
  - repo: https://github.com/adrienverge/yamllint
    rev: v1.33.0
    hooks:
      - id: yamllint
        name: YAML Lint
        args:
          - --config-file=.yamllint
          - --format=colored
  
  # Python code formatting
  - repo: https://github.com/psf/black
    rev: 24.1.0
    hooks:
      - id: black
        name: Black Code Formatter
        language_version: python3.11
        files: \.py$
  
  # Python import sorting
  - repo: https://github.com/PyCQA/isort
    rev: 5.13.0
    hooks:
      - id: isort
        name: isort Import Sorter
        files: \.py$
        args:
          - --profile=black
  
  # Python linting
  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        name: Flake8 Linter
        files: \.py$
        args:
          - --max-line-length=88
          - --extend-ignore=E203,W503
  
  # Markdown linting
  - repo: https://github.com/jackdewinter/pymarkdown
    rev: v0.9.14
    hooks:
      - id: pymarkdown
        name: Markdown Lint
        args:
          - --disable-rules=MD013
          - scan
  
  # Generic checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
        name: Trim Trailing Whitespace
      - id: end-of-file-fixer
        name: Fix End of Files
      - id: check-yaml
        name: Check YAML
        args: [--safe]
      - id: check-added-large-files
        name: Check for Large Files
        args: [--maxkb=1000]
      - id: check-merge-conflict
        name: Check for Merge Conflicts
```

#### Installing and Using Pre-commit

```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install

# Run against all files (first time or manually)
pre-commit run --all-files

# Run against specific file
pre-commit run --files playbooks/my_playbook.yml

# Skip hooks (use sparingly!)
git commit --no-verify -m "Emergency fix"
```

#### Custom Pre-commit Hook Example

Create `.git/hooks/pre-commit-custom.sh`:

```bash
#!/bin/bash
# Custom pre-commit checks

set -e

echo "Running custom checks..."

# Check for debugging statements
if git diff --cached --name-only | grep -E '\.(py|yml|yaml)$' | xargs grep -n 'import pdb\|breakpoint()' 2>/dev/null; then
    echo "ERROR: Found debugging statements (pdb/breakpoint)"
    exit 1
fi

# Check for TODO/FIXME without ticket numbers
if git diff --cached | grep -E '^\+.*TODO|^\+.*FIXME' | grep -v 'JIRA-[0-9]'; then
    echo "WARNING: TODO/FIXME found without ticket number"
    echo "Please add ticket number like: TODO(JIRA-1234): description"
fi

# Check for secret patterns
if git diff --cached | grep -iE 'password.*=|api_key.*=|secret.*='; then
    echo "ERROR: Possible secret found in code"
    echo "Please use Ansible Vault for sensitive data"
    exit 1
fi

echo "Custom checks passed"
```

Make executable and add to pre-commit:

```bash
chmod +x .git/hooks/pre-commit-custom.sh

# Add to .pre-commit-config.yaml
- repo: local
  hooks:
    - id: custom-checks
      name: Custom Security Checks
      entry: .git/hooks/pre-commit-custom.sh
      language: script
      pass_filenames: false
```

### Editor Configuration Deep Dive

Proper editor configuration catches issues as you type, before pre-commit hooks even run.

#### VSCode Configuration

**Create `.vscode/settings.json`:**

```json
{
  // Python Configuration
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.envFile": "${workspaceFolder}/.env",
  "python.terminal.activateEnvironment": true,
  
  // Python Linting
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.flake8Path": "${workspaceFolder}/.venv/bin/flake8",
  "python.linting.flake8Args": [
    "--max-line-length=88",
    "--extend-ignore=E203,W503"
  ],
  "python.linting.mypyEnabled": true,
  "python.linting.mypyPath": "${workspaceFolder}/.venv/bin/mypy",
  "python.linting.pylintEnabled": false,
  
  // Python Formatting
  "python.formatting.provider": "black",
  "python.formatting.blackPath": "${workspaceFolder}/.venv/bin/black",
  "python.sortImports.path": "${workspaceFolder}/.venv/bin/isort",
  
  // Ansible Configuration
  "ansible.python.interpreterPath": "${workspaceFolder}/.venv/bin/python",
  "ansible.validation.enabled": true,
  "ansible.validation.lint.enabled": true,
  "ansible.validation.lint.path": "${workspaceFolder}/.venv/bin/ansible-lint",
  "ansible.validation.lint.arguments": "--profile=production",
  
  // YAML Configuration
  "[yaml]": {
    "editor.insertSpaces": true,
    "editor.tabSize": 2,
    "editor.autoIndent": "advanced",
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "redhat.vscode-yaml"
  },
  
  // Python file configuration
  "[python]": {
    "editor.insertSpaces": true,
    "editor.tabSize": 4,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  
  // YAML Schema Association
  "yaml.schemas": {
    "https://json.schemastore.org/ansible-playbook.json": [
      "playbooks/**/*.yml",
      "playbooks/**/*.yaml"
    ],
    "https://json.schemastore.org/ansible-vars.json": [
      "roles/*/defaults/*.yml",
      "roles/*/vars/*.yml",
      "group_vars/**/*.yml",
      "host_vars/**/*.yml"
    ]
  },
  
  // File associations
  "files.associations": {
    "*.yml": "ansible",
    "*.yaml": "ansible",
    "**/playbooks/**/*.yml": "ansible",
    "**/roles/**/*.yml": "ansible"
  },
  
  // Editor behavior
  "editor.rulers": [88, 120],
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,
  "files.trimFinalNewlines": true,
  
  // Git
  "git.ignoreLimitWarning": true,
  
  // Search exclusions
  "search.exclude": {
    "**/.venv": true,
    "**/__pycache__": true,
    "**/*.pyc": true
  },
  
  // File watcher exclusions
  "files.watcherExclude": {
    "**/.venv/**": true
  }
}
```

**Create `.vscode/extensions.json`:**

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "redhat.ansible",
    "redhat.vscode-yaml",
    "streetsidesoftware.code-spell-checker",
    "eamodio.gitlens",
    "mhutchie.git-graph"
  ]
}
```

**Create `.vscode/launch.json` for debugging:**

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Ansible: Debug Current Playbook",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/.venv/bin/ansible-playbook",
      "args": [
        "${file}",
        "-vvv"
      ],
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "env": {
        "ANSIBLE_STDOUT_CALLBACK": "debug"
      }
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}"
    }
  ]
}
```

#### Vim/Neovim Configuration

**Create `.vimrc` additions:**

```vim
" Ansible development configuration

" Python settings
au FileType python setlocal tabstop=4 shiftwidth=4 softtabstop=4 expandtab
au FileType python setlocal colorcolumn=88
au FileType python let b:ale_linters = ['flake8', 'mypy']
au FileType python let b:ale_fixers = ['black', 'isort']

" YAML/Ansible settings
au FileType yaml setlocal tabstop=2 shiftwidth=2 softtabstop=2 expandtab
au FileType yaml let b:ale_linters = ['yamllint', 'ansible-lint']
au FileType yaml setlocal indentkeys-=<:>

" ALE (Asynchronous Lint Engine) configuration
let g:ale_python_flake8_executable = '.venv/bin/flake8'
let g:ale_python_black_executable = '.venv/bin/black'
let g:ale_python_isort_executable = '.venv/bin/isort'
let g:ale_python_mypy_executable = '.venv/bin/mypy'
let g:ale_yaml_yamllint_executable = '.venv/bin/yamllint'
let g:ale_ansible_ansible_lint_executable = '.venv/bin/ansible-lint'

" Fix on save
let g:ale_fix_on_save = 1

" Show errors
let g:ale_echo_msg_format = '[%linter%] %s [%severity%]'
let g:ale_sign_error = '✘'
let g:ale_sign_warning = '⚠'
```

### Quality Check Automation

**Create `scripts/quality_check.sh`:**

```bash
#!/bin/bash
# Comprehensive quality check script

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "Ansible Quality Checks"
echo "========================================="
echo ""

# Check virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${RED}ERROR: Virtual environment not found${NC}"
    echo "Run: python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Verify tools are installed
TOOLS=("ansible-lint" "yamllint" "black" "isort" "flake8" "mypy" "pymarkdownlnt")
for tool in "${TOOLS[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        echo -e "${RED}ERROR: $tool not found${NC}"
        echo "Run: pip install -r requirements.txt"
        exit 1
    fi
done

echo -e "${GREEN}✓ Virtual environment and tools verified${NC}"
echo ""

# Find files to check
PLAYBOOKS=$(find playbooks -name "*.yml" -o -name "*.yaml" 2>/dev/null || true)
ROLES=$(find roles -type d -name "tasks" -o -name "handlers" -o -name "defaults" -o -name "vars" 2>/dev/null | sed 's|/[^/]*$||' | sort -u || true)
PYTHON_FILES=$(find roles -name "*.py" 2>/dev/null || true)
MD_FILES=$(find docs -name "*.md" 2>/dev/null || true)

# Counter for issues
ISSUES=0

# 1. Ansible Syntax Check
if [ -n "$PLAYBOOKS" ]; then
    echo "1. Running Ansible syntax check..."
    for playbook in $PLAYBOOKS; do
        if ansible-playbook --syntax-check "$playbook" >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} $playbook"
        else
            echo -e "${RED}✗${NC} $playbook"
            ansible-playbook --syntax-check "$playbook"
            ISSUES=$((ISSUES + 1))
        fi
    done
    echo ""
fi

# 2. Ansible Lint
if [ -n "$ROLES" ] || [ -n "$PLAYBOOKS" ]; then
    echo "2. Running ansible-lint..."
    if ansible-lint --profile=production $ROLES $PLAYBOOKS; then
        echo -e "${GREEN}✓ Ansible lint passed${NC}"
    else
        echo -e "${RED}✗ Ansible lint failed${NC}"
        ISSUES=$((ISSUES + 1))
    fi
    echo ""
fi

# 3. YAML Lint
echo "3. Running yamllint..."
if yamllint -c .yamllint .; then
    echo -e "${GREEN}✓ YAML lint passed${NC}"
else
    echo -e "${RED}✗ YAML lint failed${NC}"
    ISSUES=$((ISSUES + 1))
fi
echo ""

# 4. Python Quality Checks
if [ -n "$PYTHON_FILES" ]; then
    echo "4. Running Python quality checks..."
    
    # Black
    echo "   - Black (formatting)..."
    if black --check --quiet $PYTHON_FILES 2>/dev/null; then
        echo -e "     ${GREEN}✓ Black formatting check passed${NC}"
    else
        echo -e "     ${YELLOW}⚠ Black would reformat files${NC}"
        echo "     Run: black $PYTHON_FILES"
        ISSUES=$((ISSUES + 1))
    fi
    
    # isort
    echo "   - isort (import sorting)..."
    if isort --check-only --quiet $PYTHON_FILES 2>/dev/null; then
        echo -e "     ${GREEN}✓ isort check passed${NC}"
    else
        echo -e "     ${YELLOW}⚠ isort would reorganize imports${NC}"
        echo "     Run: isort $PYTHON_FILES"
        ISSUES=$((ISSUES + 1))
    fi
    
    # flake8
    echo "   - flake8 (linting)..."
    if flake8 --max-line-length=88 --extend-ignore=E203,W503 $PYTHON_FILES 2>/dev/null; then
        echo -e "     ${GREEN}✓ flake8 passed${NC}"
    else
        echo -e "     ${RED}✗ flake8 found issues${NC}"
        flake8 --max-line-length=88 --extend-ignore=E203,W503 $PYTHON_FILES
        ISSUES=$((ISSUES + 1))
    fi
    
    # mypy
    echo "   - mypy (type checking)..."
    if mypy --ignore-missing-imports $PYTHON_FILES 2>/dev/null; then
        echo -e "     ${GREEN}✓ mypy passed${NC}"
    else
        echo -e "     ${YELLOW}⚠ mypy found type issues${NC}"
        mypy --ignore-missing-imports $PYTHON_FILES
        # Don't count as failure, just warning
    fi
    echo ""
fi

# 5. Markdown Lint
if [ -n "$MD_FILES" ]; then
    echo "5. Running markdown lint..."
    if pymarkdownlnt -d MD013 scan $MD_FILES; then
        echo -e "${GREEN}✓ Markdown lint passed${NC}"
    else
        echo -e "${RED}✗ Markdown lint failed${NC}"
        ISSUES=$((ISSUES + 1))
    fi
    echo ""
fi

# Summary
echo "========================================="
if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ All quality checks passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Found $ISSUES issue(s)${NC}"
    echo ""
    echo "Fix issues and run again."
    exit 1
fi
```

Make executable:

```bash
chmod +x scripts/quality_check.sh
```

**Usage:**

```bash
# Run all quality checks
./scripts/quality_check.sh

# Run as part of CI/CD
./scripts/quality_check.sh || exit 1
```

### Continuous Integration Configuration

**Create `.github/workflows/quality.yml` for GitHub Actions:**

```yaml
name: Quality Checks

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  quality:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Cache Python dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run quality checks
        run: |
          ./scripts/quality_check.sh
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: quality-check-results
          path: |
            *.log
            reports/
```

**Create `.gitlab-ci.yml` for GitLab CI:**

```yaml
image: python:3.11

stages:
  - lint
  - test

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip
    - .venv/

before_script:
  - python -m venv .venv
  - source .venv/bin/activate
  - pip install --upgrade pip
  - pip install -r requirements.txt

ansible-lint:
  stage: lint
  script:
    - ansible-lint --profile=production roles/ playbooks/
  allow_failure: false

yaml-lint:
  stage: lint
  script:
    - yamllint -c .yamllint .
  allow_failure: false

python-quality:
  stage: lint
  script:
    - black --check roles/*/library/ roles/*/filter_plugins/
    - isort --check roles/*/library/ roles/*/filter_plugins/
    - flake8 --max-line-length=88 roles/*/library/ roles/*/filter_plugins/
  allow_failure: false

syntax-check:
  stage: test
  script:
    - |
      for playbook in playbooks/*.yml; do
        ansible-playbook --syntax-check "$playbook"
      done
  allow_failure: false
```

---

## Role Architecture Patterns

This section provides detailed guidance on designing and implementing production-grade Ansible roles.

### The Orchestrator Pattern

The orchestrator pattern is fundamental to well-organized, maintainable roles. The `tasks/main.yml` file serves as a high-level orchestrator that delegates to specialized task files.

#### Why Use the Orchestrator Pattern?

**Problems with monolithic task files:**

```yaml
# BAD: Everything in tasks/main.yml (500+ lines)
---
- name: Validate input variables
  assert:
    that:
      - var1 is defined
      - var2 is defined
  # ... 50 more validation tasks

- name: Check prerequisites
  command: which kubectl
  # ... 30 more prerequisite checks

- name: Create resources
  kubernetes.core.k8s:
    # ... 100 lines of resource creation

- name: Monitor progress
  # ... 200 lines of monitoring logic

- name: Verify results
  # ... 100 lines of verification

# Impossible to:
# - Test individual phases
# - Run only preflight checks
# - Understand workflow at a glance
# - Maintain without fear
```

**Benefits of orchestrator pattern:**

```yaml
# GOOD: Orchestrator delegates to specialized files
---
# Role: example_role
# Clear workflow visible at a glance

- name: "Phase 1: Preflight Checks"
  import_tasks: preflight.yml
  tags: [always, preflight]

- name: "Phase 2: Input Validation"
  import_tasks: validate.yml
  tags: [always, validation]

- name: "Phase 3: Resource Creation"
  import_tasks: create.yml
  tags: [creation]

- name: "Phase 4: Progress Monitoring"
  import_tasks: monitor.yml
  tags: [monitoring]

- name: "Phase 5: Result Verification"
  import_tasks: verify.yml
  tags: [verification]

# Now can:
# - Test each phase independently
# - Run only preflight: --tags preflight
# - Understand workflow immediately
# - Maintain files separately
```

#### Orchestrator Best Practices

**1. Keep main.yml under 100 lines**

The orchestrator should be readable in a single screen:

```yaml
---
# Role: portworx_upgrade
# Purpose: Orchestrate Portworx cluster upgrade process
# Author: Platform Team
# Last Updated: 2025-02-10

# === Preparation Phase ===

- name: "Phase 1: Preflight Checks"
  ansible.builtin.import_tasks: preflight.yml
  tags:
    - always
    - preflight
    - portworx_upgrade

- name: "Phase 2: Input Validation"
  ansible.builtin.import_tasks: validate.yml
  tags:
    - always
    - validation
    - portworx_upgrade

- name: "Phase 3: Cluster Health Check"
  ansible.builtin.import_tasks: health_check.yml
  tags:
    - health-check
    - portworx_upgrade

# === Execution Phase ===

- name: "Phase 4: Backup Current State"
  ansible.builtin.import_tasks: backup.yml
  tags:
    - backup
    - portworx_upgrade
  when: portworx_upgrade_enable_backup | default(true)

- name: "Phase 5: Update Configuration"
  ansible.builtin.import_tasks: update_config.yml
  tags:
    - update
    - portworx_upgrade

- name: "Phase 6: Trigger Upgrade"
  ansible.builtin.import_tasks: trigger_upgrade.yml
  tags:
    - upgrade
    - portworx_upgrade

- name: "Phase 7: Monitor Upgrade Progress"
  ansible.builtin.import_tasks: monitor.yml
  tags:
    - monitoring
    - portworx_upgrade

# === Verification Phase ===

- name: "Phase 8: Verify Upgrade Completion"
  ansible.builtin.import_tasks: verify.yml
  tags:
    - verification
    - portworx_upgrade

- name: "Phase 9: Post-Upgrade Health Check"
  ansible.builtin.import_tasks: health_check.yml
  tags:
    - health-check
    - verification
    - portworx_upgrade

- name: "Phase 10: Generate Report"
  ansible.builtin.import_tasks: report.yml
  tags:
    - reporting
    - portworx_upgrade
  when: portworx_upgrade_enable_reporting | default(true)
```

**2. Use descriptive phase names**

```yaml
# BAD: Vague names
- name: "Step 1"
  import_tasks: step1.yml

- name: "Do stuff"
  import_tasks: stuff.yml

# GOOD: Clear purpose
- name: "Phase 1: Validate Cluster Connectivity"
  import_tasks: validate_connectivity.yml

- name: "Phase 2: Check Storage Node Health"
  import_tasks: check_node_health.yml
```

**3. Tag consistently**

```yaml
# Every import should have:
# - 'always' tag (if must run)
# - Phase-specific tag
# - Role name tag

- name: "Phase 1: Preflight Checks"
  import_tasks: preflight.yml
  tags:
    - always          # Always runs (even with --tags)
    - preflight       # Phase-specific
    - my_role         # Role identifier
```

**4. Use when conditionals for optional phases**

```yaml
# Optional phases controlled by variables
- name: "Phase 5: Enable Debug Mode"
  import_tasks: debug.yml
  tags: [debug, my_role]
  when: my_role_debug_mode | default(false)

- name: "Phase 9: Cleanup Temporary Files"
  import_tasks: cleanup.yml
  tags: [cleanup, my_role]
  when: my_role_cleanup_enabled | default(true)
```

### Specialized Task File Patterns

Each specialized task file should focus on a single responsibility.

#### preflight.yml - Environment Validation

Purpose: Verify the environment is ready before making any changes

```yaml
---
# Preflight checks: Verify environment readiness
# This file should NEVER modify state - only validate

- name: Check Ansible version
  ansible.builtin.assert:
    that:
      - ansible_version.full is version('2.12.0', '>=')
    fail_msg: "Ansible 2.12.0 or higher required (found {{ ansible_version.full }})"
    success_msg: "Ansible version {{ ansible_version.full }} is compatible"
    quiet: true
  tags: [version-check]

- name: Verify required commands available
  ansible.builtin.command:
    cmd: which {{ item }}
  loop:
    - kubectl
    - oc
    - jq
  register: command_check
  changed_when: false
  failed_when: command_check.rc != 0
  tags: [prerequisites]

- name: Check Kubernetes cluster connectivity
  kubernetes.core.k8s_cluster_info:
  register: cluster_info
  failed_when: cluster_info is failed
  tags: [connectivity]

- name: Display cluster information
  ansible.builtin.debug:
    msg: |
      Connected to cluster
      Version: {{ cluster_info.version.server.kubernetes.gitVersion }}
      API Server: {{ cluster_info.connection.host }}
  tags: [connectivity]

- name: Verify required namespaces exist
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Namespace
    name: "{{ item }}"
  loop: "{{ required_namespaces }}"
  register: namespace_check
  failed_when: namespace_check.resources | length == 0
  tags: [namespaces]

- name: Check for required CustomResourceDefinitions
  kubernetes.core.k8s_info:
    api_version: apiextensions.k8s.io/v1
    kind: CustomResourceDefinition
    name: "{{ item }}"
  loop: "{{ required_crds }}"
  register: crd_check
  failed_when: crd_check.resources | length == 0
  tags: [crds]

- name: Verify sufficient cluster resources
  block:
    - name: Get node information
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Node
      register: nodes
    
    - name: Calculate total cluster capacity
      ansible.builtin.set_fact:
        total_cpu: "{{ nodes.resources | map(attribute='status.capacity.cpu') | map('int') | sum }}"
        total_memory: "{{ nodes.resources | map(attribute='status.capacity.memory') | map('regex_replace', 'Ki$', '') | map('int') | sum }}"
    
    - name: Verify minimum resources
      ansible.builtin.assert:
        that:
          - total_cpu | int >= minimum_cpu_cores | default(4)
          - total_memory | int >= minimum_memory_kb | default(8000000)
        fail_msg: "Insufficient cluster resources (CPU: {{ total_cpu }}, Memory: {{ total_memory }}Ki)"
        success_msg: "Sufficient cluster resources available"
  tags: [resources]

- name: Check for existing operations in progress
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: "{{ target_namespace }}"
    label_selectors:
      - "app={{ app_name }}"
  register: existing_pods
  failed_when: >
    existing_pods.resources |
    selectattr('metadata.labels.operation', 'defined') |
    selectattr('metadata.labels.operation', 'equalto', 'upgrade') |
    list | length > 0
  tags: [conflict-check]

- name: Preflight checks complete
  ansible.builtin.debug:
    msg: "All preflight checks passed successfully"
  tags: [always]
```

#### validate.yml - Input Validation

Purpose: Validate all user-provided variables and parameters

```yaml
---
# Input validation: Ensure all required variables are valid
# Fail fast if configuration is invalid

- name: Validate required variables are defined
  ansible.builtin.assert:
    that:
      - "{{ item.var }} is defined"
      - "{{ item.var }} | length > 0"
    fail_msg: "Required variable '{{ item.name }}' is not defined or empty"
    success_msg: "Variable '{{ item.name }}' is defined"
  loop:
    - {var: "my_role_namespace", name: "namespace"}
    - {var: "my_role_resource_name", name: "resource_name"}
    - {var: "my_role_target_version", name: "target_version"}
  loop_control:
    label: "{{ item.name }}"
  tags: [validation]

- name: Validate variable types
  ansible.builtin.assert:
    that:
      - my_role_timeout is number
      - my_role_timeout > 0
      - my_role_retry_count is number
      - my_role_retry_count >= 0
      - my_role_enable_validation is boolean
    fail_msg: "Variable has invalid type or value"
    success_msg: "All variable types are correct"
  tags: [validation]

- name: Validate enum values
  ansible.builtin.assert:
    that:
      - my_role_strategy in ['rolling', 'all-at-once', 'canary']
      - my_role_log_level in ['debug', 'info', 'warn', 'error']
    fail_msg: "Variable has invalid enum value"
  tags: [validation]

- name: Validate version format
  ansible.builtin.assert:
    that:
      - my_role_target_version is match('^[0-9]+\.[0-9]+\.[0-9]+$')
    fail_msg: "Invalid version format '{{ my_role_target_version }}'. Expected: X.Y.Z"
  tags: [validation]

- name: Validate namespace exists
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Namespace
    name: "{{ my_role_namespace }}"
  register: namespace_validation
  failed_when: namespace_validation.resources | length == 0
  tags: [validation]

- name: Validate resource exists
  kubernetes.core.k8s_info:
    api_version: "{{ my_role_api_version }}"
    kind: "{{ my_role_kind }}"
    name: "{{ my_role_resource_name }}"
    namespace: "{{ my_role_namespace }}"
  register: resource_validation
  failed_when: resource_validation.resources | length == 0
  tags: [validation]

- name: Validate version compatibility
  block:
    - name: Get current version
      ansible.builtin.set_fact:
        current_version: "{{ resource_validation.resources[0].spec.version }}"
    
    - name: Check version upgrade path
      ansible.builtin.assert:
        that:
          - current_version is version(my_role_target_version, '<')
          - current_version is version(my_role_minimum_version, '>=')
        fail_msg: |
          Invalid upgrade path
          Current: {{ current_version }}
          Target: {{ my_role_target_version }}
          Minimum supported: {{ my_role_minimum_version }}
        success_msg: "Upgrade path validated"
  tags: [validation]

- name: Validate configuration consistency
  ansible.builtin.assert:
    that:
      - not (my_role_enable_backup and my_role_skip_verification)
    fail_msg: "Cannot enable backup while skipping verification"
  tags: [validation]

- name: Input validation complete
  ansible.builtin.debug:
    msg: "All input validation passed successfully"
  tags: [always]
```

#### execute.yml - Main Operation Logic

Purpose: Perform the primary operation of the role

```yaml
---
# Main execution: Perform the role's primary operation
# This is where the actual work happens

- name: Set execution start time
  ansible.builtin.set_fact:
    execution_start_time: "{{ ansible_date_time.epoch }}"
    cacheable: false
  tags: [always]

- name: Display execution plan
  ansible.builtin.debug:
    msg: |
      Starting execution
      Operation: {{ operation_name }}
      Target: {{ my_role_resource_name }}
      Namespace: {{ my_role_namespace }}
      Timeout: {{ my_role_timeout }}s
  tags: [always]

- name: Main operation with error handling
  block:
    # Phase 1: Prepare for operation
    - name: Create temporary working directory
      ansible.builtin.file:
        path: "{{ my_role_work_dir }}"
        state: directory
        mode: '0755'
      tags: [preparation]
    
    - name: Generate operation manifest
      ansible.builtin.template:
        src: operation_manifest.j2
        dest: "{{ my_role_work_dir }}/manifest.yaml"
      tags: [preparation]
    
    # Phase 2: Execute primary operation
    - name: Apply operation configuration
      kubernetes.core.k8s:
        state: present
        definition: "{{ lookup('file', my_role_work_dir + '/manifest.yaml') | from_yaml }}"
        wait: true
        wait_timeout: "{{ my_role_timeout }}"
        wait_condition:
          type: "{{ my_role_wait_condition_type }}"
          status: "{{ my_role_wait_condition_status }}"
      register: operation_result
      tags: [execution]
    
    - name: Verify operation accepted
      ansible.builtin.assert:
        that:
          - operation_result is succeeded
          - operation_result.result is defined
        fail_msg: "Operation was not accepted by cluster"
        success_msg: "Operation accepted and processing"
      tags: [execution]
    
    # Phase 3: Monitor operation progress
    - name: Monitor operation until complete
      kubernetes.core.k8s_info:
        api_version: "{{ operation_result.result.apiVersion }}"
        kind: "{{ operation_result.result.kind }}"
        name: "{{ operation_result.result.metadata.name }}"
        namespace: "{{ operation_result.result.metadata.namespace }}"
      register: operation_status
      until:
        - operation_status.resources[0].status.phase is defined
        - operation_status.resources[0].status.phase in ['Succeeded', 'Complete', 'Running']
      retries: "{{ (my_role_timeout / 10) | int }}"
      delay: 10
      tags: [monitoring]
    
    # Phase 4: Record success
    - name: Record successful operation
      ansible.builtin.set_fact:
        my_role_execution_status: "success"
        my_role_execution_result: "{{ operation_status.resources[0] }}"
        my_role_execution_duration: "{{ (ansible_date_time.epoch | int) - (execution_start_time | int) }}"
        cacheable: true
      tags: [always]
    
    - name: Log success
      ansible.builtin.debug:
        msg: |
          Operation completed successfully
          Status: {{ operation_status.resources[0].status.phase }}
          Duration: {{ my_role_execution_duration }}s
      tags: [always]
  
  rescue:
    # Error handling
    - name: Get operation failure details
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Event
        namespace: "{{ my_role_namespace }}"
      register: operation_events
      tags: [error-handling]
    
    - name: Filter relevant events
      ansible.builtin.set_fact:
        relevant_events: "{{ operation_events.resources | selectattr('involvedObject.name', 'equalto', my_role_resource_name) | list | sort(attribute='lastTimestamp', reverse=true) }}"
      tags: [error-handling]
    
    - name: Record operation failure
      ansible.builtin.set_fact:
        my_role_execution_status: "failed"
        my_role_execution_error: "{{ ansible_failed_result.msg | default('Unknown error') }}"
        my_role_execution_duration: "{{ (ansible_date_time.epoch | int) - (execution_start_time | int) }}"
        cacheable: true
      tags: [error-handling]
    
    - name: Display failure diagnostics
      ansible.builtin.debug:
        msg: |
          Operation failed
          Error: {{ my_role_execution_error }}
          Duration: {{ my_role_execution_duration }}s
          
          Recent events:
          {{ relevant_events[:5] | map(attribute='message') | list | join('\n') }}
      tags: [error-handling]
    
    - name: Attempt automatic recovery
      ansible.builtin.include_tasks: recovery.yml
      when: my_role_enable_auto_recovery | default(false)
      tags: [error-handling, recovery]
    
    - name: Fail with comprehensive error message
      ansible.builtin.fail:
        msg: |
          Operation failed after {{ my_role_execution_duration }}s
          Error: {{ my_role_execution_error }}
          See debug output above for detailed diagnostics
      tags: [error-handling]
  
  always:
    # Cleanup (always runs)
    - name: Remove temporary working directory
      ansible.builtin.file:
        path: "{{ my_role_work_dir }}"
        state: absent
      when: my_role_cleanup_temp_dir | default(true)
      tags: [cleanup]
    
    - name: Record execution metrics
      ansible.builtin.set_fact:
        my_role_execution_end_time: "{{ ansible_date_time.epoch }}"
        my_role_execution_metrics:
          start_time: "{{ execution_start_time }}"
          end_time: "{{ ansible_date_time.epoch }}"
          duration: "{{ my_role_execution_duration | default(0) }}"
          status: "{{ my_role_execution_status | default('unknown') }}"
        cacheable: false
      tags: [always]
    
    - name: Save execution log
      ansible.builtin.copy:
        content: |
          Execution Log
          =============
          Timestamp: {{ ansible_date_time.iso8601 }}
          Operation: {{ operation_name }}
          Target: {{ my_role_resource_name }}
          Namespace: {{ my_role_namespace }}
          Status: {{ my_role_execution_status | default('unknown') }}
          Duration: {{ my_role_execution_duration | default(0) }}s
          
          {% if my_role_execution_status == 'failed' %}
          Error: {{ my_role_execution_error }}
          {% endif %}
        dest: "{{ my_role_log_dir }}/execution-{{ ansible_date_time.epoch }}.log"
        mode: '0644'
      delegate_to: localhost
      when: my_role_enable_logging | default(true)
      tags: [logging]
```

#### verify.yml - Post-Execution Verification

Purpose: Verify that the operation completed successfully and the system is in the expected state

```yaml
---
# Post-execution verification: Ensure operation completed correctly
# Validate the system is in the expected state

- name: Wait for resources to stabilize
  ansible.builtin.pause:
    seconds: 10
    prompt: "Waiting for resources to stabilize before verification"
  tags: [verification]

- name: Verify primary resource exists and is healthy
  kubernetes.core.k8s_info:
    api_version: "{{ my_role_api_version }}"
    kind: "{{ my_role_kind }}"
    name: "{{ my_role_resource_name }}"
    namespace: "{{ my_role_namespace }}"
  register: primary_resource
  failed_when: primary_resource.resources | length == 0
  tags: [verification]

- name: Check resource status
  ansible.builtin.assert:
    that:
      - primary_resource.resources[0].status.phase is defined
      - primary_resource.resources[0].status.phase in ['Running', 'Active', 'Available']
    fail_msg: "Resource is not in expected state: {{ primary_resource.resources[0].status.phase | default('Unknown') }}"
    success_msg: "Resource is in expected state"
  tags: [verification]

- name: Verify dependent resources
  block:
    - name: Get pods for resource
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Pod
        namespace: "{{ my_role_namespace }}"
        label_selectors:
          - "app={{ my_role_resource_name }}"
      register: resource_pods
    
    - name: Verify pod count
      ansible.builtin.assert:
        that:
          - resource_pods.resources | length >= my_role_minimum_replicas
        fail_msg: "Insufficient pods running (found {{ resource_pods.resources | length }}, expected {{ my_role_minimum_replicas }})"
        success_msg: "Correct number of pods running"
    
    - name: Verify all pods are ready
      ansible.builtin.assert:
        that:
          - item.status.phase == 'Running'
          - item.status.conditions | selectattr('type', 'equalto', 'Ready') | selectattr('status', 'equalto', 'True') | list | length > 0
        fail_msg: "Pod {{ item.metadata.name }} is not ready (Phase: {{ item.status.phase }})"
      loop: "{{ resource_pods.resources }}"
      loop_control:
        label: "{{ item.metadata.name }}"
  tags: [verification]

- name: Verify services are accessible
  block:
    - name: Get services for resource
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Service
        namespace: "{{ my_role_namespace }}"
        label_selectors:
          - "app={{ my_role_resource_name }}"
      register: resource_services
    
    - name: Check service endpoints
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Endpoints
        namespace: "{{ my_role_namespace }}"
        name: "{{ item.metadata.name }}"
      register: service_endpoints
      loop: "{{ resource_services.resources }}"
      loop_control:
        label: "{{ item.metadata.name }}"
    
    - name: Verify endpoints exist
      ansible.builtin.assert:
        that:
          - item.resources[0].subsets is defined
          - item.resources[0].subsets | length > 0
          - item.resources[0].subsets[0].addresses is defined
          - item.resources[0].subsets[0].addresses | length > 0
        fail_msg: "Service {{ item.item.metadata.name }} has no ready endpoints"
      loop: "{{ service_endpoints.results }}"
      loop_control:
        label: "{{ item.item.metadata.name }}"
  tags: [verification]

- name: Perform health check
  ansible.builtin.uri:
    url: "{{ my_role_health_check_url }}"
    method: GET
    status_code: 200
    timeout: 10
  register: health_check
  retries: 5
  delay: 10
  until: health_check.status == 200
  when: my_role_health_check_url is defined
  tags: [verification, health-check]

- name: Verify resource version updated
  ansible.builtin.assert:
    that:
      - primary_resource.resources[0].spec.version == my_role_target_version
    fail_msg: "Resource version mismatch (expected {{ my_role_target_version }}, found {{ primary_resource.resources[0].spec.version }})"
    success_msg: "Resource version correctly updated"
  when: my_role_target_version is defined
  tags: [verification]

- name: Check for error events
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Event
    namespace: "{{ my_role_namespace }}"
  register: namespace_events
  tags: [verification]

- name: Filter error events for our resources
  ansible.builtin.set_fact:
    error_events: "{{ namespace_events.resources | selectattr('type', 'equalto', 'Warning') | selectattr('involvedObject.name', 'equalto', my_role_resource_name) | list }}"
  tags: [verification]

- name: Warn if error events found
  ansible.builtin.debug:
    msg: |
      WARNING: {{ error_events | length }} error events found for resource
      Recent errors:
      {{ error_events | map(attribute='message') | list | join('\n') }}
  when: error_events | length > 0
  tags: [verification]

- name: Verification complete
  ansible.builtin.debug:
    msg: |
      All verification checks passed
      Resource: {{ my_role_resource_name }}
      Status: {{ primary_resource.resources[0].status.phase }}
      Pods: {{ resource_pods.resources | length }}
      Services: {{ resource_services.resources | length }}
  tags: [verification]
```

#### monitor.yml - Progress Monitoring

Purpose: Monitor long-running operations with proper timeout handling

```yaml
---
# Progress monitoring: Monitor operation until completion
# Implements dual timeout strategy (global + inactivity)

- name: Initialize monitoring variables
  ansible.builtin.set_fact:
    monitoring_start_time: "{{ ansible_date_time.epoch }}"
    last_activity_time: "{{ ansible_date_time.epoch }}"
    global_timeout: "{{ my_role_global_timeout | default(2100) }}"  # 35 minutes
    inactivity_timeout: "{{ my_role_inactivity_timeout | default(2100) }}"
    per_resource_timeout: "{{ my_role_per_resource_timeout | default(1500) }}"  # 25 minutes
    resource_tracking: {}
    monitoring_interval: "{{ my_role_monitoring_interval | default(15) }}"
  tags: [monitoring]

- name: Display monitoring configuration
  ansible.builtin.debug:
    msg: |
      Starting operation monitoring
      Global timeout: {{ global_timeout }}s ({{ (global_timeout / 60) | int }}m)
      Inactivity timeout: {{ inactivity_timeout }}s ({{ (inactivity_timeout / 60) | int }}m)
      Per-resource timeout: {{ per_resource_timeout }}s ({{ (per_resource_timeout / 60) | int }}m)
      Monitoring interval: {{ monitoring_interval }}s
  tags: [monitoring]

- name: Monitor operation progress
  block:
    - name: Get current resource state
      kubernetes.core.k8s_info:
        api_version: "{{ my_role_api_version }}"
        kind: "{{ my_role_kind }}"
        namespace: "{{ my_role_namespace }}"
        label_selectors: "{{ my_role_label_selectors | default([]) }}"
      register: current_resources
      tags: [monitoring]
    
    - name: Analyze resource states
      ansible.builtin.set_fact:
        total_resources: "{{ current_resources.resources | length }}"
        completed_resources: "{{ current_resources.resources | selectattr('status.phase', 'equalto', 'Succeeded') | list }}"
        in_progress_resources: "{{ current_resources.resources | selectattr('status.phase', 'in', ['Running', 'Pending']) | list }}"
        failed_resources: "{{ current_resources.resources | selectattr('status.phase', 'equalto', 'Failed') | list }}"
      tags: [monitoring]
    
    - name: Detect activity (state changes)
      ansible.builtin.set_fact:
        previous_completed_count: "{{ resource_tracking.get('completed_count', 0) }}"
        current_completed_count: "{{ completed_resources | length }}"
      tags: [monitoring]
    
    - name: Determine if activity occurred
      ansible.builtin.set_fact:
        has_activity: "{{ current_completed_count | int != previous_completed_count | int }}"
      tags: [monitoring]
    
    - name: Update activity timestamp if progress made
      ansible.builtin.set_fact:
        last_activity_time: "{{ ansible_date_time.epoch }}"
        resource_tracking: "{{ resource_tracking | combine({'completed_count': current_completed_count}) }}"
      when: has_activity
      tags: [monitoring]
    
    - name: Calculate elapsed times
      ansible.builtin.set_fact:
        total_elapsed: "{{ (ansible_date_time.epoch | int) - (monitoring_start_time | int) }}"
        time_since_activity: "{{ (ansible_date_time.epoch | int) - (last_activity_time | int) }}"
      tags: [monitoring]
    
    - name: Check global timeout
      ansible.builtin.fail:
        msg: |
          Global timeout exceeded
          Timeout: {{ global_timeout }}s
          Elapsed: {{ total_elapsed }}s
          Completed: {{ completed_resources | length }}/{{ total_resources }}
      when: total_elapsed | int > global_timeout | int
      tags: [monitoring]
    
    - name: Check inactivity timeout
      ansible.builtin.fail:
        msg: |
          Inactivity timeout exceeded
          No progress for {{ time_since_activity }}s
          Timeout: {{ inactivity_timeout }}s
          Stuck at: {{ completed_resources | length }}/{{ total_resources }} resources
      when: time_since_activity | int > inactivity_timeout | int
      tags: [monitoring]
    
    - name: Check for failed resources
      ansible.builtin.fail:
        msg: |
          Resource failures detected
          Failed: {{ failed_resources | length }}
          Failed resources: {{ failed_resources | map(attribute='metadata.name') | list | join(', ') }}
      when: failed_resources | length > 0
      tags: [monitoring]
    
    - name: Track individual resource timeouts
      ansible.builtin.set_fact:
        resource_tracking: >
          {{ resource_tracking | combine({
            item.metadata.name: {
              'start_time': resource_tracking.get(item.metadata.name, {}).get('start_time', ansible_date_time.epoch),
              'status': item.status.phase
            }
          }) }}
      loop: "{{ current_resources.resources }}"
      loop_control:
        label: "{{ item.metadata.name }}"
      tags: [monitoring]
    
    - name: Check per-resource timeout
      ansible.builtin.fail:
        msg: "Resource {{ item.key }} exceeded per-resource timeout of {{ per_resource_timeout }}s"
      when:
        - item.value.start_time is defined
        - (ansible_date_time.epoch | int) - (item.value.start_time | int) > per_resource_timeout | int
        - item.value.status not in ['Succeeded', 'Complete']
      loop: "{{ resource_tracking | dict2items }}"
      loop_control:
        label: "{{ item.key }}"
      tags: [monitoring]
    
    - name: Display progress
      ansible.builtin.debug:
        msg: |
          Monitoring Progress:
          Completed: {{ completed_resources | length }}/{{ total_resources }} ({{ ((completed_resources | length / total_resources) * 100) | int }}%)
          In Progress: {{ in_progress_resources | length }}
          Failed: {{ failed_resources | length }}
          Elapsed: {{ total_elapsed }}s ({{ (total_elapsed / 60) | int }}m)
          Time since last activity: {{ time_since_activity }}s
      tags: [monitoring]
    
    - name: Check if operation complete
      ansible.builtin.set_fact:
        operation_complete: "{{ completed_resources | length == total_resources }}"
      tags: [monitoring]
    
    - name: Wait before next check
      ansible.builtin.pause:
        seconds: "{{ monitoring_interval }}"
      when: not operation_complete
      tags: [monitoring]
  
  until: operation_complete
  retries: "{{ (global_timeout / monitoring_interval) | int }}"
  delay: "{{ monitoring_interval }}"
  tags: [monitoring]

- name: Calculate final statistics
  ansible.builtin.set_fact:
    monitoring_duration: "{{ (ansible_date_time.epoch | int) - (monitoring_start_time | int) }}"
    monitoring_result: "success"
  tags: [monitoring]

- name: Display monitoring summary
  ansible.builtin.debug:
    msg: |
      Monitoring complete
      Total resources: {{ total_resources }}
      Completed: {{ completed_resources | length }}
      Duration: {{ monitoring_duration }}s ({{ (monitoring_duration / 60) | int }}m {{ (monitoring_duration % 60) }}s)
      Average time per resource: {{ (monitoring_duration / total_resources) | int }}s
  tags: [monitoring]
```

Continue in next response...

#### report.yml - Result Reporting

Purpose: Generate comprehensive reports of operation results

```yaml
---
# Result reporting: Generate operation reports
# Creates both human-readable and machine-readable reports

- name: Collect operation metrics
  ansible.builtin.set_fact:
    report_data:
      operation:
        name: "{{ operation_name }}"
        target: "{{ my_role_resource_name }}"
        namespace: "{{ my_role_namespace }}"
        timestamp: "{{ ansible_date_time.iso8601 }}"
      execution:
        status: "{{ my_role_execution_status }}"
        duration: "{{ my_role_execution_duration }}s"
        start_time: "{{ execution_start_time }}"
        end_time: "{{ ansible_date_time.epoch }}"
      resources:
        total: "{{ total_resources | default(0) }}"
        completed: "{{ completed_resources | default([]) | length }}"
        failed: "{{ failed_resources | default([]) | length }}"
      cluster:
        version: "{{ cluster_info.version.server.kubernetes.gitVersion }}"
        nodes: "{{ nodes.resources | length }}"
  tags: [reporting]

- name: Generate JSON report
  ansible.builtin.copy:
    content: "{{ report_data | to_nice_json }}"
    dest: "{{ my_role_report_destination }}"
    mode: '0644'
  delegate_to: localhost
  when: my_role_report_format == 'json'
  tags: [reporting]

- name: Generate human-readable report
  ansible.builtin.template:
    src: report.j2
    dest: "{{ my_role_report_destination }}"
    mode: '0644'
  delegate_to: localhost
  when: my_role_report_format == 'text'
  tags: [reporting]

- name: Display report location
  ansible.builtin.debug:
    msg: "Report generated: {{ my_role_report_destination }}"
  tags: [reporting]
```

### Advanced Role Patterns

#### Multi-Stage Operations

For operations that have distinct stages that must be executed in order:

```yaml
---
# Multi-stage operation pattern
# Each stage must complete before next begins

- name: Stage 1 - Preparation
  block:
    - name: Execute stage 1 tasks
      ansible.builtin.import_tasks: stage1_preparation.yml
    
    - name: Verify stage 1 completion
      ansible.builtin.assert:
        that:
          - stage1_complete is defined
          - stage1_complete | bool
        fail_msg: "Stage 1 did not complete successfully"
  tags: [stage1, preparation]

- name: Stage 2 - Data Migration  
  block:
    - name: Execute stage 2 tasks
      ansible.builtin.import_tasks: stage2_migration.yml
    
    - name: Verify stage 2 completion
      ansible.builtin.assert:
        that:
          - stage2_complete is defined
          - stage2_complete | bool
        fail_msg: "Stage 2 did not complete successfully"
  when: stage1_complete | default(false)
  tags: [stage2, migration]

- name: Stage 3 - Verification
  block:
    - name: Execute stage 3 tasks
      ansible.builtin.import_tasks: stage3_verification.yml
    
    - name: Verify stage 3 completion
      ansible.builtin.assert:
        that:
          - stage3_complete is defined
          - stage3_complete | bool
        fail_msg: "Stage 3 did not complete successfully"
  when:
    - stage1_complete | default(false)
    - stage2_complete | default(false)
  tags: [stage3, verification]
```

#### Conditional Workflows

Different execution paths based on detected conditions:

```yaml
---
# Conditional workflow pattern
# Different paths based on current state

- name: Detect current state
  block:
    - name: Check if resource exists
      kubernetes.core.k8s_info:
        api_version: v1
        kind: "{{ resource_kind }}"
        name: "{{ resource_name }}"
        namespace: "{{ resource_namespace }}"
      register: resource_check
    
    - name: Determine workflow path
      ansible.builtin.set_fact:
        resource_exists: "{{ resource_check.resources | length > 0 }}"
        resource_state: "{{ resource_check.resources[0].status.phase if resource_check.resources | length > 0 else 'NotFound' }}"
  tags: [detection]

- name: Path 1 - Create new resource
  ansible.builtin.import_tasks: create_new.yml
  when: not resource_exists
  tags: [create]

- name: Path 2 - Update existing resource
  ansible.builtin.import_tasks: update_existing.yml
  when:
    - resource_exists
    - resource_state in ['Running', 'Ready']
  tags: [update]

- name: Path 3 - Repair broken resource
  ansible.builtin.import_tasks: repair.yml
  when:
    - resource_exists
    - resource_state not in ['Running', 'Ready']
  tags: [repair]
```

---

## Advanced Task Patterns

### Complex Looping Strategies

#### Looping with Complex Data Structures

```yaml
---
# Loop over dictionary with nested data

- name: Process applications
  block:
    - name: Deploy each application
      kubernetes.core.k8s:
        definition:
          apiVersion: apps/v1
          kind: Deployment
          metadata:
            name: "{{ item.key }}"
            namespace: "{{ item.value.namespace }}"
          spec:
            replicas: "{{ item.value.replicas }}"
            selector:
              matchLabels:
                app: "{{ item.key }}"
            template:
              metadata:
                labels:
                  app: "{{ item.key }}"
              spec:
                containers:
                  - name: "{{ item.key }}"
                    image: "{{ item.value.image }}"
                    ports:
                      - containerPort: "{{ item.value.port }}"
      loop: "{{ applications | dict2items }}"
      loop_control:
        label: "{{ item.key }}"
      register: deploy_results
    
    - name: Wait for each deployment
      kubernetes.core.k8s_info:
        api_version: apps/v1
        kind: Deployment
        name: "{{ item.item.key }}"
        namespace: "{{ item.item.value.namespace }}"
      register: deployment_status
      until:
        - deployment_status.resources[0].status.readyReplicas is defined
        - deployment_status.resources[0].status.readyReplicas == item.item.value.replicas
      retries: 30
      delay: 10
      loop: "{{ deploy_results.results }}"
      loop_control:
        label: "{{ item.item.key }}"
  
  vars:
    applications:
      frontend:
        namespace: production
        replicas: 3
        image: myapp/frontend:1.2.3
        port: 8080
      backend:
        namespace: production
        replicas: 5
        image: myapp/backend:1.2.3
        port: 8081
      worker:
        namespace: production
        replicas: 2
        image: myapp/worker:1.2.3
        port: 8082
```

#### Batch Processing with Batches

```yaml
---
# Process items in batches to avoid overwhelming system

- name: Get all nodes
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Node
  register: all_nodes

- name: Create batches
  ansible.builtin.set_fact:
    node_batches: "{{ all_nodes.resources | batch(batch_size) | list }}"
  vars:
    batch_size: 5

- name: Process each batch
  block:
    - name: Process nodes in batch {{ batch_index }}
      kubernetes.core.k8s:
        api_version: v1
        kind: Node
        name: "{{ item.metadata.name }}"
        definition:
          metadata:
            labels:
              processed: "true"
              batch: "{{ batch_index }}"
      loop: "{{ item }}"
      loop_control:
        label: "{{ item.metadata.name }}"
    
    - name: Wait between batches
      ansible.builtin.pause:
        seconds: 30
        prompt: "Waiting between batches to allow system to stabilize"
      when: batch_index < (node_batches | length - 1)
  
  loop: "{{ node_batches }}"
  loop_control:
    loop_var: item
    index_var: batch_index
    label: "Batch {{ batch_index + 1 }}/{{ node_batches | length }}"
```

#### Until Loops with Complex Conditions

```yaml
---
# Wait for complex conditions with multiple requirements

- name: Wait for cluster to be fully ready
  block:
    - name: Check cluster state
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Node
      register: nodes
    
    - name: Check critical pods
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Pod
        namespace: kube-system
        label_selectors:
          - "component in (kube-apiserver,kube-controller-manager,kube-scheduler,etcd)"
      register: critical_pods
    
    - name: Evaluate readiness
      ansible.builtin.set_fact:
        ready_nodes: "{{ nodes.resources | selectattr('status.conditions', 'defined') | selectattr('status.conditions', 'selectattr', 'type', 'equalto', 'Ready') | selectattr('status.conditions', 'selectattr', 'status', 'equalto', 'True') | list }}"
        ready_critical_pods: "{{ critical_pods.resources | selectattr('status.phase', 'equalto', 'Running') | list }}"
    
    - name: Display status
      ansible.builtin.debug:
        msg: |
          Ready nodes: {{ ready_nodes | length }}/{{ nodes.resources | length }}
          Ready critical pods: {{ ready_critical_pods | length }}/{{ critical_pods.resources | length }}
    
    - name: Check if fully ready
      ansible.builtin.set_fact:
        cluster_ready: "{{ ready_nodes | length == nodes.resources | length and ready_critical_pods | length == critical_pods.resources | length }}"
  
  until: cluster_ready | bool
  retries: 60
  delay: 10
```

### Advanced Filtering and Data Transformation

#### Using Jinja2 Filters Effectively

```yaml
---
# Advanced data filtering and transformation

- name: Get all pods
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: production
  register: all_pods

# Filter pods by multiple criteria
- name: Filter running application pods
  ansible.builtin.set_fact:
    app_pods: "{{ all_pods.resources | 
                   selectattr('status.phase', 'equalto', 'Running') |
                   selectattr('metadata.labels.app', 'defined') |
                   selectattr('metadata.labels.app', 'match', '^myapp-') |
                   list }}"

# Extract specific fields
- name: Get pod names and IPs
  ansible.builtin.set_fact:
    pod_info: "{{ app_pods | 
                  map('combine', {'name': item.metadata.name, 'ip': item.status.podIP}) |
                  list }}"

# Group by label
- name: Group pods by component
  ansible.builtin.set_fact:
    pods_by_component: "{{ app_pods | 
                           groupby('metadata.labels.component') |
                           items2dict }}"

# Calculate statistics
- name: Calculate resource usage
  ansible.builtin.set_fact:
    total_memory_requests: "{{ app_pods | 
                                map(attribute='spec.containers') | 
                                flatten |
                                map(attribute='resources.requests.memory') |
                                map('regex_replace', 'Mi$', '') |
                                map('int') |
                                sum }}"
    total_cpu_requests: "{{ app_pods |
                            map(attribute='spec.containers') |
                            flatten |
                            map(attribute='resources.requests.cpu') |
                            map('regex_replace', 'm$', '') |
                            map('int') |
                            sum }}"

# Custom filtering with reject/select
- name: Find pods with issues
  ansible.builtin.set_fact:
    problem_pods: "{{ all_pods.resources |
                      rejectattr('status.phase', 'equalto', 'Running') |
                      list }}"
    
    high_restart_pods: "{{ all_pods.resources |
                           selectattr('status.containerStatuses', 'defined') |
                           selectattr('status.containerStatuses.0.restartCount', 'gt', 5) |
                           list }}"

# Transform and combine
- name: Create pod summary
  ansible.builtin.set_fact:
    pod_summary:
      total: "{{ all_pods.resources | length }}"
      running: "{{ all_pods.resources | selectattr('status.phase', 'equalto', 'Running') | list | length }}"
      pending: "{{ all_pods.resources | selectattr('status.phase', 'equalto', 'Pending') | list | length }}"
      failed: "{{ all_pods.resources | selectattr('status.phase', 'equalto', 'Failed') | list | length }}"
      by_node: "{{ all_pods.resources | groupby('spec.nodeName') | items2dict(key_name='node', value_name='pods') }}"
```

#### Custom Jinja2 Filter Plugin

Create `filter_plugins/kubernetes_filters.py`:

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.errors import AnsibleFilterError
from typing import Any, Dict, List


def pod_ready(pod: Dict[str, Any]) -> bool:
    """
    Check if a pod is ready.
    
    Args:
        pod: Pod resource dictionary
        
    Returns:
        True if pod is ready, False otherwise
    """
    try:
        conditions = pod.get("status", {}).get("conditions", [])
        ready_condition = next(
            (c for c in conditions if c.get("type") == "Ready"), None
        )
        return ready_condition is not None and ready_condition.get("status") == "True"
    except (KeyError, TypeError, StopIteration):
        return False


def pods_ready_count(pods: List[Dict[str, Any]]) -> int:
    """
    Count number of ready pods.
    
    Args:
        pods: List of pod resource dictionaries
        
    Returns:
        Number of ready pods
    """
    return sum(1 for pod in pods if pod_ready(pod))


def parse_k8s_quantity(quantity: str) -> int:
    """
    Parse Kubernetes quantity string to integer.
    
    Handles suffixes: Ki, Mi, Gi, Ti, m
    
    Args:
        quantity: Quantity string (e.g., "2Gi", "500m")
        
    Returns:
        Integer value
    """
    if not quantity:
        return 0
    
    quantity = str(quantity)
    
    # Handle millicores (m)
    if quantity.endswith("m"):
        return int(quantity[:-1])
    
    # Handle memory units
    multipliers = {
        "Ki": 1024,
        "Mi": 1024 ** 2,
        "Gi": 1024 ** 3,
        "Ti": 1024 ** 4,
        "K": 1000,
        "M": 1000 ** 2,
        "G": 1000 ** 3,
        "T": 1000 ** 4,
    }
    
    for suffix, multiplier in multipliers.items():
        if quantity.endswith(suffix):
            return int(quantity[: -len(suffix)]) * multiplier
    
    # No suffix, return as int
    try:
        return int(quantity)
    except ValueError:
        return 0


def resource_requests_total(pods: List[Dict[str, Any]], resource: str) -> int:
    """
    Calculate total resource requests for pods.
    
    Args:
        pods: List of pod dictionaries
        resource: Resource type ('cpu' or 'memory')
        
    Returns:
        Total resource requests
    """
    total = 0
    for pod in pods:
        containers = pod.get("spec", {}).get("containers", [])
        for container in containers:
            requests = container.get("resources", {}).get("requests", {})
            if resource in requests:
                total += parse_k8s_quantity(requests[resource])
    return total


class FilterModule:
    """Ansible filter plugin for Kubernetes operations."""
    
    def filters(self):
        return {
            "pod_ready": pod_ready,
            "pods_ready_count": pods_ready_count,
            "parse_k8s_quantity": parse_k8s_quantity,
            "resource_requests_total": resource_requests_total,
        }
```

**Usage in playbooks:**

```yaml
---
- name: Use custom Kubernetes filters
  hosts: localhost
  tasks:
    - name: Get pods
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Pod
        namespace: production
      register: pods
    
    - name: Count ready pods
      ansible.builtin.debug:
        msg: "Ready pods: {{ pods.resources | pods_ready_count }}"
    
    - name: Calculate total memory requests
      ansible.builtin.debug:
        msg: "Total memory: {{ pods.resources | resource_requests_total('memory') }} bytes"
    
    - name: Filter only ready pods
      ansible.builtin.set_fact:
        ready_pods: "{{ pods.resources | selectattr('pod_ready') | list }}"
```

### Async Operations and Parallelism

#### Running Tasks Asynchronously

```yaml
---
# Run long operations in parallel

- name: Start multiple async operations
  block:
    - name: Trigger operation on each cluster
      kubernetes.core.k8s:
        definition: "{{ lookup('template', 'operation.j2') }}"
      async: 3600  # Run for up to 1 hour
      poll: 0      # Don't wait, return immediately
      register: async_operations
      loop: "{{ clusters }}"
      loop_control:
        label: "{{ item.name }}"
    
    - name: Do other work while operations run
      ansible.builtin.debug:
        msg: "Operations running in background, continuing with other tasks"
    
    - name: Check on async operations periodically
      ansible.builtin.async_status:
        jid: "{{ item.ansible_job_id }}"
      register: operation_results
      until: operation_results.finished
      retries: 360  # Check for up to 1 hour
      delay: 10     # Check every 10 seconds
      loop: "{{ async_operations.results }}"
      loop_control:
        label: "{{ item.item.name }}"
    
    - name: Verify all operations succeeded
      ansible.builtin.assert:
        that:
          - item.rc == 0
        fail_msg: "Operation failed on {{ item.item.name }}"
      loop: "{{ operation_results.results }}"
      loop_control:
        label: "{{ item.item.name }}"
```

#### Parallel Execution with Strategy

```yaml
---
# Use free strategy for parallel execution
- name: Parallel cluster operations
  hosts: all_clusters
  strategy: free  # Each host runs independently
  gather_facts: false
  
  tasks:
    - name: Check cluster health
      kubernetes.core.k8s_cluster_info:
      register: cluster_info
    
    - name: Execute operation
      kubernetes.core.k8s:
        definition: "{{ operation_definition }}"
      when: cluster_info is succeeded
    
    - name: Wait for completion
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Pod
        namespace: operations
        name: "operation-{{ inventory_hostname }}"
      register: operation_pod
      until: operation_pod.resources[0].status.phase == 'Succeeded'
      retries: 180
      delay: 10
```

---

## Kubernetes/OpenShift Native Automation

This section provides comprehensive examples of replacing shell commands with native Ansible modules.

### Complete oc Command Translation Guide

#### Getting Resources

**Task: List all pods in a namespace**

```yaml
# WRONG - Shell script approach
- name: Get pods (wrong way)
  shell: oc get pods -n {{ namespace }} --no-headers
  register: pods_output

- name: Parse pod names
  shell: echo "{{ pods_output.stdout }}" | awk '{print $1}'
  register: pod_names

# RIGHT - Ansible approach
- name: Get pods (right way)
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: "{{ namespace }}"
  register: pods

- name: Extract pod names
  ansible.builtin.set_fact:
    pod_names: "{{ pods.resources | map(attribute='metadata.name') | list }}"
```

**Task: Get pods with specific labels**

```yaml
# WRONG
- name: Get app pods (wrong)
  shell: oc get pods -n {{ namespace }} -l app=myapp --no-headers

# RIGHT
- name: Get app pods (right)
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: "{{ namespace }}"
    label_selectors:
      - "app=myapp"
  register: app_pods
```

**Task: Get resource by name**

```yaml
# WRONG
- name: Get deployment (wrong)
  shell: oc get deployment myapp -n {{ namespace }} -o json
  register: deploy_json

- name: Parse JSON
  set_fact:
    deployment: "{{ deploy_json.stdout | from_json }}"

# RIGHT
- name: Get deployment (right)
  kubernetes.core.k8s_info:
    api_version: apps/v1
    kind: Deployment
    name: myapp
    namespace: "{{ namespace }}"
  register: deployment_info

- name: Access deployment
  set_fact:
    deployment: "{{ deployment_info.resources[0] }}"
```

#### Creating/Updating Resources

**Task: Create a deployment**

```yaml
# WRONG
- name: Create deployment (wrong)
  shell: |
    cat <<EOF | oc apply -f -
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: myapp
      namespace: {{ namespace }}
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: myapp
      template:
        metadata:
          labels:
            app: myapp
        spec:
          containers:
          - name: myapp
            image: myapp:1.0.0
    EOF

# RIGHT
- name: Create deployment (right)
  kubernetes.core.k8s:
    state: present
    definition:
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: myapp
        namespace: "{{ namespace }}"
      spec:
        replicas: 3
        selector:
          matchLabels:
            app: myapp
        template:
          metadata:
            labels:
              app: myapp
          spec:
            containers:
              - name: myapp
                image: "myapp:{{ app_version }}"
```

**Task: Update resource with patch**

```yaml
# WRONG
- name: Scale deployment (wrong)
  shell: |
    oc patch deployment myapp -n {{ namespace }} \
      --type merge \
      --patch '{"spec":{"replicas":{{ replicas }}}}'

# RIGHT
- name: Scale deployment (right)
  kubernetes.core.k8s:
    api_version: apps/v1
    kind: Deployment
    name: myapp
    namespace: "{{ namespace }}"
    definition:
      spec:
        replicas: "{{ replicas }}"
```

**Task: Apply from template**

```yaml
# WRONG
- name: Apply config (wrong)
  shell: oc apply -f /tmp/config.yaml

# RIGHT - Option 1: From file
- name: Apply config from file (right)
  kubernetes.core.k8s:
    state: present
    src: /tmp/config.yaml

# RIGHT - Option 2: From template
- name: Apply config from template (right)
  kubernetes.core.k8s:
    state: present
    definition: "{{ lookup('template', 'config.j2') | from_yaml }}"
```

#### Deleting Resources

**Task: Delete a resource**

```yaml
# WRONG
- name: Delete pod (wrong)
  shell: oc delete pod {{ pod_name }} -n {{ namespace }}

# RIGHT
- name: Delete pod (right)
  kubernetes.core.k8s:
    api_version: v1
    kind: Pod
    name: "{{ pod_name }}"
    namespace: "{{ namespace }}"
    state: absent
```

**Task: Delete with wait**

```yaml
# WRONG
- name: Delete and wait (wrong)
  shell: oc delete deployment myapp -n {{ namespace }}
- name: Wait
  shell: sleep 30

# RIGHT
- name: Delete and wait (right)
  kubernetes.core.k8s:
    api_version: apps/v1
    kind: Deployment
    name: myapp
    namespace: "{{ namespace }}"
    state: absent
    wait: true
    wait_timeout: 300
```

#### Executing Commands in Pods

**Task: Run command in pod**

```yaml
# WRONG
- name: Run command (wrong)
  shell: oc rsh -n {{ namespace }} {{ pod_name }} /bin/bash -c "{{ command }}"
  register: output

# RIGHT
- name: Run command (right)
  kubernetes.core.k8s_exec:
    namespace: "{{ namespace }}"
    pod: "{{ pod_name }}"
    command: "{{ command }}"
  register: output

- name: Display output
  ansible.builtin.debug:
    msg: "{{ output.stdout }}"
```

**Task: Run command in specific container**

```yaml
# WRONG
- name: Run in container (wrong)
  shell: oc rsh -n {{ namespace }} -c {{ container }} {{ pod_name }} {{ command }}

# RIGHT
- name: Run in container (right)
  kubernetes.core.k8s_exec:
    namespace: "{{ namespace }}"
    pod: "{{ pod_name }}"
    container: "{{ container }}"
    command: "{{ command }}"
```

**Task: Copy file to/from pod**

```yaml
# WRONG
- name: Copy to pod (wrong)
  shell: oc cp /local/file {{ namespace }}/{{ pod_name }}:/remote/file

# RIGHT
- name: Copy to pod (right)
  kubernetes.core.k8s_cp:
    namespace: "{{ namespace }}"
    pod: "{{ pod_name }}"
    remote_path: /remote/file
    local_path: /local/file
    state: to_pod
```

Continue in next response with more Kubernetes patterns and real-world examples...

### Real-World Kubernetes Automation Examples

#### Example 1: Storage Cluster Upgrade Monitoring

Complete implementation showing proper Kubernetes automation for Portworx-style upgrades:

```yaml
---
# roles/storage_upgrade/tasks/main.yml
# Real-world storage cluster upgrade with monitoring

- name: Preflight - Verify cluster health
  kubernetes.core.k8s_info:
    api_version: core.libopenstorage.org/v1
    kind: StorageCluster
    name: "{{ cluster_name }}"
    namespace: "{{ cluster_namespace }}"
  register: storage_cluster
  failed_when:
    - storage_cluster.resources | length == 0
    - storage_cluster.resources[0].status.phase != "Running"

- name: Get current cluster configuration
  ansible.builtin.set_fact:
    current_image: "{{ storage_cluster.resources[0].spec.image }}"
    current_version: "{{ storage_cluster.resources[0].spec.image.split(':')[1] }}"
    cluster_nodes: "{{ storage_cluster.resources[0].status.storage.storageNodesStatus | length }}"

- name: Validate upgrade path
  ansible.builtin.assert:
    that:
      - current_version is version(target_version, '<')
      - target_version in supported_versions
    fail_msg: "Invalid upgrade from {{ current_version }} to {{ target_version }}"

- name: Update autoUpdateComponents before image update
  kubernetes.core.k8s:
    api_version: core.libopenstorage.org/v1
    kind: StorageCluster
    name: "{{ cluster_name }}"
    namespace: "{{ cluster_namespace }}"
    definition:
      spec:
        autoUpdateComponents: Once
  register: auto_update_result

- name: Wait for operator to process autoUpdateComponents
  ansible.builtin.pause:
    seconds: 5

- name: Trigger upgrade by updating image
  kubernetes.core.k8s:
    api_version: core.libopenstorage.org/v1
    kind: StorageCluster
    name: "{{ cluster_name }}"
    namespace: "{{ cluster_namespace }}"
    definition:
      spec:
        image: "portworx/oci-monitor:{{ target_version }}"
  register: upgrade_trigger

- name: Initialize upgrade monitoring
  ansible.builtin.set_fact:
    upgrade_start_time: "{{ ansible_date_time.epoch }}"
    last_activity_time: "{{ ansible_date_time.epoch }}"
    pod_upgrade_tracking: {}

- name: Monitor rolling upgrade progress
  block:
    - name: Get storage pods current state
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Pod
        namespace: "{{ cluster_namespace }}"
        label_selectors:
          - "name=portworx"
      register: storage_pods
    
    - name: Analyze upgrade progress
      ansible.builtin.set_fact:
        target_image: "portworx/oci-monitor:{{ target_version }}"
        upgraded_pods: "{{ storage_pods.resources | selectattr('spec.containers[0].image', 'equalto', 'portworx/oci-monitor:' + target_version) | list }}"
        upgrading_pods: "{{ storage_pods.resources | rejectattr('spec.containers[0].image', 'equalto', 'portworx/oci-monitor:' + target_version) | list }}"
    
    - name: Check for pod activity (state changes)
      ansible.builtin.set_fact:
        previous_count: "{{ pod_upgrade_tracking.get('upgraded_count', 0) }}"
        current_count: "{{ upgraded_pods | length }}"
    
    - name: Update activity time if progress made
      ansible.builtin.set_fact:
        last_activity_time: "{{ ansible_date_time.epoch }}"
        pod_upgrade_tracking: "{{ pod_upgrade_tracking | combine({'upgraded_count': current_count}) }}"
      when: current_count | int != previous_count | int
    
    - name: Calculate elapsed times
      ansible.builtin.set_fact:
        total_elapsed: "{{ (ansible_date_time.epoch | int) - (upgrade_start_time | int) }}"
        time_since_activity: "{{ (ansible_date_time.epoch | int) - (last_activity_time | int) }}"
    
    - name: Check global timeout
      ansible.builtin.fail:
        msg: "Upgrade exceeded global timeout of {{ global_timeout }}s (elapsed: {{ total_elapsed }}s)"
      when: total_elapsed | int > global_timeout | int
    
    - name: Check inactivity timeout
      ansible.builtin.fail:
        msg: "No upgrade activity for {{ time_since_activity }}s (timeout: {{ inactivity_timeout }}s)"
      when: time_since_activity | int > inactivity_timeout | int
    
    - name: Display progress
      ansible.builtin.debug:
        msg: |
          Upgrade Progress: {{ upgraded_pods | length }}/{{ storage_pods.resources | length }}
          Elapsed: {{ total_elapsed }}s ({{ (total_elapsed / 60) | int }}m)
          Last activity: {{ time_since_activity }}s ago
    
    - name: Track individual pod upgrade times
      ansible.builtin.set_fact:
        pod_upgrade_tracking: >
          {{ pod_upgrade_tracking | combine({
            item.metadata.name: {
              'start_time': pod_upgrade_tracking.get(item.metadata.name, {}).get('start_time', ansible_date_time.epoch),
              'image': item.spec.containers[0].image,
              'node': item.spec.nodeName
            }
          }) }}
      loop: "{{ storage_pods.resources }}"
      loop_control:
        label: "{{ item.metadata.name }}"
    
    - name: Check per-pod timeout
      ansible.builtin.fail:
        msg: "Pod {{ item.key }} exceeded per-pod timeout of {{ per_pod_timeout }}s"
      when:
        - item.value.start_time is defined
        - (ansible_date_time.epoch | int) - (item.value.start_time | int) > per_pod_timeout | int
        - item.value.image != target_image
      loop: "{{ pod_upgrade_tracking | dict2items }}"
      loop_control:
        label: "{{ item.key }}"
    
    - name: Wait before next check
      ansible.builtin.pause:
        seconds: 15
      when: upgraded_pods | length < storage_pods.resources | length
  
  until: upgraded_pods | length == storage_pods.resources | length
  retries: "{{ (global_timeout / 15) | int }}"
  delay: 15

- name: Verify cluster health post-upgrade
  kubernetes.core.k8s_info:
    api_version: core.libopenstorage.org/v1
    kind: StorageCluster
    name: "{{ cluster_name }}"
    namespace: "{{ cluster_namespace }}"
  register: final_cluster_state
  until:
    - final_cluster_state.resources[0].status.phase == "Running"
    - final_cluster_state.resources[0].status.conditions | selectattr('type', 'equalto', 'Available') | selectattr('status', 'equalto', 'True') | list | length > 0
  retries: 30
  delay: 10

- name: Display upgrade summary
  ansible.builtin.debug:
    msg: |
      Upgrade Complete
      Previous version: {{ current_version }}
      New version: {{ target_version }}
      Total time: {{ (ansible_date_time.epoch | int) - (upgrade_start_time | int) }}s
      Pods upgraded: {{ cluster_nodes }}
      Average time per pod: {{ ((ansible_date_time.epoch | int) - (upgrade_start_time | int)) / cluster_nodes | int }}s
```

#### Example 2: Multi-Cluster Configuration Sync

```yaml
---
# Synchronize configuration across multiple clusters

- name: Multi-cluster configuration sync
  hosts: k8s_clusters
  gather_facts: false
  serial: 1
  
  vars:
    config_namespace: "config-management"
    config_map_name: "global-config"
  
  tasks:
    - name: Verify cluster connectivity
      kubernetes.core.k8s_cluster_info:
      register: cluster_info
      failed_when: cluster_info is failed
    
    - name: Display cluster being configured
      ansible.builtin.debug:
        msg: |
          Configuring cluster: {{ inventory_hostname }}
          Version: {{ cluster_info.version.server.kubernetes.gitVersion }}
    
    - name: Ensure config namespace exists
      kubernetes.core.k8s:
        api_version: v1
        kind: Namespace
        name: "{{ config_namespace }}"
        state: present
    
    - name: Get current config if exists
      kubernetes.core.k8s_info:
        api_version: v1
        kind: ConfigMap
        name: "{{ config_map_name }}"
        namespace: "{{ config_namespace }}"
      register: current_config
      failed_when: false
    
    - name: Determine if update needed
      ansible.builtin.set_fact:
        config_exists: "{{ current_config.resources | length > 0 }}"
        update_needed: "{{ current_config.resources | length == 0 or current_config.resources[0].data != new_config_data }}"
    
    - name: Apply configuration
      kubernetes.core.k8s:
        state: present
        definition:
          apiVersion: v1
          kind: ConfigMap
          metadata:
            name: "{{ config_map_name }}"
            namespace: "{{ config_namespace }}"
            labels:
              managed-by: ansible
              sync-version: "{{ config_version }}"
          data: "{{ new_config_data }}"
      when: update_needed
      register: config_result
    
    - name: Trigger pod restarts if configuration changed
      block:
        - name: Get pods using this config
          kubernetes.core.k8s_info:
            api_version: v1
            kind: Pod
            namespace: "{{ config_namespace }}"
            label_selectors:
              - "uses-config={{ config_map_name }}"
          register: affected_pods
        
        - name: Delete pods to trigger restart with new config
          kubernetes.core.k8s:
            api_version: v1
            kind: Pod
            name: "{{ item.metadata.name }}"
            namespace: "{{ config_namespace }}"
            state: absent
          loop: "{{ affected_pods.resources }}"
          loop_control:
            label: "{{ item.metadata.name }}"
          when: affected_pods.resources | length > 0
        
        - name: Wait for pods to be recreated
          kubernetes.core.k8s_info:
            api_version: v1
            kind: Pod
            namespace: "{{ config_namespace }}"
            label_selectors:
              - "uses-config={{ config_map_name }}"
          register: new_pods
          until:
            - new_pods.resources | length >= affected_pods.resources | length
            - new_pods.resources | selectattr('status.phase', 'equalto', 'Running') | list | length == new_pods.resources | length
          retries: 60
          delay: 5
      when:
        - update_needed
        - trigger_pod_restart | default(true)
    
    - name: Record sync result
      ansible.builtin.set_fact:
        sync_result:
          cluster: "{{ inventory_hostname }}"
          config_version: "{{ config_version }}"
          updated: "{{ update_needed }}"
          pods_restarted: "{{ affected_pods.resources | default([]) | length if update_needed else 0 }}"
          timestamp: "{{ ansible_date_time.iso8601 }}"
        cacheable: true
    
    - name: Wait between clusters
      ansible.builtin.pause:
        seconds: 30
      when: inventory_hostname != groups['k8s_clusters'][-1]

- name: Generate sync report
  hosts: localhost
  gather_facts: false
  
  tasks:
    - name: Collect all sync results
      ansible.builtin.set_fact:
        all_results: "{{ groups['k8s_clusters'] | map('extract', hostvars, 'sync_result') | list }}"
    
    - name: Display sync summary
      ansible.builtin.debug:
        msg: |
          Multi-cluster Configuration Sync Complete
          Total clusters: {{ all_results | length }}
          Updated: {{ all_results | selectattr('updated', 'equalto', true) | list | length }}
          No changes: {{ all_results | selectattr('updated', 'equalto', false) | list | length }}
          Total pods restarted: {{ all_results | map(attribute='pods_restarted') | sum }}
    
    - name: Save sync report
      ansible.builtin.copy:
        content: "{{ all_results | to_nice_json }}"
        dest: "/tmp/config-sync-{{ ansible_date_time.epoch }}.json"
      delegate_to: localhost
```

---

## Custom Module Development Guide

### When and Why to Create Custom Modules

**Create a custom module when:**

1. You're repeating the same complex shell command pattern in multiple places
2. You need to interact with external tools that don't have Ansible modules
3. You need custom parsing or validation logic
4. You want proper idempotency for external tool operations

**Example: pxctl Status Module**

Let's build a complete custom module for interacting with Portworx's `pxctl` command:

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Platform Team
# Apache License 2.0

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: pxctl_status
short_description: Execute pxctl status command in Portworx pod
description:
  - Executes pxctl status commands inside a Portworx pod
  - Handles authentication token automatically
  - Parses structured output
  - Returns cluster health information
  - Provides proper error handling and idempotency
version_added: "1.0.0"
author:
  - Platform Team (@platform-team)
options:
  namespace:
    description:
      - Namespace where Portworx pods run
    type: str
    required: true
  pod_name:
    description:
      - Name of Portworx pod to execute command in
      - If not provided, will find first available portworx pod
    type: str
    required: false
  command:
    description:
      - Pxctl command to execute (without 'pxctl' prefix)
      - Examples: 'status', 'cluster list', 'volume list'
    type: str
    default: 'status'
  timeout:
    description:
      - Command execution timeout in seconds
    type: int
    default: 30
requirements:
  - python >= 3.11
  - kubectl command available
notes:
  - Module uses kubectl exec to run commands in pods
  - Automatically retrieves Portworx auth token from pod
  - Returns structured data for easy consumption
seealso:
  - module: kubernetes.core.k8s_exec
"""

EXAMPLES = r"""
# Get cluster status from specific pod
- name: Get Portworx cluster status
  pxctl_status:
    namespace: kube-system
    pod_name: portworx-abc123
  register: px_status

# Get status from any available pod
- name: Get cluster status from any pod
  pxctl_status:
    namespace: kube-system
  register: px_status

# Get specific node status
- name: Check node health
  pxctl_status:
    namespace: kube-system
    command: "status node show {{ node_id }}"
  register: node_status

# List all volumes
- name: Get volume list
  pxctl_status:
    namespace: kube-system
    command: "volume list"
  register: volumes
"""

RETURN = r"""
status:
  description: Overall cluster status
  type: str
  returned: always
  sample: "Operational"
output:
  description: Raw command output
  type: str
  returned: always
  sample: "Status: Operational\\nCluster ID: px-cluster-123"
parsed_data:
  description: Parsed structured data from output
  type: dict
  returned: when available
  sample:
    cluster_id: "px-cluster-123"
    cluster_uuid: "550e8400-e29b-41d4-a716-446655440000"
    status: "Operational"
nodes:
  description: List of cluster nodes
  type: list
  returned: when available
  sample:
    - id: "node1"
      status: "Online"
      ip: "10.0.0.1"
changed:
  description: Whether the module made changes
  type: bool
  returned: always
  sample: false
"""

import json
import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from ansible.module_utils.basic import AnsibleModule


class PxctlStatusRunner:
    """Main class for pxctl_status module."""
    
    def __init__(self, module: AnsibleModule):
        """Initialize the module runner."""
        self.module = module
        self.namespace = module.params["namespace"]
        self.pod_name = module.params.get("pod_name")
        self.command = module.params["command"]
        self.timeout = module.params["timeout"]
        self.auth_token: Optional[str] = None
    
    def find_portworx_pod(self) -> str:
        """Find a running Portworx pod if pod_name not specified."""
        cmd = [
            "kubectl",
            "get",
            "pods",
            "-n",
            self.namespace,
            "-l",
            "name=portworx",
            "-o",
            "jsonpath={.items[0].metadata.name}",
        ]
        
        rc, stdout, stderr = self.module.run_command(cmd, check_rc=False)
        
        if rc != 0 or not stdout:
            self.module.fail_json(
                msg=f"Failed to find Portworx pod in namespace {self.namespace}",
                stderr=stderr,
            )
        
        return stdout.strip()
    
    def get_auth_token(self, pod_name: str) -> str:
        """Retrieve Portworx authentication token from pod."""
        cmd = [
            "kubectl",
            "exec",
            "-n",
            self.namespace,
            pod_name,
            "--",
            "cat",
            "/etc/pwx/auth_token",
        ]
        
        rc, stdout, stderr = self.module.run_command(cmd, check_rc=False)
        
        if rc != 0:
            # Token might not be required
            return ""
        
        return stdout.strip()
    
    def execute_pxctl(self, pod_name: str, pxctl_command: str) -> Tuple[int, str, str]:
        """Execute pxctl command in pod."""
        # Build command
        cmd_parts = ["kubectl", "exec", "-n", self.namespace, pod_name, "--"]
        
        # Add auth token if available
        if self.auth_token:
            cmd_parts.extend(["pxctl", "--auth-token", self.auth_token])
        else:
            cmd_parts.append("pxctl")
        
        # Add the actual command
        cmd_parts.extend(pxctl_command.split())
        
        # Execute with timeout
        rc, stdout, stderr = self.module.run_command(
            cmd_parts, check_rc=False, timeout=self.timeout
        )
        
        return rc, stdout, stderr
    
    def parse_status_output(self, output: str) -> Dict[str, Any]:
        """Parse pxctl status output into structured data."""
        parsed = {
            "cluster_id": None,
            "cluster_uuid": None,
            "status": None,
            "nodes": [],
        }
        
        # Parse cluster ID
        cluster_id_match = re.search(r"Cluster\s+ID:\s+(\S+)", output)
        if cluster_id_match:
            parsed["cluster_id"] = cluster_id_match.group(1)
        
        # Parse cluster UUID
        uuid_match = re.search(
            r"Cluster\s+UUID:\s+([0-9a-f-]{36})", output, re.IGNORECASE
        )
        if uuid_match:
            parsed["cluster_uuid"] = uuid_match.group(1)
        
        # Parse status
        status_match = re.search(r"Status:\s+(\w+)", output)
        if status_match:
            parsed["status"] = status_match.group(1)
        
        # Parse node information (simplified)
        node_pattern = r"(\S+)\s+(\S+)\s+(\d+\.\d+\.\d+\.\d+)"
        for match in re.finditer(node_pattern, output):
            parsed["nodes"].append(
                {
                    "id": match.group(1),
                    "status": match.group(2),
                    "ip": match.group(3),
                }
            )
        
        return parsed
    
    def execute(self) -> Dict[str, Any]:
        """Main execution method."""
        # Find pod if not specified
        pod_name = self.pod_name or self.find_portworx_pod()
        
        # Get auth token
        self.auth_token = self.get_auth_token(pod_name)
        
        # Execute pxctl command
        rc, stdout, stderr = self.execute_pxctl(pod_name, self.command)
        
        if rc != 0:
            self.module.fail_json(
                msg=f"pxctl command failed: {self.command}",
                rc=rc,
                stdout=stdout,
                stderr=stderr,
                pod_name=pod_name,
            )
        
        # Parse output if it's a status command
        parsed_data = None
        if "status" in self.command.lower():
            try:
                parsed_data = self.parse_status_output(stdout)
            except Exception as e:
                # Parsing failed, but we still have raw output
                pass
        
        result = {
            "changed": False,  # Read-only operation
            "output": stdout,
            "pod_name": pod_name,
            "command": self.command,
        }
        
        if parsed_data:
            result["parsed_data"] = parsed_data
            if parsed_data.get("status"):
                result["status"] = parsed_data["status"]
            if parsed_data.get("nodes"):
                result["nodes"] = parsed_data["nodes"]
        
        return result


def run_module():
    """Main module entry point."""
    module_args = dict(
        namespace=dict(type="str", required=True),
        pod_name=dict(type="str", required=False),
        command=dict(type="str", default="status"),
        timeout=dict(type="int", default=30),
    )
    
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    
    if module.check_mode:
        module.exit_json(
            changed=False, msg="Check mode: no commands executed"
        )
    
    runner = PxctlStatusRunner(module)
    result = runner.execute()
    
    module.exit_json(**result)


def main():
    """Module execution wrapper."""
    run_module()


if __name__ == "__main__":
    main()
```

**Usage in playbooks:**

```yaml
---
- name: Use pxctl_status custom module
  hosts: localhost
  tasks:
    - name: Get Portworx cluster status
      pxctl_status:
        namespace: kube-system
      register: px_status
    
    - name: Display cluster status
      ansible.builtin.debug:
        msg: |
          Cluster Status: {{ px_status.status }}
          Cluster ID: {{ px_status.parsed_data.cluster_id }}
          Nodes: {{ px_status.nodes | length }}
    
    - name: Verify cluster is operational
      ansible.builtin.assert:
        that:
          - px_status.status == "Operational"
        fail_msg: "Cluster is not operational"
```

---

## Testing Strategies

### Comprehensive Testing Workflow

**Phase 1: Syntax Validation**

```bash
#!/bin/bash
# test_syntax.sh

echo "=== Syntax Validation ==="

# Test all playbooks
for playbook in playbooks/*.yml; do
    echo "Checking $playbook..."
    ansible-playbook --syntax-check "$playbook" || exit 1
done

# Test role task files
for role in roles/*/; do
    role_name=$(basename "$role")
    echo "Checking role: $role_name..."
    
    # Create temporary playbook to test role
    cat > /tmp/test_${role_name}.yml <<EOF
---
- name: Test role $role_name
  hosts: localhost
  roles:
    - $role_name
EOF
    
    ansible-playbook --syntax-check /tmp/test_${role_name}.yml || exit 1
    rm /tmp/test_${role_name}.yml
done

echo "✓ All syntax checks passed"
```

**Phase 2: Linting**

```bash
#!/bin/bash
# test_lint.sh

echo "=== Linting ==="

# Ansible lint with production profile
echo "Running ansible-lint..."
.venv/bin/ansible-lint --profile=production roles/ playbooks/ || exit 1

# YAML lint
echo "Running yamllint..."
.venv/bin/yamllint -c .yamllint . || exit 1

# Python quality (if custom modules exist)
if ls roles/*/library/*.py 2>/dev/null | head -1 >/dev/null; then
    echo "Running Python quality checks..."
    .venv/bin/black --check roles/*/library/ roles/*/filter_plugins/ || exit 1
    .venv/bin/isort --check roles/*/library/ roles/*/filter_plugins/ || exit 1
    .venv/bin/flake8 --max-line-length=88 roles/*/library/ roles/*/filter_plugins/ || exit 1
fi

echo "✓ All linting checks passed"
```

**Phase 3: Check Mode Testing**

```bash
#!/bin/bash
# test_check_mode.sh

echo "=== Check Mode Testing ==="

for playbook in playbooks/*.yml; do
    echo "Testing $playbook in check mode..."
    ansible-playbook -i inventory/test "$playbook" --check || exit 1
done

echo "✓ All check mode tests passed"
```

**Phase 4: Integration Testing**

```yaml
---
# tests/integration/test_role.yml
# Integration test for role

- name: Integration test for my_role
  hosts: test_cluster
  gather_facts: true
  
  vars:
    test_namespace: "ansible-test-{{ ansible_date_time.epoch }}"
    cleanup_on_failure: true
  
  pre_tasks:
    - name: Create test namespace
      kubernetes.core.k8s:
        api_version: v1
        kind: Namespace
        name: "{{ test_namespace }}"
        state: present
      register: namespace_creation
    
    - name: Verify test namespace exists
      ansible.builtin.assert:
        that:
          - namespace_creation is succeeded
        fail_msg: "Failed to create test namespace"
  
  tasks:
    - name: Execute role with test configuration
      block:
        - name: Run role
          ansible.builtin.include_role:
            name: my_role
          vars:
            my_role_namespace: "{{ test_namespace }}"
            my_role_debug_mode: true
        
        - name: Verify role execution
          ansible.builtin.assert:
            that:
              - my_role_execution_status == "success"
            fail_msg: "Role execution failed"
        
        - name: Test idempotency - run role again
          ansible.builtin.include_role:
            name: my_role
          vars:
            my_role_namespace: "{{ test_namespace }}"
        
        - name: Verify idempotency
          ansible.builtin.assert:
            that:
              - my_role_execution_status == "success"
            fail_msg: "Role is not idempotent"
      
      rescue:
        - name: Cleanup on failure
          kubernetes.core.k8s:
            api_version: v1
            kind: Namespace
            name: "{{ test_namespace }}"
            state: absent
          when: cleanup_on_failure
        
        - name: Fail test
          ansible.builtin.fail:
            msg: "Integration test failed"
      
      always:
        - name: Cleanup test namespace
          kubernetes.core.k8s:
            api_version: v1
            kind: Namespace
            name: "{{ test_namespace }}"
            state: absent
          when: cleanup_on_failure or test_passed
```

---

## Conclusion

This comprehensive guide provides the detailed examples and patterns needed to write production-grade Ansible automation. Key takeaways:

1. **Think declaratively** - Describe desired state, not steps
2. **Use native modules** - Avoid shell commands whenever possible
3. **Handle errors properly** - Use block/rescue/always patterns
4. **Monitor operations** - Implement proper timeouts and progress tracking
5. **Test thoroughly** - Multiple phases from syntax to integration
6. **Document completely** - Code should be self-explanatory

For quick reference, use the [Ansible Development Standards](../../ANSIBLE-DEVELOPMENT-STANDARDS.md) document.

For specific topics:
- **Shell script migration** - See [Migration Guide](MIGRATION-GUIDE.md)
- **Kubernetes patterns** - See [Kubernetes Patterns](KUBERNETES-PATTERNS.md)
- **Code review** - See [Code Review Checklist](CODE-REVIEW-CHECKLIST.md)

---

**Document Version:** 1.0.0  
**Last Updated:** 2025-02-10  
**Maintained By:** Platform Engineering Team

