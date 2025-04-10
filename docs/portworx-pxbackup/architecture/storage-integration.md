# Storage Integration in Portworx PXBackup

This document provides details on how Portworx PXBackup integrates with various storage systems for backup data.

## Table of Contents

1. [Supported Storage Types](#supported-storage-types)
2. [S3-Compatible Storage](#s3-compatible-storage)
3. [NFS Storage](#nfs-storage)
4. [Cloud Provider Storage](#cloud-provider-storage)
5. [Storage Considerations](#storage-considerations)
6. [Best Practices](#best-practices)

## Supported Storage Types

Portworx PXBackup supports various storage backends for storing backup data:

### Object Storage

- Amazon S3
- MinIO
- IBM Cloud Object Storage
- Google Cloud Storage
- Azure Blob Storage
- Any S3-compatible object store

### File Storage

- NFS shares
- Amazon EFS
- Azure File Share
- Google Cloud Filestore

## S3-Compatible Storage

S3-compatible storage is the most commonly used storage type for enterprise PXBackup deployments.

### Configuration

To configure S3-compatible storage, create a BackupLocation CustomResource:

```yaml
apiVersion: stork.libopenstorage.org/v1alpha1
kind: BackupLocation
metadata:
  name: s3-backup-location
  namespace: app-namespace
spec:
  location:
    type: s3
    path: "bucket-name"
    s3Config:
      region: us-east-1
      accessKeyID: ACCESS_KEY_ID
      secretAccessKey: SECRET_ACCESS_KEY
      endpoint: "https://s3.amazonaws.com"
      disableSSL: false
```

For security, it's recommended to use Kubernetes secrets for storing credentials:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: s3-credentials
  namespace: app-namespace
stringData:
  region: us-east-1
  accessKeyID: ACCESS_KEY_ID
  secretAccessKey: SECRET_ACCESS_KEY
  endpoint: "https://s3.amazonaws.com"
  disableSSL: "false"
---
apiVersion: stork.libopenstorage.org/v1alpha1
kind: BackupLocation
metadata:
  name: s3-backup-location
  namespace: app-namespace
spec:
  location:
    type: s3
    path: "bucket-name"
    secretConfig: s3-credentials
```

### Advanced S3 Features

#### Object Lock

S3 Object Lock provides write-once-read-many (WORM) protection. This is critical for ransomware protection and compliance requirements.

To configure Object Lock:

```yaml
apiVersion: stork.libopenstorage.org/v1alpha1
kind: BackupLocation
metadata:
  name: s3-backup-location-object-lock
  namespace: app-namespace
spec:
  location:
    type: s3
    path: "bucket-name"
    s3Config:
      region: us-east-1
      accessKeyID: ACCESS_KEY_ID
      secretAccessKey: SECRET_ACCESS_KEY
      endpoint: "https://s3.amazonaws.com"
      disableSSL: false
      objectLockConfig:
        mode: Compliance # or Governance
        retentionDays: 30
```

Note: The S3 bucket must be created with Object Lock enabled before use.

## NFS Storage

NFS storage provides an alternative to object storage with potentially lower latency for on-premises environments.

### Configuration

To configure NFS storage:

```yaml
apiVersion: stork.libopenstorage.org/v1alpha1
kind: BackupLocation
metadata:
  name: nfs-backup-location
  namespace: app-namespace
spec:
  location:
    type: nfs
    path: "backup-folder"
    nfsConfig:
      server: "nfs-server.example.com"
      path: "/export/backups"
```

### NFS Considerations

- Ensure proper file permissions on the NFS share
- Verify network connectivity between application clusters and NFS server
- Monitor available space on the NFS server
- Consider performance implications for large backup operations

## Cloud Provider Storage

Each cloud provider offers native storage solutions optimized for their platform.

### AWS

In AWS environments, use S3 with appropriate IAM roles and bucket policies. Consider:
- Cross-region replication for disaster recovery
- S3 lifecycle policies for cost optimization
- S3 object lock for compliance requirements

### Azure

In Azure environments, use:
- Azure Blob Storage (via S3-compatible API)
- Azure File Share (via NFS)

### Google Cloud

In GCP environments, use:
- Google Cloud Storage (via S3-compatible API)
- Google Cloud Filestore (via NFS)

## Storage Considerations

When selecting storage for enterprise PXBackup deployments, consider:

### Performance

- **Throughput**: Required data transfer rate for backup operations
- **Latency**: Impact of storage latency on backup windows
- **Concurrent Operations**: Ability to handle multiple concurrent backups

### Reliability

- **Redundancy**: Ensure storage has proper redundancy mechanisms
- **Durability**: Data durability guarantees (S3 offers 99.999999999% durability)
- **Availability**: Storage uptime SLAs

### Security

- **Encryption**: Data encryption at rest and in transit
- **Access Controls**: Proper IAM/RBAC configurations
- **Compliance**: Meeting regulatory requirements

### Cost

- **Storage Costs**: Base storage costs per GB/TB
- **Transaction Costs**: Costs for PUT/GET operations
- **Data Transfer**: Network egress costs
- **Retention Costs**: Long-term storage costs

## Best Practices

### Multi-Tier Storage Strategy

Implement a tiered approach to backup storage:

1. **Hot Tier**: Recent backups on high-performance storage
2. **Cold Tier**: Older backups on cost-effective storage
3. **Archive Tier**: Long-term retention backups on archive storage

### Backup Segregation

Separate backups by environment:

- Use distinct buckets/directories for production, staging, and development
- Implement different retention policies for each environment
- Consider different access controls for each environment

### Monitoring and Alerting

- Monitor storage capacity and usage trends
- Set alerts for approaching capacity thresholds
- Monitor backup success/failure rates
- Track storage costs and optimize as needed

### Disaster Recovery

- Implement cross-region replication for critical backups
- Test restore operations from backup locations regularly
- Document storage access procedures for disaster scenarios 