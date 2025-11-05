# HashiCorp Vault Configuration Guide

## Overview

The `must_gather_log` role requires Red Hat API credentials for uploading must-gather archives to support cases. These credentials should be stored securely in HashiCorp Vault and retrieved using the `community.hashi_vault` collection lookup plugin.

## Prerequisites

### 1. Install community.hashi_vault Collection

```bash
ansible-galaxy collection install community.hashi_vault
```

### 2. HashiCorp Vault Server

- Vault server accessible from Ansible controller/AAP
- Appropriate Vault policies configured
- Authentication method configured (Token, AppRole, Kubernetes, etc.)

### 3. Required Secrets in Vault

Store Red Hat API credentials in your Vault instance at a known path.

## Vault Secret Structure

### Recommended Path Structure

```
secret/
└── data/
    ├── redhat/
    │   ├── api_token    # Red Hat API bearer token
    │   ├── username     # Alternative: Red Hat portal username
    │   └── password     # Alternative: Red Hat portal password
    └── proxy/
        ├── http_proxy   # Optional: HTTP proxy URL
        ├── https_proxy  # Optional: HTTPS proxy URL
        └── no_proxy     # Optional: No proxy list
```

### Storing Secrets in Vault

**Using Vault CLI:**

```bash
# Store Red Hat API token (recommended)
vault kv put secret/redhat api_token="your-token-here"

# OR store username/password
vault kv put secret/redhat \
  username="user@example.com" \
  password="SecurePassword123"

# Optional: Store proxy settings
vault kv put secret/proxy \
  http_proxy="http://proxy.company.com:3128" \
  https_proxy="http://proxy.company.com:3128" \
  no_proxy="localhost,127.0.0.1,.company.com"
```

**Using Vault UI:**

1. Navigate to Secrets Engine
2. Create secret at `secret/redhat`
3. Add key-value pairs:
   - `api_token`: your-token-value
   - OR `username`: your-username AND `password`: your-password

## Configuration in Ansible

### Method 1: Group Variables (Recommended)

Create `group_vars/all/main.yml`:

```yaml
---
# Red Hat API Authentication from HashiCorp Vault
rh_api_token: "{{ lookup('community.hashi_vault.hashi_vault', 
                  'secret=secret/data/redhat:api_token') }}"

# OR for username/password authentication:
# rh_api_user: "{{ lookup('community.hashi_vault.hashi_vault',
#                  'secret=secret/data/redhat:username') }}"
# rh_api_pass: "{{ lookup('community.hashi_vault.hashi_vault',
#                  'secret=secret/data/redhat:password') }}"

# Optional: Proxy configuration
# proxy_http: "{{ lookup('community.hashi_vault.hashi_vault',
#              'secret=secret/data/proxy:http_proxy') }}"
# proxy_https: "{{ lookup('community.hashi_vault.hashi_vault',
#               'secret=secret/data/proxy:https_proxy') }}"
# proxy_no: "{{ lookup('community.hashi_vault.hashi_vault',
#            'secret=secret/data/proxy:no_proxy') }}"
```

### Method 2: Playbook Variables

In your playbook:

```yaml
---
- name: Collect and upload must-gather
  hosts: openshift_masters[0]
  vars:
    OC_BIN: "/usr/local/bin/oc"
    cluster_name: "prod-ocp-01"
    rh_case: "03123456"
    
    # Fetch from HashiCorp Vault
    rh_api_token: "{{ lookup('community.hashi_vault.hashi_vault',
                      'secret=secret/data/redhat:api_token') }}"
  
  roles:
    - role: must_gather_log
      tasks_from: main_condense
```

### Method 3: Host/Group Variables with Vault Path

For multiple environments:

```yaml
# group_vars/production/vault_paths.yml
vault_redhat_secret_path: "secret/data/production/redhat"

# group_vars/production/main.yml
rh_api_token: "{{ lookup('community.hashi_vault.hashi_vault',
                  'secret=' + vault_redhat_secret_path + ':api_token') }}"

# group_vars/staging/vault_paths.yml
vault_redhat_secret_path: "secret/data/staging/redhat"
```

## Vault Authentication Methods

The `community.hashi_vault` collection supports multiple authentication methods. Choose the appropriate method for your environment.

### Method 1: Token Authentication (Simple)

**Environment Variable:**

```bash
export VAULT_ADDR="https://vault.company.com:8200"
export VAULT_TOKEN="s.abc123def456..."

ansible-playbook must_gather.yml
```

**In ansible.cfg:**

```ini
[community.hashi_vault.hashi_vault]
vault_url = https://vault.company.com:8200
vault_token = s.abc123def456...  # NOT recommended - use environment variable
```

### Method 2: AppRole Authentication (Recommended for Automation)

**Setup:**

```bash
# Enable AppRole auth method in Vault
vault auth enable approle

# Create policy for must-gather secrets
vault policy write must-gather-policy - <<EOF
path "secret/data/redhat" {
  capabilities = ["read"]
}
path "secret/data/proxy" {
  capabilities = ["read"]
}
EOF

# Create AppRole
vault write auth/approle/role/ansible-must-gather \
  policies="must-gather-policy" \
  secret_id_ttl=24h \
  token_ttl=20m

# Get role_id
vault read auth/approle/role/ansible-must-gather/role-id

# Generate secret_id
vault write -f auth/approle/role/ansible-must-gather/secret-id
```

**Use in Ansible:**

```bash
export VAULT_ADDR="https://vault.company.com:8200"
export VAULT_ROLE_ID="abc-123-def"
export VAULT_SECRET_ID="xyz-789-ghi"

ansible-playbook must_gather.yml
```

**Or in group_vars:**

```yaml
# group_vars/all/vault_auth.yml
vault_auth_method: approle
vault_role_id: "{{ lookup('env', 'VAULT_ROLE_ID') }}"
vault_secret_id: "{{ lookup('env', 'VAULT_SECRET_ID') }}"
```

### Method 3: Kubernetes Service Account (For AAP in Kubernetes)

**Vault Configuration:**

```bash
# Enable Kubernetes auth
vault auth enable kubernetes

# Configure Kubernetes auth
vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc:443" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

# Create role for AAP service account
vault write auth/kubernetes/role/ansible-aap \
  bound_service_account_names=ansible-automation-platform \
  bound_service_account_namespaces=aap \
  policies=must-gather-policy \
  ttl=20m
```

**Use in Ansible (AAP automatically provides JWT):**

```yaml
# group_vars/all/vault_auth.yml
vault_auth_method: kubernetes
vault_role: ansible-aap
```

### Method 4: AWS IAM Authentication (For AAP on AWS)

```bash
export VAULT_ADDR="https://vault.company.com:8200"
export VAULT_AUTH_METHOD="aws"
# AWS credentials from instance role or environment
```

## Lookup Plugin Syntax

### Basic Syntax

```yaml
variable: "{{ lookup('community.hashi_vault.hashi_vault', 
              'secret=path/to/secret:key') }}"
```

### With Auth Method Specified

```yaml
variable: "{{ lookup('community.hashi_vault.hashi_vault',
              'secret=secret/data/redhat:api_token
               auth_method=approle
               role_id=' + vault_role_id + '
               secret_id=' + vault_secret_id) }}"
```

### With Full Parameters

```yaml
variable: "{{ lookup('community.hashi_vault.hashi_vault',
              'secret=secret/data/redhat:api_token',
              url='https://vault.company.com:8200',
              auth_method='token',
              token=lookup('env', 'VAULT_TOKEN')) }}"
```

### With Error Handling

```yaml
variable: "{{ lookup('community.hashi_vault.hashi_vault',
              'secret=secret/data/redhat:api_token',
              default='') | default('', true) }}"
```

## Complete Configuration Example

### Directory Structure

```
ansible-project/
├── ansible.cfg
├── inventory/
│   ├── hosts
│   └── group_vars/
│       └── all/
│           ├── main.yml              # Non-sensitive variables
│           └── vault_lookups.yml     # Vault lookup definitions
├── playbooks/
│   └── must_gather.yml
└── roles/
    └── must_gather_log/
```

### ansible.cfg

```ini
[defaults]
inventory = inventory/hosts
roles_path = roles

[community.hashi_vault.hashi_vault]
vault_url = https://vault.company.com:8200
```

### inventory/group_vars/all/vault_lookups.yml

```yaml
---
# HashiCorp Vault Lookups
# Authentication via VAULT_TOKEN environment variable

# Red Hat API Credentials
rh_api_token: "{{ lookup('community.hashi_vault.hashi_vault',
                  'secret=secret/data/redhat:api_token') }}"

# Optional: Username/Password Alternative
# rh_api_user: "{{ lookup('community.hashi_vault.hashi_vault',
#                  'secret=secret/data/redhat:username') }}"
# rh_api_pass: "{{ lookup('community.hashi_vault.hashi_vault',
#                  'secret=secret/data/redhat:password') }}"

# Proxy Configuration
proxy_http: "{{ lookup('community.hashi_vault.hashi_vault',
             'secret=secret/data/proxy:http_proxy',
             default='') | default('', true) }}"

proxy_https: "{{ lookup('community.hashi_vault.hashi_vault',
              'secret=secret/data/proxy:https_proxy',
              default='') | default('', true) }}"
```

### playbooks/must_gather.yml

```yaml
---
- name: Collect OpenShift must-gather and upload to Red Hat
  hosts: openshift_masters[0]
  gather_facts: true
  
  vars:
    OC_BIN: "/usr/local/bin/oc"
    cluster_name: "{{ inventory_hostname_short }}"
  
  tasks:
    - name: Include must_gather_log role
      ansible.builtin.include_role:
        name: must_gather_log
        tasks_from: main_condense
      vars:
        rh_case: "{{ support_case_number }}"
```

## Troubleshooting

### Issue: "Unable to find 'community.hashi_vault.hashi_vault' lookup plugin"

**Cause:** Collection not installed

**Solution:**

```bash
ansible-galaxy collection install community.hashi_vault

# Verify installation
ansible-galaxy collection list | grep hashi_vault
```

### Issue: "Permission denied" from Vault

**Cause:** Insufficient Vault policy permissions

**Solution:**

```bash
# Check current token capabilities
vault token capabilities secret/data/redhat

# Should show: ["read"]

# If not, update policy:
vault policy write must-gather-policy - <<EOF
path "secret/data/redhat" {
  capabilities = ["read"]
}
EOF
```

### Issue: "Error retrieving secret from Vault"

**Cause:** Incorrect secret path or authentication failure

**Solution:**

```bash
# Test Vault access manually
vault kv get secret/redhat

# Verify VAULT_TOKEN is set
echo $VAULT_TOKEN

# Test with Ansible lookup
ansible localhost -m debug \
  -a "msg={{ lookup('community.hashi_vault.hashi_vault', 'secret=secret/data/redhat:api_token') }}"
```

### Issue: "SSL certificate verification failed"

**Cause:** Self-signed certificate or untrusted CA

**Solution:**

**Option 1: Add CA certificate**
```bash
export VAULT_CACERT=/path/to/vault-ca.crt
```

**Option 2: Disable verification (NOT recommended for production)**
```bash
export VAULT_SKIP_VERIFY=1
```

**Option 3: In lookup**
```yaml
rh_api_token: "{{ lookup('community.hashi_vault.hashi_vault',
                  'secret=secret/data/redhat:api_token
                   validate_certs=false') }}"
```

## Security Best Practices

### 1. Use AppRole for Automation

- Don't use root or long-lived tokens
- Use AppRole with limited policies
- Rotate secret_id regularly

### 2. Implement Least Privilege

```hcl
# Vault policy - only read access to specific paths
path "secret/data/redhat" {
  capabilities = ["read"]
}

path "secret/data/proxy" {
  capabilities = ["read"]
}

# Deny all other paths
path "secret/*" {
  capabilities = ["deny"]
}
```

### 3. Use Short-Lived Tokens

```bash
vault write auth/approle/role/ansible-must-gather \
  token_ttl=20m \
  token_max_ttl=1h
```

### 4. Audit Vault Access

```bash
# Enable audit logging
vault audit enable file file_path=/var/log/vault_audit.log

# Monitor access to secrets
tail -f /var/log/vault_audit.log | grep "secret/data/redhat"
```

### 5. Rotate Credentials

```bash
# Generate new Red Hat API token
# Update in Vault:
vault kv put secret/redhat api_token="new-token-here"

# Old token is immediately invalidated for new runs
# No Ansible code changes required
```

## Integration with AAP

### AAP Custom Credential Type

**Input Configuration:**
```yaml
fields:
  - id: vault_token
    type: string
    label: HashiCorp Vault Token
    secret: true
  - id: vault_addr
    type: string
    label: Vault Address
    default: https://vault.company.com:8200
```

**Injector Configuration:**
```yaml
env:
  VAULT_TOKEN: "{{ vault_token }}"
  VAULT_ADDR: "{{ vault_addr }}"
```

### AAP Execution Environment

Ensure `community.hashi_vault` is installed in your EE:

```yaml
# execution-environment.yml
dependencies:
  galaxy: requirements.yml

# requirements.yml
collections:
  - name: community.hashi_vault
    version: ">=3.0.0"
```

## Related Documentation

- HashiCorp Vault: https://www.vaultproject.io/docs
- community.hashi_vault Collection: https://docs.ansible.com/ansible/latest/collections/community/hashi_vault/
- `README_CONDENSE.md` - Complete role documentation
- `defaults/main.yml` - Variable definitions with examples
- `QUICK_REFERENCE.md` - Quick reference guide


