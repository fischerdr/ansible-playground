#!/bin/bash

# Define variables
PROJECT_DIR="$(pwd)"
CACHE_DIR="${PROJECT_DIR}/cache"
TMP_DIR="${PROJECT_DIR}/tmp"
LOGS_DIR="${PROJECT_DIR}/logs"
DOCKER_GID=$(getent group docker | cut -d: -f3)
IMAGE_NAME="ansible-navigator-custom"
IMAGE_TAG="latest"

# Function to check if directory exists
check_dir() {
    if [ ! -d "$1" ]; then
        echo "Warning: Directory $1 does not exist"
        return 1
    fi
    return 0
}

# Function to check if Docker socket exists
check_docker_socket() {
    if [ ! -S "/var/run/docker.sock" ]; then
        echo "Error: Docker socket not found at /var/run/docker.sock"
        echo "Make sure Docker daemon is running"
        return 1
    fi
    return 0
}

# Function to build Docker image if needed
build_image() {
    if ! docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" >/dev/null 2>&1; then
        echo "Building Docker image ${IMAGE_NAME}:${IMAGE_TAG}..."
        docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .
    fi
}

# Create required directories if they don't exist
for dir in "${CACHE_DIR}" "${TMP_DIR}" "${LOGS_DIR}"; do
    mkdir -p "${dir}"
done

# Validate project directory and Docker socket
check_dir "${PROJECT_DIR}" || exit 1
check_docker_socket || exit 1

# Check for required configuration files
if [ ! -f "${PROJECT_DIR}/ansible-navigator.yml" ]; then
    echo "Error: ansible-navigator.yml not found in project directory"
    exit 1
fi

if [ ! -f "${PROJECT_DIR}/ansible.cfg" ]; then
    echo "Error: ansible.cfg not found in project directory"
    exit 1
fi

# Build or update the image
build_image

# Build volume mount arguments
VOLUMES=(
    "-v ${PROJECT_DIR}:/runner/project:Z"
    "-v ${CACHE_DIR}:/runner/cache:Z"
    "-v ${TMP_DIR}:/runner/tmp:Z"
    "-v ${LOGS_DIR}:/runner/logs:Z"
    "-v /var/run/docker.sock:/var/run/docker.sock"
)

# Add SSH directory mount if it exists
if [ -d "${HOME}/.ssh" ]; then
    VOLUMES+=("-v ${HOME}/.ssh:/home/runner/.ssh:Z")
fi

# Add Kubeconfig directory mount if it exists
if [ -d "${HOME}/.kube" ]; then
    VOLUMES+=("-v ${HOME}/.kube:/home/runner/.kube:Z")
fi

# Create setup script for container initialization
cat > "${TMP_DIR}/container-init.sh" << 'EOF'
#!/bin/bash

# Add docker group with host's GID
if [ ! -z "$DOCKER_GID" ]; then
    groupadd -g $DOCKER_GID docker
    usermod -aG docker runner
fi

# Install required packages
dnf install -y docker-ce-cli

# Execute the provided command or default to bash
if [ $# -gt 0 ]; then
    exec "$@"
else
    exec /bin/bash
fi
EOF

chmod +x "${TMP_DIR}/container-init.sh"

# Run the container
echo "Starting Docker container with ansible-navigator..."
docker run \
    --rm \
    -it \
    --name ansible-navigator \
    "${VOLUMES[@]}" \
    -e DOCKER_GID="${DOCKER_GID}" \
    -e ANSIBLE_CONFIG=/runner/project/ansible.cfg \
    -e ANSIBLE_NAVIGATOR_CONFIG=/runner/project/ansible-navigator.yml \
    -e RUNNER_PROJECT_DIR=/runner/project \
    -e RUNNER_CACHE_DIR=/runner/cache \
    -e RUNNER_TEMP_DIR=/runner/tmp \
    -e RUNNER_LOGS_DIR=/runner/logs \
    --group-add "${DOCKER_GID}" \
    -w /runner/project \
    "${IMAGE_NAME}:${IMAGE_TAG}" \
    /runner/tmp/container-init.sh \
    ansible-navigator run setup_cluster_pxbkup.yml \
    --eei "${IMAGE_NAME}:${IMAGE_TAG}" \
    --pp never \
    --mode interactive \
    --lf /runner/logs/ansible-navigator.log
