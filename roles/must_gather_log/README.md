# Must-Gather Log Collection and Upload Role

## Purpose

Collects OpenShift must-gather diagnostic bundles and uploads them directly to Red Hat support cases via HTTP API. This role is designed for execution within Ansible Automation Platform Execution Environments and supports proxy-authenticated uploads.

## Requirements

### Ansible Version

- Ansible >= 2.15

### Collections

- ansible.builtin (core modules)

### External Dependencies

- OpenShift CLI (`oc`) binary available in execution environment or mounted volume
- Red Hat API access token with case attachment permissions
- Network access to `api.access.redhat.com` (direct or via proxy)
- curl utility (available in most execution environments)
- bash shell (for upload script execution)

### Target Platforms

- OpenShift Container Platform 4.x
- Red Hat CoreOS or RHEL hosts with OpenShift cluster access

## Role Variables

### Required Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `rh_case` | string | Red Hat support case number for attachment upload | `"01234567"` |
| `RH_API_TOKEN` | environment variable | Red Hat API authentication token (injected by AAP credential) | Provided by AAP credential |

### Optional Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `working_dir` | string | `"/usr/local/bin"` | Directory containing oc CLI binary |
| `mustgather_output_dir` | string | `"/tmp/must-gather-{{ epoch }}"` | Output directory for must-gather artifacts |
| `mustgather_log_dir` | string | `"{{ mustgather_output_dir }}"` | Working directory for oc adm must-gather command |
| `mustgather_var_log_dir` | string | `"{{ mustgather_output_dir }}"` | Cleanup target directory |
| `must_gather_image` | string | `"quay.io/openshift-release-dev/ocp-v4.0-art-dev@sha256:latest"` | Must-gather container image reference |
| `rh_upload_description` | string | `"must-gather for {{ inventory_hostname }}"` | Description text for uploaded attachment |
| `skip_mustgather_deletion` | boolean | `false` | Preserve must-gather artifacts after upload |
| `must_gather_version` | string | `""` | Version identifier (must be defined and non-empty to trigger collection) |

### Proxy Configuration (Environment Variables)

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `RH_API_PROXY` | environment variable | Proxy server (host:port or full URL) | `"proxy.example.com:8080"` or `"http://proxy.example.com:8080"` |
| `RH_API_PROXY_USER` | environment variable | Proxy authentication username | `"proxy_user"` |
| `RH_API_PROXY_PASS` | environment variable | Proxy authentication password | Injected by AAP credential |

All proxy-related variables should be injected via AAP credentials for security.

## Role Structure

```text
roles/must_gather_log/
├── defaults/
│   └── main.yml              # Default variable definitions
├── files/
│   ├── upload_to_redhat.sh   # Upload script for Red Hat API
│   └── README.md             # Upload script documentation
├── meta/
│   └── main.yml              # Role metadata
├── tasks/
│   └── main.yml              # Main task execution
└── README.md                 # This file
```

### Upload Script Architecture

The role uses a modular architecture with the upload logic extracted to `files/upload_to_redhat.sh`. This provides:

- **Improved Maintainability**: Upload logic can be modified independently
- **Enhanced Testability**: Script can be tested and debugged standalone
- **Better Separation of Concerns**: Bash logic separated from Ansible orchestration
- **Cleaner Linting**: Eliminates Jinja2/YAML parser conflicts

The script accepts configuration via environment variables and returns standardized exit codes. See `files/README.md` for detailed script documentation.

## Dependencies

None

## Example Playbook

### Basic Usage

```yaml
---
- name: "Collect and upload OpenShift must-gather diagnostics"
  hosts: openshift_control_plane[0]
  gather_facts: true
  become: false
  
  vars:
    rh_case: "01234567"
    must_gather_version: "4.14"
    
  roles:
    - role: must_gather_log
```

### With Custom Image and Preservation

```yaml
---
- name: "Collect must-gather with custom image and preserve artifacts"
  hosts: ocp_masters[0]
  gather_facts: true
  
  vars:
    rh_case: "{{ ticket_number }}"
    must_gather_version: "{{ ocp_version }}"
    must_gather_image: "registry.example.com/custom-must-gather:v4.14"
    skip_mustgather_deletion: true
    
  roles:
    - role: must_gather_log
```

### Using Tags for Selective Execution

```yaml
---
- name: "Execute only validation and collection phases"
  hosts: openshift_hosts
  
  vars:
    rh_case: "12345678"
    must_gather_version: "4.15"
    
  roles:
    - role: must_gather_log
      tags: [validation, collection, archiving]
```

## AAP Job Template Configuration

### Credentials Required

#### 1. Red Hat API Token Credential

Create a custom credential type:

**Credential Type Name:** Red Hat API Token

**Input Configuration:**

```yaml
fields:
  - id: rh_api_token
    type: string
    label: Red Hat API Token
    secret: true
required:
  - rh_api_token
```

**Injector Configuration:**

```yaml
env:
  RH_API_TOKEN: '{{ rh_api_token }}'
```

#### 2. Red Hat API Proxy Credential (Optional)

**Input Configuration:**

```yaml
fields:
  - id: rh_api_proxy
    type: string
    label: Proxy Server
  - id: rh_api_proxy_user
    type: string
    label: Proxy Username
  - id: rh_api_proxy_pass
    type: string
    label: Proxy Password
    secret: true
```

**Injector Configuration:**

```yaml
env:
  RH_API_PROXY: '{{ rh_api_proxy }}'
  RH_API_PROXY_USER: '{{ rh_api_proxy_user }}'
  RH_API_PROXY_PASS: '{{ rh_api_proxy_pass }}'
```

#### 3. OpenShift Cluster Credential

Use OpenShift or Kubernetes API Bearer Token credential type to authenticate oc commands.

### Survey Variables

Configure job template survey to prompt for:

| Variable | Type | Default | Required |
|----------|------|---------|----------|
| `rh_case` | text | | Yes |
| `must_gather_version` | text | `"4.14"` | Yes |
| `skip_mustgather_deletion` | boolean | `false` | No |

### Extra Variables Example

```yaml
rh_case: "{{ survey_rh_case }}"
must_gather_version: "{{ survey_must_gather_version }}"
working_dir: "/runner/oc-cli"
```

## Role Tags

| Tag | Purpose |
|-----|---------|
| `validation` | Variable and prerequisite validation tasks |
| `node_selection` | Must-gather node identification and labeling |
| `preparation` | Directory and environment preparation |
| `collection` | Must-gather execution |
| `archiving` | Log compression and archive creation |
| `upload` | Red Hat API upload operations |
| `transfer` | Archive transfer from managed host to EE |
| `api` | Red Hat API interaction |
| `response` | API response parsing |
| `cleanup` | Temporary file and directory removal |
| `logging` | Operation logging |
| `always` | Tasks that always execute |

### Tag Usage Examples

```bash
# Run only validation checks
ansible-playbook playbook.yml --tags validation

# Skip upload phase (collect and archive only)
ansible-playbook playbook.yml --skip-tags upload

# Execute collection and upload only (assumes node already labeled)
ansible-playbook playbook.yml --tags collection,archiving,upload
```

## Error Handling

The role implements comprehensive error handling using block/rescue/always constructs:

### Validation Phase

- Validates all required variables before execution
- Verifies oc binary existence and executability
- Confirms RH_API_TOKEN presence in environment

### Collection Phase

- Identifies or labels appropriate must-gather node
- Validates must-gather output creation
- Logs detailed error messages for troubleshooting

### Upload Phase

- Validates archive size (enforces 1GB limit for HTTP upload)
- Handles proxy authentication securely
- Preserves archive on upload failure for manual intervention
- Provides detailed troubleshooting guidance on failure

### Cleanup Phase

- Removes temporary archives from execution environment (on success)
- Removes must-gather directory from managed host (unless preserved)
- Logs operation completion status

## Operational Workflow

1. **Validation:** Verifies required variables and tools
2. **Node Selection:** Identifies or labels infra node for must-gather
3. **Preparation:** Creates output directory
4. **Collection:** Executes `oc adm must-gather`
5. **Archiving:** Compresses logs into tar.gz archive
6. **Transfer:** Fetches archive to execution environment
7. **Upload:** Executes `upload_to_redhat.sh` script to upload archive to Red Hat API
8. **Cleanup:** Removes temporary artifacts
9. **Logging:** Records operation status

The upload phase uses a standalone bash script that validates file size, handles proxy configuration, and performs the multipart HTTP upload with proper error handling and standardized exit codes.

## Troubleshooting

### Common Issues

#### RH_API_TOKEN not found

**Symptom:** Task fails with "RH_API_TOKEN not set in environment"

**Resolution:**

- Ensure AAP credential is attached to job template
- Verify credential type correctly injects `RH_API_TOKEN` environment variable
- Check credential is not expired

#### Archive upload fails with HTTP 401

**Symptom:** Upload fails with "HTTP 401" error (exit code 14)

**Resolution:**

- Validate Red Hat API token is current and not expired
- Verify token has permissions for case attachment upload
- Regenerate token from Red Hat Customer Portal if necessary

#### Upload script exit codes

The upload script (`files/upload_to_redhat.sh`) returns standardized exit codes:

| Exit Code | Description |
|-----------|-------------|
| 0 | Success - upload completed |
| 10 | RH_API_TOKEN environment variable not set |
| 11 | Archive file not found or required variable missing |
| 12 | Archive exceeds 1GB HTTP upload limit |
| 13 | Network or SSL error during curl execution |
| 14 | HTTP response indicates upload failure |

For detailed script documentation, see `files/README.md`.

#### Archive exceeds 1GB limit

**Symptom:** Upload fails with "file is larger than 1GB" error

**Resolution:**

- Must-gather output exceeds HTTP upload limit
- Use alternative upload method (FTP/SFTP)
- Consider filtering must-gather collection scope

#### Proxy authentication failures

**Symptom:** Upload fails with "network/ssl" or timeout errors

**Resolution:**

- Verify `RH_API_PROXY_USER` and `RH_API_PROXY_PASS` are correct
- Test proxy connectivity from execution environment
- Confirm proxy allows HTTPS connections to api.access.redhat.com

#### No infra nodes found

**Symptom:** Node selection fails with no nodes available

**Resolution:**

- Verify cluster has nodes labeled with `tier=infra`
- Check oc CLI authentication and cluster connectivity
- Manually label node if necessary: `oc label node <node-name> tier=infra`

#### Must-gather collection timeout

**Symptom:** Collection phase times out or hangs

**Resolution:**

- Check cluster health and resource availability
- Verify must-gather image is accessible from cluster
- Review pod logs: `oc logs -n openshift-must-gather-<id>`

## Security Considerations

### Credential Management

- All credentials injected via AAP environment variables
- No credentials stored in playbooks or inventory
- Proxy credentials never logged or exposed

### Sensitive Data Protection

- Upload tasks use `no_log: true` to prevent credential disclosure
- Archive paths not logged to prevent information leakage
- API responses sanitized before logging

### Network Security

- Enforces TLS/SSL for Red Hat API communication
- Supports authenticated proxy for corporate environments
- Validates certificates by default

### Artifact Cleanup

- Temporary archives removed from execution environment after successful upload
- Managed host directories cleaned unless explicitly preserved
- Failed uploads preserve archives with clear notification

## Performance Considerations

### Archive Size Management

- HTTP upload limited to 1GB (Red Hat API constraint)
- Large must-gather outputs may require alternative upload methods
- Consider must-gather scope reduction for very large clusters

### Network Transfer

- Archive transfer from managed host to EE may be slow on large files
- Upload time depends on network bandwidth and archive size
- Typical upload time: 2-5 minutes for 200-500MB archives

### Resource Usage

- Must-gather collection can be resource-intensive on target node
- Role uses node-selector to target infra nodes
- Temporary disk space required: ~2x must-gather output size

## Maintainer

Enterprise Automation Team

## License

Proprietary - Internal Use Only

## Version History

- **v2.0** (2025-01-27): Comprehensive refactoring for AAP EE compatibility
  - Added complete variable validation with pre-execution checks
  - Implemented block/rescue/always error handling throughout
  - Enhanced security controls with consistent no_log usage
  - Added comprehensive tagging for selective execution
  - Improved logging and troubleshooting guidance
  - **Extracted upload logic to modular script** (`files/upload_to_redhat.sh`)
  - Standardized exit codes for upload operations
  - Created comprehensive role and script documentation
  
- **v1.0**: Initial version with basic must-gather collection and upload
