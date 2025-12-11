# Portworx Upgrade Role - Quick Start Guide

Get started with the portworx_upgrade role in 5 minutes.

## Prerequisites

- Ansible Core 2.12+
- `oc` CLI configured with cluster admin access
- Python 3.8+

## Installation (3 Steps)

### 1. Extract and Install

```bash
# Extract the role
tar -xzf portworx-upgrade-role-1.0.0.tar.gz -C roles/
mv roles/portworx-upgrade-role roles/portworx_upgrade

# Install dependencies
ansible-galaxy collection install -r roles/portworx_upgrade/requirements.yml
pip install -r roles/portworx_upgrade/requirements.txt
```

### 2. Get Version File

```bash
# Set your target version
export PXVER=3.5.0
export KBVER=$(oc version | awk '/Server Version/ {print $3}')

# Download version file
curl -o roles/portworx_upgrade/files/versions/versions-${PXVER} \
  "https://install.portworx.com/$PXVER/version?kbver=$KBVER"
```

### 3. Create Playbook

```bash
# Copy example playbook
cp roles/portworx_upgrade/example-playbook.yml playbooks/px_upgrade.yml
```

## Usage (4 Common Scenarios)

### Scenario 1: Basic Upgrade

```bash
ansible-playbook playbooks/px_upgrade.yml -e portworx_target_version=3.5.0
```

**Time**: ~30-60 minutes depending on cluster size

### Scenario 2: Preflight Check Only

```bash
ansible-playbook playbooks/px_upgrade.yml \
  -e portworx_target_version=3.5.0 \
  --tags preflight
```

**Time**: ~2-5 minutes
**Use case**: Validate cluster is ready before scheduling upgrade

### Scenario 3: Upgrade with Impatient Mode

```bash
ansible-playbook playbooks/px_upgrade.yml \
  -e portworx_target_version=3.5.0 \
  -e portworx_impatient_mode=true \
  -e portworx_impatient_batch_size=7
```

**Time**: ~15-30 minutes (faster for large clusters)
**Use case**: Accelerated upgrade for clusters with many storageless nodes

### Scenario 4: Skip Operator Upgrade

```bash
ansible-playbook playbooks/px_upgrade.yml \
  -e portworx_target_version=3.5.0 \
  -e portworx_skip_operator_upgrade=true
```

**Time**: ~20-40 minutes
**Use case**: Operator already upgraded separately

## What Happens During Upgrade

```
Phase 1: Pre-flight Validation (2-5 min)
  ├─ Environment check
  ├─ Node label validation
  ├─ Pod health check
  ├─ Cluster health (pxctl status)
  ├─ STC updateStrategy validation
  └─ Resource backup

Phase 2: Operator Upgrade (5-10 min)
  ├─ Approve install plans
  ├─ Wait for CSV ready
  └─ Verify cluster health

Phase 3: ConfigMap Update (1 min)
  ├─ Delete old px-versions
  └─ Create new px-versions

Phase 4: Component Updates (3 min)
  └─ Patch STC autoUpdateComponents

Phase 5: StorageCluster Update (1 min)
  └─ Update image field (TRIGGER)

Phase 6: Monitor Rolling Upgrade (20-40 min)
  ├─ Watch pod image changes
  ├─ Track upgrade progress
  ├─ Timeout detection
  └─ Optional: Impatient mode

Phase 7: Final Validation (2-5 min)
  ├─ All pods upgraded check
  ├─ Cluster health check
  └─ Version consistency

Phase 8: Report Generation (1 min)
  └─ Upgrade summary
```

## Common Issues

### Issue: "Version file not found"

**Solution**:
```bash
export PXVER=3.5.0
export KBVER=$(oc version | awk '/Server Version/ {print $3}')
curl -o roles/portworx_upgrade/files/versions/versions-${PXVER} \
  "https://install.portworx.com/$PXVER/version?kbver=$KBVER"
```

### Issue: "Module kubernetes.core.k8s not found"

**Solution**:
```bash
ansible-galaxy collection install kubernetes.core
pip install kubernetes PyYAML
```

### Issue: "STC updateStrategy invalid"

**Solution**:
The StorageCluster must have these settings:
```yaml
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      disruption:
        allow: true
```

Update manually if needed:
```bash
oc edit storagecluster -n portworx
```

### Issue: "Upgrade timeout"

**Check**:
```bash
# Check operator logs
oc logs -n portworx -l name=portworx-operator --tail=50

# Check StorageCluster
oc describe stc -n portworx

# Check pod status
oc get pods -n portworx -l name=portworx -o wide
```

## Next Steps

1. **Review full documentation**: `roles/portworx_upgrade/README.md`
2. **Customize variables**: Edit your playbook to tune timeouts, logging, etc.
3. **Test in dev**: Run preflight checks and dry runs first
4. **Production upgrade**: Schedule maintenance window and run full upgrade

## Support

- **Documentation**: `roles/portworx_upgrade/README.md`
- **Installation**: `roles/portworx_upgrade/INSTALL.md`
- **Examples**: `roles/portworx_upgrade/example-playbook.yml`
- **Version History**: `roles/portworx_upgrade/CHANGELOG.md`

## Key Configuration Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `portworx_target_version` | **REQUIRED** | Target version (e.g., "3.5.0") |
| `portworx_impatient_mode` | `false` | Enable batch storageless deletion |
| `portworx_detailed_logging` | `true` | Detailed progress logging |
| `portworx_skip_operator_upgrade` | `false` | Skip operator phase |

See `roles/portworx_upgrade/defaults/main.yml` for all 50+ variables.

## Verification

After installation, verify everything is ready:

```bash
# 1. Check role exists
ls -la roles/portworx_upgrade/

# 2. Check dependencies
ansible-galaxy collection list | grep kubernetes.core
python -c "import kubernetes; print('OK')"

# 3. Syntax check
ansible-playbook playbooks/px_upgrade.yml --syntax-check

# 4. Test preflight (no changes)
ansible-playbook playbooks/px_upgrade.yml \
  -e portworx_target_version=3.5.0 \
  --tags preflight \
  --check
```

All checks should pass before proceeding with actual upgrade.

---

**Ready to upgrade?** Run: `ansible-playbook playbooks/px_upgrade.yml -e portworx_target_version=3.5.0`
