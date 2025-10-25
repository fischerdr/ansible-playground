# defrag_etcd_db

## Purpose

Defragment etcd databases in OpenShift clusters to reclaim disk space and optimize performance. This role is designed for execution through Ansible Automation Platform (AAP) using Execution Environments (EEs).

## Requirements

### Platform Requirements

- Ansible >= 2.15
- Ansible Automation Platform (AAP) 2.x or later
- Execution Environment with required dependencies

### Collection Dependencies

- `kubernetes.core` >= 2.4.0

### External Dependencies

- OpenShift CLI (`oc`) available in Execution Environment
- Valid kubeconfig with cluster-admin or etcd operator privileges
- Target: OpenShift 4.x clusters

## Role Variables

### Required Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `cluster_name` | string | OpenShift cluster identifier for operational context | `prod-ocp-01` |
| `oc_binary` | string | Path to oc binary in EE | `/usr/bin/oc` |

### Optional Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `kubeconfig` | string | "" | Path to kubeconfig file (typically injected via AAP credential) |
| `cmd_timeout` | integer | 240 | Command timeout in seconds for etcdctl operations |
| `db_size_diff_baseline` | integer | 20 | Defragmentation threshold percentage (skips defrag if below) |
| `force` | boolean | false | Force defragmentation regardless of threshold |
| `skip_compact` | boolean | false | Skip compaction step before defragmentation |
| `pause_event_seconds` | integer | 10 | Pause duration after event cleanup (seconds) |
| `member_list` | string | "" | Comma-separated pod names (empty for auto-discovery). **Note**: When provided, assessment and preparation steps are skipped, defragmentation proceeds directly on specified pods. |
| `wait_between_members` | integer | 60 | Wait time between defragmentation of individual members |
| `max_retry_multiplier` | integer | 2 | Multiplier for maximum retry attempts |
| `debug_mode` | boolean | false | Enable verbose module logging |
| `working_dir` | string | "" | Deprecated - not used in AAP-compliant version |

## Dependencies

- **Common role** (optional) - Include common setup tasks if available
- **AAP Credential** - OpenShift kubeconfig credential type

## Architecture

### Execution Flow

1. **Variable Validation** - Validates required variables are defined
2. **Pod Discovery** - Discovers etcd pods via kubernetes.core.k8s_info
3. **Leader Detection** - Identifies etcd cluster leader and non-leader members
4. **Pre-defrag Assessment** - Evaluates database size utilization using leader pod
5. **Threshold Check** - Determines if defragmentation is required
6. **Preparation** - Cleans events and compacts database using non-leader member
7. **Health Check** - Validates etcd cluster health
8. **Defragmentation** - Executes leader-aware defragmentation via custom module
9. **Post-defrag Verification** - Confirms cluster health after operation

### Leader Detection and Non-Leader Compaction

The role implements intelligent leader detection to minimize cluster disruption:

#### Leader Detection Process

1. **Query Endpoint Status** - Retrieves endpoint status from any etcd pod to identify leader ID
2. **Query Member List** - Maps leader ID to actual pod name
3. **Identify Leader Pod** - Determines which discovered pod is the current leader
4. **Select Non-Leader Member** - Identifies a non-leader member for compaction operations

#### Why Non-Leader for Compaction

**Best Practice**: Compaction and event cleanup operations are executed on non-leader members to:

- **Minimize Leader Disruption** - Keeps the leader focused on consensus and write operations
- **Reduce Cluster Impact** - Prevents potential leader election if operations cause timeouts
- **Optimize Performance** - Distributes operational load across cluster members
- **Maintain Availability** - Ensures leader remains available for critical cluster operations

The role uses:
- **Leader pod** for assessment queries (endpoint status for size analysis)
- **Non-leader member** for event cleanup and compaction operations
- **Any pod** (preferring leader) for health checks

### Leader-Aware Defragmentation

The custom `defrag_etcd` module implements intelligent leader detection during defragmentation:

- **Defragments non-leader members first** - Minimizes risk to cluster consensus
- **Defragments leader last** - Ensures cluster stability throughout operation
- **Implements bounded retry logic** - Handles transient failures gracefully
- **Waits between operations** - Allows cluster stabilization between member defragmentation
- **Automatic leader re-detection** - Handles leader changes during operation

## Example Usage

### Basic Playbook

```yaml
---
- name: Defragment etcd database
  hosts: localhost
  gather_facts: false
  
  roles:
    - role: defrag_etcd_db
      vars:
        cluster_name: "prod-ocp-01"
        oc_binary: "/usr/bin/oc"
        kubeconfig: "{{ lookup('env', 'K8S_AUTH_KUBECONFIG') }}"
```

### Force Defragmentation

```yaml
---
- name: Force etcd defragmentation
  hosts: localhost
  gather_facts: false
  
  roles:
    - role: defrag_etcd_db
      vars:
        cluster_name: "prod-ocp-01"
        oc_binary: "/usr/bin/oc"
        kubeconfig: "{{ lookup('env', 'K8S_AUTH_KUBECONFIG') }}"
        force: true
        debug_mode: true
```

### Target Specific Pods

```yaml
---
- name: Defragment specific etcd members
  hosts: localhost
  gather_facts: false
  
  roles:
    - role: defrag_etcd_db
      vars:
        cluster_name: "prod-ocp-01"
        oc_binary: "/usr/bin/oc"
        kubeconfig: "{{ lookup('env', 'K8S_AUTH_KUBECONFIG') }}"
        member_list: "etcd-0,etcd-1,etcd-2"
```

**Important**: When `member_list` is provided, the role:
- ✅ **Performs leader detection** on specified pods
- ✅ **Executes defragmentation** in leader-aware order
- ✅ **Runs health checks** before and after
- ❌ **Skips assessment** (no database size threshold check)
- ❌ **Skips preparation** (no event cleanup or compaction)

This allows targeted defragmentation without prerequisites when you know specific pods require maintenance.

## AAP Job Template Configuration

### Credentials

Configure the following credentials in AAP:

1. **OpenShift Credential**
   - Credential Type: OpenShift or Bearer Token
   - Injects kubeconfig into EE environment

### Extra Variables

```yaml
cluster_name: "prod-ocp-01"
oc_binary: "/usr/bin/oc"
db_size_diff_baseline: 20
force: false
debug_mode: false
```

### Job Settings

- **Job Type**: Run
- **Inventory**: localhost
- **Limit**: localhost
- **Verbosity**: 1 (Verbose) or 2 (Debug) for detailed output
- **Execution Environment**: Custom EE with kubernetes.core collection and oc binary

## Execution Environment Requirements

The EE must include the following components:

### Required Binaries

- OpenShift CLI (`oc`) - typically installed at `/usr/bin/oc`

### Required Collections

- `kubernetes.core` >= 2.4.0

### Python Requirements

- Python 3.9 or later
- `kubernetes` Python library
- `openshift` Python library

### Sample EE Definition

```yaml
---
version: 3

images:
  base_image:
    name: registry.redhat.io/ansible-automation-platform-24/ee-minimal-rhel9:latest

dependencies:
  galaxy: requirements.yml
  python: requirements.txt
  system: bindep.txt

additional_build_steps:
  append_final:
    - RUN microdnf install -y openshift-clients
```

## Tags

The role implements the following tags for granular execution control:

- `validation` - Variable validation tasks
- `discovery` - Pod discovery tasks
- `leader_detection` - Leader and non-leader member identification
- `assessment` - Pre-defrag database analysis
- `preparation` - Pre-defrag preparation tasks (event cleanup, compaction)
- `health_check` - Health verification tasks (pre and post defrag)
- `pre_defrag` - Pre-defragmentation health check
- `post_defrag` - Post-defragmentation health check
- `defragmentation` - Defragmentation operation
- `critical` - Critical operations requiring review
- `completion` - Completion message
- `always` - Tasks that always run

### Tag Usage Examples

```bash
# Run only validation, discovery, and leader detection
ansible-playbook playbook.yml --tags "validation,discovery,leader_detection"

# Skip health checks
ansible-playbook playbook.yml --skip-tags "health_check"

# Run only defragmentation (assumes preparation complete)
ansible-playbook playbook.yml --tags "defragmentation"

# Run full workflow excluding leader detection (use when member_list provided)
ansible-playbook playbook.yml --skip-tags "leader_detection"
```

## Testing

### Check Mode

Execute in check mode to validate configuration without making changes:

```bash
ansible-playbook playbook.yml --check --tags validation,discovery
```

### Dry Run

Use the assessment tag to evaluate whether defragmentation is needed:

```bash
ansible-playbook playbook.yml --tags assessment
```

### Debug Mode

Enable debug mode for troubleshooting:

```yaml
debug_mode: true
```

## Operational Considerations

### Pre-requisites

1. Ensure etcd cluster is healthy before running defragmentation
2. Verify sufficient disk space on etcd nodes
3. Schedule defragmentation during maintenance windows when possible
4. Confirm backup procedures are in place

### Performance Impact

- Defragmentation temporarily increases CPU and I/O usage
- Each member defragmentation may take 30-60 seconds
- Total operation time: `(member_count * wait_between_members) + defrag_time`
- Example: 3-member cluster with 60s wait = approximately 3-5 minutes total

### Monitoring

Monitor the following metrics during defragmentation:

- etcd CPU usage
- etcd memory usage
- Disk I/O
- etcd leader elections (should remain stable)
- Cluster health via `etcdctl endpoint health`

### Troubleshooting

#### Defragmentation Fails

1. Check etcd cluster health: `oc exec -n openshift-etcd <pod> -- etcdctl endpoint health`
2. Review AAP job logs for detailed error messages
3. Enable debug mode: `debug_mode: true`
4. Verify network connectivity to etcd endpoints
5. Confirm sufficient disk space on etcd nodes

#### Threshold Not Met

If defragmentation is skipped due to threshold:

```
Defragmentation not required: utilization 15% below threshold 20%
```

Options:
- Adjust `db_size_diff_baseline` to lower threshold
- Set `force: true` to bypass threshold check

#### Timeout Errors

Increase timeout values if operations fail with timeout errors:

```yaml
cmd_timeout: 300  # Increase from default 240
```

## Security Considerations

### Credentials Management

- Never hardcode credentials in playbooks
- Use AAP credential injection for kubeconfig
- Leverage Vault-based secret management for sensitive data
- Enable `no_log` for tasks handling sensitive information (already implemented in custom module)

### RBAC Requirements

The service account or user must have permissions to:

- List pods in `openshift-etcd` namespace
- Execute commands in etcd pods
- Read pod status and metadata

### Audit Trail

All operations are logged through:

- AAP job execution logs
- Ansible task output with timestamps
- Custom module debug logging (when enabled)

## Maintenance

### Regular Tasks

1. Review and update `db_size_diff_baseline` based on cluster patterns
2. Monitor defragmentation frequency and adjust scheduling
3. Update role dependencies when new versions are available
4. Review and clean up old job execution logs in AAP

### Version Updates

When updating the role:

1. Review CHANGELOG for breaking changes
2. Test in non-production environment first
3. Update EE with latest dependencies
4. Validate with `--check` mode before production deployment

## Support

For issues or questions:

1. Review AAP job output logs
2. Enable debug mode for detailed information
3. Consult OpenShift etcd operator documentation
4. Contact Enterprise Automation Team

## Author

Enterprise Automation Team

## License

Apache-2.0

## Changelog

### Version 2.0.0 (Current)

- Complete rewrite for AAP/EE compatibility
- Replaced shell commands with kubernetes.core modules where possible
- Implemented leader-aware defragmentation
- Added comprehensive error handling with block/rescue/always
- Introduced FQCN for all modules
- Added extensive variable documentation
- Implemented tag-based execution control
- Enhanced health checking procedures
- Removed hardcoded paths and working_dir dependency

### Version 1.0.0 (Legacy)

- Initial implementation with shell-based commands
- Hardcoded paths incompatible with EE isolation
- Limited error handling
- Deprecated - not compatible with AAP/EE

