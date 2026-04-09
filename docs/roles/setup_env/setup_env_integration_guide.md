# Setup Environment Role Integration Guide

## Purpose

This guide explains how to integrate the `setup_env` role into existing playbooks as a pre-task to override old paths and variables with new configuration from Vault.

## Integration Pattern

The `setup_env` role is designed to be used as a pre-task in existing playbooks to:

1. **Retrieve credentials** from Vault (kubeconfig and SSH private key)
2. **Override old variables** with new paths and configuration
3. **Maintain compatibility** with existing playbook logic
4. **Provide seamless migration** from old credential management to Vault-based approach

## Basic Integration Template

```yaml
---
- name: "Your existing playbook with setup_env integration"
  hosts: your_target_hosts
  gather_facts: true
  become: false
  vars:
    # Required: Cluster name for setup_env role
    cluster_name: "your-cluster-name"
    
    # Optional: Override default kubeconfig directory
    kubeconfig_dir: "{{ ansible_env.HOME }}/.kube/configs"
    
    # Your existing variables (will be overridden by setup_env)
    old_kubeconfig_path: "/old/path/to/kubeconfig"
    old_ssh_key_path: "/old/path/to/ssh_key"
    old_cluster_endpoint: "https://old-cluster.example.com"

  pre_tasks:
    # Step 1: Setup environment using setup_env role
    - name: "Setup Kubernetes environment using setup_env role"
      ansible.builtin.include_role:
        name: setup_env
      vars:
        cluster_name: "{{ cluster_name }}"
        kubeconfig_dir: "{{ kubeconfig_dir }}"
        debug_mode: "{{ debug_mode | default(false) }}"
        validate_certs: "{{ validate_certs | default(true) }}"
      tags: [setup_env, k8s_setup, pre_task]

    # Step 2: Override old variables with new paths
    - name: "Override old configuration paths with new setup_env paths"
      ansible.builtin.set_fact:
        # Override old kubeconfig path
        kubeconfig_path: "{{ kubeconfig_dir }}/{{ cluster_name }}.kubeconfig"
        # Override old SSH key path
        ssh_key_path: "{{ kubeconfig_dir }}/{{ cluster_name }}.sshpriv"
        # Override old cluster endpoint (extracted from kubeconfig)
        cluster_endpoint: "{{ kubeconfig_data | from_yaml | json_query('clusters[0].cluster.server') | default('unknown') }}"
      tags: [setup_env, variable_override, pre_task]

  # Your existing tasks continue here with overridden variables
  tasks:
    - name: "Your existing task using new kubeconfig path"
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Node
        kubeconfig: "{{ kubeconfig_path }}"  # Uses new path from setup_env
        validate_certs: "{{ validate_certs }}"
      # ... rest of your task
```

## Variable Override Examples

### Common Variable Overrides

```yaml
# Override kubeconfig-related variables
- name: "Override kubeconfig variables"
  ansible.builtin.set_fact:
    kubeconfig_path: "{{ kubeconfig_dir }}/{{ cluster_name }}.kubeconfig"
    kubeconfig_content: "{{ kubeconfig_data }}"
    cluster_endpoint: "{{ kubeconfig_data | from_yaml | json_query('clusters[0].cluster.server') }}"
    cluster_ca_cert: "{{ kubeconfig_data | from_yaml | json_query('clusters[0].cluster.certificate-authority-data') }}"
  tags: [setup_env, variable_override]

# Override SSH-related variables
- name: "Override SSH variables"
  ansible.builtin.set_fact:
    ssh_key_path: "{{ kubeconfig_dir }}/{{ cluster_name }}.sshpriv"
    ssh_key_content: "{{ ssh_private_key }}"
    ssh_user: "{{ kubeconfig_data | from_yaml | json_query('users[0].user.username') | default('core') }}"
  tags: [setup_env, variable_override]

# Override cluster-specific variables
- name: "Override cluster variables"
  ansible.builtin.set_fact:
    cluster_name_parsed: "{{ cluster_name }}"
    cluster_user: "{{ cluster_user }}"
    cluster_environment: "{{ cluster_env }}"
    cluster_region: "{{ region }}"
    cluster_zone: "{{ zone }}"
  tags: [setup_env, variable_override]
```

## Migration Strategies

### Strategy 1: Gradual Migration

```yaml
# Use conditional logic to support both old and new approaches
- name: "Setup environment (new approach)"
  ansible.builtin.include_role:
    name: setup_env
  vars:
    cluster_name: "{{ cluster_name }}"
  when: use_vault_credentials | default(true)
  tags: [setup_env, new_approach]

- name: "Setup environment (legacy approach)"
  ansible.builtin.include_tasks: legacy_setup.yml
  when: not (use_vault_credentials | default(true))
  tags: [legacy, old_approach]

- name: "Set unified variables for both approaches"
  ansible.builtin.set_fact:
    kubeconfig_path: "{{ kubeconfig_dir }}/{{ cluster_name }}.kubeconfig if use_vault_credentials | default(true) else old_kubeconfig_path }}"
    ssh_key_path: "{{ kubeconfig_dir }}/{{ cluster_name }}.sshpriv if use_vault_credentials | default(true) else old_ssh_key_path }}"
  tags: [unified_variables]
```

### Strategy 2: Complete Replacement

```yaml
# Replace old credential setup entirely with setup_env role
- name: "Setup Kubernetes environment (replaces old credential setup)"
  ansible.builtin.include_role:
    name: setup_env
  vars:
    cluster_name: "{{ cluster_name }}"
    kubeconfig_dir: "{{ kubeconfig_dir | default('~/.kube/configs') }}"
  tags: [setup_env, replacement]

# Remove old credential setup tasks and replace with variable overrides
- name: "Override all old credential variables"
  ansible.builtin.set_fact:
    kubeconfig_path: "{{ kubeconfig_dir }}/{{ cluster_name }}.kubeconfig"
    ssh_key_path: "{{ kubeconfig_dir }}/{{ cluster_name }}.sshpriv"
    cluster_endpoint: "{{ kubeconfig_data | from_yaml | json_query('clusters[0].cluster.server') }}"
    # Add any other variables your playbook needs
  tags: [setup_env, variable_override]
```

## Tag Usage for Selective Execution

```yaml
# Run only setup_env role
ansible-playbook your_playbook.yml --tags setup_env

# Run setup_env and variable overrides
ansible-playbook your_playbook.yml --tags setup_env,variable_override

# Skip setup_env and run only existing tasks
ansible-playbook your_playbook.yml --skip-tags setup_env,pre_task

# Run everything except examples
ansible-playbook your_playbook.yml --skip-tags example
```

## Error Handling Integration

```yaml
pre_tasks:
  - name: "Setup environment with error handling"
    block:
      - name: "Setup Kubernetes environment using setup_env role"
        ansible.builtin.include_role:
          name: setup_env
        vars:
          cluster_name: "{{ cluster_name }}"
          kubeconfig_dir: "{{ kubeconfig_dir }}"
        tags: [setup_env, k8s_setup, pre_task]

      - name: "Override old configuration paths"
        ansible.builtin.set_fact:
          kubeconfig_path: "{{ kubeconfig_dir }}/{{ cluster_name }}.kubeconfig"
          ssh_key_path: "{{ kubeconfig_dir }}/{{ cluster_name }}.sshpriv"
        tags: [setup_env, variable_override, pre_task]

    rescue:
      - name: "Handle setup_env failure"
        ansible.builtin.fail:
          msg: "Failed to setup environment using setup_env role. Please check cluster_name and Vault configuration."

    always:
      - name: "Log setup completion status"
        ansible.builtin.debug:
          msg: "Environment setup completed with status: {{ 'SUCCESS' if kubeconfig_path is defined else 'FAILED' }}"
```

## Best Practices

### 1. Variable Naming Convention

```yaml
# Use consistent naming for overridden variables
kubeconfig_path: "{{ kubeconfig_dir }}/{{ cluster_name }}.kubeconfig"
ssh_key_path: "{{ kubeconfig_dir }}/{{ cluster_name }}.sshpriv"
cluster_endpoint: "{{ kubeconfig_data | from_yaml | json_query('clusters[0].cluster.server') }}"
```

### 2. Conditional Execution

```yaml
# Make setup_env optional based on environment or conditions
- name: "Setup environment (conditional)"
  ansible.builtin.include_role:
    name: setup_env
  vars:
    cluster_name: "{{ cluster_name }}"
  when: 
    - setup_env_enabled | default(true)
    - cluster_name is defined
  tags: [setup_env, conditional]
```

### 3. Validation After Override

```yaml
- name: "Validate overridden variables"
  ansible.builtin.assert:
    that:
      - kubeconfig_path is defined
      - ssh_key_path is defined
      - cluster_endpoint is defined
    fail_msg: "Required variables not set after setup_env role execution"
    success_msg: "All required variables validated after setup_env role"
  tags: [validation, post_setup]
```

## Troubleshooting

### Common Issues

1. **Variable not defined after setup_env role**
   - Ensure you're using `ansible.builtin.set_fact` to override variables
   - Check that the setup_env role completed successfully

2. **Old variables still being used**
   - Verify variable precedence in your playbook
   - Ensure override tasks run after setup_env role

3. **Kubeconfig path not found**
   - Check that `kubeconfig_dir` exists and is writable
   - Verify cluster_name format matches expected pattern

### Debug Commands

```bash
# Run with debug to see variable values
ansible-playbook your_playbook.yml -v --tags setup_env,variable_override

# Check if setup_env role variables are available
ansible-playbook your_playbook.yml --tags setup_env -e "debug_mode=true"

# Validate cluster name format
ansible-playbook your_playbook.yml --tags validation
```

## Example Integration Files

- `test_setup_env.yml` - Complete example showing integration pattern
- `docs/setup_env_integration_guide.md` - This integration guide
- `roles/setup_env/README.md` - Role documentation and usage

## Support

For issues with setup_env role integration:

1. Check the role documentation in `roles/setup_env/README.md`
2. Review the example in `test_setup_env.yml`
3. Validate your cluster_name format matches expected patterns
4. Ensure Vault configuration and credentials are correct
