# Portworx Upgrade Role - Distribution Package

Version: 1.0.0
Release Date: 2025-12-10

## Package Contents

- `portworx-upgrade-role-1.0.0.tar.gz` - Complete standalone Ansible role (22KB)
- `portworx-upgrade-role-1.0.0.tar.gz.sha256` - SHA256 checksum for verification

## Checksum Verification

Before extracting, verify the integrity of the tarball:

```bash
sha256sum -c portworx-upgrade-role-1.0.0.tar.gz.sha256
```

Expected output:

```text
portworx-upgrade-role-1.0.0.tar.gz: OK
```

## Quick Installation

### 1. Extract the Role

```bash
tar -xzf portworx-upgrade-role-1.0.0.tar.gz -C roles/
mv roles/portworx-upgrade-role roles/portworx_upgrade
```

### 2. Install Dependencies

```bash
# Ansible collections
ansible-galaxy collection install -r roles/portworx_upgrade/requirements.yml

# Python libraries
pip install -r roles/portworx_upgrade/requirements.txt
```

### 3. Download Version Files

```bash
export PXVER=3.5.0
export KBVER=$(oc version | awk '/Server Version/ {print $3}')
curl -o roles/portworx_upgrade/files/versions/versions-${PXVER} \
  "https://install.portworx.com/$PXVER/version?kbver=$KBVER"
```

### 4. Run Example Playbook

```bash
cp roles/portworx_upgrade/example-playbook.yml playbooks/px_upgrade.yml
ansible-playbook playbooks/px_upgrade.yml -e portworx_target_version=3.5.0
```

## Package Contents Detail

The tarball contains a complete, self-contained Ansible role with:

### Documentation

- `README.md` - Comprehensive role documentation
- `INSTALL.md` - Detailed installation guide
- `CHANGELOG.md` - Version history and changes
- `LICENSE` - MIT license

### Configuration Files

- `.gitignore` - Git ignore patterns
- `.ansible-lint` - Ansible-lint configuration (production profile)
- `requirements.yml` - Ansible collection requirements
- `requirements.txt` - Python requirements

### Role Files

- `defaults/main.yml` - Default variables (50 variables)
- `vars/main.yml` - Internal constants
- `meta/main.yml` - Galaxy metadata
- `handlers/main.yml` - Handlers
- `example-playbook.yml` - Example usage playbook

### Task Files (30 files)

- `tasks/main.yml` - Main orchestration (8 phases)
- `tasks/preflight/*.yml` - Pre-flight validation (6 files)
- `tasks/upgrade/*.yml` - Upgrade execution (4 files)
- `tasks/monitor/*.yml` - Monitoring logic (5 files)
- `tasks/validate/*.yml` - Final validation (4 files)
- `tasks/report/*.yml` - Report generation (2 files)

### Templates

- `templates/upgrade_summary.j2` - Upgrade summary report template

### Version Files

- `files/versions/README.md` - Version file documentation
- `files/versions/versions-3.4.0.1` - Example version file

## Features

- **Comprehensive Preflight Validation** - Environment, nodes, pods, cluster health, STC config
- **Operator Upgrade** - Auto-approval with health verification
- **Kubernetes API-Based Monitoring** - Efficient tracking without pxctl overhead
- **Dual Timeout Strategy** - 35min global, 25min per-pod
- **Impatient Mode** - Optional batch deletion for storageless nodes
- **Optimized for Large Clusters** - Inline shell processing for 500+ node clusters
- **Safety Checks** - Cluster health verification at all stages
- **Detailed Reporting** - Comprehensive upgrade summary with timing breakdown

## Requirements

- Ansible Core 2.12+
- kubernetes.core collection v2.3.0+
- Python 3.8+
- OpenShift 4.18+
- Portworx 3.4.0+ (source version)
- Cluster admin access

## Documentation - review

After extraction, review these files in order:

1. `INSTALL.md` - Installation and setup
2. `README.md` - Complete role documentation
3. `example-playbook.yml` - Usage examples
4. `CHANGELOG.md` - Version history

## Support

For issues, questions, or contributions:

1. Review documentation in `README.md`
2. Check troubleshooting section
3. Verify dependencies are installed
4. Open an issue on GitHub with full details

## Version Information

- **Version**: 1.0.0
- **Release Date**: 2025-12-10
- **Ansible-lint**: Passes production profile
- **Python**: 3.8+
- **Collections**: kubernetes.core v2.3.0+

## What's Included

```text
portworx-upgrade-role/
├── README.md                    # Complete documentation
├── INSTALL.md                   # Installation guide
├── CHANGELOG.md                 # Version history
├── LICENSE                      # MIT license
├── example-playbook.yml         # Example usage
├── requirements.yml             # Collection dependencies
├── requirements.txt             # Python dependencies
├── .ansible-lint               # Linting configuration
├── .gitignore                  # Git ignore patterns
├── defaults/main.yml           # Default variables
├── vars/main.yml               # Internal constants
├── meta/main.yml               # Galaxy metadata
├── handlers/main.yml           # Handlers
├── tasks/                      # Task files (30 files)
│   ├── main.yml
│   ├── preflight/             # Validation tasks
│   ├── upgrade/               # Upgrade tasks
│   ├── monitor/               # Monitoring tasks
│   ├── validate/              # Final validation tasks
│   └── report/                # Reporting tasks
├── templates/                  # Jinja2 templates
│   └── upgrade_summary.j2
└── files/versions/             # Version file location
    ├── README.md
    └── versions-3.4.0.1       # Example version file
```

## Testing

The role has been tested with:

- ✅ ansible-lint (production profile)
- ✅ ansible-playbook --syntax-check
- ✅ OpenShift 4.18
- ✅ Portworx 3.4.0.1

## License

MIT License - See LICENSE file for details

## Authors

Enterprise Platform Team

---

For detailed documentation, extract the tarball and review `README.md` and `INSTALL.md`.
