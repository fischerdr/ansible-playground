# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code
in this repository.

**Document Version:** 3.0
**Last Updated:** 2026-04-08

---

## Repository Overview

This is an enterprise Ansible Automation Platform (AAP) project for managing
Kubernetes clusters, HashiCorp Vault integration, and Portworx backup operations.
All automation is executed through Ansible Automation Platform using Execution
Environments (EEs) only.

**Key Technologies:**

- Ansible Core 2.18.4
- Python 3.11
- Kubernetes/OpenShift
- HashiCorp Vault
- Portworx Backup (via purepx.px_backup collection)
- Podman container runtime (required)

**Key Documentation:**

- `.agents/skills/ansible/SKILL.md` — Ansible skill entry point, rules, and reference router
- `docs/project_organization.md` — Where things go and why
- `docs/execution-environment.md` — EE dependency and configuration reference

---

## Before Making Any Changes

**1. Read the Ansible skill**

```bash
view .agents/skills/ansible/SKILL.md
```

**2. Read existing code in the area you are changing**

```bash
view roles/<similar_role>/tasks/main.yml
view roles/<similar_role>/defaults/main.yml
```

**3. Load the relevant reference for the task**

```bash
# Kubernetes/OpenShift work
view .agents/skills/ansible/references/KUBERNETES-PATTERNS.md

# Custom module work
view .agents/skills/ansible/references/ANSIBLE-ROLE-STANDARDS.md

# Vault integration
view .agents/skills/ansible/references/SecurityGuidelinesvault.md
```

Do not load all references by default. Load the one relevant to the task.

---

## Python and Ansible Execution Environment

### Authoritative Execution Boundary

All Python and Ansible tooling MUST execute from the project-local virtual
environment at `.venv` in the repository root. System Python, system Ansible,
and globally installed tools are not supported.

### Authoritative Binaries

```bash
.venv/bin/python
.venv/bin/pip
.venv/bin/ansible
.venv/bin/ansible-playbook
.venv/bin/ansible-galaxy
.venv/bin/ansible-lint
.venv/bin/black
.venv/bin/isort
.venv/bin/flake8
.venv/bin/mypy
```

Shell activation (`source .venv/bin/activate`) is permitted for interactive
developer workflows. Scripts, automation, and CI MUST invoke tools explicitly
from `.venv/bin/`.

### Initial Environment Setup

```bash
./setup.sh
```

### Dependency Installation

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/ansible-galaxy collection install -r requirements.yml
chmod +x build.sh && ./build.sh
```

### Role Testing Workflow

1. Syntax validation: `ansible-playbook --syntax-check playbooks/<playbook>.yml`
2. Ansible-lint: `.venv/bin/ansible-lint roles/<role-name>/`
3. Tag-based testing: `ansible-playbook <playbook>.yml --tags preflight --check`
4. Dry-run: `--check` flag
5. Test environment first, then production-like environment

---

## Architecture

### Directory Structure

```text
roles/            Reusable Ansible roles — one directory per role
playbooks/        Orchestration playbooks, organized by functional area
Build-EE/         Execution Environment build configurations
collections/      Local Ansible collections
inventory/        Inventory files with group_vars/ and host_vars/
scripts/          Standalone utility scripts (not executed by AAP)
aap_import/       AAP/AWX import configurations, one subdir per role
library/          Symlinks to custom modules for local dev only
docs/             All project documentation
```

See `docs/project_organization.md` for the complete structure rules and
naming conventions.

### Current Roles

| Role | Purpose |
|------|---------|
| `common` | Shared tasks, filters, and utilities used across roles |
| `configure_clusters` | Cluster configuration and setup |
| `defrag_etcd_db` | etcd database defragmentation for OpenShift |
| `must_gather_log` | Log collection and Red Hat support case upload |
| `portworx_upgrade` | Automated Portworx cluster upgrades on OpenShift |
| `pxbackup` | Portworx PX-Backup operations and schedule management |
| `setup_env` | Environment setup — retrieves credentials from Vault |
| `upgrade_clusters` | Cluster upgrade automation |
| `vault_fix_portworx` | Vault namespace and policy setup for Portworx |
| `vault_kv2_demo` | Vault KV2 secrets engine demonstration role |
| `vault_multi_namespace_monitor` | Vault auth testing across multiple namespaces |

### Custom Modules

Custom Python modules live in `roles/<role_name>/library/` and are symlinked
from `library/` for local development.

Current modules:

- `roles/defrag_etcd_db/library/defrag_etcd.py` — etcd defragmentation
- `roles/must_gather_log/library/redhat_sso_device_auth.py` — Red Hat SSO OAuth2
- `roles/must_gather_log/library/redhat_upload.py` — Red Hat support case upload
- `roles/portworx_upgrade/library/pxctl_status.py` — pxctl command execution

All custom modules follow Ansible 2.18+ standards with DOCUMENTATION, EXAMPLES,
and RETURN sections, argument specs, and check mode support.

### Custom Filter Plugins

Filter plugins live in `roles/<role_name>/filter_plugins/`.

- `roles/common/filter_plugins/custom_filters.py`
- `roles/pxbackup/filter_plugins/lookup_helpers.py`
- `roles/portworx_upgrade/filter_plugins/operator_version.py`
- `roles/portworx_upgrade/filter_plugins/pod_classifier.py`

### Key Collections

- `purepx.px_backup` — Portworx backup API
- `kubernetes.core` — Kubernetes cluster management (v2.3.0+)
- `community.hashi_vault` — HashiCorp Vault integration
- `ansible.posix`, `ansible.utils` — Standard utilities
- `community.vmware` — VMware vSphere integration
- `amazon.aws`, `community.aws`, `google.cloud` — Cloud providers

---

## Non-Negotiable Rules

### Rule 1: FQCN on Every Module

```yaml
# Correct
- name: Create directory
  ansible.builtin.file:
    path: /tmp/work
    state: directory

# Never — missing FQCN is forbidden
- name: Create directory
  file:
    path: /tmp/work
    state: directory
```

### Rule 2: Never Use oc/kubectl in Shell for Kubernetes Operations

```yaml
# Never
- name: Get pods
  shell: oc get pods -n {{ namespace }}

# Always
- name: Get pod information
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: "{{ namespace }}"
```

Exception: only with explicit user confirmation and documented justification.

### Rule 3: Orchestrator Pattern — tasks/main.yml Delegates Only

```yaml
# Correct — main.yml is a phase map
- name: "Phase 1: Preflight"
  ansible.builtin.import_tasks: preflight.yml
  tags: [always, preflight, role_name]

- name: "Phase 2: Execute"
  ansible.builtin.import_tasks: execute.yml
  tags: [execution, role_name]

# Never — no logic in main.yml
- name: Do something
  shell: some command
```

### Rule 4: block/rescue/always for Critical Operations

```yaml
- name: Critical operation
  block:
    - name: Execute operation
      kubernetes.core.k8s:
        definition: "{{ resource }}"
  rescue:
    - name: Handle failure
      ansible.builtin.debug:
        msg: "Failed: {{ ansible_failed_result.msg }}"
  always:
    - name: Cleanup
      ansible.builtin.file:
        path: /tmp/work
        state: absent
```

### Rule 5: changed_when/failed_when on Every shell/command Task

```yaml
# Read-only operation
- name: Query cluster status
  ansible.builtin.shell: pxctl status
  changed_when: false

# State change detected from output
- name: Apply configuration
  ansible.builtin.shell: apply_config.sh
  changed_when: "'applied' in result.stdout"

# Grep and similar — multiple valid exit codes
- name: Check for pattern
  ansible.builtin.shell: grep pattern file.txt
  failed_when: result.rc not in [0, 1]
  changed_when: false
```

### Rule 6: Meaningful Task Names

```yaml
# Correct
- name: Ensure application configuration directory exists with correct permissions
- name: Wait for deployment to reach ready state with all replicas available

# Never
- name: Create dir
- name: Wait
```

---

## Coding Standards

### Ansible Best Practices

- Always use FQCN for all modules
- Use lowercase `true`/`false` for boolean values
- Use `no_log: true` for tasks involving credentials or tokens
- Define required variables at playbook start, validate with `assert`
- Use `block`/`rescue`/`always` for error handling
- Use `ignore_errors` sparingly and only with documented justification
- Design all tasks to be idempotent
- Avoid `shell` and `command` unless no module alternative exists

### Variable Management

- Role defaults: `roles/<role>/defaults/main.yml` — operator-overridable
- Role constants: `roles/<role>/vars/main.yml` — not for override
- Prefix role variables: `<role_prefix>_<name>` — e.g., `px_upgrade_timeout`
- Use descriptive names — no single letters, no unexplained abbreviations
- Document complex variable structures in `defaults/main.yml` comments

### Kubernetes/OpenShift Operations

- Use `kubernetes.core.k8s` for all resource management
- Always specify `api_version` and `kind`
- Use `state: present` for creation/updates, `state: absent` for deletion
- Use `wait: true` with explicit `wait_timeout` values
- Always specify `namespace` explicitly — never rely on defaults

### Python Standards (Modules and Filters)

- Python 3.11+ syntax only
- Type hints required on all functions
- Follow PEP 8, maximum line length 100 characters
- Use `black` for formatting, `flake8` for linting, `mypy` for type checking
- All custom modules must include DOCUMENTATION, EXAMPLES, RETURN sections
- Use `AnsibleFilterError` for filter plugin errors — never return None
- No bare `except:` clauses — ever

### Custom Module Template

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2024, Author <email>
# GNU General Public License v3.0+

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
  - Author Name (@github_handle)
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
'''

from ansible.module_utils.basic import AnsibleModule


def run_module():
    module_args = dict(
        param_name=dict(type='str', required=True),
    )
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    result = dict(changed=False, msg='', result={})

    try:
        if module.check_mode:
            result['msg'] = 'Check mode: no changes made'
            module.exit_json(**result)
        # Module logic here
        result['changed'] = True
        module.exit_json(**result)
    except Exception as e:
        module.fail_json(msg=f'Module execution failed: {str(e)}', **result)


def main():
    run_module()


if __name__ == '__main__':
    main()
```

**For complete working examples:** See `docs/examples/custom_module_example.py`
and `docs/examples/filter_plugin_example.py`.

---

## Quality Assurance

### Automatic Quality Enforcement

Claude Code runs these without user approval (configured in `.claude/settings.local.json`):

- Python files: `isort`, `black`, `flake8`
- Ansible files: `ansible-lint`

### Quality Gates — Run After Every Change

```bash
# Ansible content
.venv/bin/ansible-lint roles/<role_name>/
.venv/bin/yamllint roles/<role_name>/
.venv/bin/ansible-playbook --syntax-check playbooks/<playbook>.yml

# Python modules and filters
.venv/bin/isort roles/<role_name>/library/
.venv/bin/black roles/<role_name>/library/
.venv/bin/flake8 roles/<role_name>/library/
.venv/bin/mypy roles/<role_name>/library/
```

Fix all issues before presenting output to the user. Run again until clean.

### Pre-Completion Checklist

**Ansible:**

- [ ] All modules use FQCN
- [ ] Task names are descriptive
- [ ] No oc/kubectl in shell (or explicitly justified)
- [ ] shell/command tasks have changed_when/failed_when
- [ ] Critical operations use block/rescue/always
- [ ] Variables follow naming convention
- [ ] ansible-lint passes clean

**Python:**

- [ ] Type hints on all functions
- [ ] Docstrings present
- [ ] Specific exception handling (no bare except)
- [ ] Passes black, isort, flake8, mypy

**Documentation:**

- [ ] All code blocks specify language identifier
- [ ] No emojis
- [ ] Professional tone
- [ ] README updated if interface changed

---

## Common Pitfalls

**Generating without reading first**
Always `view` existing similar code before writing new code. Match the patterns
already established in the role or adjacent roles.

**Shell commands for Kubernetes**
If the instinct is to use `shell: oc ...` or `shell: kubectl ...`, stop.
Check `.agents/skills/ansible/references/KUBERNETES-PATTERNS.md` for
the correct module-based approach.

**Missing error handling**
Any task that makes a change to a cluster, Vault, or external system needs
`block/rescue/always`. Read-only tasks do not.

**Assuming file locations**
Always `view` a path before modifying it. Never assume a file exists or has
a particular structure.

**Not running quality checks**
Generate code → run ansible-lint → fix issues → run again → present clean output.
Never skip this loop.

---

## Configuration Files

- `ansible.cfg` — Ansible configuration (inventory, fact caching, SSH retries, callbacks)
- `.ansible-lint` — Ansible-lint configuration
- `.flake8` — Python linting configuration
- `.mypy.ini` — Mypy type checking configuration
- `tox.ini` — Test automation configuration

---

## AAP/AWX Integration

### AAP Project Structure

The `aap_import/` directory contains configurations for importing roles into AAP.
Each role subdirectory includes:

- `README.md` — Role import guide
- `import_to_aap.sh` — Automated import script
- `project_*.json` — Project configuration
- `execution_environment.json` — EE configuration
- `job_template_*.json` — Job template(s)
- `survey_spec_*.json` — Survey specifications
- `workflow_*.json` — Workflow templates (optional)

Reference implementation: `aap_import/portworx_upgrade/`

### Import Methods

1. Automated: `cd aap_import/<role_name> && ./import_to_aap.sh`
2. AWX CLI: `awx projects create --name "..." --scm_type git --scm_url "..."`
3. Web UI: Manual creation following README
4. API: Direct API calls using the JSON files

Never commit credentials. Use AAP credential types for all secrets.

---

## Documentation Standards

- No emojis or icons anywhere — documentation, task names, commit messages
- Ask before creating documentation files — never create unsolicited READMEs
- All code blocks must specify a language identifier (MD040 compliance)
- Professional tone throughout

**File placement:**

- `CLAUDE.md` — Repo root only
- `README.md` — Repo root only (main project README)
- Role-specific docs — `docs/roles/<role_name>/`
- General standards — `.agents/skills/ansible/references/`
- `aap_import/<role>/README.md` — AAP import guides
- All other docs — `docs/` with appropriate subdirectory

---

## Git Commit Messages

Do NOT add Claude Code attribution or co-authorship to commit messages.

```text
# Correct
feat: Replace oc commands with kubernetes.core modules in cluster_setup role

Converted shell commands to native Kubernetes modules for reliability
and idempotency.

# Never
feat: Add new feature

Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Markdown Code Block Language Specification

All fenced code blocks MUST include a language identifier (MD040).

```yaml
- name: Example task
  ansible.builtin.debug:
    msg: "correct"
```

```python
def example():
    pass
```

```text
Plain text content with no specific language.
```

Use `text` as the default when no specific language applies. Never create a
code block with opening ` ``` ` without a language specifier.

### Common Language Identifiers

- Programming: `python`, `bash`, `javascript`, `java`, `yaml`, `json`, `xml`
- Output/Logs: `text`, `console`, `log`
- Documentation: `markdown`, `html`, `css`
- Configuration: `ini`, `toml`, `conf`
- When in doubt: `text`

This rule is clear, actionable, and includes examples of both correct and incorrect usage. It fits well with your existing Ansible documentation standards and will prevent MD040 violations in any markdown files Claude creates for you.

---
