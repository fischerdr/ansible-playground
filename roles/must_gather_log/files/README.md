# Upload Script Documentation

## upload_to_redhat.sh

### Purpose

Uploads must-gather archive files to Red Hat support cases via the Red Hat Customer Portal API. This script handles authentication, proxy configuration, file validation, and multipart form upload.

### Usage

This script is invoked by the `must_gather_log` role and is not intended for standalone execution. It expects all configuration via environment variables.

### Environment Variables

#### Required

- `RH_API_TOKEN` - Red Hat API authentication token (Bearer token)
- `MG_ARCHIVE_FILE` - Full path to the must-gather archive file
- `MG_CASE_ID` - Red Hat support case number
- `MG_UPLOAD_DESC` - Description text for the uploaded attachment

#### Optional (Proxy Configuration)

- `RH_API_PROXY` - Proxy server URL (format: `host:port` or `http://host:port`)
- `RH_API_PROXY_USER` - Proxy authentication username
- `RH_API_PROXY_PASS` - Proxy authentication password

### Exit Codes

| Code | Constant | Description |
|------|----------|-------------|
| 0 | Success | Upload completed successfully |
| 10 | ERR_NO_TOKEN | RH_API_TOKEN environment variable not set |
| 11 | ERR_FILE_NOT_FOUND | Archive file not found or required variable missing |
| 12 | ERR_FILE_TOO_LARGE | Archive exceeds 1GB HTTP upload limit |
| 13 | ERR_CURL_FAILED | Network or SSL error during curl execution |
| 14 | ERR_HTTP_ERROR | HTTP response code indicates upload failure |

### Output

On success, the script outputs the JSON response body from the Red Hat API to stdout. This typically includes:

```json
{
  "fileName": "must-gather.tar.gz",
  "uuid": "attachment-uuid",
  "size": 12345678,
  "uploadDate": "2025-01-27T12:00:00Z"
}
```

### Error Handling

All errors are written to stderr with descriptive messages. The script uses strict error handling (`set -euo pipefail`) to ensure any command failure causes immediate exit.

### Security Considerations

- Never logs or exposes the `RH_API_TOKEN` value
- Proxy credentials are handled securely and not logged
- Designed for execution within AAP Execution Environments with credential injection
- Uses HTTPS for all API communication

### Maintenance

When updating this script:

1. Preserve the exit code constants for backward compatibility
2. Maintain the JSON output format for parsing in Ansible tasks
3. Test with and without proxy configuration
4. Verify error messages are descriptive for troubleshooting
5. Ensure no credentials are logged or exposed in output

### Testing

To test locally (requires valid credentials):

```bash
export RH_API_TOKEN="your-token-here"
export MG_ARCHIVE_FILE="/path/to/archive.tar.gz"
export MG_CASE_ID="01234567"
export MG_UPLOAD_DESC="Test upload"

./upload_to_redhat.sh
```

For proxy testing, additionally set:

```bash
export RH_API_PROXY="proxy.example.com:8080"
export RH_API_PROXY_USER="username"
export RH_API_PROXY_PASS="password"
```
