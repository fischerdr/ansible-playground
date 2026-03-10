# Ansible Development Standards

**Document Version:** 1.0.0  
**Last Updated:** 2025-02-10  
**Target Audience:** Mid-level engineers developing enterprise Ansible automation  
**Purpose:** Core standards for production-grade Ansible roles, playbooks, and custom modules

---

## Table of Contents

1. [Introduction](#introduction)
2. [Core Principles](#core-principles)
3. [Development Environment](#development-environment)
4. [Role Development Standards](#role-development-standards)
5. [Playbook Design Standards](#playbook-design-standards)
6. [Task Writing Standards](#task-writing-standards)
7. [Custom Module Development](#custom-module-development)
8. [Kubernetes/OpenShift Patterns](#kubernetesopenshift-patterns)
9. [Error Handling Patterns](#error-handling-patterns)
10. [Variable Management](#variable-management)
11. [Testing Standards](#testing-standards)
12. [Documentation Requirements](#documentation-requirements)
13. [Quality Assurance](#quality-assurance)
14. [AAP Integration Guidelines](#aap-integration-guidelines)
15. [Quick Reference](#quick-reference)

---

## Introduction

### Purpose of This Document

This document establishes the standards and best practices for developing Ansible automation within our organization. These standards ensure:

- **Consistency** across all automation code
- **Reliability** in production environments
- **Maintainability** by current and future team members
- **Scalability** from single-host to multi-cluster operations
- **Safety** through proper error handling and validation

### Document Scope

**This document covers:**

- Ansible role development
- Playbook design patterns
- Custom module creation
- Kubernetes/OpenShift automation patterns
- Quality assurance processes

**This document does NOT cover:**

- Basic Ansible syntax (assumed knowledge)
- Inventory management (separate document)
- AAP administration (separate document)

### How to Use This Document

**Standards Level Indicators:**

- **MUST** / **REQUIRED** / **MANDATORY** - No exceptions, enforced by tooling
- **SHOULD** / **RECOMMENDED** - Follow unless you have documented justification
- **MAY** / **OPTIONAL** - Use at your discretion

**Document Navigation:**

- Use this document as a **reference** - not meant to be read cover-to-cover
- Search for specific topics when needed
- Refer to the [Comprehensive Guide](docs/ansible/COMPREHENSIVE-GUIDE.md) for detailed examples
- Use the [Quick Reference](#quick-reference) for common patterns

### Relationship to Other Documents

- **COMPREHENSIVE-GUIDE.md** - Detailed examples and deep dives
- **MIGRATION-GUIDE.md** - How to refactor existing playbooks
- **CODE-REVIEW-CHECKLIST.md** - PR review requirements
- **KUBERNETES-PATTERNS.md** - K8s/OpenShift specific patterns
- **AGENTS.md** - AI agent coding standards
- **CLAUDE.md** - Claude Code specific instructions

---

## Core Principles

### The Ansible Way vs Shell Scripting

**CRITICAL MINDSET SHIFT**: Ansible is **declarative**, not **imperative**. Stop thinking in terms of "run these commands in sequence" and start thinking in terms of "ensure this state exists."

**Wrong Way (Shell Script Thinking):**

```yaml
- name: Check if file exists
  shell: test -f /etc/config.conf
  register: file_check
  
- name: Create file if missing
  shell: touch /etc/config.conf
  when: file_check.rc != 0
```

**Right Way (Ansible Thinking):**

```yaml
- name: Ensure configuration file exists
  ansible.builtin.file:
    path: /etc/config.conf
    state: touch
    mode: '0644'
```

**Key Differences:**

| Shell Script Thinking | Ansible Thinking |
|----------------------|------------------|
| Execute commands sequentially | Declare desired state |
| Check before acting | Let modules handle checks |
| Manual error handling | Built-in idempotency |
| Text parsing and grep | Structured data handling |
| Exit codes | Module return values |

### Enterprise-Grade Automation Principles

**1. Idempotency First**

- Running the same playbook multiple times produces the same result
- No side effects from repeated execution
- Use `changed_when` and `failed_when` appropriately

**2. Safety Through Validation**

- Validate inputs before execution
- Check prerequisites (preflight checks)
- Verify results after execution
- Fail fast with clear error messages

**3. Observable Operations**

- Log important operations
- Provide progress indicators
- Report results clearly
- Enable debugging without code changes

**4. Defensive Programming**

- Expect failures and handle them gracefully
- Use timeouts for all external operations
- Implement retries for transient failures
- Clean up resources in all exit paths

**5. Maintainability**

- Code should be self-documenting
- Use meaningful names (tasks, variables, roles)
- Modular design (small, focused task files)
- Comprehensive comments for complex logic

### Quality Over Speed

**We prioritize:**

- Correctness over quick implementation
- Maintainability over cleverness
- Clarity over brevity
- Reliability over features

**This means:**

- Take time to write proper error handling
- Don't skip validation steps to save time
- Write tests even for "simple" roles
- Document as you develop, not after

---

## Development Environment

### Required Tools

**MUST install and configure:**

```bash
# Python virtual environment (REQUIRED)
python3.11 -m venv .venv
source .venv/bin/activate  # Always activate before work

# Ansible and tools
pip install ansible-core>=2.18
pip install ansible-lint>=24.0
pip install yamllint

# Python quality tools
pip install black>=24.0
pip install isort>=5.0
pip install flake8>=7.0
pip install mypy>=1.0

# Markdown linting
pip install pymarkdownlnt
```

### Virtual Environment Usage

**CRITICAL**: ALL Ansible and Python commands MUST use the virtual environment.

```bash
# Correct - using venv
.venv/bin/ansible-playbook playbook.yml
.venv/bin/ansible-lint roles/

# Wrong - using system Python
ansible-playbook playbook.yml  # DON'T DO THIS
```

**Why this matters:**

- Consistent versions across team
- Isolated from system packages
- Reproducible in CI/CD and AAP Execution Environments

### Pre-commit Hooks

**SHOULD configure** pre-commit hooks to catch issues before commit:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/ansible/ansible-lint
    rev: v24.2.0
    hooks:
      - id: ansible-lint
        args: ["--profile=production"]
        
  - repo: https://github.com/psf/black
    rev: 24.1.0
    hooks:
      - id: black
        language_version: python3.11
        
  - repo: https://github.com/PyCQA/isort
    rev: 5.13.0
    hooks:
      - id: isort
        
  - repo: https://github.com/adrienverge/yamllint
    rev: v1.33.0
    hooks:
      - id: yamllint
        args: ["-c", ".yamllint"]
```

Install hooks:

```bash
pip install pre-commit
pre-commit install
```

### Editor Configuration

**RECOMMENDED** editor settings (VSCode example):

```json
{
  "ansible.python.interpreterPath": "${workspaceFolder}/.venv/bin/python",
  "ansible.validation.enabled": true,
  "ansible.validation.lint.enabled": true,
  "ansible.validation.lint.path": "${workspaceFolder}/.venv/bin/ansible-lint",
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "[yaml]": {
    "editor.formatOnSave": true,
    "editor.tabSize": 2
  },
  "[python]": {
    "editor.formatOnSave": true,
    "editor.tabSize": 4
  }
}
```

### Quality Check Workflow

**MUST run** before every commit:

```bash
# 1. Ansible linting
.venv/bin/ansible-lint roles/<role_name>/

# 2. YAML linting
.venv/bin/yamllint roles/<role_name>/

# 3. Syntax check
.venv/bin/ansible-playbook --syntax-check playbooks/*.yml

# 4. Python quality (if custom modules/filters)
.venv/bin/black roles/<role_name>/library/
.venv/bin/isort roles/<role_name>/library/
.venv/bin/flake8 roles/<role_name>/library/
.venv/bin/mypy roles/<role_name>/library/

# 5. Markdown linting (if documentation changes)
pymarkdownlnt -d MD013 scan docs/
```

---

## Role Development Standards

### Role Structure

**REQUIRED** directory structure for all roles:

```text
<role_name>/
├── README.md                      # Role documentation (REQUIRED)
├── CHANGELOG.md                   # Version history (REQUIRED)
├── LICENSE                        # License file (REQUIRED)
├── requirements.yml               # Collection dependencies (if needed)
├── requirements.txt               # Python dependencies (if custom modules)
├── .ansible-lint                  # Role-specific lint config (OPTIONAL)
├── defaults/
│   └── main.yml                  # Default variables (REQUIRED)
├── vars/
│   └── main.yml                  # Internal constants (OPTIONAL)
├── meta/
│   └── main.yml                  # Role metadata (REQUIRED)
├── tasks/
│   ├── main.yml                  # Orchestrator (REQUIRED)
│   ├── preflight.yml             # Pre-flight checks (RECOMMENDED)
│   ├── validate.yml              # Input validation (RECOMMENDED)
│   ├── prepare.yml               # Preparation steps (OPTIONAL)
│   ├── execute.yml               # Main execution (OPTIONAL)
│   ├── verify.yml                # Post-execution checks (RECOMMENDED)
│   ├── cleanup.yml               # Cleanup operations (OPTIONAL)
│   └── report.yml                # Result reporting (OPTIONAL)
├── handlers/
│   └── main.yml                  # Event handlers (OPTIONAL)
├── templates/                     # Jinja2 templates (OPTIONAL)
├── files/                        # Static files (OPTIONAL)
├── library/                      # Custom modules (OPTIONAL)
│   ├── <module_name>.py
│   └── README.md
└── filter_plugins/               # Custom filters (OPTIONAL)
    ├── <filter_name>.py
    └── README.md
```

### Orchestrator Pattern (tasks/main.yml)

**MUST** use orchestrator pattern for `tasks/main.yml`:

```yaml
---
# Role: <role_name>
# Purpose: Brief description of what this role does
# Author: Your Name
# Last Updated: YYYY-MM-DD

# Phase 1: Preflight Checks
- name: "Phase 1: Preflight Checks"
  ansible.builtin.import_tasks: preflight.yml
  tags:
    - always
    - preflight
    - <role_name>

# Phase 2: Input Validation
- name: "Phase 2: Input Validation"
  ansible.builtin.import_tasks: validate.yml
  tags:
    - always
    - validation
    - <role_name>

# Phase 3: Preparation
- name: "Phase 3: Preparation"
  ansible.builtin.import_tasks: prepare.yml
  tags:
    - preparation
    - <role_name>
  when: <role_name>_skip_preparation | default(false) | bool == false

# Phase 4: Execution
- name: "Phase 4: Execution"
  ansible.builtin.import_tasks: execute.yml
  tags:
    - execution
    - <role_name>

# Phase 5: Verification
- name: "Phase 5: Verification"
  ansible.builtin.import_tasks: verify.yml
  tags:
    - verification
    - <role_name>
  when: <role_name>_skip_verification | default(false) | bool == false

# Phase 6: Reporting
- name: "Phase 6: Reporting"
  ansible.builtin.import_tasks: report.yml
  tags:
    - reporting
    - <role_name>
  when: <role_name>_enable_reporting | default(true) | bool
```

**Key principles:**

- **Keep main.yml under 100 lines** - it should only orchestrate
- **Use import_tasks** for static includes, **include_tasks** for dynamic
- **Every phase is optional** except main execution
- **Use tags consistently** for selective execution
- **Document each phase** with clear comments

### Task File Organization

**SHOULD** organize task files by workflow phase:

**preflight.yml** - Environment and prerequisite checks:

```yaml
---
# Preflight checks: Verify environment is ready for role execution

- name: Check Ansible version
  ansible.builtin.assert:
    that:
      - ansible_version.full is version('2.12.0', '>=')
    fail_msg: "Ansible 2.12.0 or higher required"
    quiet: true
  tags: [version-check]

- name: Verify required commands are available
  ansible.builtin.command:
    cmd: which {{ item }}
  loop:
    - kubectl
    - oc
  changed_when: false
  failed_when: false
  register: command_check
  tags: [prerequisites]

- name: Fail if required commands missing
  ansible.builtin.fail:
    msg: "Required command '{{ item.item }}' not found in PATH"
  loop: "{{ command_check.results }}"
  when: item.rc != 0
  tags: [prerequisites]
```

**validate.yml** - Input validation:

```yaml
---
# Input validation: Ensure all required variables are defined and valid

- name: Validate required variables are defined
  ansible.builtin.assert:
    that:
      - <role_name>_namespace is defined
      - <role_name>_namespace | length > 0
      - <role_name>_resource_name is defined
      - <role_name>_resource_name | length > 0
    fail_msg: "Required variable is missing or empty"
    quiet: false
  tags: [validation]

- name: Validate variable types
  ansible.builtin.assert:
    that:
      - <role_name>_timeout is number
      - <role_name>_timeout > 0
      - <role_name>_retry_count is number
      - <role_name>_retry_count >= 0
    fail_msg: "Variable has invalid type or value"
  tags: [validation]
```

### Naming Conventions

**MUST** follow these naming conventions:

**Role Names:**

- Use snake_case: `portworx_upgrade`, `must_gather_log`
- Be descriptive: Name should indicate purpose
- Avoid abbreviations unless widely known

**Variable Names:**

- Prefix with role name: `<role_name>_variable_name`
- Use snake_case: `portworx_upgrade_timeout`
- Be descriptive: `portworx_upgrade_global_timeout` not `px_to`
- Boolean variables should be questions: `enable_debug` not `debug_flag`

**Task Names:**

- Use action verbs: "Create", "Validate", "Check", "Update"
- Be specific: "Validate cluster connectivity" not "Check"
- Indicate what, not how: "Ensure pod is running" not "kubectl get pod"
- Use sentence case: "Check cluster status" not "check cluster status"

**Tag Names:**

- Use lowercase with hyphens: `pre-flight`, `post-check`
- Be consistent across roles
- Include role name tag: `portworx-upgrade`
- Use standard tags: `always`, `never`, `preparation`, `validation`, `execution`, `verification`, `reporting`

### Variable Management

**defaults/main.yml** - User-configurable variables:

```yaml
---
# <role_name> default variables
# These can be overridden by users

# General settings
<role_name>_namespace: "default"
<role_name>_timeout: 300  # seconds
<role_name>_retry_count: 30
<role_name>_retry_delay: 10  # seconds

# Feature flags
<role_name>_enable_validation: true
<role_name>_enable_verification: true
<role_name>_enable_reporting: true
<role_name>_debug_mode: false

# Operational settings
<role_name>_max_concurrent: 5
<role_name>_failure_threshold: 3
<role_name>_wait_for_ready: true

# Reporting settings
<role_name>_report_format: "json"  # json, yaml, text
<role_name>_report_destination: "/tmp/<role_name>-report.json"
```

**vars/main.yml** - Internal constants (users should not change):

```yaml
---
# <role_name> internal variables
# DO NOT override these in playbooks

# Internal constants
__<role_name>_version: "1.0.0"
__<role_name>_supported_k8s_versions:
  - "1.26"
  - "1.27"
  - "1.28"

# Internal state variables
__<role_name>_temp_dir: "/tmp/ansible-<role_name>-{{ ansible_date_time.epoch }}"
__<role_name>_log_file: "{{ __<role_name>_temp_dir }}/execution.log"
```

**meta/main.yml** - Role metadata:

```yaml
---
galaxy_info:
  role_name: <role_name>
  namespace: your_namespace
  author: Your Name
  description: Brief description of role purpose
  company: Your Company
  license: Apache-2.0
  
  min_ansible_version: "2.12"
  
  platforms:
    - name: EL
      versions:
        - "8"
        - "9"
  
  galaxy_tags:
    - kubernetes
    - openshift
    - automation
    - infrastructure

dependencies: []
```

---

## Playbook Design Standards

### Playbook Structure

**MUST** follow this structure for all playbooks:

```yaml
---
# Playbook: <playbook_name>.yml
# Purpose: Brief description of what this playbook does
# Author: Your Name
# Last Updated: YYYY-MM-DD
#
# Usage:
#   ansible-playbook -i inventory playbook.yml
#   ansible-playbook -i inventory playbook.yml --tags preflight
#   ansible-playbook -i inventory playbook.yml --check

- name: Descriptive playbook name
  hosts: target_hosts
  gather_facts: true  # or false with justification
  become: false  # or true with justification
  
  # Variables specific to this playbook
  vars:
    playbook_variable: "value"
  
  # Files containing additional variables
  vars_files:
    - vars/common.yml
    - vars/environment.yml
  
  # Pre-execution tasks
  pre_tasks:
    - name: Display playbook information
      ansible.builtin.debug:
        msg: |
          Playbook: {{ ansible_play_name }}
          Target: {{ inventory_hostname }}
          User: {{ ansible_user_id }}
          Started: {{ ansible_date_time.iso8601 }}
      tags: [always]
    
    - name: Validate prerequisites
      ansible.builtin.assert:
        that:
          - ansible_version.full is version('2.12.0', '>=')
          - required_variable is defined
        fail_msg: "Prerequisites not met"
      tags: [always]
  
  # Role execution
  roles:
    - role: <role_name>
      vars:
        <role_name>_variable: "value"
      tags: [<role_name>]
  
  # Post-execution tasks
  post_tasks:
    - name: Display execution summary
      ansible.builtin.debug:
        msg: |
          Execution Status: {{ <role_name>_execution_status }}
          Duration: {{ execution_duration }}s
          Completed: {{ ansible_date_time.iso8601 }}
      tags: [always]
```

### Common Playbook Anti-Patterns to Avoid

**❌ Anti-Pattern 1: Playbook as a Shell Script**

```yaml
# DON'T DO THIS
- name: Bad playbook
  hosts: localhost
  tasks:
    - shell: oc get pods -n openshift-storage
    - shell: oc get pv | grep -i portworx
    - shell: oc describe storagecluster
```

**✅ Correct Approach:**

```yaml
# DO THIS
- name: Good playbook
  hosts: localhost
  tasks:
    - name: Get pods in storage namespace
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Pod
        namespace: openshift-storage
      register: storage_pods
    
    - name: Get Portworx persistent volumes
      kubernetes.core.k8s_info:
        api_version: v1
        kind: PersistentVolume
        label_selectors:
          - "pv.kubernetes.io/provisioned-by=portworx"
      register: portworx_pvs
```

**❌ Anti-Pattern 2: No Error Handling**

```yaml
# DON'T DO THIS
- name: Bad playbook
  hosts: localhost
  tasks:
    - name: Update resource
      kubernetes.core.k8s:
        definition: "{{ resource_def }}"
    
    - name: Wait for ready
      shell: sleep 30
```

**✅ Correct Approach:**

```yaml
# DO THIS
- name: Good playbook
  hosts: localhost
  tasks:
    - name: Update resource with error handling
      block:
        - name: Update resource
          kubernetes.core.k8s:
            definition: "{{ resource_def }}"
            wait: true
            wait_timeout: 300
          register: update_result
        
        - name: Wait for pod to be ready
          kubernetes.core.k8s_info:
            api_version: v1
            kind: Pod
            namespace: "{{ namespace }}"
            name: "{{ pod_name }}"
          register: pod_status
          until:
            - pod_status.resources | length > 0
            - pod_status.resources[0].status.phase == 'Running'
          retries: 30
          delay: 10
      
      rescue:
        - name: Handle failure
          ansible.builtin.debug:
            msg: "Operation failed: {{ ansible_failed_result.msg }}"
        
        - name: Fail with clear message
          ansible.builtin.fail:
            msg: "Resource update failed"
```

---

## Task Writing Standards

### Mandatory Task Elements

**MUST** include these elements in every task:

1. **Meaningful name**: Describes what the task does
2. **FQCN**: Fully Qualified Collection Name for all modules
3. **Tags**: At least role name and phase tags
4. **changed_when/failed_when**: For shell/command tasks
5. **Error handling**: For operations that can fail

### FQCN Usage

**MUST** use Fully Qualified Collection Names:

```yaml
# Correct
- name: Create directory
  ansible.builtin.file:
    path: /tmp/work
    state: directory

- name: Get pod information
  kubernetes.core.k8s_info:
    kind: Pod
    namespace: default

# Wrong
- name: Create directory
  file:  # Missing FQCN
    path: /tmp/work
    state: directory
```

### Idempotency with changed_when and failed_when

**MUST** define `changed_when` and `failed_when` for shell/command tasks:

**Read-only operations** - Never report as changed:

```yaml
- name: Get list of storage nodes
  ansible.builtin.shell: |
    set -o pipefail &&
    oc get nodes -l node-role.kubernetes.io/storage='' --no-headers
  args:
    executable: /bin/bash
  register: storage_nodes
  changed_when: false  # Read-only operation
  failed_when: storage_nodes.rc != 0
```

**Operations with grep** - Allow no-match exit code:

```yaml
- name: Check for running pods
  ansible.builtin.shell: |
    set -o pipefail &&
    oc get pods -n {{ namespace }} | grep Running
  args:
    executable: /bin/bash
  register: running_pods
  changed_when: false
  failed_when: running_pods.rc not in [0, 1]  # 1 = no matches, OK
```

**State-modifying operations** - Detect actual changes:

```yaml
- name: Apply configuration
  ansible.builtin.shell: |
    oc apply -f /tmp/config.yaml
  register: apply_result
  changed_when: "'configured' in apply_result.stdout or 'created' in apply_result.stdout"
  failed_when: apply_result.rc != 0
```

### Loop Constructs

**Use `loop` with list** (preferred):

```yaml
- name: Create multiple directories
  ansible.builtin.file:
    path: "{{ item }}"
    state: directory
    mode: '0755'
  loop:
    - /tmp/dir1
    - /tmp/dir2
    - /tmp/dir3
```

**Use `loop` with complex data**:

```yaml
- name: Create users with specific settings
  ansible.builtin.user:
    name: "{{ item.name }}"
    uid: "{{ item.uid }}"
    groups: "{{ item.groups }}"
  loop:
    - name: alice
      uid: 1001
      groups: [admin, developers]
    - name: bob
      uid: 1002
      groups: [developers]
  loop_control:
    label: "{{ item.name }}"  # Cleaner output
```

### Retries and Timeouts

**SHOULD** implement retries for operations that may fail transiently:

```yaml
- name: Wait for API endpoint to be available
  ansible.builtin.uri:
    url: "{{ api_endpoint }}/health"
    method: GET
    status_code: 200
    timeout: 10
  register: health_check
  retries: 30
  delay: 10
  until: health_check.status == 200

- name: Wait for pod to be ready
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: "{{ namespace }}"
    name: "{{ pod_name }}"
  register: pod_status
  retries: 60
  delay: 5
  until:
    - pod_status.resources | length > 0
    - pod_status.resources[0].status.phase == 'Running'
```

---

## Custom Module Development

### When to Create Custom Modules

**SHOULD** create custom modules when:

1. **Repeated complex shell commands**: Same multi-line shell script used in multiple roles
2. **External tool interaction**: Need to parse output from tools like `pxctl`, `etcdctl`
3. **Custom logic**: Behavior not available in existing modules
4. **Idempotency**: Need proper change detection for external state
5. **Error handling**: Need structured error handling for specific operations

**SHOULD NOT** create custom modules when:

1. Existing module can do the job
2. Simple shell command is sufficient
3. Operation is one-time use

### Module Structure Template

**MUST** follow this structure for all custom modules:

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Your Name <your.email@company.com>
# Apache License 2.0

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: module_name
short_description: Brief one-line description
description:
  - Detailed description of what the module does
version_added: "1.0.0"
author:
  - Your Name (@github_username)
options:
  parameter_name:
    description:
      - Description of this parameter
    type: str
    required: true
requirements:
  - python >= 3.11
"""

EXAMPLES = r"""
# Basic usage
- name: Basic example
  module_name:
    parameter_name: value
"""

RETURN = r"""
changed:
  description: Whether the module made changes
  type: bool
  returned: always
message:
  description: Human-readable message
  type: str
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule


def run_module():
    module_args = dict(
        parameter_name=dict(type="str", required=True),
    )
    
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    
    if module.check_mode:
        module.exit_json(changed=False)
    
    # Module logic here
    result = dict(
        changed=False,
        message="Operation completed"
    )
    
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
```

---

## Kubernetes/OpenShift Patterns

### Stop Using `oc` Commands

**CRITICAL**: Stop using `shell: oc command` for everything. Use native Kubernetes modules.

### Common oc Command Translations

**Pattern 1: Getting Resources**

❌ **Wrong**:

```yaml
- name: Get pods
  shell: oc get pods -n openshift-storage --no-headers
  register: pods
```

✅ **Correct**:

```yaml
- name: Get pods in storage namespace
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: openshift-storage
  register: pods
```

**Pattern 2: Updating Resources**

❌ **Wrong**:

```yaml
- name: Patch deployment
  shell: |
    oc patch deployment {{ deploy_name }} -n {{ namespace }} \
      --patch '{"spec":{"replicas":{{ replica_count }}}}'
```

✅ **Correct**:

```yaml
- name: Scale deployment
  kubernetes.core.k8s:
    api_version: apps/v1
    kind: Deployment
    name: "{{ deploy_name }}"
    namespace: "{{ namespace }}"
    definition:
      spec:
        replicas: "{{ replica_count }}"
```

**Pattern 3: Executing Commands in Pods**

❌ **Wrong**:

```yaml
- name: Run command in pod
  shell: oc rsh -n {{ namespace }} {{ pod_name }} /bin/bash -c "{{ command }}"
  register: pod_output
```

✅ **Correct**:

```yaml
- name: Execute command in pod
  kubernetes.core.k8s_exec:
    namespace: "{{ namespace }}"
    pod: "{{ pod_name }}"
    command: "{{ command }}"
  register: pod_output
```

### Working with Custom Resource Definitions (CRDs)

```yaml
- name: Get StorageCluster resource
  kubernetes.core.k8s_info:
    api_version: core.libopenstorage.org/v1
    kind: StorageCluster
    namespace: kube-system
    name: px-cluster
  register: storage_cluster

- name: Update StorageCluster image
  kubernetes.core.k8s:
    api_version: core.libopenstorage.org/v1
    kind: StorageCluster
    name: px-cluster
    namespace: kube-system
    definition:
      spec:
        image: "portworx/oci-monitor:{{ new_version }}"
```

### Pod Lifecycle Monitoring

```yaml
- name: Wait for pod to be running
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: "{{ namespace }}"
    name: "{{ pod_name }}"
  register: pod_status
  until:
    - pod_status.resources | length > 0
    - pod_status.resources[0].status.phase == 'Running'
    - pod_status.resources[0].status.conditions | selectattr('type', 'equalto', 'Ready') | selectattr('status', 'equalto', 'True') | list | length > 0
  retries: 60
  delay: 10
```

### Multi-Cluster Patterns

```yaml
---
# Sequential cluster operations

- name: Multi-cluster operation
  hosts: k8s_clusters
  gather_facts: false
  serial: 1  # One cluster at a time
  
  tasks:
    - name: Execute operation on cluster
      ansible.builtin.include_role:
        name: cluster_operation
      vars:
        cluster_name: "{{ inventory_hostname }}"
```

---

## Error Handling Patterns

### Block/Rescue/Always Structure

**MUST** use block/rescue/always for error handling:

```yaml
- name: Operation with comprehensive error handling
  block:
    # Try block - main operation
    - name: Execute primary operation
      kubernetes.core.k8s:
        definition: "{{ resource_definition }}"
      register: operation_result
    
    - name: Record success
      ansible.builtin.set_fact:
        operation_status: "success"
  
  rescue:
    # Rescue block - error handling
    - name: Log error details
      ansible.builtin.debug:
        msg: "Operation failed: {{ ansible_failed_result.msg }}"
    
    - name: Record failure
      ansible.builtin.set_fact:
        operation_status: "failed"
    
    - name: Fail with clear message
      ansible.builtin.fail:
        msg: "Operation failed: {{ ansible_failed_result.msg }}"
  
  always:
    # Always block - cleanup (ALWAYS runs)
    - name: Remove temporary files
      ansible.builtin.file:
        path: "{{ temp_dir }}"
        state: absent
      when: temp_dir is defined
```

### Timeout Handling

```yaml
- name: Operation with dual timeout mechanism
  vars:
    global_timeout: 2100  # 35 minutes
    inactivity_timeout: 2100
    start_time: "{{ ansible_date_time.epoch }}"
  
  block:
    - name: Monitor operation with timeouts
      block:
        - name: Check resource status
          kubernetes.core.k8s_info:
            api_version: v1
            kind: Pod
            namespace: "{{ namespace }}"
          register: resource_status
        
        - name: Check global timeout
          ansible.builtin.fail:
            msg: "Global timeout exceeded"
          when: (ansible_date_time.epoch | int) - (start_time | int) > global_timeout
      
      until: operation_complete
      retries: "{{ (global_timeout / 10) | int }}"
      delay: 10
```

---

## Variable Management

### Variable Precedence

**Understanding variable precedence** (lowest to highest):

1. role defaults
2. inventory group vars
3. inventory host vars
4. playbook vars
5. role vars
6. task vars
7. extra vars (command line)

**Key Takeaways**:

- `defaults/main.yml` - Lowest precedence, easily overridden
- `vars/main.yml` - High precedence, hard to override
- `extra_vars` - Highest precedence

### Variable Validation

**MUST** validate all required variables:

```yaml
- name: Validate required variables are defined
  ansible.builtin.assert:
    that:
      - <role_name>_namespace is defined
      - <role_name>_resource_name is defined
    fail_msg: "Required variable is not defined"

- name: Validate variable types
  ansible.builtin.assert:
    that:
      - <role_name>_timeout is number
      - <role_name>_timeout > 0
    fail_msg: "Variable has invalid type or value"
```

---

## Testing Standards

### Role Testing Workflow

**MUST** test roles through these phases:

**Phase 1: Syntax Validation**

```bash
ansible-playbook --syntax-check playbooks/test_role.yml
```

**Phase 2: Linting**

```bash
.venv/bin/ansible-lint --profile=production roles/<role_name>/
.venv/bin/yamllint roles/<role_name>/
```

**Phase 3: Check Mode (Dry Run)**

```bash
ansible-playbook -i inventory playbooks/test_role.yml --check
```

**Phase 4: Tag-Based Testing**

```bash
ansible-playbook -i inventory playbooks/test_role.yml --tags preflight
ansible-playbook -i inventory playbooks/test_role.yml --tags validation
```

**Phase 5: Full Execution**

```bash
ansible-playbook -i inventory/test playbooks/test_role.yml -vv
```

### Testing Checklist

**Before committing code:**

- [ ] Syntax check passes
- [ ] Ansible-lint passes
- [ ] YAML lint passes
- [ ] Check mode runs without errors
- [ ] All tags work individually
- [ ] Full playbook runs successfully
- [ ] Error handling tested
- [ ] Documentation updated
- [ ] CHANGELOG updated

---

## Documentation Requirements

### README.md Structure

**MUST** include these sections:

```markdown
# Ansible Role: <role_name>

## Description

Brief description of what this role does.

## Requirements

- Ansible Core: 2.12+
- Python: 3.11+
- Collections:
  - kubernetes.core (>= 2.3.0)

## Role Variables

### Required Variables

| Variable | Type | Description |
|----------|------|-------------|
| `<role_name>_namespace` | string | Kubernetes namespace |

### Optional Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `<role_name>_timeout` | int | 300 | Timeout in seconds |

## Example Playbook

\`\`\`yaml
---
- name: Execute <role_name>
  hosts: localhost
  
  roles:
    - role: <role_name>
      vars:
        <role_name>_namespace: "my-namespace"
\`\`\`

## License

Apache-2.0
```

### CHANGELOG.md Format

```markdown
# Changelog

## [Unreleased]

### Added
- New features

### Changed
- Changes to existing functionality

### Fixed
- Bug fixes

## [1.0.0] - 2025-02-10

### Added
- Initial role implementation
```

---

## Quality Assurance

### Pre-commit Checklist

**MUST complete** before every commit:

- [ ] Code passes ansible-lint
- [ ] Code passes yamllint
- [ ] Syntax check passes
- [ ] Python code formatted (if applicable)
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG updated

### Code Review Requirements

**MUST pass** code review with:

- [ ] Proper FQCN usage
- [ ] Error handling implemented
- [ ] Variables properly scoped
- [ ] Tasks have meaningful names
- [ ] changed_when/failed_when defined
- [ ] Documentation complete

---

## AAP Integration Guidelines

### Execution Environment Considerations

**Key differences from local development:**

- Code runs in containers, not on AAP host
- Dependencies must be in EE build
- No direct filesystem access
- Limited debugging capabilities

### Survey Variables vs Defaults

```yaml
# In role defaults/main.yml
<role_name>_namespace: "default"  # Can be overridden by survey

# In job template survey
- variable: <role_name>_namespace
  question: "Target Namespace"
  type: text
  required: true
```

### Brief AAP Notes

- **Execution Environments** replace direct system access
- **Credentials** injected at runtime
- **Job Templates** define playbook execution parameters
- **Surveys** collect user input before execution

For detailed AAP configuration, see AAP administration documentation.

---

## Quick Reference

### Common Patterns Cheat Sheet

**Get Kubernetes Resource:**

```yaml
- name: Get resource
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: default
  register: result
```

**Update Kubernetes Resource:**

```yaml
- name: Update resource
  kubernetes.core.k8s:
    api_version: apps/v1
    kind: Deployment
    name: my-app
    namespace: default
    definition:
      spec:
        replicas: 3
```

**Execute Command in Pod:**

```yaml
- name: Run command in pod
  kubernetes.core.k8s_exec:
    namespace: default
    pod: my-pod
    command: ls -la
  register: output
```

**Wait for Pod Ready:**

```yaml
- name: Wait for pod
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: default
    name: my-pod
  register: pod
  until:
    - pod.resources[0].status.phase == 'Running'
  retries: 30
  delay: 10
```

**Error Handling Block:**

```yaml
- name: Operation with error handling
  block:
    - name: Main task
      ansible.builtin.command: /path/to/command
  rescue:
    - name: Handle error
      ansible.builtin.debug:
        msg: "Failed"
  always:
    - name: Cleanup
      ansible.builtin.file:
        path: /tmp/file
        state: absent
```

### Command Reference

```bash
# Quality checks
.venv/bin/ansible-lint roles/my_role/
.venv/bin/yamllint roles/my_role/
ansible-playbook --syntax-check playbook.yml

# Testing
ansible-playbook playbook.yml --check
ansible-playbook playbook.yml --tags preflight
ansible-playbook playbook.yml -vv

# Python quality
.venv/bin/black roles/my_role/library/
.venv/bin/flake8 roles/my_role/library/
```

---

## Appendix: Standards Enforcement

### Mandatory Standards (MUST)

These are enforced by tooling and code review:

- Use FQCN for all modules
- Define changed_when/failed_when for shell/command
- Use block/rescue/always for error handling
- Follow role directory structure
- Include required documentation files
- Pass ansible-lint production profile
- Pass syntax checks

### Recommended Standards (SHOULD)

These are best practices but may have justified exceptions:

- Use orchestrator pattern
- Implement preflight checks
- Use tag-based execution
- Create test playbooks
- Use kubernetes.core modules over oc commands

### Optional Standards (MAY)

These are at developer discretion:

- Custom modules for complex operations
- Additional task file organization
- Extended monitoring patterns
- Performance optimizations

---

**Document Maintenance:**

This document should be reviewed quarterly and updated as standards evolve.

**Version History:**

- v1.0.0 (2025-02-10): Initial release

**Contributors:**

Platform Engineering Team

---

**End of Document**
