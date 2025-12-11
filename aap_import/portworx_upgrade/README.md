# Ansible Automation Platform (AAP) Import Guide

This directory contains JSON configuration files for importing Portworx upgrade automation into Ansible Automation Platform (AAP/AWX).

## Files Overview

| File | Description | Type |
|------|-------------|------|
| `project_portworx_upgrade.json` | SCM project configuration | Project |
| `execution_environment.json` | Execution environment specification | EE |
| `job_template_portworx_upgrade.json` | Full upgrade job template with survey | Job Template |
| `job_template_portworx_preflight.json` | Preflight check only template | Job Template |
| `job_template_portworx_upgrade_impatient.json` | Impatient mode upgrade template | Job Template |
| `workflow_template_portworx_upgrade.json` | Complete workflow with approval gates | Workflow |

## Prerequisites

### AAP/AWX Setup

1. **AAP Version**: 2.4+ or AWX 23.0+
2. **Authentication**: Admin credentials or appropriate permissions
3. **CLI Tool**: `awx` CLI installed (optional but recommended)

### Required Credentials

Before importing, create these credentials in AAP:

1. **Source Control Credential** (if private repo)
   - Type: Source Control
   - SCM URL: Your Git repository

2. **Machine Credential** (for kubeconfig)
   - Type: Machine
   - Username: (not used)
   - SSH Private Key: (not used)
   - Privilege Escalation: No

3. **OpenShift/Kubernetes Credential**
   - Type: OpenShift or Kubernetes API Bearer Token
   - API Server URL: Your OpenShift API endpoint
   - Bearer Token: Service account token with cluster-admin

### Required Inventory

Create an inventory with a single host:

- **Inventory Name**: `localhost-inventory`
- **Host**: `localhost`
- **Variables**:
  ```yaml
  ansible_connection: local
  ansible_python_interpreter: /usr/bin/python3
  ```

## Import Methods

### Method 1: Using AWX CLI (Recommended)

#### 1. Install AWX CLI

```bash
pip install awxkit
```

#### 2. Configure AWX CLI

```bash
export CONTROLLER_HOST=https://your-aap-server
export CONTROLLER_USERNAME=admin
export CONTROLLER_PASSWORD=your-password
export CONTROLLER_VERIFY_SSL=false  # Only for self-signed certs
```

#### 3. Import Project

```bash
awx projects create \
  --name "Portworx Upgrade Automation" \
  --organization "Default" \
  --scm_type git \
  --scm_url "https://github.com/your-org/ansible-playground.git" \
  --scm_branch "feature/portworx-upgrade" \
  --scm_update_on_launch true

# Wait for project sync
awx projects update <project-id>
```

#### 4. Import Execution Environment

```bash
awx execution_environments create \
  --name "Portworx Upgrade EE" \
  --image "quay.io/ansible/awx-ee:latest" \
  --pull missing
```

#### 5. Import Job Templates

```bash
# Full upgrade template
awx job_templates create \
  --name "Portworx Cluster Upgrade" \
  --description "Automated Portworx cluster upgrade" \
  --job_type run \
  --inventory "localhost-inventory" \
  --project "Portworx Upgrade Automation" \
  --playbook "playbooks/px_upgrade.yml" \
  --ask_variables_on_launch true \
  --ask_tags_on_launch true \
  --survey_enabled true \
  --survey_spec @job_template_portworx_upgrade.json

# Preflight template
awx job_templates create \
  --name "Portworx Upgrade - Preflight Check" \
  --description "Preflight validation only" \
  --job_type run \
  --inventory "localhost-inventory" \
  --project "Portworx Upgrade Automation" \
  --playbook "playbooks/px_upgrade.yml" \
  --job_tags "preflight" \
  --ask_variables_on_launch true \
  --survey_enabled true \
  --survey_spec @job_template_portworx_preflight.json

# Impatient mode template
awx job_templates create \
  --name "Portworx Cluster Upgrade - Impatient Mode" \
  --description "Accelerated upgrade with impatient mode" \
  --job_type run \
  --inventory "localhost-inventory" \
  --project "Portworx Upgrade Automation" \
  --playbook "playbooks/px_upgrade.yml" \
  --ask_variables_on_launch true \
  --survey_enabled true \
  --survey_spec @job_template_portworx_upgrade_impatient.json
```

### Method 2: Using AAP Web UI

#### 1. Create Project

1. Navigate to: **Resources → Projects**
2. Click: **Add**
3. Configure:
   - **Name**: Portworx Upgrade Automation
   - **Organization**: Select your organization
   - **Source Control Type**: Git
   - **Source Control URL**: Your repository URL
   - **Source Control Branch/Tag**: `feature/portworx-upgrade`
   - **Update Revision on Launch**: ✓ Enabled
4. Click: **Save**
5. Wait for sync to complete

#### 2. Create Execution Environment

1. Navigate to: **Administration → Execution Environments**
2. Click: **Add**
3. Configure:
   - **Name**: Portworx Upgrade EE
   - **Image**: `quay.io/ansible/awx-ee:latest`
   - **Pull**: Missing
4. Click: **Save**

#### 3. Create Job Templates

##### Full Upgrade Template

1. Navigate to: **Resources → Templates**
2. Click: **Add → Add job template**
3. Configure:
   - **Name**: Portworx Cluster Upgrade
   - **Description**: Automated Portworx cluster upgrade
   - **Job Type**: Run
   - **Inventory**: Select `localhost-inventory`
   - **Project**: Portworx Upgrade Automation
   - **Execution Environment**: Portworx Upgrade EE
   - **Playbook**: `playbooks/px_upgrade.yml`
   - **Credentials**: Add OpenShift/K8s credential
   - **Variables**:
     ```yaml
     portworx_target_version: ""
     portworx_impatient_mode: false
     portworx_detailed_logging: true
     ```
   - **Options**:
     - ✓ Prompt on launch: Variables
     - ✓ Prompt on launch: Tags
     - ✓ Enable Survey
4. Click: **Save**
5. Add Survey (see Survey Configuration below)

##### Preflight Check Template

1. Same as above but:
   - **Name**: Portworx Upgrade - Preflight Check
   - **Job Tags**: `preflight`
   - **Allow Simultaneous**: ✓ Enabled

##### Impatient Mode Template

1. Same as full upgrade but:
   - **Name**: Portworx Cluster Upgrade - Impatient Mode
   - **Variables**:
     ```yaml
     portworx_target_version: ""
     portworx_impatient_mode: true
     portworx_impatient_batch_size: 7
     portworx_detailed_logging: true
     ```

### Method 3: Using API/Curl

#### Import Project

```bash
curl -X POST https://your-aap-server/api/v2/projects/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d @project_portworx_upgrade.json
```

#### Import Job Template

```bash
curl -X POST https://your-aap-server/api/v2/job_templates/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d @job_template_portworx_upgrade.json
```

## Survey Configuration

### Full Upgrade Survey

The survey collects these parameters from users:

1. **Target Portworx Version** (Required)
   - Type: Text
   - Variable: `portworx_target_version`
   - Example: `3.5.0`

2. **Cluster Name** (Optional)
   - Type: Text
   - Variable: `portworx_cluster_name`
   - For reporting purposes

3. **Enable Impatient Mode** (Required)
   - Type: Multiple Choice
   - Choices: `false`, `true`
   - Default: `false`
   - Variable: `portworx_impatient_mode`

4. **Impatient Mode Batch Size** (Optional)
   - Type: Integer
   - Min: 1, Max: 10
   - Default: 5
   - Variable: `portworx_impatient_batch_size`

5. **Skip Operator Upgrade** (Optional)
   - Type: Multiple Choice
   - Choices: `false`, `true`
   - Default: `false`
   - Variable: `portworx_skip_operator_upgrade`

6. **Detailed Logging** (Optional)
   - Type: Multiple Choice
   - Choices: `true`, `false`
   - Default: `true`
   - Variable: `portworx_detailed_logging`

7. **Work Directory** (Optional)
   - Type: Text
   - Default: `/tmp/ansible-workdir`
   - Variable: `portworx_work_dir`

### Survey Import via API

```bash
# Get job template ID
TEMPLATE_ID=$(curl -s https://your-aap-server/api/v2/job_templates/ \
  -H "Authorization: Bearer <token>" | jq '.results[] | select(.name=="Portworx Cluster Upgrade") | .id')

# Import survey spec
curl -X POST https://your-aap-server/api/v2/job_templates/${TEMPLATE_ID}/survey_spec/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d @job_template_portworx_upgrade.json
```

## Post-Import Configuration

### 1. Update Project SCM URL

Edit `project_portworx_upgrade.json` and update:
```json
"scm_url": "https://github.com/YOUR-ORG/ansible-playground.git"
```

### 2. Assign Credentials

For each job template:
1. Navigate to template
2. Click **Edit**
3. Under **Credentials**, add:
   - OpenShift/K8s credential
   - (Optional) Vault credential if using encrypted vars

### 3. Assign Organization

1. Edit project/templates
2. Select appropriate organization
3. Save

### 4. Configure Notifications (Optional)

Add notifications for job success/failure:
1. Navigate to job template
2. Click **Notifications**
3. Add notification templates for:
   - Success
   - Failure
   - Start

## Workflow Import

The workflow provides a complete upgrade process:

```
┌─────────────────┐
│ Preflight Check │
└────────┬────────┘
         │ Success
         ↓
┌─────────────────┐
│ Approval Gate   │
└────────┬────────┘
         │ Approved
         ↓
┌─────────────────┐
│ Upgrade Exec    │
└────┬────────────┘
     │ Success    │ Failure
     ↓            ↓
┌─────────┐  ┌─────────┐
│ Success │  │ Failure │
│ Notify  │  │ Notify  │
└─────────┘  └─────────┘
```

To import workflow:

1. Navigate to: **Resources → Templates**
2. Click: **Add → Add workflow template**
3. Use **Workflow Visualizer** to recreate the structure
4. Or use API with `workflow_template_portworx_upgrade.json`

## Testing

### 1. Test Project Sync

```bash
awx projects update <project-id> --monitor
```

### 2. Test Job Template Launch

```bash
# Dry run with preflight only
awx job_templates launch <template-id> \
  --extra_vars '{"portworx_target_version": "3.5.0"}' \
  --tags preflight \
  --monitor
```

### 3. Verify Survey

1. Navigate to job template
2. Click **Launch**
3. Verify survey questions appear
4. Fill in test values
5. Do not launch (or use check mode)

## Troubleshooting

### Project Sync Fails

**Issue**: Project won't sync from Git

**Solutions**:
- Check SCM URL is correct
- Verify credential has access
- Check branch name
- Review project logs in AAP

### Job Template Launch Fails

**Issue**: Job fails immediately on launch

**Solutions**:
- Verify inventory exists and has `localhost`
- Check execution environment is available
- Verify credentials are assigned
- Check playbook path is correct

### Survey Not Showing

**Issue**: Survey doesn't appear on launch

**Solutions**:
- Ensure "Enable Survey" is checked
- Verify survey spec is valid JSON
- Re-import survey via API
- Check survey has at least one question

### Version File Missing

**Issue**: Role reports version file not found

**Solutions**:
- Version files must be downloaded manually to EE
- Add to custom EE build
- Or provide via extra vars with content

## Custom Execution Environment

For production use, build a custom EE with version files:

```dockerfile
# execution-environment.yml
version: 3
images:
  base_image:
    name: quay.io/ansible/ansible-runner:latest

dependencies:
  galaxy: requirements.yml
  python: requirements.txt
  system: bindep.txt

additional_build_files:
  - src: roles/portworx_upgrade/files/versions/
    dest: /runner/roles/portworx_upgrade/files/versions/
```

Build and push:
```bash
ansible-builder build -t quay.io/your-org/portworx-upgrade-ee:1.0.0
podman push quay.io/your-org/portworx-upgrade-ee:1.0.0
```

## Security Considerations

1. **Credentials**:
   - Use AAP vault for sensitive variables
   - Never commit credentials to Git
   - Rotate service account tokens regularly

2. **RBAC**:
   - Limit who can launch upgrade jobs
   - Use workflow approval gates for production
   - Audit job execution logs

3. **Execution Environment**:
   - Use trusted base images
   - Scan images for vulnerabilities
   - Version and track EE changes

## Support

For issues with AAP import:

1. Check AAP logs: `/var/log/tower/`
2. Review job output in AAP UI
3. Verify project sync logs
4. Check execution environment logs
5. Consult role README for role-specific issues

## References

- AAP Documentation: https://docs.ansible.com/automation-controller/
- AWX CLI: https://github.com/ansible/awx/tree/devel/awxkit
- Execution Environments: https://ansible.readthedocs.io/projects/builder/
- Role Documentation: `../roles/portworx_upgrade/README.md`
