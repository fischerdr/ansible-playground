# Portworx PXBackup Diagrams

This document contains diagrams illustrating Portworx PXBackup architecture, deployment models, workflows, and other key concepts.

## Table of Contents

1. [Architecture Diagrams](#architecture-diagrams)
2. [Deployment Models](#deployment-models)
3. [Backup Workflow Diagrams](#backup-workflow-diagrams)
4. [Multi-Datacenter Setup](#multi-datacenter-setup)
5. [Component Interaction](#component-interaction)
6. [Storage Integration](#storage-integration)

## Architecture Diagrams

### High-Level Architecture

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

### Component Architecture

```
+----------------------------------------+
|             PX-Backup Server           |
+----------------------------------------+
| +----------------+ +----------------+  |
| | Web UI/Console | | REST API       |  |
| +----------------+ +----------------+  |
| +----------------+ +----------------+  |
| | Backup Manager | | Scheduler      |  |
| +----------------+ +----------------+  |
| +----------------+ +----------------+  |
| | Cluster Manager| | Security/Auth  |  |
| +----------------+ +----------------+  |
+----------------------------------------+
              |
              v
+----------------------------------------+
|            Authentication               |
+----------------------------------------+
| +----------------+ +----------------+  |
| | Keycloak       | | External OIDC  |  |
| +----------------+ +----------------+  |
+----------------------------------------+
              |
              v
+----------------------------------------+
|             Datastore                   |
+----------------------------------------+
| +----------------+ +----------------+  |
| | MongoDB        | | Metadata Store |  |
| +----------------+ +----------------+  |
+----------------------------------------+
```

## Deployment Models

### Dedicated Management Model

```
+-----------------------+        +-----------------------+
|   Management Cluster  |        |  Application Cluster  |
|   (PXBackup)          |        |                       |
|                       |        |                       |
| +-------------------+ |        | +-------------------+ |
| | PX-Backup Server  | |<-------| | Stork             | |
| +-------------------+ |        | +-------------------+ |
|                       |        |                       |
| +-------------------+ |        | +-------------------+ |
| | Keycloak          | |        | | Applications      | |
| +-------------------+ |        | +-------------------+ |
|                       |        |                       |
| +-------------------+ |        | +-------------------+ |
| | MongoDB           | |        | | Portworx          | |
| +-------------------+ |        | +-------------------+ |
+-----------------------+        +-----------------------+
           |
           v
+-----------------------+
|   Storage             |
|                       |
| +-------------------+ |
| | S3/NFS Storage    | |
| +-------------------+ |
+-----------------------+
```

### Shared Model

```
+----------------------------------------------------+
|            Combined Cluster                        |
|                                                    |
| +-------------------+  +----------------------+    |
| | PX-Backup Server  |  | Applications         |    |
| +-------------------+  +----------------------+    |
|                                                    |
| +-------------------+  +----------------------+    |
| | Keycloak          |  | Stork                |    |
| +-------------------+  +----------------------+    |
|                                                    |
| +-------------------+  +----------------------+    |
| | MongoDB           |  | Portworx             |    |
| +-------------------+  +----------------------+    |
+----------------------------------------------------+
                    |
                    v
        +------------------------+
        |       Storage          |
        | +--------------------+ |
        | | S3/NFS Storage     | |
        | +--------------------+ |
        +------------------------+
```

### Multi-Region Model

```
+-------------------+            +-------------------+
| Region A          |            | Region B          |
| (Primary)         |            | (Secondary)       |
|                   |            |                   |
| +--------------+  |            | +--------------+  |
| | PX-Backup    |  |<---------->| | PX-Backup    |  |
| | Cluster      |  |    Sync    | | Cluster      |  |
| +--------------+  |            | +--------------+  |
|        |          |            |        |          |
|        v          |            |        v          |
| +--------------+  |            | +--------------+  |
| | App Clusters |  |            | | App Clusters |  |
| +--------------+  |            | +--------------+  |
|        |          |            |        |          |
|        v          |            |        v          |
| +--------------+  |            | +--------------+  |
| | Backup       |  |<---------->| | Backup       |  |
| | Storage      |  |    Repli-  | | Storage      |  |
| +--------------+  |    cation  | +--------------+  |
+-------------------+            +-------------------+
```

## Backup Workflow Diagrams

### Basic Backup Workflow

```
+-------------+    +-------------+    +-------------+
| User        | -> | PX-Backup   | -> | Stork       |
| Initiates   |    | Server      |    | on App      |
| Backup      |    | Processes   |    | Cluster     |
+-------------+    +-------------+    +-------------+
                                           |
                        +----------------->|
                        |                  v
+-------------+    +-------------+    +-------------+
| Backup      | <- | Data        | <- | Volume      |
| Location    |    | Transfer    |    | Snapshots   |
| Stores Data |    | to Storage  |    | Created     |
+-------------+    +-------------+    +-------------+
      |
      v
+-------------+    +-------------+    +-------------+
| Status      | -> | Metadata    | -> | User        |
| Updated     |    | Updated in  |    | Notified    |
|             |    | Datastore   |    |             |
+-------------+    +-------------+    +-------------+
```

### Detailed Backup Process

```
+--------------------------------------------------------+
|                      Backup Process                    |
+--------------------------------------------------------+
|                                                        |
|  1. User initiates backup (manual or scheduled)        |
|                |                                       |
|                v                                       |
|  2. PX-Backup validates request & permissions          |
|                |                                       |
|                v                                       |
|  3. PX-Backup creates ApplicationBackup CR             |
|                |                                       |
|                v                                       |
|  4. Stork detects CR and begins backup process         |
|                |                                       |
|                v                                       |
|  5. Pre-exec rules executed (application quiescing)    |
|                |                                       |
|                v                                       |
|  6. Resource definitions backed up                     |
|                |                                       |
|                v                                       |
|  7. Volume snapshots created                           |
|                |                                       |
|                v                                       |
|  8. Volume data exported to backup location            |
|                |                                       |
|                v                                       |
|  9. Post-exec rules executed (application unquiescing) |
|                |                                       |
|                v                                       |
| 10. Backup metadata stored                             |
|                |                                       |
|                v                                       |
| 11. Backup status updated                              |
|                                                        |
+--------------------------------------------------------+
```

## Multi-Datacenter Setup

### Cross-Datacenter Backup and Restore

```
+-------------------+            +-------------------+
| Datacenter A      |            | Datacenter B      |
|                   |            |                   |
| +-------------+   |            | +-------------+   |
| | PX-Backup   |   |<---------->| | Application |   |
| | Server      |   |    VPN/    | | Cluster     |   |
| +-------------+   |   Direct   | +-------------+   |
|       |           |    Link    |       |           |
|       |           |            |       |           |
|       v           |            |       v           |
| +-------------+   |            | +-------------+   |
| | Application |   |            | | Backup      |   |
| | Cluster     |   |            | | Location    |   |
| +-------------+   |            | +-------------+   |
|       |           |            |                   |
|       v           |            |                   |
| +-------------+   |            |                   |
| | Backup      |   |            |                   |
| | Location    |   |            |                   |
| +-------------+   |            |                   |
+-------------------+            +-------------------+
```

### Disaster Recovery Setup

```
+---------------------------------------------------------+
|                 Primary Site                            |
| +-------------------+     +---------------------+       |
| | PX-Backup Cluster |     | Application Cluster |       |
| +-------------------+     +---------------------+       |
|          |                           |                  |
|          |                           |                  |
|          v                           v                  |
|  +--------------------------------------------------+   |
|  |               Local Backup Storage               |   |
|  +--------------------------------------------------+   |
|                          |                              |
+--------------------------|------------------------------ +
                           | Cross-Region
                           | Replication
+---------------------------|------------------------------ +
|                          v                               |
|  +--------------------------------------------------+    |
|  |               DR Backup Storage                  |    |
|  +--------------------------------------------------+    |
|                   |                                      |
|                   |                                      |
|                   v                                      |
| +--------------------+     +----------------------+      |
| | DR PX-Backup       |     | DR Application       |      |
| | Cluster            |     | Cluster              |      |
| +--------------------+     +----------------------+      |
|                                                          |
|                 Disaster Recovery Site                   |
+----------------------------------------------------------+
```

## Component Interaction

### Authentication Flow

```
+-----------------+     +-----------------+     +-----------------+
| User            | --> | PX-Backup       | --> | Keycloak/OIDC   |
| Web Browser     |     | Web Interface   |     | Provider        |
+-----------------+     +-----------------+     +-----------------+
        ^                       |                      |
        |                       |                      |
        +------------------------+----------------------+
                              Token
                            Exchange
```

### Backup API Interaction

```
+----------------+     +----------------+     +----------------+
| External Tool  | --> | PX-Backup      | --> | Application    |
| or Script      |     | REST API       |     | Cluster API    |
+----------------+     +----------------+     +----------------+
                               |
                               v
                      +----------------+
                      | Backup         |
                      | Location       |
                      +----------------+
```

## Storage Integration

### S3 Storage Integration

```
+----------------+     +----------------+     +----------------+
| PX-Backup      | --> | S3 Compatible  | --> | Versioned      |
| Server         |     | API            |     | Bucket         |
+----------------+     +----------------+     +----------------+
        |                                           |
        |                                           |
        v                                           v
+----------------+                        +----------------+
| Backup         |                        | Object         |
| Metadata       |                        | Lock           |
| (MongoDB)      |                        | (Optional)     |
+----------------+                        +----------------+
```

### NFS Storage Integration

```
+----------------+     +----------------+     +----------------+
| PX-Backup      | --> | Stork          | --> | NFS Server     |
| Server         |     | Components     |     | /Share         |
+----------------+     +----------------+     +----------------+
        |                      |                     |
        |                      v                     |
        |              +----------------+            |
        |              | PVCs for       |            |
        |              | NFS Mounts     |            |
        |              +----------------+            |
        |                                            |
        v                                            v
+----------------+                         +----------------+
| Backup         |                         | File-based     |
| Metadata       |                         | Storage        |
| (MongoDB)      |                         |                |
+----------------+                         +----------------+
```

Note: These diagrams can be converted to more visual formats using tools like draw.io, Lucidchart, or Mermaid. For production documentation, consider rendering these ASCII diagrams into professional graphics. 