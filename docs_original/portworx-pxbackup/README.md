# Portworx PXBackup Enterprise Deployment Documentation

This documentation provides a comprehensive guide for deploying and managing Portworx PXBackup in an enterprise environment. It covers the architecture, deployment, operation, and troubleshooting aspects of PXBackup.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](architecture/README.md)
3. [Deployment](deployment/README.md)
4. [Operation](operation/README.md)
5. [Diagrams](diagrams/README.md)

## Overview

Portworx Backup (PX-Backup) is a Kubernetes backup solution that allows you to back up and restore applications, KubeVirt Virtual Machines (VMs), and their data across multiple clusters. PX-Backup provides a centralized management interface for data protection across your entire Kubernetes environment, supporting multiple clusters, cloud providers, and storage backends.

Key features of Portworx PXBackup include:

- **Multi-cluster management**: Centralized backup and restore operations across multiple Kubernetes clusters
- **Application-aware backups**: Ensures consistency of applications and their data
- **Multi-cloud support**: Works with major cloud providers (AWS, Azure, GCP) and on-premises deployments
- **Storage flexibility**: Supports various storage backends including S3-compatible object stores, NFS, and cloud-specific storage
- **Granular backup control**: Backup entire namespaces or specific applications using label selectors
- **Scheduling capabilities**: Define backup policies with retention settings
- **Pre/post-backup operations**: Support for execution rules before and after backups
- **Security and multi-tenancy**: Role-based access control and resource sharing
- **Monitoring and reporting**: Track backup and restore operations

This documentation is intended for IT administrators, platform engineers, and DevOps professionals responsible for implementing and managing data protection strategies in Kubernetes environments.

## Document Structure

The documentation is organized into the following sections:

1. **Architecture**: Details on PXBackup components, workflows, and integration points
2. **Deployment**: Step-by-step deployment guides for different environments
3. **Operation**: Day-to-day management, backup strategies, and operational procedures
4. **Diagrams**: Visual representations of architectures, workflows, and deployment models

Each section provides in-depth information relevant to enterprise deployments, with a focus on best practices and real-world scenarios. 