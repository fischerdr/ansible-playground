# Copilot Instructions for Ansible Automation Projects

This file provides comprehensive instructions to GitHub Copilot when working with Ansible automation code.

## Project Context

You are assisting an Automation Engineer working with Ansible to build infrastructure automation, configuration management, and application deployment solutions.

### Technology Stack

- **Ansible Core:** 2.15+ (modern Ansible practices)
- **Python:** 3.9+ (target 3.11+ for best compatibility)
- **Platform:** Ansible Automation Platform (AAP) with Execution Environments (optional: can also run standalone)
- **Common Technologies:** Linux systems, cloud platforms, container platforms, configuration management

### Platform Considerations

- When using Execution Environments (EE), all playbooks run in containerized environments
- EE isolation should be considered in automation decisions when applicable
- All dependencies should be declared in requirements files for reproducibility
- Support both traditional Ansible deployments and modern AAP/EE architectures

## Code Generation Standards

### Ansible Playbook Requirements

When generating Ansible playbooks or tasks:

1. **YAML Document Marker (CRITICAL)**
   - **ALWAYS** start YAML files with `---` on the first line
   - This is the YAML document start marker and is required for Ansible
   - Never omit or remove this marker
   - Example:
     ```yaml
     ---
     - name: My playbook
       hosts: all
     ```

2. **FQCN Usage (Required)**
   - Always use Fully Qualified Collection Names for all modules
   - Example: `ansible.builtin.copy` not `copy`
   - Example: `kubernetes.core.k8s` not `k8s`

3. **Boolean Values**
   - Use lowercase `true` and `false` for boolean values
   - Never use `True`, `False`, `yes`, `no`, `on`, or `off`

4. **Multi-line Strings (Block Scalars)**
   - Use `|-` (literal block scalar, strip trailing newlines) for preserving line breaks
   - Use `>-` (folded block scalar, strip trailing newlines) for long text that should wrap
   - Always use block scalars for shell commands, scripts, and multi-line content
   - **Complex Jinja2 Expressions (>100 characters):**
     - Use `>-` with structured formatting
     - Break lookup/filter parameters across lines
     - Indent for readability: opening `{{`, function/parameters, filters, closing `}}`
   - Examples:
     - Scripts and commands: `content: |-` or `shell: |-`
     - Long descriptions: `msg: >-`
     - YAML/JSON content: `content: |-`
     - Complex lookups: `value: >-` with multi-line Jinja2

5. **Documentation**
   - Include clear description comment block at the start of every playbook
   - Use meaningful play and task names that describe the purpose
   - Document required and optional variables
   - Add comments for complex operations

6. **Variable Management**
   - Define required variables at the start of the playbook
   - Use `assert` tasks to validate required variables
   - Document optional variables with default values
   - Use proper variable scoping (host_vars, group_vars, playbook vars)
   - Follow variable precedence order: extra vars > command line > role vars > include vars > block vars > task vars > role defaults > inventory vars

5. **Task Organization**
   - Group related tasks in `block` directives
   - Use `rescue` and `always` blocks for error handling
   - Register results for important operations
   - Use proper task delegation when needed
   - Organize long task lists using `include_tasks`

6. **Security Requirements**
   - Use `no_log: true` for sensitive operations (tokens, credentials, passwords)
   - Never log sensitive information
   - Use `validate_certs: true` for HTTPS operations
   - Validate all external input using `assert` module
   - Implement proper privilege escalation with `become` only when necessary
   - Use Ansible Vault for encrypting sensitive data

7. **Idempotency**
   - Design all tasks to be idempotent
   - Use `changed_when` and `failed_when` directives appropriately
   - Avoid `shell` and `command` modules unless absolutely necessary
   - Prefer Ansible's built-in modules for specific tasks

8. **Error Handling**
   - Use `block`/`rescue`/`always` for error handling
   - Provide clear error messages
   - Register results for important operations
   - Never ignore errors without explicit justification
   - Implement rollback mechanisms when appropriate

9. **Performance Optimization**
   - Avoid loops when modules can handle lists (e.g., `yum` module with multiple packages)
   - Use async tasks for long-running operations
   - Minimize fact gathering when not needed
   - Use `loop` keyword instead of deprecated `with_items`
   - Always name loops for better task identification

### Python Module Standards

When generating custom Ansible modules or Python code:

1. **Python Version**
   - Target Python 3.11+ syntax
   - Use `from __future__ import annotations` for type hints

2. **Code Style**
   - Follow PEP 8 style guide
   - Use `black` for formatting (line length: 100 characters)
   - Use `isort` for import sorting
   - Type hints required for all functions
   - Comprehensive docstrings required

3. **Import Organization**
   ```python
   # Standard library imports
   from __future__ import annotations
   import os
   import sys

   # Third-party imports
   import requests
   from ansible.module_utils.basic import AnsibleModule

   # Local imports
   from . import helper_functions
   ```

4. **Ansible Module Requirements**
   - Include proper `DOCUMENTATION`, `EXAMPLES`, and `RETURN` strings
   - Use `argument_spec` for parameter validation
   - Return proper values: `changed`, `failed`, `msg`, `original_message`
   - Implement proper error handling with try/except blocks
   - Use `module.fail_json()` for error conditions
   - Use `module.exit_json()` for success conditions

5. **Logging**
   - Always use the `logging` module for tracking progress and errors
   - Never use `print()` statements in production code
   - Configure appropriate log levels

### Standard Ansible Directory Structure

When suggesting file locations or creating new files, follow this standard structure:

```
ansible-project/
├── roles/                    # Reusable Ansible roles
│   └── [role_name]/
│       ├── tasks/           # Role tasks (main.yml is entry point)
│       │   └── main.yml
│       ├── handlers/        # Event-driven tasks (service restarts, etc.)
│       │   └── main.yml
│       ├── defaults/        # Default variables (lowest precedence)
│       │   └── main.yml
│       ├── vars/            # Role-specific variables (higher precedence)
│       │   └── main.yml
│       ├── templates/       # Jinja2 templates (*.j2 extension)
│       ├── files/           # Static files to be copied
│       ├── library/         # Custom Ansible modules (*.py)
│       ├── filter_plugins/  # Custom Jinja2 filters
│       ├── lookup_plugins/  # Custom lookup plugins
│       ├── module_utils/    # Shared code for custom modules
│       ├── tests/           # Test playbooks and inventories
│       └── meta/            # Role metadata and dependencies
│           └── main.yml
├── playbooks/               # Orchestration playbooks
│   ├── site.yml            # Main playbook (entry point)
│   └── [component].yml     # Component-specific playbooks
├── inventory/               # Inventory files
│   ├── production/         # Production environment
│   │   ├── hosts.yml
│   │   ├── group_vars/
│   │   └── host_vars/
│   ├── staging/            # Staging environment
│   └── development/        # Development environment
├── group_vars/             # Group variables (alternative location)
│   └── all/
│       ├── vars.yml        # Common variables
│       └── vault.yml       # Encrypted secrets
├── host_vars/              # Host-specific variables
├── collections/            # Local Ansible collections (optional)
├── library/                # Project-level custom modules (optional)
├── filter_plugins/         # Project-level custom filters (optional)
├── ansible.cfg             # Ansible configuration
├── requirements.yml        # Ansible Galaxy requirements
└── requirements.txt        # Python dependencies (for EE or modules)
```

## Common Patterns to Follow

### Recommended Task Pattern

```yaml
---
- name: Clear, descriptive play name
  hosts: all
  gather_facts: true
  vars:
    required_var_1: value
    optional_var_2: "{{ lookup('env', 'ENV_VAR') | default('default_value') }}"

  tasks:
    - name: Validate required variables
      ansible.builtin.assert:
        that:
          - required_var_1 is defined
          - required_var_1 | length > 0
        fail_msg: "Required variable 'required_var_1' must be defined and non-empty"

    - name: Execute main operation
      block:
        - name: Perform operation
          ansible.builtin.copy:
            src: "{{ source_file }}"
            dest: "{{ dest_file }}"
            mode: '0644'
          register: copy_result

        - name: Verify operation
          ansible.builtin.assert:
            that:
              - copy_result.changed
            fail_msg: "Copy operation did not change anything"

      rescue:
        - name: Handle error gracefully
          ansible.builtin.debug:
            msg: "Operation failed: {{ ansible_failed_result.msg }}"

        - name: Set failure flag
          ansible.builtin.set_fact:
            operation_failed: true

      always:
        - name: Cleanup temporary files
          ansible.builtin.file:
            path: "{{ temp_file }}"
            state: absent
```

### Recommended Custom Module Pattern

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import annotations

DOCUMENTATION = r"""
---
module: my_custom_module
short_description: Brief description of what this module does
version_added: "1.0.0"
description:
    - Detailed description of the module's functionality
    - Multiple lines are supported
options:
    name:
        description:
            - The name parameter description
        required: true
        type: str
    state:
        description:
            - Desired state of the resource
        required: false
        type: str
        default: present
        choices: ['present', 'absent']
author:
    - Your Name (@github_handle)
"""

EXAMPLES = r"""
- name: Example task using this module
  my_custom_module:
    name: example
    state: present
"""

RETURN = r"""
changed:
    description: Whether the module made changes
    type: bool
    returned: always
msg:
    description: Human-readable message about what happened
    type: str
    returned: always
"""

from ansible.module_utils.basic import AnsibleModule


def run_module() -> None:
    """Main module execution function."""
    module_args = {
        "name": {"type": "str", "required": True},
        "state": {
            "type": "str",
            "required": False,
            "default": "present",
            "choices": ["present", "absent"],
        },
    }

    result = {
        "changed": False,
        "msg": "",
    }

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        # Module logic here
        result["changed"] = True
        result["msg"] = "Operation completed successfully"
        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=f"Module execution failed: {str(e)}", **result)


def main() -> None:
    """Entry point for the module."""
    run_module()


if __name__ == "__main__":
    main()
```

## Anti-patterns to Avoid

When generating code, avoid these common mistakes:

1. **Shell and Command Modules**
   - Don't suggest `shell` or `command` modules unless absolutely necessary
   - Prefer built-in modules for idempotency and better error handling
   - When using `shell`/`command`, always use `|-` for multi-line commands

2. **Hardcoded Values**
   - Don't hardcode values in playbooks or roles
   - Use variables in `group_vars/` and `host_vars/`

3. **Inconsistent Naming**
   - Follow consistent naming: lowercase with underscores for roles, playbooks, variables
   - Use descriptive names: `deploy_application` not `deploy_app`

4. **Missing Security Considerations**
   - Never generate code that logs sensitive information
   - Always suggest `no_log: true` for sensitive tasks
   - Don't store secrets in plain text

5. **Lack of Error Handling**
   - Don't generate tasks without proper error handling
   - Always include `block`/`rescue`/`always` for critical operations

6. **Poor Idempotency**
   - Don't create tasks that can't be run multiple times safely
   - Always consider the end state, not just the actions

7. **Complex Templates**
   - Don't create overly complex Jinja2 templates
   - Keep logic simple and readable

8. **Improper Multi-line Syntax**
   - Don't use quoted strings for multi-line content
   - Always use `|-` or `>-` block scalars for multi-line strings
   - Never use `\n` escape sequences in YAML strings
   - Don't write complex Jinja2 expressions (>100 chars) on a single line
   - Break lookup parameters across lines for readability

9. **Ignoring EE Constraints**
   - Don't suggest solutions that bypass Execution Environment isolation
   - All dependencies must be in requirements files

## Testing and Quality

When suggesting test code:

1. **Molecule Testing**
   - Suggest Molecule for role testing
   - Include idempotency checks
   - Use Testinfra or Goss for verification

2. **Linting**
   - Code should pass `ansible-lint` without errors
   - Python code should pass `flake8`, `black`, and `mypy`
   - YAML should pass `yamllint`

3. **Syntax Validation**
   - Suggest running `ansible-playbook --syntax-check`
   - Include dry-run examples with `--check` flag

## Communication Style

When providing explanations or comments:

- Use formal, professional tone appropriate for enterprise environments
- Produce output in Markdown format without icons or emojis
- Emphasize maintainability, clarity, and operational soundness
- Focus on enterprise-scale considerations and best practices
- Provide clear rationale for architectural decisions

## Example Scenarios

### Scenario 1: Creating a New Role

When asked to create a new role, structure it as:

```
roles/new_role/
├── tasks/
│   └── main.yml              # Entry point with include_tasks
├── handlers/
│   └── main.yml              # Service restart handlers
├── defaults/
│   └── main.yml              # Default variables
├── vars/
│   └── main.yml              # Role-specific variables
├── templates/
│   └── config.j2             # Configuration templates
├── files/
│   └── static_file.conf      # Static files
├── meta/
│   └── main.yml              # Dependencies and metadata
└── README.md                  # Role documentation
```

### Scenario 2: Custom Module Integration

When creating a custom module:

1. Place it in `roles/[role_name]/library/module_name.py`
2. Follow the custom module pattern above
3. Include comprehensive documentation strings
4. Add example usage in role's README.md
5. Ensure proper argument_spec and return values

### Scenario 3: Vault Integration

When working with secrets:

```yaml
# In group_vars/all/vault.yml (encrypted)
vault_api_token: "secret_token_here"
vault_password: "secret_password_here"

# In tasks/main.yml
- name: Authenticate to API
  ansible.builtin.uri:
    url: https://api.example.com/login
    method: POST
    body_format: json
    body:
      token: "{{ vault_api_token }}"
    validate_certs: true
  register: auth_result
  no_log: true  # Critical for security
```

### Scenario 4: Multi-line Content

When creating files with multi-line content:

```yaml
# Shell scripts - use |- for literal content
- name: Create deployment script
  ansible.builtin.copy:
    dest: /usr/local/bin/app-deploy.sh
    mode: '0755'
    owner: root
    group: root
    content: |-
      #!/bin/bash
      set -euo pipefail

      # Deploy application
      echo "Starting deployment at $(date)"
      cd /opt/myapp
      git pull origin main
      systemctl restart myapp
      echo "Deployment complete"

# Configuration files - use |- for YAML/JSON/structured content
- name: Create application config
  ansible.builtin.copy:
    dest: /etc/myapp/config.yml
    mode: '0640'
    owner: myapp
    group: myapp
    content: |-
      ---
      database:
        host: "{{ db_host }}"
        port: {{ db_port }}
        name: "{{ db_name }}"

      logging:
        level: info
        file: /var/log/myapp/app.log

# Long messages/descriptions - use >- for folded text
- name: Display installation instructions
  ansible.builtin.debug:
    msg: >-
      The application has been successfully installed.
      Please review the configuration file at /etc/myapp/config.yml
      and ensure all database connection settings are correct
      before starting the service.

# Multi-line shell commands - use |-
- name: Execute complex shell command
  ansible.builtin.shell: |-
    set -e
    if systemctl is-active --quiet myapp; then
      echo "Service is running"
      systemctl status myapp
    else
      echo "Service is not running"
      exit 1
    fi
  register: service_check
  changed_when: false

# SQL scripts - use |-
- name: Execute SQL migration
  community.postgresql.postgresql_query:
    db: myapp_db
    query: |-
      CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );

      CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

# Complex Jinja2 lookups - use >- with structured format
- name: Retrieve certificate from Vault
  ansible.builtin.set_fact:
    vault_crt: >-
      {{
        lookup(
          'community.hashi_vault.hashi_vault',
          'secret=static_secrets/data/env/' ~ cluster_user ~ '/vault:cert
           url=' ~ vault_address ~ '
           auth_method=token
           token=' ~ vault_token ~ '
           validate_certs=true
           namespace=mynamespace'
        ) | default('')
      }}
  no_log: true

# Complex filters/transformations - use >-
- name: Build complex configuration
  ansible.builtin.set_fact:
    app_config: >-
      {{
        (base_config | combine(env_config))
        | dict2items
        | selectattr('value', 'defined')
        | list
        | items2dict
      }}
```

## Additional Resources

For detailed information about specific tools and practices:

- **Ansible Galaxy**: Install collections with `ansible-galaxy collection install -r requirements.yml`
- **Ansible Documentation**: https://docs.ansible.com
- **Ansible Lint**: https://ansible-lint.readthedocs.io
- **Molecule Testing**: https://molecule.readthedocs.io
- **Best Practices**: https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html

## Common Ansible Collections

When suggesting module usage, be aware of these commonly used collections:

- `ansible.builtin`: Core Ansible modules (always use FQCN)
- `ansible.posix`: POSIX system utilities (authorized_key, mount, sysctl, etc.)
- `community.general`: General-purpose modules (various cloud, packaging, system modules)
- `community.hashi_vault`: HashiCorp Vault integration
- `kubernetes.core`: Kubernetes/OpenShift cluster management
- `amazon.aws`: AWS cloud resources
- `azure.azcollection`: Microsoft Azure resources
- `google.cloud`: Google Cloud Platform resources
- `community.docker`: Docker container management
- `community.postgresql`: PostgreSQL database management
- `community.mysql`: MySQL/MariaDB database management
- `ansible.windows`: Windows system management

## Final Notes

- **Always prioritize security, maintainability, and idempotency**
- **Target modern Ansible versions (2.15+) and Python 3.9+**
- **Follow the principle of least privilege**
- **Write clear, self-documenting code with meaningful names**
- **When in doubt, prefer explicit over implicit, clear over clever**
- **Test your automation thoroughly before production deployment**

---

**Note**: These are general Ansible best practices. Customize the guidelines based on your organization's specific requirements, infrastructure, and policies.
