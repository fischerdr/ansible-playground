# Backup Schedule Playbooks Documentation

This document describes the usage and configuration of the PX-Backup schedule creation playbooks.

## Table of Contents

- [Backup Schedule Playbooks Documentation](#backup-schedule-playbooks-documentation)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Prerequisites](#prerequisites)
  - [Available Playbooks](#available-playbooks)
  - [Single Backup Schedule](#single-backup-schedule)
    - [Required Variables](#required-variables)
    - [Optional Variables](#optional-variables)
    - [Usage Examples](#usage-examples)
  - [Multiple Backup Schedules](#multiple-backup-schedules)
    - [Schedule List Format](#schedule-list-format)
    - [Multiple Schedule Usage Examples](#multiple-schedule-usage-examples)
  - [Best Practices](#best-practices)
  - [Security Considerations](#security-considerations)

## Overview

These playbooks automate the creation of backup schedules in PX-Backup. They support both single schedule creation and bulk schedule creation with comprehensive configuration options.

## Prerequisites

- PX-Backup >= 2.8.3
- Stork >= 24.3.3
- Python >= 3.9
- Access to PX-Backup API
- Valid authentication token
- Existing schedule policies
- Existing backup locations
- Registered clusters

## Available Playbooks

1. `pxbkup_create_backupsched.yaml`: Creates a single backup schedule
2. `pxbkup_create_multiple_backupscheds.yaml`: Creates multiple backup schedules from a list

## Single Backup Schedule

### Required Variables

```yaml
# Authentication and Connection
px_backup_api_url: "https://px-backup.example.com"  # PX-Backup API URL
px_backup_token: "your-token"                       # Authentication token
validate_certs: true                                # Whether to validate SSL certificates

# Organization
org_id: "your-org-id"                              # Organization ID

# Schedule Identifiers
backup_schedule_name: "daily-backup"                # Name for the new backup schedule
schedule_policy_name: "daily-retention-30d"         # Name of existing schedule policy
backup_location_name: "s3-backup"                   # Name of existing backup location
cluster_name: "prod-cluster"                        # Name of existing cluster

# Backup Configuration
backup_resource_types:                              # List of resource types to backup
  - "apps/v1/Deployment"
  - "v1/ConfigMap"
```

### Optional Variables

```yaml
# Basic Options
backup_type: "Normal"                               # Backup type (Normal, Generic)
backup_suspend: false                               # Whether to suspend the schedule
backup_direct_kdmp: false                          # Enable direct KDMP backup
backup_skip_vm_auto_exec_rules: false              # Skip VM auto exec rules
backup_parallel: false                              # Enable parallel backups
backup_keep_cr_status: false                       # Keep CR status
backup_reclaim_policy: "Delete"                    # Policy for backup retention

# Resource Selection
backup_namespaces:                                 # List of namespaces to backup
  - "namespace1"
  - "namespace2"
backup_exclude_resource_types:                     # Resource types to exclude
  - "type1"
  - "type2"
backup_label_selectors:                           # Label selectors for filtering
  app: "myapp"
  env: "prod"
backup_ns_label_selectors: "app=myapp,env=prod"   # Namespace label selectors

# Resource Inclusion
backup_include_resources:                          # Specific resources to include
  - name: "resource1"
    namespace: "ns1"
    group: "apps"
    kind: "Deployment"
    version: "v1"

# Backup Object Configuration
backup_object_type: "All"                         # Backup object type
backup_volume_snapshot_class_mapping:             # Volume snapshot class mappings
  class1: "snap1"
  class2: "snap2"
backup_csi_snapshot_class_name: "csi-snap-class"  # CSI snapshot class name

# Rule References
pre_exec_rule_ref:                               # Pre-execution rule reference
  name: "pre-rule"
  uid: "pre-rule-uid"
post_exec_rule_ref:                              # Post-execution rule reference
  name: "post-rule"
  uid: "post-rule-uid"

# Ownership Configuration
backup_ownership:                                 # Ownership configuration
  owner: "admin"
  groups:
    - id: "group1"
      access: "Read"
  collaborators:
    - id: "user1"
      access: "Write"
  public:
    access: "Read"
```

### Usage Examples

Using command line:

```bash
# Minimal required variables
ansible-playbook pxbkup_create_backupsched.yaml \
  -e px_backup_api_url="https://px-backup.example.com" \
  -e px_backup_token="your-token" \
  -e validate_certs=true \
  -e org_id="your-org-id" \
  -e backup_schedule_name="daily-backup" \
  -e schedule_policy_name="daily-retention-30d" \
  -e backup_location_name="s3-backup" \
  -e cluster_name="prod-cluster" \
  -e '{"backup_resource_types": ["apps/v1/Deployment", "v1/ConfigMap"]}'

# With optional variables
ansible-playbook pxbkup_create_backupsched.yaml \
  -e px_backup_api_url="https://px-backup.example.com" \
  -e px_backup_token="your-token" \
  -e validate_certs=true \
  -e org_id="your-org-id" \
  -e backup_schedule_name="daily-backup" \
  -e schedule_policy_name="daily-retention-30d" \
  -e backup_location_name="s3-backup" \
  -e cluster_name="prod-cluster" \
  -e '{"backup_resource_types": ["apps/v1/Deployment", "v1/ConfigMap"]}' \
  -e backup_type="Normal" \
  -e backup_parallel=true \
  -e backup_reclaim_policy="Delete" \
  -e '{"backup_namespaces": ["namespace1", "namespace2"]}' \
  -e 'backup_ns_label_selectors="app=myapp,env=prod"'
```

Using variables file:

```yaml
# vars.yml
px_backup_api_url: "https://px-backup.example.com"
px_backup_token: "your-token"
validate_certs: true
org_id: "your-org-id"
backup_schedule_name: "daily-backup"
schedule_policy_name: "daily-retention-30d"
backup_location_name: "s3-backup"
cluster_name: "prod-cluster"
backup_resource_types:
  - "apps/v1/Deployment"
  - "v1/ConfigMap"
backup_namespaces:
  - "namespace1"
  - "namespace2"
backup_ns_label_selectors: "app=myapp,env=prod"
```

```bash
ansible-playbook pxbkup_create_backupsched.yaml -e @vars.yml
```

## Multiple Backup Schedules

### Schedule List Format

```yaml
backup_schedules:
  - name: "daily-backup-app1"
    backup_location: "s3-backup-location"
    schedule_policy: "daily-retention-30d"
    cluster: "prod-cluster-1"
    ns_label_selectors: "app=app1"
    resource_types:
      - "apps/v1/Deployment"
      - "v1/ConfigMap"
  
  - name: "weekly-backup-app2"
    backup_location: "azure-backup-location"
    schedule_policy: "weekly-retention-90d"
    cluster: "prod-cluster-2"
    ns_label_selectors: "environment=prod,app=app2"
    resource_types:
      - "apps/v1/StatefulSet"
      - "v1/Secret"
```

Each schedule in the list supports all the same optional parameters as the single schedule playbook.

### Multiple Schedule Usage Examples

Using variables file:

```yaml
# multiple_schedules_vars.yml
px_backup_api_url: "https://px-backup.example.com"
px_backup_token: "your-token"
validate_certs: true
org_id: "your-org-id"
backup_schedules:
  - name: "daily-backup-app1"
    backup_location: "s3-backup-location"
    schedule_policy: "daily-retention-30d"
    cluster: "prod-cluster-1"
    ns_label_selectors: "app=app1"
    resource_types:
      - "apps/v1/Deployment"
      - "v1/ConfigMap"
  
  - name: "weekly-backup-app2"
    backup_location: "azure-backup-location"
    schedule_policy: "weekly-retention-90d"
    cluster: "prod-cluster-2"
    ns_label_selectors: "environment=prod,app=app2"
    resource_types:
      - "apps/v1/StatefulSet"
      - "v1/Secret"
```

```bash
ansible-playbook pxbkup_create_multiple_backupscheds.yaml -e @multiple_schedules_vars.yml
```

## Best Practices

1. **Security**:
   - Store sensitive data (tokens, credentials) in Ansible Vault or environment variables
   - Use HTTPS for API communication
   - Enable SSL certificate validation

2. **Variable Management**:
   - Use descriptive variable names in snake_case
   - Group related variables in separate files
   - Document all variable requirements

3. **Error Handling**:
   - Validate all required variables before execution
   - Include proper error messages
   - Use rescue blocks for error recovery

4. **Maintenance**:
   - Keep schedule configurations in version control
   - Document all schedule configurations
   - Use consistent naming conventions

## Security Considerations

1. **Authentication**:
   - Secure the PX-Backup token
   - Rotate tokens regularly
   - Use minimal required permissions

2. **Network Security**:
   - Use HTTPS for API communication
   - Validate SSL certificates
   - Restrict API access to necessary networks

3. **Access Control**:
   - Use proper ownership settings
   - Implement least privilege access
   - Regular access review
