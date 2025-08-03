#!/bin/bash

# Test script for Ansible All-In-One Execution Environment
# This script validates that all tools and dependencies are properly installed

set -euo pipefail

# Configuration
EE_NAME="ansible-aio-ee"
EE_TAG="latest"
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Test the Ansible All-In-One Execution Environment.

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    -t, --tag TAG           Specify image tag (default: latest)
    -n, --name NAME         Specify image name (default: ansible-aio-ee)

EXAMPLES:
    $0                                    # Test with default settings
    $0 -v -t v1.0.0                      # Test with verbose output and specific tag
    $0 -n my-ee-name                      # Test with custom image name

EOF
}

# Function to test command availability
test_command() {
    local cmd="$1"
    local description="$2"
    
    print_status "Testing $description..."
    
    if docker run --rm "${EE_NAME}:${EE_TAG}" which "$cmd" >/dev/null 2>&1; then
        print_success "$description is available"
        return 0
    else
        print_error "$description is not available"
        return 1
    fi
}

# Function to test command version
test_version() {
    local cmd="$1"
    local description="$2"
    local version_args="${3:---version}"
    
    print_status "Testing $description version..."
    
    if docker run --rm "${EE_NAME}:${EE_TAG}" "$cmd" $version_args >/dev/null 2>&1; then
        print_success "$description version check passed"
        return 0
    else
        print_error "$description version check failed"
        return 1
    fi
}

# Function to test Python package
test_python_package() {
    local package="$1"
    local description="$2"
    
    print_status "Testing Python package: $description..."
    
    if docker run --rm "${EE_NAME}:${EE_TAG}" python3 -c "import $package; print('$package imported successfully')" >/dev/null 2>&1; then
        print_success "Python package $description is available"
        return 0
    else
        print_error "Python package $description is not available"
        return 1
    fi
}

# Function to test Ansible collections
test_ansible_collections() {
    print_status "Testing Ansible collections..."
    
    local collections_output
    collections_output=$(docker run --rm "${EE_NAME}:${EE_TAG}" ansible-galaxy collection list 2>/dev/null)
    
    if echo "$collections_output" | grep -q "amazon.aws\|community.aws\|kubernetes.core\|google.cloud"; then
        print_success "Key Ansible collections are available"
        if [[ "$VERBOSE" == "true" ]]; then
            echo "$collections_output"
        fi
        return 0
    else
        print_error "Required Ansible collections are missing"
        return 1
    fi
}

# Function to test environment variables
test_environment() {
    print_status "Testing environment variables..."
    
    local env_output
    env_output=$(docker run --rm "${EE_NAME}:${EE_TAG}" env | grep -E "(ANSIBLE_|PYTHON|AWS_|KUBECONFIG|HELM_)")
    
    if echo "$env_output" | grep -q "ANSIBLE_FORCE_COLOR=1"; then
        print_success "Ansible environment variables are set"
        if [[ "$VERBOSE" == "true" ]]; then
            echo "$env_output"
        fi
        return 0
    else
        print_error "Ansible environment variables are not properly set"
        return 1
    fi
}

# Function to test file permissions and directories
test_filesystem() {
    print_status "Testing filesystem setup..."
    
    # Test working directory
    if docker run --rm "${EE_NAME}:${EE_TAG}" pwd | grep -q "/workspace"; then
        print_success "Working directory is correctly set to /workspace"
    else
        print_error "Working directory is not correctly set"
        return 1
    fi
    
    # Test user
    if docker run --rm "${EE_NAME}:${EE_TAG}" whoami | grep -q "ansible"; then
        print_success "Running as non-root user 'ansible'"
    else
        print_error "Not running as expected user"
        return 1
    fi
    
    # Test required directories
    if docker run --rm "${EE_NAME}:${EE_TAG}" test -d /tmp/.helm && \
       docker run --rm "${EE_NAME}:${EE_TAG}" test -d /tmp/.kube && \
       docker run --rm "${EE_NAME}:${EE_TAG}" test -d /logs; then
        print_success "Required directories exist"
        return 0
    else
        print_error "Required directories are missing"
        return 1
    fi
}

# Function to run comprehensive tests
run_tests() {
    local failed_tests=0
    local total_tests=0
    
    print_status "Starting comprehensive EE testing..."
    
    # Test basic commands
    local commands=(
        "python3:Python 3"
        "python:Python"
        "ansible:Ansible"
        "kubectl:Kubernetes CLI"
        "helm:Helm"
        "terraform:Terraform"
        "oc:OpenShift CLI"
        "vault:HashiCorp Vault CLI"
        "aws:AWS CLI"
        "gcloud:Google Cloud SDK"
        "gsutil:Google Cloud Storage"
        "bq:BigQuery CLI"
    )
    
    for cmd_info in "${commands[@]}"; do
        IFS=':' read -r cmd description <<< "$cmd_info"
        total_tests=$((total_tests + 1))
        
        if test_command "$cmd" "$description"; then
            if [[ "$cmd" != "python" && "$cmd" != "python3" ]]; then
                test_version "$cmd" "$description" || failed_tests=$((failed_tests + 1))
            fi
        else
            failed_tests=$((failed_tests + 1))
        fi
    done
    
    # Test Python packages
    local python_packages=(
        "kubernetes:Kubernetes Python SDK"
        "boto3:AWS Python SDK"
        "hvac:HashiCorp Vault Python SDK"
        "google.auth:Google Auth Python SDK"
        "ansible:Ansible Python package"
    )
    
    for pkg_info in "${python_packages[@]}"; do
        IFS=':' read -r pkg description <<< "$pkg_info"
        total_tests=$((total_tests + 1))
        
        test_python_package "$pkg" "$description" || failed_tests=$((failed_tests + 1))
    done
    
    # Test Ansible collections
    total_tests=$((total_tests + 1))
    test_ansible_collections || failed_tests=$((failed_tests + 1))
    
    # Test environment variables
    total_tests=$((total_tests + 1))
    test_environment || failed_tests=$((failed_tests + 1))
    
    # Test filesystem setup
    total_tests=$((total_tests + 1))
    test_filesystem || failed_tests=$((failed_tests + 1))
    
    # Summary
    echo
    print_status "Test Summary:"
    print_status "Total tests: $total_tests"
    print_status "Passed: $((total_tests - failed_tests))"
    print_status "Failed: $failed_tests"
    
    if [[ $failed_tests -eq 0 ]]; then
        print_success "All tests passed! The EE is ready for use."
        return 0
    else
        print_error "$failed_tests test(s) failed. Please check the EE build."
        return 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -t|--tag)
            EE_TAG="$2"
            shift 2
            ;;
        -n|--name)
            EE_NAME="$2"
            shift 2
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_status "Starting Ansible All-In-One EE testing..."
    print_status "EE Name: ${EE_NAME}"
    print_status "EE Tag: ${EE_TAG}"
    
    # Check if image exists
    if ! docker image inspect "${EE_NAME}:${EE_TAG}" >/dev/null 2>&1; then
        print_error "Image ${EE_NAME}:${EE_TAG} not found. Please build the EE first."
        exit 1
    fi
    
    # Run tests
    run_tests
}

# Run main function
main "$@" 