# Red Hat API Upload Test

This test playbook and module help diagnose Red Hat Customer Portal API upload issues by testing both `urllib` (Python standard library) and `requests` library implementations with comprehensive logging.

## Files Created

- **Module**: [roles/must_gather_log/library/test_upload.py](../roles/must_gather_log/library/test_upload.py)
- **Playbook**: [playbooks/test_redhat_upload.yml](./test_redhat_upload.yml)

## Prerequisites

1. Valid Red Hat Customer Portal case number
2. Red Hat API authentication (token or username/password)
3. Test file or ability to create one (playbook creates test file automatically)

## Usage

### Basic Usage with Token Authentication

```bash
ansible-playbook -i inventory/hosts.yml playbooks/test_redhat_upload.yml \
  -e "rh_case_id=04300286" \
  -e "rh_api_token=YOUR_API_TOKEN"
```

### With Username/Password Authentication

```bash
ansible-playbook -i inventory/hosts.yml playbooks/test_redhat_upload.yml \
  -e "rh_case_id=04300286" \
  -e "rh_api_user=your.email@example.com" \
  -e "rh_api_pass=YOUR_PASSWORD"
```

### With Proxy Configuration

```bash
ansible-playbook -i inventory/hosts.yml playbooks/test_redhat_upload.yml \
  -e "rh_case_id=04300286" \
  -e "rh_api_token=YOUR_API_TOKEN" \
  -e "proxy_https=https://proxy.example.com:8080"
```

### Using Vault for Credentials

```bash
# Store credentials in Ansible Vault
ansible-vault create group_vars/all/vault.yml

# Add to vault.yml:
# vault_rh_api_token: "your_token_here"
# vault_rh_case_id: "04300286"

# Run playbook
ansible-playbook -i inventory/hosts.yml playbooks/test_redhat_upload.yml \
  -e "rh_case_id={{ vault_rh_case_id }}" \
  -e "rh_api_token={{ vault_rh_api_token }}" \
  --ask-vault-pass
```

## Configuration Options

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `rh_case_id` | Red Hat case number | - | Yes |
| `rh_api_token` | Red Hat API token | - | Yes* |
| `rh_api_user` | Red Hat username | - | Yes* |
| `rh_api_pass` | Red Hat password | - | Yes* |
| `proxy_http` | HTTP proxy URL | - | No |
| `proxy_https` | HTTPS proxy URL | - | No |
| `proxy_no` | Proxy bypass hosts | - | No |
| `test_log_dir` | Log directory | `/tmp/redhat_upload_test` | No |
| `test_file_size_mb` | Test file size | 1 MB | No |
| `validate_ssl_certs` | Validate SSL certs | `true` | No |
| `upload_timeout` | Upload timeout | 300s | No |
| `cleanup_test_files` | Remove test files after run | `false` | No |

\* Either `rh_api_token` OR both `rh_api_user` and `rh_api_pass` required

## What the Test Does

1. **Creates test environment**
   - Creates log directory `/tmp/redhat_upload_test`
   - Generates random test file of specified size
   - Creates compressed tarball

2. **Test 1: urllib upload**
   - Uses Python standard library `urllib`
   - Tests multipart/form-data upload
   - Logs all request/response details

3. **Test 2: requests library upload**
   - Uses `requests` library (if available)
   - Tests same upload with different HTTP client
   - Compares results with urllib

4. **Comprehensive logging**
   - Detailed logs written to `/tmp/redhat_upload_test/`
   - Separate log files for each test method
   - Includes timing, headers, response bodies, error details

## Output and Logs

The playbook will create detailed log files in the test directory:

```text
/tmp/redhat_upload_test/
├── test_upload_urllib_{case_id}_{timestamp}.log
├── test_upload_requests_{case_id}_{timestamp}.log
├── test_upload.dat (test data file)
└── test_upload.tar.gz (compressed test file)
```

### Log File Contents

Each log includes:

- Session configuration (URLs, proxy, auth method)
- File size and request body size
- Full request headers (with redacted auth tokens)
- SSL/TLS configuration
- HTTP response code and timing
- Response headers and body
- Detailed error messages and stack traces

## Interpreting Results

### Success (HTTP 200-299)

```text
status: "success"
http_code: 200
method: "urllib" or "requests"
```

### HTTP 503 (Service Unavailable)

```text
status: "http_error"
http_code: 503
error: "HTTP 503"
response_body: "<HTML><HEAD>...</HEAD></HTML>"
```

This indicates Red Hat API server is temporarily unavailable or overloaded.

### Connection/Proxy Errors

```text
status: "url_error" or "proxy_error"
error: "Connection refused" or "Proxy connection failed"
```

Check network connectivity and proxy configuration.

### SSL/TLS Errors

```text
status: "ssl_error"
error: "Certificate verification failed"
```

Check certificate validation settings or network proxy SSL handling.

## Troubleshooting

### HTTP 503 Errors

- **Cause**: Red Hat API temporarily unavailable
- **Solution**: Implement longer retry delays (see main `redhat_upload.py` module)
- **Workaround**: Wait and retry later; check Red Hat service status

### Proxy Issues

- Verify proxy URL format: `http://proxy.example.com:8080`
- For HTTPS through HTTP proxy, urllib uses CONNECT tunneling
- Check if proxy requires authentication (not currently supported)

### SSL Certificate Errors

- Set `validate_ssl_certs: false` for testing (not recommended for production)
- Check if proxy performs SSL inspection (requires proxy CA cert)

### Authentication Failures (HTTP 401/403)

- Verify API token is valid and not expired
- Ensure credentials have permission to access the case
- Check if token has appropriate scopes

## Comparing urllib vs requests

The test runs both implementations to identify library-specific issues:

- **urllib**: Python standard library, no external dependencies
- **requests**: Third-party library, generally more user-friendly

If one succeeds and the other fails, it may indicate:

- Proxy handling differences
- SSL/TLS negotiation differences
- HTTP header formatting differences
- Connection pooling/keep-alive behavior

## Next Steps

After running the test:

1. Review log files in `/tmp/redhat_upload_test/`
2. Compare urllib vs requests results
3. If both fail with HTTP 503, consider:
   - Increasing retry attempts in production module
   - Adding longer backoff delays
   - Implementing jitter to avoid thundering herd
4. If authentication fails, verify credentials and permissions
5. If proxy errors occur, review proxy configuration and SSL handling

## Cleanup

To remove test files after running:

```bash
ansible-playbook -i inventory/hosts.yml playbooks/test_redhat_upload.yml \
  -e "rh_case_id=04300286" \
  -e "rh_api_token=YOUR_TOKEN" \
  -e "cleanup_test_files=true"
```

Or manually:

```bash
rm -rf /tmp/redhat_upload_test
```
