# Changelog

All notable changes to the must_gather_log role will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2024-12-28

### Changed - BREAKING

- **Role Architecture**: Refactored to modular task delegation pattern
  - Main orchestrator (`tasks/main.yml`) now delegates to specialized task files
  - Reduced main.yml from 909 lines to 470 lines (48% reduction)
  - Each workflow component is independently testable and reusable

### Added

- **Automatic SFTP Token Generation**: OAuth2 device authorization flow support
  - New custom module: `library/redhat_sso_device_auth.py`
  - Automated Red Hat SSO device authorization without browser interaction
  - Configurable token expiry (30-90 days)
  - Automatic token refresh when expiring within threshold (default: 7 days)
  - Variables:
    - `rh_sftp_token_auto_generate`: Enable automatic token generation
    - `rh_sftp_token_expiry_days`: Token validity period (default: 30 days)
    - `rh_sftp_token_refresh_threshold_days`: Auto-refresh threshold (default: 7 days)
    - `rh_account_username`: Red Hat account username (for token generation)
    - `rh_account_password`: Red Hat account password (for token generation)
    - `rh_sso_device_auth_endpoint`: Red Hat SSO device authorization endpoint
    - `rh_sso_token_endpoint`: Red Hat SSO token exchange endpoint
    - `rh_sftp_token_endpoint`: Red Hat SFTP token generation endpoint

- **HashiCorp Vault Integration**: Token storage and retrieval
  - Automatic retrieval of SFTP credentials from Vault
  - Optional storage of generated tokens in Vault
  - Token expiry tracking in Vault metadata
  - Variables:
    - `vault_store_tokens`: Enable Vault token storage
    - `vault_addr`: Vault server URL
    - `vault_token`: Vault authentication token
    - `vault_namespace`: Vault namespace (optional)
    - `vault_validate_certs`: SSL certificate validation
    - `vault_mount_path`: KV2 mount path (default: `static_secrets`)
    - `vault_secret_path`: Secret path within mount

- **Modular Task Files**: Specialized task files for each workflow component
  - `tasks/sftp_credential_management.yml`: SFTP credential lifecycle orchestrator
  - `tasks/vault_retrieve_sftp_credentials.yml`: Vault credential retrieval
  - `tasks/check_token_expiry.yml`: Token expiry validation and refresh logic
  - `tasks/redhat_sftp_token_generation.yml`: OAuth2 device authorization token generation
  - `tasks/vault_store_sftp_token.yml`: Store generated tokens in Vault
  - `tasks/must_gather_collection.yml`: OpenShift must-gather execution
  - `tasks/must_gather_upload.yml`: Archive creation and SFTP upload
  - `tasks/cleanup.yml`: Old directory and archive retention management

- **Intelligent Credential Sourcing**: Three-tier credential management
  1. HashiCorp Vault retrieval (automatic via `vault_parameters`)
  2. Automatic token generation (OAuth2 device authorization)
  3. Manual credential provision (via extra vars or group_vars)

- **Token Expiry Management**: Automatic expiry checking and refresh
  - Parses ISO 8601 expiry dates from Vault metadata
  - Calculates days until expiration
  - Triggers automatic refresh when within threshold
  - Force refresh support via `rh_sftp_token_auto_generate: true`

- **Standalone Token Refresh**: Dedicated playbook for token-only operations
  - `playbooks/redhat-sftp-token-refresh.yml`: Generate and store tokens without must-gather collection
  - Supports both Vault storage and manual retrieval

- **Modular Execution**: Direct task file inclusion support
  - Call individual task files using `tasks_from` parameter
  - Enables reusable credential workflows in other roles
  - Independent testing of credential management

### Removed

- **Dead Code Cleanup**: Removed unused variables and files
  - `rh_upload_description`: Obsolete upload description variable
  - `command_retries`: Unused retry configuration
  - `command_delay`: Unused delay configuration
  - `timeout_seconds`: Unused timeout configuration
  - `rh_upload_fail_on_partial`: Legacy variable from HTTP API era
  - Backup files and temporary artifacts

### Fixed

- **Credential Management**: Improved error handling and validation
  - Non-fatal Vault retrieval failures with graceful fallback
  - Comprehensive credential validation with clear error messages
  - Proper `no_log` usage for sensitive operations

### Security

- **Token Generation Security**: OAuth2 device authorization implementation
  - No 2FA support requirement (Red Hat account must have 2FA disabled)
  - Time-limited bearer tokens (single-use)
  - Secure token storage in HashiCorp Vault with metadata
  - All sensitive operations use `no_log: true`

### Documentation

- **README.md**: Comprehensive update with internal architecture section
  - Documented modular task file structure
  - Added 7-phase execution workflow
  - Credential management flow diagram
  - Modular execution examples
  - Token refresh documentation

- **CLAUDE.md**: Repository standards update
  - Added `redhat_sso_device_auth.py` to custom modules list
  - Documented modular orchestrator pattern with examples
  - Added best practices for modular role architecture

### Migration Guide

#### From 2.x to 3.0

**Risk**: Low - Backward compatible, new features are opt-in

**Credential Management Options**:

```yaml
# Option 1: Existing Vault retrieval (no changes required)
rh_sftp_user: "{{ lookup('community.hashi_vault.hashi_vault', 'secret=...') }}"
rh_sftp_token: "{{ lookup('community.hashi_vault.hashi_vault', 'secret=...') }}"

# Option 2: NEW - Automatic token generation
rh_sftp_token_auto_generate: true
rh_account_username: "{{ vault_rh_account_username }}"
rh_account_password: "{{ vault_rh_account_password }}"

# Option 3: NEW - Automatic Vault retrieval (via setup_env role)
# No manual credential configuration needed
# Credentials retrieved automatically using vault_parameters
```

**Token Storage in Vault**:

```yaml
# Enable automatic token storage after generation
vault_store_tokens: true
vault_addr: "https://vault.example.com:8200"
vault_token: "{{ lookup('env', 'VAULT_TOKEN') }}"
vault_mount_path: "static_secrets"
vault_secret_path: "env/{{ cluster_user }}/redhat"
```

**Standalone Token Refresh**:

```bash
# Refresh SFTP tokens without must-gather collection
ansible-playbook playbooks/redhat-sftp-token-refresh.yml \
  -e rh_account_username=user@example.com \
  -e rh_account_password=password \
  -e vault_store_tokens=true
```

**No Breaking Changes**:

- All existing variable names remain valid
- Existing playbooks continue to work without modification
- New features are opt-in via new variables

**Requirements**:

- Red Hat account without 2FA (for automatic token generation only)
- HashiCorp Vault access (for token storage only)
- Python 3.11+ (already required)

### Testing

- All modular task files validated with ansible-lint
- Custom module passes black, isort, flake8 quality checks
- Syntax validation for all playbooks
- Backward compatibility verified with existing deployments

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
