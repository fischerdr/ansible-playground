#!/bin/bash

# Ansible Galaxy Role Builder Script
# Creates a complete Ansible role structure ready for Galaxy

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to prompt for input with default value
prompt() {
    local var_name=$1
    local prompt_text=$2
    local default_value=$3
    
    if [ -n "$default_value" ]; then
        read -p "$prompt_text [$default_value]: " input
        eval $var_name="${input:-$default_value}"
    else
        read -p "$prompt_text: " input
        eval $var_name="$input"
    fi
}

# Welcome message
echo ""
echo "======================================"
echo "  Ansible Galaxy Role Builder"
echo "======================================"
echo ""

# Gather information
prompt ROLE_NAME "Enter role name" "my_role"
prompt AUTHOR_NAME "Enter author name" "$(git config user.name 2>/dev/null || echo 'Your Name')"
prompt AUTHOR_EMAIL "Enter author email" "$(git config user.email 2>/dev/null || echo 'your.email@example.com')"
prompt ROLE_DESCRIPTION "Enter role description" "A brief description of the role"
prompt COMPANY_NAME "Enter company name (optional)" ""
prompt LICENSE "Enter license" "MIT"
prompt MIN_ANSIBLE_VERSION "Minimum Ansible version" "2.9"

# Git repository information
prompt INIT_GIT "Initialize git repository? (y/n)" "y"
if [[ "$INIT_GIT" =~ ^[Yy]$ ]]; then
    prompt GIT_REMOTE "Enter git remote URL (optional)" ""
fi

# Create role directory
print_info "Creating role directory: $ROLE_NAME"
mkdir -p "$ROLE_NAME"
cd "$ROLE_NAME"

# Create directory structure
print_info "Creating directory structure..."
mkdir -p defaults vars tasks handlers templates files meta tests .github/workflows

# Create .gitkeep files for empty directories
touch templates/.gitkeep
touch files/.gitkeep

# Create README.md
print_info "Creating README.md..."
cat > README.md << EOF
# Ansible Role: $ROLE_NAME

$ROLE_DESCRIPTION

## Requirements

Any prerequisites that may not be covered by Ansible itself or the role should be mentioned here.

## Role Variables

Available variables are listed below, along with default values (see \`defaults/main.yml\`):

\`\`\`yaml
${ROLE_NAME}_enabled: true
${ROLE_NAME}_variable: default_value
\`\`\`

Description of the variable.

## Dependencies

A list of other roles hosted on Galaxy should go here, plus any details in regards to parameters that may need to be set for other roles.

## Example Playbook

\`\`\`yaml
- hosts: servers
  roles:
    - role: $ROLE_NAME
      ${ROLE_NAME}_enabled: true
\`\`\`

## License

$LICENSE

## Author Information

This role was created by $AUTHOR_NAME.
EOF

# Create meta/main.yml
print_info "Creating meta/main.yml..."
cat > meta/main.yml << EOF
---
galaxy_info:
  role_name: $ROLE_NAME
  author: $AUTHOR_NAME
  description: $ROLE_DESCRIPTION
  $([ -n "$COMPANY_NAME" ] && echo "company: $COMPANY_NAME")
  
  license: $LICENSE
  
  min_ansible_version: "$MIN_ANSIBLE_VERSION"
  
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
  
  galaxy_tags:
    - system
    - configuration

dependencies: []
EOF

# Create defaults/main.yml
print_info "Creating defaults/main.yml..."
cat > defaults/main.yml << EOF
---
# Default variables for $ROLE_NAME role
${ROLE_NAME}_enabled: true
${ROLE_NAME}_variable: "default_value"
EOF

# Create vars/main.yml
print_info "Creating vars/main.yml..."
cat > vars/main.yml << EOF
---
# Variables that shouldn't be overridden
${ROLE_NAME}_internal_var: "internal_value"
EOF

# Create tasks/main.yml
print_info "Creating tasks/main.yml..."
cat > tasks/main.yml << EOF
---
- name: Include OS-specific variables
  ansible.builtin.include_vars: "{{ ansible_os_family }}.yml"
  when: ansible_os_family in ['Debian', 'RedHat']
  ignore_errors: true

- name: Ensure role is enabled
  ansible.builtin.assert:
    that:
      - ${ROLE_NAME}_enabled is defined
      - ${ROLE_NAME}_enabled | bool
    fail_msg: "Role ${ROLE_NAME} is not enabled"
    success_msg: "Role ${ROLE_NAME} is enabled"
  when: ${ROLE_NAME}_enabled is defined

- name: Example task
  ansible.builtin.debug:
    msg: "This is an example task for {{ ${ROLE_NAME}_variable }}"
  when: ${ROLE_NAME}_enabled | bool
EOF

# Create handlers/main.yml
print_info "Creating handlers/main.yml..."
cat > handlers/main.yml << EOF
---
- name: Restart example service
  ansible.builtin.service:
    name: example_service
    state: restarted
  listen: "restart example"
EOF

# Create tests/inventory
print_info "Creating tests/inventory..."
cat > tests/inventory << EOF
[local]
localhost ansible_connection=local
EOF

# Create tests/test.yml
print_info "Creating tests/test.yml..."
cat > tests/test.yml << EOF
---
- hosts: localhost
  remote_user: root
  roles:
    - $ROLE_NAME
EOF

# Create .github/workflows/ci.yml
print_info "Creating .github/workflows/ci.yml..."
cat > .github/workflows/ci.yml << EOF
---
name: CI

on:
  push:
    branches: [main, master, develop]
  pull_request:
    branches: [main, master]

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
          pip install ansible ansible-lint yamllint
      
      - name: Run yamllint
        run: yamllint .
      
      - name: Run ansible-lint
        run: ansible-lint .
  
  test:
    name: Test
    runs-on: ubuntu-latest
    needs: lint
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      
      - name: Install Ansible
        run: pip install ansible
      
      - name: Test role syntax
        run: |
          ansible-playbook tests/test.yml -i tests/inventory --syntax-check
EOF

# Create .gitignore
print_info "Creating .gitignore..."
cat > .gitignore << EOF
# Ansible
*.retry
*.pyc
__pycache__/
.pytest_cache/
.tox/

# Editor files
*.swp
*.swo
*~
.vscode/
.idea/

# OS files
.DS_Store
Thumbs.db

# Test files
.molecule/
.cache/
EOF

# Create .yamllint
print_info "Creating .yamllint..."
cat > .yamllint << EOF
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
EOF

# Create .ansible-lint
print_info "Creating .ansible-lint..."
cat > .ansible-lint << EOF
---
exclude_paths:
  - .github/
  - tests/

skip_list:
  - yaml[line-length]
EOF

# Initialize git if requested
if [[ "$INIT_GIT" =~ ^[Yy]$ ]]; then
    print_info "Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit: Ansible role skeleton for $ROLE_NAME"
    
    if [ -n "$GIT_REMOTE" ]; then
        print_info "Adding git remote: $GIT_REMOTE"
        git remote add origin "$GIT_REMOTE"
        print_warn "Remember to push: git push -u origin main"
    fi
fi

# Summary
echo ""
echo "======================================"
echo "  Role Created Successfully!"
echo "======================================"
echo ""
print_info "Role name: $ROLE_NAME"
print_info "Location: $(pwd)"
echo ""
echo "Next steps:"
echo "  1. Review and customize the generated files"
echo "  2. Add your tasks in tasks/main.yml"
echo "  3. Update variables in defaults/main.yml"
echo "  4. Test locally: ansible-playbook tests/test.yml -i tests/inventory"
echo "  5. Push to GitHub: git push -u origin main"
echo "  6. Import to Galaxy: ansible-galaxy role import <username> <repo>"
echo ""
print_info "Happy automating!"
echo ""
EOF