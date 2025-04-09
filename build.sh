#!/usr/bin/env bash

# Exit on error
set -e

# Define logging function
log() {
    local level="$1"
    local message="$2"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] ${message}"
}

# Define error function
error() {
    log "ERROR" "$1"
    exit 1
}

# Define variables
BUILDER_TAG="development-ee"
EE_TAG="development-ee:latest"
BUILDX_NAME="development-ee"
CONTEXT_DIR="context"
BUILD_BOTH=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --docker)
            BUILD_DOCKER=true
            shift
            ;;
        --podman)
            BUILD_PODMAN=true
            shift
            ;;
        --both)
            BUILD_BOTH=true
            shift
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Check prerequisites
if ! command -v docker >/dev/null 2>&1 && ! command -v podman >/dev/null 2>&1; then
    error "Neither Docker nor Podman is installed"
fi

if ! command -v ansible-builder >/dev/null 2>&1; then
    error "ansible-builder is not installed"
fi

# Cleanup function for Docker
cleanup_docker() {
    log "INFO" "Cleaning up Docker environment"
    # Remove buildx builder
    docker buildx rm "${BUILDX_NAME}" || true
    # Remove dangling images
    docker image prune -f || true
    # Remove unused volumes
    docker volume prune -f || true
    # Remove unused networks
    docker network prune -f || true
    # Remove build cache
    docker builder prune -f || true
    # Remove specific images
    docker rmi "${BUILDER_TAG}" "${EE_TAG}" || true
}

# Cleanup function for Podman
cleanup_podman() {
    log "INFO" "Cleaning up Podman environment"
    # Remove all unused images
    podman image prune -f || true
    # Remove all unused volumes
    podman volume prune -f || true
    # Remove all unused networks
    podman network prune -f || true
    # Remove build cache
    podman system prune -f || true
    # Remove specific images
    podman rmi "${BUILDER_TAG}" "${EE_TAG}" || true
}

# Main cleanup function
cleanup() {
    log "INFO" "Starting cleanup process"
    if [ "${BUILD_DOCKER}" = true ]; then
        cleanup_docker
    fi
    if [ "${BUILD_PODMAN}" = true ]; then
        cleanup_podman
    fi
    # Clean up Context directory
    rm -rf "${CONTEXT_DIR}" || true
    log "INFO" "Cleanup completed"
}

# Build function for Docker
build_docker() {
    # Run cleanup function
    cleanup

    log "INFO" "Building with Docker"
    # Build execution environment
    ansible-builder build -v3 -t "${BUILDER_TAG}" --container-runtime=docker || error "Failed to build Docker execution environment"
    
    # Generate Dockerfile
    log "INFO" "Generating Dockerfile for Docker build"
    ansible-builder create -v3 --output-file="Dockerfile" || error "Failed to create Dockerfile"
    
    # Build final image
    log "INFO" "Building final Docker image"
    docker build --tag="${EE_TAG}" "${CONTEXT_DIR}" || error "Failed to build final Docker image"
}

# Build function for Podman
build_podman() {
    # Run cleanup function
    cleanup

    log "INFO" "Building with Podman"
    # Build execution environment
    ansible-builder build -v3 -t "${BUILDER_TAG}" --container-runtime=podman || error "Failed to build Podman execution environment"
    
    # Generate Dockerfile
    log "INFO" "Generating Dockerfile for Podman build"
    ansible-builder create -v3 --output-file="Dockerfile" || error "Failed to create Dockerfile"
    
    # Build final image
    log "INFO" "Building final Podman image"
    podman build --tag="${EE_TAG}" "${CONTEXT_DIR}" || error "Failed to build final Podman image"
}

# Perform builds
if [ "${BUILD_BOTH}" = true ]; then
    log "INFO" "Building for both Docker and Podman"
    if command -v docker >/dev/null 2>&1; then
        build_docker
    fi
    if command -v podman >/dev/null 2>&1; then
        build_podman
    fi
else
    # Auto-detect and use available runtime
    if [ "${BUILD_PODMAN}" = true ]; then
        log "INFO" "Using Podman as container runtime"
        build_podman
    elif [ "${BUILD_DOCKER}" = true ]; then
        log "INFO" "Using Docker as container runtime"
        build_docker
    else
        log "INFO" "No container runtime specified, using Podman"
        build_podman
    fi
fi

log "INFO" "Build completed successfully"