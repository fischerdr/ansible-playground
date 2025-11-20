# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is an enterprise Ansible Automation Platform (AAP) project for managing Kubernetes clusters, HashiCorp Vault integration, and Portworx backup operations. All automation is executed through Ansible Automation Platform using Execution Environments (EEs) only.

**Key Technologies:**

- Ansible Core 2.18.4
- Python 3.11
- Kubernetes/OpenShift
- HashiCorp Vault
- Portworx Backup (via purepx.px_backup collection)
- Docker container runtime (required)

## Development Commands

### Python Environment

**IMPORTANT:** Always use the Python virtual environment located at `/development/git/ansible-playground/.venv`

```bash
# Activate virtual environment
source .venv/bin/activate

# Verify you're using the correct Python
which python  # Should show: /development/git/ansible-playground/.venv/bin/python
```

All Python commands, pip installations, and tool executions must be run using the virtual environment Python interpreter at `.venv/bin/python`.

### Setup and Installation

```bash
# Install Python dependencies (using venv)
.venv/bin/python -m pip install -r requirements.txt

# Install Ansible collections
.venv/bin/ansible-galaxy collection install -r requirements.yml

# Build execution environment
chmod +x build.sh
./build.sh
```

### Testing and Quality

**IMPORTANT:** All linting and formatting tools must be run using the virtual environment.

```bash
# Code formatting (black) - run on Python files
.venv/bin/black .

# Import sorting (isort) - run on Python files
.venv/bin/isort .

# Python linting (flake8) - run on Python files
.venv/bin/flake8 .

# Type checking (mypy) - run on Python files
.venv/bin/mypy .

# Ansible-specific linting - run on playbooks and roles
.venv/bin/ansible-lint

# YAML linting
.venv/bin/yamllint .

# Run tests
.venv/bin/pytest

# Tox testing environments
.venv/bin/tox -e podman  # Build with Podman
.venv/bin/tox -e docker  # Build with Docker
```

**Automatic Quality Checks:**

When modifying files, automatically run appropriate tools:

- **Python files** (`.py`, custom modules in `roles/*/library/`): Run black, isort, flake8
- **Ansible files** (playbooks `*.yml`, roles, tasks): Run ansible-lint
- **All changes**: Run ansible-lint on affected playbooks/roles

### Running Playbooks

```bash
# Basic playbook execution
ansible-playbook -i inventory/<inventory-file> playbooks/<playbook-name>.yml

# Syntax check
ansible-playbook --syntax-check playbooks/<playbook-name>.yml

# Dry run
ansible-playbook -i inventory/<inventory-file> playbooks/<playbook-name>.yml --check

# View changes
ansible-playbook -i inventory/<inventory-file> playbooks/<playbook-name>.yml --diff

# Increase verbosity
ansible-playbook -i inventory/<inventory-file> playbooks/<playbook-name>.yml -vvv
```

## Architecture

### Directory Structure

- **`roles/`**: Reusable Ansible roles
  - `common/`: Shared functionality across roles
  - `defrag_etcd_db/`: etcd database defragmentation for OpenShift
  - `deploy_px/`: Portworx deployment automation
  - `must_gather_log/`: Must-gather log collection and Red Hat case management
  - `pxbackup/`: Portworx backup operations
  - `setup_env/`: Environment setup and configuration
  - `upgrade_clusters/`: Cluster upgrade automation
  - `vault_multi_namespace_monitor/`: Multi-namespace Vault monitoring
  - `vault_fix_portworx/`: Vault integration fixes for Portworx

- **`playbooks/`**: Orchestration playbooks
  - `pxbkup/`: Portworx backup-specific playbooks (create/list backups, schedules, clusters)
  - Various cluster management playbooks (k8s_*, px_*, etcd_*)

- **`Build-EE/`**: Execution environment build configuration
  - `execution-environment.yml`: EE definition (CentOS Stream 9 base)
  - `update_collection_requirements.py`: Collection dependency management

- **`collections/`**: Local Ansible collections
- **`inventory/`**: Inventory files with `group_vars/` and `host_vars/`
- **`scripts/`**: Utility scripts
- **`.cursor/rules/`**: Development standards and best practices

### Custom Modules

The project includes custom Python modules embedded within roles:

- **`roles/defrag_etcd_db/library/defrag_etcd.py`**: Defragments etcd databases in OpenShift by executing etcdctl commands inside etcd pods via `oc rsh`. Implements leader-aware ordering (defragments non-leader members first, leader last).

- **`roles/must_gather_log/library/redhat_upload.py`**: Uploads must-gather archive parts to Red Hat support cases via HTTP API. Handles multi-part uploads with retry logic, exponential backoff, and comprehensive error tracking.

- **`roles/pxbackup/filter_plugins/lookup_helpers.py`**: Custom Jinja2 filters for Portworx backup operations.

All custom modules follow Ansible 2.18+ standards with proper argument specs, return values, and comprehensive documentation.

### Execution Environment Architecture

The project uses Execution Environments (EEs) for isolation and reproducibility:

- Base image: `quay.io/centos/centos:stream9`
- Python: 3.11 (explicitly removes Python 3.9 if present)
- Container runtime: **Docker only** (requirement enforced in build configuration)
- All dependencies are pinned in requirements files
- EE includes system packages for Kerberos, Git LFS, Podman, and build tools

### Key Collections Used

- `purepx.px_backup`: Portworx backup API integration
- `kubernetes.core`: Kubernetes cluster management
- `community.hashi_vault`: HashiCorp Vault integration
- `ansible.posix`, `ansible.scm`, `ansible.utils`: Standard utilities
- Cloud collections: `amazon.aws`, `community.aws`, `google.cloud`, `community.vmware`

## Coding Standards

### Ansible Best Practices

**Required Conventions:**

- Always use FQCN (Fully Qualified Collection Names) for all modules
- Use lowercase `true`/`false` for boolean values
- Include clear description comment blocks at the start of playbooks
- Use meaningful play and task names
- Use `no_log: true` for sensitive operations (tokens, credentials)

**Error Handling:**

- Use `block`/`rescue`/`always` for error handling
- Provide clear error messages
- Register results for important operations
- Never ignore errors without explicit justification

**Variables:**

- Define required variables at the start of playbooks
- Use `assert` tasks to validate required variables
- Document optional variables with default values
- Follow proper variable scoping (host_vars, group_vars, playbook vars)

**Idempotency:**

- Design all tasks to be idempotent
- Use `changed_when` and `failed_when` directives appropriately
- Avoid `shell` and `command` modules unless absolutely necessary
- Prefer Ansible's built-in modules for specific tasks

**Proper use of changed_when and failed_when:**

When using `shell` or `command` modules, always define `changed_when` and `failed_when` to ensure proper idempotency and error handling:

- **changed_when**: Controls when a task reports "changed" status
  - For read-only operations (get, list, show): Use `changed_when: false` since these never modify state
  - For operations with detectable state changes: Test the output to determine if changes occurred
  - For operations that should report unusual conditions: Test for unexpected states (e.g., empty results when data is expected)

- **failed_when**: Controls when a task reports failure
  - Always consider all valid exit codes for the command
  - For grep operations: Use `failed_when: result.rc not in [0, 1]` since grep returns 1 when no matches are found
  - For operations with retry logic: Let `until` handle failures, use `failed_when` for unrecoverable errors
  - Test both return code and output content when appropriate

Examples:

```yaml
# Read-only operation - never changes state
- name: Get list of pods
  ansible.builtin.shell: kubectl get pods --no-headers
  register: pod_list
  changed_when: false
  failed_when: pod_list.rc != 0

# Grep operation - allow both success and no-match exit codes
- name: Find worker machinesets
  ansible.builtin.shell: |
    set -o pipefail &&
    oc get machineset --no-headers | grep worker
  args:
    executable: /bin/bash
  register: machineset_list
  changed_when: false
  failed_when: machineset_list.rc not in [0, 1]

# State-modifying operation - detect actual changes
- name: Apply configuration
  ansible.builtin.shell: kubectl apply -f config.yaml
  register: apply_result
  changed_when: "'configured' in apply_result.stdout or 'created' in apply_result.stdout"
  failed_when: apply_result.rc != 0

# Operation with expected output - report change if output is unusual
- name: Verify cluster members exist
  ansible.builtin.shell: etcdctl member list
  register: member_list
  changed_when: member_list.stdout_lines | length == 0
  failed_when: member_list.rc != 0
```

Common patterns:

- `changed_when: false` - For any read/query operation
- `changed_when: result.stdout_lines | length == 0` - When empty results indicate an unexpected state
- `changed_when: "'created' in result.stdout or 'updated' in result.stdout"` - When output indicates modification
- `failed_when: result.rc != 0` - For commands with simple success/failure
- `failed_when: result.rc not in [0, 1]` - For grep and similar tools
- `failed_when: result.rc != 0 or 'error' in result.stderr | lower` - When checking both exit code and output

### Python Standards

- Python 3.11+ syntax
- Type hints required (from `__future__ import annotations`)
- Follow PEP 8 style guide
- Use `black` for formatting, `flake8` for linting, `mypy` for type checking
- Custom modules must include proper Ansible documentation (DOCUMENTATION, EXAMPLES, RETURN)

### Security

- Use Ansible Vault to encrypt sensitive data
- Never log sensitive information (use `no_log: true`)
- Validate all external input using `assert` module
- Use HTTPS for all API communication
- Implement proper privilege escalation with `become` only when necessary

## Configuration Files

- **`ansible.cfg`**: Ansible configuration
  - Inventory: `inventory/hosts.yml`
  - Fact caching: JSON files in `tmp/facts_cache/`
  - SSH retries: 8 attempts
  - Callbacks enabled: `debug`, `unixy`
  - Collections path: `./collections:/usr/share/ansible/collections`

- **`.ansible-lint`**: Ansible-lint configuration
  - Skips: line-length, var-naming rules, command-instead-of-module, name[template]

- **`.flake8`**: Python linting configuration

- **`tox.ini`**: Test automation for Podman and Docker builds

## Important Notes

### Execution Environment Requirements

- Container runtime **must** be Docker (not Podman for production builds)
- EE isolation must be considered in all automation decisions
- Python 3.11 is the only supported Python version
- All dependencies must be declared in requirements files for reproducible builds

### Platform Context

This project is designed for **Ansible Automation Platform (AAP)** deployment:

- All playbooks run inside Execution Environments
- Vault-based secret management is standard
- Enterprise security standards apply to all code
- Systems-level reasoning required for scaling considerations

### Communication Style

When working with this codebase, maintain a formal, professional tone appropriate for enterprise environments. Emphasize maintainability, clarity, and operational soundness in all changes.

### Documentation Standards

**IMPORTANT:** Follow these rules when working with documentation:

- **No emojis or icons** - Documentation must be professional and text-only
- **Ask before creating** - Always ask the user for approval before generating or modifying documentation files
- **No unsolicited documentation** - Never proactively create README files, markdown documentation, or similar without explicit user request

This applies to all documentation including:

- README files
- Markdown documentation (*.md)
- Code comments and docstrings (emojis prohibited)
- Commit messages (emojis prohibited)

## Claude Code Workflow Requirements

### Virtual Environment Usage

**CRITICAL:** All Python and Ansible commands MUST use the virtual environment at `/development/git/ansible-playground/.venv`

- Python interpreter: `.venv/bin/python`
- Pip: `.venv/bin/pip`
- Ansible tools: `.venv/bin/ansible`, `.venv/bin/ansible-playbook`, `.venv/bin/ansible-lint`, `.venv/bin/ansible-galaxy`
- Linting tools: `.venv/bin/black`, `.venv/bin/isort`, `.venv/bin/flake8`, `.venv/bin/mypy`

### Automatic Quality Enforcement

After making code changes, automatically run appropriate tools:

**For Python files** (`.py` files, modules in `roles/*/library/`, filter plugins):

1. `.venv/bin/isort <file>` - Sort imports
2. `.venv/bin/black <file>` - Format code
3. `.venv/bin/flake8 <file>` - Check for linting issues

**For Ansible files** (playbooks, roles, tasks):

1. `.venv/bin/ansible-lint <file-or-directory>` - Lint Ansible content

These tools run automatically without requiring user approval (configured in `.claude/settings.local.json`).

### Expected Behavior

When Claude Code modifies files, it should:

1. Make the requested changes
2. Automatically run the appropriate quality tools based on file type
3. Fix any issues found by the tools
4. Report the results to the user

This ensures all code maintains consistent quality and follows project standards.

### Git Commit Messages

**IMPORTANT:** Do NOT add Claude Code attribution or co-authorship to commit messages.

Commit messages should:

- Follow conventional commit format when appropriate
- Be concise and descriptive
- Focus on the "why" rather than the "what"
- Match the repository's existing commit style
- **NOT include** any Claude Code branding, attribution, or co-authorship footers

Bad example (DO NOT USE):

```text
Add new feature

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

Good example:

```text
Add etcd defragmentation monitoring

Implements health check validation before and after defrag operations
to ensure cluster stability.
```
