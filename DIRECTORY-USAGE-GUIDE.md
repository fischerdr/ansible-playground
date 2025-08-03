# Directory Usage Guide for Ansible EE

This guide explains how to use the Ansible Execution Environment build scripts now that they're organized into separate directories.

## 📁 **Directory Structure**

```text
ansible-playground/
├── ansible-aio-ee/                    # Regular (internet-connected) EE
│   ├── ansible-aio-ee.yml
│   ├── Containerfile.ansible-aio-ee
│   ├── build-ansible-aio-ee.sh
│   ├── test-ansible-aio-ee.sh
│   ├── README-ansible-aio-ee.md
│   ├── requirements.txt
│   └── requirements.yml
├── ansible-aio-ee-airgapped/          # Air-gapped (offline) EE
│   ├── ansible-aio-ee-airgapped.yml
│   ├── build-airgapped-ee.sh
│   ├── prepare-airgapped-build.sh
│   ├── README-airgapped-ee.md
│   ├── requirements-airgapped.txt
│   ├── requirements-airgapped.yml
│   ├── tools/                        # (created by prepare script)
│   ├── wheels/                       # (created by prepare script)
│   └── collections/                  # (created by prepare script)
├── requirements.txt                   # Main project requirements
├── requirements.yml                   # Main project collections
└── [other project files]
```

## 🚀 **Usage Instructions**

### **Regular EE (Internet-Connected)**

The regular EE scripts work perfectly in their new directory since all required files are co-located:

```bash
# Navigate to the regular EE directory
cd ansible-aio-ee/

# Build the EE
./build-ansible-aio-ee.sh

# Build and test
./build-ansible-aio-ee.sh --test

# Build with specific tag
./build-ansible-aio-ee.sh -t v1.0.0
```

### **Air-gapped EE (Offline)**

The air-gapped EE requires a two-phase approach:

#### **Phase 1: Preparation (Internet Required)**

```bash
# Navigate to the air-gapped EE directory
cd ansible-aio-ee-airgapped/

# Download all dependencies (requires internet)
./prepare-airgapped-build.sh

# This will create:
# - tools/ directory with binary tools
# - wheels/ directory with Python packages  
# - collections/ directory with Ansible collections
```

#### **Phase 2: Build (Air-gapped Environment)**

```bash
# In the air-gapped environment, navigate to the directory
cd ansible-aio-ee-airgapped/

# Check that all dependencies are available
./build-airgapped-ee.sh --check-deps

# Build the EE
./build-airgapped-ee.sh

# Build and test
./build-airgapped-ee.sh --test
```

## 🔧 **Script Modifications Made**

### **Air-gapped Scripts Enhanced**

The air-gapped scripts have been updated to handle the new directory structure:

1. **`prepare-airgapped-build.sh`** now:
   - Downloads wheels for both local and main project requirements
   - Handles collection downloads from either local or main project requirements
   - Creates proper directory structure within the air-gapped directory

2. **`build-airgapped-ee.sh`** continues to:
   - Check for local tools, wheels, and collections directories
   - Build using only local dependencies
   - Validate all components before building

### **Regular Scripts**

The regular EE scripts work unchanged since all dependencies are in the same directory.

## ✅ **Validation Steps**

### **For Regular EE**

```bash
cd ansible-aio-ee/
ls -la
# Should show: ansible-aio-ee.yml, requirements.txt, requirements.yml, build scripts
```

### **For Air-gapped EE (After Preparation)**

```bash
cd ansible-aio-ee-airgapped/
ls -la
# Should show: all air-gapped files plus tools/, wheels/, collections/ directories
```

## 🐛 **Troubleshooting**

### **Common Issues**

#### **"requirements.txt not found"**

- **For regular EE**: Make sure you're in the `ansible-aio-ee/` directory
- **For air-gapped EE**: Run the prepare script first

#### **"tools/ directory not found"**

- **Solution**: Run `./prepare-airgapped-build.sh` in the `ansible-aio-ee-airgapped/` directory

#### **Collection download errors**

- **Solution**: The prepare script will try local requirements first, then fall back to main project requirements

### **Path Issues**

If you encounter path-related errors:

1. **Always run scripts from their respective directories**
2. **For air-gapped**: Ensure preparation was run in the same directory as the build script
3. **Check that all required files exist in the expected locations**

## 📋 **Quick Reference**

### **Regular EE Commands**

```bash
cd ansible-aio-ee/
./build-ansible-aio-ee.sh                    # Build
./build-ansible-aio-ee.sh --test             # Build and test
./test-ansible-aio-ee.sh                     # Test existing build
```

### **Air-gapped EE Commands**

```bash
cd ansible-aio-ee-airgapped/

# Preparation phase (with internet)
./prepare-airgapped-build.sh                 # Download all dependencies
./prepare-airgapped-build.sh --clean         # Clean and re-download

# Build phase (offline)
./build-airgapped-ee.sh --check-deps         # Check dependencies
./build-airgapped-ee.sh                      # Build
./build-airgapped-ee.sh --test               # Build and test
```

## 🔄 **Migration Benefits**

### **Organization**

- Clear separation between regular and air-gapped builds
- Self-contained directories with all necessary files
- Easier to maintain and version control

### **Portability**

- Each directory can be transferred independently
- Air-gapped directory becomes completely self-contained after preparation
- Reduced confusion about which files belong to which build type

### **Maintenance**

- Easier to update specific build types
- Clear documentation for each approach
- Reduced risk of mixing regular and air-gapped components

---

**Note**: Always run the build scripts from within their respective directories to ensure proper file path resolution.
