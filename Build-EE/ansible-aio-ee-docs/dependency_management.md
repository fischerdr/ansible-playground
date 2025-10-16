# Ansible Collection Dependency Management

This project uses a two-tier dependency management system to separate direct project dependencies from collection-specific requirements.

## File Structure

- **`requirements.txt`**: Core project dependencies (Ansible, testing tools, development utilities)
- **`requirements-collections.txt`**: Auto-generated collection dependencies (discovered from collections)
- **`scripts/update_collection_requirements.py`**: Python script to discover and update collection requirements
- **`scripts/update_requirements.sh`**: Convenience shell script for common operations

## Quick Start

### 1. Update Collection Dependencies

```bash
# Scan collections and update requirements-collections.txt
./scripts/update_requirements.sh

# See what would be updated without making changes
./scripts/update_requirements.sh --dry-run

# Update and install all dependencies
./scripts/update_requirements.sh --install
```

### 2. Install Dependencies

```bash
# Install core project dependencies
pip install -r requirements.txt

# Install collection-specific dependencies
pip install -r requirements-collections.txt

# Or install both at once
pip install -r requirements.txt -r requirements-collections.txt
```

## Scripts Documentation

### `update_collection_requirements.py`

**Purpose**: Automatically discovers Python dependencies from all installed Ansible collections and generates a consolidated requirements file.

**Features**:

- ✅ Scans all `requirements.txt` files in collections directory
- ✅ Resolves version conflicts using most restrictive compatible versions
- ✅ Groups dependencies by collection type for better organization
- ✅ Tracks dependency sources for debugging
- ✅ Handles extras syntax (e.g., `package[extra1,extra2]`)
- ✅ Provides detailed conflict reporting

**Usage**:

```bash
# Basic usage
python scripts/update_collection_requirements.py

# Advanced options
python scripts/update_collection_requirements.py \
    --collections-dir ./collections \
    --output custom-requirements.txt \
    --dry-run \
    --include-test-deps \
    --verbose
```

**Options**:

- `--collections-dir PATH`: Path to collections directory (default: `collections`)
- `--output PATH`: Output file path (default: `requirements-collections.txt`)
- `--dry-run`: Show what would be written without creating files
- `--include-test-deps`: Include test dependencies from collections
- `--verbose, -v`: Show detailed package discovery information

### `update_requirements.sh`

**Purpose**: Convenience wrapper for common dependency management tasks.

**Usage**:

```bash
# Update collection requirements
./scripts/update_requirements.sh

# Preview changes without modifying files
./scripts/update_requirements.sh --dry-run

# Update and install all dependencies
./scripts/update_requirements.sh --install

# Show verbose output
./scripts/update_requirements.sh --verbose
```

## Dependency Analysis Results

The script discovered **27 unique packages** from **13 collection requirements files**:

### Core Collections Covered

- **Kubernetes** (`kubernetes.core`): kubernetes, jsonpatch, requests-oauthlib
- **AWS** (`amazon.aws`, `community.aws`): boto3, botocore
- **VMware** (`community.vmware`, `vmware.vmware`): pyvmomi, vmware-vcenter, vmware-vapi-common-client
- **Google Cloud** (`google.cloud`): google-auth, google-cloud-storage
- **Ansible Utils** (`ansible.utils`): jsonschema, textfsm, ttp, xmltodict, netaddr
- **HashiCorp Vault** (`community.hashi_vault`): requests, urllib3, packaging
- **AWX** (`awx.awx`): pytz, python-dateutil, awxkit

### Dependencies Already in Main requirements.txt

✅ `kubernetes==32.0.1` (satisfies `>=24.2.0`)  
✅ `boto3==1.37.30` (satisfies `>=1.34.0`)  
✅ `pyvmomi==8.0.3.0.1` (satisfies `>=8.0.3.0.1`)  
✅ `google-auth==2.38.0`  
✅ `google-cloud-storage==3.2.0`  
✅ `hvac==2.3.0`  
✅ `requests==2.31.0`  
✅ `python-dateutil==2.8.2` (satisfies `>=2.7.0`)  
✅ `aiohttp==3.9.3`  

### New Dependencies Added

- `jsonpatch` (Kubernetes operations)
- `botocore>=1.34.0` (AWS backend)
- `requests-oauthlib` (OAuth authentication)
- `jsonschema`, `textfsm`, `ttp`, `xmltodict`, `netaddr>=0.10.1` (Ansible utils)
- `urllib3>=1.15` (HTTP client)
- `vmware-vcenter`, `vmware-vapi-common-client` (VMware APIs)
- `pytz`, `awxkit` (AWX/Tower operations)
- Plus documentation-related dependencies for advanced usage

## Maintenance

### When to Update

Run the update script when:

- Adding new Ansible collections to your project
- Updating existing collections (`ansible-galaxy collection install -r requirements.yml --upgrade`)
- Collections change their Python dependencies
- Experiencing import errors from collection modules

### Automation Integration

Add to your CI/CD pipeline:

```yaml
# Example GitHub Actions step
- name: Update collection dependencies
  run: |
    python scripts/update_collection_requirements.py
    git diff --exit-code requirements-collections.txt || echo "::warning::Collection requirements changed"
```

### Version Conflict Resolution

The script automatically resolves version conflicts by:

1. **Compatible ranges**: Finds intersection of all version constraints
2. **Incompatible constraints**: Uses most restrictive requirement and warns
3. **Complex comments**: Strips comments that interfere with version parsing

Review the generated file for any `⚠️  VERSION CONFLICTS DETECTED` warnings and manually verify the chosen versions are appropriate for your use case.

## Benefits

1. **Automated Discovery**: No need to manually track collection dependencies
2. **Version Conflict Detection**: Automatically identifies and resolves version conflicts
3. **Source Tracking**: Know which collections require which dependencies
4. **Clean Separation**: Keep project and collection dependencies separate
5. **CI/CD Ready**: Easy to integrate into automated workflows
6. **Maintainable**: Self-updating as collections change

This system ensures that `pip install -r requirements.txt -r requirements-collections.txt` will install all necessary dependencies for your Ansible automation to work correctly.
