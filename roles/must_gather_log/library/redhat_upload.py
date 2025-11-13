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
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    import requests
    from requests.auth import HTTPBasicAuth

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

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
      - Recommended 1800s (30 min) for large files through proxies
    type: int
    required: false
    default: 1800
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
        self.timeout = params.get("timeout", 1800)

        self.results: List[Dict] = []
        self.upload_start_time = None  # Track upload start for time estimates
        self.log_dir = params.get("log_dir")

        # Setup file logging if log_dir provided
        self.logger = self._setup_logging()

        # Build upload URL
        # Red Hat API endpoint: https://api.access.redhat.com/support/v1/cases/<case_number>/attachments/
        # Note: Trailing slash is optional but included for consistency with Red Hat documentation
        self.upload_url = f"{API_BASE}/cases/{self.case_id}/attachments/"

    def _setup_logging(self) -> logging.Logger:
        """Setup file logging if log_dir is provided."""
        logger = logging.getLogger(f"redhat_upload_{self.case_id}")
        logger.setLevel(logging.DEBUG)

        # Clear any existing handlers
        logger.handlers = []

        if self.log_dir:
            # Create log directory if it doesn't exist
            try:
                os.makedirs(self.log_dir, exist_ok=True)

                # Create log file with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_file = os.path.join(
                    self.log_dir, f"redhat_upload_{self.case_id}_{timestamp}.log"
                )

                # File handler with detailed formatting
                fh = logging.FileHandler(log_file)
                fh.setLevel(logging.DEBUG)
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
                fh.setFormatter(formatter)
                logger.addHandler(fh)

                self.module.log(f"Upload logging enabled: {log_file}")
                logger.info(f"Upload session started for case {self.case_id}")
                logger.info(f"Archive pattern: {self.archive_pattern}")
                logger.info(f"Upload URL: {self.upload_url}")
                logger.info(
                    f"Proxy HTTP: {self.proxy_http if self.proxy_http else 'None'}"
                )
                logger.info(
                    f"Proxy HTTPS: {self.proxy_https if self.proxy_https else 'None'}"
                )
                logger.info(f"Max retries: {self.max_retry_attempts}")
                logger.info(f"Retry backoff: {self.retry_backoff_base}s")

            except Exception as e:
                self.module.warn(f"Failed to setup file logging: {str(e)}")

        return logger

    def _prepare_upload_config(self, file_path: str, description: str) -> Dict:
        """Prepare upload configuration for requests library.

        Red Hat API requires multipart/form-data with:
        - field "file": the file content
        - field "description": upload description text

        Returns dict with files, data, headers, auth, proxies for requests.post()
        """
        filename = os.path.basename(file_path)

        # Prepare multipart/form-data for requests
        # requests library handles the boundary and Content-Type automatically
        files = {"file": (filename, open(file_path, "rb"), "application/octet-stream")}

        data = {"description": description}

        # Build headers
        headers = {
            "Accept": "application/json",
            "User-Agent": "python-requests/2.31.0",
        }

        # Add Bearer token if provided
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        # Setup authentication
        auth = None
        if self.api_user and self.api_pass:
            auth = HTTPBasicAuth(self.api_user, self.api_pass)

        # Setup proxies
        proxies = {}
        if self.proxy_http:
            proxies["http"] = self.proxy_http
        if self.proxy_https:
            proxies["https"] = self.proxy_https

        if not proxies:
            proxies = None

        return {
            "files": files,
            "data": data,
            "headers": headers,
            "auth": auth,
            "proxies": proxies,
        }

    def _execute_upload_request(
        self, upload_config: Dict, timeout: int
    ) -> Tuple[Optional[int], Optional[str], Optional[Exception]]:
        """Execute HTTP upload using requests library.

        Args:
            upload_config: Dict with files, data, headers, auth, proxies
            timeout: Request timeout in seconds

        Returns:
            Tuple of (http_code, response_body, error)
        """
        try:
            response = requests.post(
                self.upload_url,
                files=upload_config["files"],
                data=upload_config["data"],
                headers=upload_config["headers"],
                auth=upload_config["auth"],
                proxies=upload_config["proxies"],
                timeout=timeout,
                verify=self.validate_certs,
            )

            http_code = response.status_code
            response_body = response.text

            # Close file handle
            upload_config["files"]["file"][1].close()

            return http_code, response_body, None

        except requests.exceptions.Timeout as e:
            # Close file handle on error
            try:
                upload_config["files"]["file"][1].close()
            except Exception:
                pass
            return None, None, e

        except requests.exceptions.ProxyError as e:
            try:
                upload_config["files"]["file"][1].close()
            except Exception:
                pass
            return None, None, e

        except requests.exceptions.SSLError as e:
            try:
                upload_config["files"]["file"][1].close()
            except Exception:
                pass
            return None, None, e

        except requests.exceptions.ConnectionError as e:
            try:
                upload_config["files"]["file"][1].close()
            except Exception:
                pass
            return None, None, e

        except requests.exceptions.HTTPError as e:
            http_code = e.response.status_code if e.response else None
            response_body = e.response.text if e.response else str(e)
            try:
                upload_config["files"]["file"][1].close()
            except Exception:
                pass
            return http_code, response_body, None

        except Exception as e:
            try:
                upload_config["files"]["file"][1].close()
            except Exception:
                pass
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
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)

        self.module.log(f"Uploading part {part_number}/{total_parts}: {filename}")
        self.logger.info(
            f"Starting upload - Part {part_number}/{total_parts}: {filename} ({file_size_mb:.2f} MB)"
        )

        attempt = 1
        backoff = self.retry_backoff_base

        while attempt <= self.max_retry_attempts:
            if attempt > 1:
                self.module.log(
                    f"Retry attempt {attempt}/{self.max_retry_attempts} for part {part_number} after {backoff}s delay"
                )
                self.logger.warning(
                    f"Retry attempt {attempt}/{self.max_retry_attempts} for part {part_number} after {backoff}s delay"
                )
                time.sleep(backoff)
                backoff = backoff * 2

            # Prepare upload configuration
            try:
                self.logger.debug(
                    f"Preparing upload config for part {part_number}, attempt {attempt}"
                )
                upload_config = self._prepare_upload_config(file_path, description)
                self.logger.debug(
                    f"Upload config prepared successfully for part {part_number}"
                )
            except Exception as e:
                self.logger.error(
                    f"Failed to prepare upload config for part {part_number} (attempt {attempt}): {str(e)}"
                )
                if attempt < self.max_retry_attempts:
                    self.module.warn(
                        f"Failed to prepare upload config for part {part_number} (attempt {attempt}): {str(e)}"
                    )
                    attempt += 1
                    continue
                else:
                    self.logger.error(
                        f"Exhausted retries preparing upload config for part {part_number}"
                    )
                    return {
                        "part": part_number,
                        "file": filename,
                        "status": "failed",
                        "reason": "unexpected_error",
                        "attempts": attempt,
                        "error": str(e),
                    }

            # Execute upload request
            self.logger.debug(
                f"Executing upload request for part {part_number}, attempt {attempt}"
            )
            http_code, response_body, error = self._execute_upload_request(
                upload_config, self.timeout
            )
            self.logger.debug(
                f"Upload request completed - HTTP {http_code}, error: {error}"
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
                self.logger.info(
                    f"✓ Upload SUCCESS - Part {part_number}/{total_parts} (HTTP {http_code}, attempt {attempt})"
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
                self.logger.warning(
                    f"Retryable error HTTP {http_code} for part {part_number} (attempt {attempt}) - Response: {response_body[:200] if response_body else 'N/A'}"
                )

                if attempt < self.max_retry_attempts:
                    attempt += 1
                    continue
                else:
                    self.module.log(
                        f"Upload failed after {attempt} attempts for part {part_number}: HTTP {http_code}"
                    )
                    self.logger.error(
                        f"✗ Upload FAILED - Part {part_number} exhausted retries (HTTP {http_code}, {attempt} attempts)"
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
                self.logger.error(
                    f"✗ Upload FAILED - Part {part_number} non-retryable error (HTTP {http_code}, attempt {attempt}) - Response: {response_body[:200] if response_body else 'N/A'}"
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
                avg_time_per_part = (
                    elapsed / (part_number - 1) if part_number > 1 else 0
                )
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

            reason_summary = ", ".join(
                [f"{count} {reason}" for reason, count in failure_reasons.items()]
            )
            result["summary"] = (
                f"{failure_count}/{total_parts} parts failed ({reason_summary})"
            )

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
        "timeout": dict(type="int", required=False, default=1800),
        "log_dir": dict(type="str", required=False, default=None),
    }

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    # Check for requests library
    if not HAS_REQUESTS:
        module.fail_json(
            msg="The 'requests' library is required for this module. "
            "Install it using: pip install requests"
        )

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
