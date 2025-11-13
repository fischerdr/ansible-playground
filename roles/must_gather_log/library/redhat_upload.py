#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# redhat_upload.py
# Ansible module to upload must-gather archive parts to Red Hat support case via HTTP API
#
# This module handles multi-part archive uploads with per-part retry logic,
# granular error tracking, and comprehensive status reporting for enterprise
# automation environments.
#
# Author: Senior Systems Automation Engineer
# License: Apache-2.0

from __future__ import annotations

import glob
import os
import ssl
import time
from typing import Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import (
    BaseHandler,
    HTTPBasicAuthHandler,
    HTTPPasswordMgrWithDefaultRealm,
    ProxyHandler,
    Request,
    build_opener,
    install_opener,
)

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r"""
---
module: redhat_upload
short_description: Upload must-gather archive parts to Red Hat support case via HTTP API
description:
  - Upload must-gather archive parts to Red Hat support case via HTTP API
  - Handles multi-part archive uploads with per-part retry logic
  - Supports exponential backoff for retryable errors
  - Provides granular error tracking and comprehensive status reporting
  - Intended for use in Ansible Execution Environments (EEs)
  - Uses Red Hat API endpoint: C(https://api.access.redhat.com/support/v1/cases/<case_number>/attachments/)
  - HTTP uploads have a 1GB size limit per file (SFTP has no limit but is not supported by this module)
  - Supports both Bearer token authentication and Basic authentication (username/password)
notes:
  - The Red Hat API requires multipart/form-data with fields C(file) and C(description)
  - Example curl command: C(curl -u <username> -F "file=@<path>" -F "description=<desc>" -X POST https://api.access.redhat.com/support/v1/cases/<case>/attachments/)
  - For files larger than 1GB, use SFTP upload (not supported by this module) or split archives into multiple parts
options:
  case_id:
    description:
      - Red Hat support case number
    type: str
    required: true
  archive_pattern:
    description:
      - Glob pattern for archive files or single file path
      - Supports shell-style glob patterns (e.g., /path/to/*.tar.gz*)
      - Can be a single file path
    type: str
    required: true
  upload_description:
    description:
      - Base upload description text
      - Each part will be appended with " - Part X/Y" automatically
    type: str
    required: true
  api_token:
    description:
      - Red Hat API authentication token (preferred authentication method)
      - Mutually exclusive with api_user/api_pass
    type: str
    required: false
    no_log: true
  api_user:
    description:
      - Red Hat API username (fallback authentication method)
      - Required if api_token is not provided
      - Must be used together with api_pass
    type: str
    required: false
    no_log: true
  api_pass:
    description:
      - Red Hat API password (fallback authentication method)
      - Required if api_token is not provided
      - Must be used together with api_user
    type: str
    required: false
    no_log: true
  proxy_http:
    description:
      - HTTP proxy server URL (e.g., http://proxy.example.com:8080)
    type: str
    required: false
    default: null
  proxy_https:
    description:
      - HTTPS proxy server URL (e.g., https://proxy.example.com:8080)
    type: str
    required: false
    default: null
  proxy_no:
    description:
      - Comma-separated list of hosts to bypass proxy
    type: str
    required: false
    default: null
  max_retry_attempts:
    description:
      - Maximum retry attempts per file
    type: int
    required: false
    default: 3
  retry_backoff_base:
    description:
      - Base backoff seconds for retries (exponential backoff: base * 2^attempt)
    type: int
    required: false
    default: 2
  fail_on_partial:
    description:
      - Fail if any part fails (true) or allow partial success (false)
      - When false, module returns success even if some parts fail
    type: bool
    required: false
    default: true
  max_file_size_bytes:
    description:
      - Maximum file size in bytes (Red Hat API limit is 1 GiB)
    type: int
    required: false
    default: 1073741824
  validate_certs:
    description:
      - Validate SSL certificates for HTTPS requests
      - Set to false only for internal/development environments
    type: bool
    required: false
    default: true
  timeout:
    description:
      - Request timeout in seconds
    type: int
    required: false
    default: 300
author:
  - Senior Systems Automation Engineer
"""

EXAMPLES = r"""
- name: Upload archive parts to Red Hat support case with token authentication
  redhat_upload:
    case_id: "01234567"
    archive_pattern: "/tmp/archives/*.tar.gz*"
    upload_description: "must-gather for cluster-1"
    api_token: "{{ vault_rh_api_token }}"
    max_retry_attempts: 5
    fail_on_partial: true

- name: Upload single archive file with username/password authentication
  redhat_upload:
    case_id: "01234567"
    archive_pattern: "/tmp/must-gather.tar.gz"
    upload_description: "must-gather for cluster-1"
    api_user: "{{ vault_rh_api_user }}"
    api_pass: "{{ vault_rh_api_pass }}"
    proxy_https: "https://proxy.example.com:8080"

- name: Upload archives allowing partial success
  redhat_upload:
    case_id: "01234567"
    archive_pattern: "{{ controller_temp_dir.path }}/*.tar.gz*"
    upload_description: "{{ computed_upload_description }}"
    api_token: "{{ rh_api_token }}"
    fail_on_partial: false
    max_retry_attempts: 3
"""

RETURN = r"""
status:
  description: Overall upload status (success, failed, partial)
  type: str
  returned: always
  sample: "success"
case_id:
  description: Red Hat case number
  type: str
  returned: always
  sample: "01234567"
total_parts:
  description: Total number of archive parts processed
  type: int
  returned: always
  sample: 3
success_count:
  description: Number of successfully uploaded parts
  type: int
  returned: always
  sample: 3
failure_count:
  description: Number of failed upload parts
  type: int
  returned: always
  sample: 0
results:
  description: Detailed per-part upload results
  type: list
  elements: dict
  returned: always
  contains:
    part:
      description: Part number (1-indexed)
      type: int
      sample: 1
    file:
      description: Basename of uploaded file
      type: str
      sample: "must-gather.tar.gz"
    status:
      description: Upload status (success, failed)
      type: str
      sample: "success"
    attempts:
      description: Number of retry attempts made
      type: int
      sample: 1
    http_code:
      description: HTTP status code from API response
      type: int
      returned: when status is success or failed with HTTP error
      sample: 200
    reason:
      description: Failure reason (connection_error, retryable_error_exhausted, non_retryable_error, unexpected_error)
      type: str
      returned: when status is failed
      sample: "non_retryable_error"
    response:
      description: API response body (if applicable)
      type: str
      returned: when status is failed with HTTP error
      sample: "{\"error\": \"Invalid case ID\"}"
"""

# Constants
API_BASE = "https://api.access.redhat.com/support/v1"
HTTP_SUCCESS_MIN = 200
HTTP_SUCCESS_MAX = 299
HTTP_RATE_LIMIT = 429


class RedHatUploadController:
    """Controller class for Red Hat upload operations."""

    def __init__(self, module: AnsibleModule, params: Dict):
        """Initialize controller with AnsibleModule and parameters."""
        self.module = module
        self.case_id = params.get("case_id")
        self.archive_pattern = params.get("archive_pattern")
        self.upload_description = params.get("upload_description")
        self.api_token = params.get("api_token")
        self.api_user = params.get("api_user")
        self.api_pass = params.get("api_pass")
        self.proxy_http = params.get("proxy_http")
        self.proxy_https = params.get("proxy_https")
        self.proxy_no = params.get("proxy_no")
        self.max_retry_attempts = params.get("max_retry_attempts", 3)
        self.retry_backoff_base = params.get("retry_backoff_base", 2)
        self.fail_on_partial = params.get("fail_on_partial", True)
        self.max_file_size_bytes = params.get("max_file_size_bytes", 1073741824)
        self.validate_certs = params.get("validate_certs", True)
        self.timeout = params.get("timeout", 300)

        self.results: List[Dict] = []
        self.upload_start_time = None  # Track upload start for time estimates

        # Build upload URL
        # Red Hat API endpoint: https://api.access.redhat.com/support/v1/cases/<case_number>/attachments/
        # Note: Trailing slash is optional but included for consistency with Red Hat documentation
        self.upload_url = f"{API_BASE}/cases/{self.case_id}/attachments/"

        # Setup HTTP opener with proxy and authentication
        self._setup_opener()

    def _setup_opener(self):
        """Setup HTTP opener with proxy and authentication handlers."""
        handlers: List[BaseHandler] = []

        # Proxy configuration
        # Set environment variables for proxy (urllib needs these for HTTPS through proxy)
        import os

        if self.proxy_http:
            os.environ['http_proxy'] = self.proxy_http
            os.environ['HTTP_PROXY'] = self.proxy_http
        if self.proxy_https:
            os.environ['https_proxy'] = self.proxy_https
            os.environ['HTTPS_PROXY'] = self.proxy_https
        if self.proxy_no:
            os.environ['no_proxy'] = self.proxy_no
            os.environ['NO_PROXY'] = self.proxy_no

        # Build proxy handler
        proxy_dict = {}
        if self.proxy_http:
            proxy_dict["http"] = self.proxy_http
        if self.proxy_https:
            proxy_dict["https"] = self.proxy_https
        if proxy_dict:
            handlers.append(ProxyHandler(proxy_dict))

        # Authentication
        if self.api_token:
            # Token-based authentication (Bearer token in header)
            # Will be handled in _build_request
            pass
        elif self.api_user and self.api_pass:
            # Basic authentication
            password_mgr = HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(
                None, self.upload_url, self.api_user, self.api_pass
            )
            handlers.append(HTTPBasicAuthHandler(password_mgr))

        # Build opener
        if handlers:
            opener = build_opener(*handlers)
            install_opener(opener)

    def _build_request(self, file_path: str, description: str) -> Tuple[Request, bytes]:
        """Build multipart/form-data request for file upload.

        Red Hat API requires multipart/form-data with:
        - field "file": the file content
        - field "description": upload description text

        Example curl equivalent:
        curl -u <username> -F "file=@<path>" -F "description=<desc>" -X POST <url>
        """
        # Read file content
        with open(file_path, "rb") as f:
            file_content = f.read()

        # Get filename
        filename = os.path.basename(file_path)

        # Build multipart/form-data body
        boundary = "----WebKitFormBoundary" + str(int(time.time() * 1000))
        body_parts = []

        # Add description field
        body_parts.append(f"--{boundary}\r\n".encode())
        body_parts.append(
            'Content-Disposition: form-data; name="description"\r\n\r\n'.encode()
        )
        body_parts.append(description.encode("utf-8"))
        body_parts.append("\r\n".encode())

        # Add file field
        body_parts.append(f"--{boundary}\r\n".encode())
        body_parts.append(
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
        )
        body_parts.append("Content-Type: application/octet-stream\r\n\r\n".encode())
        body_parts.append(file_content)
        body_parts.append(f"\r\n--{boundary}--\r\n".encode())

        body = b"".join(body_parts)

        # Build request
        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
            "User-Agent": "python-requests/2.28.0",  # Mimic standard HTTP client
            "Content-Length": str(len(body)),
            "Connection": "close",  # Avoid connection reuse issues
        }

        # Add Bearer token if provided
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        request = Request(self.upload_url, data=body, headers=headers)

        return request, body

    def _execute_upload_request(
        self, request: Request, timeout: int
    ) -> Tuple[Optional[int], Optional[str], Optional[Exception]]:
        """Execute HTTP request and return (http_code, response_body, error)."""
        import urllib.request

        try:
            # Create SSL context with proxy-friendly settings
            ssl_context = ssl.create_default_context()
            if not self.validate_certs:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            else:
                # Enable TLS 1.2+ for proxy compatibility
                ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
                # Load default CA certificates for Red Hat API
                ssl_context.load_default_certs()

            # Proxy tunneling for HTTPS requires specific handling
            # Python's urllib will automatically use CONNECT method for HTTPS through HTTP proxy

            # Execute request
            response = urllib.request.urlopen(request, timeout=timeout, context=ssl_context)

            http_code = response.getcode()
            response_body = response.read().decode("utf-8", errors="ignore")

            return http_code, response_body, None

        except HTTPError as e:
            http_code = e.code
            try:
                response_body = e.read().decode("utf-8", errors="ignore")
            except Exception:
                response_body = str(e)
            return http_code, response_body, None

        except URLError as e:
            return None, None, e

        except Exception as e:
            return None, None, e

    def _is_retryable_error(self, http_code: Optional[int]) -> bool:
        """Determine if HTTP error is retryable (5xx, 429)."""
        if http_code is None:
            return True  # Connection errors are retryable

        # Retry on 5xx server errors or 429 rate limit
        if http_code >= 500 or http_code == HTTP_RATE_LIMIT:
            return True

        return False

    def validate_parameters(self) -> bool:
        """Validate all input parameters."""
        errors = []

        # Validate case_id
        if (
            not self.case_id
            or not isinstance(self.case_id, str)
            or len(self.case_id.strip()) == 0
        ):
            errors.append("case_id is required and must be a non-empty string")

        # Validate archive_pattern
        if (
            not self.archive_pattern
            or not isinstance(self.archive_pattern, str)
            or len(self.archive_pattern.strip()) == 0
        ):
            errors.append("archive_pattern is required and must be a non-empty string")

        # Validate upload_description
        if (
            not self.upload_description
            or not isinstance(self.upload_description, str)
            or len(self.upload_description.strip()) == 0
        ):
            errors.append(
                "upload_description is required and must be a non-empty string"
            )

        # Validate authentication
        if not self.api_token:
            if not self.api_user or not self.api_pass:
                errors.append(
                    "Authentication required: provide api_token or both api_user and api_pass"
                )

        # Validate retry configuration
        if self.max_retry_attempts < 1:
            errors.append("max_retry_attempts must be >= 1")

        if self.retry_backoff_base < 1:
            errors.append("retry_backoff_base must be >= 1")

        # Validate file size limit
        if self.max_file_size_bytes < 1:
            errors.append("max_file_size_bytes must be >= 1")

        if errors:
            self.module.fail_json(
                msg="Parameter validation failed: " + "; ".join(errors)
            )
            return False

        return True

    def discover_files(self) -> List[str]:
        """Expand archive_pattern and build file list."""
        files = []

        # Check if pattern is a single file
        if os.path.isfile(self.archive_pattern):
            files.append(self.archive_pattern)
        else:
            # Expand glob pattern
            matched_files = glob.glob(self.archive_pattern)
            files.extend(matched_files)

        # Sort for consistent ordering
        files.sort()

        return files

    def validate_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate single file (existence, readability, size)."""
        # Check existence
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"

        if not os.path.isfile(file_path):
            return False, f"Path is not a file: {file_path}"

        # Check readability
        if not os.access(file_path, os.R_OK):
            return False, f"File not readable: {file_path}"

        # Check size
        try:
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, f"File is empty: {file_path}"

            if file_size > self.max_file_size_bytes:
                return (
                    False,
                    f"File exceeds size limit ({file_size} bytes > {self.max_file_size_bytes} bytes): {file_path}",
                )

        except OSError as e:
            return False, f"Error getting file size: {str(e)}"

        return True, None

    def upload_file_with_retry(  # noqa: C901
        self, file_path: str, part_number: int, total_parts: int
    ) -> Dict:
        """Upload single file with retry logic and exponential backoff."""
        description = f"{self.upload_description} - Part {part_number}/{total_parts}"
        filename = os.path.basename(file_path)

        self.module.log(f"Uploading part {part_number}/{total_parts}: {filename}")

        attempt = 1
        backoff = self.retry_backoff_base

        while attempt <= self.max_retry_attempts:
            if attempt > 1:
                self.module.log(
                    f"Retry attempt {attempt}/{self.max_retry_attempts} for part {part_number} after {backoff}s delay"
                )
                time.sleep(backoff)
                backoff = backoff * 2

            # Build request
            try:
                request, _ = self._build_request(file_path, description)
            except Exception as e:
                if attempt < self.max_retry_attempts:
                    self.module.warn(
                        f"Failed to build request for part {part_number} (attempt {attempt}): {str(e)}"
                    )
                    attempt += 1
                    continue
                else:
                    return {
                        "part": part_number,
                        "file": filename,
                        "status": "failed",
                        "reason": "unexpected_error",
                        "attempts": attempt,
                        "error": str(e),
                    }

            # Execute request
            http_code, response_body, error = self._execute_upload_request(
                request, self.timeout
            )

            # Handle connection errors
            if error is not None:
                self.module.warn(
                    f"Connection error for part {part_number} (attempt {attempt}): {str(error)}"
                )

                if attempt < self.max_retry_attempts:
                    attempt += 1
                    continue
                else:
                    return {
                        "part": part_number,
                        "file": filename,
                        "status": "failed",
                        "reason": "connection_error",
                        "attempts": attempt,
                        "error": str(error),
                    }

            # Check HTTP status code
            if (
                http_code is not None
                and HTTP_SUCCESS_MIN <= http_code <= HTTP_SUCCESS_MAX
            ):
                self.module.log(
                    f"Successfully uploaded part {part_number}/{total_parts} (HTTP {http_code})"
                )
                return {
                    "part": part_number,
                    "file": filename,
                    "status": "success",
                    "http_code": http_code,
                    "attempts": attempt,
                }

            # Check if error is retryable
            if self._is_retryable_error(http_code):
                self.module.warn(
                    f"Retryable error HTTP {http_code} for part {part_number} (attempt {attempt})"
                )

                if attempt < self.max_retry_attempts:
                    attempt += 1
                    continue
                else:
                    self.module.log(
                        f"Upload failed after {attempt} attempts for part {part_number}: HTTP {http_code}"
                    )
                    result = {
                        "part": part_number,
                        "file": filename,
                        "status": "failed",
                        "reason": "retryable_error_exhausted",
                        "http_code": http_code,
                        "attempts": attempt,
                    }
                    if response_body:
                        result["response"] = response_body
                    return result

            else:
                # Non-retryable error
                self.module.log(
                    f"Non-retryable error HTTP {http_code} for part {part_number}"
                )
                result = {
                    "part": part_number,
                    "file": filename,
                    "status": "failed",
                    "reason": "non_retryable_error",
                    "http_code": http_code,
                    "attempts": attempt,
                }
                if response_body:
                    result["response"] = response_body
                return result

        # Should not reach here
        self.module.warn(
            f"Unexpected state in upload retry loop for part {part_number}"
        )
        return {
            "part": part_number,
            "file": filename,
            "status": "failed",
            "reason": "unexpected_error",
            "attempts": attempt,
        }

    def execute_upload(self) -> Dict:
        """Main orchestration: discover, validate, upload all files."""
        # Discover files
        archive_files = self.discover_files()

        if not archive_files:
            self.module.fail_json(
                msg=f"No files found matching pattern: {self.archive_pattern}"
            )

        self.module.log(f"Found {len(archive_files)} archive part(s) to upload")

        # Validate all files before attempting upload
        validation_errors = []
        for file_path in archive_files:
            is_valid, error_msg = self.validate_file(file_path)
            if not is_valid:
                validation_errors.append(error_msg)

        if validation_errors:
            self.module.fail_json(
                msg="File validation failed: " + "; ".join(validation_errors)
            )

        # Upload each file
        total_parts = len(archive_files)
        part_number = 1
        success_count = 0
        failure_count = 0

        # Log total upload size for visibility
        total_size_mb = sum(os.path.getsize(f) for f in archive_files) / (1024 * 1024)
        self.module.log(
            f"Starting upload of {total_parts} parts, total size: {total_size_mb:.2f} MB"
        )

        # Start time tracking
        self.upload_start_time = time.time()

        for file_path in archive_files:
            # Progress logging for large uploads
            if total_parts > 10 and part_number % 10 == 0:
                elapsed = time.time() - self.upload_start_time
                avg_time_per_part = elapsed / (part_number - 1) if part_number > 1 else 0
                remaining_parts = total_parts - (part_number - 1)
                estimated_remaining_sec = avg_time_per_part * remaining_parts
                estimated_remaining_min = estimated_remaining_sec / 60

                self.module.log(
                    f"Upload progress: {part_number}/{total_parts} "
                    f"({success_count} success, {failure_count} failed) - "
                    f"Est. remaining: {estimated_remaining_min:.1f} min"
                )

            result = self.upload_file_with_retry(file_path, part_number, total_parts)
            self.results.append(result)

            if result.get("status") == "success":
                success_count += 1
                self.module.log(f"Part {part_number}/{total_parts}: ✓ Success")
            else:
                failure_count += 1
                self.module.warn(
                    f"Part {part_number}/{total_parts}: ✗ Failed - {result.get('reason', 'unknown')}"
                )

            part_number += 1

        # Determine final status
        if failure_count == 0:
            final_status = "success"
        elif success_count == 0:
            final_status = "failed"
        else:
            final_status = "partial"

        # Build result dictionary
        result = {
            "status": final_status,
            "case_id": self.case_id,
            "total_parts": total_parts,
            "success_count": success_count,
            "failure_count": failure_count,
            "results": self.results,
        }

        # Add descriptive message for failures
        if final_status != "success":
            failed_parts = [r for r in self.results if r.get("status") != "success"]
            failure_reasons = {}
            for part_result in failed_parts:
                reason = part_result.get("reason", "unknown")
                failure_reasons[reason] = failure_reasons.get(reason, 0) + 1

            reason_summary = ", ".join([f"{count} {reason}" for reason, count in failure_reasons.items()])
            result["summary"] = f"{failure_count}/{total_parts} parts failed ({reason_summary})"

        return result


def main():
    """Module entry point."""
    argument_spec = {
        "case_id": dict(type="str", required=True),
        "archive_pattern": dict(type="str", required=True),
        "upload_description": dict(type="str", required=True),
        "api_token": dict(type="str", required=False, default=None, no_log=True),
        "api_user": dict(type="str", required=False, default=None, no_log=True),
        "api_pass": dict(type="str", required=False, default=None, no_log=True),
        "proxy_http": dict(type="str", required=False, default=None),
        "proxy_https": dict(type="str", required=False, default=None),
        "proxy_no": dict(type="str", required=False, default=None),
        "max_retry_attempts": dict(type="int", required=False, default=3),
        "retry_backoff_base": dict(type="int", required=False, default=2),
        "fail_on_partial": dict(type="bool", required=False, default=True),
        "max_file_size_bytes": dict(type="int", required=False, default=1073741824),
        "validate_certs": dict(type="bool", required=False, default=True),
        "timeout": dict(type="int", required=False, default=300),
    }

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    try:
        controller = RedHatUploadController(module, module.params)

        # Validate parameters
        if not controller.validate_parameters():
            return

        # Execute upload
        result = controller.execute_upload()

        # Determine if module should fail
        should_fail = False
        if result["status"] == "failed":
            should_fail = True
        elif result["status"] == "partial" and controller.fail_on_partial:
            should_fail = True

        # Determine changed status
        changed = result["status"] in ["success", "partial"]

        if should_fail:
            failure_msg = f"Upload {result['status']}: {result['failure_count']}/{result['total_parts']} parts failed"
            module.fail_json(msg=failure_msg, **result)
        else:
            module.exit_json(changed=changed, **result)

    except Exception as e:
        module.fail_json(msg=f"Module failed: {str(e)}", failed=True)


if __name__ == "__main__":
    main()
