# Air-gapped Ansible All-In-One Execution Environment

A comprehensive Ansible Execution Environment designed for air-gapped (offline) environments, where internet access is not available during the build process. This EE includes all major cloud and container management tools using locally stored binaries and dependencies.

## 🔒 **Air-gapped Features**

### **Offline Capability**

- All tools are pre-downloaded and stored locally
- Python packages installed from local wheels
- Ansible collections installed from local archives
- No internet access required during build

### **Security Benefits**

- Complete control over all dependencies
- No external downloads during build
- Audit trail of all included components
- Suitable for secure/classified environments

## 📦 **Included Tools & Components**

### **Base Environment**

- **Base Image**: Red Hat Universal Base Image 8 (stream)
- **Python Version**: 3.11 (set as default interpreter)
- **Ansible**: Latest stable version with all dependencies

### **Cloud & Container Tools**

- **kubectl**: Kubernetes command-line tool
- **Helm**: Kubernetes package manager
- **Terraform**: Infrastructure as Code tool
- **OpenShift CLI (oc)**: OpenShift command-line tool
- **HashiCorp Vault CLI**: Secret management command-line tool
- **AWS CLI v2**: Amazon Web Services command-line interface
- **Google Cloud SDK**: Google Cloud Platform tools (gcloud, gsutil, bq)

### **Ansible Collections**

All collections from your requirements are included locally:

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

## 📁 **File Structure**

```
├── ansible-aio-ee-airgapped.yml        # EE definition for air-gapped build
├── requirements-airgapped.yml          # Ansible collections (local sources)
├── requirements-airgapped.txt          # Python requirements (for local wheels)
├── prepare-airgapped-build.sh          # Preparation script (run with internet)
├── build-airgapped-ee.sh              # Build script (run offline)
├── tools/                             # Local tool binaries
│   ├── kubectl
│   ├── helm
│   ├── terraform
│   ├── oc
│   ├── vault
│   ├── awscliv2.zip
│   └── google-cloud-sdk.tar.gz
├── wheels/                            # Python wheel files
│   └── *.whl
├── collections/                       # Ansible collection archives
│   └── *.tar.gz
└── README-airgapped-ee.md            # This documentation
```

## 🛠️ **Setup Process**

### **Phase 1: Preparation (Internet Required)**

Run this phase in an environment with internet access:

```bash
# Download all dependencies
./prepare-airgapped-build.sh

# Or download specific components
./prepare-airgapped-build.sh --tools-only
./prepare-airgapped-build.sh --wheels-only
./prepare-airgapped-build.sh --collections-only
```

This will create:

- `tools/` directory with all binary tools
- `wheels/` directory with Python packages
- `collections/` directory with Ansible collections

### **Phase 2: Transfer to Air-gapped Environment**

Transfer the entire project directory to your air-gapped environment using approved methods:

- Removable media (USB, CD/DVD)
- Secure file transfer
- Physical transport

### **Phase 3: Build (Offline)**

In your air-gapped environment:

```bash
# Check that all dependencies are available
./build-airgapped-ee.sh --check-deps

# Build the EE
./build-airgapped-ee.sh

# Build and test
./build-airgapped-ee.sh --test
```

## 🔧 **Build Options**

### **Preparation Phase Commands**

```bash
# Full preparation (recommended)
./prepare-airgapped-build.sh

# With verbose output
./prepare-airgapped-build.sh -v

# Clean existing downloads and re-download
./prepare-airgapped-build.sh --clean

# Download only specific components
./prepare-airgapped-build.sh --tools-only
./prepare-airgapped-build.sh --wheels-only
./prepare-airgapped-build.sh --collections-only
```

### **Build Phase Commands**

```bash
# Basic build
./build-airgapped-ee.sh

# Build with specific tag
./build-airgapped-ee.sh -t v1.0.0

# Build using Docker directly
./build-airgapped-ee.sh -m docker

# Build with verbose output
./build-airgapped-ee.sh -v

# Check dependencies before building
./build-airgapped-ee.sh --check-deps

# Build and run tests
./build-airgapped-ee.sh --test
```

## ✅ **Validation**

### **Dependency Check**

```bash
# Verify all local dependencies are available
./build-airgapped-ee.sh --check-deps
```

Expected output:

```
[SUCCESS] tools/ directory found
[SUCCESS] ✓ tools/kubectl
[SUCCESS] ✓ tools/helm
[SUCCESS] ✓ tools/terraform
[SUCCESS] ✓ tools/oc
[SUCCESS] ✓ tools/awscliv2.zip
[SUCCESS] ✓ tools/google-cloud-sdk.tar.gz
[SUCCESS] collections/ directory found
[SUCCESS] wheels/ directory found
[SUCCESS] All dependencies are available for air-gapped build
```

### **Build Testing**

```bash
# Test the built EE
./build-airgapped-ee.sh --test

# Manual testing
docker run --rm ansible-aio-ee-airgapped:latest ansible --version
docker run --rm ansible-aio-ee-airgapped:latest kubectl version --client
docker run --rm ansible-aio-ee-airgapped:latest helm version
```

## 🚀 **Usage Examples**

### **Running Ansible Playbooks**

```bash
# Run playbook with air-gapped EE
docker run --rm -v $(pwd):/workspace ansible-aio-ee-airgapped:latest ansible-playbook playbook.yml

# Run with inventory
docker run --rm -v $(pwd):/workspace ansible-aio-ee-airgapped:latest ansible-playbook -i inventory/hosts.yml playbook.yml
```

### **Cloud Operations**

```bash
# Kubernetes operations
docker run --rm -v ~/.kube:/tmp/.kube ansible-aio-ee-airgapped:latest kubectl get pods

# AWS operations (with credentials)
docker run --rm -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY ansible-aio-ee-airgapped:latest aws s3 ls

# Terraform operations
docker run --rm -v $(pwd):/workspace ansible-aio-ee-airgapped:latest terraform init
```

### **Interactive Shell**

```bash
# Access the EE shell
docker run -it --rm ansible-aio-ee-airgapped:latest /bin/bash

# With mounted workspace
docker run -it --rm -v $(pwd):/workspace ansible-aio-ee-airgapped:latest /bin/bash
```

## 🔧 **Customization**

### **Adding New Tools**

1. Download the tool binary in the preparation phase
2. Add it to the `tools/` directory
3. Update `ansible-aio-ee-airgapped.yml` to copy and install the tool
4. Rebuild the EE

### **Adding Python Packages**

1. Add the package to `requirements-airgapped.txt`
2. Run `pip download` to get the wheel files
3. Rebuild the EE

### **Adding Ansible Collections**

1. Add the collection to `requirements-airgapped.yml`
2. Download the collection using `ansible-galaxy collection download`
3. Rebuild the EE

## 🛡️ **Security Considerations**

### **Advantages**

- Complete control over all dependencies
- No external network access during build
- Audit trail of all included components
- Reproducible builds
- Suitable for classified environments

### **Best Practices**

- Verify checksums of downloaded tools
- Scan all dependencies for vulnerabilities
- Keep local dependencies updated
- Document all included versions
- Test thoroughly before deployment

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Missing Dependencies**

```bash
# Error: tools/kubectl missing
# Solution: Run preparation script again
./prepare-airgapped-build.sh --tools-only
```

#### **Build Failures**

```bash
# Check dependencies first
./build-airgapped-ee.sh --check-deps

# Build with verbose output
./build-airgapped-ee.sh -v
```

#### **Tool Not Found in Container**

```bash
# Check if tool is installed
docker run --rm ansible-aio-ee-airgapped:latest which <tool_name>

# Check PATH
docker run --rm ansible-aio-ee-airgapped:latest echo $PATH
```

### **Debug Steps**

1. Verify all local dependencies are present
2. Check file permissions on tools
3. Review build logs for errors
4. Test individual components
5. Compare with working internet-connected build

## 📊 **Tool Versions**

The air-gapped EE includes specific versions of tools downloaded during preparation:

- **kubectl**: Latest stable (downloaded at preparation time)
- **Helm**: v3.14.4
- **Terraform**: v1.7.5
- **OpenShift CLI**: Latest stable (downloaded at preparation time)
- **HashiCorp Vault CLI**: v1.15.6
- **AWS CLI**: v2 (latest at preparation time)
- **Google Cloud SDK**: Latest (downloaded at preparation time)

To update versions:

1. Run the preparation script again with `--clean`
2. Transfer updated files to air-gapped environment
3. Rebuild the EE

## 📋 **Checklist for Air-gapped Deployment**

### **Preparation Phase** ✅

- [ ] Run `./prepare-airgapped-build.sh` with internet access
- [ ] Verify all tools downloaded to `tools/` directory
- [ ] Verify Python wheels downloaded to `wheels/` directory
- [ ] Verify Ansible collections downloaded to `collections/` directory
- [ ] Create secure transfer package

### **Transfer Phase** ✅

- [ ] Transfer entire project directory to air-gapped environment
- [ ] Verify file integrity after transfer
- [ ] Ensure all files have correct permissions

### **Build Phase** ✅

- [ ] Run `./build-airgapped-ee.sh --check-deps`
- [ ] Build EE with `./build-airgapped-ee.sh`
- [ ] Test EE with `./build-airgapped-ee.sh --test`
- [ ] Verify all tools work correctly

### **Deployment Phase** ✅

- [ ] Tag EE for your registry
- [ ] Push to internal registry (if applicable)
- [ ] Test with actual playbooks
- [ ] Document deployment for team

## 🤝 **Contributing**

To contribute to the air-gapped EE:

1. Test changes in both internet-connected and air-gapped environments
2. Update both regular and air-gapped versions
3. Document any new dependencies or tools
4. Ensure security compliance for air-gapped environments

## 📄 **License**

This Air-gapped Execution Environment is provided under the same license as the parent project.

---

**Note**: This air-gapped EE is specifically designed for secure, isolated environments where internet access is not available during the build process. Ensure you follow your organization's security policies for transferring and using external software in air-gapped environments.
