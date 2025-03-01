# PX-Backup Role

This Ansible role manages cluster definitions in PX-Backup using Vault for secure kubeconfig storage. For each cluster, it:

1. Validates and processes cluster variables based on naming convention
2. Creates a service account with necessary RBAC permissions
3. Stores the service account kubeconfig in Vault
4. Creates/updates the cluster definition in PX-Backup using the service account kubeconfig

## Requirements

- Ansible >= 2.14
- Python >= 3.9
- Access to PX-Backup API
- Access to HashiCorp Vault
- Required collections:
  - community.hashi_vault
  - purepx.px_backup
  - kubernetes.core
  - ansible.utils
  - community.general

## Role Variables

### Required Variables

```yaml
# PX-Backup Configuration
px_backup_api_url: "https://pxbackup.example.com"  # PX-Backup API endpoint
pxcentral_auth_url: "https://pxbackup.example.com/auth"  # Auth endpoint
pxcentral_client_id: "your-client-id"
pxcentral_username: "your-username"
pxcentral_password: "your-password"
org_id: "your-org-id"

# Vault Configuration
vault_address: "https://vault.example.com"  # Vault server address
vault_token_path: "/run/secrets/vault-token"  # Path to Vault token file
vault_automation_default_namespace: "your-namespace"
vault_automation_config_path: "your/config/path/"
vault_automation_config_mount_point: "secret"

# Environment-specific Vault addresses
vault_automation_prod_address: "https://vault-prod.example.com"
vault_automation_dev_address: "https://vault-dev.example.com"
vault_automation_stage_address: "https://vault-stage.example.com"
vault_automation_eng_address: "https://vault-eng.example.com"

# Inventory Configuration
inventory_url: "https://inventory.example.com"  # Inventory service URL

# Clusters Configuration
clusters:
  - name: "user-platform-env-region-id"  # Must follow naming convention
    description: "Production Cluster 1"   # Optional
    cloud_type: "AWS"                    # Optional: AWS, AZURE, GCP, or OTHER
    cloud_credential_ref: "aws-cred-1"   # Optional
    platform_credential_ref: "plat-1"    # Optional
    px_config:                          # Optional
      storage_classes: ["px-ha"]        # Optional: List of storage classes
      namespaces: ["app1", "app2"]      # Optional: List of namespaces
    service_token: ""                   # Optional: Pre-existing token
    skip_sa_creation: false             # Optional: Skip SA creation
```

### Optional Variables

```yaml
# PX-Backup Optional Configuration
pxcentral_verify_ssl: true  # Verify SSL certificates
token_duration: "7d"        # Token validity duration

# Vault Optional Configuration
validate_certs: true        # Validate Vault SSL certificates
vault_cacert_path: ""       # Path to CA certificate
vault_namespace: ""         # Enterprise Vault namespace

# Kubernetes Configuration
k8s_ns: "portworx"                            # Namespace for resources
service_account_name: "pxbackup-sa"           # Service account name
cluster_role_name: "pxbackup-cluster-role"    # Cluster role name
sa_role_name: "pxbackup-role"                 # Namespaced role name
cluster_role_binding_name: "pxbackup-cluster-rolebinding"
sa_role_binding_name: "pxbackup-rolebinding"
outp_k8s_config_path: "/tmp/k8s"             # Temp kubeconfig path
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
   - Sets up temporary directories for kubeconfig handling

2. Cluster Variable Processing:
   - Validates cluster name format against strict pattern
   - Parses cluster name into components (user, platform, env, region, zone)
   - Determines environment type (prod, dev, test)
   - Sets environment-specific Vault configurations
   - Retrieves cluster information from inventory service

3. Vault Integration Flow:
   - Validates Vault token file permissions and content
   - Determines correct Vault path based on environment
   - Retrieves master kubeconfig from appropriate path
   - Handles Vault namespace and mount point selection
   - Manages SSL certificate validation for Vault communication

4. Kubernetes Resource Management:
   - Creates dedicated namespace if not exists
   - Generates service account with minimal permissions
   - Creates role with required PX-Backup permissions
   - Sets up role bindings for proper authorization
   - Generates and validates service account token
   - Creates secure kubeconfig with token authentication

5. PX-Backup Integration:
   - Authenticates with PX-Backup using provided credentials
   - Validates organization access and permissions
   - Creates or updates cluster definition
   - Configures backup settings and storage classes
   - Validates cluster connection and accessibility
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
  
  roles:
    - role: pxbackup
      vars:
        px_backup_api_url: "https://pxbackup.example.com"
        pxcentral_auth_url: "https://pxbackup.example.com/auth"
        org_id: "your-org-id"
        clusters:
          - name: "user1-k8s-p-eusw1a-1"
            description: "Production Cluster"
            cloud_type: "AWS"
            cloud_credential_ref: "aws-prod-1"
            px_config:
              storage_classes: ["px-ha"]
              namespaces: ["app1", "app2"]
          - name: "user2-k8s-d-eusw1b-2"
            description: "Development Cluster"
            cloud_type: "AZURE"
            cloud_credential_ref: "azure-dev-1"
```

## License

Apache-2.0
