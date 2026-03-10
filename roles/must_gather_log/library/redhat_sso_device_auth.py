#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Enterprise Automation Team
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: redhat_sso_device_auth
short_description: Automate Red Hat SSO device authorization approval
description:
  - Automates the approval of Red Hat SSO device authorization via HTTP
  - Handles multi-step authentication flow without requiring browser
  - Manages session cookies and HTML form extraction automatically
  - Designed for Red Hat Customer Portal device authorization workflow
version_added: "1.0.0"
author:
  - Enterprise Automation Team
options:
  verification_uri:
    description:
      - Device verification URI from Red Hat SSO
      - Complete URI including user code parameter
    type: str
    required: true
  username:
    description: Red Hat Customer Portal username
    type: str
    required: true
  password:
    description: Red Hat Customer Portal password
    type: str
    required: true
    no_log: true
  proxy:
    description:
      - HTTP/HTTPS proxy URL
      - Applied to both HTTP and HTTPS connections
    type: str
    required: false
requirements:
  - python >= 3.11
  - requests >= 2.28.0
  - urllib3 >= 1.26.0
notes:
  - Red Hat account MUST NOT have 2FA/MFA enabled
  - SSL certificate verification is disabled for corporate proxies
  - Requires network access to Red Hat SSO endpoints
  - Session cookies are managed automatically
seealso:
  - name: Red Hat SSO Device Authorization
    link: https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/auth/device
"""

EXAMPLES = r"""
- name: Approve device authorization with direct connection
  redhat_sso_device_auth:
    verification_uri: "{{ device_auth_response.verification_uri_complete }}"
    username: "user@example.com"
    password: "password123"
  register: approval_result

- name: Approve device authorization via corporate proxy
  redhat_sso_device_auth:
    verification_uri: "{{ verification_uri }}"
    username: "{{ redhat_username }}"
    password: "{{ redhat_password }}"
    proxy: "http://proxy-appgw.aexp.com:9090"
  register: approval_result
  no_log: true

- name: Verify approval succeeded
  ansible.builtin.assert:
    that:
      - approval_result.success | bool
    fail_msg: "Device authorization failed: {{ approval_result.msg }}"

- name: Use approval result in subsequent tasks
  ansible.builtin.debug:
    msg: "Device approved via {{ approval_result.details.steps_completed }} steps"
  when: approval_result.success
"""

RETURN = r"""
changed:
  description: Whether the module made changes (always true on success)
  type: bool
  returned: always
  sample: true
success:
  description: Whether device authorization approval succeeded
  type: bool
  returned: always
  sample: true
msg:
  description: Human-readable message describing the result
  type: str
  returned: always
  sample: "Device authorization approved successfully"
details:
  description: Detailed execution information
  type: dict
  returned: always
  sample:
    step1_success: true
    step2_success: true
    step3_success: true
    steps_completed: 3
    final_url: "https://sso.redhat.com/auth/.../success"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    import re
    from typing import Dict, Optional, Tuple
    from urllib.parse import urljoin

    import requests
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class RedHatDeviceApprover:
    """Handles Red Hat SSO device authorization approval via HTTP"""

    def __init__(
        self,
        verification_uri: str,
        username: str,
        password: str,
        proxy: Optional[str] = None,
    ):
        self.verification_uri = verification_uri
        self.username = username
        self.password = password
        self.proxy = proxy
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        )

        # Disable SSL certificate verification for corporate proxies
        self.session.verify = False

        # Configure proxy if provided
        if self.proxy:
            self.session.proxies = {
                "http": self.proxy,
                "https": self.proxy,
            }

        # Store results for details
        self.details = {
            "step1_success": False,
            "step2_success": False,
            "step3_success": False,
            "steps_completed": 0,
            "final_url": "",
        }

    def extract_form_data(
        self, html: str, form_action_pattern: str
    ) -> Tuple[Optional[str], Dict[str, str]]:
        """
        Extract form action URL and hidden fields from HTML

        Returns:
            (action_url, form_data_dict)
        """
        # Find form action
        action_match = re.search(
            rf'<form[^>]+action="([^"]+)"[^>]*{form_action_pattern}',
            html,
            re.IGNORECASE,
        )
        if not action_match:
            action_match = re.search(r'<form[^>]+action="([^"]+)"', html)

        action_url = action_match.group(1) if action_match else None

        # Extract hidden fields
        form_data = {}
        hidden_fields = re.findall(
            r'<input[^>]+type=["\']hidden["\'][^>]*>', html, re.IGNORECASE
        )
        for field in hidden_fields:
            name_match = re.search(r'name=["\']([^"\']+)["\']', field)
            value_match = re.search(r'value=["\']([^"\']*)["\']', field)
            if name_match:
                name = name_match.group(1)
                value = value_match.group(1) if value_match else ""
                form_data[name] = value

        return action_url, form_data

    def step1_visit_verification_url(self) -> bool:
        """Visit verification URL and follow redirects"""
        try:
            response = self.session.get(
                self.verification_uri, allow_redirects=True, timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Step 1 failed - Request error: {e}")

        self.current_url = response.url
        self.current_html = response.text

        # Check if we're at login page
        if "login" in response.url.lower() or "login" in response.text.lower():
            self.details["step1_success"] = True
            self.details["steps_completed"] = 1
            return True
        else:
            raise Exception(
                f"Step 1 failed - Unexpected page, not a login page: {response.url}"
            )

    def step2_submit_login(self) -> bool:
        """Submit login credentials"""
        # Extract login form data
        action_url, form_data = self.extract_form_data(self.current_html, "")

        if not action_url:
            raise Exception("Step 2 failed - Could not find login form action URL")

        # Make action URL absolute
        if not action_url.startswith("http"):
            action_url = urljoin(self.current_url, action_url)

        # Add credentials to form data
        form_data.update({"username": self.username, "password": self.password})

        try:
            response = self.session.post(
                action_url, data=form_data, allow_redirects=True, timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Step 2 failed - Request error: {e}")

        self.current_url = response.url
        self.current_html = response.text

        # Check for login errors
        error_patterns = [
            r"invalid.*credentials",
            r"incorrect.*username.*password",
            r"authentication.*failed",
            r"login.*failed",
            r"account.*locked",
            r"invalid.*password",
        ]
        for pattern in error_patterns:
            if re.search(pattern, response.text, re.IGNORECASE):
                raise Exception(f"Step 2 failed - Login error detected: {pattern}")

        # Check for 2FA/MFA requirement
        mfa_patterns = [
            r"two.factor",
            r"2fa",
            r"multi.factor",
            r"verification.*code",
            r"authenticator",
        ]
        for pattern in mfa_patterns:
            if re.search(pattern, response.text, re.IGNORECASE):
                raise Exception(
                    "Step 2 failed - 2FA/MFA detected. Account must not have two-factor authentication enabled"
                )

        # Check if we reached approval page
        url_has_oauth_grant = "OAUTH_GRANT" in response.url
        approval_indicators = [
            r"grant.*access",
            r"approve",
            r"authorize",
            r"allow.*access",
        ]
        found_approval = any(
            re.search(pattern, response.text, re.IGNORECASE)
            for pattern in approval_indicators
        )

        if url_has_oauth_grant or found_approval:
            self.details["step2_success"] = True
            self.details["steps_completed"] = 2
            return True
        else:
            raise Exception(
                f"Step 2 failed - Did not reach approval page: {response.url}"
            )

    def step3_approve_device(self) -> bool:
        """Submit approval for device authorization"""
        # Extract approval form data
        action_url, form_data = self.extract_form_data(self.current_html, "")

        if not action_url:
            raise Exception("Step 3 failed - Could not find approval form action URL")

        # Make action URL absolute
        if not action_url.startswith("http"):
            action_url = urljoin(self.current_url, action_url)

        # Add approval to form data
        approval_fields = {
            "approve": "true",
            "grant": "true",
            "authorize": "true",
            "consent": "true",
            "accept": "yes",
        }
        form_data.update(approval_fields)

        try:
            response = self.session.post(
                action_url, data=form_data, allow_redirects=True, timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Step 3 failed - Request error: {e}")

        self.details["final_url"] = response.url

        # Check for success indicators
        success_patterns = [
            r"success",
            r"approved",
            r"authorized",
            r"granted",
            r"device.*has.*been.*approved",
        ]

        found_success = any(
            re.search(pattern, response.text, re.IGNORECASE)
            for pattern in success_patterns
        )

        if found_success or response.status_code == 200:
            self.details["step3_success"] = True
            self.details["steps_completed"] = 3
            return True
        else:
            raise Exception(
                f"Step 3 failed - No success indicators found (HTTP {response.status_code})"
            )

    def approve(self) -> Dict[str, any]:
        """
        Execute full approval flow

        Returns:
            dict: Result with success status and details
        """
        try:
            self.step1_visit_verification_url()
            self.step2_submit_login()
            self.step3_approve_device()

            return {
                "success": True,
                "msg": "Device authorization approved successfully",
                "details": self.details,
            }
        except Exception as e:
            return {
                "success": False,
                "msg": str(e),
                "details": self.details,
            }


def approve_device(module):
    """Execute device approval flow using module parameters"""
    verification_uri = module.params["verification_uri"]
    username = module.params["username"]
    password = module.params["password"]
    proxy = module.params.get("proxy")

    # Create approver instance
    approver = RedHatDeviceApprover(verification_uri, username, password, proxy)

    # Execute approval flow
    result = approver.approve()

    # Add changed status
    result["changed"] = result["success"]

    return result


def run_module():
    """Main module execution function"""
    module_args = dict(
        verification_uri=dict(type="str", required=True),
        username=dict(type="str", required=True),
        password=dict(type="str", required=True, no_log=True),
        proxy=dict(type="str", required=False, default=None),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False,  # Cannot dry-run external authentication
    )

    # Check for requests library
    if not HAS_REQUESTS:
        module.fail_json(
            msg="requests library is required for this module. Install with: pip install requests",
            changed=False,
        )

    # Validate verification_uri
    if not module.params["verification_uri"].startswith("http"):
        module.fail_json(
            msg=f"Invalid verification_uri: {module.params['verification_uri']}. Must start with http:// or https://",
            changed=False,
        )

    # Validate proxy if provided
    if module.params.get("proxy") and not module.params["proxy"].startswith("http"):
        module.fail_json(
            msg=f"Invalid proxy URL: {module.params['proxy']}. Must start with http:// or https://",
            changed=False,
        )

    # Execute approval flow
    try:
        result = approve_device(module)

        if result["success"]:
            module.exit_json(**result)
        else:
            module.fail_json(**result)
    except Exception as e:
        module.fail_json(
            msg=f"Unexpected error during device approval: {str(e)}", changed=False
        )


def main():
    run_module()


if __name__ == "__main__":
    main()
