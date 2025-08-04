#!/bin/bash

# Build script for Ansible All-In-One Execution Environment
# This script builds the EE using ansible-builder and provides testing capabilities

set -euo pipefail

# Configuration
EE_NAME="ansible-aio-ee"
EE_TAG="latest"
BUILD_METHOD="ansible-builder"  # or "docker"
VERBOSE=false
PUSH_IMAGE=false
REGISTRY=""

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

Build and optionally test the Ansible All-In-One Execution Environment.

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    -t, --tag TAG           Specify image tag (default: latest)
    -m, --method METHOD     Build method: ansible-builder or docker (default: ansible-builder)
    -p, --push              Push image to registry after build
    -r, --registry REGISTRY Registry to push to (required if --push is used)
    --test                  Run tests after build
    --clean                 Clean up build artifacts

EXAMPLES:
    $0                                    # Build with default settings
    $0 -v -t v1.0.0                      # Build with verbose output and specific tag
    $0 -m docker                         # Build using Docker directly
    $0 -p -r quay.io/myuser/ansible-aio-ee  # Build and push to registry
    $0 --test                            # Build and run tests
    $0 --clean                           # Clean up build artifacts

EOF
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check for ansible-builder
    if ! command -v ansible-builder &> /dev/null; then
        print_error "ansible-builder is not installed. Please install it first:"
        echo "pip install ansible-builder"
        exit 1
    fi
    
    # Check for Docker/Podman
    if ! command -v docker &> /dev/null && ! command -v podman &> /dev/null; then
        print_error "Neither docker nor podman is available. Please install one of them."
        exit 1
    fi
    
    # Check for required files
    if [[ ! -f "requirements.txt" ]]; then
        print_error "requirements.txt not found in current directory"
        exit 1
    fi
    
    if [[ ! -f "requirements.yml" ]]; then
        print_error "requirements.yml not found in current directory"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to build with ansible-builder
build_with_ansible_builder() {
    print_status "Building EE with ansible-builder..."
    
    local build_args=""
    if [[ "$VERBOSE" == "true" ]]; then
        build_args="--verbosity 3"
    fi
    
    if ansible-builder build \
        --file ansible-aio-ee.yml \
        --tag "${EE_NAME}:${EE_TAG}" \
        $build_args; then
        print_success "EE built successfully with ansible-builder"
    else
        print_error "Failed to build EE with ansible-builder"
        exit 1
    fi
}

# Function to build with Docker
build_with_docker() {
    print_status "Building EE with Docker..."
    
    local build_args=""
    if [[ "$VERBOSE" == "true" ]]; then
        build_args="--progress=plain"
    fi
    
    if docker build \
        -f Containerfile.ansible-aio-ee \
        -t "${EE_NAME}:${EE_TAG}" \
        $build_args .; then
        print_success "EE built successfully with Docker"
    else
        print_error "Failed to build EE with Docker"
        exit 1
    fi
}

# Function to test the EE
test_ee() {
    print_status "Testing the Execution Environment..."
    
    # Test basic functionality
    print_status "Testing basic tools..."
    
    docker run --rm "${EE_NAME}:${EE_TAG}" python3 --version
    docker run --rm "${EE_NAME}:${EE_TAG}" ansible --version
    docker run --rm "${EE_NAME}:${EE_TAG}" kubectl version --client
    docker run --rm "${EE_NAME}:${EE_TAG}" helm version
    docker run --rm "${EE_NAME}:${EE_TAG}" terraform version
    docker run --rm "${EE_NAME}:${EE_TAG}" oc version
    docker run --rm "${EE_NAME}:${EE_TAG}" vault version
    docker run --rm "${EE_NAME}:${EE_TAG}" aws --version
    docker run --rm "${EE_NAME}:${EE_TAG}" gcloud version
    
    print_success "Basic tool tests passed"
    
    # Test Ansible collections
    print_status "Testing Ansible collections..."
    docker run --rm "${EE_NAME}:${EE_TAG}" ansible-galaxy collection list
    
    print_success "Collection tests passed"
    
    # Test Python packages
    print_status "Testing Python packages..."
    docker run --rm "${EE_NAME}:${EE_TAG}" python3 -c "
import kubernetes
import boto3
import hvac
import google.auth
print('All required Python packages are available')
"
    
    print_success "Python package tests passed"
}

# Function to push image
push_image() {
    if [[ -z "$REGISTRY" ]]; then
        print_error "Registry not specified. Use -r/--registry option."
        exit 1
    fi
    
    print_status "Tagging image for registry..."
    docker tag "${EE_NAME}:${EE_TAG}" "${REGISTRY}:${EE_TAG}"
    
    print_status "Pushing image to registry..."
    if docker push "${REGISTRY}:${EE_TAG}"; then
        print_success "Image pushed successfully to ${REGISTRY}:${EE_TAG}"
    else
        print_error "Failed to push image to registry"
        exit 1
    fi
}

# Function to clean up
cleanup() {
    print_status "Cleaning up build artifacts..."
    
    # Remove build context
    if [[ -d ".ansible-builder" ]]; then
        rm -rf .ansible-builder
        print_success "Removed .ansible-builder directory"
    fi
    
    # Remove ansible-builder context directory
    if [[ -d "context" ]]; then
        rm -rf context
        print_success "Removed context directory"
    fi
    
    # Remove temporary files
    find . -name "*.tmp" -delete 2>/dev/null || true
    
    print_success "Cleanup completed"
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
        -m|--method)
            BUILD_METHOD="$2"
            shift 2
            ;;
        -p|--push)
            PUSH_IMAGE=true
            shift
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        --test)
            RUN_TESTS=true
            shift
            ;;
        --clean)
            CLEANUP_ONLY=true
            shift
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
    print_status "Starting Ansible All-In-One EE build process..."
    print_status "EE Name: ${EE_NAME}"
    print_status "EE Tag: ${EE_TAG}"
    print_status "Build Method: ${BUILD_METHOD}"
    
    # Check prerequisites
    check_prerequisites
    
    # Cleanup only mode
    if [[ "${CLEANUP_ONLY:-false}" == "true" ]]; then
        cleanup
        exit 0
    fi
    
    # Build the EE
    case "$BUILD_METHOD" in
        "ansible-builder")
            build_with_ansible_builder
            ;;
        "docker")
            build_with_docker
            ;;
        *)
            print_error "Invalid build method: $BUILD_METHOD"
            exit 1
            ;;
    esac
    
    # Run tests if requested
    if [[ "${RUN_TESTS:-false}" == "true" ]]; then
        test_ee
    fi
    
    # Push image if requested
    if [[ "$PUSH_IMAGE" == "true" ]]; then
        push_image
    fi
    
    print_success "Build process completed successfully!"
    print_status "Image: ${EE_NAME}:${EE_TAG}"
    
    if [[ "$PUSH_IMAGE" == "true" ]]; then
        print_status "Registry: ${REGISTRY}:${EE_TAG}"
    fi

}

# Run main function
main "$@" 