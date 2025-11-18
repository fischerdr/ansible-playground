# Must-Gather Log Collection Role

## Overview

An Ansible role designed for Ansible Automation Platform execution environments that automates the collection of OpenShift must-gather diagnostic bundles and optionally uploads them directly to Red Hat support cases via SFTP.

## Features

- **Automated Collection**: Executes `oc adm must-gather` on designated OpenShift infrastructure nodes
- **Flexible Operation Modes**:
  - **Collect & Upload**: Collects diagnostics and uploads to Red Hat support case via SFTP
  - **Collect Only**: Collects and preserves archives locally without upload requirement
- **SFTP Upload**: Direct SFTP upload to Red Hat support with no file size limits
- **Proxy Support**: HTTP CONNECT proxy tunneling for restricted network environments
- **Archive Preservation**: Preserves archives with structured naming convention and retention policies
- **Comprehensive Logging**: Detailed SFTP operation logs for troubleshooting
- **Node Label Management**: Automatically selects and labels infrastructure nodes using Kubernetes API
- **Collision-Free**: Epoch timestamps prevent file/directory collisions on multiple runs

## Requirements

### Platform Requirements

- Ansible Core >= 2.18.4
- OpenShift Container Platform 4.x
- Ansible Automation Platform with execution environment support
- Python 3.11+ (for execution environment)

### Required Collections

- `ansible.builtin` (core modules)
- `kubernetes.core` (for OpenShift node operations and labeling)
- `community.hashi_vault` (optional, for HashiCorp Vault credential retrieval)

### External Dependencies

- OpenShift CLI (`oc`) binary in execution environment
- `sshpass`: For non-interactive SFTP authentication
- `nc` (netcat): For HTTP proxy tunneling (if proxy is used)
- Red Hat SFTP credentials (only required when uploading)
- Network access to `sftp.access.redhat.com` (only required when uploading, direct or via proxy)

## Installation

### Using Ansible Galaxy

```bash
ansible-galaxy install must_gather_log
```

### From Source

```bash
git clone <repository-url>
cd ansible-playground/roles/must_gather_log
```

## Basic Usage

### Mode 1: Collect and Upload to Red Hat Support

When you provide a Red Hat case number, the role collects diagnostics and uploads them via SFTP:

```yaml
- name: Collect and upload must-gather diagnostics
  hosts: localhost
  gather_facts: true

  vars:
    OC_BIN: "/usr/local/bin/oc"
    cluster_name: "prod-ocp-01"
    rh_case: "03123456"
    rh_sftp_user: "{{ vault_rh_sftp_user }}"
    rh_sftp_token: "{{ vault_rh_sftp_token }}"
    proxy_http: "http://proxy.example.com:8080"

  roles:
    - role: must_gather_log
```

### Mode 2: Collect Only (No Upload)

When you omit the Red Hat case number, the role only collects and preserves archives locally:

```yaml
- name: Collect must-gather diagnostics locally
  hosts: localhost
  gather_facts: true

  vars:
    OC_BIN: "/usr/local/bin/oc"
    cluster_name: "prod-ocp-01"
    # rh_case not provided - archives will be preserved locally

  roles:
    - role: must_gather_log
```

### Required Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OC_BIN` | Yes | Path to oc CLI binary | `/usr/local/bin/oc` |
| `cluster_name` | Recommended | Cluster identifier for archive naming | `prod-ocp-01` |
| `rh_case` | No* | Red Hat support case number | `03123456` |
| `rh_sftp_user` | No** | Red Hat Customer Portal username | Injected via AAP credential or Vault |
| `rh_sftp_token` | No** | Red Hat SFTP authentication token | Injected via AAP credential or Vault |
| `proxy_http` | No | HTTP proxy URL for SFTP | `http://proxy.example.com:8080` |

\* Required only when uploading to Red Hat support
\*\* Required only when uploading (`rh_case` is provided)

### Authentication (When Uploading)

Authentication is only required when `rh_case` is provided.

#### HashiCorp Vault Integration (Recommended)

```yaml
vars:
  rh_sftp_user: "{{ lookup('community.hashi_vault.hashi_vault', 'secret=secret/data/redhat:sftp_user') }}"
  rh_sftp_token: "{{ lookup('community.hashi_vault.hashi_vault', 'secret=secret/data/redhat:sftp_token') }}"
```

#### Generating SFTP Token

Red Hat SFTP tokens are time-limited and should be generated fresh for each upload:

- **Web UI**: https://access.redhat.com/support/secure-ftp
- **API**: `curl -X POST https://api.access.redhat.com/support/v2/sftp/token`

**Note**: If authentication is not provided when `rh_case` is set, the role will fail with a clear error message during validation.

## Common Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `must_gather_version` | `"4.14"` | OpenShift version for must-gather image |
| `skip_mustgather_deletion` | `false` | Preserve working directories after completion |
| `mustgather_output_dir` | `/tmp/must-gather-<epoch>` | Base directory for collections |
| `mustgather_archive_dir` | `/tmp/must-gather-archives` | Archive preservation directory |
| `mustgather_upload_logs` | `/tmp/must-gather-upload-logs` | SFTP upload logs directory |
| `mustgather_archive_retention_days` | `30` | Days to keep archived must-gather files (0 = forever) |
| `mustgather_archive_retention_count` | `10` | Maximum number of archives to keep (0 = unlimited) |
| `mustgather_label_selector` | `"must_gather"` | Label key for node selection |
| `mustgather_label_value` | `"true"` | Label value for node selection |
| `rh_sftp_host` | `"sftp.access.redhat.com"` | Red Hat SFTP server hostname |

## Configuration Examples

### Complete Example with Vault and Proxy

```yaml
- name: Production must-gather with upload
  hosts: localhost
  gather_facts: true

  vars:
    # Cluster configuration
    OC_BIN: "/usr/local/bin/oc"
    cluster_name: "prod-ocp-cluster-01"
    rh_case: "03456789"

    # HashiCorp Vault lookups
    vault_parameters: "url={{ vault_addr }} namespace={{ vault_namespace }}"
    rh_sftp_user: "{{ lookup('community.hashi_vault.hashi_vault', vault_parameters ~ ' secret=secret/data/redhat:sftp_user') }}"
    rh_sftp_token: "{{ lookup('community.hashi_vault.hashi_vault', vault_parameters ~ ' secret=secret/data/redhat:sftp_token') }}"
    proxy_http: "{{ lookup('community.hashi_vault.hashi_vault', vault_parameters ~ ' secret=secret/data/proxy:http_proxy') }}"

    # Optional overrides
    mustgather_archive_retention_days: 60
    skip_mustgather_deletion: false

  roles:
    - role: must_gather_log
```

### AAP Credential Injection

Create a custom credential type in Ansible Automation Platform:

**Input Configuration**:
```yaml
fields:
  - id: rh_sftp_user
    type: string
    label: Red Hat SFTP Username
  - id: rh_sftp_token
    type: string
    label: Red Hat SFTP Token
    secret: true
```

**Injector Configuration**:
```yaml
extra_vars:
  rh_sftp_user: '{{ rh_sftp_user }}'
  rh_sftp_token: '{{ rh_sftp_token }}'
```

## Operational Workflow

The role follows this workflow:

1. **Pre-Validation**:
   - Determines operation mode based on `rh_case` presence
   - Verifies required variables and oc binary
   - Validates SFTP credentials (only if uploading)

2. **Node Selection**:
   - Queries existing nodes with must-gather label using `kubernetes.core.k8s_info`
   - Selects or labels infrastructure node using `kubernetes.core.k8s` with merge patch
   - Idempotent labeling with Kubernetes API

3. **Directory Preparation**:
   - Creates clean working directories with epoch timestamps
   - Preserves existing archives with retention policy
   - Creates SFTP upload logging directory

4. **Collection Execution**:
   - Runs `oc adm must-gather` command with node selector
   - Validates collection output
   - Uses mirrored must-gather image if configured

5. **Archive Creation**:
   - Compresses collection into single tar.gz file
   - Calculates compression ratio
   - No file splitting required (SFTP has no size limit)

6. **Archive Handling** (conditional):
   - **If `rh_case` provided (Upload Mode)**:
     - Tests SFTP connectivity with logging
     - Uploads archive to Red Hat SFTP server
     - Files named: `CASEID_cluster-must-gather.tar.gz`
     - Files auto-attach to case within minutes
     - Detailed upload logs written to `mustgather_upload_logs`
   - **If `rh_case` not provided (Local Mode)**:
     - Displays archive location
     - Preserves archives locally with instructions for manual upload

7. **Cleanup**:
   - Removes temporary files and artifacts (unless `skip_mustgather_deletion: true`)
   - Applies retention policy to old archives

8. **Logging**:
   - Records operation status to `/var/log/ansible-must-gather.log`
   - Displays comprehensive operation summary
   - SFTP logs preserved in `mustgather_upload_logs` directory

## SFTP Upload Details

### Red Hat SFTP Requirements

Per Red Hat documentation (https://access.redhat.com/articles/5594481):

- **Server**: `sftp.access.redhat.com` (port 22 or 80)
- **Naming Convention**: Files must be named `CASEID_filename` (e.g., `02436811_must-gather.tar.gz`)
- **Upload Location**: Root directory on SFTP server
- **Auto-Attachment**: Files with correct naming auto-attach to cases within minutes
- **File Retention**: Successfully attached files retained for 3 years
- **Incorrect Files**: Incorrectly named files deleted after 30 days
- **File Size**: No file size limit

### SFTP Upload Logs

All SFTP operations are logged to `mustgather_upload_logs` directory:

- **Connectivity Test**: `sftp-connectivity-test-<epoch>.log`
- **Upload Operation**: `sftp-upload-<epoch>-part0.log`

Logs include:
- Timestamp and connection details
- Complete SFTP session output (stdout and stderr)
- Exit codes and status (SUCCESS/FAILED)

### Proxy Support

The role supports HTTP CONNECT proxy tunneling using netcat:

```yaml
vars:
  proxy_http: "http://proxy.example.com:8080"
```

This uses SSH `ProxyCommand` with netcat for HTTP tunneling:
```
-o "ProxyCommand=nc --proxy proxy.example.com:8080 --proxy-type http %h %p"
```

## Testing

### Quick SFTP Upload Test (Recommended)

Use the test playbook to validate SFTP upload functionality without full must-gather collection:

```bash
ansible-playbook playbooks/test-must-gather-upload.yml \
  -e "rh_case=12345678" \
  -e "cluster_name=test-cluster" \
  -e "sftp_user=your-username" \
  -e "sftp_token=your-sftp-token" \
  -e "proxy_http=http://proxy.example.com:8080"
```

This creates mock archives (configurable size, default 10MB) and tests only the SFTP upload functionality, dramatically reducing test time (~2 minutes vs 45-50 minutes).

### Full Integration Test

Test complete workflow including must-gather collection:

```bash
# With upload
ansible-playbook playbooks/must-gather-ocp-logs.yml \
  -e "cluster_name=test-cluster" \
  -e "rh_case=12345678"

# Without upload (collect only)
ansible-playbook playbooks/must-gather-ocp-logs.yml \
  -e "cluster_name=test-cluster"
```

## Troubleshooting

### SFTP Authentication Failures

**Symptoms**: Connection refused or authentication failed

**Debug Steps**:

1. Verify SFTP token is not expired (tokens are time-limited)
2. Generate fresh token: https://access.redhat.com/support/secure-ftp
3. Verify credentials are correctly populated from Vault
4. Check SFTP logs in `mustgather_upload_logs` directory
5. Test manual connection:
   ```bash
   sftp username@sftp.access.redhat.com
   ```

### Proxy Connection Issues

**Symptoms**: SFTP connectivity test fails with proxy-related errors

**Debug Steps**:

1. Verify `proxy_http` format: `http://proxy.example.com:8080`
2. Verify `nc` (netcat) is installed in execution environment
3. Test proxy connectivity:
   ```bash
   nc -v --proxy proxy.example.com:8080 --proxy-type http sftp.access.redhat.com 22
   ```
4. Check SFTP connectivity log for detailed error messages

### Upload Skipped When Expected

**Symptoms**: "Upload: Skipped (no Red Hat case provided)" but you provided `rh_case`

**Debug Steps**:

1. Check if `rh_case` variable is properly defined in playbook/inventory
2. Verify `rh_case` is not an empty string `""`
3. Review operation mode message in play output
4. Check validation block for SFTP credential errors

### Upload Failures

**Symptoms**: Upload status shows failures, archives preserved locally

**Debug Steps**:

1. Review SFTP upload logs in `mustgather_upload_logs` directory
2. Check `upload_status.results` for error details
3. Verify Red Hat case exists and is accessible
4. Verify network connectivity: `curl -I https://api.access.redhat.com`
5. Check proxy configuration if applicable
6. Review preserved archive path for manual upload

### File Naming Issues

**Symptoms**: File uploaded but not attached to case

**Debug Steps**:

1. Verify file follows Red Hat naming convention: `CASEID_filename`
2. Check upload logs for actual filename used
3. Verify case ID is correct and case is open
4. Files may take several minutes to auto-attach; check case attachments

### Multiple Run Collisions

**Symptoms**: Concerned about directory/file overwrites on multiple runs

**Verification**: All files and directories use epoch timestamps for uniqueness:
- Working directories: `must-gather-<epoch>/`
- Preserved archives: `cluster-case12345-<epoch>-must-gather.tar.gz`
- Upload logs: `sftp-upload-<epoch>-part0.log`

No collisions will occur on multiple runs.

## Archive Preservation and Retention

### Preservation Strategy

The role automatically preserves old archives before cleanup:

1. **Before each run**: Old `must-gather.tar.gz` files are copied to `mustgather_archive_dir`
2. **Naming**: `cluster-caseID-<epoch>-must-gather.tar.gz`
3. **Retention policies** applied after preservation

### Retention Policies

Two retention policies can be configured (both applied if set):

**Age-based retention**:
```yaml
mustgather_archive_retention_days: 30  # Keep archives for 30 days (0 = forever)
```

**Count-based retention**:
```yaml
mustgather_archive_retention_count: 10  # Keep last 10 archives (0 = unlimited)
```

Archives are deleted oldest-first when retention limits are exceeded.

## Security Considerations

### Credential Management

- **Never hardcode credentials** in playbook vars or group_vars
- **Always use HashiCorp Vault lookups** for sensitive data
- Configure Vault authentication via environment variables or AAP credentials
- Use appropriate Vault policies to limit secret access

### SFTP Token Security

- SFTP tokens are **single-use and time-limited**
- Generate fresh token for each upload session
- Tokens automatically expire after use or timeout
- Stored tokens should be rotated regularly in Vault

### Sensitive Data Handling

- All SFTP operations use `no_log: true` to prevent credential exposure
- Upload logs do not contain passwords or tokens
- Archives may contain cluster diagnostic data - handle appropriately

### Network Security

- SFTP connections use standard SSH encryption
- Proxy support uses HTTP CONNECT tunneling (encrypted after tunnel establishment)
- No unencrypted credential transmission

## Migration Notes

### From HTTP API Upload (v1.x)

This role has been refactored from HTTP API upload to SFTP upload:

**Key Changes**:
- No file size limits (was 1GB with HTTP API)
- No file splitting required
- Simplified authentication (SFTP token instead of API token/user/pass)
- Direct SFTP upload (no custom Python module required)
- Detailed operation logging

**Removed Components**:
- `redhat_upload.py` module (no longer used)
- HTTP API authentication variables
- File splitting logic
- Multi-part upload tracking

**Updated Variables**:
| Old Variable | New Variable | Notes |
|--------------|--------------|-------|
| `rh_api_token` | `rh_sftp_token` | Different token type |
| `rh_api_user` | `rh_sftp_user` | SFTP username |
| `rh_api_pass` | N/A | Not used with SFTP |
| N/A | `rh_sftp_host` | SFTP server hostname |

## Support

For issues or questions:

1. Review SFTP upload logs in `mustgather_upload_logs` directory
2. Check Red Hat SFTP documentation: https://access.redhat.com/articles/5594481
3. Verify SFTP token generation: https://access.redhat.com/support/secure-ftp

## License

Apache-2.0

## Author

Senior Systems Automation Engineer
