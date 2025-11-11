# GitHub Copilot Quick Reference - Ansible Enterprise Automation

## Critical Rules (ALWAYS Follow)

### Ansible Syntax
1. **FQCN Required**: `ansible.builtin.copy` NOT `copy`
2. **Booleans**: `true`/`false` NOT `True`/`False`/`yes`/`no`
3. **Multi-line Strings**: Use `|-` (literal, strip trailing newlines) or `>-` (folded, strip trailing newlines)
4. **Security**: `no_log: true` for tokens/passwords/credentials
5. **Error Handling**: Use `block`/`rescue`/`always` for critical operations
6. **Idempotency**: Avoid `shell`/`command` - use built-in modules

### Python Standards
1. **Version**: Python 3.11+ only
2. **Imports**: `from __future__ import annotations`
3. **Type Hints**: Required for all functions
4. **Formatting**: Black (100 char line length)
5. **Logging**: Use `logging` module, never `print()`

### Platform Constraints
- **Execution Environment**: All code runs in Ansible Automation Platform (AAP) Execution Environments
- **Python Version**: Target Python 3.11+ for modern EE compatibility
- **All dependencies**: Must be declared in requirements.txt/requirements.yml for reproducibility

## Essential Code Templates

### Ansible Task with Error Handling
```yaml
- name: Descriptive task name
  block:
    - name: Main operation
      ansible.builtin.copy:
        src: "{{ source }}"
        dest: "{{ dest }}"
      register: result

    - name: Verify result
      ansible.builtin.assert:
        that: result.changed
        fail_msg: "Operation failed"

  rescue:
    - name: Handle error
      ansible.builtin.debug:
        msg: "Error: {{ ansible_failed_result.msg }}"

  always:
    - name: Cleanup
      ansible.builtin.file:
        path: "{{ temp_file }}"
        state: absent
```

### Custom Ansible Module
```python
#!/usr/bin/python
from __future__ import annotations

DOCUMENTATION = r"""
module: module_name
short_description: What it does
options:
    name:
        description: Parameter description
        required: true
        type: str
"""

from ansible.module_utils.basic import AnsibleModule

def run_module() -> None:
    module_args = {"name": {"type": "str", "required": True}}
    result = {"changed": False, "msg": ""}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        # Logic here
        result["changed"] = True
        module.exit_json(**result)
    except Exception as e:
        module.fail_json(msg=f"Failed: {str(e)}", **result)

def main() -> None:
    run_module()

if __name__ == "__main__":
    main()
```

### Sensitive Operations
```yaml
- name: Authenticate to API
  ansible.builtin.uri:
    url: "{{ api_url }}/login"
    method: POST
    body_format: json
    body:
      token: "{{ vault_api_token }}"
    validate_certs: true
  register: auth_result
  no_log: true  # CRITICAL - never log credentials
```

### Variable Validation
```yaml
- name: Validate required variables
  ansible.builtin.assert:
    that:
      - required_var is defined
      - required_var | length > 0
      - required_var is string
    fail_msg: "Variable 'required_var' must be defined, non-empty string"
```

## Top Anti-Patterns (NEVER Do)

1. ❌ `copy:` → ✅ `ansible.builtin.copy:`
2. ❌ `yes/no` → ✅ `true/false`
3. ❌ Logging secrets → ✅ `no_log: true`
4. ❌ `shell: echo {{ var }}` → ✅ `ansible.builtin.debug: msg="{{ var }}"`
5. ❌ Hardcoded values → ✅ Variables in `group_vars/`
6. ❌ No error handling → ✅ `block`/`rescue`/`always`
7. ❌ `with_items:` → ✅ `loop:`
8. ❌ Missing type hints → ✅ Type hints on all functions
9. ❌ `print()` statements → ✅ `logging.info()`
10. ❌ Python 3.9 → ✅ Python 3.11+

## Quick File Locations

```
roles/[role_name]/
  ├── tasks/main.yml         # Entry point
  ├── handlers/main.yml      # Service restarts
  ├── defaults/main.yml      # Default variables
  ├── templates/*.j2         # Jinja2 templates
  ├── library/*.py           # Custom modules
  └── meta/main.yml          # Dependencies

inventory/
  ├── group_vars/all/
  │   ├── vars.yml           # Common variables
  │   └── vault.yml          # Encrypted secrets
  └── host_vars/             # Host-specific vars

playbooks/                   # Orchestration
```

## Commonly Used Collections

- `ansible.builtin.*` - Core Ansible modules (always use FQCN)
- `ansible.posix.*` - POSIX system utilities
- `community.general.*` - General purpose modules
- `community.hashi_vault.*` - HashiCorp Vault integration
- `kubernetes.core.*` - Kubernetes/OpenShift management
- `amazon.aws.*` - AWS cloud resources
- `community.docker.*` - Docker container management

## Communication Style

- Professional, formal tone for enterprise environment
- No emojis or icons in code/comments
- Emphasize maintainability and security
- Clear documentation for all complex logic

## Testing Commands

```bash
# Syntax check
ansible-playbook --syntax-check playbook.yml

# Dry run
ansible-playbook --check playbook.yml

# Linting
ansible-lint
yamllint .
black .
flake8 .
mypy .

# Run with verbosity
ansible-playbook -vvv playbook.yml
```

## Security Checklist

Before suggesting code, verify:
- [ ] No secrets in plain text (use Ansible Vault)
- [ ] `no_log: true` on sensitive tasks
- [ ] `validate_certs: true` for HTTPS
- [ ] Input validation with `assert`
- [ ] Proper `become` usage (minimal privilege)
- [ ] Error messages don't leak sensitive info

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
```

### Handler Notification
```yaml
# In tasks/main.yml
- name: Update config file
  ansible.builtin.template:
    src: app.conf.j2
    dest: /etc/app/app.conf
  notify: Restart application

# In handlers/main.yml
- name: Restart application
  ansible.builtin.systemd:
    name: application
    state: restarted
```

### HashiCorp Vault Integration
```yaml
- name: Retrieve from vault using lookup
  ansible.builtin.set_fact:
    vault_crt: "{{ lookup('community.hashi_vault.hashi_vault', 'secret=static_secrets/data/env/' ~ cluster_user ~ '/vault url=' ~ vault_address ~ ' auth_method=token token=' ~ vault_token ~ ' validate_certs=true namespace=mynamespace') | default('') }}"

- name: Retrieve secret from Vault
  community.hashi_vault.vault_kv2_get:
    url: "{{ vault_addr }}"
    path: "{{ secret_path }}"
    auth_method: token
    token: "{{ vault_token }}"
  register: vault_data
  no_log: true

- name: Use retrieved secret
  ansible.builtin.set_fact:
    db_password: "{{ vault_data.secret.password }}"
  no_log: true
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
  notify: Restart application service
```

### Multi-line Strings (Block Scalars)
```yaml
# Use |- for literal style (preserves newlines, strips trailing)
- name: Create script with multiple lines
  ansible.builtin.copy:
    dest: /usr/local/bin/deploy.sh
    mode: '0755'
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
  register: shell_result
```

---

**Note**: These instructions are generic Ansible best practices. Customize for your specific project needs.
