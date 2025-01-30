#!/bin/bash

# Define variables
PROJECT_DIR="$(pwd)"
CONTAINER_NAME="ansible-navigator"
SSH_DIR="${HOME}/.ssh"
KUBE_DIR="${HOME}/.kube"
CACHE_DIR="${PROJECT_DIR}/cache"
TMP_DIR="${PROJECT_DIR}/tmp"
LOGS_DIR="${PROJECT_DIR}/logs"

# Create required directories if they don't exist
for dir in "${CACHE_DIR}" "${TMP_DIR}" "${LOGS_DIR}"; do
    mkdir -p "${dir}"
done

# Function to check if directory exists
check_dir() {
    if [ ! -d "$1" ]; then
        echo "Warning: Directory $1 does not exist"
        return 1
    fi
    return 0
}

# Validate directories
check_dir "${PROJECT_DIR}" || exit 1
check_dir "${SSH_DIR}" || echo "Warning: SSH directory not found. SSH authentication might not work."
check_dir "${KUBE_DIR}" || echo "Warning: Kubeconfig directory not found. Kubernetes operations might fail."

# Build volume mount arguments
VOLUMES=(
    "-v ${PROJECT_DIR}:/runner/project:Z"
    "-v ${CACHE_DIR}:/runner/cache:Z"
    "-v ${TMP_DIR}:/runner/tmp:Z"
    "-v ${LOGS_DIR}:/runner/logs:Z"
)

# Add SSH directory mount if it exists
if [ -d "${SSH_DIR}" ]; then
    VOLUMES+=("-v ${SSH_DIR}:/home/runner/.ssh:Z")
fi

# Add Kubeconfig directory mount if it exists
if [ -d "${KUBE_DIR}" ]; then
    VOLUMES+=("-v ${KUBE_DIR}:/home/runner/.kube:Z")
fi

# Check for required configuration files
if [ ! -f "${PROJECT_DIR}/ansible-navigator.yml" ]; then
    echo "Error: ansible-navigator.yml not found in project directory"
    exit 1
fi

if [ ! -f "${PROJECT_DIR}/ansible.cfg" ]; then
    echo "Error: ansible.cfg not found in project directory"
    exit 1
fi

# Run the container
echo "Starting Ansible Navigator container..."
docker run \
    --rm \
    -it \
    --name "${CONTAINER_NAME}" \
    "${VOLUMES[@]}" \
    -e ANSIBLE_CONFIG=/runner/project/ansible.cfg \
    -e ANSIBLE_NAVIGATOR_CONFIG=/runner/project/ansible-navigator.yml \
    -e RUNNER_PROJECT_DIR=/runner/project \
    -e RUNNER_CACHE_DIR=/runner/cache \
    -e RUNNER_TEMP_DIR=/runner/tmp \
    -e RUNNER_LOGS_DIR=/runner/logs \
    -w /runner/project \
    quay.io/centos/centos:stream9 \
    /bin/bash -c "ansible-navigator run setup_cluster_pxbkup.yml \
        --eei quay.io/centos/centos:stream9 \
        --pp never \
        --mode interactive \
        --lf /runner/logs/ansible-navigator.log"
