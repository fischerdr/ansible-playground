# Must-Gather Log Collection Role - Overview

## Purpose

An Ansible role designed for Ansible Automation Platform execution environments that automates the collection of OpenShift must-gather diagnostic bundles and uploads them directly to Red Hat support cases via HTTP API.

## Key Capabilities

### Core Functionality

- **Automated Collection**: Executes `oc adm must-gather` on designated OpenShift infrastructure nodes
- **Direct Upload**: Uploads diagnostic archives to Red Hat support cases via authenticated API
- **Large Archive Handling**: Automatically splits archives exceeding 900MB into multiple parts
- **Multi-Part Upload**: Handles sequential upload of split archive parts
- **Archive Preservation**: Optionally preserves archives on upload failure with structured naming convention
- **Comprehensive Logging**: Maintains operation logs and displays detailed execution summaries

### Enterprise Features

- **AAP Native Integration**: Designed for execution within Ansible Automation Platform using execution environments
- **Credential Management**: Supports AAP credential injection and HashiCorp Vault integration
- **Proxy Support**: Handles authenticated proxy configuration for restricted environments
- **Kubernetes Native Operations**: Uses `kubernetes.core` modules instead of shell commands
- **Idempotent Node Labeling**: Intelligently selects and labels infrastructure nodes for must-gather execution
- **Comprehensive Error Handling**: Block/rescue/always constructs with detailed troubleshooting guidance

## Requirements

### Platform Requirements

- Ansible >= 2.15
- OpenShift Container Platform 4.x
- Ansible Automation Platform with execution environment support

### Required Collections

- `ansible.builtin` (core modules)
- `kubernetes.core` (for OpenShift node operations)

### External Dependencies

- OpenShift CLI (`oc`) binary in execution environment
- Red Hat API access token with case attachment permissions
- Network access to `api.access.redhat.com` (direct or via proxy)

### Authentication

- Red Hat API token (injected via AAP credential or HashiCorp Vault)
- OpenShift cluster authentication (kubeconfig or token)

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
| `RH_API_TOKEN` | Red Hat API authentication token | Injected via AAP credential |

### Common Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `must_gather_version` | `""` | OpenShift version for must-gather image |
| `skip_mustgather_deletion` | `false` | Preserve archives after successful upload |
| `mustgather_output_dir` | `/tmp/must-gather-<epoch>` | Base directory for collections |

## Operational Workflow

### Execution Phases

1. **Pre-Validation**: Verifies required variables, oc binary, and authentication
2. **Node Selection**: Identifies or labels infrastructure node for must-gather execution
3. **Directory Preparation**: Creates clean working directories
4. **Collection Execution**: Runs `oc adm must-gather` command
5. **Archive Creation**: Compresses collection into tar.gz (splits if > 900MB)
6. **Archive Transfer**: Fetches archive from managed host to execution environment
7. **Upload**: Uploads archive parts to Red Hat support case via API
8. **Cleanup**: Removes temporary files and artifacts
9. **Logging**: Records operation status and details

### Automatic Archive Splitting

When must-gather collections exceed 900MB:

- Automatically splits into 900MB parts
- Generates sequential part files: `must-gather.tar.gz.part000`, `must-gather.tar.gz.part001`, etc.
- Uploads all parts with descriptive identifiers
- Maintains archive integrity across splits

### Archive Naming Convention

Preserved archives follow a structured naming format:

```
<cluster_name>-case<rh_case>-<original_filename>-<ISO8601_timestamp>

Example:
prod-ocp-01-case03123456-must-gather.tar.gz-2025-11-05T14-23-45Z
```

This enables:
- Cluster-based archive identification
- Case correlation across multiple collections
- Chronological sorting and audit trails
- Multi-cluster and multi-collection tracking

## Configuration Methods

### AAP Credential Injection

**Custom Credential Type - Red Hat API Token:**

Input Configuration:
```yaml
fields:
  - id: rh_api_token
    type: string
    label: Red Hat API Token
    secret: true
```

Injector Configuration:
```yaml
env:
  RH_API_TOKEN: '{{ rh_api_token }}'
```

### HashiCorp Vault Integration

For organizations using HashiCorp Vault for secret management:

```yaml
# group_vars/all/vault_lookups.yml
rh_api_token: "{{ lookup('community.hashi_vault.hashi_vault',
                  'secret=secret/data/redhat:api_token') }}"
```

Requires `community.hashi_vault` collection in execution environment.

### Proxy Configuration

For environments requiring proxy authentication:

**Custom Credential Type - Red Hat API Proxy:**

```yaml
fields:
  - id: rh_api_proxy
    type: string
    label: Proxy Server (host:port)
  - id: rh_api_proxy_user
    type: string
    label: Proxy Username
  - id: rh_api_proxy_pass
    type: string
    label: Proxy Password
    secret: true
```

## Architecture Highlights

### Kubernetes Native Operations

The role uses `kubernetes.core` modules for all node operations:

- `kubernetes.core.k8s_info`: Node discovery and querying
- `kubernetes.core.k8s`: Idempotent node labeling with merge patches
- No shell command parsing or AWK dependencies
- Structured data handling throughout

### Modular Upload Script

Upload logic is extracted to `files/upload_to_redhat.sh`:

- Separation of concerns between Ansible orchestration and upload mechanics
- Standalone testability and debugging
- Standardized exit codes for error handling
- Cleaner ansible-lint compliance

### Comprehensive Error Handling

All critical operations use block/rescue/always constructs:

- Graceful failure handling with detailed error messages
- Archive preservation on upload failure
- Automatic cleanup on success
- Troubleshooting guidance in error output

### Operational Visibility

**Operation Summary Output:**
```
===================================================================
Must-Gather Operation Summary
===================================================================
Host: ocp-master-01
Cluster: prod-ocp-01
Red Hat Case: 03123456
Status: SUCCESS
Archive Parts: 1
Collection Size: 347.52 MB
Node Used: infra-node-01
Cleanup Performed: Yes
===================================================================
```

**Persistent Logging:**
```
/var/log/ansible-must-gather.log
2025-11-05T14:23:45Z | Host: ocp-master-01 | Cluster: prod-ocp-01 | Status: SUCCESS | Case: 03123456 | Parts: 1 | Archive: UPLOADED
```

## Performance Characteristics

### Typical Execution Times

| Phase | Duration |
|-------|----------|
| Pre-Validation | 5-10 seconds |
| Node Selection | 3-5 seconds |
| Directory Preparation | 2-3 seconds |
| Must-Gather Collection | 5-15 minutes |
| Archive Creation | 2-10 minutes |
| Upload | 3-15 minutes |
| Cleanup | 2-5 seconds |
| **Total** | **10-35 minutes** |

### Resource Requirements

- **Disk (Managed Host)**: 2-3x collection size
- **Disk (Controller)**: 1x collection size (temporary)
- **Memory**: 500MB-1GB for archive operations
- **Network**: Bandwidth dependent on archive size and upload duration

## Security Considerations

### Credential Protection

- All credentials injected via AAP environment variables
- No credentials stored in playbooks or inventory
- `no_log: true` on credential-handling tasks
- Proxy credentials never logged or exposed

### Archive Security

- Archives may contain sensitive cluster diagnostic data
- Temporary archives cleaned on successful upload
- Failed uploads preserve archives with clear notification
- Archive encryption recommended for preserved files

### Network Security

- HTTPS enforced for all Red Hat API communication
- SSL certificate validation enabled by default
- Proxy support for enterprise security boundaries

## Available Tags

Selective execution using Ansible tags:

| Tag | Purpose |
|-----|---------|
| `validation` | Pre-execution validation checks |
| `node_selection` | Must-gather node identification |
| `preparation` | Directory and environment setup |
| `collection` | Must-gather execution |
| `archiving` | Archive creation and compression |
| `upload` | Red Hat API upload operations |
| `cleanup` | Temporary file removal |
| `always` | Tasks that execute regardless of tag selection |

### Tag Usage Examples

```bash
# Run only collection (skip upload)
ansible-playbook playbook.yml --tags collection,archiving

# Skip cleanup (preserve files for inspection)
ansible-playbook playbook.yml --skip-tags cleanup

# Run validation only
ansible-playbook playbook.yml --tags validation
```

## Troubleshooting Quick Reference

### Common Issues

**RH_API_TOKEN not found:**
- Verify AAP credential attached to job template
- Check credential injector configuration
- Confirm credential not expired

**Archive exceeds 1GB:**
- Automatic splitting handles this
- Verify split archives uploaded successfully
- Check Red Hat case for all parts

**No infra nodes found:**
- Verify nodes labeled with `tier=infra`
- Check OpenShift cluster connectivity
- Manually label node: `oc label node <node-name> tier=infra`

**Upload fails with HTTP 401:**
- Red Hat API token invalid or expired
- Regenerate token from Red Hat Customer Portal
- Update credential in AAP or Vault

### Upload Script Exit Codes

| Exit Code | Description |
|-----------|-------------|
| 0 | Success - upload completed |
| 10 | RH_API_TOKEN environment variable not set |
| 11 | Archive file not found or required variable missing |
| 12 | Archive exceeds 1GB HTTP upload limit |
| 13 | Network or SSL error during curl execution |
| 14 | HTTP response indicates upload failure |

## Documentation Reference

### Detailed Documentation

- **`README.md`**: Complete role documentation with all configuration options
- **`QUICK_REFERENCE.md`**: Operator quick reference with common commands
- **`IMPLEMENTATION_SUMMARY.md`**: Technical implementation details and architecture decisions
- **`IMPLEMENTATION_COMPARISON.md`**: Comparison of implementation approaches
- **`HASHICORP_VAULT_CONFIGURATION.md`**: HashiCorp Vault integration guide
- **`ARCHIVE_NAMING_CONVENTION.md`**: Archive naming format and search patterns
- **`ARCHIVE_PRESERVATION.md`**: Archive preservation procedures and policies
- **`files/README.md`**: Upload script documentation

### Role Structure

```
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
├── README.md                 # Complete operational documentation
├── OVERVIEW.md               # This document
├── QUICK_REFERENCE.md        # Quick reference guide
├── IMPLEMENTATION_SUMMARY.md # Technical implementation summary
└── [Additional documentation files]
```

## Version Information

### Current Version

**Version 2.0** - Comprehensive AAP/EE implementation

### Key Features in Version 2.0

- Complete AAP execution environment compatibility
- Kubernetes native operations (no shell parsing)
- Automatic archive splitting for large collections
- Multi-part upload capability
- Modular upload script architecture
- Comprehensive error handling throughout
- Enhanced operational visibility and logging
- HashiCorp Vault integration support
- Structured archive naming convention
- Enterprise security standards compliance

## Support and Maintenance

### Maintainer

Enterprise Automation Team

### License

Proprietary - Internal Use Only

### Feedback and Issues

For issues, questions, or enhancement requests:

1. Review comprehensive documentation in role directory
2. Check troubleshooting sections in `README.md`
3. Review operation logs at `/var/log/ansible-must-gather.log`
4. Run with increased verbosity: `ansible-playbook -vvv`
5. Contact Enterprise Automation Team with detailed context

## Migration from Previous Implementations

Organizations using earlier implementations should:

1. Review `IMPLEMENTATION_COMPARISON.md` for detailed differences
2. Update calling playbooks with new required variables (`OC_BIN`, `cluster_name`)
3. Test in non-production environment
4. Deploy to production following standard change management procedures

The current implementation maintains backward compatibility where possible while providing enhanced functionality and enterprise-grade operational characteristics.

