# Portworx Upgrade Role

Production-ready Ansible role for automated Portworx cluster upgrades on OpenShift 4.18+.

## Features

- **Operator-Controlled Rolling Upgrades**: Monitors operator-managed rolling upgrades without direct pod control
- **Comprehensive Preflight Validation**: Environment, nodes, pods, cluster status, and StorageCluster configuration checks
- **Dual Timeout Strategy**: 35-minute global inactivity timeout + 25-minute per-pod timeout
- **Impatient Mode**: Accelerated storageless node upgrades via batch deletion (5-7 pods at a time)
- **Safety-First Design**: Storage node validation before storageless pod acceleration
- **Detailed Monitoring**: Real-time pod image tracking via Kubernetes API
- **Complete Reporting**: Upgrade summary with timing, pod counts, and validation results

## Requirements

- Ansible Core 2.12+
- Python 3.9+
- Collections:
  - `kubernetes.core` >= 2.3.0 (required for StorageCluster CRD operations)
  - `ansible.builtin`
- OpenShift CLI (`oc`) or kubectl access
- Cluster admin permissions on target OpenShift cluster

## Quick Start

### 1. Install the Role

```bash
ansible-galaxy role install portworx_upgrade
```

Or from this archive:

```bash
tar -xzf portworx-upgrade-role-1.0.0.tar.gz
cp -r portworx-upgrade-role /path/to/your/roles/portworx_upgrade
```

### 2. Install Collections

```bash
ansible-galaxy collection install -r requirements.yml
```

### 3. Create Playbook

```yaml
---
- name: Upgrade Portworx cluster
  hosts: localhost
  gather_facts: true
  vars:
    portworx_target_version: "3.5.0"
    portworx_cluster_name: "prod-cluster"
    portworx_impatient_mode: false
  roles:
    - role: portworx_upgrade
```

### 4. Run Upgrade

```bash
# Preflight check only
ansible-playbook upgrade.yml --tags preflight

# Full upgrade
ansible-playbook upgrade.yml

# With impatient mode
ansible-playbook upgrade.yml -e portworx_impatient_mode=true
```

## Role Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `portworx_target_version` | Target Portworx OCI version | `"3.5.0"` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `portworx_cluster_name` | `""` | Cluster name for reporting |
| `portworx_namespace` | `"portworx"` | Portworx namespace |
| `portworx_impatient_mode` | `false` | Enable accelerated storageless node upgrades |
| `portworx_impatient_batch_size` | `5` | Storageless pods to delete per batch (3-10) |
| `portworx_pod_upgrade_timeout` | `1500` | Per-pod upgrade timeout (25 minutes) |
| `portworx_global_inactivity_timeout` | `2100` | Global inactivity timeout (35 minutes) |
| `portworx_skip_operator_upgrade` | `false` | Skip operator upgrade phase |
| `portworx_detailed_logging` | `true` | Enable detailed debug logging |
| `portworx_work_dir` | `/tmp/ansible-workdir` | Base directory for reports and logs |

See `defaults/main.yml` for complete variable list.

## Execution Phases

The role executes in 8 sequential phases:

1. **Preflight Validation** (tags: `preflight`, `validation`)
   - Environment validation (kubeconfig, namespace, permissions)
   - Node validation (Ready status, resource capacity)
   - Pod validation (Running status, version detection)
   - Cluster status validation (PX operational, KVDB health)
   - StorageCluster configuration validation (updateStrategy)
   - Resource backup (StorageCluster, ConfigMap, Subscription) - when `portworx_backup_resources: true`

2. **Upgrade Operator** (tags: `upgrade`, `operator`)
   - Updates operator subscription channel
   - Approves install plan if manual approval required

3. **Update ConfigMap** (tags: `upgrade`, `configmap`)
   - Updates px-versions ConfigMap with target version

4. **Update Components** (tags: `upgrade`, `components`)
   - Patches StorageCluster autoUpdateComponents

5. **Trigger StorageCluster Upgrade** (tags: `upgrade`, `storagecluster`)
   - Updates StorageCluster image to target version

6. **Monitor Automatic Rolling Upgrade** (tag: `monitor`)
   - Tracks pod image changes via Kubernetes API
   - Detects stuck upgrades using dual timeout strategy
   - Executes impatient mode for storageless nodes (if enabled)

7. **Final Validation** (tags: `validate`, `final`)
   - Final pod validation
   - Cluster health verification
   - Version consistency check

8. **Generate Reports** (tag: `report`)
   - Generates upgrade summary report
   - Creates timestamped report files

## Tag-Based Execution

Run specific phases using tags:

```bash
# Preflight checks only (includes resource backup if portworx_backup_resources=true)
ansible-playbook upgrade.yml --tags preflight

# All upgrade phases (operator, configmap, components, storagecluster)
ansible-playbook upgrade.yml --tags upgrade

# Specific upgrade phases
ansible-playbook upgrade.yml --tags operator      # Operator upgrade only
ansible-playbook upgrade.yml --tags configmap     # ConfigMap update only
ansible-playbook upgrade.yml --tags components    # Component update only
ansible-playbook upgrade.yml --tags storagecluster # StorageCluster trigger only

# Monitoring only (assumes upgrade already triggered)
ansible-playbook upgrade.yml --tags monitor

# Final validation only
ansible-playbook upgrade.yml --tags validate

# Report generation only
ansible-playbook upgrade.yml --tags report

# Combined examples
ansible-playbook upgrade.yml --tags preflight,upgrade  # Preflight + all upgrade phases
ansible-playbook upgrade.yml --tags validate,report    # Validation + reporting
```

**Notes**:

- Resource backup is part of the preflight phase and runs when `portworx_backup_resources` is set to `true` (default)
- Multiple tags can be combined using comma-separated values
- The `upgrade` tag runs all upgrade phases (operator, configmap, components, storagecluster)
- Granular tags (operator, configmap, components, storagecluster) allow selective execution of specific upgrade steps

## Impatient Mode

Accelerates storageless node upgrades by deleting pods in batches instead of waiting for operator-controlled rolling updates.

**Safety Guarantees**:
- Only affects storageless nodes (never storage nodes)
- Validates storage nodes upgraded before acceleration
- Batch size configurable (5-7 recommended)
- Safety checks between batches
- Automatic fallback to normal mode if issues detected

**Usage**:

```yaml
vars:
  portworx_impatient_mode: true
  portworx_impatient_batch_size: 7
```

## AAP/AWX Integration

This role includes complete AAP/AWX import configurations in the `aap_import/` directory.

### Quick Import

```bash
cd aap_import
./import_to_aap.sh
```

See `aap_import/README.md` for detailed import instructions, including:
- Automated import script usage
- Manual AWX CLI commands
- Web UI import steps
- Job template configurations
- Workflow with approval gates

## Version Files

The role includes pre-configured version mappings in `versions/`:

- `versions-3.4.0.1/`: Example version configuration
- `README.md`: Instructions for adding new versions

Each version directory contains:
- `portworx_versions.yml`: Component version mappings
- `metadata.yml`: Version metadata and compatibility info

## Monitoring and Timeouts

### Dual Timeout Strategy

1. **Global Inactivity Timeout** (35 minutes default)
   - Triggers if no pod state changes detected
   - Tracks "activity" as any pod in Terminating/Pending/ContainerCreating/new-but-not-ready states

2. **Per-Pod Timeout** (25 minutes default)
   - Triggers if individual pod stuck in non-running state
   - Separate timer for each pod

### Activity Detection

The role considers these states as "activity" (reset inactivity timer):
- Pod in Terminating state
- Pod in Pending state
- Pod in ContainerCreating state
- Pod Running but not Ready with new image

## Troubleshooting

### Preflight Validation Failures

```bash
# Check cluster status
oc get storagecluster -n portworx
oc get pods -n portworx

# Verify operator
oc get csv -n portworx
```

### Stuck Upgrade Detection

If upgrade appears stuck:

1. Check pod events: `oc describe pod <pod-name> -n portworx`
2. Check operator logs: `oc logs -n portworx deployment/portworx-operator`
3. Verify StorageCluster status: `oc get storagecluster -n portworx -o yaml`

### Impatient Mode Issues

If impatient mode fails:

1. Verify storage nodes upgraded: Check pod images manually
2. Review batch size: Reduce to 3-5 for large clusters
3. Check safety validation: Review role output for safety check failures

## Examples

### Basic Upgrade

```yaml
---
- name: Upgrade Portworx to 3.5.0
  hosts: localhost
  vars:
    portworx_target_version: "3.5.0"
  roles:
    - portworx_upgrade
```

### Upgrade with Impatient Mode

```yaml
---
- name: Fast Portworx upgrade
  hosts: localhost
  vars:
    portworx_target_version: "3.5.0"
    portworx_impatient_mode: true
    portworx_impatient_batch_size: 7
  roles:
    - portworx_upgrade
```

### Skip Operator Upgrade

```yaml
---
- name: Upgrade Portworx (operator pre-upgraded)
  hosts: localhost
  vars:
    portworx_target_version: "3.5.0"
    portworx_skip_operator_upgrade: true
  roles:
    - portworx_upgrade
```

## Architecture

### Key Design Decisions

1. **Monitor, Don't Control**: Role monitors operator-controlled rolling upgrades instead of managing pod lifecycle directly
2. **Kubernetes API First**: Uses k8s_info to track pod image changes, not pxctl polling
3. **Inline Shell Processing**: Returns only results from pxctl commands to handle large clusters (500+ nodes)
4. **Activity-Based Timeouts**: Tracks any state change as activity, not just completion
5. **Safety Over Speed**: Multiple validation layers before allowing impatient mode acceleration

### Custom Modules

- `library/pxctl_status.py`: Executes pxctl commands with auth token handling and structured output

## License

Apache License 2.0

## Author

Enterprise Platform Automation Team

## Support

For issues and feature requests:
1. Check `aap_import/README.md` for AAP-specific troubleshooting
2. Review role execution logs for detailed error messages
3. Verify cluster meets requirements in preflight validation output
