# Red Hat Upload Module Migration Plan

## Overview

This document outlines the requirements, design considerations, and implementation steps for migrating the Bash script-based Red Hat support case upload functionality (`upload_to_redhat_condense.sh`) and its corresponding Ansible task into a Python-based Ansible module.

## Current Implementation Analysis

### Current Architecture

**Bash Script**: `roles/must_gather_log/files/upload_to_redhat_condense.sh`

- Purpose: Upload must-gather archive parts to Red Hat support case via HTTP API
- Input: Environment variables (MG_CASE_ID, MG_ARCHIVE_PATTERN, MG_UPLOAD_DESC, RH_API_TOKEN, etc.)
- Output: JSON status to stdout
- Exit Codes: 0 (success), 1 (validation error), 2 (all failed), 3 (partial failure)

**Ansible Task**: `roles/must_gather_log/tasks/main_condense.yml` (lines 434-455)

- Uses `ansible.builtin.script` module to execute the Bash script
- Passes configuration via environment variables
- Handles exit codes and JSON parsing
- Implements `no_log: true` for security

### Functional Requirements

1. **File Pattern Expansion**: Support glob patterns and single file paths
2. **File Validation**: Check file existence, readability, size limits (1 GiB max)
3. **Multi-part Upload**: Upload multiple archive parts sequentially
4. **Retry Logic**: Per-file retry with exponential backoff
5. **Authentication**: Support token-based or username/password authentication
6. **Proxy Support**: HTTP/HTTPS proxy configuration
7. **Error Handling**: Categorize errors (retryable vs non-retryable)
8. **JSON Output**: Structured results with per-part status
9. **Exit Code Mapping**: Map upload status to appropriate exit codes

## Migration Requirements

### 1. Module Structure

#### 1.1 Directory Organization

```
roles/must_gather_log/
├── library/
│   └── redhat_upload.py          # New Python module
├── files/
│   └── upload_to_redhat_condense.sh  # Deprecated (to be removed)
└── tasks/
    └── main_condense.yml          # Updated to use new module
```

#### 1.2 Module Naming

- Module Name: `redhat_upload`
- File Name: `redhat_upload.py`
- FQCN: `redhat_upload` (or `community.redhat.upload` if creating a collection)

### 2. Module Interface Design

#### 2.1 Required Parameters

```yaml
case_id:
  description: Red Hat support case number
  type: str
  required: true

archive_pattern:
  description: Glob pattern for archive files or single file path
  type: str
  required: true

upload_description:
  description: Base upload description text
  type: str
  required: true
```

#### 2.2 Authentication Parameters

```yaml
api_token:
  description: Red Hat API authentication token (preferred)
  type: str
  required: false
  no_log: true

api_user:
  description: Red Hat API username (fallback authentication)
  type: str
  required: false
  no_log: true

api_pass:
  description: Red Hat API password (fallback authentication)
  type: str
  required: false
  no_log: true
```

#### 2.3 Optional Parameters

```yaml
proxy_http:
  description: HTTP proxy server URL
  type: str
  required: false
  default: null

proxy_https:
  description: HTTPS proxy server URL
  type: str
  required: false
  default: null

proxy_no:
  description: Comma-separated list of hosts to bypass proxy
  type: str
  required: false
  default: null

max_retry_attempts:
  description: Maximum retry attempts per file
  type: int
  required: false
  default: 3

retry_backoff_base:
  description: Base backoff seconds for retries
  type: int
  required: false
  default: 2

fail_on_partial:
  description: Fail if any part fails (true) or allow partial success (false)
  type: bool
  required: false
  default: true

max_file_size_bytes:
  description: Maximum file size in bytes (Red Hat API limit)
  type: int
  required: false
  default: 1073741824  # 1 GiB

validate_certs:
  description: Validate SSL certificates for HTTPS requests
  type: bool
  required: false
  default: true

timeout:
  description: Request timeout in seconds
  type: int
  required: false
  default: 300
```

#### 2.4 Return Values

```yaml
status:
  description: Overall upload status (success, failed, partial)
  type: str
  returned: always

case_id:
  description: Red Hat case number
  type: str
  returned: always

total_parts:
  description: Total number of archive parts processed
  type: int
  returned: always

success_count:
  description: Number of successfully uploaded parts
  type: int
  returned: always

failure_count:
  description: Number of failed upload parts
  type: int
  returned: always

results:
  description: Detailed per-part upload results
  type: list
  elements: dict
  returned: always
  contains:
    part:
      description: Part number (1-indexed)
      type: int
    file:
      description: Basename of uploaded file
      type: str
    status:
      description: Upload status (success, failed)
      type: str
    attempts:
      description: Number of retry attempts made
      type: int
    http_code:
      description: HTTP status code from API response
      type: int
      returned: when status is success or failed with HTTP error
    reason:
      description: Failure reason (curl_error, retryable_error_exhausted, non_retryable_error, unexpected_error)
      type: str
      returned: when status is failed
    curl_exit_code:
      description: curl exit code (if applicable)
      type: int
      returned: when reason is curl_error
    response:
      description: API response body (if applicable)
      type: str
      returned: when status is failed with HTTP error
```

### 3. Python Dependencies

#### 3.1 Standard Library Modules

- `json`: JSON serialization/deserialization
- `os`: File system operations, environment variables
- `glob`: File pattern matching
- `pathlib`: Path manipulation (Python 3.4+)
- `stat`: File metadata retrieval
- `time`: Sleep for retry delays
- `urllib.parse`: URL parsing and construction
- `urllib.request`: HTTP requests (alternative to requests library)

#### 3.2 External Dependencies (Optional)

**Option 1: Use Standard Library Only**

- Pros: No additional dependencies, works in minimal EEs
- Cons: More verbose code, manual JSON handling
- Recommendation: Use this approach for maximum compatibility

**Option 2: Use requests Library**

- Pros: Cleaner API, better error handling, automatic JSON handling
- Cons: Requires requests in EE
- Note: If using, add to `requirements.txt` and EE build requirements

**Recommendation**: Start with standard library (`urllib.request`) for maximum compatibility. Can migrate to `requests` later if needed.

#### 3.3 Ansible Module Requirements

- `ansible.module_utils.basic.AnsibleModule`: Core module framework
- `ansible.module_utils.common.text.converters`: Text conversion utilities (optional)

### 4. Implementation Components

#### 4.1 Core Classes/Functions

```python
class RedHatUploadController:
    """
    Main controller class for Red Hat upload operations.
    Handles file discovery, validation, upload orchestration, and result aggregation.
    """
    
    def __init__(self, module, params):
        """Initialize controller with AnsibleModule and parameters."""
        
    def validate_parameters(self):
        """Validate all input parameters."""
        
    def discover_files(self):
        """Expand archive_pattern and build file list."""
        
    def validate_file(self, file_path):
        """Validate single file (existence, readability, size)."""
        
    def build_upload_request(self, file_path, description):
        """Build HTTP multipart/form-data request for file upload."""
        
    def is_retryable_error(self, http_code):
        """Determine if HTTP error is retryable (5xx, 429)."""
        
    def upload_file_with_retry(self, file_path, part_number, total_parts):
        """Upload single file with retry logic and exponential backoff."""
        
    def execute_upload(self):
        """Main orchestration: discover, validate, upload all files."""
        
    def determine_final_status(self, results):
        """Determine overall status and exit code based on results."""
```

#### 4.2 HTTP Request Handling

**Using urllib.request (Standard Library)**:

```python
import urllib.request
import urllib.parse
import base64

def build_request(url, file_path, description, auth_token=None, auth_user=None, auth_pass=None):
    """Build multipart/form-data request with file upload."""
    
def execute_upload_request(request, proxy_config=None, timeout=300, validate_certs=True):
    """Execute HTTP request and return (http_code, response_body, error)."""
```

**Proxy Configuration**:

- Set `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY` environment variables or use `urllib.request.ProxyHandler`
- Configure proxy handler in `urllib.request.build_opener()`

#### 4.3 Error Handling Strategy

1. **Parameter Validation**: Fail fast with clear error messages
2. **File Discovery**: Return empty list if no files found, fail module
3. **File Validation**: Collect all validation errors before failing
4. **Upload Retries**: Implement exponential backoff with configurable max attempts
5. **HTTP Error Classification**:
   - Retryable: 5xx server errors, 429 rate limit
   - Non-retryable: 4xx client errors (except 429)
6. **Result Aggregation**: Collect all results, determine final status based on `fail_on_partial`

#### 4.4 JSON Output Structure

Maintain compatibility with existing JSON structure:

```json
{
  "status": "success|failed|partial",
  "case_id": "string",
  "total_parts": 0,
  "success_count": 0,
  "failure_count": 0,
  "results": [
    {
      "part": 1,
      "file": "filename.tar.gz",
      "status": "success|failed",
      "attempts": 1,
      "http_code": 200,
      "reason": "string (if failed)",
      "curl_exit_code": 0 (if curl_error),
      "response": "string (if failed with HTTP error)"
    }
  ]
}
```

### 5. Task Integration Changes

#### 5.1 Current Task (main_condense.yml)

```yaml
- name: "Upload all archive parts to Red Hat support case with retry handling"
  ansible.builtin.script:
    cmd: upload_to_redhat_condense.sh
  environment:
    MG_ARCHIVE_PATTERN: "{{ controller_temp_dir.path }}/*.tar.gz*"
    MG_CASE_ID: "{{ rh_case }}"
    # ... other environment variables
  delegate_to: localhost
  register: rh_upload_results
  failed_when: >-
    rh_upload_results.rc not in [0, 3] or
    (rh_upload_results.rc == 3 and (rh_upload_fail_on_partial | default(true) | bool))
  changed_when: rh_upload_results.rc in [0, 3]
  no_log: true
```

#### 5.2 Updated Task (Using Python Module)

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
  failed_when: >-
    rh_upload_results.status == 'failed' or
    (rh_upload_results.status == 'partial' and (rh_upload_fail_on_partial | default(true) | bool))
  changed_when: rh_upload_results.status in ['success', 'partial']
  no_log: true
```

#### 5.3 Result Parsing Changes

**Current**: Parse JSON from `stdout`

```yaml
- name: "Parse upload results from JSON output"
  ansible.builtin.set_fact:
    upload_status: "{{ rh_upload_results.stdout | from_json }}"
```

**Updated**: Direct access to module return values

```yaml
- name: "Set upload status from module results"
  ansible.builtin.set_fact:
    upload_status: "{{ rh_upload_results }}"
```

**Note**: The `upload_status` variable structure remains the same, so downstream tasks may not need changes.

### 6. Security Considerations

#### 6.1 Sensitive Data Handling

- Mark `api_token`, `api_user`, `api_pass` with `no_log: true` in module
- Use `AnsibleModule`'s `no_log_values` parameter
- Never log credentials in module output or error messages

#### 6.2 Certificate Validation

- Default `validate_certs: true` for production
- Allow override for internal/development environments
- Use `urllib.request` with `ssl.SSLContext` for certificate validation

#### 6.3 Input Sanitization

- Validate file paths to prevent directory traversal
- Validate case_id format (alphanumeric, reasonable length)
- Sanitize upload_description to prevent injection attacks

### 7. Testing Requirements

#### 7.1 Unit Testing

- Test file pattern expansion (glob, single file)
- Test file validation (existence, readability, size)
- Test retry logic with mocked HTTP responses
- Test error classification (retryable vs non-retryable)
- Test result aggregation and status determination

#### 7.2 Integration Testing

- Test with real Red Hat API (using test case)
- Test with proxy configuration
- Test with authentication (token and username/password)
- Test multi-part upload scenarios
- Test failure scenarios (network errors, API errors)

#### 7.3 Ansible Module Testing

- Use `ansible-test` for module validation
- Test with `ansible-playbook --check` (check mode)
- Validate module documentation structure
- Test with various Ansible versions (2.9+)

### 8. Documentation Requirements

#### 8.1 Module Documentation

- Complete `DOCUMENTATION` string with all parameters
- Include `EXAMPLES` section with common use cases
- Document `RETURN` values comprehensively
- Add author information and license

#### 8.2 Role Documentation

- Update `roles/must_gather_log/README.md` with module usage
- Document migration path from Bash script to module
- Update examples in role documentation

#### 8.3 Migration Guide

- Create migration guide for users transitioning from script to module
- Document breaking changes (if any)
- Provide compatibility matrix

### 9. Execution Environment Considerations

#### 9.1 EE Compatibility

- Ensure Python 3.9+ compatibility (check EE Python version)
- Verify standard library availability
- Test in minimal EE environment

#### 9.2 Dependencies

- If using `requests` library, add to EE requirements
- Document any EE-specific requirements
- Consider fallback to standard library if dependencies unavailable

#### 9.3 Performance

- Python module should have similar performance to Bash script
- Consider async operations for future optimization (not required for v1)

### 10. Migration Checklist

#### 10.1 Development Phase

- [ ] Create module structure (`library/redhat_upload.py`)
- [ ] Implement parameter validation
- [ ] Implement file discovery and validation
- [ ] Implement HTTP upload with retry logic
- [ ] Implement result aggregation
- [ ] Add comprehensive error handling
- [ ] Write module documentation (DOCUMENTATION, EXAMPLES, RETURN)

#### 10.2 Testing Phase

- [ ] Unit tests for core functionality
- [ ] Integration tests with Red Hat API
- [ ] Test with various file patterns and sizes
- [ ] Test authentication methods (token, username/password)
- [ ] Test proxy configuration
- [ ] Test error scenarios
- [ ] Validate module with `ansible-test`

#### 10.3 Integration Phase

- [ ] Update `main_condense.yml` task
- [ ] Update result parsing tasks
- [ ] Test end-to-end with role
- [ ] Verify backward compatibility with existing variables
- [ ] Update role documentation

#### 10.4 Cleanup Phase

- [ ] Mark Bash script as deprecated
- [ ] Remove Bash script after migration period
- [ ] Update role defaults if needed
- [ ] Update project documentation

#### 10.5 Deployment Phase

- [ ] Deploy to development environment
- [ ] Validate in staging environment
- [ ] Deploy to production with rollback plan
- [ ] Monitor for issues

### 11. Rollback Strategy

If issues arise with Python module:

1. **Immediate Rollback**: Revert to Bash script in `main_condense.yml`
2. **Gradual Migration**: Support both script and module with feature flag
3. **Documentation**: Keep Bash script documentation until migration complete

### 12. Future Enhancements

Potential improvements for future versions:

- Async/parallel uploads for multiple parts
- Progress reporting during uploads
- Resume capability for failed uploads
- Integration with Ansible callback plugins for better logging
- Support for additional authentication methods (OAuth, etc.)

## Summary

This migration involves:

1. **Creating** a new Python Ansible module (`redhat_upload.py`)
2. **Updating** the Ansible task to use the module instead of Bash script
3. **Maintaining** backward compatibility with existing variable structure
4. **Testing** thoroughly in execution environment context
5. **Documenting** the migration and usage patterns

The module should provide the same functionality as the Bash script while offering better integration with Ansible's error handling, idempotency checking, and result management capabilities.
