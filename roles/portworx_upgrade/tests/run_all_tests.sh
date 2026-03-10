#!/bin/bash
# Run all portworx_upgrade role tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROLE_DIR="$(dirname "$SCRIPT_DIR")"

echo "═══════════════════════════════════════════════════════════"
echo "PORTWORX UPGRADE ROLE - TEST SUITE"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Activate virtual environment if it exists
if [ -f "$ROLE_DIR/../../.venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$ROLE_DIR/../../.venv/bin/activate"
fi

# Unit tests
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "RUNNING UNIT TESTS"
echo "═══════════════════════════════════════════════════════════"
echo ""

if [ -f "$SCRIPT_DIR/unit/test_operator_version_filters.py" ]; then
    echo "Running unit/test_operator_version_filters.py..."
    python "$SCRIPT_DIR/unit/test_operator_version_filters.py" || exit 1
    echo ""
fi

if [ -f "$SCRIPT_DIR/test_storage_classification.py" ]; then
    echo "Running test_storage_classification.py..."
    python "$SCRIPT_DIR/test_storage_classification.py" || exit 1
    echo ""
fi

# Integration tests
echo "═══════════════════════════════════════════════════════════"
echo "RUNNING INTEGRATION TESTS"
echo "═══════════════════════════════════════════════════════════"
echo ""

if [ -f "$SCRIPT_DIR/integration/test_jinja2_standalone.py" ]; then
    echo "Running integration/test_jinja2_standalone.py..."
    python "$SCRIPT_DIR/integration/test_jinja2_standalone.py" || exit 1
    echo ""
fi

if [ -f "$SCRIPT_DIR/integration/test_logic_standalone.py" ]; then
    echo "Running integration/test_logic_standalone.py..."
    python "$SCRIPT_DIR/integration/test_logic_standalone.py" || exit 1
    echo ""
fi

if [ -f "$SCRIPT_DIR/integration/test_subscription_discovery.py" ]; then
    echo "Running integration/test_subscription_discovery.py..."
    python "$SCRIPT_DIR/integration/test_subscription_discovery.py" || exit 1
    echo ""
fi

if [ -f "$SCRIPT_DIR/integration/test_post_step_validation.py" ]; then
    echo "Running integration/test_post_step_validation.py..."
    python "$SCRIPT_DIR/integration/test_post_step_validation.py" || exit 1
    echo ""
fi

# Summary
echo "═══════════════════════════════════════════════════════════"
echo "ALL TESTS PASSED SUCCESSFULLY ✓"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Test Results:"
echo "  - Unit Tests: PASS ✓"
echo "    - Operator Version Filters ✓"
echo "    - Storage Pod Classification ✓"
echo "  - Integration Tests: PASS ✓"
echo "    - Jinja2 Template Logic ✓"
echo "    - Sequential Upgrade Logic ✓"
echo "    - Subscription Discovery ✓"
echo "    - Post-Step Validation ✓"
echo ""
