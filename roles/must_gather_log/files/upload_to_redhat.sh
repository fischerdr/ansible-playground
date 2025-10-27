#!/bin/bash
# Purpose: Upload must-gather archive to Red Hat support case via HTTP API
# Environment Variables Required:
#   RH_API_TOKEN - Red Hat API authentication token (required)
#   MG_ARCHIVE_FILE - Path to must-gather archive file (required)
#   MG_CASE_ID - Red Hat case number (required)
#   MG_UPLOAD_DESC - Upload description text (required)
#   RH_API_PROXY - Proxy server URL (optional)
#   RH_API_PROXY_USER - Proxy username (optional)
#   RH_API_PROXY_PASS - Proxy password (optional)

set -euo pipefail

# Exit codes
readonly ERR_NO_TOKEN=10
readonly ERR_FILE_NOT_FOUND=11
readonly ERR_FILE_TOO_LARGE=12
readonly ERR_CURL_FAILED=13
readonly ERR_HTTP_ERROR=14

# Validate token presence
if [ -z "${RH_API_TOKEN:-}" ]; then
  echo "ERROR: RH_API_TOKEN not set in environment. Ensure AAP credential injects it." >&2
  exit ${ERR_NO_TOKEN}
fi

# Validate required parameters
if [ -z "${MG_ARCHIVE_FILE:-}" ]; then
  echo "ERROR: MG_ARCHIVE_FILE environment variable not set" >&2
  exit ${ERR_FILE_NOT_FOUND}
fi

if [ -z "${MG_CASE_ID:-}" ]; then
  echo "ERROR: MG_CASE_ID environment variable not set" >&2
  exit ${ERR_FILE_NOT_FOUND}
fi

# Ensure file exists
if [ ! -f "${MG_ARCHIVE_FILE}" ]; then
  echo "ERROR: file not found: ${MG_ARCHIVE_FILE}" >&2
  exit ${ERR_FILE_NOT_FOUND}
fi

# Enforce HTTP upload size limit (1 GiB)
file_size=$(stat -c %s "${MG_ARCHIVE_FILE}" 2>/dev/null || echo 0)
readonly MAX_BYTES=$((1024*1024*1024))
if [ "${file_size}" -gt "${MAX_BYTES}" ]; then
  echo "ERROR: file is larger than 1GB (HTTP upload limit). Size: ${file_size} bytes" >&2
  exit ${ERR_FILE_TOO_LARGE}
fi

# Configure proxy if provided
if [ -n "${RH_API_PROXY:-}" ]; then
  proxy_url="${RH_API_PROXY}"

  # Add authentication if credentials provided
  if [ -n "${RH_API_PROXY_USER:-}" ]; then
    # Add scheme if not present
    case "${proxy_url}" in
      http://*|https://*)
        ;;
      *)
        proxy_url="http://${proxy_url}"
        ;;
    esac

    # Insert credentials into proxy URL
    proxy_cred="${RH_API_PROXY_USER}:${RH_API_PROXY_PASS:-}"
    proxy_url="$(echo "${proxy_url}" | sed -E "s#^(https?://)#\1${proxy_cred}@#")"
  fi

  export HTTP_PROXY="${proxy_url}"
  export HTTPS_PROXY="${proxy_url}"
fi

# Perform multipart upload
upload_output=$(curl -sS -w "\n%{http_code}" \
  -H "Authorization: Bearer ${RH_API_TOKEN}" \
  -F "file=@${MG_ARCHIVE_FILE}" \
  -F "description=${MG_UPLOAD_DESC}" \
  "https://api.access.redhat.com/support/v1/cases/${MG_CASE_ID}/attachments/") || {
  echo "curl failed (network/ssl error)" >&2
  exit ${ERR_CURL_FAILED}
}

# Parse response
http_code=$(echo "${upload_output}" | tail -n1)
response_body=$(echo "${upload_output}" | sed '$d' || true)

# Check HTTP status
if [ "${http_code}" != "201" ] && [ "${http_code}" != "200" ]; then
  echo "Upload failed: HTTP ${http_code}" >&2
  echo "Response body:" >&2
  echo "${response_body}" >&2
  exit ${ERR_HTTP_ERROR}
fi

# Emit JSON response body
echo "${response_body}"