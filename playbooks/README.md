# Ansible Playbooks

## verify_pxbackup_credentials.yml

This standalone playbook verifies PX Backup cloud credentials.

### Usage

```bash
# Run with credentials from environment variables
ansible-playbook playbooks/verify_pxbackup_credentials.yml -e "pxbackup_cloud_access_key=$PX_ACCESS_KEY" -e "pxbackup_cloud_secret_key=$PX_SECRET_KEY"

# Run with credentials from a vault file
ansible-playbook playbooks/verify_pxbackup_credentials.yml --vault-id @prompt -e "@vault/pxbackup-credentials.yml"
```

### Required Variables

- `pxbackup_cloud_access_key`: The access key for PX Backup cloud
- `pxbackup_cloud_secret_key`: The secret key for PX Backup cloud

### Security Note

The playbook uses `no_log: true` for tasks handling sensitive data to ensure credentials are not logged.
