# redhat_upload.py - Logic Flow and Architecture

## Overview

The `redhat_upload` module uploads must-gather archive files to Red Hat Customer Portal support cases using the **requests library**. It provides robust retry logic, comprehensive error handling, and detailed logging for enterprise automation environments.

## Key Design Decisions

### Why requests instead of urllib?

**Problem**: urllib requests were rejected by Akamai CDN with HTTP 503 errors
**Solution**: requests library proven to work through Akamai CDN and corporate proxies
**Evidence**: Test results showed urllib = HTTP 503, requests = HTTP 201 success

### Timeout Configuration

- **Default**: 1800 seconds (30 minutes)
- **Rationale**: Large files (up to 1GB) through corporate proxies require extended timeouts
- **Configurable**: Can be overridden per playbook/task

---

## Module Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Module Entry Point                       │
│                           main()                                 │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ├─ Check HAS_REQUESTS (fail if not available)
                                  ├─ Initialize AnsibleModule with argument_spec
                                  ├─ Create RedHatUploadController instance
                                  │
                                  v
┌─────────────────────────────────────────────────────────────────┐
│                  RedHatUploadController                          │
│                       __init__()                                 │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ├─ Store all parameters (case_id, credentials, proxy, etc.)
                                  ├─ Setup logging (_setup_logging)
                                  ├─ Build upload_url
                                  │
                                  v
┌─────────────────────────────────────────────────────────────────┐
│                    Parameter Validation                          │
│                   validate_parameters()                          │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ├─ Validate case_id (non-empty string)
                                  ├─ Validate archive_pattern (non-empty string)
                                  ├─ Validate authentication (token OR user+pass)
                                  ├─ Validate retry configuration (attempts >= 1, backoff >= 1)
                                  │
                                  v
┌─────────────────────────────────────────────────────────────────┐
│                      File Discovery                              │
│                    execute_upload() →                            │
│                    discover_files()                              │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ├─ Check if archive_pattern is single file
                                  ├─ OR expand glob pattern (e.g., *.tar.gz*)
                                  ├─ Sort files for consistent ordering
                                  │
                                  v
┌─────────────────────────────────────────────────────────────────┐
│                      File Validation                             │
│                    validate_file()                               │
│                   (for each file)                                │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ├─ Check file exists
                                  ├─ Check is regular file (not directory)
                                  ├─ Check readable permissions
                                  ├─ Check not empty (size > 0)
                                  ├─ Check size <= max_file_size_bytes (1GB default)
                                  │
                                  v
┌─────────────────────────────────────────────────────────────────┐
│                   Upload Loop (Per File)                         │
│                 upload_file_with_retry()                         │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ├─ Build description: "{base} - Part {N}/{total}"
                                  ├─ Log file size and part number
                                  │
                                  v
                        ┌─────────────────┐
                        │ Retry Loop       │
                        │ (max attempts)   │
                        └─────────────────┘
                                  │
                                  ├─ If retry: sleep with exponential backoff (base * 2^attempt)
                                  │
                                  v
┌─────────────────────────────────────────────────────────────────┐
│                  Prepare Upload Configuration                    │
│                  _prepare_upload_config()                        │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ├─ Open file in binary mode
                                  ├─ Build files dict: {"file": (filename, file_handle, mime_type)}
                                  ├─ Build data dict: {"description": description}
                                  ├─ Build headers: Accept, User-Agent
                                  ├─ Add Authorization header if api_token provided
                                  ├─ Setup HTTPBasicAuth if api_user/api_pass provided
                                  ├─ Setup proxies dict: {http: proxy_http, https: proxy_https}
                                  │
                                  v
┌─────────────────────────────────────────────────────────────────┐
│                     Execute Upload Request                       │
│                  _execute_upload_request()                       │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ├─ Call requests.post() with:
                                  │   - upload_url
                                  │   - files (multipart/form-data auto-handled)
                                  │   - data (form fields)
                                  │   - headers
                                  │   - auth (HTTPBasicAuth or None)
                                  │   - proxies
                                  │   - timeout (1800s default)
                                  │   - verify (SSL cert validation)
                                  │
                                  v
                        ┌─────────────────┐
                        │ Success?         │
                        └─────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    v                           v
              ┌─────────┐                 ┌──────────┐
              │ SUCCESS │                 │  ERROR   │
              │ HTTP    │                 │          │
              │ 2xx     │                 └──────────┘
              └─────────┘                       │
                    │                           ├─ requests.exceptions.Timeout
                    │                           ├─ requests.exceptions.ProxyError
                    │                           ├─ requests.exceptions.SSLError
                    │                           ├─ requests.exceptions.ConnectionError
                    │                           ├─ requests.exceptions.HTTPError
                    │                           └─ Generic Exception
                    │                           │
                    ├─ Close file handle        ├─ Close file handle (try/except)
                    │                           │
                    v                           v
              ┌─────────────┐           ┌──────────────┐
              │ Return:     │           │ Return:      │
              │ (http_code, │           │ (http_code,  │
              │  body,      │           │  body,       │
              │  None)      │           │  exception)  │
              └─────────────┘           └──────────────┘
                    │                           │
                    └───────────┬───────────────┘
                                │
                                v
┌─────────────────────────────────────────────────────────────────┐
│                      Error Analysis                              │
│                  _is_retryable_error()                           │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ├─ If error is not None: RETRYABLE (connection error)
                                  ├─ If http_code >= 500: RETRYABLE (server error)
                                  ├─ If http_code == 429: RETRYABLE (rate limit)
                                  ├─ Otherwise: NON-RETRYABLE (4xx client errors)
                                  │
                                  v
                    ┌─────────────────────────┐
                    │ RETRYABLE?              │
                    └─────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    v                           v
            ┌────────────┐              ┌──────────────┐
            │ YES        │              │ NO           │
            │            │              │              │
            │ More       │              │ Return       │
            │ retries?   │              │ failure      │
            └────────────┘              │ result       │
                    │                   └──────────────┘
        ┌───────────┴──────────┐
        │                      │
        v                      v
    ┌───────┐            ┌─────────┐
    │ YES   │            │ NO      │
    │ Retry │            │ Return  │
    │ (loop)│            │ failure │
    └───────┘            └─────────┘
        │                      │
        └──────────────────────┘
                    │
                    v
┌─────────────────────────────────────────────────────────────────┐
│                    Build Result Object                           │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ├─ part: Part number (1-indexed)
                                  ├─ file: Filename (basename)
                                  ├─ status: "success" or "failed"
                                  ├─ attempts: Number of retry attempts made
                                  ├─ http_code: HTTP status code (if available)
                                  ├─ reason: Failure categorization (if failed)
                                  ├─ response: API response body (if error)
                                  │
                                  v
┌─────────────────────────────────────────────────────────────────┐
│                 Aggregate Results (All Files)                    │
│                      execute_upload()                            │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ├─ Count successes and failures
                                  ├─ Determine final status:
                                  │   - "success": All parts succeeded
                                  │   - "failed": All parts failed
                                  │   - "partial": Some succeeded, some failed
                                  │
                                  v
┌─────────────────────────────────────────────────────────────────┐
│                     Return to Ansible                            │
│                         main()                                   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ├─ If status == "failed": fail_json()
                                  ├─ If status == "partial" AND fail_on_partial: fail_json()
                                  ├─ Otherwise: exit_json(changed=True)
                                  │
                                  v
                            ┌─────────┐
                            │  DONE   │
                            └─────────┘
```

---

## Data Flow

### Input Parameters

```yaml
case_id: "04300286"                    # Red Hat case number
archive_pattern: "/tmp/*.tar.gz*"      # Files to upload
upload_description: "must-gather"      # Base description
api_user: "user@example.com"           # Authentication
api_pass: "password"                   # (or use api_token)
proxy_https: "http://proxy:9090"       # Corporate proxy
timeout: 1800                          # 30 minutes (default)
max_retry_attempts: 3                  # Retry count
retry_backoff_base: 2                  # Exponential backoff base
```

### Upload Configuration (Per File)

```python
upload_config = {
    "files": {
        "file": (
            "must-gather.tar.gz",      # filename
            <file_handle>,              # binary file object
            "application/octet-stream"  # MIME type
        )
    },
    "data": {
        "description": "must-gather - Part 1/3"
    },
    "headers": {
        "Accept": "application/json",
        "User-Agent": "python-requests/2.31.0",
        # "Authorization": "Bearer <token>"  # if token auth
    },
    "auth": HTTPBasicAuth("user", "pass"),  # if basic auth, else None
    "proxies": {
        "http": "http://proxy:9090",
        "https": "http://proxy:9090"
    }  # or None if no proxy
}
```

### HTTP Request (requests.post)

```http
POST https://api.access.redhat.com/support/v1/cases/04300286/attachments/
Content-Type: multipart/form-data; boundary=<auto-generated>
Accept: application/json
User-Agent: python-requests/2.31.0
Authorization: Basic <base64-encoded>

--<boundary>
Content-Disposition: form-data; name="description"

must-gather - Part 1/3
--<boundary>
Content-Disposition: form-data; name="file"; filename="must-gather.tar.gz"
Content-Type: application/octet-stream

<binary file content>
--<boundary>--
```

### Success Response

```json
HTTP/1.1 201 Created
Content-Type: application/json

{
  "caseNumber": "04300286",
  "uuid": "184c3527-e1d0-45d4-9850-e076c034dc49",
  "checksum": "cf6b2263667c54bfa4e18ad5f8ac6f4d...",
  "createdDate": "2025-11-13T18:28:36Z",
  "createdBy": "Engineering, ePaas2",
  "description": "must-gather - Part 1/3",
  "fileName": "must-gather.tar.gz",
  "fileType": "application/gzip",
  "id": "a09Hn00004DLOQRIA5"
}
```

### Module Return Value

```python
{
    "status": "success",              # or "failed", "partial"
    "case_id": "04300286",
    "total_parts": 3,
    "success_count": 3,
    "failure_count": 0,
    "results": [
        {
            "part": 1,
            "file": "must-gather.tar.gz.aa",
            "status": "success",
            "http_code": 201,
            "attempts": 1
        },
        {
            "part": 2,
            "file": "must-gather.tar.gz.ab",
            "status": "success",
            "http_code": 201,
            "attempts": 2  # required retry
        },
        {
            "part": 3,
            "file": "must-gather.tar.gz.ac",
            "status": "success",
            "http_code": 201,
            "attempts": 1
        }
    ]
}
```

---

## Retry Logic

### Exponential Backoff Algorithm

```
Attempt 1: No delay
Attempt 2: backoff_base * 2^1 = 2 * 2 = 4 seconds
Attempt 3: backoff_base * 2^2 = 2 * 4 = 8 seconds
Attempt 4: backoff_base * 2^3 = 2 * 8 = 16 seconds
Attempt 5: backoff_base * 2^4 = 2 * 16 = 32 seconds
```

### Retryable Errors

| Error Type | Retryable | Reason |
|------------|-----------|--------|
| HTTP 5xx | Yes | Server-side error (temporary) |
| HTTP 429 | Yes | Rate limiting (wait and retry) |
| HTTP 503 | Yes | Service unavailable (Akamai/API) |
| Connection Error | Yes | Network issue (transient) |
| Timeout | Yes | Slow network/large file |
| Proxy Error | Yes | Proxy connection issue |
| SSL Error | Yes | Certificate/handshake issue |
| HTTP 4xx | No | Client error (bad request) |
| HTTP 401/403 | No | Authentication failure |
| HTTP 404 | No | Invalid case ID |

### Retry Example Timeline

```
Upload Part 1/5 - Attempt 1
├─ 18:28:30 - Start upload
├─ 18:28:32 - HTTP 503 error (Akamai rejection)
├─ Retry attempt 2/3 after 2s delay
│
Upload Part 1/5 - Attempt 2
├─ 18:28:34 - Start upload
├─ 18:28:36 - HTTP 503 error
├─ Retry attempt 3/3 after 4s delay
│
Upload Part 1/5 - Attempt 3
├─ 18:28:40 - Start upload
├─ 18:28:44 - HTTP 201 success
└─ Upload complete (3 attempts, 14s total)
```

---

## Error Handling

### Error Categorization

```python
{
    "part": 2,
    "file": "must-gather.tar.gz.ab",
    "status": "failed",
    "reason": "retryable_error_exhausted",  # or:
                                             # - "connection_error"
                                             # - "non_retryable_error"
                                             # - "unexpected_error"
    "http_code": 503,
    "attempts": 3,
    "response": "<HTML>Internal Server Error</HTML>"
}
```

### Failure Scenarios

1. **No files found**: Module fails immediately
2. **File validation fails**: Module fails before upload
3. **All parts fail**: `status: "failed"`, module fails
4. **Some parts fail**: `status: "partial"`
   - If `fail_on_partial: true` (default): Module fails
   - If `fail_on_partial: false`: Module succeeds with warning
5. **All parts succeed**: `status: "success"`, module succeeds

---

## Logging

### Console Logging (module.log)

```
Starting upload - Part 1/3: must-gather.tar.gz (512.45 MB)
Preparing upload config for part 1, attempt 1
Executing upload request for part 1, attempt 1
Successfully uploaded part 1/3 (HTTP 201)
```

### File Logging (if log_dir provided)

```
2025-11-13 18:28:30 - redhat_upload_04300286 - INFO - Upload session started
2025-11-13 18:28:30 - redhat_upload_04300286 - INFO - Upload URL: https://api.access.redhat.com/...
2025-11-13 18:28:30 - redhat_upload_04300286 - INFO - Proxy HTTPS: http://proxy:9090
2025-11-13 18:28:30 - redhat_upload_04300286 - DEBUG - Preparing upload config for part 1
2025-11-13 18:28:30 - redhat_upload_04300286 - DEBUG - Executing upload request for part 1
2025-11-13 18:28:37 - redhat_upload_04300286 - INFO - ✓ Upload SUCCESS - Part 1/3 (HTTP 201, attempt 1)
```

---

## Performance Considerations

### Large File Handling

- **Memory**: Files opened in binary mode, streamed by requests library
- **Timeout**: 1800s (30 min) default for 1GB files through proxies
- **Progress**: Logs every 10 parts for large multi-part uploads
- **Estimation**: Calculates remaining time based on average upload speed

### Network Optimization

- **Connection**: `Connection: close` header (avoid keep-alive issues)
- **Proxy**: Native requests proxy support (no environment variable conflicts)
- **SSL/TLS**: Validates certificates by default, TLS 1.2+ via requests
- **Chunked Transfer**: Handled automatically by requests library

---

## Security

### Authentication Methods

1. **Bearer Token** (Preferred)
   - Header: `Authorization: Bearer <token>`
   - Tokens masked in logs: `***TOKEN_REDACTED***`

2. **Basic Authentication** (Fallback)
   - Uses `requests.auth.HTTPBasicAuth`
   - Credentials not logged (no_log=True)

### SSL/TLS

- **Certificate Validation**: Enabled by default (`verify=True`)
- **Disable for testing**: `validate_certs: false` (not recommended)
- **TLS Version**: Managed by requests library (modern defaults)

### Sensitive Data

- All authentication parameters marked `no_log: true`
- Log files redact authorization headers
- File content never logged (binary streaming)

---

## Dependencies

### Required

- `requests` library (v2.31.0 in EE)
- `ansible.module_utils.basic.AnsibleModule`

### Optional

- Logging directory (for detailed file logs)

### Execution Environment

Already included in `requirements.txt`:
```
requests==2.31.0
urllib3==2.2.1
```

---

## Testing

### Unit Tests

Not currently implemented. Recommended tests:
- File discovery and validation
- Retry logic with mocked responses
- Error categorization
- Timeout handling

### Integration Tests

Use `test_upload.py` module (created for diagnostics):
- Tests both urllib and requests implementations
- Validates proxy configuration
- Confirms Akamai CDN compatibility

---

## Future Enhancements

### Potential Improvements

1. **Parallel Uploads**: Upload multiple parts concurrently (thread pool)
2. **Resume Support**: Track uploaded parts, skip completed on retry
3. **Checksum Validation**: Verify MD5/SHA256 before/after upload
4. **Progress Callbacks**: Real-time progress reporting to Ansible
5. **Jitter in Backoff**: Add randomness to avoid thundering herd
6. **Adaptive Timeout**: Scale timeout based on file size
7. **Compression**: On-the-fly compression before upload

### Backward Compatibility

Module interface remains stable:
- Same input parameters
- Same return structure
- Drop-in replacement for urllib version
