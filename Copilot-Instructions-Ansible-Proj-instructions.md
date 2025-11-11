# Copilot Instructions for Ansible Projects

## Project Structure Overview

This repository contains Ansible automation projects with the following structure:

- Roles organized in standard Ansible role directory structure
- Collections in the collections/ directory
- Custom Python modules and libraries in custom_modules/ directory
- Playbooks in playbooks/ directory
- Inventory files in inventory/ directory

## Code Style and Standards

### Python Modules and Libraries

- Follow PEP 8 coding standards for Python code
- Use docstrings with Google-style formatting for all functions and classes
- Implement proper error handling with custom exceptions when needed
- Include type hints where appropriate
- Maintain backward compatibility in module interfaces

**Example Python Module:**

```python
#!/usr/bin/env python3
"""
Custom Ansible module for managing system users.
"""

from ansible.module_utils.basic import AnsibleModule
import pwd
import grp

def user_exists(username):
    """Check if a user exists on the system."""
    try:
        pwd.getpwnam(username)
        return True
    except KeyError:
        return False

def create_user(username, home_dir="/home", shell="/bin/bash"):
    """Create a new system user."""
    # Implementation details here
    pass

def main():
    """Main module entry point."""
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            home=dict(type='str', default='/home'),
            shell=dict(type='str', default='/bin/bash')
        ),
        supports_check_mode=True
    )

    username = module.params['name']
    state = module.params['state']
    home_dir = module.params['home']
    shell = module.params['shell']

    # Implementation logic here
    result = dict(changed=False, user=username)
    
    if state == 'present':
        if not user_exists(username):
            create_user(username, home_dir, shell)
            result['changed'] = True
    else:
        # Handle absent state
        pass

    module.exit_json(**result)

if __name__ == '__main__':
    main()
```

### Ansible Roles

- Use consistent naming conventions for role variables (snake_case)
- Follow the standard Ansible role directory structure
- Define default variables in defaults/main.yml
- Document all role variables in README.md files
- Implement proper task organization with logical grouping and clear names

**Example Role Task File:**

```yaml
# tasks/main.yml
---
- name: Ensure required packages are installed
  yum:
    name: "{{ item }}"
    state: present
  loop: "{{ packages }}"
  become: true

- name: Create application user
  user:
    name: "{{ app_user }}"
    home: "{{ app_home }}"
    shell: "{{ app_shell }}"
    system: true
    createhome: true
  become: true

- name: Configure application directory
  file:
    path: "{{ app_directory }}"
    state: directory
    owner: "{{ app_user }}"
    group: "{{ app_group }}"
    mode: '0755'
  become: true

- name: Deploy application configuration
  template:
    src: config.j2
    dest: "{{ app_config_path }}"
    owner: "{{ app_user }}"
    group: "{{ app_group }}"
    mode: '0644'
  notify: restart application service
```

### Collections

- Follow Ansible collection naming conventions (namespace.collection_name)
- Include proper metadata in galaxy.yml
- Use consistent documentation structure across collection modules
- Maintain versioning according to semantic versioning standards

**Example Collection Module Task:**

```yaml
# plugins/modules/my_custom_module.py
---
module: my_custom_module
short_description: Custom module for managing specific tasks
description:
  - This module performs custom operations on target systems
author:
  - Your Name <your.email@example.com>
options:
  name:
    description:
      - The name of the resource to manage
    required: true
    type: str
  state:
    description:
      - The desired state of the resource
    required: false
    default: present
    choices: [ absent, present ]
    type: str

extends_documentation_fragment:
  - ansible.builtin.action_common_attributes
attributes:
  check_mode:
    support: full
  diff_mode:
    support: full

requirements:
  - Python >= 3.6
"""

RETURN = """
original_message:
  description: The original name parameter
  returned: always
  type: str
message:
  description: The output message
  returned: always
  type: str
"""

EXAMPLES = """
- name: Create a custom resource
  my_namespace.my_collection.my_custom_module:
    name: example-resource
    state: present

- name: Remove a custom resource
  my_namespace.my_collection.my_custom_module:
    name: example-resource
    state: absent
"""

from ansible.module_utils.basic import AnsibleModule

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['absent', 'present']),
        ),
        supports_check_mode=True
    )

    # Module logic here
    result = dict(
        changed=False,
        original_message=module.params['name'],
        message=f"Resource {module.params['name']} processed"
    )
    
    module.exit_json(**result)

if __name__ == '__main__':
    main()
```

## Git Workflow

### Branching Strategy

- Main branch should contain stable, production-ready code
- Feature branches should be created for new development work
- Pull requests must include automated testing results before merging
- All changes must pass linting and unit tests

**Example Branch Naming Convention:**

```bash
# Feature branches
feature/add-new-role
feature/improve-security-module

# Bug fix branches  
bugfix/fix-role-variables
hotfix/critical-fix-for-playbook

# Release branches
release/v1.2.0
```

### Commit Messages

- Use conventional commit format: <type>(<scope>): <subject>
- Types: feat, fix, docs, style, refactor, test, chore
- Include issue reference when applicable (fixes #123)

**Example Commit Messages:**

```bash
# Feature addition
feat(role): add new webserver role with SSL support

# Bug fix
fix(module): correct parameter handling in custom module

# Documentation update
docs(README): update installation instructions for collections

# Refactor
refactor(playbook): simplify complex task structure
```

## Testing Strategy

### Unit Tests for Python Modules

**Example pytest configuration:**

```python
# tests/unit/test_custom_module.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_modules'))

from my_custom_module import user_exists, create_user

def test_user_exists():
    """Test that user_exists function works correctly."""
    # Mock testing approach
    pass

def test_create_user():
    """Test that create_user function works correctly."""
    # Mock testing approach  
    pass
```

### Integration Tests with Molecule

**Example molecule scenario:**

```yaml
# molecule/default/molecule.yml
---
driver:
  name: docker
platforms:
  - name: instance
    image: "centos:7"
    pre_build_image: true
provisioner:
  name: ansible
  playbooks:
    converge: ../playbooks/test-role.yml
verifier:
  name: ansible
```

**Example test playbook for Molecule:**

```yaml
# molecule/default/playbooks/test-role.yml
---
- name: Test role with molecule
  hosts: all
  become: true
  tasks:
    - name: Include test role
      include_role:
        name: "{{ test_role_name }}"
    
    - name: Verify role functionality
      assert:
        that:
          - "test_result is defined"
        fail_msg: "Role did not set expected variables"
        success_msg: "Role executed successfully"
```

### Linting and Validation Tasks

**Example linting playbook:**

```yaml
# playbooks/lint.yml
---
- name: Run linting checks
  hosts: localhost
  gather_facts: false
  tasks:
    - name: Check YAML syntax
      command: yamllint .
      args:
        chdir: "{{ playbook_dir }}"
    
    - name: Check Python code quality
      command: flake8 custom_modules/
      args:
        chdir: "{{ playbook_dir }}"
    
    - name: Validate Ansible playbooks
      command: ansible-lint playbooks/
      args:
        chdir: "{{ playbook_dir }}"
```

## Documentation Requirements

### Role README Example

```markdown
# Web Server Role

This role installs and configures a web server with SSL support.

## Variables

| Name             | Default Value    | Description                        |
|------------------|------------------|------------------------------------|
| web_server_port  | 80               | Port for the web server            |
| ssl_enabled      | true             | Enable SSL for HTTPS connections   |
| app_user         | www-data         | User to run the web server         |

## Usage Example

```yaml
- name: Configure web server
  hosts: webservers
  roles:
    - role: webserver
      web_server_port: 8080
      ssl_enabled: false
```

```

### Collection Documentation Example
```markdown
# My Custom Collection

This collection provides custom modules and roles for Ansible automation.

## Modules

### my_custom_module
Manages custom resources in the system.

## Installation

```bash
ansible-galaxy collection install my_namespace.my_collection
```

## Usage

```yaml
- name: Use custom module
  my_namespace.my_collection.my_custom_module:
    name: example-resource
    state: present
```

```

## Security Considerations

### Example Vault Usage
**Vault encrypted variable file:**
```yaml
# group_vars/all/vault.yml
---
ansible_become_password: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          30323833393734343738303832343235313732373932353130383039333137323430313036323031
          31313832343131343030323739333731343335323131333936303936393238303539353636383032
```

### Secure Playbook Example

```yaml
# playbooks/secure-deployment.yml
---
- name: Secure deployment playbook
  hosts: all
  become: true
  vars:
    # Use vault for sensitive data
    database_password: "{{ vault_database_password }}"
    
  tasks:
    - name: Create secure directory
      file:
        path: /opt/application/config
        state: directory
        owner: appuser
        group: appgroup
        mode: '0700'
        
    - name: Deploy configuration with vault
      template:
        src: config.j2
        dest: /opt/application/config/app.conf
        owner: appuser
        group: appgroup
        mode: '0600'
      vars:
        secret_key: "{{ vault_secret_key }}"
```

## Development Environment Setup

### Example Requirements File

```txt
# requirements.txt
ansible>=2.10.0,<3.0.0
pytest>=6.0.0
molecule>=3.0.0
yamllint>=1.25.0
flake8>=3.8.0
```

### Example Development Playbook

```yaml
# playbooks/setup-dev-env.yml
---
- name: Setup development environment
  hosts: localhost
  gather_facts: false
  tasks:
    - name: Install Python dependencies
      pip:
        requirements: requirements.txt
        state: present
    
    - name: Install Ansible collections
      ansible.builtin.command: |
        ansible-galaxy collection install {{ item }}
      loop:
        - community.general
        - community.docker
        - ansible.posix
    
    - name: Setup pre-commit hooks
      command: pre-commit install
```

## CI/CD Integration

### Example GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
---
name: CI Pipeline
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: |
          pip install yamllint flake8 ansible-lint pytest
      - name: Run linters
        run: |
          yamllint .
          ansible-lint playbooks/
          flake8 custom_modules/

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: pip install pytest
      - name: Run unit tests
        run: pytest tests/
```

## Best Practices

### Example Playbook with Error Handling

```yaml
# playbooks/deploy-application.yml
---
- name: Deploy application with error handling
  hosts: all
  become: true
  vars:
    app_name: "myapp"
    
  tasks:
    - name: Check if application directory exists
      stat:
        path: "/opt/{{ app_name }}"
      register: app_dir
    
    - name: Create application directory
      file:
        path: "/opt/{{ app_name }}"
        state: directory
        owner: "{{ app_user }}"
        group: "{{ app_group }}"
        mode: '0755'
      when: not app_dir.stat.exists
    
    - name: Download application package
      get_url:
        url: "https://example.com/{{ app_name }}-latest.tar.gz"
        dest: "/tmp/{{ app_name }}.tar.gz"
        checksum: "sha256:{{ expected_checksum }}"
      retries: 3
      delay: 5
      register: download_result
      until: download_result is succeeded
    
    - name: Extract application package
      unarchive:
        src: "/tmp/{{ app_name }}.tar.gz"
        dest: "/opt/{{ app_name }}"
        owner: "{{ app_user }}"
        group: "{{ app_group }}"
        mode: '0755'
      failed_when: false
```

### Example Role with Variables and Defaults

```yaml
# roles/webserver/defaults/main.yml
---
# Default variables for webserver role
web_server_port: 80
ssl_enabled: true
ssl_cert_file: "/etc/ssl/certs/server.crt"
ssl_key_file: "/etc/ssl/private/server.key"
app_user: "www-data"
app_group: "www-data"
```

```yaml
# roles/webserver/tasks/main.yml
---
- name: Install web server packages
  package:
    name: "{{ web_server_packages }}"
    state: present
  when: web_server_packages is defined

- name: Configure web server
  template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
    owner: root
    group: root
    mode: '0644'
  notify: restart nginx

- name: Enable and start web server service
  systemd:
    name: "{{ web_server_service }}"
    enabled: true
    state: started
  when: web_server_service is defined
```

## Conflict Resolution

### Example Pull Request Template

```markdown
## Description
Brief description of changes made

## Related Issues
- Fixes #123
- Closes #456

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass  
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Variables properly documented
- [ ] Security considerations addressed
```

### Example Merge Conflict Resolution

```bash
# Before merging, resolve conflicts
git checkout feature-branch
git pull origin main
git merge main  # This may show conflicts

# Resolve conflicts manually in editor
# Then commit resolved files
git add .
git commit -m "Resolve merge conflicts with main branch"

# Push to remote
git push origin feature-branch
```
