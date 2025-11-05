# Must-Gather Role Quick Reference

## Minimum Required Configuration

```yaml
- name: Collect must-gather
  hosts: openshift_masters[0]
  vars:
    OC_BIN: "/usr/local/bin/oc"
    cluster_name: "my-cluster"
    rh_case: "03123456"
  tasks:
    - ansible.builtin.include_role:
        name: must_gather_log
        tasks_from: main_condense
```

## Required Variables

| Variable | Example | Source |
|----------|---------|--------|
| `OC_BIN` | `/usr/local/bin/oc` | Playbook vars |
| `cluster_name` | `prod-ocp-01` | Playbook vars or inventory |
| `rh_case` | `03123456` | Playbook vars or extra_vars |
| `RH_API_TOKEN` | (secret) | AAP credential injection |

## Common Optional Variables

```yaml
# OpenShift version
must_gather_version: "4.14"

# Preserve files after execution
skip_mustgather_deletion: true

# Custom upload description
rh_upload_description: "Must-gather for incident INC123456"

# Proxy configuration
proxy_https: "http://proxy.example.com:3128"
```

## AAP Credential Configuration

### Custom Credential Type

**Input Configuration:**
```yaml
fields:
  - id: rh_api_token
    type: string
    label: Red Hat API Token
    secret: true
```

**Injector Configuration:**
```yaml
env:
  RH_API_TOKEN: "{{ rh_api_token }}"
```

## Expected Output

### Success
```
===================================================================
Must-Gather Operation Summary
===================================================================
Host: ocp-master-01
Cluster: prod-ocp-01
Red Hat Case: 03123456
Status: SUCCESS
Archive Parts: 1
Collection Size: 347.52 MB
Node Used: infra-node-01
Cleanup Performed: Yes
===================================================================
```

### Large Collection (Split Archives)
```
Archive creation completed:
Number of archive parts: 3
- must-gather.tar.gz.part000: 900.00 MB
- must-gather.tar.gz.part001: 900.00 MB
- must-gather.tar.gz.part002: 421.33 MB
```

## Common Issues

### Issue: No suitable node found
**Solution:** Ensure at least one node is labeled `tier=infra`
```bash
oc label node <node-name> tier=infra
```

### Issue: Upload failed
**Check:**
1. Red Hat API token is valid
2. Case number exists and is accessible
3. Network connectivity to `api.access.redhat.com`

**Manual Upload:**
```bash
# Location shown in error message
cd /tmp/mustgather_<id>

# Upload each part
for part in must-gather.tar.gz*; do
  curl -H "Authorization: Bearer $RH_API_TOKEN" \
       -F "file=@$part" \
       -F "description=Part $part" \
       https://api.access.redhat.com/support/v1/cases/<CASE_ID>/attachments/
done
```

## Tags

```bash
# Run only collection (skip upload)
ansible-playbook playbook.yml --tags collection,archiving

# Skip cleanup (preserve files)
ansible-playbook playbook.yml --skip-tags cleanup

# Run validation only
ansible-playbook playbook.yml --tags validation
```

## Execution Time

| Phase | Time |
|-------|------|
| Validation | 5-10 seconds |
| Node Selection | 3-5 seconds |
| Must-Gather Collection | 5-15 minutes |
| Archive Creation | 2-10 minutes |
| Upload | 3-15 minutes |
| **Total** | **10-35 minutes** |

## Disk Space Requirements

- Managed Host: 2-3x collection size
- Controller: 1x collection size (temporary)
- Typical: 1-2 GB total

## Log Files

**Controller:**
```
/var/log/ansible-must-gather.log
```

**Format:**
```
2025-11-05T14:23:45Z | Host: ocp-master-01 | Cluster: prod-ocp-01 | Status: SUCCESS | Case: 03123456 | Parts: 1 | Archive: UPLOADED
```

## Troubleshooting Commands

```bash
# Verify oc binary
stat $OC_BIN
$OC_BIN version

# Verify cluster authentication
$OC_BIN whoami

# Check infra nodes
$OC_BIN get nodes -l tier=infra

# Check must-gather node
$OC_BIN get nodes -l must_gather=true

# Test Red Hat API authentication
curl -H "Authorization: Bearer $RH_API_TOKEN" \
     https://api.access.redhat.com/support/v1/cases/<CASE_ID>

# Check disk space
df -h /tmp
df -h $WORK_DIR
```

## Support

For issues or questions:
1. Review `/var/log/ansible-must-gather.log`
2. Run with increased verbosity: `ansible-playbook -vvv`
3. Check `IMPLEMENTATION_COMPARISON.md` for detailed analysis
4. Consult `README_CONDENSE.md` for comprehensive documentation

