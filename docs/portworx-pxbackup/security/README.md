# PXBackup Security Guide

This document outlines the security architecture, best practices, and considerations for securing Portworx PXBackup in enterprise environments.

## Table of Contents

1. [Overview](#overview)
2. [Security Architecture](#security-architecture)
3. [Authentication and Authorization](#authentication-and-authorization)
4. [Data Protection](#data-protection)
5. [Network Security](#network-security)
6. [Compliance and Auditing](#compliance-and-auditing)
7. [Security Hardening](#security-hardening)
8. [Incident Response](#incident-response)

## Overview

Security is a critical aspect of backup solutions, particularly for enterprise deployments managing sensitive data across multiple environments. PXBackup provides comprehensive security capabilities to protect:

- Backup data at rest and in transit
- Management APIs and interfaces
- Access to backup operations and resources
- Audit trails for compliance and forensics

This guide provides detailed information on implementing and maintaining security throughout your PXBackup deployment.

## Security Architecture

PXBackup employs a multi-layered security architecture:

```
┌─────────────────────────────────────────────────────┐
│                  Application Layer                  │
│  (UI, REST API, CLI with authentication controls)   │
├─────────────────────────────────────────────────────┤
│                  Authorization Layer                │
│  (RBAC, namespace isolation, policy enforcement)    │
├─────────────────────────────────────────────────────┤
│                  Transport Layer                    │
│  (TLS encryption, certificate management)           │
├─────────────────────────────────────────────────────┤
│                  Storage Layer                      │
│  (Encryption at rest, secure credentials)           │
├─────────────────────────────────────────────────────┤
│                  Infrastructure Layer               │
│  (Network policies, pod security, runtime security) │
└─────────────────────────────────────────────────────┘
```

Each layer implements specific controls to ensure defense in depth.

## Authentication and Authorization

### Identity Integration

PXBackup supports various authentication mechanisms:

1. **OIDC Integration**
   - Support for industry-standard OpenID Connect
   - Integration with enterprise identity providers:
     - Keycloak (built-in)
     - Active Directory/LDAP
     - Okta
     - Azure AD
     - Google Identity

2. **Configuration Example**

   ```yaml
   # Helm values configuration for OIDC
   oidc:
     centralOIDC:
       enabled: true
     externalOIDC:
       enabled: true
       clientID: "pxbackup-client"
       serverURL: "https://keycloak.example.com/auth/realms/master"
   ```

### Role-Based Access Control (RBAC)

PXBackup implements a robust RBAC model with predefined roles:

| Role | Capabilities |
|------|--------------|
| **Viewer** | Read-only access to backups and schedules |
| **Operator** | Create and manage backups and schedules |
| **Administrator** | Full access to all resources within assigned scopes |
| **Super Administrator** | Global access and configuration capabilities |

### Best Practices for RBAC

1. Implement least privilege principle:
   - Assign the minimum necessary privileges to users
   - Use namespace boundaries for multi-tenant environments
   - Regularly audit role assignments

2. Create custom roles for specialized workflows when needed
3. Separate duties for backup administration and restoration

## Data Protection

### Encryption at Rest

PXBackup ensures data is encrypted at rest:

1. **Backup Metadata Encryption**
   - MongoDB encryption using:
     - Storage-level encryption (cloud provider or local disk)
     - Application-level encryption

2. **Backup Data Encryption**
   - S3 server-side encryption (SSE-S3, SSE-KMS, SSE-C)
   - Object locking for immutability (ransomware protection)
   - Customer-managed encryption keys (CMEK)

3. **Configuration Example (AWS S3 with KMS)**

   ```yaml
   apiVersion: stork.libopenstorage.org/v1alpha1
   kind: BackupLocation
   metadata:
     name: encrypted-s3-backup
     namespace: app-namespace
   spec:
     location:
       type: s3
       path: "backup-bucket"
       s3Config:
         region: us-east-1
         accessKeyID: ACCESS_KEY_ID
         secretAccessKey: SECRET_ACCESS_KEY
         encryptionKey: "arn:aws:kms:us-east-1:account-id:key/key-id"
         disableSSL: false
   ```

### Encryption in Transit

All communications in PXBackup are secured:

1. **TLS Configuration**
   - Minimum TLS 1.2 requirement
   - Strong cipher suites
   - Certificate validation

2. **Certificate Management**
   - Integration with cert-manager
   - Support for custom CA certificates
   - Certificate rotation procedures

3. **Secure API Communications**
   - REST API secured with TLS
   - Authentication required for all endpoints
   - Token-based session management

## Network Security

### Network Segmentation

Best practices for network security:

1. **Kubernetes Network Policies**

   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: px-backup-api
     namespace: px-backup
   spec:
     podSelector:
       matchLabels:
         app: px-backup
     ingress:
     - from:
       - namespaceSelector:
           matchLabels:
             app: allowed-namespace
       ports:
       - protocol: TCP
         port: 443
   ```

2. **Service Mesh Integration**
   - Support for Istio, Linkerd, or other service meshes
   - mTLS between components
   - Traffic filtering and monitoring

### Egress Control

Secure outbound connections:

1. Limit egress to required endpoints only:
   - S3 or NFS endpoints for backup storage
   - Kubernetes API servers
   - Identity provider endpoints

2. Implement proxies for outbound traffic inspection

### API Security

Protect the PXBackup API:

1. Rate limiting to prevent DoS attacks
2. API request validation
3. Input sanitization
4. Secure error handling that doesn't leak sensitive information

## Compliance and Auditing

### Audit Logging

PXBackup generates comprehensive audit logs:

1. **Audit Events**
   - Authentication events
   - Authorization decisions
   - Backup and restore operations
   - Configuration changes
   - Administrative actions

2. **Log Aggregation**
   - Integration with Elasticsearch/Kibana
   - Splunk forwarding
   - Cloud provider logging services

3. **Log Protection**
   - Immutable logs
   - Offsite log archiving
   - Log integrity verification

### Compliance Controls

PXBackup helps meet regulatory requirements:

1. **Data Residency**
   - Configurable backup locations per region
   - Data locality enforcement

2. **Retention Policies**
   - Configurable retention periods
   - Automatic enforcement
   - Legal hold capability

3. **Immutability**
   - WORM (Write Once Read Many) storage compatibility
   - S3 Object Lock support
   - Immutable backup policies

## Security Hardening

### Secure Deployment

Harden your PXBackup installation:

1. **Pod Security**
   - Use Pod Security Standards (PSS) or Pod Security Policies (PSP)
   - Run containers as non-root
   - Read-only root filesystems

   ```yaml
   # Example PodSecurityContext
   securityContext:
     runAsNonRoot: true
     runAsUser: 1000
     fsGroup: 1000
     readOnlyRootFilesystem: true
   ```

2. **Resource Limitations**
   - Set appropriate CPU/memory limits
   - Implement Quality of Service (QoS)
   - Prevent resource exhaustion

3. **Secret Management**
   - Use Kubernetes secrets for credentials
   - Consider external secret management (Vault, AWS Secrets Manager, etc.)
   - Rotate credentials regularly

### Container Security

Secure container practices:

1. **Image Security**
   - Use only official PXBackup images
   - Implement image scanning in CI/CD
   - Enable image signature verification

2. **Runtime Security**
   - Deploy runtime security monitoring
   - Implement pod security contexts
   - Use admission controllers for policy enforcement

## Incident Response

### Security Monitoring

Monitor PXBackup for security events:

1. **Detection Capabilities**
   - Failed authentication attempts
   - Unauthorized access attempts
   - Unusual backup patterns
   - Configuration changes

2. **Integration with SIEM**
   - Forward security events to enterprise SIEM
   - Create custom detection rules
   - Establish alert thresholds

### Incident Response Plan

Prepare for security incidents:

1. **Response Procedures**
   - Document incident categorization
   - Define escalation paths
   - Establish containment procedures
   - Implement recovery processes

2. **Backup Recovery Testing**
   - Regularly test restoration procedures
   - Validate data integrity
   - Time recovery operations for RTOs

3. **Post-Incident Analysis**
   - Root cause analysis process
   - Documentation of lessons learned
   - Security control improvements

## Security Best Practices Checklist

Use this checklist to ensure your PXBackup deployment meets security requirements:

- [ ] Implemented OIDC integration with enterprise identity provider
- [ ] Configured appropriate RBAC roles for all users
- [ ] Enabled encryption for backups at rest
- [ ] Secured all network communications with TLS
- [ ] Implemented network policies for segmentation
- [ ] Configured comprehensive audit logging
- [ ] Hardened PXBackup pods with security contexts
- [ ] Established credential rotation procedures
- [ ] Tested backup and restore operations securely
- [ ] Documented incident response procedures 