#!/usr/bin/env bash

# Exit on error
set -e

# Define variables
BUILDER_TAG="development-ee"
EE_TAG="development-ee:latest"

# Log function for tracking progress
log() {
    local level="$1"
    local message="$2"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] ${message}"
}

# Error function
error() {
    local message="$1"
    log "ERROR" "${message}"
    exit 1
}

# Check if podman is installed
if ! command -v podman &> /dev/null; then
    error "podman is not installed"
fi

# Build execution environment
log "INFO" "Building execution environment with ansible-builder"
ansible-builder build -v3 -t "${BUILDER_TAG}" --container-runtime=podman || error "Failed to build execution environment"

# Generate Dockerfile
log "INFO" "Generating Dockerfile"
ansible-builder create -v3 --output-file="Dockerfile" || error "Failed to generate Dockerfile"

# Build the image
log "INFO" "Building final image"
podman build --tag="${EE_TAG}" context || error "Failed to build image"

log "INFO" "Build completed successfully" 