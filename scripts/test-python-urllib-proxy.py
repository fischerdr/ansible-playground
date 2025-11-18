#!/usr/bin/env python3
"""
Test Python urllib proxy connectivity to Red Hat API.
This helps diagnose why urllib might fail where curl succeeds.
"""

import sys
import urllib.request
from urllib.error import URLError, HTTPError

# Configuration
PROXY_HTTP = "http://proxy-appgw.aexp.com:9090"
PROXY_HTTPS = "http://proxy-appgw.aexp.com:9090"
TEST_URL = "https://api.access.redhat.com/support/v1/cases"

print("=" * 80)
print("Testing Python urllib proxy connectivity")
print("=" * 80)
print(f"Proxy HTTP:  {PROXY_HTTP}")
print(f"Proxy HTTPS: {PROXY_HTTPS}")
print(f"Test URL:    {TEST_URL}")
print()

# Test 1: ProxyHandler only
print("-" * 80)
print("Test 1: Using ProxyHandler only")
print("-" * 80)
try:
    proxy_handler = urllib.request.ProxyHandler(
        {
            "http": PROXY_HTTP,
            "https": PROXY_HTTPS,
        }
    )
    opener = urllib.request.build_opener(proxy_handler)
    urllib.request.install_opener(opener)

    req = urllib.request.Request(TEST_URL)
    req.add_header("Accept", "application/json")

    print("Attempting connection...")
    response = urllib.request.urlopen(req, timeout=10)
    print(f"✓ SUCCESS: HTTP {response.status}")
    print(f"Response headers: {dict(response.headers)}")
except HTTPError as e:
    print(f"HTTP Error {e.code}: {e.reason}")
    print(f"Response body: {e.read().decode('utf-8', errors='ignore')[:200]}")
except URLError as e:
    print(f"✗ FAILED: {e.reason}")
except Exception as e:
    print(f"✗ FAILED: {type(e).__name__}: {e}")

print()

# Test 2: Environment variables only
print("-" * 80)
print("Test 2: Using environment variables only")
print("-" * 80)
import os

os.environ["http_proxy"] = PROXY_HTTP
os.environ["https_proxy"] = PROXY_HTTPS

try:
    # Reset opener to use environment variables
    urllib.request.install_opener(urllib.request.build_opener())

    req = urllib.request.Request(TEST_URL)
    req.add_header("Accept", "application/json")

    print("Attempting connection...")
    response = urllib.request.urlopen(req, timeout=10)
    print(f"✓ SUCCESS: HTTP {response.status}")
    print(f"Response headers: {dict(response.headers)}")
except HTTPError as e:
    print(f"HTTP Error {e.code}: {e.reason}")
    print(f"Response body: {e.read().decode('utf-8', errors='ignore')[:200]}")
except URLError as e:
    print(f"✗ FAILED: {e.reason}")
except Exception as e:
    print(f"✗ FAILED: {type(e).__name__}: {e}")

# Clean up
del os.environ["http_proxy"]
del os.environ["https_proxy"]

print()
print("=" * 80)
print("Diagnosis complete")
print("=" * 80)
