# Ansible Playground Documentation

## Overview
This project contains Ansible playbooks and roles for managing Kubernetes clusters, HashiCorp Vault integration, and Portworx backup operations. It utilizes the purepx collection for interacting with the Portworx backup API.

## Prerequisites
- Python (>= 3.9, <= 3.14)
- Docker (required as container runtime)
- Ansible Core 2.15 or higher
- Access to Kubernetes cluster
- Access to HashiCorp Vault
- Access to Portworx backup API

## Environment Requirements
- Container Images: Uses either CentOS Stream or Fedora Stream base images
- Container Runtime: Docker (required)
- Execution Environment: Defined in `execution-environment.yml`

## Setup and Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ansible-playground
```

2. Install Python dependencies:
```bash
python -m pip install -r requirements.txt
```

3. Install Ansible collections:
```bash
ansible-galaxy collection install -r requirements.yml
```

4. Build the execution environment:
```bash
chmod +x build.sh
./build.sh
```

## Configuration

### Kubernetes Configuration
Ensure your kubeconfig is properly set up with the required credentials and context.

### Vault Configuration
Set up the following environment variables for Vault authentication:
- VAULT_ADDR: Your Vault server address
- VAULT_TOKEN: Your Vault authentication token

### Portworx Backup Configuration
The project uses the `purepx.px_backup` collection to interact with Portworx backup API. Configure the following:
1. Set up Portworx backup API credentials in your vault or as environment variables
2. Ensure the target cluster is registered with Portworx backup
3. Configure cloud credentials if using cloud storage

## Usage

### Running Playbooks
1. Verify your inventory is correct
2. Run the desired playbook using FQCN (Fully Qualified Collection Names):
```bash
ansible-playbook -i inventory/<inventory-file> <playbook-name>.yml
```

### Using purepx Modules
The project includes several purepx modules for Portworx backup operations:
- `purepx.px_backup.cluster`: Manage Portworx backup clusters
- `purepx.px_backup.cloud_credential`: Manage cloud credentials

Example usage:
```yaml
- name: Register cluster with Portworx backup
  purepx.px_backup.cluster:
    name: "my-cluster"
    state: present
    # additional parameters...
```

## Development

### Code Quality
This project uses several tools to maintain code quality:
- black: Code formatting
- flake8: Code linting
- mypy: Type checking
- pytest: Unit testing

Run the following commands before committing:
```bash
black .
flake8 .
mypy .
pytest
```

## Troubleshooting

Common issues and their solutions will be documented here.

### Known Issues
1. Container runtime must be set to Docker in execution-environment.yml
2. When using FQCN, ensure proper collection paths are set in ansible.cfg

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License
See the LICENSE file in the root directory.
