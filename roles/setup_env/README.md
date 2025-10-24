# Setup Environment Role

## Purpose

Configure Kubernetes environment by retrieving kubeconfig and SSH private key from Vault. This role combines the functionality of the `setup_k8s_env.sh` shell script into a reusable Ansible role.

## Requirements

- Ansible version: >= 2.9
- Collections: ansible.builtin, kubernetes.core, community.hashi_vault
- Target OS: EL 7/8/9, Ubuntu 18.04/20.04/22.04
- Required tools on target system: None (uses Ansible built-in modules)

## Variables

### Required Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| cluster_name | string | Name of the cluster to configure | "user-platform-env-region-id" |

### Optional Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| kubeconfig_dir | string | "kube_configs" | Directory to store credential files |
| vault_token_file | string | "{{ ansible_env.HOME }}/.vault-token" | Path to Vault token file |
| vault_prod_address | string | "<https://vault-prod.example.com>" | Production Vault address |
| vault_dev_address | string | "<https://vault-dev.example.com>" | Development Vault address |
| vault_test_address | string | "<https://vault-test.example.com>" | Test Vault address |
| vault_eng_address | string | "<https://vault-eng.example.com>" | Engineering Vault address |
| vault_namespace | string | "automation" | Vault namespace |
| vault_mount_point | string | "secret" | Vault mount point |
| inventory_url | string | "<https://inventory.example.com>" | Inventory service URL |
| validate_certs | boolean | true | Validate SSL certificates |
| ca_cert_path | string | "/etc/ssl/certs/ca-certificates.crt" | CA certificate path |
| debug_mode | boolean | false | Enable debug logging |
| kubeconfig_file_mode | string | "0600" | File permissions for kubeconfig files |
| ssh_key_file_mode | string | "0600" | File permissions for SSH key files |
| extra_clusters | list | [] | List of additional cluster names to process |
| test_extra_clusters | boolean | false | Enable connection testing for extra clusters |

## Dependencies

- kubernetes.core collection
- community.hashi_vault collection

## Execution Flow

The role follows this execution sequence:

1. **Validation Phase**: Validates required variables and cluster name format
2. **Cluster Parsing**: Extracts components from cluster name (user, platform, environment, region, zone, ID)
3. **Vault Configuration**: Queries inventory service and configures Vault connection parameters
4. **Credential Retrieval**: Discovers Vault token and retrieves kubeconfig/SSH key from Vault
5. **File Operations**: Creates output directory and writes credential files with secure permissions
6. **Connection Testing**: Validates kubeconfig by testing cluster connectivity
7. **Extra Clusters Processing**: If extra_clusters list is provided, processes each cluster independently with error handling
8. **Completion**: Displays success message with file locations and usage instructions for all clusters

## Example Playbook

### Basic Usage

```yaml
---
- name: Setup Kubernetes environment
  hosts: localhost
  gather_facts: true
  become: false
  vars:
    cluster_name: "user-platform-env-region-id"
    kubeconfig_dir: "/home/user/.kube/configs"
    debug_mode: true
    
  roles:
    - setup_env
```

### Using Extra Clusters

```yaml
---
- name: Setup Kubernetes environment with multiple clusters
  hosts: localhost
  gather_facts: true
  become: false
  vars:
    cluster_name: "eng-paas-d-eusw1a-4"
    extra_clusters:
      - "eng-paas-t-eusw1b-2"
      - "eng-paas-p-usw1a-1"
      - "user-k8s-d-us1-cluster1"
    test_extra_clusters: true
    kubeconfig_dir: "/apps/configs"
    
  roles:
    - setup_env
    
  post_tasks:
    - name: Display extra clusters fact
      ansible.builtin.debug:
        msg: "{{ extra_clusters }}"
```

### Accessing Extra Clusters Data in Subsequent Tasks

```yaml
---
- name: Setup and use multiple clusters
  hosts: localhost
  gather_facts: true
  become: false
  vars:
    cluster_name: "eng-paas-d-eusw1a-4"
    extra_clusters:
      - "eng-paas-t-eusw1b-2"
      - "eng-paas-p-usw1a-1"
    
  roles:
    - setup_env
    
  tasks:
    - name: Iterate through all successfully configured clusters
      ansible.builtin.debug:
        msg: |
          Processing cluster: {{ item.cluster_name }}
          Kubeconfig: {{ item.kubeconfig_path }}
          SSH Key: {{ item.ssh_key_path }}
      loop: "{{ extra_clusters }}"
      when: item.status == 'success'
      
    - name: Report failed clusters
      ansible.builtin.debug:
        msg: "Cluster {{ item.cluster_name }} failed: {{ item.error }}"
      loop: "{{ extra_clusters }}"
      when: item.status == 'failed'
```

## Tags

- validation: Input validation and format checking
- cluster_setup: Cluster name parsing and variable setup
- vault: Vault configuration and credential retrieval
- inventory: Inventory service interaction
- credentials: Credential handling and validation
- files: File operations and permissions
- testing: Connection testing and validation
- extra_clusters: Extra clusters processing and management
- completion: Final status and output
- debug: Debug information and logging

## Testing

### Basic Test

```bash
ansible-playbook -i localhost, test_setup_env.yml -e "cluster_name=test-cluster"
```

### With Debug

```bash
ansible-playbook -i localhost, test_setup_env.yml -e "cluster_name=test-cluster debug_mode=true" -v
```

## Cluster Name Format

The role expects cluster names in one of these formats:

- With zone: `<cluster_user>-<platform>-<env>-<region><zone>-<id>` (e.g., `eng-paas-d-eusw1a-4`)
- Without zone: `<cluster_user>-<platform>-<env>-<region>-<id>` (e.g., `user-k8s-p-us1-cluster1`)

Where:

- `cluster_user`: User or team identifier (e.g., `eng`, `user`)
- `platform`: Platform type (e.g., `k8s`, `paas`, `openshift`)
- `env`: Environment (`p`=prod, `t`=test, `d`=dev)
- `region`: Geographic region (e.g., `us1`, `eusw1`)
- `zone`: Availability zone (`a`, `b`, `c`) - optional
- `id`: Cluster identifier (e.g., `4`, `cluster1`)

### Environment Mapping

The role automatically maps environment codes to full names:

- `p` → `prod`
- `t` → `test`
- `d` → `dev`

### Vault Selection Logic

The role selects the appropriate Vault instance based on:

1. **Inventory Service**: If platform Vault configuration exists in inventory response
2. **Fallback Logic**: Based on environment and user:
   - `eng` user + `dev` environment → `vault_eng_address`
   - `prod` environment → `vault_prod_address`
   - `test` environment → `vault_test_address`
   - `dev` environment → `vault_dev_address`

## Output Files

The role creates two files in the specified `kubeconfig_dir` for each cluster:

- `{cluster_name}.kubeconfig`: Kubernetes configuration file
- `{cluster_name}.sshpriv`: SSH private key file

Both files are created with restrictive permissions (600) for security.

## Extra Clusters Functionality

The role supports processing multiple clusters in a single execution through the `extra_clusters` variable. This feature is designed for scenarios where you need to retrieve credentials for multiple clusters simultaneously.

### Feature Overview

- **Input**: List of cluster names via `extra_clusters` variable
- **Processing**: Each cluster is processed independently with isolated error handling
- **Output**: Ansible fact named `extra_clusters` containing results for all processed clusters
- **Error Handling**: Failures in individual clusters do not stop processing of remaining clusters

### Extra Clusters Fact Structure

The role creates an Ansible fact that can be accessed by subsequent tasks or playbooks:

```yaml
extra_clusters:
  - cluster_name: "eng-paas-d-eusw1a-4"
    kubeconfig_path: "/apps/configs/eng-paas-d-eusw1a-4.kubeconfig"
    ssh_key_path: "/apps/configs/eng-paas-d-eusw1a-4.sshpriv"
    status: "success"
    error: ""
  - cluster_name: "eng-paas-t-eusw1b-2"
    kubeconfig_path: ""
    ssh_key_path: ""
    status: "failed"
    error: "Kubeconfig not found in Vault response"
```

### Field Descriptions

- **cluster_name**: Name of the cluster as specified in the input list
- **kubeconfig_path**: Absolute path to the written kubeconfig file (empty if failed)
- **ssh_key_path**: Absolute path to the written SSH private key file (empty if failed)
- **status**: Processing status - either "success" or "failed"
- **error**: Error message if status is "failed", empty string if successful

### Connection Testing for Extra Clusters

Connection testing for extra clusters is controlled by the `test_extra_clusters` variable:

- **Default**: `false` - skips connection testing for performance
- **Enabled**: `true` - performs Kubernetes API connectivity test for each cluster

Connection testing adds processing time but provides immediate validation of retrieved credentials. Testing for the primary cluster is always performed regardless of this setting.

### Error Handling Strategy

The extra clusters processing implements a resilient error handling pattern:

1. **Isolation**: Each cluster is processed in a separate block with rescue handlers
2. **Continuation**: Failures do not interrupt processing of remaining clusters
3. **Logging**: Detailed error messages are logged for failed clusters
4. **Status Tracking**: All results (success and failure) are captured in the fact
5. **Summary**: Processing summary is displayed showing success/failure counts

### Performance Considerations

- Extra clusters are processed sequentially, not in parallel
- Each cluster requires Vault API calls and file I/O operations
- Connection testing (if enabled) adds network latency per cluster
- Expected processing time: approximately 2-5 seconds per cluster without testing

### Use Cases

1. **Multi-Environment Setup**: Retrieve credentials for dev, test, and prod clusters
2. **Multi-Region Operations**: Configure access to clusters across geographic regions
3. **Batch Configuration**: Set up multiple cluster contexts in CI/CD pipelines
4. **Disaster Recovery**: Pre-configure access to failover clusters

## Vault Secret Structure

The role expects the following secret structure in Vault:

```json
{
  "kubeconfig": "apiVersion: v1\nkind: Config\n...",
  "ssh_private.key": "-----BEGIN OPENSSH PRIVATE KEY-----\n..."
}
```

**Required Keys:**

- `kubeconfig`: Complete Kubernetes configuration file content
- `ssh_private.key`: SSH private key content (note the dot in the key name)

**Vault Path Examples:**

- With inventory: Path from inventory service platform Vault configuration
- Without inventory: `{cluster_user}/{cluster_name}` (e.g., `eng/eng-paas-d-eusw1a-4`)

## Error Handling

The role includes comprehensive error handling:

- **Input Validation**: Required variables and cluster name format validation
- **Vault Token Discovery**: Multiple token sources (environment, files) with validation
- **Vault Authentication**: Token validation using Vault API
- **Credential Retrieval**: Vault secret retrieval with error handling
- **Data Validation**: Kubeconfig and SSH key content validation
- **Connection Testing**: Kubernetes cluster connectivity verification
- **File Operations**: Secure file creation with proper permissions
- **Block/Rescue/Always**: Comprehensive error recovery patterns

### Vault Token Discovery

The role searches for Vault tokens in this order:

1. `VAULT_TOKEN` environment variable
2. `~/.vault-token` file
3. Custom `vault_token_file` variable

### Connection Testing

The role performs dual connection tests:

- List cluster nodes using `kubernetes.core.k8s_info`
- List pods in default namespace
- At least one test must succeed for role completion

All errors include descriptive messages to help with troubleshooting.
