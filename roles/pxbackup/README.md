# PX-Backup Role

This Ansible role manages cluster definitions in PX-Backup using HashiCorp Vault for secure kubeconfig storage and Portworx backup API for backup operations. The role is designed to be run from ansible-runner within a container environment. For each cluster, it:

1. Validates and processes cluster variables based on naming convention
2. Creates a service account with necessary RBAC permissions
3. Stores the service account kubeconfig in Vault
4. Creates/updates the cluster definition in PX-Backup using the service account kubeconfig
5. Configures backup schedules and policies through the Portworx backup API

## Execution Environment

This role requires a specific execution environment defined in `execution-environment.yml`:

- Base Image: CentOS Stream or Fedora Stream
- Container Runtime: Docker
- Ansible Navigator: Configured for Docker execution

## Requirements

- Ansible >= 2.14
- Python >= 3.9
- Access to PX-Backup API
- Access to HashiCorp Vault
- Access to Portworx backup API
- Required collections (installed in collections/):
  - community.hashi_vault
  - purepx.px_backup (for Portworx backup API interactions)
  - kubernetes.core
  - ansible.utils
  - community.general

## Directory Structure

```text
.
├── collections/          # Ansible collections directory
├── roles/               # Ansible roles directory
├── inventory/           # Inventory files
├── docs/               # Comprehensive documentation
├── tmp/                # Temporary files
├── cache/              # Cache files
└── execution-environment.yml  # Execution environment definition
```

## Role Variables

### Required Variables

```yaml
# Connection Configuration
validate_certs: true        # Validate SSL certificates

# PX-Backup Configuration
px_backup_api_url: "https://pxbackup.example.com"  # PX-Backup API endpoint
pxcentral_auth_url: "https://pxbackup.example.com/auth"  # Auth endpoint
pxcentral_client_id: "your-client-id"  # Client ID for PX-Backup authentication
pxcentral_username: "your-username"  # Username for PX-Backup authentication
pxcentral_password: "your-password"  # Password for PX-Backup authentication
org_id: "your-org-id"  # Organization ID in PX-Backup

# Vault Configuration
vault_address: "https://vault.example.com"  # Vault server address
vault_token: "your-vault-token"  # Vault authentication token
vault_token_path: "/run/secrets/vault-token"  # Path to Vault token file
vault_automation_default_namespace: "your-namespace"  # Default Vault namespace
vault_automation_config_path: "your/config/path/"  # Path for storing kubeconfig in Vault
vault_automation_config_mount_point: "secret"  # Vault mount point for secrets

# Environment-specific Vault addresses (at least one required)
vault_automation_prod_address: "https://vault-prod.example.com"
vault_automation_dev_address: "https://vault-dev.example.com"
vault_automation_stage_address: "https://vault-stage.example.com"
vault_automation_eng_address: "https://vault-eng.example.com"

# Inventory Configuration
inventory_url: "https://inventory.example.com"  # Inventory service URL

# Clusters Configuration
clusters:
  - name: "user-platform-env-region-id"  # Required: Must follow naming convention
    description: "Production Cluster 1"   # Optional: Cluster description
    cloud_type: "AWS"                    # Optional: AWS, AZURE, GCP, or OTHER (default: OTHER)
    cloud_credential_ref: "aws-cred-1"   # Optional: Cloud provider credential reference
    platform_credential_ref: "plat-1"    # Optional: Platform credential reference
    px_config:                          # Optional: Portworx configuration
      storage_classes: ["px-ha"]        # Optional: List of storage classes
      namespaces: ["app1", "app2"]      # Optional: List of namespaces
    service_token: ""                   # Optional: Pre-existing service token
    skip_sa_creation: false             # Optional: Skip service account creation
```

### Optional Variables

```yaml
# PX-Backup Optional Configuration
token_duration: "7d"        # Token validity duration
fail_on_cluster_error: true # Whether to fail role execution on cluster error

# Vault Optional Configuration
vault_cacert_path: ""       # Path to CA certificate for Vault
vault_namespace: ""         # Enterprise Vault namespace

# Kubernetes Configuration
k8s_ns: "portworx"                            # Namespace for resources (default: portworx)
service_account_name: "pxbackup-sa"           # Service account name (default: pxbackup-sa)
cluster_role_name: "pxbackup-cluster-role"    # Cluster role name (default: pxbackup-cluster-role)
sa_role_name: "pxbackup-role"                 # Namespaced role name (default: pxbackup-role)
cluster_role_binding_name: "pxbackup-cluster-rolebinding"  # Cluster role binding name
sa_role_binding_name: "pxbackup-rolebinding"  # Role binding name

# Backup Schedule Optional Configuration
backup_type: "Normal"                # Type of backup (default: Normal)
suspend: false                       # Whether to suspend the schedule (default: false)
direct_kdmp: false                  # Use direct KDMP (default: false)
skip_vm_auto_exec_rules: false      # Skip VM auto exec rules (default: false)
parallel_backup: false              # Enable parallel backup (default: false)
keep_cr_status: false              # Keep CR status (default: false)
ns_label_selectors: {}             # Namespace label selectors
exclude_resource_types: []         # Resource types to exclude
label_selectors: {}               # Label selectors for resources
include_resources: []             # Specific resources to include
backup_object_type: ""           # Backup object type
volume_snapshot_class_mapping: {} # Volume snapshot class mapping
csi_snapshot_class_name: ""      # CSI snapshot class name
pre_exec_rule_ref: {}           # Pre-execution rule reference
post_exec_rule_ref: {}          # Post-execution rule reference
ownership: {}                   # Backup ownership configuration
```

## Cluster Naming Convention

Clusters must follow this naming format:

```text
<cluster_user>-<platform>-<env>-<region><zone>-<id>
```

Example: `ansible-infrastructure-d-eusw1a-4`

- cluster_user: ansible
- platform: infrastructure
- env: d (dev), p (prod), t (test)
- region: eusw1
- zone: a (zone-a), b (zone-b), c (zone-c)
- id: 4

## Process Flow

1. Initial Setup and Validation:
   - Validates required variables (API URLs, credentials, org_id)
   - Checks SSL certificates and CA paths
   - Validates Vault token file existence and permissions
   - Sets up temporary directories in tmp/ for kubeconfig handling

2. Cluster Variable Processing:
   - Validates cluster name format against strict pattern
   - Parses cluster name into components (user, platform, env, region, zone)
   - Determines environment type (prod, dev, test)
   - Sets environment-specific Vault configurations
   - Retrieves cluster information from inventory service

3. Vault Integration Flow:
   - Uses ansible.builtin.stat to validate Vault token file permissions
   - Uses community.hashi_vault collection for Vault operations
   - Determines correct Vault path based on environment
   - Retrieves master kubeconfig from appropriate path
   - Handles Vault namespace and mount point selection

4. Kubernetes Resource Management:
   - Uses kubernetes.core collection for all Kubernetes operations
   - Creates dedicated namespace if not exists
   - Generates service account with minimal permissions
   - Creates role with required PX-Backup permissions
   - Sets up role bindings for proper authorization
   - Generates and validates service account token

5. PX-Backup Integration:
   - Uses purepx.px_backup collection for API interactions
   - Authenticates with PX-Backup using provided credentials
   - Validates organization access and permissions
   - Creates or updates cluster definition
   - Configures backup settings and storage classes
   - Sets up cloud provider integration if specified

6. Error Handling and Cleanup:
   - Implements proper error handling at each stage
   - Cleans up temporary files and resources
   - Provides detailed error messages and logging
   - Handles SSL/TLS verification failures
   - Manages token expiration and renewal

## Security Considerations

1. Authentication and Authorization:
   - Secure handling of PX-Backup credentials
   - Token-based authentication for service accounts
   - Role-based access control (RBAC) implementation
   - Minimal permission principle for service accounts
   - Regular token rotation and expiration handling

2. Vault Security:
   - Secure token file handling with strict permissions
   - Environment-specific Vault paths and namespaces
   - SSL/TLS certificate validation
   - Secure storage of sensitive kubeconfig data
   - Proper error handling for Vault operations

3. Data Protection:
   - No sensitive data in logs (no_log: true)
   - Secure temporary file handling
   - Proper cleanup of sensitive data
   - Encrypted communication channels
   - Protected kubeconfig storage

4. Network Security:
   - SSL/TLS verification for all API communications
   - Support for custom CA certificates
   - Secure handling of endpoints and URLs
   - Proper validation of SSL certificates
   - Protection against man-in-the-middle attacks
  
5. Operational Security:
   - Environment isolation (prod/dev/test)
   - Audit logging of operations
   - Proper error handling and reporting
   - Secure variable handling
   - Configuration validation

6. Compliance Features:
   - Supports enterprise security requirements
   - Audit trail for cluster operations
   - Secure secret management
   - Environment-specific configurations
   - Role-based access control

7. Best Practices:
   - No hardcoded secrets
   - Proper error handling
   - Secure default configurations
   - Regular security updates
   - Documentation of security features

## Example Playbook

```yaml
---
- name: Configure PX-Backup Clusters
  hosts: localhost
  gather_facts: false
  collections:
    - community.hashi_vault
    - purepx.px_backup
    - kubernetes.core
    - ansible.utils
    - community.general
  
  roles:
    - role: pxbackup
      vars:
        # Connection Configuration
        validate_certs: true
        ca_cert_path: "/etc/ssl/certs/ca-certificates.crt"

        # PX-Backup Configuration
        px_backup_api_url: "https://pxbackup.example.com"
        pxcentral_auth_url: "https://pxbackup.example.com/auth"
        pxcentral_client_id: "px-backup-client"
        pxcentral_username: "admin"
        pxcentral_password: "{{ vault_pxcentral_password }}"
        org_id: "default"

        # Vault Configuration
        vault_token_path: "/run/secrets/vault-token"
        vault_automation_prod_address: "https://vault-prod.example.com"
        vault_automation_dev_address: "https://vault-dev.example.com"
        vault_automation_default_namespace: "automation"
        vault_automation_config_path: "kubernetes/"
        vault_automation_config_mount_point: "secret"

        # Cluster Configuration
        clusters:
          - name: "user1-platform-p-usw2a-1"
            description: "Production Cluster US West 2 Zone A"
            cloud_type: "AWS"
            px_config:
              storage_classes:
                - "portworx-db-sc"
                - "portworx-file-sc"
              namespaces:
                - "prod-apps"
                - "monitoring"

        # Backup Schedule Configuration
        backup_schedules:
          - name: "daily-prod-apps"
            backup_location: "aws-s3-backup"
            schedule_policy: "daily-30d-retention"
            cluster: "user1-platform-p-usw2a-1"
            resource_types:
              - "apps/v1/Deployment"
              - "apps/v1/StatefulSet"
              - "v1/ConfigMap"
              - "v1/Secret"
            reclaim_policy: "Retain"
            backup_type: "Normal"
            ns_label_selectors: "environment=prod,tier=application"
```

## Example Configuration

### Example extra_vars.json

```json
{
  "px_backup_api_url": "https://pxbackup.example.com",
  "pxcentral_auth_url": "https://pxbackup.example.com/auth",
  "pxcentral_client_id": "px-backup-client",
  "pxcentral_username": "admin",
  "pxcentral_password": "{{ vault_pxcentral_password }}",
  "token_duration": "7d",
  "org_id": "default",

  "vault_token_path": "/run/secrets/vault-token",
  "vault_automation_prod_address": "https://vault-prod.example.com",
  "vault_automation_dev_address": "https://vault-dev.example.com",
  "vault_automation_stage_address": "https://vault-stage.example.com",
  "vault_automation_eng_address": "https://vault-eng.example.com",
  "vault_automation_default_namespace": "automation",
  "vault_automation_config_path": "kubernetes/",
  "vault_automation_config_mount_point": "secret",

  "k8s_ns": "portworx",
  "service_account_name": "pxbackup-sa",
  "validate_certs": true,
  "ca_cert_path": "/etc/ssl/certs/ca-certificates.crt",

  "clusters": [
    {
      "name": "user1-platform-p-usw2a-1",
      "description": "Production Cluster US West 2 Zone A",
      "cloud_type": "AWS",
      "px_config": {
        "storage_classes": [
          "portworx-db-sc",
          "portworx-file-sc"
        ],
        "namespaces": [
          "prod-apps",
          "monitoring"
        ]
      }
    }
  ],

  "backup_schedules": [
    {
      "name": "daily-prod-apps",
      "backup_location": "aws-s3-backup",
      "schedule_policy": "daily-30d-retention",
      "cluster": "user1-platform-p-usw2a-1",
      "ns_label_selectors": "environment=prod,tier=application",
      "resource_types": [
        "apps/v1/Deployment",
        "apps/v1/StatefulSet",
        "v1/ConfigMap",
        "v1/Secret"
      ],
      "reclaim_policy": "Retain",
      "backup_type": "Normal"
    }
  ]
}
```

## Running the Role

### Using ansible-playbook

1. Direct execution with extra vars:

```bash
ansible-playbook -i inventory/hosts.yml playbook.yml \
  --extra-vars "@extra_vars.json" \
  --extra-vars "validate_certs=true" \
  -v
```

2. Check mode (dry run):

```bash
ansible-playbook -i inventory/hosts.yml playbook.yml \
  --extra-vars "@extra_vars.json" \
  --check \
  -v
```

3. Using vault-encrypted variables:

```bash
ansible-playbook -i inventory/hosts.yml playbook.yml \
  --extra-vars "@extra_vars.json" \
  --vault-password-file /path/to/vault-password \
  -v
```

4. Using tags to run specific tasks:

```bash
ansible-playbook -i inventory/hosts.yml playbook.yml \
  --extra-vars "@extra_vars.json" \
  --tags "setup,backup" \
  -v
```

### Using ansible-runner

1. Basic execution:

```bash
ansible-runner run /path/to/project \
  -p playbook.yml \
  --container-runtime docker \
  -v
```

2. With private data directory:

```bash
ansible-runner run /path/to/project \
  -p playbook.yml \
  --container-runtime docker \
  --private-data-dir /path/to/private \
  -v
```

3. With specific inventory:

```bash
ansible-runner run /path/to/project \
  -p playbook.yml \
  --container-runtime docker \
  --inventory /path/to/inventory \
  -v
```

4. With environment variables:

```bash
ansible-runner run /path/to/project \
  -p playbook.yml \
  --container-runtime docker \
  -e ANSIBLE_CONFIG=/path/to/ansible.cfg \
  -e ANSIBLE_VAULT_PASSWORD_FILE=/path/to/vault-password \
  -v
```

### Project Directory Structure for ansible-runner

```text
/path/to/project/
├── env/                    # Environment variables and settings
│   └── envvars            # Environment variables file
├── inventory/             # Inventory files
│   └── hosts.yml         # Inventory definitions
├── project/              # Project files
│   ├── roles/           # Roles directory
│   │   └── pxbackup/    # PX-Backup role
│   ├── collections/     # Collections directory
│   ├── playbook.yml    # Main playbook
│   └── extra_vars.json # Variables file
└── tmp/                 # Temporary files (created by role)
```

## License

Apache-2.0
