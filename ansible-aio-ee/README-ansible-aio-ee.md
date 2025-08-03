# Ansible All-In-One Execution Environment (EE)

A comprehensive Ansible Execution Environment that includes all major cloud and container management tools, built on Red Hat Universal Base Image 8 (stream) with Python 3.11.

## 🚀 Features

### Base Environment
- **Base Image**: Red Hat Universal Base Image 8 (stream)
- **Python Version**: 3.11 (set as default interpreter)
- **Ansible**: Latest stable version with all dependencies

### Cloud & Container Tools
- **AWS CLI/SDK**: Latest version for AWS operations
- **Google Cloud SDK**: Latest version (gcloud, gsutil, bq)
- **kubectl**: Latest stable version for Kubernetes management
- **Helm**: Latest stable version for Kubernetes package management
- **Terraform**: Latest stable version for Infrastructure as Code
- **OpenShift CLI**: Latest stable version (oc) for OpenShift operations

### Ansible Collections
All collections from your `requirements.yml` are included:
- `amazon.aws` - AWS cloud modules
- `ansible.posix` - POSIX system modules
- `ansible.scm` - Source control management
- `ansible.utils` - Utility modules
- `awx.awx` - AWX/Ansible Tower modules
- `community.aws` - Community AWS modules
- `community.general` - General community modules
- `community.hashi_vault` - HashiCorp Vault integration
- `community.vmware` - VMware modules
- `google.cloud` - Google Cloud modules
- `kubernetes.core` - Kubernetes modules
- `purepx.px_backup` - Portworx backup modules

### Python Dependencies
All Python packages from your `requirements.txt` are included, covering:
- Core dependencies (click, requests, urllib3, etc.)
- Kubernetes and cloud dependencies
- Ansible development tools
- Testing and linting tools

## 📁 Files

### Execution Environment Definition
- `ansible-aio-ee.yml` - Ansible Builder EE definition file
- `Containerfile.ansible-aio-ee` - Dockerfile for direct Docker builds

### Build and Management
- `build-ansible-aio-ee.sh` - Comprehensive build script with testing
- `README-ansible-aio-ee.md` - This documentation file

## 🛠️ Building the Execution Environment

### Prerequisites
- `ansible-builder` installed: `pip install ansible-builder`
- Docker or Podman
- Required files: `requirements.txt`, `requirements.yml`

### Quick Build
```bash
# Build using ansible-builder (recommended)
./build-ansible-aio-ee.sh

# Build using Docker directly
./build-ansible-aio-ee.sh -m docker

# Build with verbose output
./build-ansible-aio-ee.sh -v

# Build with specific tag
./build-ansible-aio-ee.sh -t v1.0.0
```

### Advanced Build Options
```bash
# Build and test
./build-ansible-aio-ee.sh --test

# Build and push to registry
./build-ansible-aio-ee.sh -p -r quay.io/myuser/ansible-aio-ee

# Clean up build artifacts
./build-ansible-aio-ee.sh --clean
```

### Manual Build Commands
```bash
# Using ansible-builder
ansible-builder build --file ansible-aio-ee.yml --tag ansible-aio-ee:latest

# Using Docker directly
docker build -f Containerfile.ansible-aio-ee -t ansible-aio-ee:latest .
```

## 🧪 Testing the Execution Environment

### Basic Functionality Tests
```bash
# Test Python version
docker run --rm ansible-aio-ee:latest python3 --version

# Test Ansible
docker run --rm ansible-aio-ee:latest ansible --version

# Test cloud tools
docker run --rm ansible-aio-ee:latest aws --version
docker run --rm ansible-aio-ee:latest gcloud version
docker run --rm ansible-aio-ee:latest kubectl version --client
docker run --rm ansible-aio-ee:latest helm version
docker run --rm ansible-aio-ee:latest terraform version
docker run --rm ansible-aio-ee:latest oc version
```

### Interactive Testing
```bash
# Run interactive shell
docker run -it --rm ansible-aio-ee:latest /bin/bash

# Test with mounted volume
docker run -it --rm -v $(pwd):/workspace ansible-aio-ee:latest /bin/bash
```

## 🔧 Configuration

### Environment Variables
The EE includes pre-configured environment variables:
- `ANSIBLE_FORCE_COLOR=1` - Enable colored output
- `ANSIBLE_HOST_KEY_CHECKING=false` - Disable host key checking
- `AWS_DEFAULT_REGION=us-east-1` - Default AWS region
- `KUBECONFIG=/tmp/kubeconfig` - Kubernetes config location
- `HELM_HOME=/tmp/.helm` - Helm home directory

### Working Directory
- Default working directory: `/workspace`
- Non-root user: `ansible`
- Log directory: `/logs`

## 📦 Tool Versions

The EE includes the following tool versions:
- **Python**: 3.11.x
- **Ansible**: Latest stable
- **kubectl**: Latest stable
- **Helm**: 3.14.4
- **Terraform**: 1.7.5
- **OpenShift CLI**: Latest stable
- **AWS CLI**: v2 (latest)
- **Google Cloud SDK**: Latest

## 🔒 Security Features

- Non-root user execution
- Minimal attack surface
- Secure base image (UBI 8)
- Proper file permissions
- Certificate bundle configuration

## 🚀 Performance Optimizations

### Layer Caching
The Containerfile is optimized for Docker layer caching:
1. Base system dependencies
2. Python setup
3. Individual tool installations
4. Python packages
5. Ansible collections
6. Cleanup and finalization

### Image Size Optimization
- Multi-stage build considerations
- Cleanup of temporary files
- Removal of unnecessary packages
- Cache purging

## 🔄 Updates and Maintenance

### Updating Tool Versions
To update tool versions, modify the appropriate section in either:
- `ansible-aio-ee.yml` (for ansible-builder)
- `Containerfile.ansible-aio-ee` (for Docker builds)

### Adding New Collections
Add new collections to `requirements.yml` and rebuild the EE.

### Adding New Python Dependencies
Add new dependencies to `requirements.txt` and rebuild the EE.

## 🐛 Troubleshooting

### Common Issues

#### Build Failures
```bash
# Check prerequisites
./build-ansible-aio-ee.sh --help

# Clean and rebuild
./build-ansible-aio-ee.sh --clean
./build-ansible-aio-ee.sh -v
```

#### Tool Not Found
```bash
# Check if tool is installed
docker run --rm ansible-aio-ee:latest which <tool_name>

# Check PATH
docker run --rm ansible-aio-ee:latest echo $PATH
```

#### Permission Issues
```bash
# Run as root for debugging
docker run -it --rm --user root ansible-aio-ee:latest /bin/bash
```

### Debug Mode
```bash
# Run with debug output
docker run -it --rm ansible-aio-ee:latest /bin/bash -c "set -x; <command>"
```

## 📚 Usage Examples

### Running Ansible Playbooks
```bash
# Run playbook with EE
docker run --rm -v $(pwd):/workspace ansible-aio-ee:latest ansible-playbook playbook.yml

# Run with inventory
docker run --rm -v $(pwd):/workspace ansible-aio-ee:latest ansible-playbook -i inventory/hosts.yml playbook.yml
```

### Kubernetes Operations
```bash
# Get cluster info
docker run --rm -v ~/.kube:/tmp/.kube ansible-aio-ee:latest kubectl cluster-info

# List pods
docker run --rm -v ~/.kube:/tmp/.kube ansible-aio-ee:latest kubectl get pods
```

### AWS Operations
```bash
# List S3 buckets
docker run --rm -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY ansible-aio-ee:latest aws s3 ls

# Describe EC2 instances
docker run --rm -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY ansible-aio-ee:latest aws ec2 describe-instances
```

### Terraform Operations
```bash
# Initialize Terraform
docker run --rm -v $(pwd):/workspace ansible-aio-ee:latest terraform init

# Plan Terraform changes
docker run --rm -v $(pwd):/workspace ansible-aio-ee:latest terraform plan
```

## 🤝 Contributing

To contribute to this Execution Environment:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This Execution Environment is provided under the same license as the parent project.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the build logs with verbose output
3. Test individual components
4. Create an issue with detailed information

---

**Note**: This Execution Environment is designed for comprehensive cloud and container operations. Ensure you have proper credentials and permissions configured for the tools you plan to use. 