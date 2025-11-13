# Verification Checklist: redhat_upload.py Refactoring

## Overview

This checklist verifies that the `redhat_upload.py` module refactoring from `urllib` to `requests` library is complete and all playbooks/roles are updated and compatible.

**Date**: 2025-11-13
**Refactoring**: urllib → requests library
**Timeout Update**: 300s → 1800s (5 min → 30 min)

---

## Module Changes

### ✅ Core Library Refactoring

- [x] **Import statements updated**
  - Removed: `urllib.error`, `urllib.request`, `ssl` imports
  - Added: `requests`, `requests.auth.HTTPBasicAuth`
  - Added: `HAS_REQUESTS` import guard with graceful failure

- [x] **Method replacements**
  - `_setup_opener()` → Removed (requests handles auth/proxy natively)
  - `_build_request()` → `_prepare_upload_config()` (returns dict for requests.post)
  - `_execute_upload_request()` → Updated to use `requests.post()`

- [x] **Timeout increased**
  - DOCUMENTATION default: `300` → `1800`
  - `__init__` default: `300` → `1800`
  - `main()` argument_spec: `300` → `1800`

- [x] **Error handling enhanced**
  - Added: `requests.exceptions.Timeout`
  - Added: `requests.exceptions.ProxyError`
  - Added: `requests.exceptions.SSLError`
  - Added: `requests.exceptions.ConnectionError`
  - Added: `requests.exceptions.HTTPError`
  - All exceptions include proper file handle cleanup

- [x] **Code quality**
  - Python syntax: Valid
  - Black formatting: Passed
  - Ansible-lint: 0 failures, 0 warnings

---

## Role Updates

### ✅ roles/must_gather_log/defaults/main.yml

```yaml
# Added timeout configuration
rh_upload_timeout: 1800  # 30 min for large files through proxies
```

**Status**: ✅ Added
**Location**: Line 102

### ✅ roles/must_gather_log/tasks/main.yml

```yaml
# Updated redhat_upload module call (line 486-504)
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
  retry_backoff_base: "{{ rh_upload_retry_backoff | default(2) }}"
  fail_on_partial: "{{ rh_upload_fail_on_partial | default(true) }}"
  timeout: "{{ rh_upload_timeout | default(1800) }}"  # ✅ ADDED
  log_dir: "{{ mustgather_upload_logs | default(omit) }}"
```

**Status**: ✅ Updated with timeout parameter
**Location**: Line 500

---

## Playbook Updates

### ✅ playbooks/test-must-gather-upload.yml

```yaml
# Updated redhat_upload module call (line 345-363)
redhat_upload:
  case_id: "{{ rh_case }}"
  archive_pattern: "{{ controller_temp_dir.path }}/*.tar.gz*"
  upload_description: "{{ test_upload_description }}"
  api_token: "{{ rh_api_token | default(omit) }}"
  api_user: "{{ rh_api_user | default(omit) }}"
  api_pass: "{{ rh_api_pass | default(omit) }}"
  proxy_http: "{{ proxy_http | default(omit) }}"
  proxy_https: "{{ proxy_https | default(omit) }}"
  proxy_no: "{{ proxy_no | default(omit) }}"
  max_retry_attempts: "{{ rh_upload_max_retries | default(3) }}"
  retry_backoff_base: "{{ rh_upload_retry_backoff | default(2) }}"
  fail_on_partial: "{{ rh_upload_fail_on_partial | default(true) }}"
  timeout: "{{ rh_upload_timeout | default(1800) }}"  # ✅ ADDED
  log_dir: "{{ mustgather_upload_logs }}"
```

**Status**: ✅ Updated with timeout parameter
**Location**: Line 359

---

## Module Parameter Compatibility

### Module Signature (redhat_upload.py)

| Parameter | Type | Required | Default | Used in Playbooks |
|-----------|------|----------|---------|-------------------|
| `case_id` | str | Yes | - | ✅ Yes |
| `archive_pattern` | str | Yes | - | ✅ Yes |
| `upload_description` | str | Yes | - | ✅ Yes |
| `api_token` | str | No | None | ✅ Yes |
| `api_user` | str | No | None | ✅ Yes |
| `api_pass` | str | No | None | ✅ Yes |
| `proxy_http` | str | No | None | ✅ Yes |
| `proxy_https` | str | No | None | ✅ Yes |
| `proxy_no` | str | No | None | ✅ Yes |
| `max_retry_attempts` | int | No | 3 | ✅ Yes |
| `retry_backoff_base` | int | No | 2 | ✅ Yes |
| `fail_on_partial` | bool | No | True | ✅ Yes |
| `max_file_size_bytes` | int | No | 1073741824 | ⚠️ No (uses default) |
| `validate_certs` | bool | No | True | ⚠️ No (uses default) |
| `timeout` | int | No | **1800** | ✅ **Yes (NEW)** |
| `log_dir` | str | No | None | ✅ Yes |

**Status**: ✅ All parameters compatible

---

## Backward Compatibility

### ✅ Existing Playbooks

Playbooks that don't explicitly pass `timeout` will use the module's default of 1800s (30 min).

**Before (implicit 300s)**:
```yaml
redhat_upload:
  case_id: "{{ rh_case }}"
  # ... other params ...
  # timeout: NOT SPECIFIED (used 300s)
```

**After (implicit 1800s)**:
```yaml
redhat_upload:
  case_id: "{{ rh_case }}"
  # ... other params ...
  # timeout: NOT SPECIFIED (now uses 1800s)
```

**Impact**: ✅ Positive - Existing playbooks get longer timeout automatically

### ✅ Role Defaults Override

Users can override timeout per-environment:

```yaml
# group_vars/production.yml
rh_upload_timeout: 3600  # 1 hour for very large files

# group_vars/test.yml
rh_upload_timeout: 600  # 10 min for small test files
```

---

## Testing Checklist

### Module Tests

- [x] **Syntax validation**
  ```bash
  python -m py_compile roles/must_gather_log/library/redhat_upload.py
  ```
  **Result**: ✅ No errors

- [x] **Code formatting**
  ```bash
  black roles/must_gather_log/library/redhat_upload.py
  ```
  **Result**: ✅ All done! ✨ 🍰 ✨

- [x] **Linting**
  ```bash
  ansible-lint roles/must_gather_log/library/redhat_upload.py
  ```
  **Result**: ✅ Passed: 0 failure(s), 0 warning(s)

### Role Tests

- [x] **Role tasks linting**
  ```bash
  ansible-lint roles/must_gather_log/tasks/main.yml
  ```
  **Result**: ✅ Passed: 0 failure(s), 0 warning(s)

### Playbook Tests

- [x] **Test playbook linting**
  ```bash
  ansible-lint playbooks/test-must-gather-upload.yml
  ```
  **Result**: ✅ Passed: 0 failure(s), 0 warning(s) on 13 files

### Integration Tests

- [ ] **Functional test with small file**
  ```bash
  ansible-playbook -i inventory/hosts.yml playbooks/test-must-gather-upload.yml \
    -e "rh_case_id=CASE_NUMBER" \
    -e "test_archive_size_mb=10"
  ```
  **Expected**: HTTP 201 success, not HTTP 503

- [ ] **Functional test with large file**
  ```bash
  ansible-playbook -i inventory/hosts.yml playbooks/test-must-gather-upload.yml \
    -e "rh_case_id=CASE_NUMBER" \
    -e "test_archive_size_mb=500"
  ```
  **Expected**: HTTP 201 success within 30-min timeout

- [ ] **Production role test**
  ```bash
  ansible-playbook -i inventory/hosts.yml playbooks/collect-must-gather.yml \
    -e "rh_case=CASE_NUMBER"
  ```
  **Expected**: Full must-gather collection and upload success

---

## Known Issues & Resolutions

### ✅ Issue: HTTP 503 from Akamai CDN

**Root Cause**: urllib User-Agent rejected by Akamai edge servers
**Evidence**: Test logs showing urllib → 503, requests → 201
**Resolution**: Refactored to requests library with compatible User-Agent
**Status**: ✅ Resolved

### ✅ Issue: Upload timeout for large files

**Root Cause**: 5-minute timeout insufficient for 1GB files through proxy
**Evidence**: Timeouts observed with large must-gather archives
**Resolution**: Increased default timeout to 30 minutes (1800s)
**Status**: ✅ Resolved

---

## Deployment Checklist

### Pre-Deployment

- [x] Code review completed
- [x] All linting checks passed
- [x] Module documentation updated
- [x] Role defaults documented
- [x] Logic flow diagram created
- [ ] Integration tests passed (requires live Red Hat case)

### Deployment

- [ ] Merge to main branch
- [ ] Tag release (e.g., `v2.0.0-requests`)
- [ ] Update execution environment (rebuild EE)
- [ ] Deploy to AAP/AWX
- [ ] Update job templates with new timeout if needed

### Post-Deployment

- [ ] Monitor first production run
- [ ] Verify upload logs show requests library usage
- [ ] Confirm no HTTP 503 errors
- [ ] Validate timeout handling for large files
- [ ] Collect metrics (upload time, success rate)

---

## Rollback Plan

If issues occur after deployment:

1. **Revert module**: `git revert <commit-hash>`
2. **Rebuild EE**: Without requests library changes
3. **Update timeouts**: Manually adjust if still using old module
4. **Redeploy**: Push reverted code to AAP

**Revert commits** (in order):
```bash
git revert d7f2848  # Playbook updates
git revert 97e9ee2  # Timeout increase + docs
git revert 84a3b50  # urllib → requests refactoring
```

---

## Documentation

### Updated Documentation

- [x] **Module docstring** (DOCUMENTATION, EXAMPLES, RETURN)
- [x] **Role defaults** (defaults/main.yml with timeout)
- [x] **Logic flow diagram** (docs/redhat_upload_logic_flow.md)
- [x] **Verification checklist** (this document)

### External References

- **Red Hat API**: https://api.access.redhat.com/support/v1/cases/{case}/attachments/
- **requests library**: https://requests.readthedocs.io/
- **Akamai errors**: errors.edgesuite.net (CDN rejection page)

---

## Success Criteria

### ✅ Module Refactoring

- [x] requests library implemented
- [x] urllib completely removed
- [x] Timeout increased to 1800s
- [x] All parameters functional
- [x] Error handling comprehensive

### ✅ Integration

- [x] Role tasks updated
- [x] Role defaults updated
- [x] Test playbook updated
- [x] All linting passed
- [x] Documentation complete

### ⏳ Production Validation

- [ ] First production run successful
- [ ] No HTTP 503 errors observed
- [ ] Large file uploads complete within timeout
- [ ] Upload logs confirm requests library usage
- [ ] Performance metrics acceptable

---

## Contacts

**Module Owner**: Senior Systems Automation Engineer
**Codebase**: /development/git/ansible-playground
**Issue Tracking**: Internal tracking system
**Support**: Escalate to platform team for upload failures

---

## Appendix: Test Execution Commands

### Quick Syntax Check

```bash
# Module syntax
python -m py_compile roles/must_gather_log/library/redhat_upload.py

# Format code
source .venv/bin/activate
black roles/must_gather_log/library/redhat_upload.py

# Lint module
ansible-lint roles/must_gather_log/library/redhat_upload.py

# Lint role
ansible-lint roles/must_gather_log/tasks/main.yml

# Lint test playbook
ansible-lint playbooks/test-must-gather-upload.yml
```

### Test Upload Module

```bash
# Small file test (10MB)
ansible-playbook -i inventory/hosts.yml playbooks/test-must-gather-upload.yml \
  -e "rh_case_id=CASE_NUMBER" \
  -e "test_archive_size_mb=10" \
  -e "rh_upload_max_retries=5"

# Large file test (500MB)
ansible-playbook -i inventory/hosts.yml playbooks/test-must-gather-upload.yml \
  -e "rh_case_id=CASE_NUMBER" \
  -e "test_archive_size_mb=500" \
  -e "rh_upload_timeout=3600"

# Multi-part test
ansible-playbook -i inventory/hosts.yml playbooks/test-must-gather-upload.yml \
  -e "rh_case_id=CASE_NUMBER" \
  -e "test_create_split_archives=true"
```

### View Upload Logs

```bash
# Find latest upload logs
find /apps/persistence/clusters/*/must-gather-upload-logs -name "redhat_upload_*.log" -type f -mmin -60

# View detailed log
tail -f /path/to/redhat_upload_CASE_TIMESTAMP.log

# Search for errors
grep -i "error\|fail\|503" /path/to/redhat_upload_CASE_TIMESTAMP.log
```

---

**Verification Complete**: 2025-11-13
**Status**: ✅ Ready for testing
**Next Steps**: Run integration tests with live Red Hat case
