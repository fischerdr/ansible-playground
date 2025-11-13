#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# test_upload.py
# Minimal test module to debug Red Hat API uploads with comprehensive logging
#
# Tests both urllib (standard library) and requests library implementations

from __future__ import annotations

import json
import logging
import os
import ssl
import time
from datetime import datetime
from typing import Dict, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import (HTTPBasicAuthHandler,
                            HTTPPasswordMgrWithDefaultRealm, Request,
                            build_opener, install_opener)

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r"""
---
module: test_upload
short_description: Test Red Hat API upload with comprehensive logging
description:
  - Minimal test module to debug Red Hat API uploads
  - Tests both urllib (standard library) and requests library
  - Comprehensive logging for debugging connection issues
options:
  case_id:
    description: Red Hat support case number
    type: str
    required: true
  test_file:
    description: Path to test file to upload
    type: str
    required: true
  upload_description:
    description: Upload description text
    type: str
    required: true
  api_token:
    description: Red Hat API authentication token
    type: str
    required: false
    no_log: true
  api_user:
    description: Red Hat API username
    type: str
    required: false
    no_log: true
  api_pass:
    description: Red Hat API password
    type: str
    required: false
    no_log: true
  proxy_http:
    description: HTTP proxy URL
    type: str
    required: false
  proxy_https:
    description: HTTPS proxy URL
    type: str
    required: false
  proxy_no:
    description: Comma-separated list of hosts to bypass proxy
    type: str
    required: false
  validate_certs:
    description: Validate SSL certificates
    type: bool
    required: false
    default: true
  timeout:
    description: Request timeout in seconds
    type: int
    required: false
    default: 300
  log_dir:
    description: Directory for detailed logs
    type: str
    required: false
  use_requests:
    description: Use requests library instead of urllib
    type: bool
    required: false
    default: false
"""

EXAMPLES = r"""
- name: Test upload with urllib (default)
  test_upload:
    case_id: "04300286"
    test_file: "/tmp/test.tar.gz"
    upload_description: "Test upload"
    api_token: "{{ vault_rh_api_token }}"
    log_dir: "/tmp/upload_debug"

- name: Test upload with requests library
  test_upload:
    case_id: "04300286"
    test_file: "/tmp/test.tar.gz"
    upload_description: "Test upload"
    api_token: "{{ vault_rh_api_token }}"
    use_requests: true
    log_dir: "/tmp/upload_debug"
"""

RETURN = r"""
status:
  description: Upload status
  type: str
  returned: always
method:
  description: Upload method used (urllib or requests)
  type: str
  returned: always
http_code:
  description: HTTP status code
  type: int
  returned: when available
response_body:
  description: Response body from API
  type: str
  returned: when available
"""

API_BASE = "https://api.access.redhat.com/support/v1"


class TestUploadController:
    """Controller for test uploads with comprehensive logging."""

    def __init__(self, module: AnsibleModule, params: Dict):
        """Initialize controller."""
        self.module = module
        self.case_id = params.get("case_id")
        self.test_file = params.get("test_file")
        self.upload_description = params.get("upload_description")
        self.api_token = params.get("api_token")
        self.api_user = params.get("api_user")
        self.api_pass = params.get("api_pass")
        self.proxy_http = params.get("proxy_http")
        self.proxy_https = params.get("proxy_https")
        self.proxy_no = params.get("proxy_no")
        self.validate_certs = params.get("validate_certs", True)
        self.timeout = params.get("timeout", 300)
        self.log_dir = params.get("log_dir")
        self.use_requests = params.get("use_requests", False)

        self.upload_url = f"{API_BASE}/cases/{self.case_id}/attachments/"
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive file logging."""
        logger = logging.getLogger(f"test_upload_{self.case_id}")
        logger.setLevel(logging.DEBUG)
        logger.handlers = []

        if self.log_dir:
            try:
                os.makedirs(self.log_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                method = "requests" if self.use_requests else "urllib"
                log_file = os.path.join(
                    self.log_dir, f"test_upload_{method}_{self.case_id}_{timestamp}.log"
                )

                fh = logging.FileHandler(log_file)
                fh.setLevel(logging.DEBUG)
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
                fh.setFormatter(formatter)
                logger.addHandler(fh)

                self.module.log(f"Test upload logging: {log_file}")
                logger.info("=" * 80)
                logger.info(f"TEST UPLOAD SESSION START - Method: {method}")
                logger.info("=" * 80)
                logger.info(f"Case ID: {self.case_id}")
                logger.info(f"Test file: {self.test_file}")
                logger.info(f"Upload URL: {self.upload_url}")
                logger.info(f"Upload method: {method}")
                logger.info(f"Proxy HTTP: {self.proxy_http or 'None'}")
                logger.info(f"Proxy HTTPS: {self.proxy_https or 'None'}")
                logger.info(f"Proxy NO: {self.proxy_no or 'None'}")
                logger.info(f"Validate certs: {self.validate_certs}")
                logger.info(f"Timeout: {self.timeout}s")
                logger.info(f"Auth method: {'Token' if self.api_token else 'Basic'}")
                logger.info("=" * 80)

            except Exception as e:
                self.module.warn(f"Failed to setup logging: {str(e)}")

        return logger

    def _test_upload_urllib(
        self,
    ) -> Tuple[str, Optional[int], Optional[str], Optional[str]]:
        """Test upload using urllib (standard library)."""
        self.logger.info(">>> STARTING URLLIB UPLOAD TEST <<<")

        # Set proxy environment variables
        if self.proxy_http:
            os.environ["http_proxy"] = self.proxy_http
            os.environ["HTTP_PROXY"] = self.proxy_http
            self.logger.debug(f"Set HTTP_PROXY env: {self.proxy_http}")

        if self.proxy_https:
            os.environ["https_proxy"] = self.proxy_https
            os.environ["HTTPS_PROXY"] = self.proxy_https
            self.logger.debug(f"Set HTTPS_PROXY env: {self.proxy_https}")

        if self.proxy_no:
            os.environ["no_proxy"] = self.proxy_no
            os.environ["NO_PROXY"] = self.proxy_no
            self.logger.debug(f"Set NO_PROXY env: {self.proxy_no}")

        # Setup authentication
        handlers = []
        if self.api_user and self.api_pass:
            self.logger.debug("Configuring Basic authentication handler")
            password_mgr = HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(
                None, self.upload_url, self.api_user, self.api_pass
            )
            handlers.append(HTTPBasicAuthHandler(password_mgr))

        # Build opener
        if handlers:
            opener = build_opener(*handlers)
            install_opener(opener)
            self.logger.debug("Installed custom opener with auth handler")
        else:
            install_opener(build_opener())
            self.logger.debug("Installed default opener")

        # Read file
        self.logger.debug(f"Reading test file: {self.test_file}")
        with open(self.test_file, "rb") as f:
            file_content = f.read()
        file_size = len(file_content)
        self.logger.info(
            f"File size: {file_size} bytes ({file_size / (1024 * 1024):.2f} MB)"
        )

        # Build multipart/form-data
        filename = os.path.basename(self.test_file)
        boundary = "----WebKitFormBoundary" + str(int(time.time() * 1000))

        self.logger.debug(f"Building multipart/form-data with boundary: {boundary}")

        body_parts = []
        body_parts.append(f"--{boundary}\r\n".encode())
        body_parts.append(
            'Content-Disposition: form-data; name="description"\r\n\r\n'.encode()
        )
        body_parts.append(self.upload_description.encode("utf-8"))
        body_parts.append("\r\n".encode())
        body_parts.append(f"--{boundary}\r\n".encode())
        body_parts.append(
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
        )
        body_parts.append("Content-Type: application/octet-stream\r\n\r\n".encode())
        body_parts.append(file_content)
        body_parts.append(f"\r\n--{boundary}--\r\n".encode())

        body = b"".join(body_parts)
        body_size = len(body)
        self.logger.info(
            f"Request body size: {body_size} bytes ({body_size / (1024 * 1024):.2f} MB)"
        )

        # Build request headers
        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
            "User-Agent": "python-urllib/3.11-test",
            "Content-Length": str(body_size),
            "Connection": "close",
        }

        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
            self.logger.debug("Added Bearer token authorization header")

        self.logger.debug("Request headers:")
        for key, value in headers.items():
            if key.lower() == "authorization":
                self.logger.debug(f"  {key}: Bearer ***TOKEN_REDACTED***")
            else:
                self.logger.debug(f"  {key}: {value}")

        request = Request(self.upload_url, data=body, headers=headers)

        # Create SSL context
        ssl_context = ssl.create_default_context()
        if not self.validate_certs:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            self.logger.warning("SSL certificate validation DISABLED")
        else:
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            ssl_context.load_default_certs()
            self.logger.debug("SSL certificate validation ENABLED (TLS 1.2+)")

        # Execute request
        self.logger.info(f"Executing HTTP POST to {self.upload_url}")
        self.logger.info(f"Timeout: {self.timeout}s")

        start_time = time.time()

        try:
            import urllib.request

            self.logger.debug("Calling urllib.request.urlopen()...")
            response = urllib.request.urlopen(
                request, timeout=self.timeout, context=ssl_context
            )

            elapsed = time.time() - start_time
            http_code = response.getcode()
            response_body = response.read().decode("utf-8", errors="ignore")

            self.logger.info(f"✓ HTTP Response: {http_code} (elapsed: {elapsed:.2f}s)")
            self.logger.debug(f"Response headers: {dict(response.headers)}")
            self.logger.debug(f"Response body: {response_body[:500]}")

            return "success", http_code, response_body, None

        except HTTPError as e:
            elapsed = time.time() - start_time
            http_code = e.code
            try:
                response_body = e.read().decode("utf-8", errors="ignore")
            except Exception:
                response_body = str(e)

            self.logger.error(f"✗ HTTP Error: {http_code} (elapsed: {elapsed:.2f}s)")
            self.logger.error(f"Error response body: {response_body[:1000]}")

            return "http_error", http_code, response_body, f"HTTP {http_code}"

        except URLError as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            self.logger.error(f"✗ URL Error (elapsed: {elapsed:.2f}s): {error_msg}")
            return "url_error", None, None, error_msg

        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            self.logger.error(
                f"✗ Unexpected Error (elapsed: {elapsed:.2f}s): {error_msg}"
            )
            self.logger.exception("Exception details:")
            return "unexpected_error", None, None, error_msg

    def _test_upload_requests(
        self,
    ) -> Tuple[str, Optional[int], Optional[str], Optional[str]]:
        """Test upload using requests library."""
        try:
            import requests
        except ImportError:
            self.logger.error("requests library not available")
            return "library_error", None, None, "requests library not installed"

        self.logger.info(">>> STARTING REQUESTS LIBRARY UPLOAD TEST <<<")

        # Setup proxies
        proxies = {}
        if self.proxy_http:
            proxies["http"] = self.proxy_http
            self.logger.debug(f"Using HTTP proxy: {self.proxy_http}")
        if self.proxy_https:
            proxies["https"] = self.proxy_https
            self.logger.debug(f"Using HTTPS proxy: {self.proxy_https}")

        if not proxies:
            proxies = None

        # Read file
        self.logger.debug(f"Reading test file: {self.test_file}")
        file_size = os.path.getsize(self.test_file)
        self.logger.info(
            f"File size: {file_size} bytes ({file_size / (1024 * 1024):.2f} MB)"
        )

        # Prepare multipart/form-data
        filename = os.path.basename(self.test_file)
        files = {
            "file": (filename, open(self.test_file, "rb"), "application/octet-stream")
        }
        data = {"description": self.upload_description}

        # Setup headers
        headers = {
            "Accept": "application/json",
            "User-Agent": "python-requests/2.31-test",
        }

        # Setup authentication
        auth = None
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
            self.logger.debug("Using Bearer token authentication")
        elif self.api_user and self.api_pass:
            auth = (self.api_user, self.api_pass)
            self.logger.debug("Using Basic authentication")

        self.logger.debug("Request headers:")
        for key, value in headers.items():
            if key.lower() == "authorization":
                self.logger.debug(f"  {key}: Bearer ***TOKEN_REDACTED***")
            else:
                self.logger.debug(f"  {key}: {value}")

        self.logger.info(f"Executing HTTP POST to {self.upload_url}")
        self.logger.info(f"Timeout: {self.timeout}s")
        self.logger.debug(f"Proxies: {proxies}")
        self.logger.debug(f"Verify SSL: {self.validate_certs}")

        start_time = time.time()

        try:
            self.logger.debug("Calling requests.post()...")
            response = requests.post(
                self.upload_url,
                files=files,
                data=data,
                headers=headers,
                auth=auth,
                proxies=proxies,
                timeout=self.timeout,
                verify=self.validate_certs,
            )

            elapsed = time.time() - start_time
            http_code = response.status_code
            response_body = response.text

            self.logger.info(f"✓ HTTP Response: {http_code} (elapsed: {elapsed:.2f}s)")
            self.logger.debug(f"Response headers: {dict(response.headers)}")
            self.logger.debug(f"Response body: {response_body[:500]}")

            # Close file
            files["file"][1].close()

            if 200 <= http_code <= 299:
                return "success", http_code, response_body, None
            else:
                return "http_error", http_code, response_body, f"HTTP {http_code}"

        except requests.exceptions.Timeout as e:
            elapsed = time.time() - start_time
            error_msg = f"Request timeout after {elapsed:.2f}s"
            self.logger.error(f"✗ Timeout Error: {error_msg}")
            files["file"][1].close()
            return "timeout_error", None, None, error_msg

        except requests.exceptions.ProxyError as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            self.logger.error(f"✗ Proxy Error (elapsed: {elapsed:.2f}s): {error_msg}")
            files["file"][1].close()
            return "proxy_error", None, None, error_msg

        except requests.exceptions.SSLError as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            self.logger.error(f"✗ SSL Error (elapsed: {elapsed:.2f}s): {error_msg}")
            files["file"][1].close()
            return "ssl_error", None, None, error_msg

        except requests.exceptions.ConnectionError as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            self.logger.error(
                f"✗ Connection Error (elapsed: {elapsed:.2f}s): {error_msg}"
            )
            files["file"][1].close()
            return "connection_error", None, None, error_msg

        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            self.logger.error(
                f"✗ Unexpected Error (elapsed: {elapsed:.2f}s): {error_msg}"
            )
            self.logger.exception("Exception details:")
            files["file"][1].close()
            return "unexpected_error", None, None, error_msg

    def execute_test(self) -> Dict:
        """Execute test upload."""
        # Validate file
        if not os.path.isfile(self.test_file):
            self.module.fail_json(msg=f"Test file not found: {self.test_file}")

        if not os.access(self.test_file, os.R_OK):
            self.module.fail_json(msg=f"Test file not readable: {self.test_file}")

        # Execute upload
        if self.use_requests:
            status, http_code, response_body, error = self._test_upload_requests()
            method = "requests"
        else:
            status, http_code, response_body, error = self._test_upload_urllib()
            method = "urllib"

        self.logger.info("=" * 80)
        self.logger.info(f"TEST UPLOAD COMPLETE - Status: {status}")
        self.logger.info("=" * 80)

        result = {
            "status": status,
            "method": method,
        }

        if http_code is not None:
            result["http_code"] = http_code

        if response_body:
            result["response_body"] = response_body

        if error:
            result["error"] = error

        return result


def main():
    """Module entry point."""
    argument_spec = {
        "case_id": dict(type="str", required=True),
        "test_file": dict(type="str", required=True),
        "upload_description": dict(type="str", required=True),
        "api_token": dict(type="str", required=False, default=None, no_log=True),
        "api_user": dict(type="str", required=False, default=None, no_log=True),
        "api_pass": dict(type="str", required=False, default=None, no_log=True),
        "proxy_http": dict(type="str", required=False, default=None),
        "proxy_https": dict(type="str", required=False, default=None),
        "proxy_no": dict(type="str", required=False, default=None),
        "validate_certs": dict(type="bool", required=False, default=True),
        "timeout": dict(type="int", required=False, default=300),
        "log_dir": dict(type="str", required=False, default=None),
        "use_requests": dict(type="bool", required=False, default=False),
    }

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    try:
        controller = TestUploadController(module, module.params)
        result = controller.execute_test()

        # Determine success
        if result["status"] == "success":
            module.exit_json(changed=True, **result)
        else:
            module.fail_json(
                msg=f"Upload test failed: {result.get('error', 'Unknown error')}",
                **result,
            )

    except Exception as e:
        module.fail_json(msg=f"Module failed: {str(e)}", failed=True)


if __name__ == "__main__":
    main()
