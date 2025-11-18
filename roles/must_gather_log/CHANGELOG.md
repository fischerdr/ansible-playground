# Changelog

All notable changes to the must_gather_log role will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-11-17

### Changed - BREAKING

- **Upload Method**: Migrated from Red Hat HTTP API to SFTP upload
- **Authentication**: Changed from API tokens to SFTP tokens
- **Variables Renamed**:
  - `rh_api_token` → `rh_sftp_token`
  - `rh_api_user` → `rh_sftp_user`
  - `rh_api_pass` → removed (not used with SFTP)
- **File Size Limits**: Removed 1GB file size limit (SFTP has no limit)
- **Archive Handling**: Simplified to single tar.gz file (no splitting required)

### Added

- SFTP upload support with sshpass and netcat
- HTTP CONNECT proxy tunneling for SFTP connections
- Comprehensive SFTP operation logging to `mustgather_upload_logs` directory
- Connectivity test before upload with detailed logging
- Epoch timestamp-based file naming to prevent collisions on multiple runs
- New variable: `rh_sftp_host` (default: `sftp.access.redhat.com`)
- New variable: `mustgather_upload_logs` for SFTP log storage
- Red Hat SFTP naming convention support (CASEID_filename)
- Auto-attachment to Red Hat cases within minutes of upload

### Removed

- Custom Python module `redhat_upload.py` (no longer needed)
- HTTP API upload logic and dependencies
- File splitting functionality (900MB threshold)
- Multi-part upload tracking and retry logic
- `CaseManagement-API_v1.json` API specification file
- `library/` directory (no custom modules required)
- Variables:
  - `rh_api_pass`
  - `rh_upload_max_retries` (SFTP uses standard retry)
  - `proxy_https` (SFTP uses only HTTP CONNECT tunnel)
  - `proxy_no` (not applicable for SFTP)

### Fixed

- File and directory collision prevention using epoch timestamps
- Archive search patterns now use wildcards to match all preserved archives
- Retention policy correctly applies to timestamped archives

### Security

- SFTP tokens are time-limited and single-use
- All SFTP operations use `no_log: true` to prevent credential exposure
- Upload logs do not contain sensitive credentials
- SSH encryption for all SFTP connections

### Migration Guide

#### For Existing Users

**Variable Migration**:

```yaml
# Old (v1.x)
rh_api_token: "{{ vault_rh_api_token }}"
rh_api_user: "{{ vault_rh_api_user }}"
rh_api_pass: "{{ vault_rh_api_pass }}"

# New (v2.0)
rh_sftp_user: "{{ vault_rh_sftp_user }}"
rh_sftp_token: "{{ vault_rh_sftp_token }}"
```

**Generate SFTP Token**:

- Web UI: <https://access.redhat.com/support/secure-ftp>
- API: `curl -X POST https://api.access.redhat.com/support/v2/sftp/token`

**Vault Structure Update**:

```bash
# Remove old secrets
vault kv delete secret/redhat/api_token
vault kv delete secret/redhat/api_pass

# Add new secrets
vault kv put secret/redhat \
  sftp_user="username@example.com" \
  sftp_token="generated-sftp-token"
```

**Proxy Configuration**:

```yaml
# Old (v1.x)
proxy_http: "http://proxy.example.com:8080"
proxy_https: "http://proxy.example.com:8080"
proxy_no: "localhost,127.0.0.1"

# New (v2.0) - only HTTP proxy needed for SFTP tunneling
proxy_http: "http://proxy.example.com:8080"
```

**Archive Handling**:

- No action required
- Archives are now single files (no splitting)
- Preserved archives use epoch timestamps for uniqueness

#### Playbook Updates

No playbook structure changes required. Only update variable names in your inventory or group_vars.

#### System Requirements

New dependencies for execution environment:

- `sshpass` - For non-interactive SFTP authentication
- `nc` (netcat) - For HTTP proxy tunneling

Add to your execution environment definition:

```yaml
dependencies:
  system:
    - sshpass
    - nc
```

### Documentation

- Completely rewritten README.md for SFTP implementation
- Updated group_vars_example.yml with SFTP credentials
- Added detailed SFTP upload workflow documentation
- Added troubleshooting section for SFTP-specific issues
- Added collision prevention documentation

### Testing

- Added comprehensive SFTP upload test playbook
- Test playbook supports configurable archive sizes
- Quick test mode (~2 minutes vs 45-50 minutes)
- Detailed upload log verification

## [1.x] - Previous Versions

### Features (Historical)

- HTTP API upload to Red Hat support cases
- Custom Python module for multipart uploads
- 900MB file splitting for large archives
- Archive preservation and retention policies
- Node label management
- Flexible operation modes (collect-only vs upload)

---

## Upgrade Path

### From 1.x to 2.0

**Risk**: Low - Variable name changes only

**Steps**:

1. Update variable names in inventory/group_vars
2. Generate SFTP tokens and store in Vault
3. Update execution environment with sshpass and nc
4. Test with test playbook before production use
5. Update AAP credential types if using credential injection

**Rollback**: Keep v1.x branch available if needed

**Testing**: Use `playbooks/test-must-gather-upload.yml` to verify SFTP functionality

---

For detailed usage and examples, see [README.md](README.md).
