# Must-Gather Log Role - Condensed Implementation

## Overview

This role collects OpenShift must-gather diagnostics and uploads them to Red Hat support cases. The `main_condense.yml` implementation combines the best practices from both previous implementations with enhanced features for enterprise AAP environments.

## Purpose

Automate the collection, archiving, and upload of OpenShift must-gather diagnostic data to Red Hat support cases, with intelligent handling of large archives through automatic splitting and multi-part uploads.

## Requirements

### Ansible Version

- Ansible 2.9 or higher
- Ansible Automation Platform 2.x (for AAP/EE execution)

### Collections

- `kubernetes.core` >= 2.0.0 - For native Kubernetes API interaction
- `community.general` >= 3.0.0 - For advanced archive operations

### Execution Environment Dependencies

- `oc` CLI binary available in execution environment
- Python Kubernetes client library (`kubernetes` Python package)
- `tar` utility for archive creation
- `split` utility for large file handling
- `curl` for HTTP uploads (used by upload script)

### Variables

#### Required Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `rh_case` | string | Red Hat support case number | `"03123456"` |
| `OC_BIN` | string | Path to oc binary in EE | `"/usr/local/bin/oc"` |
| `cluster_name` | string | OpenShift cluster name | `"prod-ocp-01"` |

#### Required Environment Variables (AAP Credential Injection)

| Variable | Type | Description |
|----------|------|-------------|
| `RH_API_TOKEN` | string | Red Hat API bearer token (preferred) |
| **OR** | | |
| `RH_API_USER` | string | Red Hat portal username |
| `RH_API_PASS` | string | Red Hat portal password |

#### Optional Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `must_gather_version` | string | `"4.14"` | OpenShift version for must-gather image |
| `mustgather_label_selector` | string | `"must_gather"` | Label key for node selection |
| `mustgather_label_value` | string | `"true"` | Label value for node selection |
| `skip_mustgather_deletion` | boolean | `false` | Preserve directories after execution |
| `proxy_http` | string | `null` | HTTP proxy URL |
| `proxy_https` | string | `null` | HTTPS proxy URL |
| `proxy_no` | string | `null` | No proxy list |
| `WORK_DIR` | string | `"/tmp"` | Working directory base path |

#### Computed Variables (Do Not Override)

| Variable | Description |
|----------|-------------|
| `mustgather_output_dir` | Top-level output directory |
| `mustgather_collection_dir` | Subdirectory for must-gather data |
| `amex_mirror_endpoint` | Dynamic mirror based on cloud provider |

## Architecture

### Directory Structure

```
{{ WORK_DIR }}/must-gather-{{ timestamp }}/           # mustgather_output_dir
├── {{ cluster_name }}-{{ timestamp }}/                # mustgather_collection_dir
│   ├── quay-io-openshift-release-dev-.../            # must-gather output
│   │   ├── namespaces/
│   │   ├── cluster-scoped-resources/
│   │   └── ...
│   └── event-filter.html
├── must-gather.tar.gz                                 # Single archive (if < 900MB)
└── must-gather.tar.gz.part000                         # Split archives (if > 900MB)
    must-gather.tar.gz.part001
    must-gather.tar.gz.part002
```

### Execution Flow

1. **Pre-Execution Validation**
   - Validates required variables are defined
   - Verifies `oc` binary exists and is executable
   - Confirms Red Hat API authentication is configured

2. **Node Selection and Labeling** (Kubernetes Native)
   - Queries nodes with must-gather label using `kubernetes.core.k8s_info`
   - Validates single node or no nodes (prevents ambiguous selection)
   - Queries available infra nodes if no must-gather node exists
   - Labels selected node idempotently using merge patch
   - Reports node selection outcome

3. **Directory Preparation**
   - Removes existing output directory for clean state
   - Creates top-level output directory
   - Creates collection subdirectory

4. **Must-Gather Collection**
   - Executes `oc adm must-gather` with appropriate parameters
   - Uses specified image version or default
   - Applies node selector for targeted collection
   - Validates output was created
   - Reports collection statistics

5. **Archive Creation with Size Validation**
   - Calculates collection directory size
   - Determines if splitting is required (> 900MB threshold)
   - Creates single archive or split archives as appropriate
   - Validates archive files were created
   - Reports archive information

6. **Upload to Red Hat Support**
   - Creates temporary directory on controller
   - Fetches archive files to controller execution environment
   - Uploads each archive part with appropriate metadata
   - Uses `upload_to_redhat.sh` script with retry logic
   - Logs successful upload or preserves archives on failure

7. **Cleanup and Logging**
   - Removes controller temporary directory on success
   - Removes managed host directories (conditional)
   - Records operation to persistent log file
   - Displays comprehensive operation summary

## Key Features

### Idempotency

- **Node Labeling**: Checks for existing labels before applying, uses Kubernetes merge patch
- **Directory Management**: Always creates clean state by removing then recreating
- **Archive Creation**: Size-based logic ensures consistent behavior
- **Upload Handling**: Preserves archives on failure for manual intervention

### Large Archive Handling

- **Automatic Detection**: Calculates collection size before archiving
- **Intelligent Splitting**: Splits archives larger than 900MB (90% of 1GB API limit)
- **Multi-Part Upload**: Uploads each part with sequential numbering
- **Size Reporting**: Displays size information for operational awareness

### Error Handling

- **Block/Rescue/Always**: Every major operation wrapped in comprehensive error handling
- **Detailed Diagnostics**: Troubleshooting guidance in rescue blocks
- **Operational Logging**: Persistent log file tracks all operations
- **Archive Preservation**: Failed uploads preserve archives for manual retry

### Enterprise AAP Features

- **Execution Environment Isolation**: All operations account for EE constraints
- **Credential Injection**: Expects sensitive data from AAP credentials
- **Proxy Support**: Full HTTP/HTTPS proxy configuration
- **Operational Visibility**: Comprehensive logging and status reporting
- **Clean State Management**: Proper cleanup of temporary resources

## Usage Examples

### Basic Usage with Required Variables

```yaml
- name: Collect and upload must-gather
  hosts: openshift_masters[0]
  vars:
    OC_BIN: "/usr/local/bin/oc"
    cluster_name: "prod-ocp-01"
    rh_case: "03123456"
  tasks:
    - name: Include must-gather role
      ansible.builtin.include_role:
        name: must_gather_log
        tasks_from: main_condense
```

### Advanced Usage with Custom Configuration

```yaml
- name: Collect must-gather with custom settings
  hosts: openshift_masters[0]
  vars:
    OC_BIN: "/usr/local/bin/oc"
    cluster_name: "prod-ocp-01"
    rh_case: "03123456"
    must_gather_version: "4.12"
    skip_mustgather_deletion: true
    rh_upload_description: "Must-gather for production incident INC123456"
    proxy_https: "http://proxy.example.com:3128"
  tasks:
    - name: Include must-gather role
      ansible.builtin.include_role:
        name: must_gather_log
        tasks_from: main_condense
```

### AAP Job Template Configuration

```yaml
# Survey Variables
extra_vars:
  OC_BIN: "/usr/local/bin/oc"
  cluster_name: "{{ cluster_name }}"
  rh_case: "{{ rh_case }}"
  must_gather_version: "{{ openshift_version }}"

# Credentials (Type: Environment Variables)
# Inject RH_API_TOKEN or RH_API_USER/RH_API_PASS via custom credential type
```

## Tags

The role supports the following tags for selective execution:

| Tag | Description |
|-----|-------------|
| `validation` | Pre-execution validation tasks |
| `node_selection` | Node identification and labeling |
| `preparation` | Directory creation and preparation |
| `collection` | Must-gather execution |
| `archiving` | Archive creation and validation |
| `upload` | Red Hat support case upload |
| `cleanup` | Directory cleanup |
| `always` | Tasks that always run |

### Tag Usage Examples

```bash
# Run only validation
ansible-playbook playbook.yml --tags validation

# Skip upload (collect and archive only)
ansible-playbook playbook.yml --skip-tags upload

# Run collection and archiving only
ansible-playbook playbook.yml --tags collection,archiving
```

## Troubleshooting

### Common Issues

#### 1. No Suitable Node Found

**Symptom:** Error message "No suitable node found for must-gather collection"

**Resolution:**
- Ensure at least one node is labeled `tier=infra`
- Verify cluster authentication is valid
- Check `kubernetes.core` collection is installed in EE

#### 2. Archive Size Exceeds Limit

**Symptom:** Multiple `.part` files created

**Expected Behavior:** This is normal for large collections. All parts will be uploaded.

**Manual Upload (if needed):**
```bash
for part in must-gather.tar.gz.part*; do
  curl -H "Authorization: Bearer $RH_API_TOKEN" \
       -F "file=@$part" \
       -F "description=Part $part" \
       https://api.access.redhat.com/support/v1/cases/CASE_ID/attachments/
done
```

#### 3. Upload Failed

**Symptom:** Upload rescue block triggered, archives preserved

**Resolution:**
1. Verify Red Hat API authentication is valid
2. Check network connectivity to `api.access.redhat.com`
3. Confirm case number exists and is accessible
4. Review preserved archive path in error message
5. Manually upload using preserved archives

#### 4. Must-Gather Execution Failed

**Symptom:** "Must-gather collection failed" error

**Common Causes:**
- Invalid cluster authentication
- Must-gather image not accessible
- Insufficient node resources
- Network connectivity issues

**Resolution:**
1. Verify `oc` authentication: `oc whoami`
2. Test must-gather image access: `oc adm must-gather --dry-run`
3. Check node resources: `oc describe node <node_name>`
4. Verify image registry access

### Debug Mode

To increase verbosity for troubleshooting:

```bash
ansible-playbook playbook.yml -vvv
```

### Log Files

The role creates persistent operational logs:

**Controller Log:**
```
/var/log/ansible-must-gather.log
```

**Log Format:**
```
TIMESTAMP | Host: HOSTNAME | Cluster: CLUSTER | Status: SUCCESS|FAILED | Case: CASE_ID | Parts: N | Archive: UPLOADED|PRESERVED
```

## Security Considerations

### Credential Management

- **Never** hardcode credentials in playbooks or variable files
- Use AAP custom credential types for Red Hat API authentication
- Inject sensitive data via environment variables only
- Enable `no_log: true` on tasks handling credentials

### Archive Handling

- Archives may contain sensitive cluster information
- Controller temporary directories are cleaned up on success
- Failed uploads preserve archives for manual intervention
- Consider encrypting preserved archives

### Network Security

- Use HTTPS for all Red Hat API communication
- Configure proxy settings via environment variables
- Validate SSL certificates (do not disable `validate_certs`)

## Performance Considerations

### Collection Size

- Typical must-gather size: 100-500 MB
- Large clusters may produce > 1GB collections
- Automatic splitting handles large collections
- Consider targeted must-gather options for specific subsystems

### Execution Time

- Node selection: < 10 seconds
- Must-gather collection: 5-15 minutes (cluster-dependent)
- Archive creation: 1-5 minutes (size-dependent)
- Upload time: 2-10 minutes per part (network-dependent)
- Total typical execution: 10-30 minutes

### Resource Requirements

- Disk space: 2-3x collection size (original + archive)
- Memory: 500MB-1GB for archive operations
- Network: Bandwidth for upload to Red Hat API
- Controller storage: Temporary space for archive transfer

## Integration with AAP

### Custom Credential Type

Create a custom credential type for Red Hat API authentication:

**Input Configuration:**
```yaml
fields:
  - id: rh_api_token
    type: string
    label: Red Hat API Token
    secret: true
  - id: rh_api_user
    type: string
    label: Red Hat Portal Username
  - id: rh_api_pass
    type: string
    label: Red Hat Portal Password
    secret: true
```

**Injector Configuration:**
```yaml
env:
  RH_API_TOKEN: "{{ rh_api_token | default('') }}"
  RH_API_USER: "{{ rh_api_user | default('') }}"
  RH_API_PASS: "{{ rh_api_pass | default('') }}"
```

### Execution Environment

Ensure your EE includes:

```yaml
# execution-environment.yml
dependencies:
  python: requirements.txt
  galaxy: requirements.yml
```

```yaml
# requirements.yml
collections:
  - name: kubernetes.core
    version: ">=2.0.0"
  - name: community.general
    version: ">=3.0.0"
```

```txt
# requirements.txt
kubernetes>=12.0.0
openshift>=0.12.0
```

## Comparison with Previous Implementations

| Feature | main_orig.yml | main_aap.yml | main_gpt.yml | main_condense.yml |
|---------|--------------|--------------|--------------|------------------|
| **Module Approach** | Shell commands | Shell + modules | Kubernetes native | Kubernetes native |
| **Idempotency** | Partial | Partial | Advanced | Advanced |
| **Large Archive Handling** | None | None | None | **Automatic splitting** |
| **Error Handling** | Basic | Comprehensive | Comprehensive | Comprehensive |
| **Validation** | None | Extensive | Minimal | Extensive |
| **Logging** | None | Persistent log | Debug only | Persistent log |
| **Upload Retry** | None | Single attempt | 3 attempts | 3 attempts |
| **Documentation** | Minimal | Good | Minimal | Comprehensive |

## License

Proprietary - Internal Enterprise Use Only

## Author Information

Senior Systems Automation Engineering Team

## Changelog

### Version 1.0.0 (2025-11-05)

- Initial condensed implementation
- Kubernetes native node selection
- Automatic archive splitting for large collections
- Multi-part upload support
- Comprehensive error handling and logging
- Full AAP/EE integration
- Enhanced operational visibility

