#!/usr/bin/env bash
# upload_to_redhat.sh
# Upload a file to Red Hat Support attachments API.
# Inputs (env):
#   MG_ARCHIVE_FILE   -> full path to archive (required)
#   MG_CASE_ID        -> Red Hat case id (required)
#   MG_UPLOAD_DESC    -> description text (optional)
#   RH_API_TOKEN      -> bearer token (preferred) OR
#   RH_API_USER       -> username (fallback) and
#   RH_API_PASS       -> password (fallback)
# Optional proxy vars:
#   HTTP_PROXY, HTTPS_PROXY, NO_PROXY
#
# Output: single JSON line to stdout with {"status":"ok",...} or {"status":"fail",...}
# Exit codes:
#   0 -> success
#   1..9 -> various failures (see code handling in script)

set -euo pipefail

json_out() { printf '%s\n' "$1"; }

# Validate env inputs
: "${MG_ARCHIVE_FILE:?MG_ARCHIVE_FILE must be set}"
: "${MG_CASE_ID:?MG_CASE_ID must be set}"

if [ ! -f "${MG_ARCHIVE_FILE}" ]; then
  json_out '{"status":"fail","msg":"archive not found"}'
  exit 2
fi

# Enforce 1 GiB limit
max_bytes=$((1024 * 1024 * 1024))
size=$(stat -c%s "${MG_ARCHIVE_FILE}" 2>/dev/null || echo 0)
if [ "$size" -eq 0 ]; then
  json_out '{"status":"fail","msg":"archive empty or unreadable"}'
  exit 3
fi
if [ "$size" -gt "$max_bytes" ]; then
  json_out "{\"status\":\"fail\",\"msg\":\"archive exceeds 1GiB limit\",\"size\":${size}}"
  exit 4
fi

# Determine auth parameters
auth_header=""
curl_auth=()
if [ -n "${RH_API_TOKEN:-}" ]; then
  auth_header="Authorization: Bearer ${RH_API_TOKEN}"
elif [ -n "${RH_API_USER:-}" ] && [ -n "${RH_API_PASS:-}" ]; then
  curl_auth=( -u "${RH_API_USER}:${RH_API_PASS}" )
else
  json_out '{"status":"fail","msg":"no authentication provided (set RH_API_TOKEN or RH_API_USER & RH_API_PASS)"}'
  exit 5
fi

# API endpoint (adjust if your RH API path differs)
API_BASE="https://api.access.redhat.com/support/v1"
UPLOAD_URL="${API_BASE}/cases/${MG_CASE_ID}/attachments"

curl_base=( --silent --show-error --fail --location )
if [ -n "${auth_header}" ]; then
  curl_base+=( -H "${auth_header}" -H "Accept: application/json" )
fi

# Build form fields
desc="${MG_UPLOAD_DESC:-must-gather upload from AAP}"

# Retry loop for transient errors
max_attempts=3
attempt=1
backoff=2

while [ $attempt -le $max_attempts ]; do
  tmp_resp="$(mktemp)"
  tmp_code="$(mktemp)"

  if curl "${curl_base[@]}" "${curl_auth[@]}" -o "${tmp_resp}" -w "%{http_code}" -F "description=${desc}" -F "file=@${MG_ARCHIVE_FILE}" "${UPLOAD_URL}" >"${tmp_code}" 2>/dev/null; then
    http_code="$(cat "${tmp_code}" 2>/dev/null || echo "")"
  else
    http_code="$(cat "${tmp_code}" 2>/dev/null || echo "")"
  fi

  resp_body="$(cat "${tmp_resp}" 2>/dev/null || echo '')"
  rm -f "${tmp_code}" "${tmp_resp}"

  # success codes 200/201
  if [ "${http_code}" = "200" ] || [ "${http_code}" = "201" ]; then
    # Return raw response as JSON-escaped string to avoid leaking secrets; consumer will parse if needed.
    # Avoid depending on jq. Escape quotes simply.
    resp_escaped="$(printf '%s' "${resp_body}" | sed -e 's/"/\\"/g' -e 's/\n/\\n/g')"
    json_out "{\"status\":\"ok\",\"http_code\":${http_code},\"response\":\"${resp_escaped}\"}"
    exit 0
  fi

  # non-retryable 4xx except 429
  if [ "${http_code:0:1}" = "4" ] && [ "${http_code}" != "429" ]; then
    resp_escaped="$(printf '%s' "${resp_body}" | sed -e 's/"/\\"/g' -e 's/\n/\\n/g')"
    json_out "{\"status\":\"fail\",\"http_code\":${http_code},\"response\":\"${resp_escaped}\"}"
    exit 6
  fi

  # transient; retry with backoff
  if [ $attempt -lt $max_attempts ]; then
    sleep "${backoff}"
    backoff=$((backoff * 2))
    attempt=$((attempt + 1))
    continue
  fi

  # final failure
  resp_escaped="$(printf '%s' "${resp_body}" | sed -e 's/"/\\"/g' -e 's/\n/\\n/g')"
  json_out "{\"status\":\"fail\",\"http_code\":${http_code:-0},\"response\":\"${resp_escaped}\"}"
  exit 7
done
