# Portworx PXBackup Operations Guide

This document provides guidance for day-to-day operations of Portworx PXBackup in an enterprise environment, including backup strategies, management procedures, and best practices.

## Table of Contents

1. [Backup Strategies](#backup-strategies)
2. [User Management](#user-management)
3. [Cluster Management](#cluster-management)
4. [Backup Location Management](#backup-location-management)
5. [Schedule and Policy Management](#schedule-and-policy-management)
6. [Monitoring and Alerts](#monitoring-and-alerts)
7. [Maintenance Procedures](#maintenance-procedures)
8. [Disaster Recovery](#disaster-recovery)
9. [Performance Tuning](#performance-tuning)
10. [Security Operations](#security-operations)

## Backup Strategies

Effective backup strategies are essential for enterprise data protection. Consider the following approaches:

### Application-centric Backups

- Group related applications in the same namespace
- Use consistent labeling strategies for application components
- Create backup policies based on application requirements
- Apply pre/post-exec rules specific to applications

### Tiered Backup Approach

- **Tier 1 (Mission-Critical)**: Frequent backups, multiple backup locations, cross-region storage
- **Tier 2 (Business-Critical)**: Daily backups, local and remote storage
- **Tier 3 (Non-Critical)**: Weekly backups, local storage only

### Backup Frequency

Determine backup frequency based on:
- Recovery Point Objective (RPO) requirements
- Data change rate
- Storage capacity and costs
- Network bandwidth constraints

### Retention Policies

Implement retention policies to manage storage efficiently:
- Short-term retention (daily backups): 7-14 days
- Medium-term retention (weekly backups): 4-12 weeks
- Long-term retention (monthly backups): 6-12 months
- Compliance retention: Based on regulatory requirements

## User Management

PXBackup provides multi-tenancy and role-based access control:

### User Roles

- **Super Administrator**: Full control over all resources
- **Administrator**: Management of backups and resources
- **Operator**: Creation and management of backups
- **Viewer**: Read-only access to backups and resources

### Managing Users

```bash
# User and role management is performed through the PXBackup UI or API
# Integration with external OIDC providers is recommended for enterprise deployments
```

### Role Assignment

- Assign roles based on job responsibilities
- Follow the principle of least privilege
- Implement proper segregation of duties
- Regularly review and audit user permissions

## Cluster Management

Efficient management of registered clusters is crucial:

### Adding Clusters

```bash
# From the PXBackup UI:
# 1. Navigate to Clusters
# 2. Click "Add Cluster"
# 3. Provide cluster details and credentials

# Alternatively via API:
curl -X POST https://px-backup-api/clusters \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "production-cluster-1",
    "kubeconfig": "..."
  }'
```

### Cluster Health Monitoring

- Regularly check cluster connection status
- Monitor Stork components on application clusters
- Verify backup and restore capabilities
- Check for version compatibility issues

### Cluster Updates

- Plan updates during maintenance windows
- Update PXBackup before updating application clusters
- Test compatibility after updates
- Maintain consistent versions across multiple clusters

## Backup Location Management

Proper management of backup locations ensures data availability:

### Types of Backup Locations

- **S3-compatible storage**: AWS S3, MinIO, etc.
- **Cloud provider storage**: Azure Blob, Google Cloud Storage
- **NFS shares**: On-premises or cloud-based file shares

### Best Practices

- Create separate backup locations for different environments
- Use encryption for sensitive data
- Implement proper access controls on storage
- Regularly verify backup location accessibility
- Monitor storage capacity and usage

### Cross-Region Replication

For enterprise environments:
- Implement cross-region replication for critical data
- Configure backup policies to use multiple locations
- Test recovery from secondary locations

## Schedule and Policy Management

Effective scheduling and policy management ensures consistent backups:

### Schedule Types

- **Interval-based**: Backups at specific intervals (hourly, every 4 hours, etc.)
- **Daily**: Backups at specific times each day
- **Weekly**: Backups on specific days of the week
- **Monthly**: Backups on specific days of the month

### Creating Schedule Policies

```bash
# Example schedule policy in YAML format
apiVersion: stork.libopenstorage.org/v1alpha1
kind: SchedulePolicy
metadata:
  name: enterprise-policy
policy:
  interval:
    intervalMinutes: 240  # Every 4 hours
    retain: 6             # Keep last 6 interval backups
  daily:
    time: "01:00AM"       # 1 AM backup
    retain: 7             # Keep 7 daily backups
  weekly:
    day: "Sunday"         # Sunday backups
    time: "02:00AM"       # 2 AM backup
    retain: 4             # Keep 4 weekly backups
  monthly:
    date: 1               # 1st of month
    time: "03:00AM"       # 3 AM backup
    retain: 6             # Keep 6 monthly backups
```

### Policy Assignment

- Assign policies based on application requirements
- Consider RPO (Recovery Point Objective) needs
- Balance frequency with storage and performance impact
- Use labels to organize and filter backups

## Monitoring and Alerts

Comprehensive monitoring ensures backup reliability:

### Key Metrics to Monitor

- Backup success/failure rates
- Backup duration and size
- Storage utilization
- Component health status
- API response times

### Integration with Monitoring Systems

- Configure Prometheus for metrics collection
- Set up Grafana dashboards for visualization
- Integrate with enterprise monitoring solutions
- Implement log aggregation (ELK, Splunk, etc.)

### Alert Configuration

Set up alerts for:
- Failed backups
- Extended backup durations
- Storage capacity thresholds
- Component failures
- Authentication issues

## Maintenance Procedures

Regular maintenance ensures system reliability:

### Upgrade Procedures

```bash
# Using Helm for upgrades
helm upgrade px-backup portworx/px-backup \
  --namespace px-backup \
  --set imageVersion=<new-version> \
  --set persistentStorage.enabled=true \
  --set persistentStorage.storageClassName=<your-storage-class>
```

### Backup Cleanup

- Regularly review and clean up expired backups
- Check for orphaned backup data
- Validate retention policy effectiveness
- Monitor storage usage trends

### Audit and Compliance

- Maintain backup logs for compliance purposes
- Perform regular audits of backup completeness
- Document restore tests for critical applications
- Verify encryption and security controls

## Disaster Recovery

Plan for disaster recovery scenarios:

### Recovery Time Objectives (RTO)

- Document RTO requirements for critical applications
- Test restore procedures regularly
- Automate restore workflows where possible
- Train staff on recovery procedures

### Cross-Cluster Recovery

For full disaster recovery:
1. Deploy a new Kubernetes cluster
2. Install required components
3. Register with PXBackup
4. Restore applications and data
5. Verify application functionality

### Backup Server Recovery

If PXBackup itself needs recovery:
1. Deploy new PXBackup instance
2. Restore PXBackup datastore
3. Reconnect application clusters
4. Verify backup locations
5. Resume backup operations

## Performance Tuning

Optimize PXBackup performance for enterprise environments:

### Resource Allocation

- Adjust CPU and memory resources based on workload
- Scale MongoDB resources for large deployments
- Optimize Stork resources on application clusters

### Backup Window Management

- Schedule intensive backups during off-peak hours
- Stagger backup schedules across clusters
- Monitor impact on application performance
- Adjust pre/post-exec rules for efficient quiescing

### Volume Snapshot Optimization

- Use storage-efficient snapshots where available
- Leverage cloud provider snapshot capabilities
- Configure appropriate snapshot classes
- Monitor snapshot chain lengths

## Security Operations

Maintain security posture for backup operations:

### Authentication Management

- Regularly rotate service account credentials
- Audit user access and permissions
- Implement MFA for administrative access
- Review OIDC integration configurations

### Encryption Management

- Verify encryption of backups at rest
- Ensure secure transport for backup data
- Manage encryption keys securely
- Perform periodic security reviews

### Compliance Procedures

- Document backup and restore procedures
- Maintain audit logs for compliance purposes
- Implement retention based on regulatory requirements
- Perform regular security assessments

### Network Security

- Implement proper network policies
- Restrict access to backup storage
- Secure connections between clusters
- Regularly review firewall rules and access controls 