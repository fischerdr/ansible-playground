#!/bin/bash

# Preparation script for Air-gapped Ansible Execution Environment
# This script downloads all necessary tools and dependencies for offline building

set -euo pipefail

# Configuration
TOOLS_DIR="tools"
COLLECTIONS_DIR="collections"
WHEELS_DIR="wheels"
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

Prepare air-gapped build environment by downloading all necessary tools and dependencies.

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    --tools-only            Download only tools (skip Python wheels and collections)
    --wheels-only           Download only Python wheels (skip tools and collections)
    --collections-only      Download only Ansible collections (skip tools and wheels)
    --clean                 Clean existing downloads before starting

EXAMPLES:
    $0                      # Download everything
    $0 -v                   # Download with verbose output
    $0 --tools-only         # Download only binary tools
    $0 --clean              # Clean and download everything

EOF
}

# Function to create directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p "$TOOLS_DIR"
    mkdir -p "$COLLECTIONS_DIR"
    mkdir -p "$WHEELS_DIR"
    
    print_success "Directories created"
}

# Function to download tools
download_tools() {
    print_status "Downloading binary tools..."
    
    cd "$TOOLS_DIR"
    
    # Download kubectl
    print_status "Downloading kubectl..."
    if ! [ -f "kubectl" ]; then
        curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
        chmod +x kubectl
        print_success "kubectl downloaded"
    else
        print_warning "kubectl already exists, skipping"
    fi
    
    # Download Helm
    print_status "Downloading Helm..."
    if ! [ -f "helm" ]; then
        curl -LO "https://get.helm.sh/helm-v3.14.4-linux-amd64.tar.gz"
        tar xzf helm-v3.14.4-linux-amd64.tar.gz
        mv linux-amd64/helm ./
        rm -rf linux-amd64 helm-v3.14.4-linux-amd64.tar.gz
        chmod +x helm
        print_success "Helm downloaded"
    else
        print_warning "helm already exists, skipping"
    fi
    
    # Download Terraform
    print_status "Downloading Terraform..."
    if ! [ -f "terraform" ]; then
        curl -LO "https://releases.hashicorp.com/terraform/1.7.5/terraform_1.7.5_linux_amd64.zip"
        unzip terraform_1.7.5_linux_amd64.zip
        rm terraform_1.7.5_linux_amd64.zip
        chmod +x terraform
        print_success "Terraform downloaded"
    else
        print_warning "terraform already exists, skipping"
    fi
    
    # Download OpenShift CLI
    print_status "Downloading OpenShift CLI..."
    if ! [ -f "oc" ]; then
        curl -LO "https://mirror.openshift.com/pub/openshift-v4/x86_64/clients/ocp/stable/openshift-client-linux.tar.gz"
        tar xzf openshift-client-linux.tar.gz
        rm openshift-client-linux.tar.gz kubectl || true  # Remove kubectl if extracted with oc
        chmod +x oc
        print_success "OpenShift CLI downloaded"
    else
        print_warning "oc already exists, skipping"
    fi
    
    # Download AWS CLI
    print_status "Downloading AWS CLI..."
    if ! [ -f "awscliv2.zip" ]; then
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
        print_success "AWS CLI downloaded"
    else
        print_warning "awscliv2.zip already exists, skipping"
    fi
    
    # Download Google Cloud SDK
    print_status "Downloading Google Cloud SDK..."
    if ! [ -f "google-cloud-sdk.tar.gz" ]; then
        curl -L "https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-462.0.1-linux-x86_64.tar.gz" -o "google-cloud-sdk.tar.gz"
        print_success "Google Cloud SDK downloaded"
    else
        print_warning "google-cloud-sdk.tar.gz already exists, skipping"
    fi
    
    cd ..
    print_success "All tools downloaded to $TOOLS_DIR/"
}

# Function to download Python wheels
download_wheels() {
    print_status "Downloading Python wheels..."
    
    if ! command -v pip &> /dev/null; then
        print_error "pip is not available. Please install Python and pip first."
        return 1
    fi
    
    # Download wheels for air-gapped requirements
    pip download -r requirements-airgapped.txt -d "$WHEELS_DIR/"
    
    # Also download wheels for the main project requirements if available
    if [[ -f "../requirements.txt" ]]; then
        print_status "Found main project requirements.txt, downloading additional wheels..."
        pip download -r ../requirements.txt -d "$WHEELS_DIR/" || print_warning "Some main project wheels may not be available"
    fi
    
    # Download additional cloud SDK wheels if available
    pip download awscli boto3 google-cloud-sdk kubernetes openshift -d "$WHEELS_DIR/" || print_warning "Some cloud SDK wheels may not be available"
    
    print_success "Python wheels downloaded to $WHEELS_DIR/"
}

# Function to download Ansible collections
download_collections() {
    print_status "Downloading Ansible collections..."
    
    if ! command -v ansible-galaxy &> /dev/null; then
        print_error "ansible-galaxy is not available. Please install Ansible first."
        return 1
    fi
    
    # Download collections to local directory
    # Try local requirements first, then fall back to main project requirements
    if [[ -f "requirements-airgapped.yml" ]]; then
        print_status "Using local requirements-airgapped.yml..."
        ansible-galaxy collection download -r requirements-airgapped.yml -p "$COLLECTIONS_DIR/"
    elif [[ -f "../requirements.yml" ]]; then
        print_status "Using main project requirements.yml..."
        ansible-galaxy collection download -r ../requirements.yml -p "$COLLECTIONS_DIR/"
    else
        print_error "No requirements.yml file found (checked requirements-airgapped.yml and ../requirements.yml)"
        return 1
    fi
    
    print_success "Ansible collections downloaded to $COLLECTIONS_DIR/"
}

# Function to clean existing downloads
clean_downloads() {
    print_status "Cleaning existing downloads..."
    
    if [ -d "$TOOLS_DIR" ]; then
        rm -rf "$TOOLS_DIR"
        print_success "Cleaned $TOOLS_DIR/"
    fi
    
    if [ -d "$COLLECTIONS_DIR" ]; then
        rm -rf "$COLLECTIONS_DIR"
        print_success "Cleaned $COLLECTIONS_DIR/"
    fi
    
    if [ -d "$WHEELS_DIR" ]; then
        rm -rf "$WHEELS_DIR"
        print_success "Cleaned $WHEELS_DIR/"
    fi
}

# Function to create air-gapped build instructions
create_instructions() {
    cat > "AIRGAPPED-BUILD-INSTRUCTIONS.md" << 'EOF'
# Air-gapped Build Instructions

## Prerequisites

1. Transfer this entire directory to your air-gapped environment
2. Ensure Docker or Podman is available
3. Ensure ansible-builder is installed

## Directory Structure

After running the preparation script, you should have:

```
├── tools/                          # Binary tools
│   ├── kubectl
│   ├── helm
│   ├── terraform
│   ├── oc
│   ├── awscliv2.zip
│   └── google-cloud-sdk.tar.gz
├── wheels/                         # Python wheels
│   └── *.whl files
├── collections/                    # Ansible collections
│   └── ansible_collections/
├── ansible-aio-ee-airgapped.yml   # EE definition
├── requirements-airgapped.yml     # Collections requirements
├── requirements-airgapped.txt     # Python requirements
└── build-airgapped-ee.sh          # Build script
```

## Building the EE

### Using ansible-builder (recommended)
```bash
ansible-builder build --file ansible-aio-ee-airgapped.yml --tag ansible-aio-ee-airgapped:latest
```

### Using Docker directly
```bash
docker build -f Containerfile.ansible-aio-ee-airgapped -t ansible-aio-ee-airgapped:latest .
```

## Testing

```bash
# Test the built image
docker run --rm ansible-aio-ee-airgapped:latest ansible --version
docker run --rm ansible-aio-ee-airgapped:latest kubectl version --client
docker run --rm ansible-aio-ee-airgapped:latest helm version
```

## Troubleshooting

1. **Missing tools**: Ensure all files in tools/ directory are present
2. **Permission errors**: Check that binary files in tools/ are executable
3. **Collection errors**: Verify collections are properly downloaded in collections/
4. **Python package errors**: Check that wheels are available in wheels/

## Updating

To update tools or dependencies:
1. Run the preparation script again in an internet-connected environment
2. Transfer the updated files to your air-gapped environment
3. Rebuild the EE
EOF

    print_success "Created AIRGAPPED-BUILD-INSTRUCTIONS.md"
}

# Parse command line arguments
DOWNLOAD_TOOLS=true
DOWNLOAD_WHEELS=true
DOWNLOAD_COLLECTIONS=true
CLEAN_FIRST=false

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
        --tools-only)
            DOWNLOAD_TOOLS=true
            DOWNLOAD_WHEELS=false
            DOWNLOAD_COLLECTIONS=false
            shift
            ;;
        --wheels-only)
            DOWNLOAD_TOOLS=false
            DOWNLOAD_WHEELS=true
            DOWNLOAD_COLLECTIONS=false
            shift
            ;;
        --collections-only)
            DOWNLOAD_TOOLS=false
            DOWNLOAD_WHEELS=false
            DOWNLOAD_COLLECTIONS=true
            shift
            ;;
        --clean)
            CLEAN_FIRST=true
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
    print_status "Starting air-gapped environment preparation..."
    
    # Clean if requested
    if [[ "$CLEAN_FIRST" == "true" ]]; then
        clean_downloads
    fi
    
    # Create directories
    create_directories
    
    # Download components based on options
    if [[ "$DOWNLOAD_TOOLS" == "true" ]]; then
        download_tools
    fi
    
    if [[ "$DOWNLOAD_WHEELS" == "true" ]]; then
        download_wheels
    fi
    
    if [[ "$DOWNLOAD_COLLECTIONS" == "true" ]]; then
        download_collections
    fi
    
    # Create instructions
    create_instructions
    
    print_success "Air-gapped environment preparation completed!"
    print_status "Next steps:"
    echo "1. Transfer this entire directory to your air-gapped environment"
    echo "2. Follow the instructions in AIRGAPPED-BUILD-INSTRUCTIONS.md"
    echo "3. Build the EE using ansible-builder or Docker"
}

# Run main function
main "$@"