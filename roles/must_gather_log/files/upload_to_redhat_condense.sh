#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Purpose: Upload must-gather archive parts to Red Hat support case via HTTP API
# 
# This script handles multi-part archive uploads with per-part retry logic,
# granular error tracking, and comprehensive status reporting for enterprise
# automation environments.
#
# Environment Variables Required:
#   MG_CASE_ID          - Red Hat case number (required)
#   MG_ARCHIVE_PATTERN  - Glob pattern for archive files, or single file path (required)
#   MG_UPLOAD_DESC      - Base upload description text (required)
#   RH_API_TOKEN        - Red Hat API authentication token (preferred)
#   RH_API_USER         - Red Hat API username (fallback authentication)
#   RH_API_PASS         - Red Hat API password (fallback authentication)
#
# Optional Environment Variables:
#   HTTP_PROXY          - HTTP proxy server URL
#   HTTPS_PROXY         - HTTPS proxy server URL
#   NO_PROXY            - Comma-separated list of hosts to bypass proxy
#   MAX_RETRY_ATTEMPTS  - Maximum retry attempts per file (default: 3)
#   RETRY_BACKOFF_BASE  - Base backoff seconds for retries (default: 2)
#   FAIL_ON_PARTIAL     - Fail if any part fails (true/false, default: true)
#
# Output: JSON status to stdout with detailed results per file
# Exit Codes:
#   0  - All parts uploaded successfully
#   1  - Validation or configuration error
#   2  - All parts failed to upload
#   3  - Partial failure (some parts succeeded, some failed)

set -euo pipefail

# ==============================================================================
# Constants and Configuration
# ==============================================================================

readonly API_BASE="https://api.access.redhat.com/support/v1"
readonly MAX_FILE_SIZE_BYTES=$((1024 * 1024 * 1024))  # 1 GiB HTTP upload limit

# Exit codes
readonly EXIT_SUCCESS=0
readonly EXIT_VALIDATION_ERROR=1
readonly EXIT_ALL_FAILED=2
readonly EXIT_PARTIAL_FAILURE=3

# Retry configuration
readonly MAX_RETRY_ATTEMPTS="${MAX_RETRY_ATTEMPTS:-3}"
readonly RETRY_BACKOFF_BASE="${RETRY_BACKOFF_BASE:-2}"
readonly FAIL_ON_PARTIAL="${FAIL_ON_PARTIAL:-true}"

# HTTP status code categories
readonly HTTP_SUCCESS_MIN=200
readonly HTTP_SUCCESS_MAX=299
readonly HTTP_RATE_LIMIT=429

# ==============================================================================
# Utility Functions
# ==============================================================================

# Print error message to stderr
log_error() {
  echo "ERROR: $*" >&2
}

# Print warning message to stderr
log_warn() {
  echo "WARNING: $*" >&2
}

# Print info message to stderr
log_info() {
  echo "INFO: $*" >&2
}

# Check if jq is available and set flag
HAS_JQ=false
if command -v jq >/dev/null 2>&1; then
  # Verify jq works with a simple test
  if echo '{}' | jq . >/dev/null 2>&1; then
    HAS_JQ=true
    log_info "jq binary detected and functional"
  else
    log_warn "jq binary found but not functional, using fallback JSON handling"
  fi
else
  log_info "jq binary not found, using fallback JSON handling"
fi

# Output JSON to stdout (final result)
json_output() {
  printf '%s\n' "$1"
}

# Escape string for JSON
json_escape() {
  local string="$1"
  
  if [[ "${HAS_JQ}" == "true" ]]; then
    # Use jq for proper JSON string escaping
    printf '%s' "${string}" | jq -Rs .
  else
    # Fallback to sed-based escaping
    printf '"%s"' "$(printf '%s' "${string}" | \
      sed -e 's/\\/\\\\/g' \
          -e 's/"/\\"/g' \
          -e 's/\t/\\t/g' \
          -e 's/\r/\\r/g' \
          -e $'s/\n/\\\\n/g')"
  fi
}

# ==============================================================================
# Validation Functions
# ==============================================================================

validate_environment() {
  local errors=0

  # Validate required variables
  if [[ -z "${MG_CASE_ID:-}" ]]; then
    log_error "MG_CASE_ID environment variable is required"
    ((errors++))
  fi

  if [[ -z "${MG_ARCHIVE_PATTERN:-}" ]]; then
    log_error "MG_ARCHIVE_PATTERN environment variable is required"
    ((errors++))
  fi

  if [[ -z "${MG_UPLOAD_DESC:-}" ]]; then
    log_error "MG_UPLOAD_DESC environment variable is required"
    ((errors++))
  fi

  # Validate authentication
  if [[ -z "${RH_API_TOKEN:-}" ]]; then
    if [[ -z "${RH_API_USER:-}" ]] || [[ -z "${RH_API_PASS:-}" ]]; then
      log_error "Authentication required: Set RH_API_TOKEN or both RH_API_USER and RH_API_PASS"
      ((errors++))
    fi
  fi

  return "${errors}"
}

validate_file() {
  local file_path="$1"

  if [[ ! -f "${file_path}" ]]; then
    log_error "File not found: ${file_path}"
    return 1
  fi

  if [[ ! -r "${file_path}" ]]; then
    log_error "File not readable: ${file_path}"
    return 1
  fi

  local file_size
  file_size=$(stat -c %s "${file_path}" 2>/dev/null || echo 0)

  if [[ "${file_size}" -eq 0 ]]; then
    log_error "File is empty: ${file_path}"
    return 1
  fi

  if [[ "${file_size}" -gt "${MAX_FILE_SIZE_BYTES}" ]]; then
    log_error "File exceeds 1 GiB HTTP upload limit: ${file_path} (${file_size} bytes)"
    return 1
  fi

  return 0
}

# ==============================================================================
# Upload Functions
# ==============================================================================

build_curl_command() {
  local file_path="$1"
  local description="$2"
  local upload_url="${API_BASE}/cases/${MG_CASE_ID}/attachments"
  
  local curl_cmd=(
    curl
    --silent
    --show-error
    --location
    --write-out "\n%{http_code}"
  )

  # Add authentication
  if [[ -n "${RH_API_TOKEN:-}" ]]; then
    curl_cmd+=(
      -H "Authorization: Bearer ${RH_API_TOKEN}"
    )
  elif [[ -n "${RH_API_USER:-}" ]] && [[ -n "${RH_API_PASS:-}" ]]; then
    curl_cmd+=(
      -u "${RH_API_USER}:${RH_API_PASS}"
    )
  fi

  # Add common headers
  curl_cmd+=(
    -H "Accept: application/json"
  )

  # Add form data
  curl_cmd+=(
    -F "description=${description}"
    -F "file=@${file_path}"
  )

  # Add URL
  curl_cmd+=("${upload_url}")

  printf '%s\0' "${curl_cmd[@]}"
}

is_retryable_error() {
  local http_code="$1"

  # Retry on 5xx server errors or 429 rate limit
  if [[ "${http_code}" -ge 500 ]] || [[ "${http_code}" -eq "${HTTP_RATE_LIMIT}" ]]; then
    return 0
  fi

  return 1
}

upload_file_with_retry() {
  local file_path="$1"
  local part_number="$2"
  local total_parts="$3"
  local description="${MG_UPLOAD_DESC} - Part ${part_number}/${total_parts}"
  
  local attempt=1
  local backoff="${RETRY_BACKOFF_BASE}"
  local http_code=""
  local response_body=""
  local curl_exit_code=0

  log_info "Uploading part ${part_number}/${total_parts}: $(basename "${file_path}")"

  while [[ "${attempt}" -le "${MAX_RETRY_ATTEMPTS}" ]]; do
    if [[ "${attempt}" -gt 1 ]]; then
      log_info "Retry attempt ${attempt}/${MAX_RETRY_ATTEMPTS} for part ${part_number} after ${backoff}s delay"
      sleep "${backoff}"
    fi

    # Build curl command array
    local curl_cmd
    IFS=$'\0' read -r -d '' -a curl_cmd < <(build_curl_command "${file_path}" "${description}") || true

    # Execute curl and capture output
    local upload_output
    if upload_output=$("${curl_cmd[@]}" 2>&1); then
      curl_exit_code=0
    else
      curl_exit_code=$?
    fi

    # Parse response: last line is HTTP code, rest is body
    http_code=$(echo "${upload_output}" | tail -n1)
    response_body=$(echo "${upload_output}" | sed '$d' || echo "")

    # Check for curl execution failure
    if [[ "${curl_exit_code}" -ne 0 ]]; then
      log_warn "curl failed with exit code ${curl_exit_code} for part ${part_number} (attempt ${attempt})"
      
      if [[ "${attempt}" -lt "${MAX_RETRY_ATTEMPTS}" ]]; then
        backoff=$((backoff * 2))
        ((attempt++))
        continue
      else
        # Final attempt failed - build error JSON
        if [[ "${HAS_JQ}" == "true" ]]; then
          jq -nc \
            --arg part "${part_number}" \
            --arg file "$(basename "${file_path}")" \
            --arg status "failed" \
            --arg reason "curl_error" \
            --arg curl_exit "${curl_exit_code}" \
            --arg attempts "${attempt}" \
            '{part: ($part|tonumber), file: $file, status: $status, reason: $reason, curl_exit_code: ($curl_exit|tonumber), attempts: ($attempts|tonumber)}'
        else
          echo "{\"part\":${part_number},\"file\":$(json_escape "$(basename "${file_path}")"),\"status\":\"failed\",\"reason\":\"curl_error\",\"curl_exit_code\":${curl_exit_code},\"attempts\":${attempt}}"
        fi
        return 1
      fi
    fi

    # Check HTTP status code
    if [[ "${http_code}" -ge "${HTTP_SUCCESS_MIN}" ]] && [[ "${http_code}" -le "${HTTP_SUCCESS_MAX}" ]]; then
      log_info "Successfully uploaded part ${part_number}/${total_parts} (HTTP ${http_code})"
      
      # Build success JSON
      if [[ "${HAS_JQ}" == "true" ]]; then
        jq -nc \
          --arg part "${part_number}" \
          --arg file "$(basename "${file_path}")" \
          --arg status "success" \
          --arg http_code "${http_code}" \
          --arg attempts "${attempt}" \
          '{part: ($part|tonumber), file: $file, status: $status, http_code: ($http_code|tonumber), attempts: ($attempts|tonumber)}'
      else
        echo "{\"part\":${part_number},\"file\":$(json_escape "$(basename "${file_path}")"),\"status\":\"success\",\"http_code\":${http_code},\"attempts\":${attempt}}"
      fi
      return 0
    fi

    # Check if error is retryable
    if is_retryable_error "${http_code}"; then
      log_warn "Retryable error HTTP ${http_code} for part ${part_number} (attempt ${attempt})"
      
      if [[ "${attempt}" -lt "${MAX_RETRY_ATTEMPTS}" ]]; then
        backoff=$((backoff * 2))
        ((attempt++))
        continue
      else
        # Final retry exhausted - build error JSON with response
        log_error "Upload failed after ${attempt} attempts for part ${part_number}: HTTP ${http_code}"
        
        if [[ "${HAS_JQ}" == "true" ]]; then
          jq -nc \
            --arg part "${part_number}" \
            --arg file "$(basename "${file_path}")" \
            --arg status "failed" \
            --arg reason "retryable_error_exhausted" \
            --arg http_code "${http_code}" \
            --arg attempts "${attempt}" \
            --arg response "${response_body}" \
            '{part: ($part|tonumber), file: $file, status: $status, reason: $reason, http_code: ($http_code|tonumber), attempts: ($attempts|tonumber), response: $response}'
        else
          local escaped_response
          escaped_response=$(json_escape "${response_body}")
          echo "{\"part\":${part_number},\"file\":$(json_escape "$(basename "${file_path}")"),\"status\":\"failed\",\"reason\":\"retryable_error_exhausted\",\"http_code\":${http_code},\"attempts\":${attempt},\"response\":${escaped_response}}"
        fi
        return 1
      fi
    else
      # Non-retryable error (4xx except 429) - build error JSON
      log_error "Non-retryable error HTTP ${http_code} for part ${part_number}"
      
      if [[ "${HAS_JQ}" == "true" ]]; then
        jq -nc \
          --arg part "${part_number}" \
          --arg file "$(basename "${file_path}")" \
          --arg status "failed" \
          --arg reason "non_retryable_error" \
          --arg http_code "${http_code}" \
          --arg attempts "${attempt}" \
          --arg response "${response_body}" \
          '{part: ($part|tonumber), file: $file, status: $status, reason: $reason, http_code: ($http_code|tonumber), attempts: ($attempts|tonumber), response: $response}'
      else
        local escaped_response
        escaped_response=$(json_escape "${response_body}")
        echo "{\"part\":${part_number},\"file\":$(json_escape "$(basename "${file_path}")"),\"status\":\"failed\",\"reason\":\"non_retryable_error\",\"http_code\":${http_code},\"attempts\":${attempt},\"response\":${escaped_response}}"
      fi
      return 1
    fi
  done

  # Should not reach here - build unexpected error JSON
  log_error "Unexpected state in upload retry loop for part ${part_number}"
  
  if [[ "${HAS_JQ}" == "true" ]]; then
    jq -nc \
      --arg part "${part_number}" \
      --arg file "$(basename "${file_path}")" \
      --arg status "failed" \
      --arg reason "unexpected_error" \
      --arg attempts "${attempt}" \
      '{part: ($part|tonumber), file: $file, status: $status, reason: $reason, attempts: ($attempts|tonumber)}'
  else
    echo "{\"part\":${part_number},\"file\":$(json_escape "$(basename "${file_path}")"),\"status\":\"failed\",\"reason\":\"unexpected_error\",\"attempts\":${attempt}}"
  fi
  return 1
}

# ==============================================================================
# Main Execution Logic
# ==============================================================================

main() {
  # Validate environment first before using variables
  if ! validate_environment; then
    json_output '{"status":"error","message":"Environment validation failed"}'
    exit "${EXIT_VALIDATION_ERROR}"
  fi

  log_info "Starting must-gather upload to Red Hat case ${MG_CASE_ID}"

  # Expand file pattern and build file list
  local -a archive_files=()
  
  # Check if pattern is a single file or glob pattern
  if [[ -f "${MG_ARCHIVE_PATTERN}" ]]; then
    archive_files=("${MG_ARCHIVE_PATTERN}")
  else
    # Expand glob pattern using robust array assignment
    shopt -s nullglob
    archive_files=()
    for file in ${MG_ARCHIVE_PATTERN}; do
      archive_files+=("${file}")
    done
    shopt -u nullglob
  fi

  if [[ "${#archive_files[@]}" -eq 0 ]]; then
    log_error "No files found matching pattern: ${MG_ARCHIVE_PATTERN}"
    json_output '{"status":"error","message":"No archive files found"}'
    exit "${EXIT_VALIDATION_ERROR}"
  fi

  local total_parts="${#archive_files[@]}"
  log_info "Found ${total_parts} archive part(s) to upload"

  # Validate all files before attempting upload
  local validation_errors=0
  for file in "${archive_files[@]}"; do
    if ! validate_file "${file}"; then
      ((validation_errors++))
    fi
  done

  if [[ "${validation_errors}" -gt 0 ]]; then
    log_error "File validation failed for ${validation_errors} file(s)"
    json_output '{"status":"error","message":"File validation failed"}'
    exit "${EXIT_VALIDATION_ERROR}"
  fi

  # Upload each file and collect results
  local -a upload_results=()
  local part_number=1
  local success_count=0
  local failure_count=0

  for file in "${archive_files[@]}"; do
    local result
    if result=$(upload_file_with_retry "${file}" "${part_number}" "${total_parts}"); then
      upload_results+=("${result}")
      ((success_count++))
    else
      upload_results+=("${result}")
      ((failure_count++))
    fi
    ((part_number++))
  done

  # Determine final status
  local final_status
  local exit_code

  if [[ "${failure_count}" -eq 0 ]]; then
    final_status="success"
    exit_code="${EXIT_SUCCESS}"
    log_info "All ${total_parts} part(s) uploaded successfully"
  elif [[ "${success_count}" -eq 0 ]]; then
    final_status="failed"
    exit_code="${EXIT_ALL_FAILED}"
    log_error "All ${total_parts} part(s) failed to upload"
  else
    final_status="partial"
    exit_code="${EXIT_PARTIAL_FAILURE}"
    log_warn "${success_count}/${total_parts} part(s) uploaded successfully, ${failure_count} failed"
    
    # Override exit code if configured to fail on partial
    if [[ "${FAIL_ON_PARTIAL}" == "true" ]]; then
      exit_code="${EXIT_PARTIAL_FAILURE}"
    fi
  fi

  # Build final JSON output
  if [[ "${HAS_JQ}" == "true" ]]; then
    # Build results array string for jq parsing
    local results_array=""
    if [[ "${#upload_results[@]}" -gt 0 ]]; then
      for ((i=0; i<${#upload_results[@]}; i++)); do
        if [[ "${i}" -gt 0 ]]; then
          results_array+=","
        fi
        results_array+="${upload_results[i]}"
      done
    fi
    
    # Construct final JSON using jq
    # Use --arg with string, then parse with fromjson for proper array handling
    json_output "$(jq -nc \
      --arg status "${final_status}" \
      --arg case_id "${MG_CASE_ID}" \
      --arg total_parts "${total_parts}" \
      --arg success_count "${success_count}" \
      --arg failure_count "${failure_count}" \
      --arg results_str "[${results_array}]" \
      '{status: $status, case_id: $case_id, total_parts: ($total_parts|tonumber), success_count: ($success_count|tonumber), failure_count: ($failure_count|tonumber), results: ($results_str | fromjson)}')"
  else
    # Fallback to manual JSON construction
    local results_json=""
    for ((i=0; i<${#upload_results[@]}; i++)); do
      if [[ "${i}" -gt 0 ]]; then
        results_json+=","
      fi
      results_json+="${upload_results[i]}"
    done
    
    json_output "{\"status\":\"${final_status}\",\"case_id\":\"${MG_CASE_ID}\",\"total_parts\":${total_parts},\"success_count\":${success_count},\"failure_count\":${failure_count},\"results\":[${results_json}]}"
  fi

  exit "${exit_code}"
}

# ==============================================================================
# Script Entry Point
# ==============================================================================

main "$@"

