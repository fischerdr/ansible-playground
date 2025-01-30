# Project Organization

## Overview

This Ansible project is specifically designed to create and manage roles for integrating Kubernetes clusters with Portworx backup. The primary focus is on automating the setup and configuration of Portworx backup for Kubernetes clusters, with integration points for HashiCorp Vault and the Portworx backup API via the purepx collection.

## Project Structure

```
ansible-playground/
├── roles/
│   └── setup_cluster_pxbkup/     # Main role for Portworx backup setup
├── collections/                   # Required Ansible collections
├── docs/                         # Project documentation
├── examples/                     # Example playbooks and configurations
├── inventory/                    # Inventory configurations
├── runner/                       # Ansible-runner configurations
├── .logs/                       # Log directory
├── tmp/                         # Temporary files directory
├── cache/                       # Cache files directory
├── execution-environment.yml     # EE configuration
├── requirements.yml             # Ansible collection requirements
├── requirements.txt             # Python package requirements
├── ansible.cfg                  # Ansible configuration
├── tox.ini                      # Test environment configuration
└── build.sh                     # Build script for the project

## Key Playbooks
- setup_cluster_pxbkup.yml       # Main playbook for Portworx backup setup
- k8s_check_pxs3.yml            # Kubernetes S3 integration check
- k8s_create_sa_and_roles.yml   # Service account and role creation
- k8s_hv_setup.yml              # HashiCorp Vault setup
- k8s_label_check_balance.yml   # Label and balance checking
- k8s_labelset_check.yml        # Label set verification

## Development Standards

### Python Standards

- Version Compatibility: Python 3.9 - 3.14
- Command Line Interfaces: click and typer
- Testing Framework: pytest
- Code Quality Tools:
  - black for formatting
  - isort for import sorting
  - flake8 for linting
- Type Hints: Required for all code
- Documentation:
  - Docstrings required for all functions/classes
  - Comprehensive inline comments
  - Type hints for all parameters and returns
- Logging: Python standard logging module (outputs to .logs/)

### Shell Script Standards

- Double quotes required for variable expansion
- Function definitions must be at the top of file
- All functions must be defined before they are called
- All variables must be defined before they are used

### File Organization Standards

- Temporary Files: Must be stored in tmp/ directory
- Cache Files: Must be stored in cache/ directory
- Empty Lines: No trailing whitespace, no leading whitespace

### Ansible Standards

- FQCN (Fully Qualified Collection Names) required for all module actions
- Collections defined in requirements.yml
- Execution via ansible-runner
- Configuration in ansible.cfg
- Inventory structure in inventory/

### Execution Environment

- Base Image: CentOS Stream 9 (quay.io/centos/centos:stream9)
- Python Version: 3.12
- Runtime: Docker
- Dependencies:
  - ansible-core (2.15+)
  - ansible-runner
  - Various system packages defined in execution-environment.yml

### Security Standards

- Authentication & Authorization:
  - Kubernetes service accounts and roles managed via dedicated playbooks
  - HashiCorp Vault integration for secrets management
  - No hardcoded credentials
  - All secrets must be in environment variables or memory only

- API Security:
  - HTTPS required for all external services
  - Secure communication with Portworx backup API
  - Vault for secrets management

- Best Practices:
  - Proper error handling with logging
  - Secure coding practices throughout
  - Project temporary files in tmp/ directory
  - Project cache files in cache/ directory

### Container Standards

- Approved Base Images Only:
  - CentOS Stream
  - Fedora Stream
  - Alpine (alternative option)

### Testing and Quality Assurance

- Tox for test automation
- Ansible-lint for playbook validation
- Comprehensive logging for debugging
- Example playbooks for reference

### Documentation Requirements

1. Role Documentation
   - README.md in each role
   - Variable documentation
   - Example usage

2. Project Documentation
   - Setup instructions
   - Configuration guide
   - Playbook descriptions
   - Integration points

### Logging and Monitoring

- Structured logging implementation
- Log directory: .logs/
- Progress tracking
- Error logging and handling

## Execution Flow

1. Environment Setup
   - Execution environment build
   - Python dependencies installation
   - Ansible collection installation

2. Initial Configuration
   - Vault configuration retrieval from inventory
   - Px-Backup authentication and token management
   - Schedule policy verification and updates

3. Kubernetes Setup
   - Service account creation
   - Role and permission configuration
   - Label management
   - Cluster registration in Px-Backup

4. Portworx Backup Integration
   - S3 configuration verification
   - Schedule policy implementation
   - Label verification
   - Balance checking

## Task Structure

### Main Role: setup_cluster_pxbkup

The role follows this execution order:
1. `get_vault_config.yml`: Retrieve Vault configuration from inventory
2. `auth.yaml`: Authenticate and obtain Px-Backup token
3. `verify_update_schedulepol.yml`: Verify and update schedule policies
4. `createSaRole.yml`: Create service accounts and roles
5. `createCLSTRinPxBkup.yaml`: Register cluster in Px-Backup

Each task is modular and follows these principles:
- Authentication is handled centrally through auth.yaml
- Configuration is retrieved from inventory group_vars
- Tasks use FQCN for all module actions
- Proper error handling and logging throughout

## Maintenance and Updates

- Regular updates to execution environment
- Dependency management via requirements.yml and requirements.txt
- Version control via Git
- CI/CD integration via GitHub Actions (.github/ directory)
