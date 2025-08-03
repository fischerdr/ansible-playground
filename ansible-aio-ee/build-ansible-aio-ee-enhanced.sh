#!/bin/bash
#
# Enhanced Ansible All-In-One Execution Environment Builder
# 
# This script automatically updates collection requirements and builds
# the execution environment with the latest dependencies.
#
# Usage:
#   ./build-ansible-aio-ee-enhanced.sh [OPTIONS]
#
# Options:
#   --update-collections    Update collection requirements before build
#   --no-cache             Build without Docker cache
#   --push                 Push to registry after build
#   --registry REGISTRY    Override registry URL
#   --tag TAG              Override image tag
#   --dry-run              Show what would be done without executing
#   --verbose              Show verbose output

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
DEFAULT_REGISTRY="localhost"
DEFAULT_TAG="latest"
DEFAULT_IMAGE_NAME="ansible-aio-ee"
UPDATE_COLLECTIONS=true
USE_CACHE=true
PUSH_IMAGE=false
DRY_RUN=false
VERBOSE=false
REGISTRY="${DEFAULT_REGISTRY}"
TAG="${DEFAULT_TAG}"

# Project root (assuming script is in ansible-aio-ee subdirectory)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --update-collections)
            UPDATE_COLLECTIONS=true
            shift
            ;;
        --no-update-collections)
            UPDATE_COLLECTIONS=false
            shift
            ;;
        --no-cache)
            USE_CACHE=false
            shift
            ;;
        --push)
            PUSH_IMAGE=true
            shift
            ;;
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --tag)
            TAG="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --update-collections      Update collection requirements before build (default)"
            echo "  --no-update-collections   Skip collection requirements update"
            echo "  --no-cache               Build without Docker cache"
            echo "  --push                   Push to registry after build"
            echo "  --registry REGISTRY      Override registry URL (default: $DEFAULT_REGISTRY)"
            echo "  --tag TAG                Override image tag (default: $DEFAULT_TAG)"
            echo "  --dry-run                Show what would be done without executing"
            echo "  --verbose, -v            Show verbose output"
            echo "  --help, -h               Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Basic build with collection update"
            echo "  $0 --no-cache --push                # Build without cache and push"
            echo "  $0 --registry quay.io --tag v1.0.0  # Custom registry and tag"
            echo "  $0 --dry-run --verbose               # See what would happen"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}" >&2
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build full image name
FULL_IMAGE_NAME="${REGISTRY}/${DEFAULT_IMAGE_NAME}:${TAG}"

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}" >&2
}

log_step() {
    echo -e "${CYAN}🔧 $1${NC}"
}

execute_command() {
    local cmd="$1"
    local description="${2:-Executing command}"
    
    if [[ "$VERBOSE" == "true" ]]; then
        log_info "Command: $cmd"
    fi
    
    if [[ "$DRY_RUN" == "false" ]]; then
        if ! eval "$cmd"; then
            log_error "$description failed"
            return 1
        fi
    else
        log_info "[DRY-RUN] Would execute: $cmd"
    fi
}

# Main execution
main() {
    echo -e "${BLUE}🚀 Enhanced Ansible AIO Execution Environment Builder${NC}"
    echo "=================================================="
    echo ""
    log_info "Project root: $PROJECT_ROOT"
    log_info "Build directory: $BUILD_DIR"
    log_info "Image name: $FULL_IMAGE_NAME"
    log_info "Update collections: $UPDATE_COLLECTIONS"
    log_info "Use cache: $USE_CACHE"
    log_info "Push image: $PUSH_IMAGE"
    log_info "Dry run: $DRY_RUN"
    echo ""

    # Step 1: Validate environment
    log_step "Validating build environment..."
    
    # Check if we're in the right directory
    if [[ ! -f "$BUILD_DIR/ansible-aio-ee.yml" ]]; then
        log_error "ansible-aio-ee.yml not found in $BUILD_DIR"
        log_error "Make sure you're running this script from the ansible-aio-ee directory"
        exit 1
    fi

    # Check for required files in project root
    for file in "requirements.txt" "requirements.yml"; do
        if [[ ! -f "$PROJECT_ROOT/$file" ]]; then
            log_error "Required file not found: $PROJECT_ROOT/$file"
            exit 1
        fi
    done

    # Check for collection requirements management
    if [[ "$UPDATE_COLLECTIONS" == "true" ]]; then
        if [[ ! -f "$PROJECT_ROOT/scripts/update_collection_requirements.py" ]]; then
            log_warning "Collection requirements script not found at $PROJECT_ROOT/scripts/update_collection_requirements.py"
            log_warning "Skipping collection requirements update"
            UPDATE_COLLECTIONS=false
        fi
    fi

    log_success "Environment validation completed"

    # Step 2: Update collection requirements
    if [[ "$UPDATE_COLLECTIONS" == "true" ]]; then
        log_step "Updating collection requirements..."
        
        cd "$PROJECT_ROOT"
        execute_command \
            "python scripts/update_collection_requirements.py" \
            "Collection requirements update"
        
        if [[ "$DRY_RUN" == "false" && -f "requirements-collections.txt" ]]; then
            log_success "Collection requirements updated"
            if [[ "$VERBOSE" == "true" ]]; then
                echo "Collection requirements preview:"
                head -20 requirements-collections.txt | sed 's/^/  /'
                echo "  ..."
            fi
        fi
    else
        log_info "Skipping collection requirements update"
    fi

    # Step 3: Copy required files to build context
    log_step "Preparing build context..."
    
    cd "$BUILD_DIR"
    
    # Copy requirements files
    for file in "requirements.txt" "requirements-collections.txt" "requirements.yml"; do
        if [[ -f "$PROJECT_ROOT/$file" ]]; then
            execute_command \
                "cp '$PROJECT_ROOT/$file' '$BUILD_DIR/$file'" \
                "Copying $file to build context"
        else
            log_warning "$file not found, will be skipped in build"
        fi
    done

    log_success "Build context prepared"

    # Step 4: Build the execution environment
    log_step "Building Ansible Execution Environment..."

    # Determine build tool (ansible-builder or docker/podman)
    if command -v ansible-builder >/dev/null 2>&1; then
        log_info "Using ansible-builder for EE build"
        
        # Build command with ansible-builder
        build_cmd="ansible-builder build"
        build_cmd="$build_cmd --file ansible-aio-ee.yml"
        build_cmd="$build_cmd --tag '$FULL_IMAGE_NAME'"
        build_cmd="$build_cmd --container-runtime docker"
        
        if [[ "$USE_CACHE" == "false" ]]; then
            build_cmd="$build_cmd --no-cache"
        fi
        
        if [[ "$VERBOSE" == "true" ]]; then
            build_cmd="$build_cmd --verbosity 2"
        fi
        
    elif command -v docker >/dev/null 2>&1; then
        log_info "Using Docker for container build"
        
        # Build command with docker
        build_cmd="docker build"
        build_cmd="$build_cmd --file Containerfile.ansible-aio-ee"
        build_cmd="$build_cmd --tag '$FULL_IMAGE_NAME'"
        
        if [[ "$USE_CACHE" == "false" ]]; then
            build_cmd="$build_cmd --no-cache"
        fi
        
        build_cmd="$build_cmd ."
        
    elif command -v podman >/dev/null 2>&1; then
        log_info "Using Podman for container build"
        
        # Build command with podman
        build_cmd="podman build"
        build_cmd="$build_cmd --file Containerfile.ansible-aio-ee"
        build_cmd="$build_cmd --tag '$FULL_IMAGE_NAME'"
        
        if [[ "$USE_CACHE" == "false" ]]; then
            build_cmd="$build_cmd --no-cache"
        fi
        
        build_cmd="$build_cmd ."
        
    else
        log_error "No suitable build tool found (ansible-builder, docker, or podman)"
        exit 1
    fi

    execute_command "$build_cmd" "Building execution environment"
    log_success "Execution environment built successfully: $FULL_IMAGE_NAME"

    # Step 5: Push to registry (if requested)
    if [[ "$PUSH_IMAGE" == "true" ]]; then
        log_step "Pushing image to registry..."
        
        if command -v docker >/dev/null 2>&1; then
            execute_command "docker push '$FULL_IMAGE_NAME'" "Pushing image with Docker"
        elif command -v podman >/dev/null 2>&1; then
            execute_command "podman push '$FULL_IMAGE_NAME'" "Pushing image with Podman"
        else
            log_error "No suitable tool found for pushing (docker or podman)"
            exit 1
        fi
        
        log_success "Image pushed to registry: $FULL_IMAGE_NAME"
    fi

    # Step 6: Verification and summary
    log_step "Build verification..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # Test the built image
        if command -v docker >/dev/null 2>&1; then
            test_cmd="docker run --rm '$FULL_IMAGE_NAME' ansible --version"
        elif command -v podman >/dev/null 2>&1; then
            test_cmd="podman run --rm '$FULL_IMAGE_NAME' ansible --version"
        fi
        
        if [[ -n "${test_cmd:-}" ]]; then
            execute_command "$test_cmd" "Testing built image"
            log_success "Image verification completed"
        fi
    fi

    # Clean up build context files
    if [[ "$DRY_RUN" == "false" ]]; then
        for file in "requirements.txt" "requirements-collections.txt" "requirements.yml"; do
            if [[ -f "$BUILD_DIR/$file" && -f "$PROJECT_ROOT/$file" ]]; then
                rm -f "$BUILD_DIR/$file"
            fi
        done
        
        # Clean up ansible-builder context directory
        if [[ -d "$BUILD_DIR/context" ]]; then
            rm -rf "$BUILD_DIR/context"
            log_success "Removed context directory"
        fi
        
        # Clean up .ansible-builder directory
        if [[ -d "$BUILD_DIR/.ansible-builder" ]]; then
            rm -rf "$BUILD_DIR/.ansible-builder"
            log_success "Removed .ansible-builder directory"
        fi
    fi

    echo ""
    echo -e "${GREEN}🎉 Build completed successfully!${NC}"
    echo "=================================================="
    echo -e "${BLUE}Image:${NC} $FULL_IMAGE_NAME"
    echo -e "${BLUE}Size:${NC} $(docker images --format "table {{.Size}}" "$FULL_IMAGE_NAME" 2>/dev/null | tail -n1 || echo "Unknown")"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo "  1. Test the image: docker run -it --rm $FULL_IMAGE_NAME"
    echo "  2. Use in playbooks: ansible-playbook --ee-image $FULL_IMAGE_NAME"
    echo "  3. Configure in ansible-navigator.yml"
    
    if [[ "$PUSH_IMAGE" == "false" && "$REGISTRY" != "localhost" ]]; then
        echo "  4. Push to registry: docker push $FULL_IMAGE_NAME"
    fi
}

# Execute main function
main "$@"