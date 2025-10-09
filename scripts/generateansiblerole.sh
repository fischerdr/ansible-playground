#!/bin/bash

# Ansible Galaxy Role Generator
# Creates a complete, ready-to-commit Ansible role repository

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Ansible Galaxy Role Generator         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Get inputs with defaults
read -p "Role name [my_role]: " ROLE_NAME
ROLE_NAME=${ROLE_NAME:-my_role}

read -p "Author name [$(git config user.name 2>/dev/null || echo 'Your Name')]: " AUTHOR_NAME
AUTHOR_NAME=${AUTHOR_NAME:-$(git config user.name 2>/dev/null || echo 'Your Name')}

read -p "Author email [$(git config user.email 2>/dev/null || echo 'your.email@example.com')]: " AUTHOR_EMAIL
AUTHOR_EMAIL=${AUTHOR_EMAIL:-$(git config user.email 2>/dev/null || echo 'your.email@example.com')}

read -p "Description [Ansible role for $ROLE_NAME]: " DESCRIPTION
DESCRIPTION=${DESCRIPTION:-"Ansible role for $ROLE_NAME"}

read -p "Company/Organization (optional): " COMPANY

read -p "License [MIT]: " LICENSE
LICENSE=${LICENSE:-MIT}

read -p "Min Ansible version [2.9]: " MIN_ANSIBLE
MIN_ANSIBLE=${MIN_ANSIBLE:-2.9}

ROLE_DIR="ansible-role-${ROLE_NAME}"
YEAR=$(date +%Y)

echo ""
echo -e "${GREEN}Creating role: $ROLE_DIR${NC}"

# Create directory structure
mkdir -p "$ROLE_DIR"/{defaults,vars,tasks,handlers,templates,files,meta,tests,.github/workflows}

# README.md
cat > "$ROLE_DIR/README.md" << EOF
# Ansible Role: $ROLE_NAME

$DESCRIPTION

## Requirements

Any prerequisites that may not be covered by Ansible itself or the role should be mentioned here.

## Role Variables

Available variables are listed below, along with default values (see \`defaults/main.yml\`):

\`\`\`yaml
${ROLE_NAME}_enabled: true
${ROLE_NAME}_package_name: "example-package"
${ROLE_NAME}_config_path: "/etc/example"
\`\`\`

- \`${ROLE_NAME}_enabled\`: Enable or disable the role (default: \`true\`)
- \`${ROLE_NAME}_package_name\`: Name of the package to install
- \`${ROLE_NAME}_config_path\`: Path to configuration directory

## Dependencies

None.

## Example Playbook

\`\`\`yaml
- hosts: servers
  become: yes
  roles:
    - role: $ROLE_NAME
      ${ROLE_NAME}_enabled: true
      ${ROLE_NAME}_package_name: "custom-package"
\`\`\`

## Testing

\`\`\`bash
# Syntax check
ansible-playbook tests/test.yml -i tests/inventory --syntax-check

# Run tests locally
ansible-playbook tests/test.yml -i tests/inventory --connection=local
\`\`\`

## License

$LICENSE

## Author Information

This role was created by $AUTHOR_NAME.

For issues, questions, or contributions, please visit the repository.
EOF

# meta/main.yml
cat > "$ROLE_DIR/meta/main.yml" << EOF
---
galaxy_info:
  role_name: $ROLE_NAME
  author: $AUTHOR_NAME
  description: $DESCRIPTION
$([ -n "$COMPANY" ] && echo "  company: $COMPANY")
  
  license: $LICENSE
  
  min_ansible_version: "$MIN_ANSIBLE"
  
  platforms:
    - name: Ubuntu
      versions:
        - focal
        - jammy
        - noble
    - name: Debian
      versions:
        - bullseye
        - bookworm
    - name: EL
      versions:
        - "8"
        - "9"
    - name: Fedora
      versions:
        - "38"
        - "39"
  
  galaxy_tags:
    - system
    - configuration
    - automation

dependencies: []
EOF

# defaults/main.yml
cat > "$ROLE_DIR/defaults/main.yml" << EOF
---
# defaults file for $ROLE_NAME

# Enable or disable this role
${ROLE_NAME}_enabled: true

# Package configuration
${ROLE_NAME}_package_name: "example-package"
${ROLE_NAME}_package_state: "present"

# Service configuration
${ROLE_NAME}_service_name: "example-service"
${ROLE_NAME}_service_state: "started"
${ROLE_NAME}_service_enabled: true

# Configuration paths
${ROLE_NAME}_config_path: "/etc/example"
${ROLE_NAME}_config_file: "{{ ${ROLE_NAME}_config_path }}/config.yml"

# Custom configuration
${ROLE_NAME}_custom_config: {}
EOF

# vars/main.yml
cat > "$ROLE_DIR/vars/main.yml" << EOF
---
# vars file for $ROLE_NAME

# These variables should not be overridden by users
${ROLE_NAME}_internal_version: "1.0.0"
EOF

# tasks/main.yml
cat > "$ROLE_DIR/tasks/main.yml" << EOF
---
# tasks file for $ROLE_NAME

- name: Include OS-specific variables
  ansible.builtin.include_vars: "{{ ansible_os_family }}.yml"
  when: ansible_os_family in ['Debian', 'RedHat']
  ignore_errors: true

- name: Ensure role is enabled
  ansible.builtin.assert:
    that:
      - ${ROLE_NAME}_enabled is defined
      - ${ROLE_NAME}_enabled | bool
    fail_msg: "Role $ROLE_NAME is not enabled. Set ${ROLE_NAME}_enabled: true to enable it."
    quiet: true
  when: ${ROLE_NAME}_enabled is defined

- name: Display role information
  ansible.builtin.debug:
    msg: "Executing $ROLE_NAME role v{{ ${ROLE_NAME}_internal_version }}"
  when: ${ROLE_NAME}_enabled | bool

- name: Ensure package is installed
  ansible.builtin.package:
    name: "{{ ${ROLE_NAME}_package_name }}"
    state: "{{ ${ROLE_NAME}_package_state }}"
  when:
    - ${ROLE_NAME}_enabled | bool
    - ${ROLE_NAME}_package_name is defined

- name: Ensure configuration directory exists
  ansible.builtin.file:
    path: "{{ ${ROLE_NAME}_config_path }}"
    state: directory
    mode: '0755'
  when: ${ROLE_NAME}_enabled | bool

- name: Deploy configuration file
  ansible.builtin.template:
    src: config.yml.j2
    dest: "{{ ${ROLE_NAME}_config_file }}"
    mode: '0644'
  notify: restart ${ROLE_NAME} service
  when: ${ROLE_NAME}_enabled | bool

- name: Ensure service is in desired state
  ansible.builtin.service:
    name: "{{ ${ROLE_NAME}_service_name }}"
    state: "{{ ${ROLE_NAME}_service_state }}"
    enabled: "{{ ${ROLE_NAME}_service_enabled }}"
  when:
    - ${ROLE_NAME}_enabled | bool
    - ${ROLE_NAME}_service_name is defined
EOF

# handlers/main.yml
cat > "$ROLE_DIR/handlers/main.yml" << EOF
---
# handlers file for $ROLE_NAME

- name: restart ${ROLE_NAME} service
  ansible.builtin.service:
    name: "{{ ${ROLE_NAME}_service_name }}"
    state: restarted
  listen: "restart ${ROLE_NAME} service"

- name: reload ${ROLE_NAME} service
  ansible.builtin.service:
    name: "{{ ${ROLE_NAME}_service_name }}"
    state: reloaded
  listen: "reload ${ROLE_NAME} service"
EOF

# templates/.gitkeep
touch "$ROLE_DIR/templates/.gitkeep"

# files/.gitkeep
touch "$ROLE_DIR/files/.gitkeep"

# tests/inventory
cat > "$ROLE_DIR/tests/inventory" << EOF
[local]
localhost ansible_connection=local

[test_servers]
localhost
EOF

# tests/test.yml
cat > "$ROLE_DIR/tests/test.yml" << EOF
---
- name: Test $ROLE_NAME role
  hosts: localhost
  become: true
  
  roles:
    - role: $ROLE_NAME
      ${ROLE_NAME}_enabled: true
EOF

# .github/workflows/ci.yml
cat > "$ROLE_DIR/.github/workflows/ci.yml" << EOF
---
name: CI

on:
  push:
    branches: [main, master, develop]
  pull_request:
    branches: [main, master]
  workflow_dispatch:

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install ansible ansible-lint yamllint
      
      - name: Run yamllint
        run: yamllint .
      
      - name: Run ansible-lint
        run: ansible-lint .
  
  test:
    name: Test
    runs-on: ubuntu-latest
    needs: lint
    strategy:
      matrix:
        ansible-version:
          - '2.9'
          - '2.15'
          - 'latest'
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      
      - name: Install Ansible
        run: |
          if [ "\${{ matrix.ansible-version }}" = "latest" ]; then
            pip install ansible
          else
            pip install "ansible==\${{ matrix.ansible-version }}.*"
          fi
      
      - name: Test role syntax
        run: |
          ansible-playbook tests/test.yml -i tests/inventory --syntax-check
      
      - name: Run role
        run: |
          ansible-playbook tests/test.yml -i tests/inventory --connection=local
EOF

# .gitignore
cat > "$ROLE_DIR/.gitignore" << EOF
# Ansible
*.retry
*.pyc
__pycache__/
.pytest_cache/
.tox/
*.log

# Molecule
.molecule/
.cache/

# Editor files
*.swp
*.swo
*~
.vscode/
.idea/
*.sublime-project
*.sublime-workspace

# OS files
.DS_Store
Thumbs.db
desktop.ini

# Test files
test_output/
*.tfstate
*.tfstate.backup
.terraform/

# Environment
.env
.venv
venv/
ENV/
EOF

# .yamllint
cat > "$ROLE_DIR/.yamllint" << EOF
---
extends: default

rules:
  line-length:
    max: 120
    level: warning
  indentation:
    spaces: 2
    indent-sequences: true
  truthy:
    allowed-values: ['true', 'false', 'yes', 'no']
  comments:
    min-spaces-from-content: 1
  braces:
    max-spaces-inside: 1
  brackets:
    max-spaces-inside: 1

ignore: |
  .github/
  .molecule/
EOF

# .ansible-lint
cat > "$ROLE_DIR/.ansible-lint" << EOF
---
profile: production

exclude_paths:
  - .github/
  - .molecule/
  - tests/

skip_list:
  - yaml[line-length]
  - name[casing]

warn_list:
  - experimental
  - jinja[spacing]

enable_list:
  - no-same-owner
EOF

# .gitattributes
cat > "$ROLE_DIR/.gitattributes" << EOF
* text=auto eol=lf
*.yml linguist-language=YAML
EOF

# LICENSE
if [ "$LICENSE" == "MIT" ]; then
cat > "$ROLE_DIR/LICENSE" << EOF
MIT License

Copyright (c) $YEAR $AUTHOR_NAME

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
else
cat > "$ROLE_DIR/LICENSE" << EOF
$LICENSE License

Copyright (c) $YEAR $AUTHOR_NAME

Add your license text here.
EOF
fi

# Initialize git
cd "$ROLE_DIR"
git init
git add .
git commit -m "Initial commit: Ansible role $ROLE_NAME"

echo ""
echo -e "${GREEN}✅ Role created successfully!${NC}"
echo ""
echo -e "${BLUE}Directory structure:${NC}"
tree -L 2 2>/dev/null || find . -maxdepth 2 -print | sed 's|[^/]*/| |g'
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. cd $ROLE_DIR"
echo "  2. Review and customize the files"
echo "  3. Add remote: git remote add origin <your-repo-url>"
echo "  4. Push: git push -u origin main"
echo "  5. Import to Galaxy: ansible-galaxy role import <namespace> <repo-name>"
echo ""
echo -e "${GREEN}Happy automating! 🚀${NC}"
EOF