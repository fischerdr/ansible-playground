# Must-Gather Log Collection Role

## Overview

An Ansible role designed for Ansible Automation Platform execution environments that automates the collection of OpenShift must-gather diagnostic bundles and optionally uploads them directly to Red Hat support cases via HTTP API.

**New in v2.0**: Upload to Red Hat support is now optional. The role can collect and preserve must-gather archives locally without requiring a Red Hat case number.

## Features

- **Automated Collection**: Executes `oc adm must-gather` on designated OpenShift infrastructure nodes
- **Flexible Operation Modes**:
  - **Collect & Upload**: Collects diagnostics and uploads to Red Hat support case
  - **Collect Only**: Collects and preserves archives locally without upload requirement
- **Optional Red Hat Upload**: Upload to Red Hat support cases via authenticated API (when `rh_case` is provided)
- **Large Archive Handling**: Automatically splits archives exceeding 900MB into multiple parts
- **Multi-Part Upload**: Handles sequential upload of split archive parts with retry logic
- **Python Module**: Uses native Python Ansible module (`redhat_upload`) for reliable uploads
- **Archive Preservation**: Preserves archives with structured naming convention
- **Comprehensive Logging**: Maintains operation logs and displays detailed execution summaries
- **Node Label Management**: Automatically selects and labels infrastructure nodes using Kubernetes API

## Requirements

### Platform Requirements

- Ansible Core >= 2.18.4
- OpenShift Container Platform 4.x
- Ansible Automation Platform with execution environment support
- Python 3.11+ (for module execution)

### Required Collections

- `ansible.builtin` (core modules)
- `kubernetes.core` (for OpenShift node operations and labeling)
- `community.hashi_vault` (optional, for HashiCorp Vault credential retrieval)

### External Dependencies

- OpenShift CLI (`oc`) binary in execution environment
- Red Hat API access token with case attachment permissions (only required when uploading)
- Network access to `api.access.redhat.com` (only required when uploading, direct or via proxy)

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

When you provide a Red Hat case number, the role collects diagnostics and uploads them:

```yaml
- name: Collect and upload must-gather diagnostics
  hosts: localhost
  gather_facts: true

  vars:
    OC_BIN: "/usr/local/bin/oc"
    cluster_name: "prod-ocp-01"
    rh_case: "03123456"
    rh_api_token: "{{ vault_rh_api_token }}"

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
| `rh_api_token` | No** | Red Hat API authentication token | Injected via AAP credential or Vault |

\* Required only when uploading to Red Hat support
\*\* Required only when uploading (`rh_case` is provided)

### Authentication Options (When Uploading)

Authentication is only required when `rh_case` is provided.

#### Option 1: API Token (Preferred)

```yaml
rh_api_token: "{{ vault_rh_api_token }}"
```

#### Option 2: Username/Password

```yaml
rh_api_user: "{{ vault_rh_api_user }}"
rh_api_pass: "{{ vault_rh_api_pass }}"
```

**Note**: If authentication is not provided when `rh_case` is set, the role will fail with a clear error message during validation.

## Module Usage

The role uses the `redhat_upload` module for uploading archive parts. The module is automatically available when the role is used.

### Module Parameters

The module accepts the following parameters (mapped from role variables):

| Module Parameter | Role Variable | Default | Description |
|-----------------|---------------|---------|-------------|
| `case_id` | `rh_case` | - | Red Hat support case number (required) |
| `archive_pattern` | Generated | - | Glob pattern for archive files (required) |
| `upload_description` | `rh_upload_description` | Generated | Upload description text (required) |
| `api_token` | `rh_api_token` | - | API authentication token |
| `api_user` | `rh_api_user` | - | API username |
| `api_pass` | `rh_api_pass` | - | API password |
| `proxy_http` | `proxy_http` | - | HTTP proxy URL |
| `proxy_https` | `proxy_https` | - | HTTPS proxy URL |
| `proxy_no` | `proxy_no` | - | Proxy bypass list |
| `max_retry_attempts` | `rh_upload_max_retries` | 3 | Maximum retry attempts per file |
| `fail_on_partial` | `rh_upload_fail_on_partial` | true | Fail if any part fails |

### Direct Module Usage

You can also use the module directly in playbooks:

```yaml
- name: Upload archive parts to Red Hat support case
  redhat_upload:
    case_id: "03123456"
    archive_pattern: "/tmp/archives/*.tar.gz*"
    upload_description: "must-gather for cluster-1"
    api_token: "{{ vault_rh_api_token }}"
    max_retry_attempts: 5
    fail_on_partial: true
  delegate_to: localhost
  register: upload_result
  no_log: true

- name: Display upload results
  ansible.builtin.debug:
    msg: "Uploaded {{ upload_result.success_count }}/{{ upload_result.total_parts }} parts"
```

## Common Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `must_gather_version` | `"4.14"` | OpenShift version for must-gather image |
| `skip_mustgather_deletion` | `false` | Preserve working directories after completion |
| `mustgather_output_dir` | `/tmp/must-gather-<epoch>` | Base directory for collections |
| `mustgather_archive_retention_days` | `30` | Days to keep archived must-gather files (0 = forever) |
| `mustgather_archive_retention_count` | `10` | Maximum number of archives to keep (0 = unlimited) |
| `mustgather_label_selector` | `"must_gather"` | Label key for node selection |
| `mustgather_label_value` | `"true"` | Label value for node selection |
| `rh_upload_max_retries` | `3` | Maximum retry attempts per archive part (upload mode only) |
| `rh_upload_fail_on_partial` | `true` | Fail playbook if any part fails (upload mode only) |

## Configuration Examples

### HashiCorp Vault Integration

```yaml
vars:
  vault_parameters: "url={{ vault_addr }} namespace={{ vault_namespace }}"
  rh_api_user: "{{ lookup('community.hashi_vault.hashi_vault', vault_parameters ~ ' secret=static_secrets/data/env/redhat')['user'] }}"
  rh_api_pass: "{{ lookup('community.hashi_vault.hashi_vault', vault_parameters ~ ' secret=static_secrets/data/env/redhat')['password'] }}"
  proxy_http: "{{ lookup('community.hashi_vault.hashi_vault', vault_parameters ~ ' secret=static_secrets/data/proxy')['http_proxy'] }}"
```

### AAP Credential Injection

Create a custom credential type in AAP:

```yaml
fields:
  - id: rh_api_token
    type: string
    label: Red Hat API Token
    secret: true
```

Configure injector:

```yaml
env:
  RH_API_TOKEN: '{{ rh_api_token }}'
```

### Proxy Configuration

```yaml
vars:
  proxy_http: "http://proxy.example.com:8080"
  proxy_https: "https://proxy.example.com:8080"
  proxy_no: "localhost,127.0.0.1,api.access.redhat.com"
```

## Upload Module Return Values

The `redhat_upload` module returns the following structure:

```yaml
status: "success" | "failed" | "partial"
case_id: "03123456"
total_parts: 3
success_count: 3
failure_count: 0
results:
  - part: 1
    file: "must-gather.tar.gz.part000"
    status: "success"
    attempts: 1
    http_code: 201
  - part: 2
    file: "must-gather.tar.gz.part001"
    status: "success"
    attempts: 1
    http_code: 201
```

## Operational Workflow

The role follows this workflow:

1. **Pre-Validation**:
   - Determines operation mode based on `rh_case` presence
   - Verifies required variables and oc binary
   - Validates authentication credentials (only if uploading)

2. **Node Selection**:
   - Queries existing nodes with must-gather label using `kubernetes.core.k8s_info`
   - Selects or labels infrastructure node using `kubernetes.core.k8s` with merge patch
   - Uses Jinja2 dictionary literal syntax for dynamic label construction

3. **Directory Preparation**:
   - Creates clean working directories
   - Preserves existing archives with retention policy

4. **Collection Execution**:
   - Runs `oc adm must-gather` command with node selector
   - Validates collection output

5. **Archive Creation**:
   - Compresses collection into tar.gz
   - Automatically splits if > 900MB

6. **Archive Handling** (conditional):
   - **If `rh_case` provided (Upload Mode)**:
     - Fetches archive to execution environment
     - Uploads archive parts to Red Hat support case via `redhat_upload` module
     - Preserves failed uploads with detailed error reporting
   - **If `rh_case` not provided (Local Mode)**:
     - Displays archive location
     - Preserves archives locally with instructions for manual upload

7. **Cleanup**:
   - Removes temporary files and artifacts
   - Applies retention policy to old archives

8. **Logging**:
   - Records operation status to persistent log
   - Displays comprehensive operation summary

## Automatic Archive Splitting

When must-gather collections exceed 900MB:

- Automatically splits into 900MB parts
- Generates sequential part files: `must-gather.tar.gz.part000`, `must-gather.tar.gz.part001`, etc.
- Uploads all parts with descriptive identifiers via `redhat_upload` module
- Maintains archive integrity across splits

## Migration from Bash Script

If you were previously using the Bash script (`upload_to_redhat_condense.sh`), the Python module provides equivalent functionality with improved integration:

- **Better Error Handling**: Native Ansible error handling and reporting
- **Improved Security**: Sensitive parameters automatically marked with `no_log`
- **Type Validation**: Built-in parameter validation
- **Consistent Results**: Structured return values matching Ansible conventions

See `redhat_upload_module_migration_plan.md` for detailed migration information.

## Testing

### Quick Upload Test (Recommended)

Use the test playbook to validate upload functionality without full must-gather collection (~2 minutes vs 45-50 minutes):

```bash
ansible-playbook playbooks/test-must-gather-upload.yml \
  -e "rh_case=12345678" \
  -e "cluster_name=test-cluster" \
  -e "cluster_user=your-env"
```

This creates mock archives and tests only the `redhat_upload` module, dramatically reducing test time.

### Module Syntax Validation

```bash
python3.11 -m py_compile roles/must_gather_log/library/redhat_upload.py
```

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

### Module Not Found

**Symptoms**: `module 'redhat_upload' not found` or `couldn't resolve module/action 'redhat_upload'`

**Solutions**:

1. When using role: Module should be automatically available
2. In standalone playbooks: Set `ANSIBLE_LIBRARY` environment variable:

   ```yaml
   environment:
     ANSIBLE_LIBRARY: "{{ playbook_dir }}/../roles/must_gather_log/library"
   ```

3. Verify role's `library/` directory exists and contains `redhat_upload.py`

### Jinja2 Template Variable Not Evaluated

**Symptoms**: Kubernetes API error showing literal `{{ variable_name }}` instead of value

**Solution**: This issue has been fixed in v2.0 using Jinja2 dictionary literal syntax. Ensure you're using the latest version.

### Authentication Failures

**Symptoms**: HTTP 401 or 403 errors during upload

**Debug Steps**:

1. Verify `rh_case` is provided (check operation mode message)
2. Verify Red Hat API token/credentials are valid
3. Check token has not expired
4. Verify case access permissions for service account
5. Test credentials manually: `curl -u "user:pass" https://api.access.redhat.com/rs/cases/YOUR_CASE`

### Upload Skipped When Expected

**Symptoms**: "Upload: Skipped (no Red Hat case provided)" but you provided `rh_case`

**Debug Steps**:

1. Check if `rh_case` variable is properly defined in your playbook/inventory
2. Verify `rh_case` is not an empty string `""`
3. Review operation mode message in play output
4. Check task output for validation errors

### Upload Failures

**Symptoms**: Upload status shows failures, archives preserved locally

**Debug Steps**:

1. Check `upload_status.results` for per-part error details
2. Review HTTP status codes returned
3. Verify network connectivity: `curl -I https://api.access.redhat.com`
4. Check proxy configuration if applicable
5. Review preserved archive path for manual upload
6. Increase retry attempts: `rh_upload_max_retries: 5`

## Support

For issues or questions:

1. Check `TESTING_CHECKLIST.md` for common scenarios
2. Review `redhat_upload_module_migration_plan.md` for migration guidance
3. Check module documentation: `ansible-doc redhat_upload` (when module is in path)

## License

Apache-2.0

## Author

Senior Systems Automation Engineer
