# Multi-Datacenter Deployment of PXBackup

This document provides detailed guidance for deploying Portworx PXBackup across multiple datacenters in an enterprise environment.

## Table of Contents

1. [Overview](#overview)
2. [Architecture Options](#architecture-options)
3. [Network Requirements](#network-requirements)
4. [Deployment Procedure](#deployment-procedure)
5. [Cross-Datacenter Backup Configuration](#cross-datacenter-backup-configuration)
6. [Monitoring and Operations](#monitoring-and-operations)
7. [Disaster Recovery Considerations](#disaster-recovery-considerations)

## Overview

Multi-datacenter deployments of PXBackup enable:

- Centralized management of backups across geographic locations
- Cross-datacenter disaster recovery
- Compliance with data residency requirements
- Improved backup reliability and availability

A typical enterprise deployment spans multiple datacenters, with PXBackup managing Kubernetes clusters across these locations.

## Architecture Options

### Centralized Management Model

In this model:
- PXBackup is deployed in a primary datacenter
- Application clusters in all datacenters connect to this central instance
- Backup storage can be local to each datacenter or centralized

**Advantages:**
- Simplified management through a single control plane
- Consistent policies across all locations
- Reduced operational overhead

**Disadvantages:**
- Single point of failure for management plane
- Dependency on cross-datacenter networking
- Potentially higher latency for remote clusters

### Distributed Management Model

In this model:
- PXBackup is deployed in each datacenter
- Each instance manages local application clusters
- Federation provides a global view across instances

**Advantages:**
- Higher availability during network partitions
- Lower latency for backup operations
- Compliance with strict data sovereignty requirements

**Disadvantages:**
- More complex to manage
- Potential for policy inconsistencies
- Higher resource requirements

### Hybrid Model (Recommended)

In this model:
- Primary PXBackup instance in main datacenter
- Secondary standby instances in other datacenters
- Synchronized configuration and metadata

**Advantages:**
- Balance of centralized management and resilience
- Failover capabilities during outages
- Optimized performance for local operations

**Disadvantages:**
- More complex initial setup
- Requires synchronization mechanisms

## Network Requirements

A multi-datacenter deployment has specific network requirements:

### Cross-Datacenter Connectivity

- Reliable, low-latency connections between datacenters
- Sufficient bandwidth for metadata transfer (minimum 10 Mbps)
- Ideally dedicated links or SD-WAN with QoS

### Security Requirements

- Encrypted VPN tunnels between datacenters
- Firewall rules to allow specific traffic:
  - PXBackup API (typically TCP 443)
  - Kubernetes API server ports (typically TCP 6443)
  - Metrics and monitoring ports
- Certificate-based authentication for cross-datacenter communication

### DNS Configuration

- Consistent DNS resolution across datacenters
- Consider Global Server Load Balancing (GSLB) for management interface
- Internal DNS entries for all cluster endpoints

## Deployment Procedure

### 1. Prepare Infrastructure

- Set up Kubernetes clusters in each datacenter
- Establish network connectivity between datacenters
- Configure storage in each datacenter

### 2. Deploy Primary PXBackup

```bash
# Deploy PXBackup in primary datacenter
helm install px-backup portworx/px-backup \
    --namespace px-backup \
    --create-namespace \
    --set oidc.centralOIDC.enabled=true \
    --set persistentStorage.enabled=true \
    --set persistentStorage.storageClassName=<primary-dc-storage-class> \
    --set storkRequired=true
```

### 3. Register Application Clusters

```bash
# Register clusters from all datacenters with primary PXBackup
# This can be done through the UI or API
```

### 4. Configure Backup Locations

Create backup locations in each datacenter:

```yaml
# Example for DC1
apiVersion: stork.libopenstorage.org/v1alpha1
kind: BackupLocation
metadata:
  name: dc1-s3-backup
  namespace: app-namespace
spec:
  location:
    type: s3
    path: "dc1-backup-bucket"
    s3Config:
      region: us-east-1
      accessKeyID: ACCESS_KEY_ID
      secretAccessKey: SECRET_ACCESS_KEY
      endpoint: "https://s3.dc1.example.com"
      disableSSL: false

# Example for DC2
apiVersion: stork.libopenstorage.org/v1alpha1
kind: BackupLocation
metadata:
  name: dc2-s3-backup
  namespace: app-namespace
spec:
  location:
    type: s3
    path: "dc2-backup-bucket"
    s3Config:
      region: eu-west-1
      accessKeyID: ACCESS_KEY_ID
      secretAccessKey: SECRET_ACCESS_KEY
      endpoint: "https://s3.dc2.example.com"
      disableSSL: false
```

### 5. Deploy Secondary PXBackup (Optional)

For high availability, deploy PXBackup in secondary datacenters:

```bash
# Deploy PXBackup in secondary datacenter
helm install px-backup portworx/px-backup \
    --namespace px-backup \
    --create-namespace \
    --set oidc.centralOIDC.enabled=true \
    --set persistentStorage.enabled=true \
    --set persistentStorage.storageClassName=<secondary-dc-storage-class> \
    --set storkRequired=true
```

Configure synchronization between instances (this typically requires custom tooling or manual procedures).

## Cross-Datacenter Backup Configuration

### Local Backup Strategy

For efficient operations, configure primary backups to use local storage:

```yaml
apiVersion: stork.libopenstorage.org/v1alpha1
kind: ApplicationBackup
metadata:
  name: app-backup-dc1-local
  namespace: app-namespace
spec:
  backupLocation: dc1-s3-backup  # Local to DC1
  namespaces:
  - app-namespace
  reclaimPolicy: Delete
  selectors:
    app: my-application
```

### Cross-Datacenter Backup Strategy

For disaster recovery, configure cross-datacenter backups:

```yaml
apiVersion: stork.libopenstorage.org/v1alpha1
kind: ApplicationBackup
metadata:
  name: app-backup-dc1-to-dc2
  namespace: app-namespace
spec:
  backupLocation: dc2-s3-backup  # Remote in DC2
  namespaces:
  - app-namespace
  reclaimPolicy: Delete
  selectors:
    app: my-application
```

### Scheduling Considerations

- Schedule frequent backups to local storage (hourly/daily)
- Schedule less frequent backups to remote storage (daily/weekly)
- Stagger backup schedules to avoid network contention
- Consider bandwidth limitations between datacenters

## Monitoring and Operations

### Unified Monitoring

- Deploy Prometheus and Grafana in each datacenter
- Configure federation for a global view
- Create dashboards for cross-datacenter metrics

### Health Checks

Implement regular health checks for:
- PXBackup components in each datacenter
- Network connectivity between datacenters
- Storage access and availability
- Backup success rates across locations

### Alerting Strategy

Configure alerts for:
- Failed backups in any datacenter
- Network connectivity issues
- Storage capacity thresholds
- Authentication/authorization failures

## Disaster Recovery Considerations

### Datacenter Failure Scenarios

Plan for different failure scenarios:
- **Management Datacenter Failure**: Procedures to activate secondary PXBackup
- **Application Datacenter Failure**: Restore procedures to alternate datacenter
- **Storage Datacenter Failure**: Procedures to access backup data from alternate locations

### Recovery Process

Document specific procedures for:
1. Assessing the failure scope
2. Activating secondary management if needed
3. Identifying available backup locations
4. Restoring to available infrastructure
5. Validating application functionality
6. Resuming normal backup operations

### Testing and Validation

- Conduct regular disaster recovery drills
- Test cross-datacenter restores quarterly
- Validate RTO (Recovery Time Objective) for critical applications
- Document results and improve procedures based on findings

### Documentation

Maintain comprehensive documentation for:
- Network topology between datacenters
- Storage configuration and access methods
- Authentication and authorization requirements
- Step-by-step recovery procedures for various scenarios 