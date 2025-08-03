# Execution Environment Integration with Collection Dependency Management

This document explains how the collection dependency management system has been integrated into your Ansible Execution Environment (EE) build process.

## 🔄 **Integration Overview**

The dependency management system is now fully integrated into your EE builds:

```
┌─────────────────────────────────────────────────────────────────┐
│                    EE Build Process                             │
├─────────────────────────────────────────────────────────────────┤
│ 1. Update collection requirements (automatic)                  │
│    └── scripts/update_collection_requirements.py               │
│                                                                 │
│ 2. Install base dependencies                                   │
│    └── requirements.txt (your core dependencies)               │
│                                                                 │
│ 3. Install collection dependencies                             │
│    └── requirements-collections.txt (auto-generated)           │
│                                                                 │
│ 4. Install Ansible collections                                 │
│    └── requirements.yml                                        │
│                                                                 │
│ 5. Build container with all tools                              │
│    └── Cloud CLIs, Kubernetes tools, etc.                     │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 **Updated Files**

### **Modified EE Configurations:**
- ✅ `execution-environment.yml` - Main EE configuration
- ✅ `ansible-aio-ee/ansible-aio-ee.yml` - All-in-one EE configuration  
- ✅ `ansible-aio-ee/Containerfile.ansible-aio-ee` - Container build file
- ✅ `ansible-navigator.yml` - Navigator configuration

### **New Build Tools:**
- ✅ `ansible-aio-ee/build-ansible-aio-ee-enhanced.sh` - Enhanced build script
- ✅ `docs/execution_environment_integration.md` - This integration guide

## 🚀 **Building Your Enhanced EE**

### **Quick Start:**
```bash
# Build with automatic collection requirements update
./ansible-aio-ee/build-ansible-aio-ee-enhanced.sh

# Build and push to registry
./ansible-aio-ee/build-ansible-aio-ee-enhanced.sh --push --registry quay.io --tag v1.0.0
```

### **Enhanced Build Script Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--update-collections` | Update collection requirements before build | **enabled** |
| `--no-update-collections` | Skip collection requirements update | disabled |
| `--no-cache` | Build without Docker cache | cache enabled |
| `--push` | Push to registry after build | don't push |
| `--registry REGISTRY` | Override registry URL | `localhost` |
| `--tag TAG` | Override image tag | `latest` |
| `--dry-run` | Show what would be done | execute |
| `--verbose` | Show detailed output | normal |

### **Build Process Workflow:**

1. **Environment Validation** - Checks for required files and tools
2. **Collection Requirements Update** - Automatically scans collections and updates `requirements-collections.txt`
3. **Build Context Preparation** - Copies requirements files to build directory
4. **Container Build** - Uses ansible-builder, Docker, or Podman
5. **Image Verification** - Tests the built image
6. **Registry Push** - Optionally pushes to registry
7. **Cleanup** - Removes temporary files

## 🛠 **Manual Build Process**

If you prefer manual builds or CI/CD integration:

### **Step 1: Update Collection Dependencies**
```bash
# Update collection requirements
python scripts/update_collection_requirements.py

# Or use the helper script
./scripts/update_requirements.sh
```

### **Step 2: Build with ansible-builder**
```bash
cd ansible-aio-ee

# Copy requirements files to build context
cp ../requirements.txt .
cp ../requirements-collections.txt .
cp ../requirements.yml .

# Build the EE
ansible-builder build \
    --file ansible-aio-ee.yml \
    --tag localhost/ansible-aio-ee:latest \
    --container-runtime docker
```

### **Step 3: Alternative - Build with Docker/Podman**
```bash
cd ansible-aio-ee

# Copy requirements files
cp ../requirements.txt .
cp ../requirements-collections.txt .
cp ../requirements.yml .

# Build with Docker
docker build \
    --file Containerfile.ansible-aio-ee \
    --tag localhost/ansible-aio-ee:latest \
    .

# Or build with Podman
podman build \
    --file Containerfile.ansible-aio-ee \
    --tag localhost/ansible-aio-ee:latest \
    .
```

## 🔧 **Configuration Details**

### **Dependencies Installation Order:**

The EE installs Python dependencies in this specific order to avoid conflicts:

1. **System packages** (dnf/yum packages)
2. **Core Python tools** (`pip`, `setuptools`, `wheel`)
3. **Main requirements** (`requirements.txt` - your pinned versions)
4. **Collection requirements** (`requirements-collections.txt` - collection needs)
5. **Ansible collections** (`requirements.yml`)

### **Dependency Resolution:**

- **Your pinned versions take precedence** - Collection minimums are satisfied by your exact versions
- **No version conflicts** - All overlapping packages are compatible
- **New dependencies added** - 22 additional packages for collection functionality
- **Automatic updates** - Collections changes are detected and integrated

### **Key Changes Made:**

**execution-environment.yml:**
```yaml
# Before
python: requirements.txt

# After  
python: requirements.txt
# Additional build step installs requirements-collections.txt
```

**ansible-aio-ee.yml:**
```yaml
# Before
- RUN python3.11 -m pip install awscli boto3 google-cloud-sdk kubernetes openshift

# After
- COPY requirements-collections.txt /tmp/requirements-collections.txt
- RUN python3.11 -m pip install -r /tmp/requirements-collections.txt
# Removes hardcoded packages to avoid conflicts
```

**Containerfile:**
```dockerfile
# Before
COPY requirements.txt /tmp/requirements.txt
RUN python3.11 -m pip install -r /tmp/requirements.txt && \
    python3.11 -m pip install awscli boto3 google-cloud-sdk kubernetes openshift

# After
COPY requirements.txt /tmp/requirements.txt
COPY requirements-collections.txt /tmp/requirements-collections.txt
RUN python3.11 -m pip install -r /tmp/requirements.txt && \
    python3.11 -m pip install -r /tmp/requirements-collections.txt
```

## 🎯 **Using Your Enhanced EE**

### **With ansible-navigator:**
```bash
# Configuration already updated in ansible-navigator.yml
ansible-navigator run playbooks/my-playbook.yml
```

### **With ansible-playbook:**
```bash
ansible-playbook --ee-image localhost/ansible-aio-ee:latest playbooks/my-playbook.yml
```

### **Direct Container Run:**
```bash
# Interactive shell
docker run -it --rm \
    --volume ${PWD}:/workspace:Z \
    --workdir /workspace \
    localhost/ansible-aio-ee:latest \
    /bin/bash

# Run specific playbook
docker run --rm \
    --volume ${PWD}:/workspace:Z \
    --workdir /workspace \
    localhost/ansible-aio-ee:latest \
    ansible-playbook playbooks/my-playbook.yml
```

## 🔄 **CI/CD Integration**

### **GitHub Actions Example:**
```yaml
name: Build Ansible EE
on: 
  push:
    paths: 
      - 'collections/**'
      - 'requirements.yml'
      - 'requirements.txt'

jobs:
  build-ee:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Update collection requirements
        run: python scripts/update_collection_requirements.py
      
      - name: Check for changes
        run: |
          if git diff --exit-code requirements-collections.txt; then
            echo "No collection requirement changes"
          else
            echo "Collection requirements updated"
            git add requirements-collections.txt
            git commit -m "Auto-update collection requirements"
          fi
      
      - name: Build EE
        run: ./ansible-aio-ee/build-ansible-aio-ee-enhanced.sh --push --registry ghcr.io --tag ${{ github.sha }}
```

### **GitLab CI Example:**
```yaml
build-ee:
  stage: build
  script:
    - python scripts/update_collection_requirements.py
    - ./ansible-aio-ee/build-ansible-aio-ee-enhanced.sh --push --registry $CI_REGISTRY --tag $CI_COMMIT_SHA
  only:
    changes:
      - collections/**/*
      - requirements.yml
      - requirements.txt
```

## 🧪 **Testing Your EE**

### **Dependency Verification:**
```bash
# Test that all collection dependencies are available
docker run --rm localhost/ansible-aio-ee:latest python -c "
import kubernetes
import boto3
import jsonpatch
import jsonschema
import textfsm
import netaddr
print('✅ All collection dependencies available')
"
```

### **Collection Module Testing:**
```bash
# Test Kubernetes collection
docker run --rm localhost/ansible-aio-ee:latest ansible-doc kubernetes.core.k8s

# Test AWS collection  
docker run --rm localhost/ansible-aio-ee:latest ansible-doc amazon.aws.ec2_instance

# Test VMware collection
docker run --rm localhost/ansible-aio-ee:latest ansible-doc community.vmware.vmware_guest
```

## 📊 **Benefits of Integration**

1. **🔄 Automated Updates** - Collection requirements stay current automatically
2. **🚫 No Conflicts** - Systematic dependency resolution prevents version conflicts
3. **📦 Complete Coverage** - All 27 collection dependencies included
4. **🏗️ Reproducible Builds** - Consistent environments across development/production
5. **⚡ Optimized Layers** - Docker layer caching for faster rebuilds
6. **🔧 Easy Maintenance** - Single script handles entire build process

## 🔍 **Troubleshooting**

### **Build Failures:**

**Missing requirements-collections.txt:**
```bash
# Manually generate it
python scripts/update_collection_requirements.py
```

**Collection requirements script not found:**
```bash
# The build script will warn and skip update
# Manually ensure requirements-collections.txt exists
```

**Version conflicts during build:**
```bash
# Check for conflicts in generated file
grep "VERSION CONFLICTS" requirements-collections.txt
# Review and manually resolve if needed
```

### **Runtime Issues:**

**Module import errors:**
```bash
# Verify specific dependency is included
docker run --rm localhost/ansible-aio-ee:latest pip list | grep package-name
```

**Collection module failures:**
```bash
# Test collection availability
docker run --rm localhost/ansible-aio-ee:latest ansible-galaxy collection list
```

This integration ensures your Execution Environment has all the Python dependencies needed for your Ansible collections to work reliably! 🎯