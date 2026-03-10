# Ansible Automation Platform (AAP) Import Configurations

This directory contains AAP/AWX import configurations for different Ansible roles in this project.

## Directory Structure

```
aap_import/
├── README.md                   # This file
└── portworx_upgrade/           # Portworx upgrade role configurations
    ├── README.md               # Detailed import guide
    ├── import_to_aap.sh        # Automated import script
    ├── project_*.json          # Project configurations
    ├── job_template_*.json     # Job template configurations
    ├── workflow_template_*.json # Workflow configurations
    └── execution_environment.json # EE configuration
```

## Available Role Configurations

### Portworx Upgrade

**Location**: `portworx_upgrade/`

Automated Portworx cluster upgrade configurations for AAP with:
- Full upgrade job template
- Preflight check job template
- Impatient mode job template
- Workflow with approval gates
- Survey specifications
- Automated import script

**Quick Start**:
```bash
cd aap_import/portworx_upgrade
./import_to_aap.sh
```

See `portworx_upgrade/README.md` for complete documentation.

## General Import Process

### Prerequisites

1. AAP/AWX 2.4+ or AWX 23.0+
2. Admin access or appropriate permissions
3. `awx` CLI installed (optional): `pip install awxkit`

### Configuration Variables

Before importing, set these environment variables:

```bash
export CONTROLLER_HOST=https://your-aap-server
export CONTROLLER_USERNAME=admin
export CONTROLLER_PASSWORD=your-password
export ORG_NAME="Default"  # Optional
```

### Import Methods

Each role directory provides three import methods:

1. **Automated Script** - `./import_to_aap.sh` (recommended)
2. **AWX CLI** - Manual commands using `awx` CLI
3. **Web UI** - Step-by-step instructions for UI import
4. **API/Curl** - Direct API calls with JSON files

### Common Steps

1. Create/sync SCM project
2. Create execution environment
3. Create inventory (usually localhost)
4. Import job templates
5. Configure surveys
6. Add credentials
7. Test with preflight runs

## File Types

### Project Configuration (`project_*.json`)

Defines SCM project settings:
- Git repository URL
- Branch/tag
- Update on launch settings

### Job Template (`job_template_*.json`)

Defines job template settings:
- Playbook path
- Variables
- Tags
- Survey specification
- Launch options

### Workflow Template (`workflow_template_*.json`)

Defines workflow with:
- Node connections
- Approval gates
- Success/failure paths
- Notification hooks

### Execution Environment (`execution_environment.json`)

Defines container image settings:
- Image name
- Pull policy
- Custom builds

## Adding New Role Configurations

To add a new role:

1. Create directory: `aap_import/your_role/`
2. Add configuration files:
   - `README.md` - Detailed import guide
   - `project_*.json` - Project configuration
   - `job_template_*.json` - Job templates
   - `import_to_aap.sh` - Import script (optional)
3. Update this README with new role information

## Best Practices

### Naming Conventions

- **Project**: `{Role Name} Automation`
- **Job Template**: `{Role Name} - {Action}`
- **Workflow**: `{Role Name} - Full Workflow`
- **EE**: `{Role Name} EE`

### Security

- Never commit credentials to Git
- Use AAP vault for sensitive variables
- Limit job template execution permissions
- Use approval gates for production workflows

### Testing

1. Test project sync first
2. Test with preflight/check mode
3. Verify survey questions
4. Test with non-production inventory
5. Review job output logs

## Troubleshooting

### Common Issues

**Project won't sync**:
- Check Git URL and credentials
- Verify branch name
- Check AAP can reach Git server

**Job template fails immediately**:
- Verify inventory exists
- Check execution environment is available
- Ensure credentials are assigned
- Verify playbook path

**Survey not showing**:
- Check "Enable Survey" is checked
- Verify survey spec JSON is valid
- Re-import survey via API

### Getting Help

1. Check role-specific README in subdirectories
2. Review AAP logs: `/var/log/tower/`
3. Check AAP documentation: https://docs.ansible.com/automation-controller/
4. Review job execution output in AAP UI

## Resources

- AAP Documentation: https://docs.ansible.com/automation-controller/
- AWX CLI: https://github.com/ansible/awx/tree/devel/awxkit
- Execution Environments: https://ansible.readthedocs.io/projects/builder/
- API Reference: https://docs.ansible.com/automation-controller/latest/html/administration/api_ref.html

## Contributing

When adding new role configurations:

1. Follow existing directory structure
2. Include comprehensive README
3. Provide multiple import methods
4. Add automated import script if possible
5. Document survey specifications
6. Include troubleshooting section
