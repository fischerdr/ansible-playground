#!/bin/bash

# Define variables
BUILDER_TAG="development-ee"
EE_TAG="development-ee:latest"
BUILDX_NAME="development-ee"

# Build execution environment
ansible-builder build -v3 -t "${BUILDER_TAG}" --container-runtime=docker

# Build ee environment
docker buildx create --name "${BUILDX_NAME}"
docker buildx use "${BUILDX_NAME}"
ansible-builder create -v3 --output-file="Dockerfile"
docker buildx build --load --tag="${EE_TAG}" context