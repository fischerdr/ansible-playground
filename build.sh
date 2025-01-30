#!/bin/bash

# Define variables
BUILDER_TAG="quay.io/ansible/awx-ee"
EE_TAG="test-ee:latest"
BUILDX_NAME="test-ee"

# Build execution environment
ansible-builder build -v3 -t "${BUILDER_TAG}" --container-runtime=docker

# Build ee environment
docker buildx create --name "${BUILDX_NAME}"
docker buildx use "${BUILDX_NAME}"
ansible-builder create -v3 --output-file="Dockerfile"
docker buildx build --load --tag="${EE_TAG}" context