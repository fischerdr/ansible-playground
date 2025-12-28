# Must-Gather Log Role - Distribution Package

Version: 3.0.0
Release Date: 2024-12-28

## Package Contents

- `must-gather-log-role-3.0.0.tar.gz` - Complete standalone Ansible role (46KB)



## Quick Installation

### 1. Extract the Role

```bash
tar -xzf must-gather-log-role-3.0.0.tar.gz
cp -r must-gather-log-role-3.0.0/must_gather_log /path/to/ansible/project/roles/
```

### 2. Install Dependencies

```bash
cd /path/to/ansible/project

# Install Ansible collections
ansible-galaxy collection install kubernetes.core community.hashi_vault

# Verify oc CLI is available
which oc
```

### 3. Create and Run Playbook

See `docs/example-playbook.yml` for a complete example.

```bash
ansible-playbook playbooks/must-gather-ocp-logs.yml \
  -e cluster_name=prod-ocp-01 \
  -e rh_case=03123456 \
  -e rh_sftp_user=user@example.com \
  -e rh_sftp_token=token
```

## Key Features

### Modular Architecture

- 9 specialized task files with clean orchestrator pattern
- 48% code reduction in main orchestrator (909 → 470 lines)
- Each component independently testable and reusable

### Automatic SFTP Token Generation

- OAuth2 device authorization flow (no browser required)
- Automatic token refresh when expiring within threshold
- Configurable token expiry (30-90 days)

### HashiCorp Vault Integration

- Automatic credential retrieval
- Optional token storage with metadata
- Token expiry tracking

### Intelligent Credential Management

Three-tier credential sourcing:

1. HashiCorp Vault retrieval (automatic)
2. Automatic token generation (OAuth2)
3. Manual credential provision

### Flexible Operation Modes

- Collect & Upload: Full must-gather with SFTP upload
- Collect Only: Local preservation without upload requirement

## Requirements

- **Ansible Core:** >= 2.18.4
- **Python:** 3.11+ (recommended)
- **OpenShift CLI:** `oc` binary
- **Collections:**
  - ansible.builtin
  - ansible.posix
  - kubernetes.core >= 2.3.0
  - community.hashi_vault >= 3.0.0

## Documentation

- **Quick Start**: Top-level `README.md`
- **Quick Start Guide**: `docs/QUICKSTART.md`
- **Role Documentation**: `must_gather_log/README.md`
- **Version History**: `must_gather_log/CHANGELOG.md`
- **Example Playbook**: `docs/example-playbook.yml`
- **Package Manifest**: `docs/MANIFEST.txt`

## Support

For issues or questions:

1. Review the role README: `must_gather_log/README.md`
2. Check the CHANGELOG: `must_gather_log/CHANGELOG.md`
3. Consult the quick start guide: `docs/QUICKSTART.md`

## License

Apache-2.0 - See LICENSE file for details

## Version Information

**Version:** 3.0.0  
**Release Date:** 2024-12-28  
**Breaking Changes:** None (backward compatible)

### Changelog Highlights

- Modular architecture refactoring
- Automatic SFTP token generation via OAuth2
- HashiCorp Vault integration
- Token expiry management
- 9 modular task files
- Custom Ansible module for device authorization
- Comprehensive documentation updates

See `roles/must_gather_log/CHANGELOG.md` for complete version history.
