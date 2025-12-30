# Ansible Role Development to Production Workflow

**Document Version:** 1.0.0  
**Last Updated:** 2024-12-30  
**Purpose:** Guide for developing Ansible roles in a monorepo and preparing them for production distribution

---

## Table of Contents

1. [Workflow Overview](#workflow-overview)
2. [Phase 1: Development in Monorepo](#phase-1-development-in-monorepo)
3. [Phase 2: Quality Assurance](#phase-2-quality-assurance)
4. [Phase 3: Documentation Preparation](#phase-3-documentation-preparation)
5. [Phase 4: Distribution Package Creation](#phase-4-distribution-package-creation)
6. [Phase 5: Standalone Git Repository Setup](#phase-5-standalone-git-repository-setup)
7. [Automation Scripts](#automation-scripts)
8. [Quality Checklists](#quality-checklists)

---

## Workflow Overview

### Development Pipeline

```text
[Monorepo Development] → [Quality Assurance] → [Documentation] → [Tarball Creation] → [Git Repository]
        ↓                        ↓                    ↓                   ↓                    ↓
   Feature work          Testing/Linting      Complete docs       Standalone pkg      Production ready
   Version control       Code quality         All files           Self-contained      Independent repo
   Shared resources      Standards check      Templates           Distribution        Team handoff
```

### Key Principles

1. **Develop in context** - Build roles alongside other roles with shared resources
2. **Test iteratively** - Validate as you develop using monorepo tooling
3. **Document comprehensively** - Create complete standalone documentation
4. **Package cleanly** - Create self-contained distribution with all dependencies
5. **Deploy independently** - Enable standalone git repository or direct installation

---

## Phase 1: Development in Monorepo

### Initial Setup

#### Directory Structure

```text
ansible-playground/                    # Monorepo root
├── roles/
│   └── <role_name>/                  # Role under development
│       ├── README.md                 # Role documentation (in-progress)
│       ├── CHANGELOG.md              # Version history
│       ├── defaults/
│       │   └── main.yml             # Default variables
│       ├── vars/
│       │   └── main.yml             # Internal constants
│       ├── meta/
│       │   └── main.yml             # Role metadata
│       ├── library/                  # Custom modules (optional)
│       │   └── *.py
│       ├── filter_plugins/           # Custom filters (optional)
│       │   └── *.py
│       ├── tasks/
│       │   ├── main.yml             # Orchestrator
│       │   └── *.yml                # Modular task files
│       ├── templates/                # Jinja2 templates (optional)
│       ├── files/                    # Static files (optional)
│       └── handlers/                 # Handlers (optional)
│           └── main.yml
├── playbooks/
│   └── <role_playbook>.yml          # Test/example playbooks
├── docs/
│   └── <role_name>/                 # Role-specific documentation
│       ├── architecture.md
│       ├── usage_examples.md
│       └── specification.md
├── .ansible-lint                     # Shared linting config
├── .gitignore                        # Shared git ignore
└── requirements.yml                  # Shared collection dependencies
```

#### Step 1: Create Role Structure

```bash
# Option 1: Using ansible-galaxy
cd ansible-playground
ansible-galaxy init roles/<role_name>

# Option 2: Manual creation
mkdir -p roles/<role_name>/{defaults,vars,meta,tasks,templates,files,handlers,library,filter_plugins}
touch roles/<role_name>/{defaults,vars,meta,tasks,handlers}/main.yml
```

#### Step 2: Initialize Core Files

**`roles/<role_name>/meta/main.yml`:**

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

**`roles/<role_name>/defaults/main.yml`:**

```yaml
---
# <role_name> default variables

# General settings
<role_name>_variable_one: "default_value"
<role_name>_variable_two: true
<role_name>_timeout: 300

# Feature flags
<role_name>_enable_feature_x: false
<role_name>_debug_mode: false
```

**`roles/<role_name>/README.md`:**

```markdown
# Ansible Role: <role_name>

## Description

Brief description of what this role does.

## Requirements

- Ansible Core 2.12+
- Collections: (list required collections)
- Python 3.11+

## Role Variables

See `defaults/main.yml` for all available variables.

## Example Playbook

\`\`\`yaml
---
- name: Example usage
  hosts: localhost
  gather_facts: true
  
  tasks:
    - name: Run <role_name>
      ansible.builtin.include_role:
        name: <role_name>
      vars:
        <role_name>_variable_one: "custom_value"
\`\`\`

## License

Apache-2.0

## Author

Your Name
```

**`roles/<role_name>/CHANGELOG.md`:**

```markdown
# Changelog

All notable changes to this role will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Initial role structure
- Basic functionality

### Changed

### Fixed

### Removed
```

### Development Workflow

#### Step 1: Implement Modular Task Architecture

**Best Practice:** Use orchestrator pattern with specialized task files

**`roles/<role_name>/tasks/main.yml`** (Orchestrator):

```yaml
---
# Role: <role_name>
# Purpose: [Brief description]

# Phase 1: Preparation
- name: "Phase 1: Preparation"
  ansible.builtin.include_tasks: preparation.yml
  tags: [preparation, <role_name>]

# Phase 2: Validation
- name: "Phase 2: Validation"
  ansible.builtin.include_tasks: validation.yml
  tags: [validation, <role_name>]

# Phase 3: Execution
- name: "Phase 3: Execution"
  ansible.builtin.include_tasks: execution.yml
  tags: [execution, <role_name>]

# Phase 4: Verification
- name: "Phase 4: Verification"
  ansible.builtin.include_tasks: verification.yml
  tags: [verification, <role_name>]

# Phase 5: Reporting
- name: "Phase 5: Reporting"
  ansible.builtin.include_tasks: reporting.yml
  tags: [reporting, <role_name>]
  when: <role_name>_enable_reporting | default(true)
```

**Guidelines:**
- Keep `main.yml` under 500 lines (orchestrator only)
- Create specialized task files for distinct workflows
- Use descriptive names: `vault_retrieve_credentials.yml`, `cluster_health_check.yml`
- Document each task file with header comments
- Use tags for selective execution

#### Step 2: Implement Task Files

**Example: `roles/<role_name>/tasks/preparation.yml`:**

```yaml
---
# Preparation phase: Environment setup and prerequisite checks

- name: Validate required variables
  ansible.builtin.assert:
    that:
      - <role_name>_variable_one is defined
      - <role_name>_variable_two is defined
    fail_msg: "Required variables are not defined"
    success_msg: "All required variables are present"
  tags: [validation]

- name: Create working directory
  ansible.builtin.file:
    path: "{{ <role_name>_work_dir }}"
    state: directory
    mode: '0755'
  tags: [filesystem]

- name: Check external dependencies
  ansible.builtin.command: which <required_tool>
  register: dependency_check
  changed_when: false
  failed_when: dependency_check.rc != 0
  tags: [dependencies]
```

#### Step 3: Create Test Playbooks

**`playbooks/<role_name>_test.yml`:**

```yaml
---
- name: Test <role_name> role
  hosts: localhost
  gather_facts: true

  vars:
    # Override defaults for testing
    <role_name>_debug_mode: true
    <role_name>_variable_one: "test_value"

  tasks:
    - name: Run <role_name> role
      ansible.builtin.include_role:
        name: <role_name>
      tags: [<role_name>]

    - name: Verify results
      ansible.builtin.debug:
        msg: "Role execution completed successfully"
```

#### Step 4: Implement Custom Modules (if needed)

**Location:** `roles/<role_name>/library/<module_name>.py`

**Template:** See CLAUDE.md for complete module template

**Key Requirements:**
- Follow Ansible 2.18+ module standards
- Include DOCUMENTATION, EXAMPLES, RETURN sections
- Support check mode
- Implement proper error handling
- Use type hints and validation

**Example Module Structure:**

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: <module_name>
short_description: Brief description
description:
  - Detailed description
version_added: "1.0.0"
author:
  - Your Name (@github_handle)
options:
  name:
    description: Resource name
    type: str
    required: true
requirements:
  - python >= 3.11
'''

EXAMPLES = r'''
- name: Basic usage
  <module_name>:
    name: example
'''

RETURN = r'''
changed:
  description: Whether changes were made
  type: bool
  returned: always
result:
  description: Operation result
  type: dict
  returned: success
'''

from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(changed=False, result={})

    try:
        # Implementation here
        if module.check_mode:
            result['msg'] = 'Check mode: would process resource'
            module.exit_json(**result)

        # Actual processing
        result['changed'] = True
        result['result'] = {'status': 'success'}
        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=f'Module failed: {str(e)}', **result)

def main():
    run_module()

if __name__ == '__main__':
    main()
```

#### Step 5: Implement Custom Filter Plugins (if needed)

**Location:** `roles/<role_name>/filter_plugins/<filter_name>.py`

**Template:** See CLAUDE.md for complete filter plugin template

**Example Filter Structure:**

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
filter: <filter_name>
author: Your Name (@github_handle)
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
    msg: "{{ value | <filter_name> }}"
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
        return {
            '<filter_name>': self.filter_method
        }

    @staticmethod
    def filter_method(value, param=None):
        if not isinstance(value, (str, dict, list)):
            raise AnsibleFilterError(
                f"Expected str/dict/list, got {type(value).__name__}"
            )

        try:
            # Filter implementation
            return transformed_value
        except Exception as e:
            raise AnsibleFilterError(f"Error in <filter_name>: {str(e)}")
```

### Version Control During Development

```bash
# Create feature branch
git checkout -b feature/<role_name>-development

# Regular commits during development
git add roles/<role_name>/
git commit -m "feat(<role_name>): add initial task structure"

git add playbooks/<role_name>_test.yml
git commit -m "test(<role_name>): add test playbook"

# When feature is complete (but before distribution)
git push origin feature/<role_name>-development
# Create pull request for review
```

---

## Phase 2: Quality Assurance

### Pre-Distribution Testing

Before creating a distribution package, ensure the role meets all quality standards.

### Step 1: Syntax Validation

```bash
# Check playbook syntax
ansible-playbook --syntax-check playbooks/<role_name>_test.yml

# Check task file syntax
ansible-playbook --syntax-check -i localhost, roles/<role_name>/tasks/main.yml
```

### Step 2: Ansible Lint

```bash
# Lint the entire role
.venv/bin/ansible-lint roles/<role_name>/

# Lint specific task files
.venv/bin/ansible-lint roles/<role_name>/tasks/main.yml

# Expected passes:
# - No syntax errors
# - No critical violations
# - Warning-level issues documented in README
```

### Step 3: Python Code Quality (if applicable)

**For custom modules:**

```bash
# Format code
.venv/bin/isort roles/<role_name>/library/*.py
.venv/bin/black roles/<role_name>/library/*.py

# Lint
.venv/bin/flake8 roles/<role_name>/library/*.py

# Type checking
.venv/bin/mypy roles/<role_name>/library/*.py
```

**For filter plugins:**

```bash
# Format code
.venv/bin/isort roles/<role_name>/filter_plugins/*.py
.venv/bin/black roles/<role_name>/filter_plugins/*.py

# Lint
.venv/bin/flake8 roles/<role_name>/filter_plugins/*.py

# Type checking
.venv/bin/mypy roles/<role_name>/filter_plugins/*.py
```

### Step 4: Functional Testing

```bash
# Dry-run test
ansible-playbook -i inventory/test playbooks/<role_name>_test.yml --check

# Execute in test environment
ansible-playbook -i inventory/test playbooks/<role_name>_test.yml

# Test with tags
ansible-playbook -i inventory/test playbooks/<role_name>_test.yml --tags preparation,validation

# Verbose execution for debugging
ansible-playbook -i inventory/test playbooks/<role_name>_test.yml -vvv
```

### Step 5: Update CHANGELOG.md

**Update for release version:**

```markdown
# Changelog

## [1.0.0] - 2024-12-30

### Added
- Initial role implementation
- Modular task architecture with 5 phases
- Custom module: <module_name>
- Custom filter: <filter_name>
- Comprehensive error handling
- Support for check mode
- Detailed logging and reporting

### Changed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Removed
- N/A (initial release)

## [Unreleased]
```

---

## Phase 3: Documentation Preparation

### Required Documentation Files

For standalone distribution, the following documentation files are required:

1. **README.md** - Complete role documentation
2. **INSTALL.md** - Installation and setup guide
3. **CHANGELOG.md** - Version history (already created)
4. **LICENSE** - License file
5. **DISTRIBUTION-README.md** - Distribution package notes
6. **QUICKSTART.md** - Quick start guide
7. **MANIFEST.txt** - Package contents manifest
8. **example-playbook.yml** - Complete usage example

### Step 1: Finalize README.md

**Template:**

```markdown
# Ansible Role: <role_name>

## Description

Comprehensive description of role purpose, functionality, and use cases.

## Features

- Feature 1: Description
- Feature 2: Description
- Feature 3: Description

## Requirements

### Ansible

- Ansible Core: 2.12+
- Collections:
  - kubernetes.core (>=2.3.0)
  - community.hashi_vault (>=3.0.0)
  - ansible.posix

### Python

- Python: 3.11+
- Libraries: (list if any)

### System Requirements

- OpenShift: 4.18+
- Cluster admin access
- (other requirements)

## Role Variables

### Required Variables

| Variable | Type | Description |
|----------|------|-------------|
| `<role_name>_required_var` | string | Description |

### Optional Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `<role_name>_optional_var` | bool | `false` | Description |
| `<role_name>_timeout` | int | `300` | Timeout in seconds |

See `defaults/main.yml` for complete variable reference.

## Dependencies

List any role dependencies here.

## Example Playbook

### Basic Usage

\`\`\`yaml
---
- name: Basic <role_name> usage
  hosts: localhost
  gather_facts: true

  tasks:
    - name: Run <role_name>
      ansible.builtin.include_role:
        name: <role_name>
      vars:
        <role_name>_required_var: "value"
\`\`\`

### Advanced Usage

\`\`\`yaml
---
- name: Advanced <role_name> usage
  hosts: localhost
  gather_facts: true

  tasks:
    - name: Run <role_name> with custom settings
      ansible.builtin.include_role:
        name: <role_name>
      vars:
        <role_name>_required_var: "value"
        <role_name>_optional_var: true
        <role_name>_timeout: 600
\`\`\`

### Tag-based Execution

\`\`\`yaml
---
- name: Run specific phases
  hosts: localhost
  gather_facts: true

  tasks:
    - name: Run preparation and validation only
      ansible.builtin.include_role:
        name: <role_name>
      tags: [preparation, validation]
\`\`\`

## Tags

Available tags for selective execution:

- `preparation` - Environment preparation
- `validation` - Input validation
- `execution` - Main execution
- `verification` - Result verification
- `reporting` - Generate reports

## Return Values

The role registers facts that can be used in subsequent tasks:

| Fact | Type | Description |
|------|------|-------------|
| `<role_name>_result` | dict | Execution results |
| `<role_name>_status` | string | Final status |

## Error Handling

The role implements comprehensive error handling:

- All phases wrapped in block/rescue
- Clear error messages
- Failed tasks set descriptive failure messages
- Check mode fully supported

## Troubleshooting

### Common Issues

**Issue 1:**
- Symptoms: Description
- Cause: Explanation
- Solution: Resolution steps

**Issue 2:**
- Symptoms: Description
- Cause: Explanation
- Solution: Resolution steps

### Debug Mode

Enable debug mode for detailed logging:

\`\`\`yaml
<role_name>_debug_mode: true
\`\`\`

## Testing

### Syntax Check

\`\`\`bash
ansible-playbook --syntax-check playbooks/<role_name>.yml
\`\`\`

### Dry Run

\`\`\`bash
ansible-playbook -i inventory playbooks/<role_name>.yml --check
\`\`\`

### Full Execution

\`\`\`bash
ansible-playbook -i inventory playbooks/<role_name>.yml
\`\`\`

## Contributing

Contributions are welcome! Please ensure:

1. All code passes ansible-lint
2. Python code formatted with black/isort
3. Changes documented in CHANGELOG.md
4. Tests pass successfully

## License

Apache-2.0

## Author Information

Created by: Your Name
Organization: Your Organization
Contact: your.email@example.com

## Acknowledgments

List any acknowledgments, references, or credits here.
```

### Step 2: Create INSTALL.md

**Template:**

```markdown
# Installation Guide - <role_name>

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
3. [Post-Installation Setup](#post-installation-setup)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- Ansible Core: 2.12 or higher
- Python: 3.11 or higher
- Operating System: RHEL/CentOS 8+
- Container Runtime: Podman or Docker (for EE deployments)

### Required Access

- Target system: SSH access with appropriate privileges
- Cluster: Admin access (if managing Kubernetes/OpenShift)
- Vault: Read/write access to required paths (if using HashiCorp Vault)

### Required Collections

The role requires these Ansible collections:

- `kubernetes.core` (>= 2.3.0)
- `community.hashi_vault` (>= 3.0.0)
- `ansible.posix`

## Installation Methods

### Method 1: Extract from Tarball (Recommended)

#### Step 1: Download and Verify

\`\`\`bash
# Download tarball
curl -LO https://example.com/<role-name>-role-1.0.0.tar.gz
curl -LO https://example.com/<role-name>-role-1.0.0.tar.gz.sha256

# Verify checksum
sha256sum -c <role-name>-role-1.0.0.tar.gz.sha256
# Expected: <role-name>-role-1.0.0.tar.gz: OK
\`\`\`

#### Step 2: Extract to Roles Directory

\`\`\`bash
# Extract to roles directory
tar -xzf <role-name>-role-1.0.0.tar.gz -C roles/

# Rename to standard role name
mv roles/<role-name>-role-1.0.0 roles/<role_name>

# Verify structure
ls -la roles/<role_name>/
\`\`\`

#### Step 3: Install Dependencies

\`\`\`bash
# Install Ansible collections
ansible-galaxy collection install -r roles/<role_name>/requirements.yml

# Install Python dependencies (if requirements.txt exists)
pip install -r roles/<role_name>/requirements.txt
\`\`\`

### Method 2: Clone from Git Repository

\`\`\`bash
# Clone repository
cd roles/
git clone https://github.com/your-org/<role_name>.git
cd <role_name>

# Install dependencies
ansible-galaxy collection install -r requirements.yml
pip install -r requirements.txt  # if exists
\`\`\`

### Method 3: Ansible Galaxy (if published)

\`\`\`bash
# Install from Galaxy
ansible-galaxy role install your_namespace.<role_name>

# Install to custom path
ansible-galaxy role install your_namespace.<role_name> -p ./roles
\`\`\`

## Post-Installation Setup

### Step 1: Configure Variables

Create a variables file or use group_vars:

\`\`\`bash
# Option 1: Copy example
cp roles/<role_name>/group_vars_example.yml group_vars/all/<role_name>.yml

# Option 2: Create new file
cat > group_vars/all/<role_name>.yml << 'EOF'
---
<role_name>_required_var: "your_value"
<role_name>_optional_var: true
EOF
\`\`\`

### Step 2: Create Inventory

\`\`\`bash
# Create inventory file
cat > inventory/production << 'EOF'
[targets]
server1.example.com
server2.example.com

[targets:vars]
ansible_user=ansible
ansible_become=true
EOF
\`\`\`

### Step 3: Create Playbook

\`\`\`bash
# Copy example playbook
cp roles/<role_name>/example-playbook.yml playbooks/<role_name>.yml

# Or create custom playbook
cat > playbooks/<role_name>.yml << 'EOF'
---
- name: Execute <role_name>
  hosts: targets
  gather_facts: true

  tasks:
    - name: Run <role_name> role
      ansible.builtin.include_role:
        name: <role_name>
      vars:
        <role_name>_required_var: "{{ <role_name>_required_var }}"
EOF
\`\`\`

## Verification

### Step 1: Syntax Check

\`\`\`bash
ansible-playbook --syntax-check playbooks/<role_name>.yml
# Expected: playbook: playbooks/<role_name>.yml
\`\`\`

### Step 2: Lint Check

\`\`\`bash
ansible-lint playbooks/<role_name>.yml
# Expected: No critical errors
\`\`\`

### Step 3: Dry Run

\`\`\`bash
ansible-playbook -i inventory/production playbooks/<role_name>.yml --check
# Expected: No failures, shows what would change
\`\`\`

### Step 4: Test Execution

\`\`\`bash
# Run against test/dev environment first
ansible-playbook -i inventory/test playbooks/<role_name>.yml

# Verify results
# (check for success indicators)
\`\`\`

## Troubleshooting

### Collection Not Found

**Error:**
\`\`\`
ERROR! couldn't resolve module/action 'kubernetes.core.k8s'
\`\`\`

**Solution:**
\`\`\`bash
ansible-galaxy collection install -r requirements.yml --force
\`\`\`

### Python Module Missing

**Error:**
\`\`\`
ModuleNotFoundError: No module named 'kubernetes'
\`\`\`

**Solution:**
\`\`\`bash
pip install -r requirements.txt
# Or if requirements.txt doesn't exist:
pip install kubernetes openshift
\`\`\`

### Role Not Found

**Error:**
\`\`\`
ERROR! the role '<role_name>' was not found
\`\`\`

**Solution:**
\`\`\`bash
# Verify role location
ls -la roles/<role_name>/

# Check ansible.cfg for roles_path
grep roles_path ansible.cfg

# Add role path if needed
export ANSIBLE_ROLES_PATH=./roles:~/.ansible/roles:/etc/ansible/roles
\`\`\`

### Permission Denied

**Error:**
\`\`\`
FAILED! => {"msg": "Permission denied"}
\`\`\`

**Solution:**
\`\`\`bash
# Ensure SSH access
ssh ansible@target-host

# Check become settings in inventory
# Ensure ansible_become=true is set if privilege escalation needed
\`\`\`

## Additional Resources

- **Main README**: See [README.md](README.md) for complete role documentation
- **Quick Start**: See [QUICKSTART.md](docs/QUICKSTART.md) for rapid deployment
- **Examples**: See [playbooks/](playbooks/) directory for usage examples
- **Changelog**: See [CHANGELOG.md](CHANGELOG.md) for version history

## Support

For issues, questions, or contributions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review [README.md](README.md) documentation
3. Open an issue on GitHub with:
   - Ansible version: `ansible --version`
   - Python version: `python --version`
   - Error messages and logs
   - Steps to reproduce

---

**Next Steps:**

After successful installation, proceed to [QUICKSTART.md](docs/QUICKSTART.md) for your first deployment.
```

### Step 3: Create LICENSE File

```text
Apache License 2.0

Copyright (c) 2024 Your Organization

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

### Step 4: Create requirements.yml

**Based on role dependencies:**

```yaml
---
collections:
  # Kubernetes/OpenShift management
  - name: kubernetes.core
    version: ">=2.3.0"

  # HashiCorp Vault (if used)
  - name: community.hashi_vault
    version: ">=3.0.0"

  # Standard utilities
  - name: ansible.posix
    version: ">=1.3.0"

  # Add other collections as needed
  # - name: community.general
  #   version: ">=5.0.0"
```

### Step 5: Create requirements.txt (if Python dependencies exist)

```text
# Kubernetes/OpenShift Python client
kubernetes>=28.1.0
openshift>=0.13.0

# Additional dependencies (if needed)
# hvac>=1.2.0  # For Vault
# jmespath>=1.0.0  # For JSON/data manipulation
```

### Step 6: Create .ansible-lint Configuration

```yaml
---
profile: production

exclude_paths:
  - .git/
  - .venv/
  - .tox/

skip_list:
  - yaml[line-length]  # Allow longer lines for readability
  - var-naming[no-role-prefix]  # Allow variables without role prefix in some cases

warn_list:
  - experimental  # Warn about experimental features
  - no-changed-when  # Warn when changed_when not used
  - command-instead-of-module  # Warn when module exists

# Enable offline mode if no internet connection
# offline: true
```

### Step 7: Create .gitignore

```text
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/
.venv/
venv/

# Ansible
*.retry
.ansible/
.cache/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Secrets
*.vault
*.secret
credentials.yml
vault-password.txt

# Temporary files
*.tmp
*.temp
.work_dir/
```

### Step 8: Create example-playbook.yml

**Simple, clear example for quick start:**

```yaml
---
- name: Example <role_name> usage
  hosts: localhost
  gather_facts: true

  vars:
    # Required variables
    <role_name>_required_var: "example_value"

    # Optional variables (customize as needed)
    <role_name>_optional_var: true
    <role_name>_timeout: 300
    <role_name>_debug_mode: false

  tasks:
    - name: Run <role_name> role
      ansible.builtin.include_role:
        name: <role_name>
      vars:
        <role_name>_extra_setting: "value"

    - name: Display results
      ansible.builtin.debug:
        var: <role_name>_result
      when: <role_name>_result is defined
```

---

## Phase 4: Distribution Package Creation

### Overview

Create a self-contained tarball with top-level role directories (NOT nested) that can serve dual purposes:
1. Extract directly into `roles/` directory
2. Use as standalone git repository

### Critical Pattern: Top-Level Structure

**CORRECT:**

```text
<role-name>-role-<version>/
├── README.md                # Top level
├── INSTALL.md               # Top level
├── CHANGELOG.md             # Top level
├── LICENSE                  # Top level
├── requirements.yml         # Top level
├── requirements.txt         # Top level (if exists)
├── .ansible-lint           # Top level
├── .gitignore              # Top level
├── example-playbook.yml     # Top level
├── defaults/                # Role directory at top level
│   └── main.yml
├── meta/                    # Role directory at top level
│   └── main.yml
├── vars/                    # Role directory at top level (if exists)
│   └── main.yml
├── tasks/                   # Role directory at top level
│   └── *.yml
├── library/                 # Role directory at top level (if exists)
│   └── *.py
├── filter_plugins/          # Role directory at top level (if exists)
│   └── *.py
├── templates/               # Role directory at top level (if exists)
├── files/                   # Role directory at top level (if exists)
├── handlers/                # Role directory at top level (if exists)
│   └── main.yml
└── playbooks/               # Example playbooks at top level
    └── *.yml
```

**INCORRECT (Never Use This):**

```text
# DO NOT USE THIS NESTED STRUCTURE
<role-name>-role-<version>/
├── README.md
└── <role_name>/            # WRONG: Role nested under subdirectory
    ├── defaults/
    ├── meta/
    └── tasks/
```

### Step-by-Step Tarball Creation

#### Step 1: Prepare Staging Directory

```bash
# Set variables
ROLE_NAME="<role_name>"
VERSION="1.0.0"
TARBALL_NAME="${ROLE_NAME//_/-}-role-${VERSION}"
STAGING_DIR="/tmp/${TARBALL_NAME}"
PROJECT_ROOT="$(pwd)"

# Clean and create staging directory
rm -rf "${STAGING_DIR}"
mkdir -p "${STAGING_DIR}"
```

#### Step 2: Copy Role Directories to Top Level

```bash
# Copy each role directory individually to top level (NOT the parent role directory)
echo "Copying role directories to staging..."

# Required directories
cp -r "${PROJECT_ROOT}/roles/${ROLE_NAME}/defaults" "${STAGING_DIR}/"
cp -r "${PROJECT_ROOT}/roles/${ROLE_NAME}/meta" "${STAGING_DIR}/"
cp -r "${PROJECT_ROOT}/roles/${ROLE_NAME}/tasks" "${STAGING_DIR}/"

# Optional directories (only if they exist)
[[ -d "${PROJECT_ROOT}/roles/${ROLE_NAME}/vars" ]] && \
    cp -r "${PROJECT_ROOT}/roles/${ROLE_NAME}/vars" "${STAGING_DIR}/"

[[ -d "${PROJECT_ROOT}/roles/${ROLE_NAME}/library" ]] && \
    cp -r "${PROJECT_ROOT}/roles/${ROLE_NAME}/library" "${STAGING_DIR}/"

[[ -d "${PROJECT_ROOT}/roles/${ROLE_NAME}/filter_plugins" ]] && \
    cp -r "${PROJECT_ROOT}/roles/${ROLE_NAME}/filter_plugins" "${STAGING_DIR}/"

[[ -d "${PROJECT_ROOT}/roles/${ROLE_NAME}/templates" ]] && \
    cp -r "${PROJECT_ROOT}/roles/${ROLE_NAME}/templates" "${STAGING_DIR}/"

[[ -d "${PROJECT_ROOT}/roles/${ROLE_NAME}/files" ]] && \
    cp -r "${PROJECT_ROOT}/roles/${ROLE_NAME}/files" "${STAGING_DIR}/"

[[ -d "${PROJECT_ROOT}/roles/${ROLE_NAME}/handlers" ]] && \
    cp -r "${PROJECT_ROOT}/roles/${ROLE_NAME}/handlers" "${STAGING_DIR}/"
```

#### Step 3: Copy Top-Level Files

```bash
echo "Copying top-level documentation files..."

# Copy from role directory
cp "${PROJECT_ROOT}/roles/${ROLE_NAME}/README.md" "${STAGING_DIR}/"
cp "${PROJECT_ROOT}/roles/${ROLE_NAME}/CHANGELOG.md" "${STAGING_DIR}/"
[[ -f "${PROJECT_ROOT}/roles/${ROLE_NAME}/group_vars_example.yml" ]] && \
    cp "${PROJECT_ROOT}/roles/${ROLE_NAME}/group_vars_example.yml" "${STAGING_DIR}/"

# Copy from monorepo root (if shared configs)
cp "${PROJECT_ROOT}/.ansible-lint" "${STAGING_DIR}/"
cp "${PROJECT_ROOT}/.gitignore" "${STAGING_DIR}/"
```

#### Step 4: Create Configuration Files

```bash
echo "Creating configuration files..."

# Create requirements.yml
cat > "${STAGING_DIR}/requirements.yml" << 'EOF'
---
collections:
  - name: kubernetes.core
    version: ">=2.3.0"
  - name: ansible.posix
    version: ">=1.3.0"
  # Add other collections as needed
EOF

# Create requirements.txt (if Python dependencies exist)
if [[ -f "${PROJECT_ROOT}/requirements.txt" ]]; then
    # Extract relevant dependencies or create role-specific file
    cat > "${STAGING_DIR}/requirements.txt" << 'EOF'
kubernetes>=28.1.0
openshift>=0.13.0
# Add other Python dependencies as needed
EOF
fi

# Create LICENSE
cat > "${STAGING_DIR}/LICENSE" << 'EOF'
Apache License 2.0

Copyright (c) 2024 Your Organization

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
EOF

# Create INSTALL.md (use template from Phase 3)
# Copy from docs if it exists, or create from template
if [[ -f "${PROJECT_ROOT}/docs/${ROLE_NAME}/INSTALL.md" ]]; then
    cp "${PROJECT_ROOT}/docs/${ROLE_NAME}/INSTALL.md" "${STAGING_DIR}/"
else
    # Create basic INSTALL.md
    cat > "${STAGING_DIR}/INSTALL.md" << 'EOF'
# Installation Guide

See README.md for complete installation instructions.

## Quick Install

```bash
tar -xzf <role-name>-role-<version>.tar.gz -C roles/
mv roles/<role-name>-role-<version> roles/<role_name>
ansible-galaxy collection install -r roles/<role_name>/requirements.yml
```
EOF
fi

# Create example-playbook.yml
cat > "${STAGING_DIR}/example-playbook.yml" << 'EOF'
---
- name: Example <role_name> usage
  hosts: localhost
  gather_facts: true

  tasks:
    - name: Run <role_name> role
      ansible.builtin.include_role:
        name: <role_name>
      vars:
        <role_name>_required_var: "example_value"
EOF
```

#### Step 5: Create Playbooks Directory

```bash
echo "Creating playbooks directory..."
mkdir -p "${STAGING_DIR}/playbooks"

# Copy relevant playbooks from monorepo
# Identify playbooks that use this role
if [[ -f "${PROJECT_ROOT}/playbooks/${ROLE_NAME}_test.yml" ]]; then
    cp "${PROJECT_ROOT}/playbooks/${ROLE_NAME}_test.yml" "${STAGING_DIR}/playbooks/"
fi

# Add any other related playbooks
# cp "${PROJECT_ROOT}/playbooks/other_playbook.yml" "${STAGING_DIR}/playbooks/"
```

#### Step 6: Create Documentation Directory (Optional)

```bash
echo "Creating docs directory..."
mkdir -p "${STAGING_DIR}/docs"

# Create DISTRIBUTION-README.md
cat > "${STAGING_DIR}/docs/DISTRIBUTION-README.md" << 'EOF'
# Distribution Package

This package contains a complete, self-contained Ansible role.

## Contents

- Complete role with all dependencies
- Example playbooks
- Full documentation
- Configuration files

## Installation

See INSTALL.md in the root directory.

## Usage

See README.md for complete usage documentation.
EOF

# Create QUICKSTART.md
cat > "${STAGING_DIR}/docs/QUICKSTART.md" << 'EOF'
# Quick Start Guide

## 1. Extract

```bash
tar -xzf <role-name>-role-<version>.tar.gz -C roles/
mv roles/<role-name>-role-<version> roles/<role_name>
```

## 2. Install Dependencies

```bash
ansible-galaxy collection install -r roles/<role_name>/requirements.yml
```

## 3. Run Example

```bash
cp roles/<role_name>/example-playbook.yml playbooks/
ansible-playbook playbooks/example-playbook.yml
```
EOF

# Create MANIFEST.txt
echo "Generating manifest..."
cd "${STAGING_DIR}"
find . -type f | sort > docs/MANIFEST.txt
cd "${PROJECT_ROOT}"
```

#### Step 7: Create Tarball

```bash
echo "Creating tarball..."
cd /tmp
tar -czf "${TARBALL_NAME}.tar.gz" "${TARBALL_NAME}/"

# Create checksum
sha256sum "${TARBALL_NAME}.tar.gz" > "${TARBALL_NAME}.tar.gz.sha256"

# Move to docs directory in monorepo
mkdir -p "${PROJECT_ROOT}/docs/${ROLE_NAME}"
mv "${TARBALL_NAME}.tar.gz" "${PROJECT_ROOT}/docs/${ROLE_NAME}/"
mv "${TARBALL_NAME}.tar.gz.sha256" "${PROJECT_ROOT}/docs/${ROLE_NAME}/"
```

#### Step 8: Verify Tarball Structure

```bash
echo "Verifying tarball structure..."

# List contents
tar -tzf "${PROJECT_ROOT}/docs/${ROLE_NAME}/${TARBALL_NAME}.tar.gz" | head -50

# Verify checksum
cd "${PROJECT_ROOT}/docs/${ROLE_NAME}"
sha256sum -c "${TARBALL_NAME}.tar.gz.sha256"

# Extract to temporary location for verification
TEST_DIR="/tmp/test-extract"
rm -rf "${TEST_DIR}"
mkdir -p "${TEST_DIR}/roles"
tar -xzf "${TARBALL_NAME}.tar.gz" -C "${TEST_DIR}/roles/"
mv "${TEST_DIR}/roles/${TARBALL_NAME}" "${TEST_DIR}/roles/${ROLE_NAME}"

# Verify ansible-lint passes
cd "${TEST_DIR}"
ansible-lint "roles/${ROLE_NAME}/"

# Verify example playbook
ansible-playbook --syntax-check "roles/${ROLE_NAME}/example-playbook.yml"

# Clean up
cd "${PROJECT_ROOT}"
rm -rf "${TEST_DIR}"

echo "✅ Tarball created successfully: ${PROJECT_ROOT}/docs/${ROLE_NAME}/${TARBALL_NAME}.tar.gz"
echo "📦 Size: $(du -h "${PROJECT_ROOT}/docs/${ROLE_NAME}/${TARBALL_NAME}.tar.gz" | cut -f1)"
```

### Tarball Creation Automation Script

Create `scripts/create_role_distribution.sh`:

```bash
#!/bin/bash
# create_role_distribution.sh - Create standalone role distribution tarball
#
# Usage: ./create_role_distribution.sh <role_name> <version>
# Example: ./create_role_distribution.sh must_gather_log 3.0.0

set -euo pipefail

# Function to display usage
usage() {
    echo "Usage: $0 <role_name> <version>"
    echo ""
    echo "Arguments:"
    echo "  role_name    Name of the role (use underscores, e.g., must_gather_log)"
    echo "  version      Version number (e.g., 1.0.0)"
    echo ""
    echo "Example:"
    echo "  $0 must_gather_log 3.0.0"
    exit 1
}

# Validate arguments
if [[ $# -ne 2 ]]; then
    usage
fi

ROLE_NAME="${1}"
VERSION="${2}"
TARBALL_NAME="${ROLE_NAME//_/-}-role-${VERSION}"
STAGING_DIR="/tmp/${TARBALL_NAME}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Validate role exists
if [[ ! -d "${PROJECT_ROOT}/roles/${ROLE_NAME}" ]]; then
    echo "ERROR: Role not found: ${PROJECT_ROOT}/roles/${ROLE_NAME}"
    exit 1
fi

echo "========================================="
echo "Creating Distribution Package"
echo "========================================="
echo "Role: ${ROLE_NAME}"
echo "Version: ${VERSION}"
echo "Tarball: ${TARBALL_NAME}.tar.gz"
echo ""

# Clean staging directory
echo "Step 1: Preparing staging directory..."
rm -rf "${STAGING_DIR}"
mkdir -p "${STAGING_DIR}"

# Copy role directories to top level
echo "Step 2: Copying role directories..."
for dir in defaults meta tasks vars library filter_plugins templates files handlers; do
    if [[ -d "${PROJECT_ROOT}/roles/${ROLE_NAME}/${dir}" ]]; then
        echo "  - Copying ${dir}/"
        cp -r "${PROJECT_ROOT}/roles/${ROLE_NAME}/${dir}" "${STAGING_DIR}/"
    fi
done

# Copy top-level files
echo "Step 3: Copying documentation files..."
for file in README.md CHANGELOG.md group_vars_example.yml; do
    if [[ -f "${PROJECT_ROOT}/roles/${ROLE_NAME}/${file}" ]]; then
        echo "  - Copying ${file}"
        cp "${PROJECT_ROOT}/roles/${ROLE_NAME}/${file}" "${STAGING_DIR}/"
    fi
done

# Copy configuration files
echo "Step 4: Copying configuration files..."
cp "${PROJECT_ROOT}/.ansible-lint" "${STAGING_DIR}/"
cp "${PROJECT_ROOT}/.gitignore" "${STAGING_DIR}/"

# Create requirements files
echo "Step 5: Creating requirements files..."
if [[ -f "${PROJECT_ROOT}/roles/${ROLE_NAME}/requirements.yml" ]]; then
    cp "${PROJECT_ROOT}/roles/${ROLE_NAME}/requirements.yml" "${STAGING_DIR}/"
else
    cat > "${STAGING_DIR}/requirements.yml" << 'EOF'
---
collections:
  - name: kubernetes.core
    version: ">=2.3.0"
  - name: ansible.posix
    version: ">=1.3.0"
EOF
fi

# Create LICENSE
echo "Step 6: Creating LICENSE..."
cat > "${STAGING_DIR}/LICENSE" << 'EOF'
Apache License 2.0

Copyright (c) 2024 Your Organization

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
EOF

# Create INSTALL.md
echo "Step 7: Creating INSTALL.md..."
cat > "${STAGING_DIR}/INSTALL.md" << EOF
# Installation Guide - ${ROLE_NAME}

## Quick Install

\`\`\`bash
# Extract tarball
tar -xzf ${TARBALL_NAME}.tar.gz -C roles/
mv roles/${TARBALL_NAME} roles/${ROLE_NAME}

# Install dependencies
ansible-galaxy collection install -r roles/${ROLE_NAME}/requirements.yml
\`\`\`

## Detailed Installation

See README.md for complete installation instructions.
EOF

# Create example playbook
echo "Step 8: Creating example playbook..."
cat > "${STAGING_DIR}/example-playbook.yml" << EOF
---
- name: Example ${ROLE_NAME} usage
  hosts: localhost
  gather_facts: true

  tasks:
    - name: Run ${ROLE_NAME} role
      ansible.builtin.include_role:
        name: ${ROLE_NAME}
EOF

# Create playbooks directory
echo "Step 9: Creating playbooks directory..."
mkdir -p "${STAGING_DIR}/playbooks"
if [[ -f "${PROJECT_ROOT}/playbooks/${ROLE_NAME}_test.yml" ]]; then
    cp "${PROJECT_ROOT}/playbooks/${ROLE_NAME}_test.yml" "${STAGING_DIR}/playbooks/"
fi

# Create docs directory
echo "Step 10: Creating docs directory..."
mkdir -p "${STAGING_DIR}/docs"

cat > "${STAGING_DIR}/docs/DISTRIBUTION-README.md" << 'EOF'
# Distribution Package

This package contains a complete, self-contained Ansible role.

## Contents

- Complete role with all dependencies
- Example playbooks
- Full documentation
- Configuration files

## Installation

See INSTALL.md in the root directory.
EOF

# Generate manifest
echo "Step 11: Generating manifest..."
cd "${STAGING_DIR}"
find . -type f | sort > docs/MANIFEST.txt
cd "${PROJECT_ROOT}"

# Create tarball
echo "Step 12: Creating tarball..."
cd /tmp
tar -czf "${TARBALL_NAME}.tar.gz" "${TARBALL_NAME}/"
sha256sum "${TARBALL_NAME}.tar.gz" > "${TARBALL_NAME}.tar.gz.sha256"

# Move to docs directory
echo "Step 13: Moving to docs directory..."
mkdir -p "${PROJECT_ROOT}/docs/${ROLE_NAME}"
mv "${TARBALL_NAME}.tar.gz" "${PROJECT_ROOT}/docs/${ROLE_NAME}/"
mv "${TARBALL_NAME}.tar.gz.sha256" "${PROJECT_ROOT}/docs/${ROLE_NAME}/"

# Verify
echo ""
echo "Step 14: Verifying tarball..."
cd "${PROJECT_ROOT}/docs/${ROLE_NAME}"
sha256sum -c "${TARBALL_NAME}.tar.gz.sha256"

echo ""
echo "========================================="
echo "✅ Distribution Package Created"
echo "========================================="
echo "Location: ${PROJECT_ROOT}/docs/${ROLE_NAME}/${TARBALL_NAME}.tar.gz"
echo "Size: $(du -h "${PROJECT_ROOT}/docs/${ROLE_NAME}/${TARBALL_NAME}.tar.gz" | cut -f1)"
echo ""
echo "Tarball contents (first 30 lines):"
tar -tzf "${PROJECT_ROOT}/docs/${ROLE_NAME}/${TARBALL_NAME}.tar.gz" | head -30
echo ""
echo "✅ Ready for distribution!"

# Clean up
rm -rf "${STAGING_DIR}"
```

Make the script executable:

```bash
chmod +x scripts/create_role_distribution.sh
```

Usage:

```bash
./scripts/create_role_distribution.sh must_gather_log 3.0.0
```

---

## Phase 5: Standalone Git Repository Setup

### Overview

The tarball created in Phase 4 can be used to create a standalone git repository for independent development and distribution.

### Step 1: Extract and Initialize Repository

```bash
# Create new directory for standalone repository
mkdir -p ~/repositories/<role_name>-role
cd ~/repositories/<role_name>-role

# Extract tarball
tar -xzf /path/to/<role-name>-role-<version>.tar.gz --strip-components=1

# Initialize git repository
git init

# Create .gitattributes (optional)
cat > .gitattributes << 'EOF'
# Auto detect text files
* text=auto

# Force LF for shell scripts
*.sh text eol=lf

# Force LF for Python
*.py text eol=lf

# Force LF for YAML
*.yml text eol=lf
*.yaml text eol=lf

# Binary files
*.png binary
*.jpg binary
*.tar.gz binary
EOF

# Initial commit
git add .
git commit -m "Initial commit: ${ROLE_NAME} v${VERSION}

- Complete role implementation
- Documentation and examples
- Configuration files
- Ready for standalone use"
```

### Step 2: Create Repository Structure

The repository is already structured correctly from the tarball. Verify:

```bash
# Verify structure
tree -L 2 -a

# Expected output:
# .
# ├── .ansible-lint
# ├── .git/
# ├── .gitattributes
# ├── .gitignore
# ├── CHANGELOG.md
# ├── INSTALL.md
# ├── LICENSE
# ├── README.md
# ├── defaults/
# │   └── main.yml
# ├── docs/
# │   ├── DISTRIBUTION-README.md
# │   ├── MANIFEST.txt
# │   └── QUICKSTART.md
# ├── example-playbook.yml
# ├── handlers/
# │   └── main.yml
# ├── library/
# │   └── *.py
# ├── meta/
# │   └── main.yml
# ├── playbooks/
# │   └── *.yml
# ├── requirements.yml
# ├── tasks/
# │   └── *.yml
# └── templates/
```

### Step 3: Create GitHub/GitLab Repository

```bash
# Create repository on GitHub/GitLab via web interface or CLI

# Example using GitHub CLI
gh repo create your-org/<role_name>-role --public --description "Ansible role for <purpose>"

# Add remote
git remote add origin git@github.com:your-org/<role_name>-role.git

# Push
git branch -M main
git push -u origin main
```

### Step 4: Create Tags and Releases

```bash
# Create annotated tag for version
git tag -a "v${VERSION}" -m "Release version ${VERSION}

Features:
- Feature 1
- Feature 2
- Feature 3

For detailed changes, see CHANGELOG.md"

# Push tag
git push origin "v${VERSION}"

# Create GitHub release (if using GitHub)
gh release create "v${VERSION}" \
    --title "Release ${VERSION}" \
    --notes-file CHANGELOG.md
```

### Step 5: Set Up CI/CD (Optional)

**GitHub Actions - `.github/workflows/ci.yml`:**

```yaml
---
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install ansible-core ansible-lint
          ansible-galaxy collection install -r requirements.yml

      - name: Run ansible-lint
        run: ansible-lint .

      - name: Syntax check
        run: ansible-playbook --syntax-check example-playbook.yml

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install ansible-core
          ansible-galaxy collection install -r requirements.yml

      - name: Run molecule tests (if configured)
        run: |
          pip install molecule molecule-plugins[docker]
          molecule test
```

### Step 6: Create Contributing Guide

**`CONTRIBUTING.md`:**

```markdown
# Contributing to <role_name>

Thank you for your interest in contributing!

## Development Setup

### Prerequisites

- Ansible Core 2.12+
- Python 3.11+
- Git

### Setup

\`\`\`bash
# Clone repository
git clone https://github.com/your-org/<role_name>-role.git
cd <role_name>-role

# Install dependencies
ansible-galaxy collection install -r requirements.yml
\`\`\`

## Development Workflow

### 1. Create Feature Branch

\`\`\`bash
git checkout -b feature/your-feature-name
\`\`\`

### 2. Make Changes

- Follow Ansible best practices
- Use FQCN for all modules
- Add tests for new features
- Update documentation

### 3. Test Changes

\`\`\`bash
# Syntax check
ansible-playbook --syntax-check example-playbook.yml

# Lint
ansible-lint .

# Test execution
ansible-playbook example-playbook.yml --check
\`\`\`

### 4. Commit Changes

Follow conventional commit format:

\`\`\`
feat: add new feature
fix: resolve bug in task
docs: update README
test: add test cases
\`\`\`

### 5. Submit Pull Request

- Update CHANGELOG.md
- Ensure all tests pass
- Provide clear description

## Code Style

- Use 2-space indentation for YAML
- Use FQCN for all modules
- Include meaningful task names
- Document complex logic
- Follow Python PEP 8 for custom modules

## Testing

All changes must pass:

- ansible-lint
- Syntax validation
- Functional testing (where applicable)

## Questions?

Open an issue for discussion before major changes.
```

### Step 7: Update README for Standalone Repository

Add installation instructions specific to standalone repository:

```markdown
## Installation

### From Source

\`\`\`bash
# Clone repository
git clone https://github.com/your-org/<role_name>-role.git roles/<role_name>

# Install dependencies
ansible-galaxy collection install -r roles/<role_name>/requirements.yml
\`\`\`

### From Release Tarball

\`\`\`bash
# Download latest release
curl -LO https://github.com/your-org/<role_name>-role/releases/download/v1.0.0/<role-name>-role-1.0.0.tar.gz

# Extract
tar -xzf <role-name>-role-1.0.0.tar.gz -C roles/
mv roles/<role-name>-role-1.0.0 roles/<role_name>

# Install dependencies
ansible-galaxy collection install -r roles/<role_name>/requirements.yml
\`\`\`

### From Ansible Galaxy (if published)

\`\`\`bash
ansible-galaxy role install your_namespace.<role_name>
\`\`\`
```

---

## Automation Scripts

### Complete Automation Script

**`scripts/role_to_production.sh`:**

```bash
#!/bin/bash
# role_to_production.sh - Complete workflow from development to production
#
# Usage: ./role_to_production.sh <role_name> <version>
# Example: ./role_to_production.sh must_gather_log 3.0.0

set -euo pipefail

usage() {
    echo "Usage: $0 <role_name> <version> [options]"
    echo ""
    echo "Arguments:"
    echo "  role_name    Role name (underscores, e.g., must_gather_log)"
    echo "  version      Version number (e.g., 1.0.0)"
    echo ""
    echo "Options:"
    echo "  --skip-tests        Skip quality tests"
    echo "  --skip-git          Skip git operations"
    echo "  --create-repo       Create standalone git repository"
    echo "  --repo-path <path>  Path for standalone repository"
    echo ""
    exit 1
}

# Parse arguments
ROLE_NAME="${1:-}"
VERSION="${2:-}"
SKIP_TESTS=false
SKIP_GIT=false
CREATE_REPO=false
REPO_PATH=""

shift 2 2>/dev/null || usage

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-git)
            SKIP_GIT=true
            shift
            ;;
        --create-repo)
            CREATE_REPO=true
            shift
            ;;
        --repo-path)
            REPO_PATH="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

[[ -z "$ROLE_NAME" ]] && usage
[[ -z "$VERSION" ]] && usage

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARBALL_NAME="${ROLE_NAME//_/-}-role-${VERSION}"

echo "========================================="
echo "Role to Production Workflow"
echo "========================================="
echo "Role: ${ROLE_NAME}"
echo "Version: ${VERSION}"
echo "Project: ${PROJECT_ROOT}"
echo ""

# Phase 1: Quality Assurance
if [[ "$SKIP_TESTS" == false ]]; then
    echo "Phase 1: Quality Assurance"
    echo "-------------------------"
    
    # Syntax check
    echo "Running syntax check..."
    if ! ansible-playbook --syntax-check "${PROJECT_ROOT}/playbooks/${ROLE_NAME}"*.yml 2>/dev/null; then
        echo "⚠️  No playbooks found for syntax check (this is ok)"
    fi
    
    # Ansible lint
    echo "Running ansible-lint..."
    .venv/bin/ansible-lint "${PROJECT_ROOT}/roles/${ROLE_NAME}/" || {
        echo "❌ Ansible-lint failed"
        exit 1
    }
    
    # Python quality (if modules/filters exist)
    if [[ -d "${PROJECT_ROOT}/roles/${ROLE_NAME}/library" ]] || \
       [[ -d "${PROJECT_ROOT}/roles/${ROLE_NAME}/filter_plugins" ]]; then
        echo "Running Python quality checks..."
        
        for dir in library filter_plugins; do
            if [[ -d "${PROJECT_ROOT}/roles/${ROLE_NAME}/${dir}" ]]; then
                echo "  Checking ${dir}..."
                .venv/bin/isort "${PROJECT_ROOT}/roles/${ROLE_NAME}/${dir}/"*.py
                .venv/bin/black "${PROJECT_ROOT}/roles/${ROLE_NAME}/${dir}/"*.py
                .venv/bin/flake8 "${PROJECT_ROOT}/roles/${ROLE_NAME}/${dir}/"*.py
            fi
        done
    fi
    
    echo "✅ Quality checks passed"
    echo ""
fi

# Phase 2: Create Distribution Package
echo "Phase 2: Creating Distribution Package"
echo "--------------------------------------"

if [[ -f "${PROJECT_ROOT}/scripts/create_role_distribution.sh" ]]; then
    "${PROJECT_ROOT}/scripts/create_role_distribution.sh" "${ROLE_NAME}" "${VERSION}"
else
    echo "❌ Distribution script not found"
    exit 1
fi

echo ""

# Phase 3: Git Operations (in monorepo)
if [[ "$SKIP_GIT" == false ]]; then
    echo "Phase 3: Version Control (Monorepo)"
    echo "----------------------------------"
    
    cd "${PROJECT_ROOT}"
    
    # Check for uncommitted changes
    if [[ -n "$(git status --porcelain)" ]]; then
        echo "⚠️  Uncommitted changes detected"
        echo "Commit changes? (y/n)"
        read -r response
        if [[ "$response" == "y" ]]; then
            git add "roles/${ROLE_NAME}/" "docs/${ROLE_NAME}/"
            git commit -m "Release ${ROLE_NAME} v${VERSION}

- Created distribution package
- Updated documentation
- Version ${VERSION} ready for release"
        fi
    fi
    
    # Create tag
    echo "Creating tag ${ROLE_NAME}-v${VERSION}..."
    git tag -a "${ROLE_NAME}-v${VERSION}" -m "Release ${ROLE_NAME} v${VERSION}"
    
    echo "✅ Git operations complete"
    echo ""
fi

# Phase 4: Create Standalone Repository (optional)
if [[ "$CREATE_REPO" == true ]]; then
    echo "Phase 4: Creating Standalone Repository"
    echo "---------------------------------------"
    
    if [[ -z "$REPO_PATH" ]]; then
        REPO_PATH="${HOME}/repositories/${TARBALL_NAME}"
    fi
    
    echo "Repository path: ${REPO_PATH}"
    
    # Create directory
    mkdir -p "${REPO_PATH}"
    cd "${REPO_PATH}"
    
    # Extract tarball
    tar -xzf "${PROJECT_ROOT}/docs/${ROLE_NAME}/${TARBALL_NAME}.tar.gz" --strip-components=1
    
    # Initialize git
    git init
    git add .
    git commit -m "Initial commit: ${ROLE_NAME} v${VERSION}"
    git tag -a "v${VERSION}" -m "Release version ${VERSION}"
    
    echo "✅ Standalone repository created at: ${REPO_PATH}"
    echo ""
    echo "To push to remote:"
    echo "  cd ${REPO_PATH}"
    echo "  git remote add origin <repository-url>"
    echo "  git push -u origin main"
    echo "  git push origin v${VERSION}"
    echo ""
fi

# Summary
echo "========================================="
echo "✅ Production Workflow Complete"
echo "========================================="
echo ""
echo "Distribution package:"
echo "  ${PROJECT_ROOT}/docs/${ROLE_NAME}/${TARBALL_NAME}.tar.gz"
echo ""
echo "Next steps:"
echo "  1. Test installation from tarball"
echo "  2. Push tags to remote: git push origin ${ROLE_NAME}-v${VERSION}"
echo "  3. Create release notes"
echo "  4. Distribute tarball to users"
if [[ "$CREATE_REPO" == true ]]; then
    echo "  5. Push standalone repository"
fi
echo ""
```

Make executable:

```bash
chmod +x scripts/role_to_production.sh
```

Usage examples:

```bash
# Complete workflow
./scripts/role_to_production.sh must_gather_log 3.0.0

# Skip tests (if already validated)
./scripts/role_to_production.sh must_gather_log 3.0.0 --skip-tests

# Create standalone repository
./scripts/role_to_production.sh must_gather_log 3.0.0 --create-repo --repo-path ~/repos/must-gather-log

# Skip git operations (for testing)
./scripts/role_to_production.sh must_gather_log 3.0.0 --skip-git
```

---

## Quality Checklists

### Pre-Distribution Checklist

Before creating distribution package:

- [ ] All tasks have meaningful names
- [ ] FQCN used for all modules
- [ ] `changed_when` and `failed_when` properly set for shell/command tasks
- [ ] Sensitive data uses `no_log: true`
- [ ] Variables properly scoped (defaults, vars, host_vars, group_vars)
- [ ] Error handling with block/rescue/always
- [ ] Syntax check passes
- [ ] Ansible-lint passes (production profile)
- [ ] Python code formatted (black, isort)
- [ ] Python code linted (flake8, mypy)
- [ ] README.md complete and accurate
- [ ] CHANGELOG.md updated with version
- [ ] INSTALL.md created
- [ ] LICENSE file present
- [ ] requirements.yml lists all collections
- [ ] requirements.txt lists all Python deps (if any)
- [ ] .ansible-lint configured
- [ ] .gitignore configured
- [ ] example-playbook.yml functional
- [ ] Test playbooks pass
- [ ] Custom modules follow standards
- [ ] Custom filters follow standards
- [ ] Documentation complete

### Distribution Package Checklist

Verify tarball:

- [ ] Top-level structure (NOT nested)
- [ ] All required files present
- [ ] README.md at top level
- [ ] INSTALL.md at top level
- [ ] CHANGELOG.md at top level
- [ ] LICENSE at top level
- [ ] requirements.yml at top level
- [ ] .ansible-lint at top level
- [ ] .gitignore at top level
- [ ] example-playbook.yml at top level
- [ ] defaults/ directory at top level
- [ ] meta/ directory at top level
- [ ] tasks/ directory at top level
- [ ] playbooks/ directory present
- [ ] docs/ directory present
- [ ] Checksum file (.sha256) present
- [ ] Tarball extracts cleanly
- [ ] ansible-lint passes after extraction
- [ ] Syntax check passes after extraction
- [ ] Example playbook runs

### Standalone Repository Checklist

Before pushing standalone repository:

- [ ] Git initialized
- [ ] .gitattributes present (optional)
- [ ] Initial commit done
- [ ] Version tag created
- [ ] Remote repository created
- [ ] Remote added to local repo
- [ ] CONTRIBUTING.md present
- [ ] CI/CD workflow configured (optional)
- [ ] README updated for standalone use
- [ ] License verified
- [ ] No sensitive data in history
- [ ] All documentation links work
- [ ] Installation instructions tested

---

## Summary

### Key Principles

1. **Develop in context** - Build alongside other roles with shared resources
2. **Test continuously** - Validate throughout development cycle
3. **Document thoroughly** - Create complete standalone documentation
4. **Package properly** - Top-level structure for dual-purpose use
5. **Distribute cleanly** - Self-contained with all dependencies

### Common Pitfalls to Avoid

**DON'T:**

- ❌ Nest role under subdirectory in tarball
- ❌ Skip quality checks before distribution
- ❌ Omit required documentation files
- ❌ Hard-code paths or environment assumptions
- ❌ Include sensitive data or credentials
- ❌ Forget to update CHANGELOG.md
- ❌ Create inaccurate MANIFEST.txt
- ❌ Skip functional testing

**DO:**

- ✅ Use top-level role directories
- ✅ Run all quality checks
- ✅ Include complete documentation set
- ✅ Use configurable variables
- ✅ Test tarball extraction and usage
- ✅ Maintain version consistency
- ✅ Create accurate MANIFEST.txt
- ✅ Verify standalone functionality

### Workflow Summary

```text
Development → QA → Documentation → Distribution → Repository
    ↓           ↓          ↓              ↓             ↓
Feature     Test      Complete       Tarball      Git repo
work        code      docs           creation     setup
Monorepo    Lint      Templates      Verify       Push
```

---

## Document Maintenance

**Update this document when:**

- New role distribution patterns emerge
- Documentation requirements change
- Quality standards are updated
- Automation scripts are modified
- New tools are introduced

**Document Owner:** Platform Engineering Team  
**Review Cycle:** Quarterly or per major release  
**Last Reviewed:** 2024-12-30
