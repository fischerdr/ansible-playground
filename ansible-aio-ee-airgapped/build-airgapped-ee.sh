#!/bin/bash

# Build script for Air-gapped Ansible Execution Environment
# This script builds the EE using locally available tools and dependencies

set -euo pipefail

# Configuration
EE_NAME="ansible-aio-ee-airgapped"
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

Build the Air-gapped Ansible All-In-One Execution Environment.

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    -t, --tag TAG           Specify image tag (default: latest)
    -m, --method METHOD     Build method: ansible-builder or docker (default: ansible-builder)
    -p, --push              Push image to registry after build
    -r, --registry REGISTRY Registry to push to (required if --push is used)
    --test                  Run tests after build
    --clean                 Clean up build artifacts
    --check-deps            Check if all dependencies are available locally

EXAMPLES:
    $0                                    # Build with default settings
    $0 -v -t v1.0.0                      # Build with verbose output and specific tag
    $0 -m docker                         # Build using Docker directly
    $0 --check-deps                      # Check if all local dependencies are available
    $0 --test                            # Build and run tests

EOF
}

# Function to check local dependencies
check_dependencies() {
    print_status "Checking local dependencies for air-gapped build..."
    
    local missing_deps=0
    
    # Check for tools directory
    if [[ ! -d "tools" ]]; then
        print_error "tools/ directory not found. Run prepare-airgapped-build.sh first."
        missing_deps=$((missing_deps + 1))
    else
        print_success "tools/ directory found"
        
        # Check individual tools
        local tools=("kubectl" "helm" "terraform" "oc" "vault" "awscliv2.zip" "google-cloud-sdk.tar.gz")
        for tool in "${tools[@]}"; do
            if [[ -f "tools/$tool" ]]; then
                print_success "✓ tools/$tool"
            else
                print_error "✗ tools/$tool missing"
                missing_deps=$((missing_deps + 1))
            fi
        done
    fi
    
    # Check for collections directory
    if [[ ! -d "collections" ]]; then
        print_warning "collections/ directory not found. Collections will be installed from requirements."
    else
        print_success "collections/ directory found"
        local collection_count
        collection_count=$(find collections/ -name "*.tar.gz" 2>/dev/null | wc -l)
        print_status "Found $collection_count collection archives"
    fi
    
    # Check for wheels directory
    if [[ ! -d "wheels" ]]; then
        print_warning "wheels/ directory not found. Python packages will be installed from PyPI if available."
    else
        print_success "wheels/ directory found"
        local wheel_count
        wheel_count=$(find wheels/ -name "*.whl" 2>/dev/null | wc -l)
        print_status "Found $wheel_count wheel files"
    fi
    
    # Check for collection wheels directory
    if [[ ! -d "wheels-collections" ]]; then
        print_warning "wheels-collections/ directory not found. Collection dependencies may not be available offline."
    else
        print_success "wheels-collections/ directory found"
        local collection_wheel_count
        collection_wheel_count=$(find wheels-collections/ -name "*.whl" 2>/dev/null | wc -l)
        print_status "Found $collection_wheel_count collection dependency wheel files"
    fi
    
    # Check for requirements files
    if [[ -f "requirements-airgapped.txt" ]]; then
        print_success "✓ requirements-airgapped.txt"
    else
        print_error "✗ requirements-airgapped.txt missing"
        missing_deps=$((missing_deps + 1))
    fi
    
    if [[ -f "requirements-airgapped.yml" ]]; then
        print_success "✓ requirements-airgapped.yml"
    else
        print_error "✗ requirements-airgapped.yml missing"
        missing_deps=$((missing_deps + 1))
    fi
    
    # Check for collection requirements file
    if [[ -f "requirements-collections-airgapped.txt" ]]; then
        print_success "✓ requirements-collections-airgapped.txt"
    else
        print_warning "⚠ requirements-collections-airgapped.txt missing (collection dependencies may not be complete)"
    fi
    
    # Check for EE definition file
    if [[ -f "ansible-aio-ee-airgapped.yml" ]]; then
        print_success "✓ ansible-aio-ee-airgapped.yml"
    else
        print_error "✗ ansible-aio-ee-airgapped.yml missing"
        missing_deps=$((missing_deps + 1))
    fi
    
    if [[ $missing_deps -eq 0 ]]; then
        print_success "All dependencies are available for air-gapped build"
        return 0
    else
        print_error "$missing_deps dependencies are missing"
        print_status "Run 'prepare-airgapped-build.sh' in an internet-connected environment first"
        return 1
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking build prerequisites..."
    
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
    
    print_success "Prerequisites check passed"
}

# Function to prepare build context
prepare_build_context() {
    print_status "Preparing build context..."
    
    # Clean and create context directory
    if [[ -d "context" ]]; then
        print_status "Removing existing context directory..."
        rm -rf context
    fi
    
    print_status "Creating fresh context directory..."
    mkdir -p context
    
    # Copy all required directories and files to context
    print_status "Setting up build context..."
    
    # Copy directories
    for dir in tools wheels wheels-collections collections; do
        if [[ -d "$dir" ]]; then
            print_status "Copying $dir/ to context directory..."
            cp -r "$dir" context/
        else
            print_warning "$dir directory not found, creating empty directory in context"
            mkdir -p "context/$dir"
        fi
    done
    
    # Copy requirements files
    for req_file in requirements-airgapped.txt requirements-airgapped.yml requirements-collections-airgapped.txt; do
        if [[ -f "$req_file" ]]; then
            print_status "Copying $req_file to context directory..."
            cp "$req_file" context/
        else
            print_warning "$req_file not found"
        fi
    done
    
    # Copy the EE definition file to context
    if [[ -f "ansible-aio-ee-airgapped.yml" ]]; then
        print_status "Copying ansible-aio-ee-airgapped.yml to context directory..."
        cp ansible-aio-ee-airgapped.yml context/
    else
        print_error "ansible-aio-ee-airgapped.yml not found"
        exit 1
    fi
    
    print_success "Build context prepared successfully"
}

# Function to build with ansible-builder
build_with_ansible_builder() {
    print_status "Building air-gapped EE with ansible-builder..."
    
    # Prepare build context
    prepare_build_context
    
    local build_args=""
    if [[ "$VERBOSE" == "true" ]]; then
        build_args="--verbosity 3"
    fi
    
    # Check if ansible-builder supports --context
    if ansible-builder build --help | grep -q "\-\-context"; then
        # Use --context if available (newer versions)
        print_status "Running ansible-builder build with --context..."
        if ansible-builder build \
            --no-cache \
            --file context/ansible-aio-ee-airgapped.yml \
            --context context \
            --tag "${EE_NAME}:${EE_TAG}" \
            $build_args; then
            print_success "Air-gapped EE built successfully with ansible-builder"
        else
            print_error "Failed to build air-gapped EE with ansible-builder"
            exit 1
        fi
    else
        # Fallback: change directory and run from context (older versions)
        print_status "Running ansible-builder build from context directory..."
        cd context
        
        if ansible-builder build \
            --no-cache \
            --file ansible-aio-ee-airgapped.yml \
            --tag "${EE_NAME}:${EE_TAG}" \
            $build_args; then
            print_success "Air-gapped EE built successfully with ansible-builder"
            cd ..
        else
            print_error "Failed to build air-gapped EE with ansible-builder"
            cd ..
            exit 1
        fi
    fi
}

# Function to build with Docker
build_with_docker() {
    print_status "Building air-gapped EE with Docker..."
    
    # Prepare build context
    prepare_build_context
    
    # Create a Containerfile for the air-gapped build
    create_airgapped_containerfile
    
    local build_args=""
    if [[ "$VERBOSE" == "true" ]]; then
        build_args="--progress=plain"
    fi
    
    # Change to context directory for build
    cd context
    
    if docker build \
        -f Containerfile.ansible-aio-ee-airgapped \
        -t "${EE_NAME}:${EE_TAG}" \
        $build_args .; then
        print_success "Air-gapped EE built successfully with Docker"
    else
        print_error "Failed to build air-gapped EE with Docker"
        cd ..
        exit 1
    fi
    
    # Return to parent directory
    cd ..
}

# Function to create Containerfile for air-gapped build
create_airgapped_containerfile() {
    cat > "context/Containerfile.ansible-aio-ee-airgapped" << 'EOF'
# Air-gapped Ansible All-In-One Execution Environment
# Based on Red Hat Universal Base Image 8 (stream)
# Uses local tools and dependencies for offline building

FROM registry.access.redhat.com/ubi8/ubi:8.9

# Set build arguments
ARG BUILD_ENV=production
ARG PYTHON_VERSION=3.11
ARG AIRGAPPED=true

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ANSIBLE_FORCE_COLOR=1 \
    ANSIBLE_HOST_KEY_CHECKING=false \
    ANSIBLE_RETRY_FILES_ENABLED=false \
    ANSIBLE_COLLECTIONS_PATH=./collections:/usr/share/ansible/collections \
    ANSIBLE_ROLES_PATH=./roles:/usr/share/ansible/roles \
    AWS_DEFAULT_REGION=us-east-1 \
    KUBECONFIG=/tmp/kubeconfig \
    HELM_HOME=/tmp/.helm \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    LOG_DIR=/logs \
    REQUESTS_CA_BUNDLE=/etc/pki/tls/certs/ca-bundle.crt \
    CURL_CA_BUNDLE=/etc/pki/tls/certs/ca-bundle.crt

# Install system dependencies (Layer 1: Base system)
RUN dnf -y update && \
    dnf -y install dnf-utils && \
    dnf config-manager --set-enabled crb || dnf config-manager --set-enabled powertools || true && \
    dnf -y install \
    git-core \
    python3.11 \
    python3.11-devel \
    python3.11-pip \
    krb5-devel \
    krb5-workstation \
    openssl-devel \
    git-lfs \
    subversion \
    sshpass \
    rsync \
    wget \
    nc \
    curl \
    podman-remote \
    cmake \
    gcc \
    gcc-c++ \
    make \
    libcurl-devel \
    unzip \
    which \
    jq \
    ca-certificates \
    gnupg2 && \
    dnf clean all

# Set Python 3.11 as default using alternatives system (Layer 2: Python setup)
RUN alternatives --install /usr/bin/unversioned-python python /usr/bin/python3.11 1 && \
    alternatives --set python /usr/bin/python3.11 && \
    ln -sf /usr/bin/unversioned-python /usr/bin/python && \
    /usr/bin/unversioned-python -m pip install -U pip setuptools wheel

# Copy and install local tools (Layer 3: Local tools)
COPY tools/kubectl /usr/local/bin/kubectl
COPY tools/helm /usr/local/bin/helm
COPY tools/terraform /usr/local/bin/terraform
COPY tools/oc /usr/local/bin/oc
COPY tools/vault /usr/local/bin/vault
COPY tools/awscliv2.zip /tmp/awscliv2.zip
COPY tools/google-cloud-sdk.tar.gz /tmp/google-cloud-sdk.tar.gz

RUN chmod +x /usr/local/bin/kubectl /usr/local/bin/helm /usr/local/bin/terraform /usr/local/bin/oc /usr/local/bin/vault

# Install yq manually since it's not available in UBI8
RUN curl -L https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -o /usr/local/bin/yq && chmod +x /usr/local/bin/yq || echo "yq installation failed - may be offline"

# Install AWS CLI from local archive (Layer 4: AWS CLI)
RUN cd /tmp && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf aws awscliv2.zip

# Install Google Cloud SDK from local archive (Layer 5: Google Cloud SDK)
RUN cd /root && \
    tar xzf /tmp/google-cloud-sdk.tar.gz && \
    rm /tmp/google-cloud-sdk.tar.gz && \
    /root/google-cloud-sdk/install.sh --quiet --usage-reporting=false --path-update=false && \
    ln -s /root/google-cloud-sdk/bin/gcloud /usr/local/bin/gcloud && \
    ln -s /root/google-cloud-sdk/bin/gsutil /usr/local/bin/gsutil && \
    ln -s /root/google-cloud-sdk/bin/bq /usr/local/bin/bq

# Copy requirements files (Layer 6: Requirements)
COPY requirements-airgapped.txt /tmp/requirements-airgapped.txt
COPY requirements-airgapped.yml /tmp/requirements-airgapped.yml

# Copy collection requirements if available
COPY requirements-collections-airgapped.txt /tmp/requirements-collections-airgapped.txt

# Copy local wheels if available (Layer 7: Local wheels)
COPY wheels/ /tmp/wheels/

# Copy collection wheels if available
COPY wheels-collections/ /tmp/wheels-collections/

# Install Python dependencies (Layer 8: Python packages)
# Install collection dependencies first (they may be needed by main requirements)
RUN if [ -s "/tmp/requirements-collections-airgapped.txt" ] && [ -d "/tmp/wheels-collections" ] && [ "$(ls -A /tmp/wheels-collections)" ]; then \
        echo "Installing collection dependencies from local wheels..."; \
        python -m pip install --no-index --find-links /tmp/wheels-collections -r /tmp/requirements-collections-airgapped.txt; \
    elif [ -s "/tmp/requirements-collections-airgapped.txt" ]; then \
        echo "Collection dependency wheels not found, attempting online install..."; \
        python -m pip install -r /tmp/requirements-collections-airgapped.txt || echo "Collection dependencies installation failed - may not be fully offline"; \
    else \
        echo "No collection requirements file found, skipping collection dependencies"; \
    fi

# Install main requirements
RUN if [ -d "/tmp/wheels" ] && [ "$(ls -A /tmp/wheels)" ]; then \
        echo "Installing main requirements from local wheels..."; \
        python -m pip install --no-index --find-links /tmp/wheels -r /tmp/requirements-airgapped.txt; \
    else \
        echo "Main requirement wheels not found, attempting online install..."; \
        python -m pip install -r /tmp/requirements-airgapped.txt; \
    fi

# Copy and install Ansible collections (Layer 9: Collections)
COPY collections/ /tmp/collections/
RUN if [ -d "/tmp/collections" ] && [ "$(ls -A /tmp/collections)" ]; then \
        echo "Installing collections from local archives..."; \
        find /tmp/collections -name "*.tar.gz" -exec ansible-galaxy collection install {} -p /usr/share/ansible/collections \; || \
        ansible-galaxy collection install -r /tmp/requirements-airgapped.yml -p /usr/share/ansible/collections; \
    else \
        echo "No local collections found, installing from requirements..."; \
        ansible-galaxy collection install -r /tmp/requirements-airgapped.yml -p /usr/share/ansible/collections; \
    fi

# Remove old Python versions and clean up (Layer 10: Cleanup)
RUN dnf -y remove python3.6 python3.6-devel python3.8 python3.8-devel python3.9 python3.9-devel || true && \
    rm -rf /tmp/* /var/cache/dnf /var/cache/yum && \
    python -m pip cache purge

# Create necessary directories and set up environment (Layer 11: Environment setup)
RUN mkdir -p /tmp/.helm /tmp/.kube /logs /workspace && \
    useradd -m -s /bin/bash ansible && \
    chown -R ansible:ansible /workspace /logs

# Set up PATH to include all tools
ENV PATH="/usr/local/bin:/root/google-cloud-sdk/bin:${PATH}"

# Verify installations (Layer 12: Verification)
RUN python --version && \
    which kubectl && \
    which helm && \
    which terraform && \
    which oc && \
    which vault && \
    which aws && \
    which gcloud && \
    which yq && \
    ansible --version && \
    oc version --client

# Set working directory and switch to non-root user
WORKDIR /workspace
USER ansible

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import ansible; print('Air-gapped Ansible EE is healthy')" || exit 1

# Default command
CMD ["/bin/bash"]
EOF

    print_success "Created Containerfile.ansible-aio-ee-airgapped in context directory"
}

# Function to test the EE
test_ee() {
    print_status "Testing the Air-gapped Execution Environment..."
    
    # Determine which container runtime to use
    local container_cmd=""
    if command -v docker &> /dev/null; then
        container_cmd="docker"
    elif command -v podman &> /dev/null; then
        container_cmd="podman"
    else
        print_error "Neither docker nor podman is available for testing"
        return 1
    fi
    
    # Test basic functionality
    print_status "Testing basic tools..."
    
    $container_cmd run --rm "${EE_NAME}:${EE_TAG}" python3 --version
    $container_cmd run --rm "${EE_NAME}:${EE_TAG}" ansible --version
    $container_cmd run --rm "${EE_NAME}:${EE_TAG}" which kubectl
    $container_cmd run --rm "${EE_NAME}:${EE_TAG}" which helm
    $container_cmd run --rm "${EE_NAME}:${EE_TAG}" which terraform
    $container_cmd run --rm "${EE_NAME}:${EE_TAG}" which oc
    $container_cmd run --rm "${EE_NAME}:${EE_TAG}" which vault
    $container_cmd run --rm "${EE_NAME}:${EE_TAG}" which aws
    $container_cmd run --rm "${EE_NAME}:${EE_TAG}" which gcloud
    $container_cmd run --rm "${EE_NAME}:${EE_TAG}" which yq
    
    print_success "Basic tool tests passed"
    
    # Test Ansible collections
    print_status "Testing Ansible collections..."
    $container_cmd run --rm "${EE_NAME}:${EE_TAG}" ansible-galaxy collection list
    
    print_success "Collection tests passed"
    
    # Test Python packages
    print_status "Testing Python packages..."
    $container_cmd run --rm "${EE_NAME}:${EE_TAG}" python3 -c "
try:
    import kubernetes
    print('✓ kubernetes module available')
except ImportError:
    print('⚠ kubernetes module not available')

try:
    import boto3
    print('✓ boto3 module available')
except ImportError:
    print('⚠ boto3 module not available')

try:
    import hvac
    print('✓ hvac module available')
except ImportError:
    print('⚠ hvac module not available')

try:
    import ansible
    print('✓ ansible module available')
except ImportError:
    print('✗ ansible module not available')

print('Python package test completed')
"
    
    print_success "Python package tests passed"
    print_success "Air-gapped EE is ready for use!"
}

# Function to push image
push_image() {
    if [[ -z "$REGISTRY" ]]; then
        print_error "Registry not specified. Use -r/--registry option."
        exit 1
    fi
    
    # Determine which container runtime to use
    local container_cmd=""
    if command -v docker &> /dev/null; then
        container_cmd="docker"
    elif command -v podman &> /dev/null; then
        container_cmd="podman"
    else
        print_error "Neither docker nor podman is available for pushing"
        exit 1
    fi
    
    print_status "Tagging image for registry..."
    $container_cmd tag "${EE_NAME}:${EE_TAG}" "${REGISTRY}:${EE_TAG}"
    
    print_status "Pushing image to registry..."
    if $container_cmd push "${REGISTRY}:${EE_TAG}"; then
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
    if [[ -d "context" ]]; then
        rm -rf context
        print_success "Removed context directory"
    fi
    
    # Remove ansible-builder artifacts
    if [[ -d ".ansible-builder" ]]; then
        rm -rf .ansible-builder
        print_success "Removed .ansible-builder directory"
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
        --check-deps)
            CHECK_DEPS_ONLY=true
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
    print_status "Starting Air-gapped Ansible All-In-One EE build process..."
    print_status "EE Name: ${EE_NAME}"
    print_status "EE Tag: ${EE_TAG}"
    print_status "Build Method: ${BUILD_METHOD}"
    
    # Check dependencies only mode
    if [[ "${CHECK_DEPS_ONLY:-false}" == "true" ]]; then
        check_dependencies
        exit $?
    fi
    
    # Cleanup only mode
    if [[ "${CLEANUP_ONLY:-false}" == "true" ]]; then
        cleanup
        exit 0
    fi
    
    # Check prerequisites and dependencies
    check_prerequisites
    check_dependencies
    
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
    
    print_success "Air-gapped build process completed successfully!"
    print_status "Image: ${EE_NAME}:${EE_TAG}"
    
    if [[ "$PUSH_IMAGE" == "true" ]]; then
        print_status "Registry: ${REGISTRY}:${EE_TAG}"
    fi
    
    # Clean up build artifacts
    cleanup
    
    print_status "Next steps:"
    echo "1. Test the EE: ./build-airgapped-ee.sh --test"
    echo "2. Use the EE: docker run -it --rm ${EE_NAME}:${EE_TAG} /bin/bash"
    echo "3. Or with podman: podman run -it --rm ${EE_NAME}:${EE_TAG} /bin/bash"
}

# Run main function
main "$@"