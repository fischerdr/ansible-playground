# Execution Environment Configuration

## Overview

This document describes the execution environment configuration for the Ansible Portworx backup project. The environment is designed to support Kubernetes cluster integration with Portworx backup, including HashiCorp Vault integration and the Portworx backup API.

## Base Image and Runtime

- Base Image: CentOS Stream 9 (`quay.io/centos/centos:stream9`)
- Container Runtime: Docker/Podman
- Python Version: 3.11

## Project Structure Integration

The execution environment supports the following project structure:

```
ansible-playground/
├── logs/           # Structured logging output
├── collections/    # Ansible collections (both local and system paths)
└── var/run/receptor/  # Receptor runtime files
```

## Dependencies

### System Packages

1. Build and Compilation Tools
   - gcc, gcc-c++
   - cmake
   - make
   - python3.11-devel
   - openssl-devel
   - libcurl-devel
   - krb5-devel

2. Runtime Tools
   - git-core, git-lfs
   - krb5-workstation
   - subversion
   - sshpass
   - rsync
   - unzip
   - podman-remote
   - python3.11

### Python Packages

1. Core Dependencies
   - click >= 8.0.0
   - requests >= 2.31.0
   - urllib3 >= 2.0.0
   - python-dateutil >= 2.8.2
   - Jinja2 >= 3.1.0

2. Kubernetes and Cloud
   - kubernetes >= 28.1.0
   - boto3 >= 1.34.0
   - pyvmomi >= 8.0.0
   - hvac >= 2.0.0

3. Ansible Tools
   - ansible-core >= 2.15.0
   - ansible-runner >= 2.3.0
   - ansible-navigator >= 3.5.0
   - ansible-compat == 25.1.1
   - ansible-lint >= 6.22.0

4. Development Tools
   - pytest >= 7.0.0
   - black >= 23.0.0
   - flake8 >= 6.0.0
   - mypy >= 1.0.0
   - tox
   - tox-ansible

### Environment Configuration

1. Ansible Settings
   - Collections Path: `./collections:/usr/share/ansible/collections`
   - Force Color Output: Enabled
   - Python Path: `/usr/local/lib/python3.11/site-packages`

2. Logging Configuration
   - Format: JSON
   - Level: INFO
   - Directory: `/logs`

3. Security Settings
   - CA Bundle: `/etc/pki/tls/certs/ca-bundle.crt`
   - Secure HTTPS communication enabled

4. Additional Features
   - Receptor integration from `quay.io/ansible/receptor:devel`
   - Git LFS system-wide installation
   - Python 3.11 as default python interpreter

## Building and Running

### Building the Environment

```bash
ansible-builder create -v 3
```

### Running with Navigator

```bash
ansible-navigator run playbook.yml --execution-environment-image test-ee:latest
```

## Maintenance

- System updates via dnf during build
- Python package updates via pip
- Receptor updates from upstream container
- Git LFS system-wide configuration

## Best Practices

1. Use structured logging with JSON format
2. Leverage local and system collection paths
3. Utilize Receptor for enhanced execution capabilities
4. Keep Python 3.11 as the standard interpreter
5. Maintain secure communication with proper CA certificates
