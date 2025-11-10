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

### Setup and Installation

```bash
# Install Python dependencies
python -m pip install -r requirements.txt

# Install Ansible collections
ansible-galaxy collection install -r requirements.yml

# Build execution environment
chmod +x build.sh
./build.sh
```

### Testing and Quality

```bash
# Code formatting and linting
black .
flake8 .
mypy .

# Ansible-specific linting
ansible-lint

# YAML linting
yamllint .

# Run tests
pytest

# Tox testing environments
tox -e podman  # Build with Podman
tox -e docker  # Build with Docker
```

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
