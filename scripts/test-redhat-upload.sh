#!/bin/bash
# Test script for Red Hat case attachment upload via curl
# This mimics what the redhat_upload.py module does

set -e

# Configuration
CASE_NUMBER="${1}"
FILE_PATH="${2}"
DESCRIPTION="${3:-Must-gather upload test from command line - $(date -Iseconds)}"
PROXY="${HTTP_PROXY:-${http_proxy:-}}"  # Use environment proxy if set

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_error() { echo -e "${RED}ERROR: $1${NC}" >&2; }
print_success() { echo -e "${GREEN}SUCCESS: $1${NC}"; }
print_info() { echo -e "${YELLOW}INFO: $1${NC}"; }

# Validate inputs
if [ -z "$CASE_NUMBER" ]; then
    print_error "Case number is required"
    echo ""
    echo "Usage: $0 <case-number> <file-path> [description]"
    echo ""
    echo "Example:"
    echo "  $0 01234567 /tmp/must-gather.tar.gz"
    echo ""
    echo "To find test files created by playbook:"
    echo "  find /tmp -name 'must-gather*.tar.gz' -type f -mmin -60"
    exit 1
fi

if [ -z "$FILE_PATH" ]; then
    print_error "File path is required"
    echo ""
    echo "Usage: $0 <case-number> <file-path> [description]"
    echo ""
    echo "Example:"
    echo "  $0 01234567 /tmp/must-gather.tar.gz"
    echo ""
    echo "To find test files created by playbook:"
    echo "  find /tmp -name 'must-gather*.tar.gz' -type f -mmin -60"
    exit 1
fi

if [ ! -f "$FILE_PATH" ]; then
    print_error "File not found: $FILE_PATH"
    exit 1
fi

# Get file size
FILE_SIZE=$(stat -c%s "$FILE_PATH" 2>/dev/null || stat -f%z "$FILE_PATH" 2>/dev/null)
FILE_SIZE_MB=$(echo "scale=2; $FILE_SIZE / 1024 / 1024" | bc)

# Check for credentials
if [ -z "$RH_USERNAME" ] || [ -z "$RH_PASSWORD" ]; then
    print_error "Red Hat credentials not set"
    echo ""
    echo "Please set environment variables:"
    echo "  export RH_USERNAME='your-username'"
    echo "  export RH_PASSWORD='your-password'"
    echo ""
    echo "Or use an access token:"
    echo "  export RH_ACCESS_TOKEN='your-token'"
    exit 1
fi

print_info "Upload Configuration"
echo "  Case Number: $CASE_NUMBER"
echo "  File: $FILE_PATH"
echo "  File Size: ${FILE_SIZE_MB} MB"
echo "  Description: $DESCRIPTION"
if [ -n "$PROXY" ]; then
    echo "  Proxy: $PROXY"
else
    echo "  Proxy: (none)"
fi
echo ""

# Determine authentication method
if [ -n "$RH_ACCESS_TOKEN" ]; then
    print_info "Using OAuth Bearer token authentication"
    AUTH_HEADER="-H 'Authorization: Bearer ${RH_ACCESS_TOKEN}'"
    AUTH_METHOD="token"
else
    print_info "Using Basic authentication (username/password)"
    AUTH_HEADER="-u '${RH_USERNAME}:${RH_PASSWORD}'"
    AUTH_METHOD="basic"
fi

echo ""
print_info "Starting upload..."

# Create temp file for response
RESPONSE_FILE=$(mktemp)
HTTP_CODE_FILE=$(mktemp)

# Cleanup on exit
trap "rm -f $RESPONSE_FILE $HTTP_CODE_FILE" EXIT

# Execute upload
if [ "$AUTH_METHOD" = "token" ]; then
    if [ -n "$PROXY" ]; then
        HTTP_CODE=$(curl -s -w "%{http_code}" -o "$RESPONSE_FILE" \
            -x "${PROXY}" \
            -X POST \
            -H "Authorization: Bearer ${RH_ACCESS_TOKEN}" \
            -H "Accept: application/json" \
            -F "description=${DESCRIPTION}" \
            -F "file=@${FILE_PATH}" \
            "https://api.access.redhat.com/support/v1/cases/${CASE_NUMBER}/attachments/")
    else
        HTTP_CODE=$(curl -s -w "%{http_code}" -o "$RESPONSE_FILE" \
            -X POST \
            -H "Authorization: Bearer ${RH_ACCESS_TOKEN}" \
            -H "Accept: application/json" \
            -F "description=${DESCRIPTION}" \
            -F "file=@${FILE_PATH}" \
            "https://api.access.redhat.com/support/v1/cases/${CASE_NUMBER}/attachments/")
    fi
else
    if [ -n "$PROXY" ]; then
        HTTP_CODE=$(curl -s -w "%{http_code}" -o "$RESPONSE_FILE" \
            -u "${RH_USERNAME}:${RH_PASSWORD}" \
            -x "${PROXY}" \
            -X POST \
            -H "Accept: application/json" \
            -F "description=${DESCRIPTION}" \
            -F "file=@${FILE_PATH}" \
            "https://api.access.redhat.com/support/v1/cases/${CASE_NUMBER}/attachments/")
    else
        HTTP_CODE=$(curl -s -w "%{http_code}" -o "$RESPONSE_FILE" \
            -u "${RH_USERNAME}:${RH_PASSWORD}" \
            -X POST \
            -H "Accept: application/json" \
            -F "description=${DESCRIPTION}" \
            -F "file=@${FILE_PATH}" \
            "https://api.access.redhat.com/support/v1/cases/${CASE_NUMBER}/attachments/")
    fi
fi

echo ""
echo "========================================================================"
echo "UPLOAD RESULT"
echo "========================================================================"
echo "HTTP Status Code: $HTTP_CODE"
echo ""

# Parse response
if [ "$HTTP_CODE" = "200" ]; then
    print_success "Upload completed successfully!"
    echo ""
    echo "Response body:"
    cat "$RESPONSE_FILE" | python3 -m json.tool 2>/dev/null || cat "$RESPONSE_FILE"
    exit 0
elif [ "$HTTP_CODE" = "401" ]; then
    print_error "Authentication failed (401 Unauthorized)"
    echo "Check your credentials and try again"
elif [ "$HTTP_CODE" = "403" ]; then
    print_error "Access forbidden (403 Forbidden)"
    echo "You may not have permission to upload to this case"
elif [ "$HTTP_CODE" = "404" ]; then
    print_error "Case not found (404 Not Found)"
    echo "Verify the case number: $CASE_NUMBER"
elif [ "$HTTP_CODE" = "503" ]; then
    print_error "Service unavailable (503 Service Unavailable)"
    echo "Red Hat API or CDN is experiencing issues"
    echo "Wait a few minutes and try again"
else
    print_error "Upload failed with HTTP $HTTP_CODE"
fi

echo ""
echo "Response body:"
cat "$RESPONSE_FILE"
echo ""

exit 1
