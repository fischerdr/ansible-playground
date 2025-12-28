#!/usr/bin/env python3
"""
Test Red Hat SSO Device Authorization Auto-Approval via HTTP

This script attempts to programmatically approve device authorization
without using a full browser (Selenium/Playwright).

Usage:
    python3 test_redhat_auto_approve.py <verification_uri> <username> <password> [proxy]

Example:
    python3 test_redhat_auto_approve.py \
        "https://sso.redhat.com/auth/realms/redhat-external/device?user_code=ABCD-EFGH" \
        "user@domain.com" \
        "password123" \
        "http://proxy-appgw.aexp.com:9090"

Exit Codes:
    0 = Success (auto-approval worked)
    1 = Failed (requires browser/2FA/unsupported)
    2 = Invalid arguments
"""

import re
import sys
from typing import Dict, Optional, Tuple
from urllib.parse import urljoin

# Ignore warrings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import requests
except ImportError:
    print("ERROR: requests library not installed")
    print("Install with: pip install requests")
    sys.exit(2)


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

        # Disable SSL certificate verification
        self.session.verify = False

        # Suppress SSL warnings
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Configure proxy if provided
        if self.proxy:
            self.session.proxies = {
                "http": self.proxy,
                "https": self.proxy,
            }
            print(f"Using proxy: {self.proxy}")

    def log(self, step: str, message: str, detail: str = ""):
        """Print formatted log message"""
        print(f"[{step}] {message}")
        if detail:
            print(f"    {detail}")

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
        self.log("1", "Visiting verification URL", self.verification_uri)

        try:
            response = self.session.get(
                self.verification_uri, allow_redirects=True, timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as e:
            self.log("1", "✗ FAILED", f"Request error: {e}")
            return False

        self.current_url = response.url
        self.current_html = response.text

        # Debug output
        print("\n[DEBUG] Step 1 Response:")
        print(f"  Status Code: {response.status_code}")
        print(f"  Final URL: {response.url}")
        print(f"  Redirect History: {[r.url for r in response.history]}")
        print(f"  Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"  HTML Length: {len(response.text)} bytes")

        # Check if we're at login page
        if "login" in response.url.lower() or "login" in response.text.lower():
            self.log("1", "✓ Redirected to login page", response.url)
            return True
        else:
            self.log("1", "✗ Unexpected page", f"URL: {response.url}")
            # Save HTML for debugging
            with open("/tmp/redhat_sso_debug.html", "w") as f:
                f.write(response.text)
            self.log("1", "HTML saved to /tmp/redhat_sso_debug.html for debugging")
            print("\n[DEBUG] HTML preview (first 500 chars):")
            print(response.text[:500])
            return False

    def step2_submit_login(self) -> bool:  # noqa: C901
        """Submit login credentials"""
        self.log("2", "Attempting to submit login credentials")

        # Extract login form data
        action_url, form_data = self.extract_form_data(self.current_html, "")

        if not action_url:
            self.log("2", "✗ FAILED", "Could not find login form action URL")
            print("\n[DEBUG] Available forms in HTML:")
            forms = re.findall(r"<form[^>]*>.*?</form>", self.current_html, re.DOTALL)
            print(f"  Found {len(forms)} form(s)")
            return False

        # Make action URL absolute
        if not action_url.startswith("http"):
            action_url = urljoin(self.current_url, action_url)

        self.log("2", f"Login form action: {action_url}")

        # Add credentials to form data
        form_data.update({"username": self.username, "password": self.password})

        # Log form fields (without password)
        safe_form_data = {
            k: v if k != "password" else "***" for k, v in form_data.items()
        }
        self.log("2", f"Form fields: {', '.join(safe_form_data.keys())}")
        print("\n[DEBUG] Step 2 Form Submission:")
        print(f"  Action URL: {action_url}")
        print(f"  Form Fields: {safe_form_data}")

        try:
            response = self.session.post(
                action_url, data=form_data, allow_redirects=True, timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as e:
            self.log("2", "✗ FAILED", f"Request error: {e}")
            return False

        self.current_url = response.url
        self.current_html = response.text

        print("\n[DEBUG] Step 2 Response:")
        print(f"  Status Code: {response.status_code}")
        print(f"  Final URL: {response.url}")
        print(f"  Redirect History: {[r.url for r in response.history]}")
        print(f"  HTML Length: {len(response.text)} bytes")

        # Check for login errors (specific patterns only, not generic "error")
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
                self.log("2", "✗ FAILED", f"Login error detected: {pattern}")
                print(f"  Error pattern matched: {pattern}")
                return False

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
                self.log(
                    "2",
                    "✗ FAILED - 2FA/MFA REQUIRED",
                    "Account has two-factor authentication enabled - cannot automate",
                )
                print(f"  2FA pattern matched: {pattern}")
                return False

        # Check if we reached approval page
        # Look for OAUTH_GRANT in URL (strongest indicator)
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

        print("\n[DEBUG] Approval Page Detection:")
        print(f"  URL contains 'OAUTH_GRANT': {url_has_oauth_grant}")
        print(f"  Found approval indicators in HTML: {found_approval}")
        for pattern in approval_indicators:
            match = re.search(pattern, response.text, re.IGNORECASE)
            print(f"  Pattern '{pattern}': {'MATCH' if match else 'no match'}")

        if url_has_oauth_grant or found_approval:
            self.log("2", "✓ Login successful - reached approval page", response.url)
            return True
        else:
            self.log("2", "✗ UNCERTAIN", "Did not clearly reach approval page")
            # Save HTML for debugging
            with open("/tmp/redhat_sso_post_login.html", "w") as f:
                f.write(response.text)
            self.log("2", "HTML saved to /tmp/redhat_sso_post_login.html")
            print("\n[DEBUG] HTML preview (first 500 chars):")
            print(response.text[:500])
            return False

    def step3_approve_device(self) -> bool:
        """Submit approval for device authorization"""
        self.log("3", "Attempting to approve device authorization")

        # Extract approval form data
        action_url, form_data = self.extract_form_data(self.current_html, "")

        if not action_url:
            self.log("3", "✗ FAILED", "Could not find approval form action URL")
            print("\n[DEBUG] Available forms in HTML:")
            forms = re.findall(r"<form[^>]*>.*?</form>", self.current_html, re.DOTALL)
            print(f"  Found {len(forms)} form(s)")
            print("\n[DEBUG] Looking for buttons in HTML:")
            buttons = re.findall(
                r"<button[^>]*>.*?</button>",
                self.current_html,
                re.DOTALL | re.IGNORECASE,
            )
            print(f"  Found {len(buttons)} button(s)")
            for i, button in enumerate(buttons[:5]):  # Show first 5 buttons
                print(f"  Button {i + 1}: {button[:100]}")
            return False

        # Make action URL absolute
        if not action_url.startswith("http"):
            action_url = urljoin(self.current_url, action_url)

        self.log("3", f"Approval form action: {action_url}")

        # Add approval to form data
        # Try multiple common approval field names
        approval_fields = {
            "approve": "true",
            "grant": "true",
            "authorize": "true",
            "consent": "true",
            "accept": "yes",
        }
        form_data.update(approval_fields)

        self.log("3", f"Form fields: {', '.join(form_data.keys())}")
        print("\n[DEBUG] Step 3 Form Submission:")
        print(f"  Action URL: {action_url}")
        print(f"  Hidden Fields: {list(form_data.keys())}")
        print(f"  Approval Fields Added: {list(approval_fields.keys())}")

        try:
            response = self.session.post(
                action_url, data=form_data, allow_redirects=True, timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as e:
            self.log("3", "✗ FAILED", f"Request error: {e}")
            return False

        print("\n[DEBUG] Step 3 Response:")
        print(f"  Status Code: {response.status_code}")
        print(f"  Final URL: {response.url}")
        print(f"  Redirect History: {[r.url for r in response.history]}")
        print(f"  HTML Length: {len(response.text)} bytes")

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

        print("\n[DEBUG] Success Detection:")
        print(f"  Found success indicators: {found_success}")
        for pattern in success_patterns:
            match = re.search(pattern, response.text, re.IGNORECASE)
            print(f"  Pattern '{pattern}': {'MATCH' if match else 'no match'}")

        if found_success or response.status_code == 200:
            self.log("3", "✓ Approval submitted successfully", response.url)
            # Save successful response for review
            with open("/tmp/redhat_sso_post_approval_success.html", "w") as f:
                f.write(response.text)
            print("  Success HTML saved to /tmp/redhat_sso_post_approval_success.html")
            return True
        else:
            self.log(
                "3", "✗ UNCERTAIN", f"HTTP {response.status_code} - unclear if approved"
            )
            # Save HTML for debugging
            with open("/tmp/redhat_sso_post_approval.html", "w") as f:
                f.write(response.text)
            self.log("3", "HTML saved to /tmp/redhat_sso_post_approval.html")
            print("\n[DEBUG] HTML preview (first 500 chars):")
            print(response.text[:500])
            return False

    def approve(self) -> bool:
        """Execute full approval flow"""
        print("=" * 70)
        print("Red Hat SSO Device Authorization Auto-Approval Test")
        print("=" * 70)
        print(f"Verification URI: {self.verification_uri}")
        print(f"Username: {self.username}")
        print(f"Proxy: {self.proxy if self.proxy else 'None (direct connection)'}")
        print("=" * 70)

        step1_success = self.step1_visit_verification_url()
        step2_success = False
        step3_success = False

        if step1_success:
            step2_success = self.step2_submit_login()
            if step2_success:
                step3_success = self.step3_approve_device()

        # Final Summary
        print("\n" + "=" * 70)
        print("EXECUTION SUMMARY")
        print("=" * 70)
        print(f"Step 1 (Visit URL):    {'✓ SUCCESS' if step1_success else '✗ FAILED'}")
        print(f"Step 2 (Login):        {'✓ SUCCESS' if step2_success else '✗ FAILED'}")
        print(f"Step 3 (Approve):      {'✓ SUCCESS' if step3_success else '✗ FAILED'}")
        print("=" * 70)

        if step3_success:
            print("OVERALL RESULT: ✓ SUCCESS")
            print("Device authorization approved via HTTP!")
            print("\nThis means automation is possible without full browser!")
            print("\nDebug files saved:")
            print("  - /tmp/redhat_sso_post_approval_success.html")
        else:
            print("OVERALL RESULT: ✗ FAILED")
            print("\nTroubleshooting:")
            print("  1. Review debug output above for specific failure point")
            print("  2. Check HTML files saved in /tmp:")
            if not step1_success:
                print("     - /tmp/redhat_sso_debug.html (initial page)")
            if step1_success and not step2_success:
                print("     - /tmp/redhat_sso_post_login.html (after login attempt)")
            if step2_success and not step3_success:
                print(
                    "     - /tmp/redhat_sso_post_approval.html (after approval attempt)"
                )
            print("  3. Verify credentials are correct")
            print("  4. Check if 2FA is enabled on account")
            print("  5. Check if Red Hat changed their SSO page structure")

        print("=" * 70)
        return step3_success


def main():
    """Main entry point"""
    if len(sys.argv) < 4 or len(sys.argv) > 5:
        print(__doc__)
        sys.exit(2)

    verification_uri = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    proxy = sys.argv[4] if len(sys.argv) == 5 else None

    # Validate inputs
    if not verification_uri.startswith("http"):
        print(f"ERROR: Invalid verification URI: {verification_uri}")
        print("Must start with http:// or https://")
        sys.exit(2)

    if proxy and not proxy.startswith("http"):
        print(f"ERROR: Invalid proxy URL: {proxy}")
        print("Must start with http:// or https://")
        sys.exit(2)

    # Run approval test
    approver = RedHatDeviceApprover(verification_uri, username, password, proxy)

    try:
        success = approver.approve()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
