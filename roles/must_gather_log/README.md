# Must-Gather Log Collection Role

## Overview

An Ansible role designed for Ansible Automation Platform execution environments that automates the collection of OpenShift must-gather diagnostic bundles and uploads them directly to Red Hat support cases via HTTP API.

## Features

- **Automated Collection**: Executes `oc adm must-gather` on designated OpenShift infrastructure nodes
- **Direct Upload**: Uploads diagnostic archives to Red Hat support cases via authenticated API
- **Large Archive Handling**: Automatically splits archives exceeding 900MB into multiple parts
- **Multi-Part Upload**: Handles sequential upload of split archive parts with retry logic
- **Python Module**: Uses native Python Ansible module (`redhat_upload`) for reliable uploads
- **Archive Preservation**: Optionally preserves archives on upload failure with structured naming convention
- **Comprehensive Logging**: Maintains operation logs and displays detailed execution summaries

## Requirements

### Platform Requirements

- Ansible >= 2.15
- OpenShift Container Platform 4.x
- Ansible Automation Platform with execution environment support
- Python 3.9+ (for module execution)

### Required Collections

- `ansible.builtin` (core modules)
- `kubernetes.core` (for OpenShift node operations)

### External Dependencies

- OpenShift CLI (`oc`) binary in execution environment
- Red Hat API access token with case attachment permissions
- Network access to `api.access.redhat.com` (direct or via proxy)

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

### Minimum Configuration

```yaml
- name: Collect and upload must-gather diagnostics
  hosts: openshift_masters[0]
  gather_facts: true
  
  vars:
    OC_BIN: "/usr/local/bin/oc"
    cluster_name: "prod-ocp-01"
    rh_case: "03123456"
    rh_api_token: "{{ vault_rh_api_token }}"
    
  roles:
    - role: must_gather_log
      tasks_from: main_condense
```

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OC_BIN` | Path to oc CLI binary | `/usr/local/bin/oc` |
| `cluster_name` | Cluster identifier for archive naming | `prod-ocp-01` |
| `rh_case` | Red Hat support case number | `03123456` |
| `rh_api_token` | Red Hat API authentication token | Injected via AAP credential or Vault |

### Authentication Options

#### Option 1: API Token (Preferred)

```yaml
rh_api_token: "{{ vault_rh_api_token }}"
```

#### Option 2: Username/Password

```yaml
rh_api_user: "{{ vault_rh_api_user }}"
rh_api_pass: "{{ vault_rh_api_pass }}"
```

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
| `skip_mustgather_deletion` | `false` | Preserve archives after successful upload |
| `mustgather_output_dir` | `/tmp/must-gather-<epoch>` | Base directory for collections |
| `rh_upload_max_retries` | `3` | Maximum retry attempts per archive part |
| `rh_upload_fail_on_partial` | `true` | Fail playbook if any part fails |

## Configuration Examples

### HashiCorp Vault Integration

```yaml
vars:
  rh_api_token: "{{ lookup('community.hashi_vault.hashi_vault', 'secret=secret/data/redhat:api_token') }}"
  rh_api_user: "{{ lookup('community.hashi_vault.hashi_vault', 'secret=secret/data/redhat:username') }}"
  rh_api_pass: "{{ lookup('community.hashi_vault.hashi_vault', 'secret=secret/data/redhat:password') }}"
  proxy_http: "{{ lookup('community.hashi_vault.hashi_vault', 'secret=secret/data/proxy:http_proxy') }}"
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

1. **Pre-Validation**: Verifies required variables, oc binary, and authentication
2. **Node Selection**: Identifies or labels infrastructure node for must-gather execution
3. **Directory Preparation**: Creates clean working directories
4. **Collection Execution**: Runs `oc adm must-gather` command
5. **Archive Creation**: Compresses collection into tar.gz (splits if > 900MB)
6. **Archive Transfer**: Fetches archive from managed host to execution environment
7. **Upload**: Uploads archive parts to Red Hat support case via `redhat_upload` module
8. **Cleanup**: Removes temporary files and artifacts
9. **Logging**: Records operation status and details

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

### Unit Tests

Run module syntax validation:

```bash
python3 -m py_compile roles/must_gather_log/library/redhat_upload.py
```

### Integration Tests

Test with a real Red Hat case (using test case):

```bash
ansible-playbook playbooks/test_redhat_upload.yml \
  -e rh_case="TEST_CASE_ID" \
  -e rh_api_token="YOUR_TOKEN"
```

See `TESTING_CHECKLIST.md` for comprehensive testing scenarios.

## Troubleshooting

### Module Not Found

**Symptoms**: `module 'redhat_upload' not found`

**Solution**: Ensure the role's `library/` directory is in the module search path. When using the role, the module should be automatically available.

### Authentication Failures

**Symptoms**: HTTP 401 or 403 errors

**Debug Steps**:

1. Verify token is valid
2. Check token expiration
3. Verify case access permissions
4. Try regenerating API token

### Upload Failures

**Symptoms**: Upload status shows failures

**Debug Steps**:

1. Check `upload_status.results` for per-part details
2. Review HTTP status codes
3. Verify network connectivity to `api.access.redhat.com`
4. Check proxy configuration if applicable

## Support

For issues or questions:

1. Check `TESTING_CHECKLIST.md` for common scenarios
2. Review `redhat_upload_module_migration_plan.md` for migration guidance
3. Check module documentation: `ansible-doc redhat_upload` (when module is in path)

## License

Apache-2.0

## Author

Senior Systems Automation Engineer
