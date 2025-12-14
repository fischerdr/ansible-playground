#!/bin/bash
# Run all unit tests for portworx_upgrade monitoring fixes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
VENV_BIN="$PROJECT_ROOT/.venv/bin"

echo "==================================================================="
echo "Running All Portworx Upgrade Monitoring Tests"
echo "==================================================================="
echo ""

# Test 1: Filter Plugin Unit Tests
echo "1. Running filter plugin unit tests (Python)..."
echo "-------------------------------------------------------------------"
$VENV_BIN/python "$SCRIPT_DIR/test_storage_classification.py"
echo ""

# Test 2: Storage Detection Logic Tests
echo "2. Running storage detection logic tests (Ansible)..."
echo "-------------------------------------------------------------------"
$VENV_BIN/ansible-playbook "$SCRIPT_DIR/test_storage_detection.yml"
echo ""

# Test 3: Activity Detection Logic Tests
echo "3. Running activity detection logic tests (Ansible)..."
echo "-------------------------------------------------------------------"
$VENV_BIN/ansible-playbook "$SCRIPT_DIR/test_activity_detection.yml"
echo ""

# Test 4: Impatient Mode Multi-Batch Tests
echo "4. Running impatient mode multi-batch tests (Ansible)..."
echo "-------------------------------------------------------------------"
$VENV_BIN/ansible-playbook "$SCRIPT_DIR/test_impatient_mode.yml"
echo ""

# Test 5: Per-Pod Timeout Logic Tests
echo "5. Running per-pod timeout logic tests (Ansible)..."
echo "-------------------------------------------------------------------"
$VENV_BIN/ansible-playbook "$SCRIPT_DIR/test_per_pod_timeout.yml"
echo ""

# Test 6: Node Validation Logic Tests
echo "6. Running node validation logic tests (Ansible)..."
echo "-------------------------------------------------------------------"
$VENV_BIN/ansible-playbook "$SCRIPT_DIR/test_validate_nodes.yml"
echo ""

# Test 7: Global Timeout Sliding Window Tests
echo "7. Running global timeout sliding window tests (Ansible)..."
echo "-------------------------------------------------------------------"
$VENV_BIN/ansible-playbook "$SCRIPT_DIR/test_global_timeout_sliding_window.yml"
echo ""

echo "==================================================================="
echo "ALL TESTS PASSED"
echo "==================================================================="
echo ""
echo "Test Summary:"
echo "  Filter plugin storage classification (6 tests)"
echo "  Storage pod detection label-based (5 tests)"
echo "  Activity detection completion-based (5 tests)"
echo "  Impatient mode multi-batch execution (7 tests)"
echo "  Per-pod timeout logic (3 tests)"
echo "  Node validation logic (6 tests)"
echo "  Global timeout sliding window (4 tests)"
echo ""
echo "Critical fixes validated:"
echo "  1. Storage detection using pod labels (prevents data loss)"
echo "  2. Activity detection based on completions (timeout works)"
echo "  3. Impatient mode allows multiple batches (actual acceleration)"
echo "  4. Per-pod timeout timestamp parsing (correct age calculation)"
echo "  5. Node validation Jinja2 logic (Ready and schedulable checks)"
echo "  6. Filter plugin documentation complete (all 4 filters)"
echo "  7. Global timeout sliding window (oldest pod tracking)"
echo ""
