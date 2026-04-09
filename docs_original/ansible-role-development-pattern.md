# Ansible Role Development and Distribution Pattern

**Document Version:** 1.0.0
**Last Updated:** 2024-12-28
**Applies To:** Enterprise Ansible Automation Platform projects

## Overview

This document defines the standard pattern for developing Ansible roles within a monorepo structure and creating standalone distribution packages for external use or independent git repositories.

## Table of Contents

1. [Development Phase: Role in Monorepo](#development-phase-role-in-monorepo)
2. [Distribution Phase: Standalone Tarball Creation](#distribution-phase-standalone-tarball-creation)
3. [Tarball Structure Pattern](#tarball-structure-pattern)
4. [Documentation Requirements](#documentation-requirements)
5. [Quality Standards](#quality-standards)
6. [Examples](#examples)

---

## Development Phase: Role in Monorepo

### Directory Structure

During development, roles exist within the monorepo at `roles/<role_name>/`:

```text
ansible-playground/                    # Monorepo root
├── roles/
│   └── <role_name>/                  # Role under development
│       ├── README.md                 # Role documentation
│       ├── CHANGELOG.md              # Version history
│       ├── defaults/
│       │   └── main.yml             # Default variables
│       ├── meta/
│       │   └── main.yml             # Role metadata
│       ├── library/                  # Custom modules (optional)
│       │   └── *.py
│       ├── filter_plugins/           # Custom filters (optional)
│       │   └── *.py
│       ├── tasks/
│       │   └── *.yml                # Task files
│       ├── templates/                # Jinja2 templates (optional)
│       ├── files/                    # Static files (optional)
│       ├── vars/                     # Role variables (optional)
│       │   └── main.yml
│       └── group_vars_example.yml    # Example group variables
├── playbooks/
│   └── <role_playbook>.yml          # Playbooks using the role
├── docs/
│   └── <role_name>/                 # Role-specific documentation
│       ├── architecture.md
│       ├── usage_examples.md
│       └── ...
└── .ansible-lint                     # Shared linting config
```

### Development Workflow

1. **Create role structure**: Use `ansible-galaxy init roles/<role_name>` or manual creation
2. **Implement role logic**: Follow modular task architecture pattern
3. **Create playbooks**: Add usage examples in `playbooks/`
4. **Document**: Maintain README.md and CHANGELOG.md
5. **Test**: Use ansible-lint, syntax checks, and execution tests
6. **Commit**: Version control within monorepo feature branches

### Modular Task Architecture (Recommended)

**Pattern**: Orchestrator delegation to specialized task files

**Example Structure**:

```yaml
# roles/<role_name>/tasks/main.yml (Orchestrator)
---
# Phase 1: Preparation
- name: "Prepare environment"
  ansible.builtin.include_tasks: preparation.yml
  tags: [preparation]

# Phase 2: Execution
- name: "Execute main workflow"
  ansible.builtin.include_tasks: execution.yml
  tags: [execution]

# Phase 3: Validation
- name: "Validate results"
  ansible.builtin.include_tasks: validation.yml
  tags: [validation]
```

**Benefits**:

- Clear separation of concerns
- Independent testing of components
- Reusable task files
- Easier maintenance and troubleshooting
- Reduced main.yml complexity

**Guidelines**:

- Keep main.yml as simple orchestrator (< 500 lines)
- Create specialized task files for distinct workflows
- Use descriptive task file names (e.g., `vault_retrieve_credentials.yml`)
- Document each task file with header comments
- Use tags for selective execution

---

## Distribution Phase: Standalone Tarball Creation

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

### Required Files for Standalone Distribution

**Top-Level Files** (at tarball root):

```text
<role-name>-role-<version>/
├── README.md                    # Complete role documentation
├── INSTALL.md                   # Installation guide
├── CHANGELOG.md                 # Version history
├── LICENSE                      # Apache-2.0 or appropriate license
├── requirements.yml             # Ansible collection dependencies
├── .ansible-lint               # Linting configuration
├── .gitignore                  # Git ignore patterns
├── example-playbook.yml         # Simple usage example
└── group_vars_example.yml       # Example group variables (if applicable)
```

**Role Directories** (at top level, NOT nested):

```text
<role-name>-role-<version>/
├── defaults/
│   └── main.yml                # Default variables
├── meta/
│   └── main.yml                # Role metadata
├── library/                     # Custom modules (if applicable)
│   └── *.py
├── filter_plugins/              # Custom filters (if applicable)
│   └── *.py
├── tasks/
│   └── *.yml                   # All task files
├── templates/                   # Jinja2 templates (if applicable)
├── files/                       # Static files (if applicable)
└── vars/                        # Role variables (if applicable)
    └── main.yml
```

**Playbooks Directory** (example playbooks):

```text
<role-name>-role-<version>/
└── playbooks/
    ├── <main-playbook>.yml     # Primary usage playbook
    └── <additional>.yml         # Additional use cases
```

**Documentation Directory**:

```text
<role-name>-role-<version>/
└── docs/
    ├── DISTRIBUTION-README.md   # Distribution package notes
    ├── QUICKSTART.md           # Quick start guide
    ├── ROLE-README.md          # Full role documentation (copy of role README)
    ├── MANIFEST.txt            # Package contents manifest
    └── example-playbook.yml    # Complete example playbook
```

---

## Tarball Structure Pattern

### Critical Pattern: Top-Level Role Directories

**CORRECT PATTERN** (following portworx-upgrade-role example):

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

**INCORRECT PATTERN** (nested role structure):

```text
# DO NOT USE THIS STRUCTURE
<role-name>-role-<version>/
├── README.md
└── <role_name>/                # WRONG: Role nested under subdirectory
    ├── defaults/
    ├── meta/
    ├── tasks/
    └── ...
```

### Why Top-Level Structure?

1. **Dual-purpose usage**:
   - Extract to `roles/` directory: `tar -xzf role.tar.gz -C roles/ && mv roles/<role-name>-role-<version> roles/<role_name>`
   - Use as standalone git repository: `tar -xzf role.tar.gz && cd <role-name>-role-<version> && git init`

2. **Ansible role discovery**: Ansible expects role directories at the top level of a role path

3. **Simplified installation**: No nested directory navigation required

4. **Git repository readiness**: Can immediately become a git repository without restructuring

### Creating the Tarball

#### **Step 1: Create staging directory**

```bash
mkdir -p /tmp/<role-name>-role-<version>
```

#### **Step 2: Copy role directories to top level**

```bash
# Copy role directories (NOT the role parent directory)
cp -r roles/<role_name>/defaults /tmp/<role-name>-role-<version>/
cp -r roles/<role_name>/meta /tmp/<role-name>-role-<version>/
cp -r roles/<role_name>/tasks /tmp/<role-name>-role-<version>/
cp -r roles/<role_name>/library /tmp/<role-name>-role-<version>/  # if exists
# ... copy all role directories individually
```

#### **Step 3: Copy top-level files**

```bash
cp roles/<role_name>/README.md /tmp/<role-name>-role-<version>/
cp roles/<role_name>/CHANGELOG.md /tmp/<role-name>-role-<version>/
# ... copy all required top-level files
```

#### **Step 4: Create documentation**

```bash
mkdir -p /tmp/<role-name>-role-<version>/docs
# Create/copy: DISTRIBUTION-README.md, QUICKSTART.md, ROLE-README.md, MANIFEST.txt
```

#### **Step 5: Create playbooks directory**

```bash
mkdir -p /tmp/<role-name>-role-<version>/playbooks
cp playbooks/<role-playbook>.yml /tmp/<role-name>-role-<version>/playbooks/
```

#### **Step 6: Add configuration files**

```bash
cp .ansible-lint /tmp/<role-name>-role-<version>/
cp .gitignore /tmp/<role-name>-role-<version>/
# Create requirements.yml with required collections
```

#### **Step 7: Create tarball**

```bash
cd /tmp
tar -czf <role-name>-role-<version>.tar.gz <role-name>-role-<version>/
```

#### **Step 8: Store in docs**

```bash
mv <role-name>-role-<version>.tar.gz /path/to/project/docs/<role_name>/
```

---

## Documentation Requirements

### 1. README.md (Top Level)

**Purpose**: Complete role documentation for users

**Required Sections**:

```markdown
# Role Name

Brief description

## Features

- Key feature 1
- Key feature 2

## Requirements

- Ansible Core version
- Python version
- Required collections
- External dependencies

## Installation

### From Tarball
```bash
tar -xzf <role-name>-role-<version>.tar.gz -C roles/
mv roles/<role-name>-role-<version> roles/<role_name>
ansible-galaxy collection install -r roles/<role_name>/requirements.yml
```

### As Git Repository

```bash
tar -xzf <role-name>-role-<version>.tar.gz
cd <role-name>-role-<version>
git init
git add .
git commit -m "Initial commit: <role_name> role v<version>"
```

## Variables

### Required Variables

- `var_name`: Description

### Optional Variables

- `var_name`: Description (default: value)

## Usage

### Basic Example

```yaml
- name: Example playbook
  hosts: localhost
  roles:
    - role: <role_name>
      var_name: value
```

### Advanced Examples

See `playbooks/` directory and `docs/example-playbook.yml`

## Architecture

Brief architecture overview

## Tags

Available tags for selective execution

## Dependencies

Collections and roles required

## License

Apache-2.0

## Author

Name and contact

### 2. INSTALL.md

**Purpose**: Step-by-step installation instructions

**Required Sections**:

- Prerequisites
- Installation methods (tarball, git clone)
- Dependency installation
- Verification steps
- Troubleshooting

### 3. CHANGELOG.md

**Purpose**: Version history and release notes

**Format**:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Version] - YYYY-MM-DD

### Added
- New feature descriptions

### Changed
- Modified behavior descriptions

### Fixed
- Bug fix descriptions

### Removed
- Removed feature descriptions

### Security
- Security-related changes
```

### 4. docs/DISTRIBUTION-README.md

**Purpose**: Tarball-specific distribution notes

**Required Sections**:

- Package information (version, size, date)
- Tarball structure tree
- Quick installation guide
- Using as git repository
- Documentation references

### 5. docs/QUICKSTART.md

**Purpose**: Fast-track usage guide with common scenarios

**Required Sections**:

- Installation (condensed)
- Basic usage scenarios (3-5 examples)
- Common configuration patterns
- Documentation references
- Next steps

### 6. docs/ROLE-README.md

**Purpose**: Copy of main README.md for reference within docs/

**Content**: Identical to top-level README.md

### 7. docs/MANIFEST.txt

**Purpose**: Complete package contents inventory

**Required Sections**:

```text
=============================================================================
<Role Name> v<version> - Distribution Package Manifest
=============================================================================

PACKAGE INFORMATION
-------------------
File: <role-name>-role-<version>.tar.gz
Size: <size> KB
Version: <version>
Release Date: YYYY-MM-DD
License: Apache-2.0

PACKAGE CONTENTS
----------------
Total Files: <count>
Total Directories: <count>

ROOT FILES (<count>):
  - README.md (Complete role documentation)
  - INSTALL.md (Installation guide)
  - CHANGELOG.md (Version history)
  - LICENSE (Apache-2.0 license)
  - requirements.yml (Ansible collection dependencies)
  - .ansible-lint (Linting configuration)
  - .gitignore (Git ignore patterns)
  - example-playbook.yml (Example usage playbook)

PLAYBOOKS (<count>):
  playbooks/
    - <playbook-name>.yml (Description)

ROLE DIRECTORIES (<count>):
  defaults/
    - main.yml (Default variables)

  meta/
    - main.yml (Role metadata)

  library/
    - <module>.py (Custom module - description)

  tasks/ (<count> modular task files)
    - main.yml (Main orchestrator)
    - <task-file>.yml (Description)

DOCUMENTATION (<count>):
  docs/
    - DISTRIBUTION-README.md (Distribution package notes)
    - QUICKSTART.md (Quick start guide)
    - ROLE-README.md (Complete role documentation)
    - MANIFEST.txt (This file)
    - example-playbook.yml (Example playbook)

KEY FEATURES
------------
1. Feature 1
2. Feature 2

DEPENDENCIES
------------
Ansible Collections:
  - collection.name >= version

System Requirements:
  - Ansible Core >= version
  - Python >= version
  - External tools

SETUP INSTRUCTIONS
------------------
1. Extract tarball:
   tar -xzf <role-name>-role-<version>.tar.gz -C roles/
   mv roles/<role-name>-role-<version> roles/<role_name>

2. Install dependencies:
   ansible-galaxy collection install -r roles/<role_name>/requirements.yml

3. Run example playbook:
   ansible-playbook playbooks/<playbook>.yml

USING AS GIT REPOSITORY
------------------------
cd <role-name>-role-<version>
git init
git add .
git commit -m "Initial commit: <role_name> role v<version>"
git remote add origin <your-git-url>
git push -u origin main

DOCUMENTATION
-------------
- Installation Guide: INSTALL.md
- Quick Start: README.md (role root)
- Quick Start Guide: docs/QUICKSTART.md
- Distribution Notes: docs/DISTRIBUTION-README.md
- Full Documentation: docs/ROLE-README.md
- Version History: CHANGELOG.md
- Example Playbooks: playbooks/ and example-playbook.yml

QUALITY ASSURANCE
-----------------
All files pass:
  ✓ ansible-lint (production profile)
  ✓ black (Python formatting)
  ✓ isort (Python import sorting)
  ✓ flake8 (Python linting)
  ✓ Syntax validation (all playbooks)

BACKWARD COMPATIBILITY
----------------------
Version <version> compatibility notes

=============================================================================
For support, see README.md and docs/QUICKSTART.md
=============================================================================
```

### 8. docs/example-playbook.yml

**Purpose**: Complete, production-ready example playbook

**Requirements**:

- Fully functional example
- Common use case demonstration
- Variable examples
- Comments explaining configuration
- Error handling example

### 9. example-playbook.yml (Top Level)

**Purpose**: Simplified quick-start example

**Requirements**:

- Minimal viable example
- Basic variable usage
- Clear and concise
- 20-40 lines maximum

---

## Quality Standards

### Pre-Distribution Checklist

**Code Quality**:

- [ ] All Python files pass: `isort`, `black`, `flake8`, `mypy`
- [ ] All Ansible files pass: `ansible-lint`
- [ ] All playbooks pass: `ansible-playbook --syntax-check`
- [ ] No TODO/FIXME comments in production code
- [ ] All sensitive data removed (no hardcoded credentials)

**Documentation**:

- [ ] README.md complete and accurate
- [ ] INSTALL.md with step-by-step instructions
- [ ] CHANGELOG.md updated with current version
- [ ] MANIFEST.txt reflects actual tarball contents
- [ ] All documentation files use consistent formatting
- [ ] No broken internal references
- [ ] All example playbooks tested and functional

**Structure**:

- [ ] Role directories at top level (not nested)
- [ ] All required files present
- [ ] requirements.yml lists all collections
- [ ] .ansible-lint configuration included
- [ ] .gitignore appropriate for role
- [ ] LICENSE file included

**Testing**:

- [ ] Role executes successfully in test environment
- [ ] Example playbooks run without errors
- [ ] All tags work correctly
- [ ] Check mode (--check) works properly
- [ ] Idempotency verified (multiple runs = same result)

**Version Control**:

- [ ] CHANGELOG.md updated with release notes
- [ ] Version numbers consistent across all files
- [ ] Git tag created in monorepo for release
- [ ] Tarball stored in `docs/<role_name>/` directory

### Linting Configuration

**Include `.ansible-lint` with role**:

```yaml
---
profile: production

skip_list:
  - yaml[line-length]  # Allow longer lines for readability
  - var-naming[no-role-prefix]  # Allow unprefixed vars in defaults
  - name[casing]  # Allow flexible task naming

warn_list:
  - experimental  # Warn on experimental features

exclude_paths:
  - .cache/
  - test/
  - molecule/
```

### requirements.yml Format

**Include all required collections**:

```yaml
---
collections:
  - name: kubernetes.core
    version: ">=2.3.0"

  - name: community.hashi_vault
    version: ">=3.0.0"

  - name: ansible.posix

  - name: ansible.utils
```

---

## Examples

### Example 1: must_gather_log Role Distribution

**Monorepo Structure**:

```text
ansible-playground/
├── roles/
│   └── must_gather_log/
│       ├── README.md
│       ├── CHANGELOG.md
│       ├── defaults/main.yml
│       ├── meta/main.yml
│       ├── library/redhat_sso_device_auth.py
│       ├── tasks/
│       │   ├── main.yml
│       │   ├── cleanup.yml
│       │   ├── sftp_credential_management.yml
│       │   ├── vault_retrieve_sftp_credentials.yml
│       │   ├── check_token_expiry.yml
│       │   ├── redhat_sftp_token_generation.yml
│       │   ├── vault_store_sftp_token.yml
│       │   ├── must_gather_collection.yml
│       │   └── must_gather_upload.yml
│       └── group_vars_example.yml
├── playbooks/
│   ├── must-gather-ocp-logs.yml
│   └── redhat-sftp-token-refresh.yml
└── docs/
    └── must-gather-log/
        ├── architecture.md
        └── usage_examples.md
```

**Tarball Structure** (must-gather-log-role-3.0.0.tar.gz - 36KB):

```text
must-gather-log-role-3.0.0/
├── README.md                    # Complete role documentation
├── INSTALL.md                   # Installation guide
├── CHANGELOG.md                 # Version history
├── LICENSE                      # Apache-2.0 license
├── requirements.yml             # Ansible collection dependencies
├── .ansible-lint               # Linting configuration
├── .gitignore                  # Git ignore patterns
├── example-playbook.yml         # Simple example
├── group_vars_example.yml       # Example group variables
├── defaults/
│   └── main.yml                # 50+ default variables
├── meta/
│   └── main.yml                # Role metadata
├── library/
│   └── redhat_sso_device_auth.py  # Custom module (456 lines)
├── tasks/
│   ├── main.yml                # Main orchestrator (470 lines)
│   ├── cleanup.yml
│   ├── sftp_credential_management.yml
│   ├── vault_retrieve_sftp_credentials.yml
│   ├── check_token_expiry.yml
│   ├── redhat_sftp_token_generation.yml
│   ├── vault_store_sftp_token.yml
│   ├── must_gather_collection.yml
│   └── must_gather_upload.yml
├── playbooks/
│   ├── must-gather-ocp-logs.yml
│   └── redhat-sftp-token-refresh.yml
└── docs/
    ├── DISTRIBUTION-README.md
    ├── QUICKSTART.md
    ├── ROLE-README.md
    ├── MANIFEST.txt
    └── example-playbook.yml
```

**Creation Commands**:

```bash
# Create staging directory
mkdir -p /tmp/must-gather-log-role-3.0.0

# Copy role directories to top level
cp -r roles/must_gather_log/defaults /tmp/must-gather-log-role-3.0.0/
cp -r roles/must_gather_log/meta /tmp/must-gather-log-role-3.0.0/
cp -r roles/must_gather_log/library /tmp/must-gather-log-role-3.0.0/
cp -r roles/must_gather_log/tasks /tmp/must-gather-log-role-3.0.0/

# Copy top-level files
cp roles/must_gather_log/README.md /tmp/must-gather-log-role-3.0.0/
cp roles/must_gather_log/CHANGELOG.md /tmp/must-gather-log-role-3.0.0/
cp roles/must_gather_log/group_vars_example.yml /tmp/must-gather-log-role-3.0.0/

# Create and populate docs directory
mkdir -p /tmp/must-gather-log-role-3.0.0/docs
# Create DISTRIBUTION-README.md, QUICKSTART.md, ROLE-README.md, MANIFEST.txt
# Copy example-playbook.yml to docs/

# Create playbooks directory
mkdir -p /tmp/must-gather-log-role-3.0.0/playbooks
cp playbooks/must-gather-ocp-logs.yml /tmp/must-gather-log-role-3.0.0/playbooks/
cp playbooks/redhat-sftp-token-refresh.yml /tmp/must-gather-log-role-3.0.0/playbooks/

# Add configuration files
cp .ansible-lint /tmp/must-gather-log-role-3.0.0/
cp .gitignore /tmp/must-gather-log-role-3.0.0/

# Create LICENSE file
cat > /tmp/must-gather-log-role-3.0.0/LICENSE << 'EOF'
Apache License 2.0
...
EOF

# Create requirements.yml
cat > /tmp/must-gather-log-role-3.0.0/requirements.yml << 'EOF'
---
collections:
  - name: kubernetes.core
    version: ">=2.3.0"
  - name: community.hashi_vault
    version: ">=3.0.0"
  - name: ansible.posix
EOF

# Create simple example-playbook.yml
cat > /tmp/must-gather-log-role-3.0.0/example-playbook.yml << 'EOF'
---
- name: Collect must-gather logs
  hosts: localhost
  gather_facts: true

  tasks:
    - name: Run must-gather collection
      ansible.builtin.include_role:
        name: must_gather_log
      vars:
        cluster_name: prod-ocp-01
        rh_case: 03123456
EOF

# Create tarball
cd /tmp
tar -czf must-gather-log-role-3.0.0.tar.gz must-gather-log-role-3.0.0/

# Move to docs
mv must-gather-log-role-3.0.0.tar.gz /path/to/ansible-playground/docs/must-gather-log/

# Verify
tar -tzf /path/to/ansible-playground/docs/must-gather-log/must-gather-log-role-3.0.0.tar.gz | head -30
```

### Example 2: portworx_upgrade Role Distribution

**Tarball Structure** (portworx-upgrade-role-1.0.0.tar.gz):

```text
portworx-upgrade-role-1.0.0/
├── README.md
├── INSTALL.md
├── CHANGELOG.md
├── LICENSE
├── requirements.yml
├── .ansible-lint
├── .gitignore
├── example-playbook.yml
├── defaults/
│   └── main.yml
├── meta/
│   └── main.yml
├── library/
│   └── pxctl_status.py
├── tasks/
│   ├── main.yml
│   ├── preflight_validation.yml
│   ├── upgrade_trigger.yml
│   ├── monitoring.yml
│   └── validation.yml
├── playbooks/
│   └── px_upgrade.yml
└── docs/
    ├── DISTRIBUTION-README.md
    ├── QUICKSTART.md
    ├── ROLE-README.md
    ├── MANIFEST.txt
    └── example-playbook.yml
```

---

## Summary

### Key Principles

1. **Top-Level Structure**: Role directories MUST be at tarball root, not nested
2. **Dual Purpose**: Tarball must work both as role installation and git repository
3. **Complete Documentation**: 7-9 documentation files required for standalone usage
4. **Quality Checks**: All code must pass linting and syntax validation
5. **Version Consistency**: Version numbers must match across all files
6. **Self-Contained**: Include all dependencies, configs, and examples

### Common Pitfalls to Avoid

**DON'T**:

- ❌ Nest role under subdirectory (e.g., `tarball/role_name/defaults/`)
- ❌ Omit playbooks directory
- ❌ Skip MANIFEST.txt or make it inaccurate
- ❌ Forget to update CHANGELOG.md
- ❌ Include credentials or sensitive data
- ❌ Skip quality checks (linting, syntax validation)
- ❌ Hardcode paths or assumptions about environment
- ❌ Omit requirements.yml or .ansible-lint

**DO**:

- ✅ Place role directories at top level
- ✅ Include complete documentation set
- ✅ Create accurate MANIFEST.txt reflecting actual contents
- ✅ Update all version numbers consistently
- ✅ Test tarball extraction and usage
- ✅ Run all quality checks before distribution
- ✅ Use relative paths and configurable variables
- ✅ Include all configuration files

### Version Control

**Monorepo**:

- Develop on feature branch
- Tag release: `git tag -a must_gather_log-v3.0.0 -m "Release v3.0.0"`
- Merge to main after testing

**Standalone Distribution**:

- Store tarball in `docs/<role_name>/`
- Commit tarball with release tag
- Users can extract and create independent git repository

---

## Appendix: Automation Script Template

```bash
#!/bin/bash
# create_role_tarball.sh - Create standalone role distribution tarball
#
# Usage: ./create_role_tarball.sh <role_name> <version>
# Example: ./create_role_tarball.sh must_gather_log 3.0.0

set -euo pipefail

ROLE_NAME="${1:?Role name required}"
VERSION="${2:?Version required}"
TARBALL_NAME="${ROLE_NAME//_/-}-role-${VERSION}"
STAGING_DIR="/tmp/${TARBALL_NAME}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Creating standalone tarball for role: ${ROLE_NAME} v${VERSION}"

# Clean staging directory
rm -rf "${STAGING_DIR}"
mkdir -p "${STAGING_DIR}"

# Copy role directories to top level
echo "Copying role directories..."
for dir in defaults meta library filter_plugins tasks templates files vars; do
    if [[ -d "${PROJECT_ROOT}/roles/${ROLE_NAME}/${dir}" ]]; then
        cp -r "${PROJECT_ROOT}/roles/${ROLE_NAME}/${dir}" "${STAGING_DIR}/"
    fi
done

# Copy top-level files
echo "Copying top-level files..."
for file in README.md CHANGELOG.md group_vars_example.yml; do
    if [[ -f "${PROJECT_ROOT}/roles/${ROLE_NAME}/${file}" ]]; then
        cp "${PROJECT_ROOT}/roles/${ROLE_NAME}/${file}" "${STAGING_DIR}/"
    fi
done

# Create/copy documentation
echo "Creating documentation..."
mkdir -p "${STAGING_DIR}/docs"
# TODO: Create DISTRIBUTION-README.md, QUICKSTART.md, ROLE-README.md, MANIFEST.txt
# TODO: Copy example-playbook.yml

# Create playbooks directory
echo "Copying playbooks..."
mkdir -p "${STAGING_DIR}/playbooks"
# TODO: Identify and copy relevant playbooks

# Create configuration files
echo "Creating configuration files..."
cp "${PROJECT_ROOT}/.ansible-lint" "${STAGING_DIR}/"
cp "${PROJECT_ROOT}/.gitignore" "${STAGING_DIR}/"

# Create requirements.yml
cat > "${STAGING_DIR}/requirements.yml" << 'EOF'
---
collections:
  # TODO: Add required collections
EOF

# Create LICENSE
cat > "${STAGING_DIR}/LICENSE" << 'EOF'
Apache License 2.0
# TODO: Add full license text
EOF

# Create INSTALL.md
cat > "${STAGING_DIR}/INSTALL.md" << 'EOF'
# Installation Guide
# TODO: Add installation instructions
EOF

# Create simple example-playbook.yml
cat > "${STAGING_DIR}/example-playbook.yml" << 'EOF'
---
# TODO: Add simple example playbook
EOF

# Create tarball
echo "Creating tarball..."
cd /tmp
tar -czf "${TARBALL_NAME}.tar.gz" "${TARBALL_NAME}/"

# Move to docs
mkdir -p "${PROJECT_ROOT}/docs/${ROLE_NAME}"
mv "${TARBALL_NAME}.tar.gz" "${PROJECT_ROOT}/docs/${ROLE_NAME}/"

echo "✅ Tarball created: ${PROJECT_ROOT}/docs/${ROLE_NAME}/${TARBALL_NAME}.tar.gz"
echo "📦 Size: $(du -h "${PROJECT_ROOT}/docs/${ROLE_NAME}/${TARBALL_NAME}.tar.gz" | cut -f1)"

# Verify structure
echo "📋 Verifying structure..."
tar -tzf "${PROJECT_ROOT}/docs/${ROLE_NAME}/${TARBALL_NAME}.tar.gz" | head -20

echo "✅ Done! Tarball ready for distribution."
```

---

**Document Maintenance**: Update this document when:

- New role distribution patterns emerge
- Documentation requirements change
- Quality standards are updated
- Additional automation is added

**Document Owner**: Platform Engineering Team
**Review Cycle**: Quarterly or per major release
