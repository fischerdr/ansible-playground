# vault_fix_portworx

Configures HashiCorp Vault integration for Portworx clusters running on Kubernetes/OpenShift.

## Description

This role automates the setup of Vault authentication and authorization for Portworx storage clusters. It creates necessary Vault namespaces, policies, and Kubernetes authentication configurations to enable Portworx to securely access secrets stored in Vault.

## Requirements

- Ansible Core 2.18.4+
- Python 3.11+
- Collections:
  - `community.hashi_vault` >= 6.0.0
  - `kubernetes.core` >= 3.0.0
- Valid Vault authentication token with admin privileges
- Kubernetes/OpenShift cluster access
- Portworx deployed or ready to deploy

## Role Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `cluster_user` | Cluster user identifier | `cld`, `hub`, `hzn` |
| `cluster_env` | Environment code | `l`, `d`, `t`, `p` |
| `cluster_tenant` | Tenant identifier | `shared`, `ampz` |
| `cluster_datacenter` | Datacenter code | `phx`, `slc` |
| `cluster_region` | Region type | `internet`, `intranet` |
| `vault_address` | Vault server URL | `https://vault.example.com` |
| `vault_token` | Vault authentication token | (secret) |
| `vault_vars` | Dictionary of Vault configuration | See below |
| `network` | Dictionary with cluster network info | See below |

### vault_vars Structure

```yaml
vault_vars:
  ADDRESS: "https://vault.example.com"
  PARENT_NAMESPACE: "parent-namespace"
  VAULT_NS: "parent-namespace-user-tenant-env-dc"
  VAULT_SECRET_NAMESPACE: "secret-namespace"  # Optional: namespace for secret lookups
  VAULT_SECRET_PATH: "static_secrets/data/env"  # Optional: KV path prefix
  VAULT_KV_MOUNT: "static_secrets"  # Optional: KV mount point
  K8S_PATH: "k8s-user-tenant-env-dc"
```

### network Structure

```yaml
network:
  master:
    cname: "api.cluster.example.com"
```

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `storage_namespace` | `portworx` | Kubernetes namespace for storage solution |
| `ldap_group_name` | (empty) | LDAP group for Vault access control |
| `over_write` | `false` | Force policy updates |
| `s3_endpoint_map` | See defaults | Environment-to-S3-endpoint mapping |
| `s3_bucket_map` | See defaults | Environment-to-S3-bucket mapping |

## Dependencies

None.

## Example Playbook

```yaml
---
- name: Configure Vault for Storage Solution
  hosts: localhost
  gather_facts: false

  vars:
    cluster_user: myuser
    cluster_env: p
    cluster_tenant: shared
    cluster_datacenter: dc1
    cluster_region: internet
    vault_address: "https://vault.example.com"
    vault_token: "{{ lookup('env', 'VAULT_TOKEN') }}"

    # Optional: Override S3 configuration
    s3_endpoint_map:
      l: "s3-local.example.com"
      d: "s3-dev.example.com"
      t: "s3-test.example.com"
      p: "s3-prod.example.com"

    s3_bucket_map:
      l: "storage-backup-local"
      d: "storage-backup-dev"
      t: "storage-backup-test"
      p: "storage-backup-prod"

    # Optional: Set LDAP group for access control
    ldap_group_name: "vault-storage-admins"

    vault_vars:
      ADDRESS: "https://vault.example.com"
      PARENT_NAMESPACE: "my-org"
      VAULT_NS: "my-org-myuser-shared-p-dc1"
      VAULT_SECRET_NAMESPACE: "secrets"
      VAULT_SECRET_PATH: "kv/data/env"
      K8S_PATH: "k8s-myuser-shared-p-dc1"

    network:
      master:
        cname: "api.cluster.example.com"

  roles:
    - vault_fix_portworx
```

## Tasks Overview

The role performs the following operations:

1. **Vault Login**: Authenticates to Vault using LDAP credentials
2. **Namespace Setup**: Creates Vault child namespaces for storage solution
3. **Policy Configuration**: Applies Vault policies for resource access control
4. **Kubernetes Resources**: Creates ServiceAccount, ClusterRoleBinding, and Secrets
5. **Vault Auth Backend**: Configures Kubernetes authentication in Vault
6. **Vault Roles**: Creates Vault roles bound to Kubernetes ServiceAccounts

## Templates

The role includes HCL policy templates for:

- `role-config.json.j2`: Kubernetes role configuration
- `cluster-policy-template.hcl.j2`: Cluster-level Vault policy
- `storage-policy-template.hcl.j2`: Storage-specific Vault policy
- `storage-child-ns-prod-policy-template.hcl.j2`: Production namespace policy
- `storage-child-ns-nonprod-policy-template.hcl.j2`: Non-production namespace policy
- `child-ns-storage-engine-prod-policy-template.hcl.j2`: Production engine policy
- `child-ns-storage-engine-nonprod-policy-template.hcl.j2`: Non-production engine policy

## Tags

Available tags for selective execution:

- `vault`: All Vault operations
- `k8s`: All Kubernetes operations
- `login`: Vault authentication only
- `namespace`: Namespace operations
- `policy`: Policy configuration
- `secret`: Secret creation
- `auth`: Authentication backend setup
- `role`: Vault role configuration

Example:
```bash
ansible-playbook playbook.yml --tags vault,k8s
```

## Security Considerations

- All sensitive operations use `no_log: true` to prevent credential exposure
- TLS certificate validation is enforced (`validate_certs: true`)
- Credentials are retrieved from Vault KV secrets engine
- ServiceAccount tokens are used for Kubernetes authentication
- Least-privilege policies are applied based on environment

## Customization

This role is designed to be generic and reusable. To adapt it for your organization:

1. Override the `s3_endpoint_map` and `s3_bucket_map` variables with your infrastructure endpoints
2. Set `ldap_group_name` to your organization's LDAP/AD group
3. Configure `vault_vars.VAULT_SECRET_NAMESPACE` and `vault_vars.VAULT_SECRET_PATH` to match your Vault KV structure
4. Customize namespace construction logic in `defaults/main.yml` if needed
5. Modify HCL policy templates in `templates/` to match your security requirements

## License

MIT

## Author Information

Originally developed for enterprise Ansible Automation Platform deployments.
Genericized for community use.
