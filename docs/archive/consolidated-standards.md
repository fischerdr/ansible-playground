# Consolidated Ansible Role Standards

**Purpose:** Single-document consolidation of all Ansible role development standards, conventions, and guidance from the project documentation library.
**Sources:** docs/ANSIBLE-ROLE-STANDARDS.md, docs/ANSIBLE-ROLE-DEVELOPMENT-WORKFLOW.md, docs/ansible-role-development-pattern.md, docs/DEVELOPMENT_STANDARDS.md, docs/CLAUDE-ROLE-WORKFLOW.md, docs/MARKDOWN_STANDARDS.md, docs/Guidelines-vaultandansible-copy.md, docs/SecurityGuidelinesvault.md, docs/VaultSecurityMigrationGuide.md, docs/VERIFICATION_CHECKLIST.md, docs/Ansible_Standards_Documentation/AGENTS.md, docs/Ansible_Standards_Documentation/ANSIBLE-DEVELOPMENT-STANDARDS.md, docs/Ansible_Standards_Documentation/Ansible_Tags_Usage_Guide.md, docs/Ansible_Standards_Documentation/CLAUDE.md, docs/Ansible_Standards_Documentation/CODE-REVIEW-CHECKLIST.md, docs/Ansible_Standards_Documentation/COMPREHENSIVE-GUIDE.md, docs/Ansible_Standards_Documentation/KUBERNETES-PATTERNS.md, docs/Ansible_Standards_Documentation/MIGRATION-GUIDE.md, docs/Ansible_Standards_Documentation/PR-TEMPLATE.md, docs/examples/README.md, docs/examples/changed_when_failed_when_examples.yml, docs/examples/custom_module_example.py, docs/examples/filter_plugin_example.py, docs/examples/module_testing_example.py

---

## Table of Contents

1. [Role Structure](#1-role-structure)
2. [Orchestrator Pattern and Task Organization](#2-orchestrator-pattern-and-task-organization)
3. [Variable Conventions](#3-variable-conventions)
4. [FQCN and Module Selection](#4-fqcn-and-module-selection)
5. [Idempotency: changed_when and failed_when](#5-idempotency-changed_when-and-failed_when)
6. [Error Handling](#6-error-handling)
7. [Tags](#7-tags)
8. [Kubernetes and OpenShift Patterns](#8-kubernetes-and-openshift-patterns)
9. [Custom Module Development](#9-custom-module-development)
10. [Custom Filter Plugins](#10-custom-filter-plugins)
11. [Testing Standards](#11-testing-standards)
12. [Documentation Requirements](#12-documentation-requirements)
13. [Security and Vault Integration](#13-security-and-vault-integration)
14. [Vault Security Migration](#14-vault-security-migration)
15. [Distribution and Tarball Packaging](#15-distribution-and-tarball-packaging)
16. [Code Review and PR Standards](#16-code-review-and-pr-standards)
17. [Development Workflow](#17-development-workflow)
18. [AI Agent Standards](#18-ai-agent-standards)

---

## 1. Role Structure

*`source: ANSIBLE-ROLE-STANDARDS.md` v1.0.0, `source: ANSIBLE-DEVELOPMENT-STANDARDS.md` v1.0.0, `source: ansible-role-development-pattern.md` v1.0.0*

### Complete Role Directory Layout

Every production Ansible role should follow this structure:

```text
<role_name>/
├── README.md                      # Role documentation (REQUIRED)
├── CHANGELOG.md                   # Version history (REQUIRED)
├── LICENSE                        # License file (Apache-2.0 recommended) (REQUIRED)
├── .ansible-lint                  # Role-specific lint config (optional)
├── requirements.yml               # Ansible collection dependencies
├── requirements.txt               # Python dependencies (if needed)
├── defaults/
│   └── main.yml                  # Default variables (user-configurable) (REQUIRED)
├── vars/
│   └── main.yml                  # Internal constants (not user-configurable)
├── meta/
│   └── main.yml                  # Role metadata and dependencies (REQUIRED)
├── tasks/
│   ├── main.yml                  # Main orchestrator (REQUIRED)
│   ├── preflight.yml             # Pre-flight checks (RECOMMENDED)
│   ├── validate.yml              # Input validation (RECOMMENDED)
│   ├── prepare.yml               # Environment preparation
│   ├── execute.yml               # Main execution
│   ├── verify.yml                # Post-execution verification (RECOMMENDED)
│   ├── cleanup.yml               # Cleanup operations
│   └── report.yml                # Result reporting
├── handlers/
│   └── main.yml                  # Event handlers
├── templates/
│   ├── config.j2                 # Configuration templates
│   └── report.j2                 # Report templates
├── files/
│   ├── scripts/                  # Static scripts
│   └── configs/                  # Static configuration files
├── library/                       # Custom Ansible modules
│   ├── <module_name>.py
│   └── README.md                 # Module documentation
├── filter_plugins/                # Custom Jinja2 filters
│   ├── <filter_name>.py
│   └── README.md                 # Filter documentation
├── module_utils/                  # Shared Python utilities (optional)
│   └── <utility_name>.py
└── tests/                         # Role tests (optional)
    ├── test.yml                  # Test playbook
    └── inventory                 # Test inventory
```

### Required Files (Minimum)

Every role MUST have:

1. `defaults/main.yml` — Default variables
2. `meta/main.yml` — Role metadata
3. `tasks/main.yml` — Main entry point
4. `README.md` — Documentation
5. `CHANGELOG.md` — Version history

### Monorepo Development Structure

*`source: ANSIBLE-ROLE-DEVELOPMENT-WORKFLOW.md` v1.0.0, `source: ansible-role-development-pattern.md` v1.0.0*

During development, roles exist within the monorepo at `roles/<role_name>/`:

```text
ansible-playground/                    # Monorepo root
├── roles/
│   └── <role_name>/                  # Role under development
│       ├── README.md
│       ├── CHANGELOG.md
│       ├── defaults/
│       │   └── main.yml
│       ├── vars/
│       │   └── main.yml
│       ├── meta/
│       │   └── main.yml
│       ├── library/
│       │   └── *.py
│       ├── filter_plugins/
│       │   └── *.py
│       ├── tasks/
│       │   ├── main.yml
│       │   └── *.yml
│       ├── templates/
│       ├── files/
│       └── handlers/
│           └── main.yml
├── playbooks/
│   └── <role_playbook>.yml
├── docs/
│   └── <role_name>/
│       ├── architecture.md
│       ├── usage_examples.md
│       └── specification.md
├── .ansible-lint
├── .gitignore
└── requirements.yml
```

### Creating Role Structure

```bash
# Option 1: Using ansible-galaxy
cd ansible-playground
.venv/bin/ansible-galaxy init roles/<role_name>

# Option 2: Manual creation
mkdir -p roles/<role_name>/{defaults,vars,meta,tasks,templates,files,handlers,library,filter_plugins}
touch roles/<role_name>/{defaults,vars,meta,tasks,handlers}/main.yml
```

---

## 2. Orchestrator Pattern and Task Organization

*`source: ANSIBLE-ROLE-STANDARDS.md` v1.0.0, `source: ANSIBLE-DEVELOPMENT-STANDARDS.md` v1.0.0, `source: ansible-role-development-pattern.md` v1.0.0, `source: CLAUDE.md` v2.0.0*

### Orchestrator Pattern — tasks/main.yml

`tasks/main.yml` MUST use the orchestrator pattern — it delegates to specialized task files and contains no logic.

**Standard orchestrator template:**

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

- Keep `main.yml` under 100 lines — it should only orchestrate
- Use `import_tasks` for static includes, `include_tasks` for dynamic
- Every phase is optional except main execution
- Use tags consistently for selective execution
- Document each phase with clear comments

### Modular Task Architecture

**Pattern:** Orchestrator delegates to specialized task files, each with single responsibility.

Benefits:

- Clear separation of concerns
- Independent testing of components with `tasks_from` parameter
- Reusable task files
- Easier maintenance and troubleshooting
- Reduced `main.yml` complexity

**Task file naming conventions:**

- Use descriptive names: `vault_retrieve_credentials.yml`, `cluster_health_check.yml`
- Name files for the specific workflow: `preflight.yml`, `execute.yml`, `verify.yml`
- Document each task file with header comments

### preflight.yml Pattern

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
```

### Playbook Structure

*`source: ANSIBLE-DEVELOPMENT-STANDARDS.md` v1.0.0*

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
  become: false       # or true with justification

  vars:
    playbook_variable: "value"

  vars_files:
    - vars/common.yml

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

  roles:
    - role: <role_name>
      vars:
        <role_name>_variable: "value"
      tags: [<role_name>]

  post_tasks:
    - name: Display execution summary
      ansible.builtin.debug:
        msg: |
          Execution Status: {{ <role_name>_execution_status }}
          Completed: {{ ansible_date_time.iso8601 }}
      tags: [always]
```

### Anti-Patterns to Avoid

Anti-Pattern: Playbook as Shell Script

```yaml
# DON'T DO THIS
- name: Bad playbook
  hosts: localhost
  tasks:
    - shell: oc get pods -n openshift-storage
    - shell: oc get pv | grep -i portworx
```

Anti-Pattern: No Error Handling

```yaml
# DON'T DO THIS
- name: Update resource
  kubernetes.core.k8s:
    definition: "{{ resource_def }}"

- name: Wait for ready
  shell: sleep 30
```

Anti-Pattern: Logic in main.yml

```yaml
# WRONG - Claude should NEVER put logic in main.yml
---
- name: Do something
  shell: some command

- name: Do another thing
  file: ...
```

---

## 3. Variable Conventions

*`source: ANSIBLE-DEVELOPMENT-STANDARDS.md` v1.0.0, `source: ANSIBLE-ROLE-STANDARDS.md` v1.0.0*

### Variable Naming

- All role variables MUST be prefixed with the role name: `<role_name>_variable_name`
- Internal constants use double-underscore prefix: `__<role_name>_version`
- Use descriptive names; avoid abbreviations (`namespace` not `ns`, `timeout` not `to`)
- Use lowercase with underscores

### defaults/main.yml — User-Configurable Variables

```yaml
---
# <role_name> default variables
# These can be overridden by users

# General settings
<role_name>_namespace: "default"
<role_name>_timeout: 300        # seconds
<role_name>_retry_count: 30
<role_name>_retry_delay: 10     # seconds

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
<role_name>_report_format: "json"     # json, yaml, text
<role_name>_report_destination: "/tmp/<role_name>-report.json"
```

### vars/main.yml — Internal Constants

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

### meta/main.yml

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

### Variable Precedence (Lowest to Highest)

1. role defaults
2. inventory group vars
3. inventory host vars
4. playbook vars
5. role vars
6. task vars
7. extra vars (command line)

Key takeaways:

- `defaults/main.yml` — Lowest precedence, easily overridden
- `vars/main.yml` — High precedence, hard to override
- `extra_vars` — Highest precedence

### Variable Validation

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

### Variable Anti-Patterns

```yaml
# BAD — non-descriptive names
vars:
  ns: "kube-system"
  to: 300
  verify: true

# GOOD — descriptive, prefixed names
vars:
  cluster_setup_namespace: "kube-system"
  cluster_setup_timeout: 300
  cluster_setup_enable_verification: true
```

---

## 4. FQCN and Module Selection

*`source: ANSIBLE-DEVELOPMENT-STANDARDS.md` v1.0.0, `source: AGENTS.md` v1.0.0, `source: CLAUDE.md` v2.0.0*

### FQCN is Mandatory

All Ansible modules MUST use Fully Qualified Collection Names. No exceptions.

```yaml
# CORRECT — always generate this
- name: Create directory
  ansible.builtin.file:
    path: /tmp/work
    state: directory

- name: Get pod information
  kubernetes.core.k8s_info:
    kind: Pod
    namespace: default

# WRONG — NEVER generate this
- name: Create directory
  file:        # Missing FQCN — FORBIDDEN
    path: /tmp/work
    state: directory
```

### Prefer Native Modules Over Shell

AVOID `shell` and `command` modules for Kubernetes operations. Always prefer native modules.

```yaml
# WRONG — NEVER generate this
- name: Get pods
  shell: oc get pods -n {{ namespace }}
  register: pods

# CORRECT — ALWAYS prefer this
- name: Get pod information
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: "{{ namespace }}"
  register: pods
```

**When shell IS acceptable:**

```yaml
# Only when no module exists AND you explain why
- name: Execute pxctl command (no module available)
  ansible.builtin.shell: |
    pxctl status
  changed_when: false
  failed_when: result.rc != 0
  # Comment explaining why shell is necessary
```

### Common oc Command Translations

*`source: ANSIBLE-DEVELOPMENT-STANDARDS.md` v1.0.0, `source: CLAUDE.md` v2.0.0*

| Shell Command | Native Module |
|---|---|
| `oc get pods` | `kubernetes.core.k8s_info: kind: Pod` |
| `oc apply` | `kubernetes.core.k8s: state: present` |
| `oc delete` | `kubernetes.core.k8s: state: absent` |
| `oc scale` | `kubernetes.core.k8s` with definition |
| `oc rsh` | `kubernetes.core.k8s_exec` |
| `oc patch` | `kubernetes.core.k8s` with definition patch |

### Primary Kubernetes Modules

*`source: KUBERNETES-PATTERNS.md` v1.0.0*

| Module | Purpose | Use For |
|--------|---------|---------|
| `kubernetes.core.k8s` | Create/Update/Delete resources | Applying manifests, updating resources |
| `kubernetes.core.k8s_info` | Query resources | Getting current state, checking status |
| `kubernetes.core.k8s_exec` | Execute commands in pods | Running commands, getting pod output |
| `kubernetes.core.k8s_scale` | Scale workloads | Scaling deployments/statefulsets |
| `kubernetes.core.k8s_drain` | Drain nodes | Node maintenance operations |
| `kubernetes.core.k8s_cp` | Copy files to/from pods | File transfers |
| `kubernetes.core.helm` | Helm chart operations | Installing/upgrading charts |

### Boolean Values

Use lowercase `true`/`false`. Never use `True`/`False`, `YES`/`NO`, or `yes`/`no`.

---

## 5. Idempotency: changed_when and failed_when

*`source: ANSIBLE-DEVELOPMENT-STANDARDS.md` v1.0.0, `source: ANSIBLE-ROLE-STANDARDS.md` v1.0.0, `source: changed_when_failed_when_examples.yml`*

### Core Rule

Every `shell` and `command` task MUST define both `changed_when` and `failed_when`.

### Read-Only Operations — Always False

For any operation that only reads state, never reports as changed:

```yaml
- name: Get list of pods (read-only)
  ansible.builtin.shell: kubectl get pods --no-headers
  register: pod_list
  changed_when: false
  failed_when: pod_list.rc != 0

- name: Get cluster information
  ansible.builtin.command: oc cluster-info
  register: cluster_info
  changed_when: false
  failed_when: cluster_info.rc != 0

- name: Check service status
  ansible.builtin.shell: systemctl status nginx
  register: service_status
  changed_when: false
  failed_when: service_status.rc not in [0, 3]  # 0=running, 3=stopped
```

### Grep Operations — Allow No-Match Exit Code

grep returns `0` if matches found, `1` if no matches. Both are valid:

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

### State-Modifying Operations — Detect Changes from Output

```yaml
- name: Apply configuration
  ansible.builtin.shell: |
    oc apply -f /tmp/config.yaml
  register: apply_result
  changed_when: "'configured' in apply_result.stdout or 'created' in apply_result.stdout"
  failed_when: apply_result.rc != 0

- name: Create resource if not exists
  ansible.builtin.shell: |
    oc create -f /tmp/resource.yaml 2>&1
  register: create_result
  changed_when: create_result.rc == 0
  failed_when:
    - create_result.rc != 0
    - "'already exists' not in create_result.stderr"
```

### Unexpected State Detection

```yaml
- name: Verify expected output present
  ansible.builtin.shell: |
    some-command --output-expected-value
  register: validation_result
  changed_when: validation_result.stdout_lines | length == 0
  failed_when: validation_result.rc != 0
```

### Retry Operations

```yaml
- name: Wait for service to become available
  ansible.builtin.shell: |
    curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health
  register: health_check
  changed_when: false
  failed_when: health_check.stdout != "200"
  until: health_check.stdout == "200"
  retries: 30
  delay: 10
```

### Multi-Line Commands with pipefail

```yaml
- name: Complex pipeline operation
  ansible.builtin.shell: |
    set -o pipefail
    oc get pods -n {{ namespace }} --no-headers | \
      grep -E "Running|Ready" | \
      awk '{print $1}'
  args:
    executable: /bin/bash
  register: pod_names
  changed_when: false
  failed_when: pod_names.rc not in [0, 1]
```

### Common Patterns Reference

```yaml
# Read-only
changed_when: false
failed_when: result.rc != 0

# Grep operations
changed_when: false
failed_when: result.rc not in [0, 1]

# State changes
changed_when: "'created' in result.stdout or 'updated' in result.stdout"
failed_when: result.rc != 0

# Unexpected state
changed_when: result.stdout_lines | length == 0
failed_when: result.rc != 0
```

---

## 6. Error Handling

*`source: ANSIBLE-DEVELOPMENT-STANDARDS.md` v1.0.0, `source: ANSIBLE-ROLE-STANDARDS.md` v1.0.0, `source: AGENTS.md` v1.0.0, `source: DEVELOPMENT_STANDARDS.md` v1.0*

### Ansible: block/rescue/always

Critical operations MUST use block/rescue/always:

```yaml
- name: Operation with comprehensive error handling
  block:
    # Try block — main operation
    - name: Execute primary operation
      kubernetes.core.k8s:
        definition: "{{ resource_definition }}"
      register: operation_result

    - name: Record success
      ansible.builtin.set_fact:
        operation_status: "success"

  rescue:
    # Rescue block — error handling
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
    # Always block — cleanup (ALWAYS runs)
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
    global_timeout: 2100    # 35 minutes
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

### Retry Pattern

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

### Python Error Handling

*`source: DEVELOPMENT_STANDARDS.md` v1.0*

Every function with user interaction MUST have try/except/finally:

```python
import logging
logger = logging.getLogger(__name__)

def user_action(self, event):
    """Clear docstring explaining purpose and behavior.

    Args:
        event: Description of parameter

    Returns:
        Description of return value (if any)
    """
    logger.info("User action started - describe what user did")

    try:
        # Setup phase
        logger.debug(f"Setup details: {variable}")

        # Main logic
        result = perform_operation()

        # Handle result
        if result:
            logger.info(f"Operation succeeded: {result}")
        else:
            logger.debug("User cancelled operation")

    except SpecificException as e:
        logger.error(f"Specific error in operation: {e}", exc_info=True)
        show_user_error(f"Specific error message: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in operation: {e}", exc_info=True)
        show_user_error(f"An error occurred: {e}")
    finally:
        # Cleanup ALWAYS runs
        cleanup_resources()
        logger.debug("Cleanup completed")
```

### Forbidden Error Handling Patterns

```python
# NEVER DO THIS
try:
    data = perform_operation()
except:      # bare except — FORBIDDEN
    pass

# NEVER DO THIS
try:
    data = perform_operation()
except Exception:
    pass     # silent failure — FORBIDDEN
```

### Python Mandatory Code Elements

Every function with user interaction MUST have:

- Logger initialization at module level
- Entry logging (info level) when user triggers action
- try/except/finally structure
- Error logging with `exc_info=True` for stack traces
- User feedback on errors
- Resource cleanup in finally block

Every module MUST have:

- `import logging` at top
- `logger = logging.getLogger(__name__)` after imports
- Docstrings on all functions/classes
- Type hints on new code

---

## 7. Tags

*`source: Ansible_Tags_Usage_Guide.md`, `source: ANSIBLE-DEVELOPMENT-STANDARDS.md` v1.0.0*

### Tag Naming Conventions

- Use lowercase with hyphens: `pre-flight`, `post-check`
- Be consistent across roles
- Include role name tag: `portworx-upgrade`
- Standard tags: `always`, `never`, `preparation`, `validation`, `execution`, `verification`, `reporting`

### Tag Behavior Rules

1. No tag filter = everything runs
2. Tag filter present = only matching tags run
3. Untagged tasks do not run when filtering
4. Multiple tags use OR logic
5. Block tags are inherited by contained tasks
6. `always` overrides filtering unless explicitly skipped

### Basic Tag Usage

```yaml
- name: Install package
  ansible.builtin.dnf:
    name: httpd
    state: present
  tags:
    - install

- name: Start service
  ansible.builtin.service:
    name: httpd
    state: started
  tags:
    - service
```

### Multi-Tag Usage

A task may have multiple tags. Tag matching uses OR logic:

```yaml
- name: Install package
  ansible.builtin.dnf:
    name: httpd
    state: present
  tags:
    - install
    - web
    - base
```

### Block-Level Tags

Tags applied at the block level are inherited by all tasks inside the block:

```yaml
- block:
    - name: Task A
      ansible.builtin.debug:
        msg: "A"

    - name: Task B
      ansible.builtin.debug:
        msg: "B"
  tags:
    - web
```

### The always Tag

The `always` tag runs regardless of tag filtering:

```yaml
- name: Always run this
  ansible.builtin.debug:
    msg: "This always runs"
  tags:
    - always
```

Behavior:

- Runs when no tags are specified
- Runs when specific tags are specified
- Skipped only if explicitly excluded with `--skip-tags always`

Use `always` for mandatory validation, safety checks, or audit logic.

### Execution Summary Table

| Scenario | Tagged Task | Untagged Task | always |
|---|---|---|---|
| No tags specified | Runs | Runs | Runs |
| `--tags install` | Runs if matching | Skipped | Runs |
| `--skip-tags install` | Skipped | Runs | Runs |
| `--tags install --skip-tags always` | Runs | Skipped | Skipped |

### Operational Best Practices

- Tag all operationally distinct task groups
- Avoid mixing unrelated logic under the same tag
- Use consistent naming conventions: `install`, `config`, `validate`, `cleanup`
- Avoid leaving critical tasks untagged in controlled environments
- Use `always` only for mandatory execution logic

---

## 8. Kubernetes and OpenShift Patterns

*`source: KUBERNETES-PATTERNS.md` v1.0.0, `source: COMPREHENSIVE-GUIDE.md` v1.0.0, `source: ANSIBLE-DEVELOPMENT-STANDARDS.md` v1.0.0*

### Understanding the Kubernetes API

Every Kubernetes resource has this structure:

```yaml
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

### Creating Resources

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
```

### Querying Resources

```yaml
- name: Get all application pods
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: production
    label_selectors:
      - "app=myapp"
      - "tier in (frontend, backend, worker)"
      - "!canary"  # Exclude canary deployments
  register: app_pods

- name: Access resource fields
  ansible.builtin.debug:
    msg: |
      Name: {{ deploy.resources[0].metadata.name }}
      Namespace: {{ deploy.resources[0].metadata.namespace }}
      Replicas: {{ deploy.resources[0].spec.replicas }}
      Ready: {{ deploy.resources[0].status.readyReplicas | default(0) }}
      Image: {{ deploy.resources[0].spec.template.spec.containers[0].image }}
```

### Label Selectors

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
  - "environment"   # Key exists
  - "!deprecated"  # Key does not exist
```

### Field Selectors

```yaml
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

### Executing Commands in Pods

```yaml
- name: Execute command in pod
  kubernetes.core.k8s_exec:
    namespace: default
    pod: my-pod
    command: ls -la
  register: output
```

### Updating Resources

```yaml
# WRONG
- name: Patch deployment
  shell: |
    oc patch deployment {{ deploy_name }} -n {{ namespace }} \
      --patch '{"spec":{"replicas":{{ replica_count }}}}'

# CORRECT
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

### Structured Data vs Text Parsing

```yaml
# WRONG — fragile text parsing
- name: Count running pods
  shell: oc get pods -n {{ ns }} | grep Running | wc -l
  register: count

# CORRECT — structured data
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

## 9. Custom Module Development

*`source: ANSIBLE-ROLE-STANDARDS.md` v1.0.0, `source: ANSIBLE-DEVELOPMENT-STANDARDS.md` v1.0.0, `source: CLAUDE.md` v2.0.0, `source: custom_module_example.py`*

### When to Create Custom Modules

SHOULD create custom modules when:

1. Repeated complex shell commands — same multi-line shell script used in multiple roles
2. External tool interaction — need to parse output from tools like `pxctl`, `etcdctl`
3. Custom logic — behavior not available in existing modules
4. Idempotency — need proper change detection for external state
5. Error handling — need structured error handling for specific operations

SHOULD NOT create custom modules when:

1. An existing module can do the job
2. A simple shell command is sufficient
3. The operation is one-time use

### Module File Location

Custom modules live at `roles/<role_name>/library/<module_name>.py`

### Complete Module Structure Template

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Your Name <your.email@example.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: module_name
short_description: Brief description
description:
  - Detailed description
version_added: "1.0.0"
author:
  - Your Name (@github_handle)
options:
  param_name:
    description: Parameter description
    type: str
    required: true
requirements:
  - python >= 3.11
'''

EXAMPLES = r'''
- name: Basic usage
  module_name:
    param_name: value
'''

RETURN = r'''
changed:
  description: Whether the module made changes
  type: bool
  returned: always
msg:
  description: Human-readable message
  type: str
  returned: always
result:
  description: Detailed result data
  type: dict
  returned: success
'''

from ansible.module_utils.basic import AnsibleModule


def run_module():
    module_args = dict(
        param_name=dict(type='str', required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(changed=False, msg='', result={})

    try:
        if module.check_mode:
            result['msg'] = 'Check mode: would process resource'
            module.exit_json(**result)

        # Actual processing
        result['changed'] = True
        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=f'Module execution failed: {str(e)}', **result)


def main():
    run_module()


if __name__ == '__main__':
    main()
```

### Required Module Components

1. **Module Header:** Shebang, encoding, copyright, future imports, metaclass
2. **DOCUMENTATION section:** module name, description, options, requirements
3. **EXAMPLES section:** practical usage examples
4. **RETURN section:** all returned fields documented
5. **AnsibleModule initialization:** always support check mode, validate parameters
6. **Structured error handling:** specific exceptions, never bare `except:`
7. **Idempotency:** check current state before making changes

### Kubernetes Resource Management Pattern

```python
from kubernetes import client, config
from kubernetes.client.rest import ApiException


def manage_k8s_resource(module):
    config.load_kube_config()
    v1 = client.CoreV1Api()

    try:
        existing = v1.read_namespaced_pod(name, namespace)
        resource_exists = True
    except ApiException as e:
        if e.status == 404:
            resource_exists = False
        else:
            raise

    if module.check_mode:
        return {'changed': not resource_exists, 'msg': f'Would create {name}'}
```

### Command Execution in Pods Pattern

```python
from kubernetes.stream import stream

resp = stream(
    v1.connect_get_namespaced_pod_exec,
    pod_name, namespace,
    command=command,
    stderr=True, stdin=False, stdout=True, tty=False
)
return {'changed': False, 'msg': 'Command executed', 'stdout': resp}
```

### Module Best Practices

DO:

- Always support check mode
- Validate all input parameters
- Return meaningful error messages
- Use `module.fail_json()` for failures
- Set `changed=False` for read-only operations
- Implement idempotency
- Include comprehensive DOCUMENTATION/EXAMPLES/RETURN
- Test both success and failure paths

DO NOT:

- Use bare `except:` clauses
- Print to stdout/stderr
- Make changes in check mode
- Assume parameters are valid without checking
- Hard-code credentials
- Skip documentation sections

### Module Code Quality Requirements

All modules must pass:

```bash
.venv/bin/isort roles/<role_name>/library/*.py
.venv/bin/black roles/<role_name>/library/*.py
.venv/bin/flake8 roles/<role_name>/library/*.py
.venv/bin/mypy roles/<role_name>/library/*.py
```

---

## 10. Custom Filter Plugins

*`source: ANSIBLE-ROLE-STANDARDS.md` v1.0.0, `source: filter_plugin_example.py`, `source: examples/README.md`*

### Filter Plugin Location

- Role-specific: `roles/<role_name>/filter_plugins/<filter_name>.py`
- Global: `filter_plugins/` at repository root

### Complete Filter Plugin Template

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Your Name <your.email@example.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
filter: filter_name
author: Author Name (@github_handle)
version_added: "1.0.0"
short_description: Brief description
description:
  - Detailed description
options:
  _input:
    description: The input value
    type: any
    required: true
'''

EXAMPLES = r'''
- debug:
    msg: "{{ input_value | filter_name }}"
'''

RETURN = r'''
_value:
  description: The filtered value
  type: any
  returned: always
'''

from ansible.errors import AnsibleFilterError


class FilterModule(object):
    def filters(self):
        return {'filter_name': self.filter_method}

    @staticmethod
    def filter_method(value, param=None):
        if not isinstance(value, expected_type):
            raise AnsibleFilterError(f"Expected {expected_type}, got {type(value).__name__}")

        try:
            return transform(value, param)
        except Exception as e:
            raise AnsibleFilterError(f"Error in filter_name: {str(e)}")
```

### Available Filter Examples (from examples/filter_plugin_example.py)

Filters included in the project examples:

- `extract_field` — Extract specific fields from list of dictionaries
- `filter_by_status` — Filter items by status field
- `transform_keys` — Transform dictionary keys using a mapping
- `normalize_list` — Deduplicate and normalize lists
- `deep_merge` — Recursively merge dictionaries
- `safe_get` — Safely access nested dictionary values with dot notation
- `to_key_value_pairs` — Convert dictionary to list of key-value pairs

Example usage:

```yaml
- set_fact:
    pod_names: "{{ pods | extract_field('name') }}"

- set_fact:
    running_pods: "{{ pods | filter_by_status('Running') }}"

- set_fact:
    final_config: "{{ base_config | deep_merge(override_config) }}"
```

### Filter Plugin Best Practices

DO:

- Validate input types before processing
- Use descriptive error messages
- Provide comprehensive documentation
- Use static methods when possible
- Test edge cases

DO NOT:

- Use bare `except:` clauses
- Return None for errors — raise `AnsibleFilterError`
- Modify input values
- Perform I/O operations in filters
- Assume input types

---

## 11. Testing Standards

*`source: ANSIBLE-DEVELOPMENT-STANDARDS.md` v1.0.0, `source: ANSIBLE-ROLE-STANDARDS.md` v1.0.0, `source: DEVELOPMENT_STANDARDS.md` v1.0, `source: examples/README.md`*

### Role Testing Workflow

Phase 1: Syntax Validation

```bash
.venv/bin/ansible-playbook --syntax-check playbooks/test_role.yml
```

Phase 2: Linting

```bash
.venv/bin/ansible-lint --profile=production roles/<role_name>/
.venv/bin/yamllint roles/<role_name>/
```

Phase 3: Check Mode (Dry Run)

```bash
.venv/bin/ansible-playbook -i inventory playbooks/test_role.yml --check
```

Phase 4: Tag-Based Testing

```bash
.venv/bin/ansible-playbook -i inventory playbooks/test_role.yml --tags preflight
.venv/bin/ansible-playbook -i inventory playbooks/test_role.yml --tags validation
```

Phase 5: Full Execution

```bash
.venv/bin/ansible-playbook -i inventory/test playbooks/test_role.yml -vv
```

### Python Module Testing

*`source: module_testing_example.py`, `source: examples/README.md`*

Run unit tests:

```bash
.venv/bin/pytest tests/unit/test_<module_name>.py

# With coverage
.venv/bin/pytest --cov=library --cov-report=html tests/unit/

# Integration tests
.venv/bin/ansible-playbook tests/integration/test_custom_module.yml
```

Test scenarios to cover:

- Valid argument validation
- Missing required parameters
- Invalid parameter values
- Successful resource creation
- Resource already exists (idempotency)
- Resource deletion
- Check mode behavior
- External API errors
- State change detection

### Three-Tier Testing Strategy

*`source: DEVELOPMENT_STANDARDS.md` v1.0*

**Tier 1: Automated Tests** (pytest or equivalent)

- When: After EVERY code change
- Requirement: Must remain passing (no tolerance for breaking tests)
- Frequency: Continuous

Tier 2: Programmatic Validation

- When: GUI/integration testing not available
- Methods: Syntax validation, pattern verification, round-trip testing, API compliance checking

Tier 3: Manual Testing

- When: Full environment available
- Requirements: Structured checklist, document each step result, capture logs for review

### Testing Pre-Commit Checklist

Before committing code:

- [ ] Syntax check passes
- [ ] Ansible-lint passes
- [ ] YAML lint passes
- [ ] Check mode runs without errors
- [ ] All tags work individually
- [ ] Full playbook runs successfully
- [ ] Error handling tested
- [ ] Documentation updated
- [ ] CHANGELOG updated

### Coverage Requirements

*`source: DEVELOPMENT_STANDARDS.md` v1.0*

- Critical paths: 100% (must have tests)
- User-facing features: 90%+ (should have tests)
- Utility functions: 70%+ (nice to have tests)
- Legacy code: Test during modification (add as you touch)

---

## 12. Documentation Requirements

*`source: ANSIBLE-DEVELOPMENT-STANDARDS.md` v1.0.0, `source: MARKDOWN_STANDARDS.md`, `source: ANSIBLE-ROLE-STANDARDS.md` v1.0.0*

### README.md Required Structure

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

### meta/main.yml for Documentation

```yaml
---
galaxy_info:
  role_name: <role_name>
  author: Your Name
  description: Brief description
  company: Your Company
  license: Apache-2.0
  min_ansible_version: "2.12"
  platforms:
    - name: EL
      versions:
        - "8"
        - "9"
  galaxy_tags: []

dependencies: []
```

### Markdown Standards

*`source: MARKDOWN_STANDARDS.md`*

All markdown files MUST:

- Pass `pymarkdownlnt -d MD013 scan` before merging
- Include language identifiers on ALL fenced code blocks (MD040)
- Use no emojis — documentation must be professional and text-only
- Use ATX-style headers (`#` prefix) not Setext-style underlines
- Write in present tense for current behavior
- Use imperative mood for instructions

Linting command:

```bash
# Lint all markdown files (MD013 line length check is disabled)
pymarkdownlnt -d MD013 scan

# Lint specific file
pymarkdownlnt -d MD013 scan README.md

# Lint all markdown in docs/
pymarkdownlnt -d MD013 scan docs/
```

### Code Block Language Specification

Every fenced code block MUST include a language identifier:

```python
print("Hello World")
```

```bash
echo "Hello World"
```

```text
This is plain text content
```

If no specific language applies, use `text`. Never create code blocks with opening triple backticks without a language specifier.

Common language identifiers:

- Programming: `python`, `bash`, `javascript`, `java`, `yaml`, `json`, `xml`
- Output/Logs: `text`, `console`, `log`
- Documentation: `markdown`, `html`, `css`
- Configuration: `ini`, `toml`, `conf`, `hcl`

### Documentation Placement

All documentation files must be placed in the `docs/` directory:

- General documentation: `docs/` root
- Role-specific: `docs/<role_name>/`
- Collection-specific: `docs/<collection_name>/`
- Filter plugins: `docs/filters/`

Exceptions:

- `CLAUDE.md` — Repository root
- `README.md` — Repository root only
- `aap_import/README.md` — AAP import main documentation
- `aap_import/<role_name>/README.md` — Role-specific AAP import guides

---

## 13. Security and Vault Integration

*`source: Guidelines-vaultandansible-copy.md`, `source: SecurityGuidelinesvault.md`*

### RBAC with AD Groups

AD group structure for Vault access:

1. **Ansible_DevOps** — Read-only access to non-production secrets
   - Sub-groups: `Ansible_Dev_Admins`, `Ansible_QA_Admins`, `Ansible_Stage_Admins`
2. **Ansible_ProdOps** — Read-only access to production secrets
   - Sub-groups: `Ansible_Prod_Admins`, `Ansible_Prod_Operators`, `Ansible_Prod_Support`
3. **Ansible_Admins** — Full access to all secrets and administrative capabilities
   - Sub-groups: `Ansible_Security_Admins`, `Ansible_Platform_Admins`
4. **Ansible_Auditors** — Read-only access for compliance verification and audit purposes
   - Sub-groups: `Ansible_Compliance_Auditors`, `Ansible_Security_Auditors`

### Comprehensive KV Path Permissions Matrix

| Vault Path | AD Group | Capabilities | Purpose |
|---|---|---|---|
| `secret/ansible/dev/*` | Ansible_DevOps | read, list | Development environment secrets |
| `secret/ansible/dev/admin/*` | Ansible_Dev_Admins | read, create, update, delete, list | Development admin operations |
| `secret/ansible/stage/*` | Ansible_QA_Admins | read, list | Staging environment secrets |
| `secret/ansible/prod/*` | Ansible_ProdOps | read, list | Production environment secrets |
| `secret/ansible/prod/admin/*` | Ansible_Prod_Admins | read, create, update, delete, list | Production admin operations |
| `secret/ansible/global/*` | Ansible_DevOps, Ansible_ProdOps | read, list | Cross-environment shared secrets |
| `secret/ansible/admin/*` | Ansible_Admins | read, create, update, delete, list | Administrative secrets |
| `secret/ansible/audit/*` | Ansible_Auditors | read, list | Audit trail and compliance data |
| `sys/policies/acl/*` | Ansible_Security_Admins | read, create, update, delete, list | Policy management |
| `auth/ldap/*` | Ansible_Platform_Admins | read, create, update, delete, list | Authentication configuration |

### Vault Policy Examples

```hcl
# ansible_devops_policy.hcl
# Purpose: Provides read access to development secrets for DevOps team members

path "secret/data/ansible/dev/*" {
  capabilities = ["read", "list"]
}

path "secret/data/ansible/global/*" {
  capabilities = ["read", "list"]
}

# Deny access to production secrets
path "secret/data/ansible/prod/*" {
  capabilities = ["deny"]
}

path "secret/metadata/ansible/dev/*" {
  capabilities = ["read", "list"]
}
```

```hcl
# ansible_prod_admins_policy.hcl
# Purpose: Provides administrative access to production secrets

path "secret/data/ansible/prod/*" {
  capabilities = ["read", "create", "update", "delete", "list"]
}

path "secret/data/ansible/prod/admin/*" {
  capabilities = ["read", "create", "update", "delete", "list"]
}

path "secret/data/ansible/global/*" {
  capabilities = ["read", "list"]
}

path "secret/metadata/ansible/prod/*" {
  capabilities = ["read", "create", "update", "delete", "list"]
}
```

### Vault Namespace and Path Layout

Namespace hierarchy:

1. Root Namespace — Reserved for global administrators only
2. Organization-Level Namespaces — For business units or departments
3. Project-Level Namespaces — For specific applications or environments
4. Team-Level Namespaces — For development, operations, or security teams

Recommended path structure for Ansible:

```text
secret/                           # KV secrets engine mount
├── ansible/
│   ├── environments/
│   │   ├── production/
│   │   │   ├── app1/
│   │   │   │   ├── credentials/
│   │   │   │   ├── certificates/
│   │   │   │   └── config/
│   │   ├── staging/
│   │   └── development/
│   ├── global/
│   │   ├── api_keys/
│   │   └── certificates/
│   └── infrastructure/
│       ├── network/
│       ├── cloud/
│       └── databases/
└── shared/
    └── common_services/
```

### Host-Based Access Control

Vault should be configured to allow access only from approved hosts:

```hcl
# CIDR restriction policy
path "secret/ansible/prod/*" {
  capabilities = ["read"]
  allowed_entities = ["group=Ansible_ProdOps"]
  allowed_bound_cidrs = ["10.1.1.0/24"]
}
```

TLS client certificates for host restrictions:

```hcl
auth "cert" {
  allowed_certs = ["CN=ansible-node1.example.com"]
}
```

AppRole with host metadata binding:

```hcl
auth "approle" {
  allowed_entity_aliases = ["host-ansible-prod"]
}
```

### MFA for Untrusted Locations

```hcl
path "auth/ldap/login" {
  capabilities = ["update"]
  mfa_policy = "mfa_required"
}
```

### Ansible Vault Integration

- Use Ansible Vault to encrypt sensitive variables
- Combine Ansible Vault with HashiCorp Vault for layered security
- Never commit plaintext secrets
- Use `no_log: true` for tasks handling credentials

```yaml
# Mark sensitive operations
- name: Retrieve database credentials
  community.hashi_vault.vault_kv2_get:
    path: "{{ vault_secret_path }}"
    auth_method: approle
    role_id: "{{ vault_role_id }}"
    secret_id: "{{ vault_secret_id }}"
  register: db_credentials
  no_log: true

- name: Use credentials securely
  ansible.builtin.template:
    src: db_config.j2
    dest: /etc/app/database.conf
    mode: '0600'
  vars:
    db_password: "{{ db_credentials.secret.password }}"
  no_log: true
```

### Ansible Security Best Practices

- Use Ansible Vault to encrypt sensitive data
- Never log sensitive information — use `no_log: true`
- Validate all external input using `assert` module
- Use HTTPS for all API communication
- Implement proper privilege escalation with `become` only when necessary
- No hardcoded credentials in playbooks, roles, or variables files
- Use `sensitive` parameter where available

---

## 14. Vault Security Migration

*`source: VaultSecurityMigrationGuide.md`*

### Migration Strategy Overview

The migration process is divided into phases for incremental implementation without disrupting existing operations.

### Phase 0: Assessment and Planning (2-4 weeks)

1. Current State Documentation
   - Inventory existing Ansible playbooks and roles
   - Document current secret management practices
   - Identify all secret access patterns and consumers
   - Map existing automation workflows

2. Gap Analysis
   - Compare current practices against target security model
   - Identify high-risk areas requiring immediate attention
   - Document compliance requirements and deadlines

3. Resource Planning
   - Identify required skills and team members
   - Plan for potential downtime or maintenance windows

4. Success Metrics
   - Define KPIs for measuring security improvements
   - Establish baseline metrics

### Phase 1: Foundation Building (4-6 weeks)

1. HashiCorp Vault Deployment
   - Deploy Vault in high-availability mode
   - Configure initial authentication methods
   - Set up basic audit logging
   - Implement backup and recovery procedures

2. Initial Secret Migration
   - Identify critical secrets for initial migration
   - Create basic KV structure in Vault
   - Migrate highest-risk secrets first (e.g., production credentials)

3. Basic Authentication Setup
   - Configure LDAP/AD integration
   - Create initial policies for administrators
   - Set up emergency access procedures

4. Ansible Integration
   - Install Vault lookup plugins
   - Configure basic Vault connection
   - Test connectivity between Ansible and Vault

### Phase 2: Security Hardening (6-8 weeks)

1. Namespace and Path Structure Implementation
2. Role-Based Access Control Implementation
   - Design hierarchical AD group structure
   - Create comprehensive Vault policies for each group
   - Implement least-privilege access controls

3. Authentication Enhancement
   - Implement AppRole authentication for automation
   - Configure TLS client certificates
   - Set up MFA for human users

4. Host-Based Access Controls
   - Implement IP allowlisting
   - Configure bound CIDRs

AD Group mapping implementation:

```hcl
# Step 1: Configure LDAP authentication
vault write auth/ldap/config \
  url="ldaps://ad.example.com:636" \
  userdn="OU=Users,DC=example,DC=com" \
  userattr="sAMAccountName" \
  groupdn="OU=Groups,DC=example,DC=com" \
  groupattr="cn" \
  insecure_tls=false \
  starttls=true

# Step 2: Map AD groups to policies
vault write auth/ldap/groups/Ansible_DevOps policies=ansible_devops_policy
vault write auth/ldap/groups/Ansible_ProdOps policies=ansible_prodops_policy
vault write auth/ldap/groups/Ansible_Admins policies=ansible_admins_policy
```

AppRole setup for automation:

```hcl
vault write auth/approle/role/ansible-automation \
  token_ttl=1h \
  token_max_ttl=4h \
  token_policies=ansible-automation-policy \
  bind_secret_id=true \
  secret_id_bound_cidrs="10.0.0.0/24,192.168.1.0/24"
```

### Phase 3: Ansible Tower/RHAAP Integration (4-6 weeks)

1. Tower Security: authentication, authorization, credential management
2. Job Template Security Controls

### Phase 4: Playbook Refactoring (8-12 weeks)

1. Secret retrieval standardization
2. Dynamic secrets implementation
3. Secret rotation implementation

### Phase 5: Audit and Compliance (4-6 weeks)

1. Callback plugin implementation
2. Log aggregation
3. Compliance reporting

### Phase 6: Disaster Recovery (4-6 weeks)

1. HA configuration
2. Backup enhancement
3. Recovery testing

---

## 15. Distribution and Tarball Packaging

*`source: ansible-role-development-pattern.md` v1.0.0, `source: ANSIBLE-ROLE-DEVELOPMENT-WORKFLOW.md` v1.0.0, `source: CLAUDE-ROLE-WORKFLOW.md`*

### When to Create a Standalone Distribution

Create a standalone tarball when:

- Role is ready for external distribution
- Other teams need independent role usage
- Role should become separate git repository
- Version release milestone reached

### Tarball Naming Convention

```text
<role-name>-role-<version>.tar.gz
```

Examples:

- `portworx-upgrade-role-1.0.0.tar.gz`
- `must-gather-log-role-3.0.0.tar.gz`
- `vault-fix-portworx-role-2.1.0.tar.gz`

### Critical Pattern: Top-Level Role Directories

Role directories (defaults/, meta/, tasks/, etc.) MUST be at the top level of the tarball, NOT nested under a subdirectory.

**CORRECT PATTERN:**

```text
<role-name>-role-<version>/
├── README.md                    # Top level
├── INSTALL.md                   # Top level
├── CHANGELOG.md                 # Top level
├── LICENSE                      # Top level
├── requirements.yml             # Top level
├── .ansible-lint               # Top level
├── .gitignore                  # Top level
├── example-playbook.yml         # Top level
├── group_vars_example.yml       # Top level (if applicable)
├── defaults/                    # Role directory at top level
│   └── main.yml
├── meta/                        # Role directory at top level
│   └── main.yml
├── library/                     # Role directory at top level
│   └── *.py
├── tasks/                       # Role directory at top level
│   └── *.yml
├── playbooks/                   # Playbooks at top level
│   └── *.yml
└── docs/                        # Documentation at top level
    └── *.md
```

**INCORRECT PATTERN — DO NOT USE:**

```text
<role-name>-role-<version>/
├── README.md
└── <role_name>/                # WRONG: Role nested under subdirectory
    ├── defaults/
    ├── meta/
    ├── tasks/
    └── ...
```

### Why Top-Level Structure

1. **Dual-purpose usage:**
   - Extract to roles/ directory: `tar -xzf role.tar.gz -C roles/ && mv roles/<role-name>-role-<version> roles/<role_name>`
   - Use as standalone git repository: `tar -xzf role.tar.gz && cd <role-name>-role-<version> && git init`
2. Ansible expects role directories at the top level of a role path
3. Simplified installation — no nested directory navigation required
4. Git repository readiness — can immediately become a git repository without restructuring

### Required Documentation Files in Distribution

```text
<role-name>-role-<version>/
└── docs/
    ├── DISTRIBUTION-README.md   # Distribution package notes
    ├── QUICKSTART.md           # Quick start guide
    ├── ROLE-README.md          # Full role documentation (copy of role README)
    ├── MANIFEST.txt            # Package contents manifest
    └── example-playbook.yml    # Complete example playbook
```

### Version Control for Releases

- Tag releases in monorepo: `<role_name>-v<version>`
- Update CHANGELOG.md for each version
- Create annotated tags with release notes

```bash
# Create distribution tarball
./scripts/create_role_distribution.sh <role_name> <version>

# Complete workflow (development to production)
./scripts/role_to_production.sh <role_name> <version> [options]
```

---

## 16. Code Review and PR Standards

*`source: CODE-REVIEW-CHECKLIST.md` v1.0.0, `source: PR-TEMPLATE.md`*

### Severity Levels

**BLOCKER** — Must fix before merge:

- Security issues
- Breaking changes
- Syntax errors
- Test failures

**MAJOR** — Should fix before merge:

- Logic errors
- Missing error handling
- Poor naming
- Missing documentation

**MINOR** — Can fix after merge:

- Formatting inconsistencies
- Typos in comments
- Optimization opportunities

**SUGGESTION** — Optional improvements:

- Alternative approaches
- Performance tips
- Future enhancements

### Pre-Submission Checklist (Author)

```markdown
## Pre-Submission Checklist

### Code Quality
- [ ] All files pass syntax check (`ansible-playbook --syntax-check`)
- [ ] Ansible-lint passes with production profile
- [ ] YAML lint passes
- [ ] Python files formatted with black (if applicable)
- [ ] Python imports sorted with isort (if applicable)
- [ ] No flake8 errors (if applicable)

### Testing
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Tested in check mode (`--check`)
- [ ] Tested with tags (`--tags`)
- [ ] Tested in test environment
- [ ] Manual testing completed

### Standards Compliance
- [ ] All modules use FQCN
- [ ] All shell/command tasks have `changed_when`
- [ ] All shell/command tasks have `failed_when`
- [ ] Error handling (block/rescue/always) for critical operations
- [ ] Variables follow naming conventions
- [ ] Tasks have meaningful names
- [ ] Proper tags applied

### Documentation
- [ ] README updated (if needed)
- [ ] CHANGELOG updated
- [ ] Variables documented
- [ ] Complex logic has comments
- [ ] Examples provided (if new feature)

### Kubernetes/OpenShift Specific
- [ ] Using kubernetes.core modules instead of oc/kubectl commands
- [ ] Using structured data instead of text parsing
- [ ] Proper label selectors instead of grep
- [ ] Resource verification after operations

### Self-Review
- [ ] Reviewed own diff for issues
- [ ] No debug statements left in code
- [ ] No commented-out code
- [ ] No TODO comments without ticket numbers
- [ ] No secrets or credentials in code
```

### Code Review Checklist (Reviewer)

Phase 1: Automated Checks (2 minutes)

- [ ] Syntax validation passed
- [ ] Ansible-lint passed
- [ ] YAML lint passed
- [ ] Python quality checks passed (if applicable)
- [ ] All tests passed

Phase 2: PR Metadata (3 minutes)

- [ ] Clear title describing change
- [ ] Problem statement provided
- [ ] Solution approach explained
- [ ] Testing performed described
- [ ] Breaking changes noted (if any)

Phase 3: Code Structure Review (5 minutes)

- [ ] tasks/main.yml is orchestrator only
- [ ] Task files named appropriately
- [ ] README.md present and complete
- [ ] defaults/main.yml has all variables

Phase 4: Code Quality Review (10 minutes)

- [ ] FQCN used everywhere
- [ ] Task names are descriptive
- [ ] Variable names follow conventions
- [ ] Shell/command tasks have `changed_when` and `failed_when`
- [ ] Critical operations have block/rescue/always
- [ ] No oc/kubectl in shell without justification

### Acceptable Reasons for Shell/Command

```markdown
Acceptable reasons:
- No native module exists for this operation
- Module has a known bug that this works around
- Performance requirement that module cannot meet

Unacceptable reasons:
- "I don't know how to use the module"
- "Shell is easier"
- "It's just a one-liner"
```

### PR Title Format

Use one of these prefixes:

- `feat:` New feature or capability
- `fix:` Bug fix
- `refactor:` Code refactoring (no functional changes)
- `docs:` Documentation updates
- `test:` Test additions or modifications
- `chore:` Maintenance tasks (deps, config, etc.)

Example: `feat: Replace oc commands with k8s modules in cluster_setup playbook`

### PR Size

- Preferred: under 500 lines
- If >500 lines: justify why it cannot be split

### Security Review Checklist

- [ ] No credentials in code
- [ ] Sensitive operations use `no_log: true`
- [ ] Secrets use Ansible Vault
- [ ] File permissions explicitly set
- [ ] No SQL injection vectors
- [ ] No command injection vectors
- [ ] Input validation for user-provided variables

---

## 17. Development Workflow

*`source: ANSIBLE-ROLE-DEVELOPMENT-WORKFLOW.md` v1.0.0, `source: DEVELOPMENT_STANDARDS.md` v1.0, `source: ANSIBLE-DEVELOPMENT-STANDARDS.md` v1.0.0, `source: CLAUDE-ROLE-WORKFLOW.md`*

### Virtual Environment — Mandatory

ALL Python and Ansible commands MUST use the virtual environment at `.venv`.

```bash
# Correct — using venv
.venv/bin/ansible-playbook playbook.yml
.venv/bin/ansible-lint roles/

# Wrong — using system Python
ansible-playbook playbook.yml  # NEVER DO THIS
```

Authoritative binaries:

- `.venv/bin/python`
- `.venv/bin/pip`
- `.venv/bin/ansible`
- `.venv/bin/ansible-playbook`
- `.venv/bin/ansible-galaxy`
- `.venv/bin/ansible-lint`
- `.venv/bin/black`
- `.venv/bin/isort`
- `.venv/bin/flake8`
- `.venv/bin/mypy`

Initial setup:

```bash
./setup.sh
```

### Quality Check Workflow

MUST run before every commit:

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

### Pre-commit Hooks

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

  - repo: https://github.com/jackdewinter/pymarkdown
    rev: v0.9.14
    hooks:
      - id: pymarkdown
        args: ["-d", "MD013", "scan"]
```

### Git Commit Messages

Do NOT add Claude Code attribution or co-authorship to commit messages.

Commit messages should:

- Follow conventional commit format when appropriate
- Be concise and descriptive
- Focus on the "why" rather than the "what"
- Match the repository's existing commit style
- NOT include any Claude Code branding, attribution, or co-authorship footers

Good example:

```text
feat: Replace oc commands with kubernetes.core modules in cluster_setup role

Converted shell commands to native Kubernetes modules for better reliability
and maintainability.
```

### Python Standards

- Python 3.11+ syntax
- Type hints required for type checking (`from __future__ import annotations`)
- Follow PEP 8 style guide
- Maximum line length: 100 characters (not 79)
- Use `black` for formatting, `flake8` for linting, `mypy` for type checking

### Debugging Methodology

*`source: DEVELOPMENT_STANDARDS.md` v1.0*

Anti-whack-a-mole strategy: investigate before implementing.

1. Read the error carefully
2. Identify root cause
3. Fix underlying issue
4. Verify fix
5. Do not apply the same broken approach repeatedly

### AAP Integration Notes

- All playbooks run inside Execution Environments
- Dependencies must be declared in requirements files
- Container runtime must be Podman
- Vault-based secret management is standard
- Python 3.11 is the only supported Python version

---

## 18. AI Agent Standards

*`source: AGENTS.md` v1.0.0, `source: CLAUDE.md` v2.0.0*

### General Principles

#### Principle 1: Follow Existing Patterns

Always examine existing code before generating new code:

```text
User asks: "Create a new role for database backup"

Agent should:
1. Read existing role structure (e.g., roles/pxbackup/)
2. Examine tasks/main.yml orchestrator pattern
3. Review variable naming (role_name_variable_name)
4. Match documentation style
5. Generate new role following observed patterns
```

#### Principle 2: Never Assume — Always Verify

Do not rely on memory or training data — verify current state before making changes.

```text
Wrong: "I'll update the deployment.yml file..."
Right: "Let me first check if deployment.yml exists and read its current content..."
```

#### Principle 3: Explain Changes

Always explain what you are doing and why.

#### Principle 4: Test Before Delivering

Validate generated code before presenting it:

- Syntax is correct
- Follows project standards
- Includes error handling
- Has proper documentation
- Uses correct file paths

### Critical Rules for AI Agents

Rule 1: ALWAYS use FQCN. No exceptions.

Rule 2: NEVER use `oc`/`kubectl` in shell. Use kubernetes.core modules. Exception: only if explicitly justified and user confirms.

Rule 3: ALWAYS include error handling (block/rescue/always) for critical operations.

Rule 4: Use orchestrator pattern for tasks/main.yml — no logic in main.yml.

Rule 5: Meaningful task names — action verb + what + context.

Rule 6: ALWAYS run ansible-lint after generating code. Fix issues before presenting code to user.

Rule 7: NEVER use emojis in any generated code, documentation, or commit messages.

Rule 8: ALL code blocks must specify language identifier.

### Quality Assurance Checklist for AI Agents

Before completing any task, verify:

**Ansible Code:**

- [ ] All modules use FQCN
- [ ] Task names are descriptive
- [ ] No oc/kubectl in shell (unless justified)
- [ ] shell/command have changed_when/failed_when
- [ ] Critical operations have error handling
- [ ] Variables follow naming convention
- [ ] Documentation updated

**Python Code:**

- [ ] Type hints on all functions
- [ ] Docstrings present
- [ ] Specific exception handling
- [ ] Follows PEP 8
- [ ] Passes black, isort, flake8

**Documentation:**

- [ ] Code blocks specify language
- [ ] No emojis
- [ ] Professional tone
- [ ] Complete examples
- [ ] README structure followed

**Testing:**

- [ ] ansible-lint passes
- [ ] yamllint passes
- [ ] Syntax check passes
- [ ] Python quality checks pass (if applicable)

### Common Pitfalls for AI Agents

Pitfall 1: Not reading existing code before generating.

Pitfall 2: Using shell commands for K8s operations.

Pitfall 3: Missing error handling.

Pitfall 4: Not running quality checks.

Pitfall 5: Assuming file locations — always verify before modifying.

### Documentation Reference Map

| Topic | Reference Document |
|---|---|
| Quick standards lookup | ANSIBLE-DEVELOPMENT-STANDARDS.md |
| Detailed examples | docs/Ansible_Standards_Documentation/COMPREHENSIVE-GUIDE.md |
| K8s automation | docs/Ansible_Standards_Documentation/KUBERNETES-PATTERNS.md |
| Team migration | docs/Ansible_Standards_Documentation/MIGRATION-GUIDE.md |
| Code review | docs/Ansible_Standards_Documentation/CODE-REVIEW-CHECKLIST.md |
| AI guidelines | docs/Ansible_Standards_Documentation/AGENTS.md |
