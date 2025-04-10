# Portworx PXBackup Architecture

This document describes the architectural components, workflows, and integration points of Portworx PXBackup in an enterprise deployment.

## Table of Contents

1. [Components Overview](#components-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Details](#component-details)
4. [Backup Workflow](#backup-workflow)
5. [Integration Points](#integration-points)
6. [Security Architecture](#security-architecture)
7. [High Availability](#high-availability)

## Components Overview

Portworx Backup consists of several key components that work together to provide comprehensive backup and restore capabilities. The main components include:

- **Portworx Backup Server**: The central control plane built on gRPC framework for performance
- **REST APIs**: Provides programmatic access to backup operations
- **Portworx Central**: Web console for managing backups across clusters
- **Backup Cluster**: The Kubernetes cluster where PXBackup is deployed
- **Application Clusters**: Target Kubernetes clusters to be backed up and restored
- **Stork**: Cloud-native storage operator that bridges PXBackup and application clusters
- **Datastore**: MongoDB database storing backup metadata
- **Keycloak**: Identity and access management component
- **Object Storage**: S3-compatible storage (AWS S3, MinIO, etc.) or NFS for backup storage

## Architecture Diagram

The architecture follows a central management model where the PXBackup server is deployed in a dedicated Kubernetes cluster (or can share a cluster with applications). It connects to one or more application clusters via Stork components.

```
                 +---------------------+
                 |                     |
                 |  Portworx Central   |
                 |  (Web Console)      |
                 |                     |
                 +----------+----------+
                            |
                            v
+-----------------------------------------------------------+
|                                                           |
|                   Backup Cluster                          |
|                                                           |
|  +---------------+  +------------+  +---------------+     |
|  |               |  |            |  |               |     |
|  | PX-Backup     |  | Keycloak   |  | MongoDB       |     |
|  | Server        |  | (Auth)     |  | (Datastore)   |     |
|  |               |  |            |  |               |     |
|  +-------+-------+  +------------+  +---------------+     |
|          |                                                |
+----------|------------------------------------------------+
           |
   +-------+-------+
   |               |
   v               v
+------------------+    +------------------+
|                  |    |                  |
| Application      |    | Application      |
| Cluster 1        |    | Cluster 2        |
|                  |    |                  |
| +------------+   |    | +------------+   |
| | Stork      |   |    | | Stork      |   |
| +------------+   |    | +------------+   |
|                  |    |                  |
+-------+----------+    +-------+----------+
        |                       |
        v                       v
+----------------+     +----------------+
|                |     |                |
| Backup         |     | Backup         |
| Location       |     | Location       |
| (S3/NFS)       |     | (S3/NFS)       |
|                |     |                |
+----------------+     +----------------+
```

## Component Details

### Portworx Backup Server

The core of the PXBackup architecture, providing:
- CRUD operations for backup objects (backup location, clusters, schedules, etc.)
- Communication with Stork for application-level backups
- Monitoring of backup and restore operations

### REST APIs

PXBackup offers two primary APIs:
- **Backup API**: For creating, deleting, scheduling, and restoring backups
- **Backend API**: For user management, roles, and permissions

### Portworx Central

The web console that provides:
- User interface for all backup operations
- Cluster management and monitoring
- Scheduling and policy configuration
- Role-based access control

### Stork

Stork is a critical component that:
- Acts as a bridge between PXBackup and application clusters
- Handles storage operations for volume snapshots
- Manages backup and restore operations at the cluster level
- Creates and manages CRDs for backup operations

### Datastore

MongoDB database used for storing:
- Backup metadata
- User information and authentication data
- Configuration details
- Cluster information

### Keycloak

Provides identity and access management:
- User authentication and authorization
- Integration with external OIDC providers
- Token validation for API calls

### Cloud Storage / NFS Server

External storage systems that store the actual backup data:
- Amazon S3 or S3-compatible storage
- Azure Blob Storage
- Google Cloud Storage
- NFS file shares

## Backup Workflow

The backup workflow in PXBackup involves several stages:

1. **Initiation**: User creates a backup via UI or API
2. **Resource Selection**: PXBackup identifies resources to be backed up based on namespace/label selectors
3. **Pre-exec Rules**: Optional pre-backup operations are executed (e.g., database quiescing)
4. **Volume Snapshots**: For persistent volumes, snapshots are created
5. **Resource Backup**: Kubernetes resource definitions are backed up
6. **Data Export**: Volume data is exported to the backup location
7. **Metadata Storage**: Backup metadata is stored in the datastore
8. **Post-exec Rules**: Optional post-backup operations are executed
9. **Status Update**: Backup status is updated in the UI/API

## Integration Points

PXBackup integrates with various components in the enterprise environment:

- **Kubernetes API**: For resource management and operations
- **Cloud Provider APIs**: For cloud-specific storage operations
- **Identity Providers**: Via OIDC for authentication
- **Monitoring Systems**: For alerting and tracking
- **Storage Systems**: For backup storage

## Security Architecture

PXBackup security is built around several layers:

- **Authentication**: Via Keycloak or external OIDC providers
- **Authorization**: Role-based access control for backup resources
- **Encryption**: Data encrypted in transit and at rest
- **Network Isolation**: Proper network policies and security groups
- **Audit Logging**: Comprehensive logging of all operations

## High Availability

PXBackup is designed for high availability through:

- **MongoDB Replication**: 3-replica setup for the datastore
- **Backup Server Redundancy**: Multiple instances behind a service
- **Stork HA**: Deployed as DaemonSet on application clusters
- **Storage Redundancy**: Object storage with replication

In enterprise deployments, it's recommended to follow disaster recovery best practices:
- Deploy PXBackup in multiple regions/data centers
- Configure cross-region backup storage
- Implement regular testing of backup and restore procedures 