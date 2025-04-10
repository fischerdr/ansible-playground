# Portworx PXBackup Deployment Guide

This document provides guidance for deploying Portworx PXBackup in an enterprise environment. It covers prerequisites, installation methods, and post-installation configuration.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Enterprise Deployment Models](#enterprise-deployment-models)
3. [Installation Methods](#installation-methods)
4. [Deployment Procedure](#deployment-procedure)
5. [Multi-Datacenter Deployment](#multi-datacenter-deployment)
6. [Post-Installation Configuration](#post-installation-configuration)
7. [Deployment Validation](#deployment-validation)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying PXBackup, ensure the following prerequisites are met:

### Kubernetes Cluster Requirements

- Kubernetes version 1.19 or later
- Minimum 3 worker nodes for high availability
- Sufficient resources:
  - CPU: Minimum 4 cores per node
  - Memory: Minimum 8GB RAM per node
  - Storage: 50GB+ for PXBackup components

### Storage Requirements

- StorageClass for PXBackup persistent volumes
- External object storage (S3-compatible) or NFS for backup data
- Proper network access to storage endpoints

### Network Requirements

- Network connectivity between all Kubernetes clusters
- Access to external storage systems
- Proper DNS resolution for all components
- Firewall rules allowing necessary traffic

### Security Prerequisites

- TLS certificates for secure communication
- Service accounts with appropriate permissions
- OIDC provider configuration (optional)

### Required Tools

- Kubernetes CLI (kubectl)
- Helm 3.x
- Access to container registry

## Enterprise Deployment Models

PXBackup supports several deployment models for enterprise environments:

### Dedicated Management Model

- PXBackup deployed in a dedicated management cluster
- Application clusters connected to the management cluster
- Separation of concerns and improved security isolation
- Recommended for large enterprise deployments

### Shared Model

- PXBackup deployed in a shared cluster with applications
- Simpler architecture with fewer clusters to manage
- Suitable for smaller deployments or testing environments

### Multi-Region Model

- PXBackup deployed in multiple regions/data centers
- Cross-region backup and disaster recovery capabilities
- High availability across geographic locations
- Complex but provides maximum resilience

## Installation Methods

PXBackup can be installed using the following methods:

### Helm-based Installation (Recommended)

Helm provides the most flexible and maintainable installation method for enterprise environments:

```bash
# Add the Portworx Helm repository
helm repo add portworx https://raw.githubusercontent.com/portworx/helm/master/stable/
helm repo update

# Install PXBackup using Helm
helm install px-backup portworx/px-backup \
    --namespace px-backup \
    --create-namespace \
    --set persistentStorage.storageClassName=<your-storage-class> \
    --set storkRequired=true
```

## Deployment Procedure

The following provides a step-by-step deployment procedure for a multi-datacenter enterprise environment:

### 1. Plan Deployment Architecture

- Determine deployment model (dedicated vs. shared)
- Map out cluster architecture and connectivity
- Plan storage and network requirements
- Define backup policies and schedules

### 2. Prepare Infrastructure

- Set up Kubernetes clusters in each datacenter
- Configure storage classes and persistent volumes
- Set up network connectivity between clusters
- Configure RBAC and security policies

### 3. Prepare Backup Storage

- Set up S3-compatible storage or NFS shares
- Configure access policies and credentials
- Ensure network connectivity from clusters

### 4. Install PXBackup in Primary Datacenter

- Deploy PXBackup using Helm or operator
- Configure authentication (Keycloak or external OIDC)
- Set up initial admin accounts
- Verify basic functionality

### 5. Configure Multi-Datacenter Support

- Register application clusters from different datacenters
- Configure cross-datacenter backup locations
- Test connectivity and operations

### 6. Configure High Availability

- Ensure multiple replicas for PXBackup components
- Configure proper PDBs (Pod Disruption Budgets)
- Verify failover capabilities

## Multi-Datacenter Deployment

For enterprises with multiple datacenters, consider the following approach:

1. Deploy PXBackup in a primary datacenter
2. Register clusters from all datacenters with the central PXBackup
3. Configure backup locations in each datacenter
4. Implement cross-datacenter backup policies
5. Set up monitoring and alerts for all datacenters

### Network Considerations

- Ensure reliable VPN or direct connectivity between datacenters
- Implement proper network security between datacenters
- Monitor latency and bandwidth between locations

### Storage Considerations

- Use local backup locations for regular backups (lower latency)
- Use cross-datacenter backup locations for disaster recovery
- Consider bandwidth limitations for large backups

## Post-Installation Configuration

After installing PXBackup, complete the following configuration steps:

### Using the ansible pxbackup role deploy clusters

The PX-Backup Ansible role automates the deployment and configuration of Portworx PX-Backup in Kubernetes environments. Follow these steps to use the role:

1. **Create a playbook** (e.g., `pxbkup-setupcluster.yml`):

   ```yaml
   ---
   - name: Configure PX-Backup Clusters
     hosts: all
     gather_facts: false
   
     roles:
       - role: pxbackup
   ```

2. **Configure variables** in `extra_vars.json`:

   ```json
   {
     "px_backup_api_url": "https://pxbackup.example.com",
     "pxcentral_auth_url": "https://pxbackup.example.com/auth",
     "pxcentral_client_id": "px-backup-client",
     "pxcentral_username": "admin",
     "pxcentral_password": "{{ vault_pxcentral_password }}",
     "org_id": "default",
     
     "vault_token_path": "/run/secrets/vault-token",
     "vault_automation_prod_address": "https://vault-prod.example.com",
     "vault_automation_dev_address": "https://vault-dev.example.com",
     "vault_automation_default_namespace": "automation",
     "vault_automation_config_path": "kubernetes/",
     "vault_automation_config_mount_point": "secret"
   }
   ```

3. **Define clusters** in `extra_vars_clusters.json`:

   ```json
   {
     "clusters": [
       {
         "name": "user1-platform-p-usw2a-1",
         "description": "Production Cluster US West 2 Zone A",
         "cloud_type": "AWS",
         "px_config": {
           "storage_classes": ["portworx-db-sc", "portworx-file-sc"],
           "namespaces": ["prod-apps", "monitoring"]
         }
       }
     ]
   }
   ```

4. **Run the playbook**:

   ```bash
   ansible-playbook pxbkup-setupcluster.yml -e @extra_vars.json -e @extra_vars_clusters.json
   ```

5. **Optional: Configure backup schedules** in `extra_vars_bkupsched.json`:

   ```json
   {
     "backup_schedules": [
       {
         "name": "daily-backup",
         "backup_location": "s3-backup-location",
         "schedule_policy": "daily-retention-7",
         "namespaces": ["app-namespace", "database-namespace"]
       }
     ]
   }
   ```

6. **Optional: Run with backup schedules**:

   ```bash
   ansible-playbook pxbkup-setupcluster.yml -e @extra_vars.json -e @extra_vars_clusters.json -e @extra_vars_bkupsched.json
   ```

For more detailed information, refer to the [PX-Backup Role documentation](../../roles/pxbackup/README.md).

## Deployment Validation

After deployment, validate the installation using these checks:

### Component Verification

```bash
# Check PXBackup pods
kubectl get pods -n px-backup

# Verify services
kubectl get svc -n px-backup

# Check persistent volumes
kubectl get pvc -n px-backup
```

### Functional Validation

1. Register a test cluster
2. Create a test backup location
3. Perform a test backup of a non-critical namespace
4. Restore the test backup to verify functionality
5. Check logs for any errors or warnings

### Performance Testing

1. Test backup performance with different volume sizes
2. Measure backup and restore times
3. Verify impact on application performance during backup

## Troubleshooting

Common deployment issues and solutions:

### Installation Failures

- Check Helm/operator logs for errors
- Verify storage class exists and works
- Ensure sufficient resources are available

### Connectivity Issues

- Check network connectivity between components
- Verify DNS resolution works correctly
- Check firewall rules and security groups

### Authentication Problems

- Verify Keycloak configuration
- Check OIDC integration settings
- Review service account permissions

### Backup Failures

- Check Stork logs on application clusters
- Verify storage connectivity and permissions
- Check for application-specific issues

For more detailed troubleshooting, refer to the [Portworx documentation](https://docs.portworx.com/portworx-backup-on-prem/).
