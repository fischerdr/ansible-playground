#!/bin/bash
# Master test runner for validation integration tests
# Runs all validation logic tests with detailed reporting

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROLE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_PYTHON="${ROLE_DIR}/../../.venv/bin/python"
ANSIBLE_PLAYBOOK="${ROLE_DIR}/../../.venv/bin/ansible-playbook"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================"
echo "Portworx Upgrade Validation Tests"
echo "========================================"
echo ""

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run a test playbook
run_test() {
    local test_file=$1
    local test_name=$2

    echo -e "${BLUE}Running: ${test_name}${NC}"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if $ANSIBLE_PLAYBOOK "$test_file" --connection=local; then
        echo -e "${GREEN}✅ PASSED: ${test_name}${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo ""
        return 0
    else
        echo -e "${RED}❌ FAILED: ${test_name}${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo ""
        return 1
    fi
}

# Run all validation tests
echo "Running Storage Pool Validation Tests..."
run_test "${SCRIPT_DIR}/test_validation_storage_pools.yml" "Storage Pool Health Tests"

echo "Running Volume Health Validation Tests..."
run_test "${SCRIPT_DIR}/test_validation_volumes.yml" "Volume Health Tests"

echo "Running STC Conditions Validation Tests..."
run_test "${SCRIPT_DIR}/test_validation_stc_conditions.yml" "STC Conditions Tests"

echo "Running Node Statistics Validation Tests..."
run_test "${SCRIPT_DIR}/test_validation_nodes_simple.yml" "Node Statistics Tests"

# Summary
echo "========================================"
echo "Test Summary"
echo "========================================"
echo -e "Total Tests:  ${TOTAL_TESTS}"
echo -e "${GREEN}Passed:       ${PASSED_TESTS}${NC}"
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}Failed:       ${FAILED_TESTS}${NC}"
else
    echo -e "Failed:       ${FAILED_TESTS}"
fi
echo "========================================"

# Exit with appropriate code
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}Some tests FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}All tests PASSED${NC}"
    exit 0
fi
