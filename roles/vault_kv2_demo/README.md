# vault_kv2_demo

Comprehensive demonstration role for HashiCorp Vault integration with Kubernetes authentication and KV2 secret engine operations.

## Description

This Ansible role provides a complete example of integrating HashiCorp Vault with Kubernetes, demonstrating:

- **Vault Namespace Configuration**: Creates and configures Vault namespaces (Enterprise feature)
- **Kubernetes Authentication**: Sets up K8s service accounts and configures Vault K8s auth method
- **KV2 Secret Engine**: Enables and configures a KV version 2 secret engine
- **Secret Operations**: Writes example secrets to Vault and reads them back for validation
- **Authentication Testing**: Validates K8s authentication by obtaining and using Vault tokens
- **Cleanup Operations**: Optional cleanup of all created resources

## Requirements

### Ansible Collections

- `community.hashi_vault` >= 5.0.0
- `kubernetes.core` >= 3.0.0

Install collections:

```bash
ansible-galaxy collection install -r requirements.yml
```

### External Dependencies

- **HashiCorp Vault**: Vault server (OSS or Enterprise) accessible via HTTPS
- **Kubernetes Cluster**: Running cluster with appropriate RBAC permissions
- **Vault Root/Admin Token**: Token with permissions to create namespaces, auth methods, policies, and secret engines
- **Network Connectivity**: Ansible controller must be able to reach both Vault and Kubernetes API servers

### Permissions Required

#### Vault Permissions
- `sys/auth/*` - Enable authentication methods
- `sys/mounts/*` - Enable secret engines
- `sys/policy/*` - Create and manage policies
- `sys/namespaces/*` - Create namespaces (Enterprise only)
- `auth/kubernetes/*` - Configure Kubernetes auth
- Secret engine paths - Read/write to KV2 paths

#### Kubernetes Permissions
- Create/delete ServiceAccounts
- Create/delete Secrets
- Create/delete ClusterRoleBindings
- Read ServiceAccount tokens

## Role Variables

### Required Variables

```yaml
# Vault server address
vault_kv2_demo_vault_addr: "https://vault.example.com:8200"

# Vault root/admin token (encrypt with Ansible Vault)
vault_kv2_demo_root_token: "hvs.XXXXXXXXXXXXX"

# Kubernetes API server address for Vault auth configuration
vault_kv2_demo_k8s_host: "https://kubernetes.default.svc:443"
```

### Optional Variables

#### Vault Configuration

```yaml
# Vault namespace (Enterprise feature - leave empty for OSS)
vault_kv2_demo_vault_namespace: "demo"

# SSL certificate validation
vault_kv2_demo_validate_certs: true
vault_kv2_demo_ca_cert: ""

# Kubernetes auth mount path
vault_kv2_demo_k8s_auth_path: "kubernetes"

# KV2 engine mount path
vault_kv2_demo_kv2_mount_path: "demo-secrets"

# KV2 engine configuration
vault_kv2_demo_kv2_max_versions: 10
vault_kv2_demo_kv2_cas_required: false
vault_kv2_demo_kv2_delete_version_after: "0s"
```

#### Kubernetes Configuration

```yaml
# Kubernetes namespace for service account
vault_kv2_demo_k8s_namespace: "default"

# Service account name
vault_kv2_demo_service_account_name: "vault-auth-demo"

# Service account token secret name
vault_kv2_demo_sa_token_secret_name: "vault-auth-demo-token"

# Optional kubeconfig path
vault_kv2_demo_kubeconfig: ""

# Kubernetes SSL settings
vault_kv2_demo_k8s_verify_ssl: true
vault_kv2_demo_k8s_ssl_ca_cert: ""
```

#### Vault Role Configuration

```yaml
# Vault role name for K8s authentication
vault_kv2_demo_vault_role_name: "demo-role"

# Token TTL settings
vault_kv2_demo_vault_role_ttl: "1h"
vault_kv2_demo_vault_role_max_ttl: "24h"

# Additional policies to attach to the role
vault_kv2_demo_vault_role_policies:
  - default
  - demo-policy
```

#### Secret Data Configuration

```yaml
# List of secrets to create (override to customize)
vault_kv2_demo_secrets:
  - path: "applications/webapp"
    data:
      database_url: "postgresql://localhost:5432/webapp"
      database_username: "webapp_user"
      database_password: "changeme_webapp_password"
  - path: "applications/backend"
    data:
      redis_host: "redis.example.com"
      redis_password: "changeme_redis_password"
```

#### Operational Settings

```yaml
# Validate secrets after writing
vault_kv2_demo_validate_secrets: true

# Display secret data in output (use cautiously)
vault_kv2_demo_display_secrets: false

# Clean up all resources after completion
vault_kv2_demo_cleanup: false

# Retry settings for API operations
vault_kv2_demo_retries: 3
vault_kv2_demo_retry_delay: 5
vault_kv2_demo_request_timeout: 30
```

## Dependencies

No role dependencies. Requires the collections listed in the Requirements section.

## Example Playbook

### Basic Usage

```yaml
---
- name: Demonstrate Vault KV2 integration with Kubernetes
  hosts: localhost
  gather_facts: false

  vars:
    vault_kv2_demo_vault_addr: "https://vault.example.com:8200"
    vault_kv2_demo_root_token: "{{ vault_root_token }}"  # Store in Ansible Vault
    vault_kv2_demo_k8s_host: "https://10.0.0.1:6443"
    vault_kv2_demo_vault_namespace: "demo"

  roles:
    - vault_kv2_demo
```

### With Custom Secrets

```yaml
---
- name: Vault demo with custom secrets
  hosts: localhost
  gather_facts: false

  vars:
    vault_kv2_demo_vault_addr: "https://vault.example.com:8200"
    vault_kv2_demo_root_token: "{{ vault_root_token }}"
    vault_kv2_demo_k8s_host: "https://kubernetes.default.svc:443"

    # Custom secret paths and data
    vault_kv2_demo_secrets:
      - path: "myapp/production"
        data:
          db_host: "prod-db.example.com"
          db_password: "secure_password_123"
          api_key: "prod-api-key-xyz"

      - path: "myapp/staging"
        data:
          db_host: "staging-db.example.com"
          db_password: "staging_password_456"
          api_key: "staging-api-key-abc"

  roles:
    - vault_kv2_demo
```

### With Cleanup Enabled

```yaml
---
- name: Vault demo with cleanup
  hosts: localhost
  gather_facts: false

  vars:
    vault_kv2_demo_vault_addr: "https://vault.example.com:8200"
    vault_kv2_demo_root_token: "{{ vault_root_token }}"
    vault_kv2_demo_k8s_host: "https://kubernetes.default.svc:443"
    vault_kv2_demo_cleanup: true  # Clean up after demonstration

  roles:
    - vault_kv2_demo
```

### Vault OSS (No Namespace Support)

```yaml
---
- name: Vault demo with OSS (no namespace)
  hosts: localhost
  gather_facts: false

  vars:
    vault_kv2_demo_vault_addr: "https://vault.example.com:8200"
    vault_kv2_demo_root_token: "{{ vault_root_token }}"
    vault_kv2_demo_k8s_host: "https://kubernetes.default.svc:443"
    vault_kv2_demo_vault_namespace: ""  # Empty for Vault OSS

  roles:
    - vault_kv2_demo
```

### With Tag-Based Execution

```yaml
---
- name: Vault demo - specific operations only
  hosts: localhost
  gather_facts: false

  vars:
    vault_kv2_demo_vault_addr: "https://vault.example.com:8200"
    vault_kv2_demo_root_token: "{{ vault_root_token }}"
    vault_kv2_demo_k8s_host: "https://kubernetes.default.svc:443"

  roles:
    - vault_kv2_demo

  tags:
    - kv2
    - write
```

Available tags:
- `validation` - Input validation only
- `kubernetes` - Kubernetes resource operations
- `serviceaccount` - Service account creation
- `vault` - All Vault operations
- `namespace` - Vault namespace configuration
- `auth` - Authentication setup
- `kv2` - KV2 engine operations
- `secrets` - Secret operations
- `write` - Write secrets
- `read` - Read secrets
- `validate` - Validate secrets
- `test` - Test authentication
- `cleanup` - Cleanup resources (use with `--tags cleanup`)

## community.hashi_vault Modules Used

This role demonstrates proper use of the `community.hashi_vault` collection:

### Core Modules
- **`vault_login`** - Authenticate to Vault (token validation, Kubernetes auth)
- **`vault_read`** - Read data from Vault paths (checking if resources exist)
- **`vault_write`** - Write data to Vault paths (configuration, secrets, policies)
- **`vault_kv2_get`** - Read secrets from KV2 engine (proper KV2 structure handling)
- **`vault_list`** - List secrets in a path

### Key Parameters
All modules support:
- `url` - Vault server address
- `auth_method` - Authentication method (token, kubernetes)
- `token` - Vault token for authentication
- `namespace` - Vault namespace (Enterprise feature)
- `validate_certs` - SSL certificate validation
- `ca_cert` - Custom CA certificate path

### Administrative Operations
Note: Administrative DELETE operations (sys/mounts, sys/auth, sys/policy, sys/namespaces) still require `ansible.builtin.uri` as the `community.hashi_vault` collection does not provide dedicated modules for these operations. This is by design as these are infrastructure-level operations typically performed once during setup.

## Task Files

The role is organized into separate task files for maintainability:

- [`main.yml`](tasks/main.yml) - Main task orchestration
- [`validate_inputs.yml`](tasks/validate_inputs.yml) - Input validation
- [`setup_k8s_serviceaccount.yml`](tasks/setup_k8s_serviceaccount.yml) - Kubernetes service account setup
- [`setup_vault_namespace.yml`](tasks/setup_vault_namespace.yml) - Vault namespace configuration
- [`setup_k8s_auth.yml`](tasks/setup_k8s_auth.yml) - Kubernetes auth method setup
- [`setup_kv2_engine.yml`](tasks/setup_kv2_engine.yml) - KV2 engine configuration
- [`write_kv2_secrets.yml`](tasks/write_kv2_secrets.yml) - Write secrets to KV2
- [`read_kv2_secrets.yml`](tasks/read_kv2_secrets.yml) - Read and validate secrets
- [`test_k8s_auth.yml`](tasks/test_k8s_auth.yml) - Test K8s authentication
- [`cleanup.yml`](tasks/cleanup.yml) - Resource cleanup

## What This Role Does

### 1. Input Validation
- Validates all required variables are provided and properly formatted
- Checks Vault address, token, Kubernetes host, and other required parameters
- Validates secret structure and data integrity
- Uses `ansible.builtin.assert` for comprehensive validation

### 2. Kubernetes Service Account Setup
- Creates a ServiceAccount in the specified Kubernetes namespace using `kubernetes.core.k8s`
- Creates a ClusterRoleBinding granting `system:auth-delegator` role
- Creates a Secret containing the service account token
- Extracts the JWT token and CA certificate for Vault configuration
- Waits for token generation with retry logic

### 3. Vault Namespace Configuration (Enterprise)
- Creates a Vault namespace using `community.hashi_vault.vault_write` (requires Vault Enterprise)
- Uses `community.hashi_vault.vault_login` to validate Vault connectivity
- Handles graceful fallback for Vault OSS
- Configures namespace parameter for subsequent operations

### 4. Kubernetes Authentication Method
- Uses `community.hashi_vault.vault_write` to enable the Kubernetes auth method at the specified path
- Configures the auth backend with `community.hashi_vault.vault_write`:
  - Kubernetes API server address
  - CA certificate for API server validation
  - Service account JWT for token review
- Creates a Vault policy using `community.hashi_vault.vault_write` granting access to the KV2 mount
- Creates a Vault role using `community.hashi_vault.vault_write` bound to the service account with appropriate policies

### 5. KV2 Secret Engine
- Checks if engine exists using `community.hashi_vault.vault_read`
- Enables KV version 2 secret engine using `community.hashi_vault.vault_write` at the specified mount path
- Configures engine settings with `community.hashi_vault.vault_write`:
  - Maximum versions to retain
  - Check-and-Set (CAS) requirement
  - Version deletion policy
- Mounts the engine with appropriate TTL settings

### 6. Secret Operations
- Writes all configured secrets using `community.hashi_vault.vault_write` to the KV2 engine
- Reads back each secret using `community.hashi_vault.vault_kv2_get` to validate write operations
- Verifies KV2 data structure (data and metadata)
- Validates that written keys match expected keys
- Lists all secrets using `community.hashi_vault.vault_list` in the mount (optional)

### 7. Authentication Testing
- Authenticates to Vault using `community.hashi_vault.vault_login` with the service account JWT
- Obtains a client token from Vault
- Uses the client token with `community.hashi_vault.vault_kv2_get` to read a secret
- Validates policy permissions are correctly configured
- Demonstrates complete authentication flow

### 8. Cleanup (Optional)
- Note: Cleanup operations use `ansible.builtin.uri` for DELETE operations as `community.hashi_vault`
  does not provide dedicated modules for administrative deletions (sys/mounts, sys/auth, sys/policy, sys/namespaces)
- Deletes all secrets from KV2 engine
- Disables KV2 secret engine
- Deletes Kubernetes auth role and policy
- Disables Kubernetes auth method
- Removes Kubernetes ServiceAccount, Secret, and ClusterRoleBinding using `kubernetes.core.k8s`
- Deletes Vault namespace (Enterprise only)

## Output and Logging

The role provides detailed output at each stage:

- **Banner messages** showing what operation is being performed
- **Success/failure messages** for each resource creation
- **Summary tables** showing configuration details
- **Validation results** confirming proper setup
- **Test results** demonstrating authentication flow

Sensitive data (tokens, passwords) is protected with `no_log: true` by default. Set `vault_kv2_demo_display_secrets: true` to view secret contents (use cautiously).

## Security Considerations

### Token Management
- **Always encrypt the Vault root token** using Ansible Vault
- Tokens are marked with `no_log: true` to prevent logging
- Temporary tokens are cleared from memory after use

### Secret Storage
- Use Ansible Vault to encrypt sensitive variables
- Consider using `group_vars/vault.yml` or `host_vars/vault.yml` encrypted files
- Never commit plaintext credentials to version control

### Network Security
- **Always use HTTPS** for Vault connections (`vault_kv2_demo_validate_certs: true`)
- Provide custom CA certificates if using self-signed certificates
- Ensure network policies allow communication between Ansible, Vault, and Kubernetes

### RBAC Considerations
- The service account requires `system:auth-delegator` for token review
- Limit Vault policies to only the paths and capabilities needed
- Consider using separate namespaces for isolation in multi-tenant environments

### Cleanup
- **Use cleanup cautiously** - it deletes all created resources and secrets
- Test in non-production environments first
- Consider backup strategies before running cleanup

## Troubleshooting

### Vault Connection Errors

**Error**: `Failed to connect to Vault server`

**Solutions**:
- Verify `vault_kv2_demo_vault_addr` is correct and reachable
- Check network connectivity and firewall rules
- Verify SSL certificates if using `validate_certs: true`
- Try setting `vault_kv2_demo_validate_certs: false` for testing (not recommended for production)

### Authentication Failures

**Error**: `Kubernetes authentication failed`

**Solutions**:
- Verify service account token is valid and not expired
- Check that the role binding matches the service account name and namespace
- Ensure Kubernetes host address is correct and accessible from Vault
- Verify Kubernetes CA certificate is correct
- Check Vault logs for detailed error messages

### Namespace Errors

**Error**: `Namespace feature not supported`

**Solutions**:
- This is expected with Vault OSS - set `vault_kv2_demo_vault_namespace: ""`
- For Vault Enterprise, verify your license supports namespaces
- Check token permissions for namespace creation

### Permission Denied

**Error**: `403 Permission Denied` when creating resources

**Solutions**:
- Verify root token has appropriate permissions
- Check token hasn't expired
- Ensure token has access to the namespace (if using Enterprise)
- Review Vault audit logs for detailed permission errors

### KV2 Structure Issues

**Error**: `Secret does not have expected KV2 structure`

**Solutions**:
- Ensure you're using KV version 2, not version 1
- Verify the mount path is correct
- Check that writes are using `/data/` in the path but reads should also use `/data/`
- Use `community.hashi_vault.vault_kv2_get` for proper KV2 handling

## Integration with Existing Projects

### Using This Role as a Template

This role serves as a comprehensive example. To integrate into your project:

1. **Copy relevant task files** to your existing Vault roles
2. **Adapt variable names** to match your naming conventions
3. **Modify secret paths** to match your application structure
4. **Adjust policies** to grant appropriate permissions

### Extending the Role

To add additional functionality:

1. **Add custom secret paths** by extending `vault_kv2_demo_secrets`
2. **Create additional policies** by modifying `setup_k8s_auth.yml`
3. **Add more auth methods** by creating new task files
4. **Integrate with applications** by using the demonstrated auth flow

### Best Practices

- **Separate concerns**: Keep Vault configuration separate from application deployment
- **Use inventory variables**: Store environment-specific settings in inventory
- **Leverage tags**: Use tags for selective execution during development
- **Test thoroughly**: Always test in non-production before deploying
- **Document customizations**: Maintain documentation for any modifications

## Comparison with vault_fix_portworx Role

This role (`vault_kv2_demo`) demonstrates modern best practices compared to the legacy `vault_fix_portworx` role:

### Key Improvements

| Aspect | vault_fix_portworx (Legacy) | vault_kv2_demo (Modern) |
|--------|----------------------------|-------------------------|
| **Vault Modules** | Uses `ansible.builtin.uri` directly | Uses `community.hashi_vault` collection |
| **Authentication** | LDAP with manual token handling | Token + Kubernetes auth with proper modules |
| **Error Handling** | Manual status code checks | `block`/`rescue`/`always` with assertions |
| **SSL Validation** | `validate_certs: false` | `validate_certs: true` (secure by default) |
| **Secret Logging** | `no_log: false` on sensitive ops | `no_log: true` for all sensitive operations |
| **Variable Naming** | Mixed prefixes (px_, vault_, ldap_) | Consistent `vault_kv2_demo_` prefix |
| **Namespace Support** | Manual header construction | Native `namespace` parameter |
| **Secret Reads** | Jinja2 lookups in defaults | Task-time execution with proper modules |
| **Idempotency** | Manual checks with conditionals | Built-in module idempotency |
| **Documentation** | Inline comments | Comprehensive README with examples |

### Migration Guidance

If you're using `vault_fix_portworx` patterns, consider:

1. **Immediate**: Enable `validate_certs: true` and add proper CA certificates
2. **High Priority**: Replace `ansible.builtin.uri` with `community.hashi_vault` modules
3. **Medium Priority**: Implement `block`/`rescue`/`always` error handling
4. **Long Term**: Adopt consistent variable naming and move secrets from defaults to tasks

### Why Use community.hashi_vault?

- **Better abstraction**: Modules handle API versioning and response parsing
- **Improved security**: Built-in support for namespace isolation and token management
- **Easier maintenance**: Collection updates handle Vault API changes
- **Type safety**: Module parameters are validated before execution
- **Better errors**: Meaningful error messages instead of HTTP status codes

## License

MIT

## Author Information

This role was created as a demonstration of HashiCorp Vault integration with Kubernetes authentication and KV2 secret engine operations for enterprise Ansible Automation Platform environments.

For issues, questions, or contributions, refer to the project documentation.

## References

- [HashiCorp Vault Documentation](https://developer.hashicorp.com/vault/docs)
- [Vault Kubernetes Auth Method](https://developer.hashicorp.com/vault/docs/auth/kubernetes)
- [Vault KV Secrets Engine - Version 2](https://developer.hashicorp.com/vault/docs/secrets/kv/kv-v2)
- [community.hashi_vault Collection](https://docs.ansible.com/ansible/latest/collections/community/hashi_vault/)
- [kubernetes.core Collection](https://docs.ansible.com/ansible/latest/collections/kubernetes/core/)
