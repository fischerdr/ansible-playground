# PXBackup Deployment Guide

This guide provides step-by-step instructions for deploying Portworx PXBackup in enterprise environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Planning](#architecture-planning)
3. [Installation Methods](#installation-methods)
4. [PXBackup Central Deployment](#pxbackup-central-deployment)
5. [Cluster Registration](#cluster-registration)
6. [Storage Configuration](#storage-configuration)
7. [Security Configuration](#security-configuration)
8. [High Availability Setup](#high-availability-setup)
9. [Validation and Testing](#validation-and-testing)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying PXBackup, ensure your environment meets the following requirements:

### Hardware Requirements

- **PXBackup Central Cluster**:
  - Minimum 4 CPU cores, 8GB RAM per node
  - Recommended: 8 CPU cores, 16GB RAM per node
  - Minimum 3 nodes for HA deployments
  - 100GB available storage for PXBackup components

- **Network Requirements**:
  - Network connectivity between PXBackup central cluster and all managed clusters
  - Outbound connectivity to object storage (S3, Azure Blob, etc.)
  - Recommended bandwidth: 1Gbps minimum, 10Gbps+ for production environments

### Software Requirements

- **Kubernetes Version**:
  - Minimum: Kubernetes 1.19
  - Recommended: Kubernetes 1.23+
  - Supported distributions: EKS, GKE, AKS, OpenShift 4.6+, and vanilla Kubernetes

- **Portworx Requirements**:
  - For source clusters: Portworx Enterprise 2.6+
  - Stork 2.6+ on all source clusters

- **Object Storage**:
  - S3-compatible storage (AWS S3, MinIO, etc.)
  - Azure Blob Storage
  - Google Cloud Storage
  - Or NFS storage for smaller deployments

### Ansible Requirements (For Post-Installation Operations)

If you plan to use Ansible for post-installation operations and configuration:

- Ansible 2.9+ installed on control node
- Python 3.6+ installed on control node
- `purepx.px_backup` Ansible collection installed:
  ```bash
  ansible-galaxy collection install purepx.px_backup
  ```
- Kubernetes Python client installed:
  ```bash
  pip install kubernetes
  ```

### Access Requirements

- Admin access to Kubernetes clusters
- Object storage credentials with read/write permissions
- Kubeconfig files for all clusters
- Ability to create Kubernetes resources (ClusterRole, ServiceAccount, etc.)

## Architecture Planning

### Deployment Models

1. **Standalone Deployment**:
   - Dedicated cluster for PXBackup central components
   - Separate from production workloads
   - Recommended for enterprise deployments

2. **Co-located Deployment**:
   - PXBackup installed on an existing cluster
   - Simpler but less isolated
   - Suitable for smaller environments or testing

### Sizing Guidelines

| Environment Size | Clusters | Volumes | Central Cluster Nodes | Resources per Node |
|------------------|----------|---------|----------------------|-------------------|
| Small            | 1-5      | <500    | 1-3                  | 4 CPU, 8GB RAM    |
| Medium           | 6-20     | 500-2000| 3-5                  | 8 CPU, 16GB RAM   |
| Large            | 21-50+   | 2000+   | 5+                   | 16 CPU, 32GB RAM  |

### Network Architecture

Plan network connectivity ensuring:
- PXBackup can reach the Kubernetes API of all managed clusters
- PXBackup can access object storage
- Application teams can access the PXBackup UI/API
- Consider network segmentation and security controls

## Installation Methods

### Official Helm Installation (Recommended)

The official method for installing PXBackup is using Helm, as documented in the [official Portworx documentation](https://docs.portworx.com/portworx-central-on-prem/install/px-backup).

1. First, ensure you have Portworx Central on-premises installed in your cluster.

2. Add the Portworx Enterprise Helm repository and update it:
   ```bash
   helm repo add portworx http://charts.portworx.io/ && helm repo update
   ```

3. Prepare a `values.yaml` file with your custom configuration settings.

4. Install PXBackup using Helm:
   ```bash
   helm install px-backup portworx/px-central --namespace px-backup -f values.yaml --set pxbackup.enabled=true
   ```

   For a basic installation without a custom values file:
   ```bash
   helm install px-backup portworx/px-central --namespace px-backup \
     --set pxbackup.enabled=true \
     --set oidc.enabled=true \
     --set oidc.clientID=<client-id> \
     --set oidc.clientSecret=<client-secret> \
     --set oidc.endpoint=<oidc-endpoint> \
     --set persistentStorage.enabled=true \
     --set persistentStorage.storageClassName=<storage-class-name>
   ```

This is the officially supported method by Portworx for installing PXBackup and ensures compatibility with future updates and support.

## PXBackup Central Deployment

### Step 1: Verify Deployment

After installing PXBackup using Helm, verify the deployment with:

```bash
kubectl get pods -n px-backup
```

Verify that all pods are in Running state:
```
NAME                                        READY   STATUS    RESTARTS   AGE
px-backup-px-central-apiserver-84b86c5c6c-wv8zj   1/1     Running   0          5m
px-backup-px-central-frontend-7685b86d9c-v6jfp    1/1     Running   0          5m
px-backup-px-central-keycloak-0                    1/1     Running   0          5m
px-backup-px-central-mysql-0                       1/1     Running   0          5m
px-backup-px-central-post-setup-job-xxxxx          0/1     Completed 0          5m
```

Check the services:
```bash
kubectl get svc -n px-backup
```

## Post-Installation Operations with Ansible

The [`purepx.px_backup` Ansible collection](https://github.com/portworx/px_backup_module) can be used for operations and configurations after PXBackup is installed. This collection provides modules to interact with the PXBackup REST API.

### Cluster Registration with Ansible

Example playbook for registering a cluster with PXBackup using Ansible:

```yaml
---
- name: Register clusters with PX-Backup
  hosts: localhost
  connection: local
  gather_facts: false
  collections:
    - purepx.px_backup
  
  vars:
    px_backup_host: "https://px-backup.example.com"
    px_backup_username: "admin"
    px_backup_password: "admin"
    cluster_name: "production-cluster"
    kubeconfig_file: "~/.kube/config"
    
  tasks:
    - name: Login to PX-Backup
      purepx.px_backup.login:
        host: "{{ px_backup_host }}"
        username: "{{ px_backup_username }}"
        password: "{{ px_backup_password }}"
      register: login_result
      
    - name: Register cluster with PX-Backup
      purepx.px_backup.cluster:
        host: "{{ px_backup_host }}"
        token: "{{ login_result.token }}"
        name: "{{ cluster_name }}"
        kubeconfig_file: "{{ kubeconfig_file }}"
        state: present
```

### Storage Configuration with Ansible

Example playbook for configuring backup storage locations using Ansible:

```yaml
---
- name: Configure backup locations for PX-Backup
  hosts: localhost
  connection: local
  gather_facts: false
  collections:
    - purepx.px_backup
  
  vars:
    px_backup_host: "https://px-backup.example.com"
    px_backup_username: "admin"
    px_backup_password: "admin"
    
  tasks:
    - name: Login to PX-Backup
      purepx.px_backup.login:
        host: "{{ px_backup_host }}"
        username: "{{ px_backup_username }}"
        password: "{{ px_backup_password }}"
      register: login_result
      
    - name: Create S3 backup location
      purepx.px_backup.backup_location:
        host: "{{ px_backup_host }}"
        token: "{{ login_result.token }}"
        name: "s3-backup-location"
        provider: "S3"
        bucket: "px-backups"
        region: "us-east-1"
        s3_endpoint: "s3.amazonaws.com"
        access_key: "your-access-key"
        secret_key: "your-secret-key"
        state: present
```

### Backup Operations with Ansible

Example playbook for creating a backup using Ansible:

```yaml
---
- name: Create backup with PX-Backup
  hosts: localhost
  connection: local
  gather_facts: false
  collections:
    - purepx.px_backup
  
  vars:
    px_backup_host: "https://px-backup.example.com"
    px_backup_username: "admin"
    px_backup_password: "admin"
    cluster_name: "production-cluster"
    backup_location: "s3-backup-location"
    
  tasks:
    - name: Login to PX-Backup
      purepx.px_backup.login:
        host: "{{ px_backup_host }}"
        username: "{{ px_backup_username }}"
        password: "{{ px_backup_password }}"
      register: login_result
      
    - name: Create backup of namespace
      purepx.px_backup.backup:
        host: "{{ px_backup_host }}"
        token: "{{ login_result.token }}"
        name: "production-backup"
        cluster_name: "{{ cluster_name }}"
        namespaces: 
          - "production"
        backup_location: "{{ backup_location }}"
        pre_exec_rule: ""
        post_exec_rule: ""
        state: present
```

### Restore Operations with Ansible

Example playbook for restoring from a backup using Ansible:

```yaml
---
- name: Restore from backup with PX-Backup
  hosts: localhost
  connection: local
  gather_facts: false
  collections:
    - purepx.px_backup
  
  vars:
    px_backup_host: "https://px-backup.example.com"
    px_backup_username: "admin"
    px_backup_password: "admin"
    cluster_name: "production-cluster"
    backup_name: "production-backup"
    
  tasks:
    - name: Login to PX-Backup
      purepx.px_backup.login:
        host: "{{ px_backup_host }}"
        username: "{{ px_backup_username }}"
        password: "{{ px_backup_password }}"
      register: login_result
      
    - name: Restore from backup
      purepx.px_backup.restore:
        host: "{{ px_backup_host }}"
        token: "{{ login_result.token }}"
        name: "production-restore"
        backup_name: "{{ backup_name }}"
        cluster_name: "{{ cluster_name }}"
        namespaces:
          - "production"
        state: present
```

## Security Configuration

### Configure TLS for PXBackup UI

To secure PXBackup UI with TLS:

1. Create TLS Secret:
   ```bash
   kubectl create secret tls px-backup-tls --cert=tls.crt --key=tls.key -n px-backup
   ```

2. Update the Ingress or Service to use the TLS certificate.

## High Availability Setup

For high availability, use the Helm chart with appropriate values:

```bash
helm install px-backup portworx/px-central --namespace px-backup \
  --set pxbackup.enabled=true \
  --set pxcentral.apiserver.replicaCount=3 \
  --set pxcentral.frontend.replicaCount=2 \
  --set pxcentral.keycloak.replicaCount=2 \
  --set mysql.replication.enabled=true \
  --set mysql.replication.replicas=2
```

## Validation and Testing

After deployment, validate the installation:

1. Access the PXBackup UI using the service details:
   ```bash
   kubectl get svc -n px-backup px-backup-ui
   ```

2. Register a test cluster through the UI or API.

3. Configure a backup location.

4. Perform a test backup and restore.

## Troubleshooting

For common installation issues and their solutions, see [Troubleshooting Guide](../troubleshooting/common-issues.md).

### Common Installation Issues

1. **PXBackup pods stuck in Pending state**
   - Check for PVC binding issues
   - Verify node resources (CPU/memory)
   - Check for pod scheduling constraints

2. **Authentication failures**
   - Verify OIDC configuration
   - Check Keycloak pods are running
   - Review authentication logs

3. **Cluster registration failures**
   - Verify kubeconfig is valid
   - Check network connectivity between clusters
   - Ensure RBAC permissions are correct

4. **Database connection issues**
   - Check MySQL pods are running
   - Verify database credentials
   - Check database persistent volume

### Installation Logs

Collect logs for troubleshooting:

```bash
# Get logs from PXBackup UI
kubectl logs -n px-backup -l app=px-central-ui

# Get logs from PXBackup API server
kubectl logs -n px-backup -l app=pxcentral-apiserver

# Get logs from Keycloak
kubectl logs -n px-backup -l app=pxcentral-keycloak

# Get logs from MySQL
kubectl logs -n px-backup -l app=px-central-mysql
``` 