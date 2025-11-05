# Red Hat Upload Module Testing Checklist

## Overview

This document provides comprehensive testing scenarios for the `redhat_upload` Python Ansible module. The module replaces the Bash script (`upload_to_redhat_condense.sh`) and provides equivalent functionality with improved Ansible integration.

## Pre-Testing Verification

### Module Validation

- [ ] Module syntax validated: `python3 -m py_compile roles/must_gather_log/library/redhat_upload.py`
- [ ] Module is in correct location: `roles/must_gather_log/library/redhat_upload.py`
- [ ] Module imports are correct: `python3 -c "import sys; sys.path.insert(0, 'roles/must_gather_log/library'); import redhat_upload"`
- [ ] Code formatting validated: `isort --profile black`, `black --check`, `flake8`

### Ansible Module Testing

- [ ] Module documentation structure validated: `ansible-doc redhat_upload` (when module is in path)
- [ ] Module argument spec validated: Check `DOCUMENTATION` string
- [ ] Module return values validated: Check `RETURN` string

## Environment Setup

### Required Variables

```yaml
rh_case: "your-redhat-case-number"
rh_api_token: "your-api-token"
# OR
rh_api_user: "your-username"
rh_api_pass: "your-password"
```

### Optional Configuration

```yaml
rh_upload_max_retries: 3
rh_upload_fail_on_partial: true
proxy_http: "http://proxy.example.com:8080"
proxy_https: "https://proxy.example.com:8080"
proxy_no: "localhost,127.0.0.1"
```

## Test Scenarios

### Test 1: Single File Upload (Success Path)

**Setup**:

```yaml
- name: Upload single file
  redhat_upload:
    case_id: "12345678"
    archive_pattern: "/tmp/test-archive.tar.gz"
    upload_description: "Test upload single file"
    api_token: "valid-token-here"
  register: result
  no_log: true
```

**Expected Result**:

- Module succeeds (no failure)
- `result.status == "success"`
- `result.total_parts == 1`
- `result.success_count == 1`
- `result.failure_count == 0`
- `result.results[0].status == "success"`
- `result.results[0].http_code` in [200, 201, 202]

**Validation**:

```yaml
- name: Verify single file upload
  ansible.builtin.assert:
    that:
      - result.status == "success"
      - result.total_parts == 1
      - result.success_count == 1
      - result.results[0].status == "success"
```

### Test 2: Multi-Part Upload (Success Path)

**Setup**:

```yaml
- name: Upload multiple parts
  redhat_upload:
    case_id: "12345678"
    archive_pattern: "/tmp/test-archive.tar.gz.part*"
    upload_description: "Test upload multiple parts"
    api_token: "valid-token-here"
  register: result
  no_log: true
```

**Expected Result**:

- Module succeeds (no failure)
- `result.status == "success"`
- `result.total_parts == 3` (or number of parts)
- `result.success_count == result.total_parts`
- `result.failure_count == 0`
- All parts in `result.results` have `status == "success"`

**Validation**:

```yaml
- name: Verify multi-part upload
  ansible.builtin.assert:
    that:
      - result.status == "success"
      - result.total_parts > 1
      - result.success_count == result.total_parts
      - result.failure_count == 0
```

### Test 3: Invalid Authentication

**Setup**:

```yaml
- name: Test invalid authentication
  redhat_upload:
    case_id: "12345678"
    archive_pattern: "/tmp/test-archive.tar.gz"
    upload_description: "Test invalid auth"
    api_token: "invalid-token"
  register: result
  failed_when: false
  no_log: true
```

**Expected Result**:

- Module fails (or succeeds with failures depending on `fail_on_partial`)
- `result.status == "failed"` or `result.status == "partial"`
- `result.results[0].status == "failed"`
- `result.results[0].reason == "non_retryable_error"`
- `result.results[0].http_code` in [401, 403]

**Validation**:

```yaml
- name: Verify authentication failure
  ansible.builtin.assert:
    that:
      - result.status in ["failed", "partial"]
      - result.results[0].status == "failed"
      - result.results[0].reason == "non_retryable_error"
```

### Test 4: Invalid Case ID

**Setup**:

```yaml
- name: Test invalid case ID
  redhat_upload:
    case_id: "99999999"  # Non-existent case
    archive_pattern: "/tmp/test-archive.tar.gz"
    upload_description: "Test invalid case"
    api_token: "valid-token-here"
  register: result
  failed_when: false
  no_log: true
```

**Expected Result**:

- Module fails (or succeeds with failures)
- `result.status in ["failed", "partial"]`
- `result.results[0].status == "failed"`
- `result.results[0].reason == "non_retryable_error"`
- `result.results[0].http_code` in [404, 403]

### Test 5: Retry Logic with Transient Errors

**Setup**:

```yaml
- name: Test retry logic
  redhat_upload:
    case_id: "12345678"
    archive_pattern: "/tmp/test-archive.tar.gz"
    upload_description: "Test retry logic"
    api_token: "valid-token-here"
    max_retry_attempts: 3
    retry_backoff_base: 2
  register: result
  no_log: true
```

**Expected Result**:

- Module attempts retries on 5xx errors or 429 rate limits
- Exponential backoff is applied (2s, 4s, 8s)
- Maximum retry attempts are respected
- `result.results[0].attempts` <= `max_retry_attempts`

**Notes**: This is difficult to test without mocking. Monitor module logs to verify retry behavior.

### Test 6: Partial Upload Failure

**Setup**:
Create multiple files, but simulate one failing (e.g., invalid file or network issue):

```yaml
- name: Test partial failure
  redhat_upload:
    case_id: "12345678"
    archive_pattern: "/tmp/test-archive.tar.gz.part*"
    upload_description: "Test partial failure"
    api_token: "valid-token-here"
    fail_on_partial: false
  register: result
  no_log: true
```

**Expected Result**:

- Module succeeds (because `fail_on_partial: false`)
- `result.status == "partial"`
- `result.success_count > 0`
- `result.failure_count > 0`
- `result.success_count + result.failure_count == result.total_parts`

**Validation**:

```yaml
- name: Verify partial failure handling
  ansible.builtin.assert:
    that:
      - result.status == "partial"
      - result.success_count > 0
      - result.failure_count > 0
```

### Test 7: Parameter Validation

**Test Missing case_id**:

```yaml
- name: Test missing case_id
  redhat_upload:
    archive_pattern: "/tmp/test.tar.gz"
    upload_description: "Test"
    api_token: "test"
  register: result
  failed_when: false
  no_log: true
```

**Expected**: Module fails with validation error message about missing `case_id`

**Test Missing Authentication**:

```yaml
- name: Test missing authentication
  redhat_upload:
    case_id: "12345678"
    archive_pattern: "/tmp/test.tar.gz"
    upload_description: "Test"
  register: result
  failed_when: false
  no_log: true
```

**Expected**: Module fails with validation error message about missing authentication

### Test 8: File Pattern Expansion

**Test Glob Pattern**:

```yaml
- name: Test glob pattern
  redhat_upload:
    case_id: "12345678"
    archive_pattern: "/tmp/archives/*.tar.gz*"
    upload_description: "Test glob pattern"
    api_token: "valid-token"
  register: result
  no_log: true
```

**Expected**: All matching files are discovered and uploaded

**Test Single File**:

```yaml
- name: Test single file
  redhat_upload:
    case_id: "12345678"
    archive_pattern: "/tmp/single-archive.tar.gz"
    upload_description: "Test single file"
    api_token: "valid-token"
  register: result
  no_log: true
```

**Expected**: Single file is uploaded

### Test 9: File Validation

**Test Non-Existent File**:

```yaml
- name: Test non-existent file
  redhat_upload:
    case_id: "12345678"
    archive_pattern: "/tmp/non-existent.tar.gz"
    upload_description: "Test non-existent file"
    api_token: "valid-token"
  register: result
  failed_when: false
  no_log: true
```

**Expected**: Module fails with validation error about file not found

**Test Empty File**:

```yaml
- name: Create empty file
  ansible.builtin.file:
    path: "/tmp/empty.tar.gz"
    state: touch

- name: Test empty file
  redhat_upload:
    case_id: "12345678"
    archive_pattern: "/tmp/empty.tar.gz"
    upload_description: "Test empty file"
    api_token: "valid-token"
  register: result
  failed_when: false
  no_log: true
```

**Expected**: Module fails with validation error about empty file

**Test File Size Limit**:

```yaml
- name: Create large file (simulate)
  ansible.builtin.command:
    cmd: "dd if=/dev/zero of=/tmp/large.tar.gz bs=1M count=1025"
  # Creates 1.025GB file (exceeds 1GB limit)

- name: Test file size limit
  redhat_upload:
    case_id: "12345678"
    archive_pattern: "/tmp/large.tar.gz"
    upload_description: "Test file size limit"
    api_token: "valid-token"
    max_file_size_bytes: 1073741824  # 1GB
  register: result
  failed_when: false
  no_log: true
```

**Expected**: Module fails with validation error about file size limit

### Test 10: Proxy Configuration

**Test with HTTP Proxy**:

```yaml
- name: Test with proxy
  redhat_upload:
    case_id: "12345678"
    archive_pattern: "/tmp/test.tar.gz"
    upload_description: "Test proxy"
    api_token: "valid-token"
    proxy_http: "http://proxy.example.com:8080"
    proxy_https: "https://proxy.example.com:8080"
    proxy_no: "localhost,127.0.0.1"
  register: result
  no_log: true
```

**Expected**: Module uses proxy for requests (verify in network logs or proxy logs)

### Test 11: Authentication Methods

**Test Token Authentication**:

```yaml
- name: Test token auth
  redhat_upload:
    case_id: "12345678"
    archive_pattern: "/tmp/test.tar.gz"
    upload_description: "Test token auth"
    api_token: "valid-token"
  register: result
  no_log: true
```

**Expected**: Module uses Bearer token authentication

**Test Username/Password Authentication**:

```yaml
- name: Test user/pass auth
  redhat_upload:
    case_id: "12345678"
    archive_pattern: "/tmp/test.tar.gz"
    upload_description: "Test user/pass auth"
    api_user: "username"
    api_pass: "password"
  register: result
  no_log: true
```

**Expected**: Module uses Basic authentication

## Ansible Integration Testing

### Test 1: Role Execution

```bash
cd /development/git/ansible-playground

ansible-playbook playbooks/test_redhat_upload_module.yml \
  -e rh_case="12345678" \
  -e rh_api_token="valid-token" \
  -e test_single_file=true \
  -e test_multi_part=true
```

### Test 2: Verify Module Integration

Check that the module is properly integrated into the role:

```yaml
- name: Verify module is used in role
  ansible.builtin.debug:
    msg: "Module is integrated in main_condense.yml task"
```

### Test 3: Verify Result Parsing

Check that Ansible properly parses the module return values:

```yaml
- name: Verify result structure
  ansible.builtin.assert:
    that:
      - upload_result.status is defined
      - upload_result.case_id is defined
      - upload_result.total_parts is defined
      - upload_result.results is defined
      - upload_result.results | length > 0
```

## Success Criteria

- [ ] All validation tests pass
- [ ] Single file upload succeeds
- [ ] Multi-part upload succeeds
- [ ] Error cases handled gracefully
- [ ] Return values are structured correctly
- [ ] Retry logic functions correctly
- [ ] Authentication methods work
- [ ] Proxy configuration works
- [ ] Ansible integration works end-to-end
- [ ] No syntax errors or unhandled exceptions
- [ ] Module logs provide clear troubleshooting information

## Troubleshooting

### Module Not Found

**Symptoms**: `module 'redhat_upload' not found`

**Possible Causes**:

- Module not in library path
- Module syntax errors
- Ansible module search path incorrect

**Debug Steps**:

1. Verify module location: `ls roles/must_gather_log/library/redhat_upload.py`
2. Check module syntax: `python3 -m py_compile roles/must_gather_log/library/redhat_upload.py`
3. Test module import: `python3 -c "import sys; sys.path.insert(0, 'roles/must_gather_log/library'); import redhat_upload"`

### Authentication Failures

**Symptoms**: HTTP 401 or 403 errors

**Possible Causes**:

- Invalid or expired API token
- Incorrect username/password
- API token lacks required permissions

**Debug Steps**:

1. Verify token is valid
2. Check token expiration
3. Verify case access permissions
4. Try regenerating API token

### Upload Failures

**Symptoms**: Upload status shows failures

**Possible Causes**:

- Network connectivity issues
- Proxy configuration problems
- File validation failures
- API rate limiting

**Debug Steps**:

1. Check `upload_result.results` for per-part details
2. Review HTTP status codes
3. Verify network connectivity to `api.access.redhat.com`
4. Check proxy configuration if applicable
5. Review module logs for detailed error messages

### File Pattern Issues

**Symptoms**: No files found or wrong files uploaded

**Possible Causes**:

- Incorrect glob pattern
- Files not in expected location
- Permission issues

**Debug Steps**:

1. Verify pattern matches files: `ls /path/to/pattern`
2. Check file permissions
3. Test pattern manually: `python3 -c "import glob; print(glob.glob('/path/to/pattern'))"`

## Reporting Issues

When reporting issues, include:

1. Module version (check `redhat_upload.py` header)
2. Ansible version: `ansible --version`
3. Python version: `python3 --version`
4. Complete error output (redact sensitive data)
5. Module return values (redact sensitive data)
6. Test playbook used
7. Network configuration (proxy, etc.)
8. Execution environment details

## Migration from Bash Script

If migrating from the Bash script (`upload_to_redhat_condense.sh`), see:

- `docs/redhat_upload_module_migration_guide.md` for migration steps
- `docs/redhat_upload_module_migration_plan.md` for technical details
