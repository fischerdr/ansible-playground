#!/bin/bash

# Add docker group with host's GID if provided
if [ ! -z "$DOCKER_GID" ]; then
    sudo groupadd -g "$DOCKER_GID" docker
    sudo usermod -aG docker runner
fi

# Execute the provided command or default to bash
if [ $# -gt 0 ]; then
    exec "$@"
else
    exec /bin/bash
fi
