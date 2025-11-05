# Red Hat Upload Module Migration Guide

## Overview

This guide helps you migrate from the Bash script-based upload (`upload_to_redhat_condense.sh`) to the new Python Ansible module (`redhat_upload`).

## Migration Benefits

### Improved Integration

- **Native Ansible Module**: Better integration with Ansible's error handling and result management
- **Automatic Security**: Sensitive parameters automatically handled with `no_log: true`
- **Type Validation**: Built-in parameter validation prevents common errors
- **Structured Results**: Consistent return value structure following Ansible conventions

### Enhanced Maintainability

- **Python Standard Library**: Uses standard library only, no external dependencies
- **Better Error Messages**: More descriptive error messages with context
- **Code Reusability**: Module can be used independently or within roles

### Backward Compatibility

- **Same Functionality**: All features from Bash script are preserved
- **Same Return Structure**: Return values match the JSON output from Bash script
- **Same Variable Names**: Role variables remain unchanged

## Migration Steps

### Step 1: Update Ansible Task

**Before (Bash Script)**:

```yaml
- name: "Upload all archive parts to Red Hat support case with retry handling"
  ansible.builtin.script:
    cmd: upload_to_redhat_condense.sh
  environment:
    MG_ARCHIVE_PATTERN: "{{ controller_temp_dir.path }}/*.tar.gz*"
    MG_CASE_ID: "{{ rh_case }}"
    MG_UPLOAD_DESC: "{{ computed_upload_description }}"
    RH_API_TOKEN: "{{ rh_api_token | default(omit) }}"
    # ... other environment variables
  delegate_to: localhost
  register: rh_upload_results
  failed_when: >-
    rh_upload_results.rc not in [0, 3] or
    (rh_upload_results.rc == 3 and (rh_upload_fail_on_partial | default(true) | bool))
  changed_when: rh_upload_results.rc in [0, 3]
  no_log: true
```

**After (Python Module)**:

```yaml
- name: "Upload all archive parts to Red Hat support case with retry handling"
  redhat_upload:
    case_id: "{{ rh_case }}"
    archive_pattern: "{{ controller_temp_dir.path }}/*.tar.gz*"
    upload_description: "{{ computed_upload_description }}"
    api_token: "{{ rh_api_token | default(omit) }}"
    api_user: "{{ rh_api_user | default(omit) }}"
    api_pass: "{{ rh_api_pass | default(omit) }}"
    proxy_http: "{{ proxy_http | default(omit) }}"
    proxy_https: "{{ proxy_https | default(omit) }}"
    proxy_no: "{{ proxy_no | default(omit) }}"
    max_retry_attempts: "{{ rh_upload_max_retries | default(3) }}"
    fail_on_partial: "{{ rh_upload_fail_on_partial | default(true) }}"
  delegate_to: localhost
  register: rh_upload_results
  no_log: true
```

### Step 2: Update Result Parsing

**Before (Bash Script)**:

```yaml
- name: "Parse upload results from JSON output"
  ansible.builtin.set_fact:
    upload_status: "{{ rh_upload_results.stdout | from_json }}"
  when: rh_upload_results.stdout is defined
```

**After (Python Module)**:

```yaml
- name: "Set upload status from module results"
  ansible.builtin.set_fact:
    upload_status:
      status: "{{ rh_upload_results.status }}"
      case_id: "{{ rh_upload_results.case_id }}"
      total_parts: "{{ rh_upload_results.total_parts }}"
      success_count: "{{ rh_upload_results.success_count }}"
      failure_count: "{{ rh_upload_results.failure_count }}"
      results: "{{ rh_upload_results.results }}"
  when: rh_upload_results is defined
```

### Step 3: Update Failure Handling

**Before (Bash Script)**:

```yaml
failed_when: >-
  rh_upload_results.rc not in [0, 3] or
  (rh_upload_results.rc == 3 and (rh_upload_fail_on_partial | default(true) | bool))
```

**After (Python Module)**:
The module handles failure internally based on `fail_on_partial` parameter. No `failed_when` needed, but you can add:

```yaml
failed_when: >-
  rh_upload_results.status == 'failed' or
  (rh_upload_results.status == 'partial' and (rh_upload_fail_on_partial | default(true) | bool))
```

However, the module already handles this internally, so `failed_when` is optional.

### Step 4: Verify Downstream Tasks

Downstream tasks that use `upload_status` should work without changes since the structure remains the same:

```yaml
- name: "Display detailed upload status per part"
  ansible.builtin.debug:
    msg: |
      Upload Operation Summary:
      Status: {{ upload_status.status | upper }}
      Case ID: {{ upload_status.case_id }}
      Total Parts: {{ upload_status.total_parts }}
      # ... rest of the template
```

## Parameter Mapping

### Environment Variables to Module Parameters

| Bash Script (Environment Variable) | Python Module (Parameter) | Notes |
|-----------------------------------|---------------------------|-------|
| `MG_CASE_ID` | `case_id` | Required |
| `MG_ARCHIVE_PATTERN` | `archive_pattern` | Required |
| `MG_UPLOAD_DESC` | `upload_description` | Required |
| `RH_API_TOKEN` | `api_token` | Preferred authentication |
| `RH_API_USER` | `api_user` | Fallback authentication |
| `RH_API_PASS` | `api_pass` | Fallback authentication |
| `HTTP_PROXY` | `proxy_http` | Optional |
| `HTTPS_PROXY` | `proxy_https` | Optional |
| `NO_PROXY` | `proxy_no` | Optional |
| `MAX_RETRY_ATTEMPTS` | `max_retry_attempts` | Default: 3 |
| `RETRY_BACKOFF_BASE` | `retry_backoff_base` | Default: 2 |
| `FAIL_ON_PARTIAL` | `fail_on_partial` | Default: true |

## Return Value Comparison

### Bash Script JSON Output

```json
{
  "status": "success",
  "case_id": "03123456",
  "total_parts": 3,
  "success_count": 3,
  "failure_count": 0,
  "results": [
    {
      "part": 1,
      "file": "must-gather.tar.gz.part000",
      "status": "success",
      "attempts": 1,
      "http_code": 201
    }
  ]
}
```

### Python Module Return Values

The module returns the same structure, accessible via Ansible module return values:

```yaml
rh_upload_results:
  status: "success"
  case_id: "03123456"
  total_parts: 3
  success_count: 3
  failure_count: 0
  results:
    - part: 1
      file: "must-gather.tar.gz.part000"
      status: "success"
      attempts: 1
      http_code: 201
```

## Exit Code Mapping

### Bash Script Exit Codes

- `0`: All parts uploaded successfully
- `1`: Validation or configuration error
- `2`: All parts failed to upload
- `3`: Partial failure (some parts succeeded, some failed)

### Python Module Behavior

The module uses Ansible's standard failure mechanism:

- **Success**: Module exits with `changed: true` or `changed: false`
- **Failure**: Module calls `module.fail_json()` with appropriate message
- **Partial Failure**: Depends on `fail_on_partial` parameter:
  - If `fail_on_partial: true`: Module fails
  - If `fail_on_partial: false`: Module succeeds with `status: "partial"`

## Testing the Migration

### 1. Syntax Validation

```bash
# Validate module syntax
python3 -m py_compile roles/must_gather_log/library/redhat_upload.py

# Validate playbook syntax
ansible-playbook --syntax-check playbooks/test_redhat_upload.yml
```

### 2. Dry Run Test

```bash
ansible-playbook playbooks/test_redhat_upload.yml --check
```

### 3. Integration Test

```bash
# Test with real Red Hat case (use test case)
ansible-playbook playbooks/test_redhat_upload.yml \
  -e rh_case="TEST_CASE_ID" \
  -e rh_api_token="YOUR_TOKEN"
```

### 4. Compare Results

Run both implementations and compare results:

```bash
# Run Bash script version (if still available)
# Run Python module version
# Compare JSON outputs
```

## Rollback Plan

If issues arise with the Python module:

1. **Immediate Rollback**: Revert to Bash script in `main_condense.yml`
2. **Gradual Migration**: Support both script and module with feature flag
3. **Documentation**: Keep Bash script documentation until migration complete

### Rollback Steps

1. Revert task in `main_condense.yml` to use `ansible.builtin.script`
2. Restore result parsing from JSON
3. Restore `failed_when` logic based on exit codes
4. Test with Bash script version

## Common Issues and Solutions

### Issue: Module Not Found

**Symptom**: `module 'redhat_upload' not found`

**Solution**: Ensure the role's `library/` directory is in the module search path. When using the role, the module should be automatically available.

### Issue: Different Return Structure

**Symptom**: Downstream tasks fail with "undefined variable"

**Solution**: Verify `upload_status` fact structure matches expectations. The structure should be identical to Bash script JSON output.

### Issue: Authentication Failures

**Symptom**: HTTP 401 or 403 errors

**Solution**: Verify authentication parameters are correctly passed:

- Check `api_token` or `api_user`/`api_pass` are set
- Verify parameters are not empty strings
- Check Vault lookups are working correctly

### Issue: Proxy Not Working

**Symptom**: Connection errors despite proxy configuration

**Solution**:

- Verify proxy URLs are correct format: `http://proxy.example.com:8080`
- Check `proxy_no` configuration if needed
- Test proxy connectivity independently

## Compatibility Matrix

| Feature | Bash Script | Python Module | Status |
|---------|-------------|---------------|--------|
| File pattern expansion | Yes | Yes | Compatible |
| File validation | Yes | Yes | Compatible |
| Multi-part upload | Yes | Yes | Compatible |
| Retry logic | Yes | Yes | Compatible |
| Exponential backoff | Yes | Yes | Compatible |
| Token authentication | Yes | Yes | Compatible |
| Username/password auth | Yes | Yes | Compatible |
| Proxy support | Yes | Yes | Compatible |
| Error classification | Yes | Yes | Compatible |
| JSON output | Yes | Yes | Compatible |
| Exit codes | Yes | N/A | Module uses Ansible failure |

## Next Steps

1. **Test Migration**: Follow testing steps above
2. **Validate Results**: Compare outputs between script and module
3. **Update Documentation**: Update any custom documentation referencing the script
4. **Monitor**: Monitor for issues in production environment
5. **Cleanup**: Remove Bash script after successful migration period

## Support

For migration assistance:

1. Review `docs/redhat_upload_module_migration_plan.md` for detailed technical information
2. Check `roles/must_gather_log/README.md` for module usage examples
3. Review `roles/must_gather_log/TESTING_CHECKLIST.md` for testing scenarios
