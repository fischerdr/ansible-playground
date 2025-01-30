# Use CentOS Stream 9 as base image
FROM quay.io/centos/centos:stream9

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    PIP_NO_CACHE_DIR=1 \
    ANSIBLE_FORCE_COLOR=1 \
    PYCMD=python3.12

# Install system dependencies
RUN dnf -y update && \
    dnf -y install \
    epel-release \
    git-core \
    python3.12 \
    python3.12-devel \
    libcurl-devel \
    krb5-devel \
    krb5-workstation \
    subversion \
    git-lfs \
    sshpass \
    rsync \
    unzip \
    podman-remote \
    cmake \
    gcc \
    gcc-c++ \
    make \
    openssl-devel \
    docker-ce-cli \
    && dnf clean all \
    && rm -rf /var/cache/dnf

# Set up Python alternatives
RUN alternatives --install /usr/bin/python python /usr/bin/python3.12 312 && \
    alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 312

# Create runner user and required directories
RUN useradd -m -s /bin/bash runner && \
    mkdir -p /runner/{project,cache,tmp,logs} && \
    chown -R runner:runner /runner

# Install pip and upgrade
RUN $PYCMD -m ensurepip && \
    $PYCMD -m pip install --no-cache-dir -U pip setuptools wheel

# Copy requirements files
COPY requirements.txt requirements.yml /tmp/

# Install Python packages and Ansible collections
RUN $PYCMD -m pip install --no-cache-dir -r /tmp/requirements.txt && \
    ansible-galaxy collection install -r /tmp/requirements.yml && \
    rm -f /tmp/requirements.*

# Install additional tools
RUN git lfs install --system && \
    mkdir -p /var/run/receptor

# Set up working directory and user
WORKDIR /runner/project
USER runner

# Add entrypoint script
COPY --chown=runner:runner docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["ansible-navigator", "--help"]
