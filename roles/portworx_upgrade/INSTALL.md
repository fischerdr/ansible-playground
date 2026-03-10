# Installation Guide

## Prerequisites

### Software Requirements

- Ansible Core 2.12 or later
- Python 3.9 or later
- OpenShift CLI (`oc`) or kubectl
- Git (for collection installation)

### Cluster Requirements

- OpenShift 4.18 or later
- Portworx Operator installed
- Cluster admin permissions
- Network access to OpenShift API server

### Required Ansible Collections

```yaml
collections:
  - name: kubernetes.core
    version: ">=2.3.0"
  - name: ansible.builtin
```

## Installation Methods

### Method 1: From Archive (Recommended for Standalone Use)

1. Extract the archive:

```bash
tar -xzf portworx-upgrade-role-1.0.0.tar.gz
```

2. Copy to your Ansible roles directory:

```bash
# Option A: Project-local roles directory
mkdir -p roles
cp -r portworx-upgrade-role roles/portworx_upgrade

# Option B: System-wide roles directory
sudo cp -r portworx-upgrade-role /usr/share/ansible/roles/portworx_upgrade

# Option C: User roles directory
mkdir -p ~/.ansible/roles
cp -r portworx-upgrade-role ~/.ansible/roles/portworx_upgrade
```

3. Install required collections:

```bash
cd portworx-upgrade-role
ansible-galaxy collection install -r requirements.yml
```

### Method 2: From Git Repository

1. Clone the repository:

```bash
git clone https://github.com/your-org/ansible-playground.git
cd ansible-playground
```

2. Install collections:

```bash
ansible-galaxy collection install -r requirements.yml
```

3. The role is available at `roles/portworx_upgrade`

### Method 3: Ansible Galaxy (If Published)

```bash
ansible-galaxy role install your_org.portworx_upgrade
ansible-galaxy collection install -r ~/.ansible/roles/your_org.portworx_upgrade/requirements.yml
```

## Verify Installation

### Test Role Import

```bash
ansible-doc -t role -l | grep portworx_upgrade
```

### Check Collections

```bash
ansible-galaxy collection list | grep kubernetes.core
```

Should show `kubernetes.core` version 2.3.0 or later.

### Test Connectivity

```bash
# Verify OpenShift connectivity
oc get nodes

# Verify Portworx namespace access
oc get pods -n portworx
```

## Configuration

### 1. Set Up Inventory

Create `inventory/localhost.yml`:

```yaml
---
all:
  hosts:
    localhost:
      ansible_connection: local
      ansible_python_interpreter: "{{ ansible_playbook_python }}"
```

### 2. Create Playbook

Create `playbooks/upgrade_portworx.yml`:

```yaml
---
- name: Upgrade Portworx cluster
  hosts: localhost
  gather_facts: true
  vars:
    portworx_target_version: "3.5.0"
    portworx_cluster_name: "my-cluster"
  roles:
    - role: portworx_upgrade
```

### 3. Configure Variables

Create `group_vars/all.yml` or use command-line variables:

```yaml
---
# Required
portworx_target_version: "3.5.0"

# Optional - customize as needed
portworx_namespace: "portworx"
portworx_cluster_name: "production"
portworx_impatient_mode: false
portworx_detailed_logging: true
```

## Testing Installation

### Run Preflight Check

```bash
ansible-playbook playbooks/upgrade_portworx.yml --tags preflight --check
```

Expected output:
- No errors about missing collections
- Successful connection to cluster
- Validation checks complete

### Dry Run

```bash
ansible-playbook playbooks/upgrade_portworx.yml --check
```

## AAP/AWX Installation

For AAP/AWX deployment, see `aap_import/README.md` for:

- Automated import script
- Manual import steps
- Job template configuration
- Workflow setup

Quick import:

```bash
cd aap_import
export CONTROLLER_HOST=https://your-aap-server
export CONTROLLER_USERNAME=admin
export CONTROLLER_PASSWORD=your-password
./import_to_aap.sh
```

## Troubleshooting Installation

### Collection Not Found

```bash
# Verify collection path
ansible-config dump | grep COLLECTIONS_PATHS

# Install to specific path
ansible-galaxy collection install kubernetes.core -p ./collections
```

### Permission Issues

```bash
# Use user installation directory
ansible-galaxy collection install -r requirements.yml --force

# Or use sudo for system-wide installation
sudo ansible-galaxy collection install -r requirements.yml
```

### Python Dependencies

```bash
# Install kubernetes Python library
pip install kubernetes

# Or use virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # If provided
```

### Kubeconfig Issues

```bash
# Verify kubeconfig
export KUBECONFIG=/path/to/kubeconfig
oc whoami

# Test with Ansible
ansible localhost -m kubernetes.core.k8s_info -a "kind=Namespace"
```

## Post-Installation

### Verify Role Structure

```bash
cd roles/portworx_upgrade  # or wherever you installed
ls -la

# Expected structure:
# defaults/main.yml
# vars/main.yml
# tasks/main.yml
# tasks/preflight/
# tasks/upgrade/
# tasks/monitor/
# tasks/validate/
# tasks/report/
# templates/
# library/
# meta/main.yml
```

### Update Role Path in Playbooks

Ensure your playbook references the correct role name:

```yaml
roles:
  - role: portworx_upgrade  # If installed in roles/portworx_upgrade
  # OR
  - role: your_org.portworx_upgrade  # If installed from Galaxy
```

## Upgrading the Role

### From Archive

```bash
# Backup current version
cp -r roles/portworx_upgrade roles/portworx_upgrade.backup

# Extract and replace
tar -xzf portworx-upgrade-role-1.1.0.tar.gz
cp -r portworx-upgrade-role roles/portworx_upgrade

# Update collections
cd roles/portworx_upgrade
ansible-galaxy collection install -r requirements.yml --force
```

### From Git

```bash
cd ansible-playground
git pull origin main
ansible-galaxy collection install -r requirements.yml --force
```

## Next Steps

1. Review `README.md` for role usage and variables
2. Check `aap_import/README.md` for AAP integration
3. Explore example playbooks in `playbooks/`
4. Review version files in `versions/` directory
5. Run preflight check on target cluster
