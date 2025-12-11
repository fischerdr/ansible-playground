# GitHub Copilot Instructions - Ansible Enterprise Automation

## Critical Rules (ALWAYS Follow)

### Ansible Syntax Requirements

1. **YAML Document Marker**: ALWAYS start playbooks/role files with `---` on line 1
2. **YAML Document End Marker**: OPTIONAL end with `...` on last line
3. **YAML Document End**: ALWAYS end YAML documents with a newline
4. **FQCN Required**: Use fully qualified collection names (FQCN) for all modules
   - Example: `ansible.builtin.copy` NOT `copy`
5. **Booleans**: Use lowercase `true`/`false` only (NOT `True`/`False`/`yes`/`no`)
6. **Multi-line Strings**: Use `|-` (literal, strip trailing newlines) or `>-` (folded, strip trailing newlines)
   - Complex Jinja2 lookups (>100 chars): Use `>-` with structured formatting
   - Break lookup parameters across lines for readability
7. **Security**: Always use `no_log: true` for tokens/passwords/credentials
8. **Error Handling**: Use `block`/`rescue`/`always` for critical operations
9. **Idempotency**: Avoid `shell`/`command` modules - prefer built-in modules when possible

### Python Standards

1. **Version**: Python 3.11+ only (required for AAP EE compatibility)
2. **Imports**: Always include `from __future__ import annotations`
3. **Type Hints**: Required for all functions with proper typing
4. **Formatting**: Black formatter with 100 character line length
5. **Logging**: Use `logging` module, never `print()` statements
6. **Docstrings**: Google-style formatting for all functions and classes
7. **Error Handling**: Implement proper error handling with custom exceptions when needed

### Mandatory Local Virtual Environment

**CRITICAL**: All Python and Ansible commands must run using the project `.venv` at `/development/git/ansible-playground/.venv`

```bash
# Activate virtual environment
source .venv/bin/activate

# Verify correct Python interpreter
which python  # Should show: /development/git/ansible-playground/.venv/bin/python
```

**Always use `.venv/bin/` prefix for all commands:**

```bash
# Python commands
.venv/bin/python script.py
.venv/bin/pip install package

# Ansible commands
.venv/bin/ansible-playbook playbooks/site.yml
.venv/bin/ansible-galaxy collection install -r requirements.yml
.venv/bin/ansible-lint

# Linting and formatting tools
.venv/bin/black .
.venv/bin/isort .
.venv/bin/flake8 .
.venv/bin/mypy .
```

### Execution Environment and Platform Constraints

- **Execution Environment**: All automation executes inside AAP Execution Environments
- **Base Image**: CentOS Stream 9 with Python 3.11
- **Container Runtime**: Podman required for EE builds
- **Python Version**: Python 3.11+ mandatory for modern EE compatibility
- **Dependencies**: All dependencies must be declared in `requirements.txt` and `requirements.yml` for reproducibility
- **Isolation**: EE isolation must be considered in all automation decisions

## Code Templates and Examples

### Ansible Task with Error Handling

```yaml
---
- name: Example play using robust error handling
  hosts: all
  gather_facts: false

  tasks:
    - name: Descriptive task name
      block:
        - name: Main operation
          ansible.builtin.copy:
            src: "{{ source }}"
            dest: "{{ dest }}"
          register: _copy_result
          no_log: true

        - name: Verify result
          ansible.builtin.assert:
            that:
              - _copy_result is defined
              - _copy_result is succeeded
            fail_msg: "Copy operation failed"
          no_log: true

      rescue:
        - name: Handle error
          ansible.builtin.debug:
            msg: >-
              Error during copy operation: {{
                ansible_failed_result.msg | default('unknown error')
              }}
          no_log: true

        - name: Fail with clear message
          ansible.builtin.fail:
            msg: "Critical operation failed - aborting"

      always:
        - name: Cleanup temporary file if present
          ansible.builtin.file:
            path: "{{ temp_file }}"
            state: absent
          when: temp_file is defined
          no_log: true
```

### Custom Ansible Module Template

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Your Organization
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: module_name
short_description: Brief description of what module does
version_added: "1.0.0"
description:
  - Detailed description of module functionality
  - Additional details about usage
options:
  name:
    description:
      - Name parameter description
      - Additional details if needed
    required: true
    type: str
  state:
    description:
      - Desired state of the resource
    choices: [ present, absent ]
    default: present
    type: str
author:
  - Your Name (@github_username)
"""

EXAMPLES = r"""
- name: Example usage
  module_name:
    name: example
    state: present
"""

RETURN = r"""
msg:
  description: Operation result message
  returned: always
  type: str
  sample: "Operation completed successfully"
changed:
  description: Whether the module made changes
  returned: always
  type: bool
  sample: true
"""

from typing import Any, Dict

from ansible.module_utils.basic import AnsibleModule


def run_module() -> None:
    """Main module execution function."""
    module_args: Dict[str, Any] = {
        "name": {"type": "str", "required": True},
        "state": {"type": "str", "default": "present", "choices": ["present", "absent"]},
    }

    result: Dict[str, Any] = {"changed": False, "msg": ""}

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        # Extract parameters
        name = module.params["name"]
        state = module.params["state"]

        # Check mode support
        if module.check_mode:
            result["msg"] = f"Would process {name} with state {state}"
            module.exit_json(**result)

        # Main logic here
        result["changed"] = True
        result["msg"] = "Operation completed successfully"

        module.exit_json(**result)

    except Exception as exc:
        module.fail_json(msg=f"Module execution failed: {exc}", **result)


def main() -> None:
    """Module entry point."""
    run_module()


if __name__ == "__main__":
    main()
```

### Variable Validation

```yaml
- name: Validate required variables
  ansible.builtin.assert:
    that:
      - required_var is defined
      - required_var | length > 0
      - required_var is string
    fail_msg: "Variable 'required_var' must be defined as non-empty string"
    success_msg: "Variable validation passed"
```

### Sensitive Operations with API

```yaml
- name: Authenticate to API
  ansible.builtin.uri:
    url: "{{ api_url }}/login"
    method: POST
    body_format: json
    body:
      username: "{{ vault_username }}"
      password: "{{ vault_password }}"
    validate_certs: true
    status_code: [200, 201]
  register: _auth_result
  no_log: true

- name: Use authentication token
  ansible.builtin.uri:
    url: "{{ api_url }}/resource"
    method: GET
    headers:
      Authorization: "Bearer {{ _auth_result.json.token }}"
    validate_certs: true
  register: _resource_data
  no_log: true
```

## Shell vs Command Module - Critical Guidance

### Rule of Thumb

- Use `ansible.builtin.command` for single commands that do **not** require shell features
  - No pipes, redirects, wildcards, command chaining, or shell built-ins
- Use `ansible.builtin.shell` **when shell interpretation is required**
  - Pipes `|`, redirects `>`, globbing `*`, command chaining `&&`/`||`
  - Shell built-ins such as `set -o pipefail`, variable expansion, or here-docs
- When using `ansible.builtin.shell` in Execution Environments, always set `args: executable: /bin/bash` if you rely on bash features
- Ensure every task that runs shell/command follows variable hygiene, idempotency checks, and `no_log` masking

## Proper Use of `changed_when` and `failed_when`

When using `shell` or `command` modules, **always** define `changed_when` and `failed_when` to enforce idempotency and predictable error handling.

### Principles

- **`changed_when`** controls whether a task reports a change
  - Read/query operations: `changed_when: false`
  - State-modifying operations: detect change by testing `stdout`, `stdout_lines`, or other reliable indicators
  - Use negative indicators (empty output) when absence of output means an unusual or changed state

- **`failed_when`** controls when a task reports failure
  - Consider valid exit codes for the command (e.g., `grep` returns `1` for no matches)
  - For commands retried with `until`, prefer `until` to drive retries; reserve `failed_when` for unrecoverable conditions
  - When appropriate, test both `rc` and output content (e.g., `rc != 0 or 'error' in stderr | lower`)

- **Mask output**: per enterprise no_log policy, set `no_log: true` for tasks that may reveal runtime data

- **Variable hygiene**: register results to intermediate variables prefixed with `_` (e.g., `_pod_list`) to avoid global namespace pollution

### Common Patterns

**Read/query operation (never reports change):**

```yaml
- name: Get list of pods
  ansible.builtin.shell: kubectl get pods --no-headers -n "{{ px_namespace }}"
  register: _pod_list
  changed_when: false
  failed_when: _pod_list.rc != 0
  no_log: true
```

**Grep or pipeline where `grep` returning 1 is acceptable:**

```yaml
- name: Find worker machinesets
  ansible.builtin.shell: |
    set -o pipefail &&
    oc get machineset --no-headers -n "{{ px_namespace }}" | grep worker
  args:
    executable: /bin/bash
  register: _machineset_list
  changed_when: false
  failed_when: _machineset_list.rc not in [0, 1]
  no_log: true
```

**State-modifying operation - detect actual changes from stdout:**

```yaml
- name: Apply configuration
  ansible.builtin.shell: kubectl apply -f config.yaml -n "{{ px_namespace }}"
  register: _apply_result
  changed_when: >-
    'configured' in _apply_result.stdout or
    'created' in _apply_result.stdout or
    ('unchanged' not in _apply_result.stdout and _apply_result.rc == 0)
  failed_when: _apply_result.rc != 0
  no_log: true
```

**Operation where empty output indicates unexpected state:**

```yaml
- name: Verify cluster members exist
  ansible.builtin.shell: etcdctl member list
  register: _member_list
  changed_when: _member_list.stdout_lines | length == 0
  failed_when: _member_list.rc != 0
  no_log: true
```

**Retryable command with `until` (let `until` handle transient failures):**

```yaml
- name: Wait for pod ready
  ansible.builtin.shell: kubectl get pod mypod -n "{{ px_namespace }}" --no-headers
  register: _pod_check
  retries: 5
  delay: 10
  until: _pod_check.rc == 0 and ('Running' in _pod_check.stdout)
  changed_when: false
  failed_when: >-
    _pod_check.rc not in [0] and
    ('CrashLoopBackOff' in _pod_check.stdout or 'ImagePullBackOff' in _pod_check.stdout)
  no_log: true
```

### Quick Reference

- `changed_when: false` - For any read/query operation
- `changed_when: result.stdout_lines | length == 0` - Empty output signals unexpected change
- `changed_when: "'created' in result.stdout or 'configured' in result.stdout"` - Detect modification
- `failed_when: result.rc != 0` - Simple commands with single success rc
- `failed_when: result.rc not in [0, 1]` - grep and similar utilities where `1` is allowable
- `failed_when: result.rc != 0 or 'error' in (result.stderr | default('')) | lower` - Check both rc and textual error indicators

## HashiCorp Vault Integration

### Complex Lookup with Structured Format

```yaml
- name: Retrieve certificate from Vault
  ansible.builtin.set_fact:
    vault_crt: >-
      {{
        lookup(
          'community.hashi_vault.hashi_vault',
          'secret=static_secrets/data/env/' ~ cluster_user ~ '/vault:cert',
          'url=' ~ vault_address,
          'auth_method=token',
          'token=' ~ vault_token,
          'validate_certs=true',
          'namespace=mynamespace'
        ) | default('')
      }}
  no_log: true
```

### Module-based Vault Access

```yaml
- name: Retrieve secret from Vault
  community.hashi_vault.vault_kv2_get:
    url: "{{ vault_addr }}"
    path: "{{ secret_path }}"
    auth_method: token
    token: "{{ vault_token }}"
    validate_certs: true
  register: _vault_data
  no_log: true

- name: Use retrieved secret
  ansible.builtin.set_fact:
    db_password: "{{ _vault_data.secret.password }}"
  no_log: true
```

### Quick Vault Lookups Reference

**IMPORTANT**: These examples show patterns for retrieving secrets from Vault. Always customize paths, namespaces, and field names based on your Vault KV structure. Always use `no_log: true` with Vault operations.

#### Pattern 1: Simple Single-line Lookup (use for short paths)

```yaml
- name: Retrieve simple secret from Vault
  ansible.builtin.set_fact:
    my_secret: "{{ lookup('community.hashi_vault.hashi_vault', 'secret=path/to/secret:field url=' ~ vault_address ~ ' auth_method=token token=' ~ vault_token ~ ' validate_certs=true') | default('') }}"
  no_log: true
```

#### Pattern 2: Multi-line Structured Lookup (RECOMMENDED for complex paths)

```yaml
# Use >- block scalar for readability with complex paths and multiple parameters
# This is the preferred format for enterprise automation
- name: Retrieve certificate from Vault using structured lookup
  ansible.builtin.set_fact:
    cert_content: >-
      {{
        lookup(
          'community.hashi_vault.hashi_vault',
          'secret=' ~ vault_path_prefix ~ '/' ~ cluster_name ~ '/tls:certificate',
          'url=' ~ vault_address,
          'auth_method=token',
          'token=' ~ vault_token,
          'validate_certs=true',
          'namespace=' ~ vault_namespace
        ) | default('')
      }}
  no_log: true
```

#### Pattern 3: Variable-based Path Construction

```yaml
# Define reusable path components for consistency
- name: Set Vault path variables
  ansible.builtin.set_fact:
    vault_namespace: "{{ vault_vars.NAMESPACE | default('') }}"
    vault_path_prefix: "{{ vault_vars.PATH_PREFIX | default('kv/data/env') }}"
    vault_base_path: "{{ vault_path_prefix }}/{{ environment_name }}"
  no_log: true

# Use constructed paths in lookups
- name: Retrieve TLS certificate
  ansible.builtin.set_fact:
    tls_cert: >-
      {{
        lookup(
          'community.hashi_vault.hashi_vault',
          'secret=' ~ vault_base_path ~ '/tls:cert',
          'url=' ~ vault_address,
          'auth_method=token',
          'token=' ~ vault_token,
          'validate_certs=true',
          'namespace=' ~ vault_namespace
        ) | default('')
      }}
  no_log: true

- name: Retrieve TLS key
  ansible.builtin.set_fact:
    tls_key: >-
      {{
        lookup(
          'community.hashi_vault.hashi_vault',
          'secret=' ~ vault_base_path ~ '/tls:key',
          'url=' ~ vault_address,
          'auth_method=token',
          'token=' ~ vault_token,
          'validate_certs=true',
          'namespace=' ~ vault_namespace
        ) | default('')
      }}
  no_log: true

- name: Retrieve CA certificate
  ansible.builtin.set_fact:
    ca_cert: >-
      {{
        lookup(
          'community.hashi_vault.hashi_vault',
          'secret=' ~ vault_base_path ~ '/tls:ca_cert',
          'url=' ~ vault_address,
          'auth_method=token',
          'token=' ~ vault_token,
          'validate_certs=true',
          'namespace=' ~ vault_namespace
        ) | default('')
      }}
  no_log: true
```

#### Pattern 4: Retrieving Multiple Fields from Single Secret

```yaml
# Retrieve entire secret (all fields)
- name: Retrieve all credentials from single Vault secret
  ansible.builtin.set_fact:
    app_credentials: >-
      {{
        lookup(
          'community.hashi_vault.hashi_vault',
          'secret=' ~ vault_base_path ~ '/application',
          'url=' ~ vault_address,
          'auth_method=token',
          'token=' ~ vault_token,
          'validate_certs=true',
          'namespace=' ~ vault_namespace
        ) | default({})
      }}
  no_log: true

# Extract individual fields from retrieved secret
- name: Extract individual credential fields
  ansible.builtin.set_fact:
    app_username: "{{ app_credentials.username | default('') }}"
    app_password: "{{ app_credentials.password | default('') }}"
    app_api_key: "{{ app_credentials.api_key | default('') }}"
  no_log: true
```

#### Pattern 5: Conditional Path Based on Environment

```yaml
# Construct path dynamically based on environment/cluster type
- name: Retrieve environment-specific credentials
  ansible.builtin.set_fact:
    env_token: >-
      {{
        lookup(
          'community.hashi_vault.hashi_vault',
          'secret=kv/data/' ~ environment_type ~ '/' ~ application_name ~ ':access_token',
          'url=' ~ vault_address,
          'auth_method=token',
          'token=' ~ vault_token,
          'validate_certs=true',
          'namespace=' ~ vault_namespace
        ) | default('')
      }}
  no_log: true
  when: environment_type is defined
```

#### Pattern 6: Validate Secret Exists Before Use

```yaml
# Always validate critical secrets were retrieved successfully
- name: Retrieve API credentials from Vault
  block:
    - name: Retrieve API key
      ansible.builtin.set_fact:
        api_key: >-
          {{
            lookup(
              'community.hashi_vault.hashi_vault',
              'secret=' ~ vault_path_prefix ~ '/api:key',
              'url=' ~ vault_address,
              'auth_method=token',
              'token=' ~ vault_token,
              'validate_certs=true'
            ) | default('')
          }}
      no_log: true

    - name: Validate API key was retrieved
      ansible.builtin.assert:
        that:
          - api_key is defined
          - api_key | length > 0
        fail_msg: "Failed to retrieve API key from Vault at path {{ vault_path_prefix }}/api:key"
        success_msg: "API key retrieved successfully"
```

#### Vault Lookup Parameters Quick Reference

```yaml
# Parameter format for community.hashi_vault.hashi_vault lookup
# Customize based on your Vault configuration

# Required:
# - secret: 'secret=path/to/secret:fieldname' or 'secret=path/to/secret' (all fields)

# Connection (required):
# - url: Vault server URL

# Authentication (required - choose one method):
# - 'auth_method=token token=<token>'
# - 'auth_method=approle role_id=<id> secret_id=<id>'
# - 'auth_method=userpass username=<user> password=<pass>'

# Optional:
# - namespace: Vault namespace (Enterprise feature)
# - validate_certs: true/false (ALWAYS use true in production)

# Complete example:
- name: Example with all common parameters
  ansible.builtin.set_fact:
    my_value: >-
      {{
        lookup(
          'community.hashi_vault.hashi_vault',
          'secret=kv/data/mypath:fieldname',
          'url=https://vault.example.com:8200',
          'auth_method=token',
          'token=' ~ vault_token,
          'validate_certs=true',
          'namespace=myteam'
        ) | default('')
      }}
  no_log: true
```

#### Best Practices for Vault Lookups

1. **Always use `ansible.builtin.set_fact`** with `no_log: true` when retrieving secrets
2. **Always use `| default('')` or `| default({})`** to handle missing secrets gracefully
3. **Use structured format (`>-`)** for lookups with complex paths or multiple parameters (>100 chars)
4. **Define path components as variables** (prefixes, namespaces) for consistency
5. **Validate critical secrets exist** using `assert` before use in operations
6. **Use Vault namespaces** to isolate secrets by team/environment (Enterprise feature)
7. **Never hardcode Vault tokens** - source from AAP credentials or environment variables
8. **Use descriptive variable names** that indicate the secret type/purpose
9. **Group related Vault lookups** in a dedicated task file (e.g., `tasks/vault_secrets.yml`)

```yaml
# Example: Organized secret retrieval with validation
---
# File: roles/myapp/tasks/vault_secrets.yml
- name: Retrieve application secrets from Vault
  block:
    - name: Set Vault base path
      ansible.builtin.set_fact:
        vault_app_path: "{{ vault_path_prefix }}/{{ environment_name }}/{{ app_name }}"
      no_log: true

    - name: Retrieve database credentials
      ansible.builtin.set_fact:
        db_credentials: >-
          {{
            lookup(
              'community.hashi_vault.hashi_vault',
              'secret=' ~ vault_app_path ~ '/database',
              'url=' ~ vault_address,
              'auth_method=token',
              'token=' ~ vault_token,
              'validate_certs=true'
            ) | default({})
          }}
      no_log: true

    - name: Retrieve TLS certificates
      ansible.builtin.set_fact:
        tls_data: >-
          {{
            lookup(
              'community.hashi_vault.hashi_vault',
              'secret=' ~ vault_app_path ~ '/tls',
              'url=' ~ vault_address,
              'auth_method=token',
              'token=' ~ vault_token,
              'validate_certs=true'
            ) | default({})
          }}
      no_log: true

    - name: Validate all required secrets retrieved
      ansible.builtin.assert:
        that:
          - db_credentials is defined
          - db_credentials | length > 0
          - tls_data is defined
          - tls_data | length > 0
        fail_msg: "Failed to retrieve required secrets from Vault"
        success_msg: "All required secrets retrieved successfully"
```

## Common Use Cases

### Loop with Naming

```yaml
- name: Install required packages
  ansible.builtin.package:
    name: "{{ item }}"
    state: present
  loop:
    - git
    - curl
    - vim
  loop_control:
    label: "{{ item }}"
```

### Conditional Execution

```yaml
- name: Run only on production
  ansible.builtin.command: /usr/local/bin/deploy.sh
  when:
    - ansible_env.ENVIRONMENT == "production"
    - deploy_enabled | bool
  changed_when: false
```

### Handler Notification

```yaml
# In tasks/main.yml
- name: Update config file
  ansible.builtin.template:
    src: app.conf.j2
    dest: /etc/app/app.conf
    mode: '0644'
    owner: root
    group: root
  notify: Restart application

# In handlers/main.yml
- name: Restart application
  ansible.builtin.systemd:
    name: application
    state: restarted
    daemon_reload: true
```

### Package Installation (Multi-OS)

```yaml
- name: Install web server
  ansible.builtin.package:
    name: "{{ web_server_package }}"
    state: present
  vars:
    web_server_package: "{{ 'httpd' if ansible_os_family == 'RedHat' else 'apache2' }}"
```

### File Management with Template

```yaml
- name: Deploy application configuration
  ansible.builtin.template:
    src: templates/app_config.j2
    dest: /etc/myapp/config.yml
    owner: appuser
    group: appgroup
    mode: '0640'
    backup: true
    validate: /usr/local/bin/validate_config %s
  notify: Restart application service
```

### Multi-line Strings (Block Scalars)

```yaml
# Use |- for literal style (preserves newlines, strips trailing)
- name: Create script with multiple lines
  ansible.builtin.copy:
    dest: /usr/local/bin/deploy.sh
    mode: '0755'
    owner: root
    group: root
    content: |-
      #!/bin/bash
      set -euo pipefail

      echo "Starting deployment"
      systemctl restart myapp
      echo "Deployment complete"

# Use >- for folded style (joins lines, strips trailing)
- name: Display multi-line message
  ansible.builtin.debug:
    msg: >-
      This is a long message that spans multiple lines
      but will be folded into a single line in the output.
      Use this for long descriptions or messages.

# Use |- for shell commands
- name: Run multi-line shell script
  ansible.builtin.shell: |-
    if [ -f /etc/myapp/config ]; then
      echo "Config exists"
      cat /etc/myapp/config
    else
      echo "Config missing"
      exit 1
    fi
  register: _shell_result
  changed_when: false
```

## Testing Commands (Always via `.venv`)

### Syntax and Validation

```bash
# Activate virtual environment
source .venv/bin/activate

# Ansible syntax check
.venv/bin/ansible-playbook --syntax-check playbooks/site.yml

# Dry run (check mode)
.venv/bin/ansible-playbook --check playbooks/site.yml

# Ansible linting
.venv/bin/ansible-lint

# YAML linting
.venv/bin/yamllint .

# Run with increased verbosity
.venv/bin/ansible-playbook -vvv playbooks/site.yml
```

### Python Code Quality

```bash
# Format Python code (automatically fixes issues)
.venv/bin/black .

# Sort imports (automatically fixes issues)
.venv/bin/isort .

# Python linting (reports issues)
.venv/bin/flake8 .

# Type checking (reports type issues)
.venv/bin/mypy .

# Run tests
.venv/bin/pytest
```

### Testing Workflow for Roles

1. **Syntax validation**: `.venv/bin/ansible-playbook --syntax-check playbooks/<playbook>.yml`
2. **Ansible-lint**: `.venv/bin/ansible-lint roles/<role-name>/`
3. **Tag-based testing**: Test individual phases using `--tags`

   ```bash
   .venv/bin/ansible-playbook playbooks/px_upgrade.yml --tags preflight --check
   ```

4. **Dry-run mode**: Use `--check` to validate without changes
5. **Test environment**: Run against dev/test cluster first
6. **Production validation**: Final testing in production-like environment

## Top Anti-Patterns (NEVER Do)

| Anti-Pattern | Correct Approach |
|--------------|------------------|
| `copy:` | `ansible.builtin.copy:` |
| `yes`/`no` | `true`/`false` |
| Logging secrets | `no_log: true` |
| `shell: echo {{ var }}` | `ansible.builtin.debug: msg="{{ var }}"` |
| Hardcoded values | Variables in `group_vars/` or `defaults/` |
| No error handling | `block`/`rescue`/`always` |
| `with_items:` | `loop:` |
| Missing type hints in Python | Type hints on all functions |
| `print()` statements | `logging.info()` |
| Python 3.9 | Python 3.11+ |
| Short module names | FQCN (Fully Qualified Collection Names) |
| Logging runtime data | `no_log: true` even for non-sensitive data |
| Using `shell` unnecessarily | Prefer built-in modules |
| Missing `changed_when`/`failed_when` | Always define for `shell`/`command` |
| Global `python`/`ansible-playbook` | Always use `.venv/bin/` prefix |

## Quick File Locations

```text
roles/[role_name]/
  ├── tasks/main.yml         # Entry point for role tasks
  ├── handlers/main.yml      # Service restarts and notifications
  ├── defaults/main.yml      # Default variables (lowest precedence)
  ├── vars/main.yml          # Role variables (higher precedence)
  ├── templates/*.j2         # Jinja2 templates
  ├── files/                 # Static files to copy
  ├── library/*.py           # Custom modules
  ├── filter_plugins/*.py    # Custom Jinja2 filters
  └── meta/main.yml          # Role dependencies and metadata

inventory/
  ├── group_vars/all/
  │   ├── vars.yml           # Common variables
  │   └── vault.yml          # Encrypted secrets (Ansible Vault)
  ├── host_vars/             # Host-specific variables
  └── hosts.yml              # Inventory definition

playbooks/                   # Orchestration playbooks
Build-EE/                    # Execution environment configuration
collections/                 # Local Ansible collections
```

## Commonly Used Collections

- `ansible.builtin.*` - Core Ansible modules (always use FQCN)
- `ansible.posix.*` - POSIX system utilities (file, mount, selinux)
- `community.general.*` - General purpose modules
- `community.hashi_vault.*` - HashiCorp Vault integration
- `kubernetes.core.*` - Kubernetes/OpenShift management
- `amazon.aws.*` - AWS cloud resources
- `community.docker.*` - Docker container management
- `purepx.px_backup.*` - Portworx backup operations

## Security Checklist

Before suggesting or implementing code, verify:

- [ ] No secrets in plain text (use Ansible Vault)
- [ ] `no_log: true` on sensitive tasks and even non-sensitive tasks per enterprise policy
- [ ] `validate_certs: true` for all HTTPS connections
- [ ] Input validation with `assert` for all required variables
- [ ] Proper `become` usage (minimal privilege escalation)
- [ ] Error messages don't leak sensitive information
- [ ] Variables from Vault or EE environment variables (never hardcoded)
- [ ] Proper privilege escalation only when necessary

## Additional Operational Notes

- **Explicit executables**: When using shell features that require bash, always set `args: executable: /bin/bash`
- **Secrets and variables**: Source variables from Vault or EE environment variables - never hardcode secrets
- **Idempotency**: Prefer module implementations when possible (e.g., `kubernetes.core.k8s`, `openshift` modules)
- **Linting and auditing**: Ensure playbooks conform to ansible-lint rules; document any justified exceptions
- **No unescaped Jinja in shell**: Construct command arguments via `args:` or safely templated variables
- **Variable naming**: Use descriptive names; prefix internal variables with `_` to avoid namespace pollution
- **Check mode support**: Design tasks to work with `--check` mode when possible

## Communication Style

- Professional, formal tone appropriate for enterprise environment
- No emojis or icons in code, comments, or documentation
- Emphasize maintainability, security, and operational soundness
- Clear documentation for all complex logic
- Focus on reliability and reproducibility

## Role and Playbook Structure Best Practices

### Variables

- Define required variables at the start of playbooks
- Use `assert` tasks to validate required variables
- Document optional variables with default values in `defaults/main.yml`
- Follow proper variable scoping (host_vars, group_vars, playbook vars)
- Use consistent naming conventions (snake_case)

### Error Handling

- Use `block`/`rescue`/`always` for critical operations
- Provide clear, actionable error messages
- Register results for important operations
- Never ignore errors without explicit justification and documentation

### Idempotency

- Design all tasks to be idempotent (safe to run multiple times)
- Use `changed_when` and `failed_when` directives appropriately
- Avoid `shell` and `command` modules unless absolutely necessary
- Prefer Ansible's built-in modules for specific tasks

### Task Organization

- Use meaningful play and task names that describe the action
- Group related tasks logically
- Use tags for selective execution
- Include clear description comment blocks at the start of playbooks

## Git Workflow (Reference Only)

### Commit Messages

- Use conventional commit format: `<type>(<scope>): <subject>`
- Types: feat, fix, docs, style, refactor, test, chore
- Include issue reference when applicable (fixes #123)
- Focus on the "why" rather than the "what"
- Match repository's existing commit style

### Branching Strategy

- Main branch contains stable, production-ready code
- Feature branches for new development work
- Pull requests must include automated testing results before merging
- All changes must pass linting and unit tests

---

**Note**: These instructions follow enterprise Ansible best practices for Ansible Automation Platform deployments. All code runs inside Execution Environments with Python 3.11+. Customize as needed for specific project requirements while maintaining security and quality standards.
