# PXBackup Troubleshooting Guide

This guide provides systematic approaches to diagnose and resolve common issues encountered while using Portworx PXBackup in enterprise environments.

## Table of Contents

1. [Diagnostic Tools and Resources](#diagnostic-tools-and-resources)
2. [Installation Issues](#installation-issues)
3. [Cluster Registration Problems](#cluster-registration-problems)
4. [Backup Failures](#backup-failures)
5. [Restore Failures](#restore-failures)
6. [Performance Issues](#performance-issues)
7. [Authentication and RBAC Issues](#authentication-and-rbac-issues)
8. [Database Issues](#database-issues)
9. [Storage Provider Problems](#storage-provider-problems)
10. [Common Error Messages](#common-error-messages)

## Diagnostic Tools and Resources

### Log Collection

PXBackup provides tools to collect logs from all components for troubleshooting:

```bash
# Collect PXBackup central logs
kubectl logs -n central-namespace deployment/pxcentral-onprem-api-server > pxcentral-api.log
kubectl logs -n central-namespace deployment/pxcentral-onprem-ui > pxcentral-ui.log
kubectl logs -n central-namespace deployment/pxcentral-onprem-keycloak > pxcentral-keycloak.log
kubectl logs -n central-namespace statefulset/pxcentral-onprem-mysql > pxcentral-mysql.log

# Collect Stork logs from target cluster
kubectl logs -n kube-system deployment/stork > stork.log
kubectl logs -n kube-system deployment/stork-scheduler > stork-scheduler.log
```

### Diagnostic Commands

Key commands for gathering system state:

```bash
# Check PXBackup component status
kubectl get pods -n central-namespace

# Check Stork component status on target cluster
kubectl get pods -n kube-system | grep stork

# View PXBackup CRD status
kubectl get backuplocations -A
kubectl get backupschedules -A
kubectl get volumebackups -A
kubectl get applicationbackups -A
kubectl get clusterbackups -A
```

### Health Check Endpoints

PXBackup provides health check endpoints for monitoring:

```bash
# API server health
curl -k https://<pxbackup-central-url>/api/v1/health

# Database connectivity check
curl -k https://<pxbackup-central-url>/api/v1/health/db

# Authentication service check
curl -k https://<pxbackup-central-url>/api/v1/health/auth
```

## Installation Issues

### PXBackup Central Fails to Install

**Symptoms**:
- Helm chart installation fails
- Operator doesn't deploy components
- Some or all pods are stuck in `Pending` or `CrashLoopBackOff` state

**Troubleshooting Steps**:

1. Check Kubernetes resource availability:
   ```bash
   kubectl describe nodes | grep -A 5 "Allocatable"
   ```

2. Verify namespace exists and has no restrictions:
   ```bash
   kubectl get namespace <namespace>
   kubectl get resourcequotas -n <namespace>
   ```

3. Check pod events for specific errors:
   ```bash
   kubectl describe pod <pod-name> -n <namespace>
   ```

4. Verify Helm values configuration:
   ```bash
   helm get values pxbackup -n <namespace>
   ```

5. For operator-based installation, check the operator logs:
   ```bash
   kubectl logs deployment/pxcentral-operator -n <namespace>
   ```

**Common Resolutions**:

- Insufficient resources: Increase cluster capacity or reduce resource requests in values.yaml
- Image pull issues: Check container registry access and authentication
- Storage class issues: Verify the specified storage class exists
  ```bash
  kubectl get storageclasses
  ```
- PV provisioning: Ensure dynamic provisioning is working or create PVs manually

### TLS Certificate Issues

**Symptoms**:
- Browser shows certificate warnings
- API calls fail with certificate errors
- Connections between components fail

**Troubleshooting Steps**:

1. Check the certificate details:
   ```bash
   kubectl get secret px-backup-tls -n <namespace> -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -text
   ```

2. Verify cert manager is working (if used):
   ```bash
   kubectl get certificates,certificaterequests,orders,challenges -n <namespace>
   ```

3. Check if the hostname matches the certificate:
   ```bash
   echo | openssl s_client -connect <pxbackup-hostname>:443 -servername <pxbackup-hostname> 2>/dev/null | openssl x509 -noout -subject
   ```

**Common Resolutions**:

- Regenerate certificates with correct hostname and SANs
- Configure proper ingress TLS settings
- For self-signed certificates, add CA to trusted roots
- Use Let's Encrypt or other trusted CA for production

## Cluster Registration Problems

### Failed to Register Cluster

**Symptoms**:
- Cluster registration fails in UI
- Registration API returns errors
- Cluster appears offline after registration

**Troubleshooting Steps**:

1. Verify kubeconfig is valid:
   ```bash
   export KUBECONFIG=<path-to-kubeconfig>
   kubectl get nodes
   ```

2. Check connectivity from PXBackup to target cluster:
   ```bash
   # Run from PXBackup central pod
   kubectl exec -it deploy/pxcentral-onprem-api-server -n <namespace> -- curl -k <target-cluster-api-endpoint>
   ```

3. Verify Stork is installed on target cluster:
   ```bash
   kubectl get pods -n kube-system | grep stork
   ```

4. Check Portworx is running (required for full functionality):
   ```bash
   kubectl get pods -n kube-system | grep portworx
   PX_POD=$(kubectl get pods -n kube-system -l name=portworx -o jsonpath='{.items[0].metadata.name}')
   kubectl exec -it $PX_POD -n kube-system -- /opt/pwx/bin/pxctl status
   ```

**Common Resolutions**:

- Install or update Stork on target cluster:
  ```bash
  kubectl apply -f https://install.portworx.com/stork?version=<version>
  ```
- Fix kubeconfig with correct context and credentials
- Ensure PXBackup central has network access to target cluster API server
- Update RBAC permissions to allow PXBackup to access target cluster resources

### Cluster Shows Offline Status

**Symptoms**:
- Registered cluster shows offline status
- Cannot initiate backups on the cluster
- Scheduled backups fail to start

**Troubleshooting Steps**:

1. Check connectivity from PXBackup to cluster:
   ```bash
   kubectl exec -it deploy/pxcentral-onprem-api-server -n <namespace> -- curl -k <target-cluster-api-endpoint>
   ```

2. Verify token/kubeconfig used for registration is still valid:
   ```bash
   # Get the stored credentials (secured in a secret)
   kubectl get secret cluster-<cluster-id>-creds -n <namespace> -o yaml
   ```

3. Check if API server endpoints changed (common in managed K8s services)

**Common Resolutions**:

- Update cluster credentials
- Re-register the cluster with current kubeconfig
- Check network policies or firewall rules that might be blocking connections
- Restart PXBackup API server pod:
  ```bash
  kubectl rollout restart deployment/pxcentral-onprem-api-server -n <namespace>
  ```

## Backup Failures

### Backup Gets Stuck in "In Progress" State

**Symptoms**:
- Backup shows "In Progress" for an extended period
- No progress in data transfer
- No completion or failure notification

**Troubleshooting Steps**:

1. Check the backup CRD status:
   ```bash
   kubectl get applicationbackup <backup-name> -n <namespace> -o yaml
   ```

2. Look for Stork logs:
   ```bash
   kubectl logs deployment/stork -n kube-system | grep <backup-name>
   ```

3. Check for any stuck PVC snapshots:
   ```bash
   kubectl get volumesnapshots -A
   ```

4. Verify Portworx status:
   ```bash
   PX_POD=$(kubectl get pods -n kube-system -l name=portworx -o jsonpath='{.items[0].metadata.name}')
   kubectl exec -it $PX_POD -n kube-system -- /opt/pwx/bin/pxctl volume list
   ```

**Common Resolutions**:

- Delete stuck backup and retry:
  ```bash
  kubectl delete applicationbackup <backup-name> -n <namespace>
  ```
- Check Portworx storage system is healthy:
  ```bash
  kubectl exec -it $PX_POD -n kube-system -- /opt/pwx/bin/pxctl status
  ```
- Verify object storage access from Stork
- Restart Stork pod if it appears unresponsive:
  ```bash
  kubectl rollout restart deployment/stork -n kube-system
  ```

### Backup Fails with Object Storage Errors

**Symptoms**:
- Backup fails shortly after starting
- Errors mention S3, Azure Blob, or GCS access issues
- "Access Denied" or "Bucket not found" errors

**Troubleshooting Steps**:

1. Verify credentials are correct:
   ```bash
   kubectl get secret <backup-location-secret> -n <namespace> -o yaml
   ```

2. Check storage bucket exists and is accessible:
   ```bash
   # For AWS S3
   aws s3 ls s3://<bucket-name> --profile <profile>
   
   # For Azure
   az storage blob list --container <container-name> --account-name <account-name>
   
   # For GCP
   gsutil ls gs://<bucket-name>
   ```

3. Check permissions on the bucket:
   ```bash
   # AWS IAM policy check
   aws iam get-policy --policy-arn <policy-arn>
   aws iam get-policy-version --policy-arn <policy-arn> --version-id <version-id>
   ```

**Common Resolutions**:

- Update incorrect storage credentials:
  ```bash
  kubectl edit secret <backup-location-secret> -n <namespace>
  ```
- Fix bucket permissions with appropriate IAM policies
- Create bucket if it doesn't exist
- Check for networking issues between Kubernetes clusters and object storage
- For S3, verify the region matches the bucket region

### Application-Consistent Backup Failures

**Symptoms**:
- Backup succeeds but application data is inconsistent
- Hook execution errors in logs
- Partial backup completions

**Troubleshooting Steps**:

1. Check if pre/post backup hooks are configured correctly:
   ```bash
   kubectl get applicationbackup <backup-name> -n <namespace> -o yaml | grep -A 10 hooks
   ```

2. Review hook logs in application pods:
   ```bash
   kubectl logs <application-pod> -n <namespace> | grep -i hook
   ```

3. Verify hook execution permissions:
   ```bash
   kubectl get rolebindings,clusterrolebindings -A | grep stork
   ```

**Common Resolutions**:

- Fix hook script errors
- Add appropriate database-specific quiesce commands
- Ensure hooks have adequate timeouts:
  ```bash
  kubectl edit applicationbackupschedule <schedule-name> -n <namespace>
  # Edit the hooks.timeout field
  ```
- Add error handling to hook scripts
- Test hooks manually before automated execution

## Restore Failures

### Restore Operation Fails to Start

**Symptoms**:
- Clicking restore button has no effect
- Restore API returns errors
- "Failed to create restore" message

**Troubleshooting Steps**:

1. Check if the target cluster is online:
   ```bash
   # From PXBackup central UI or API
   GET /api/v1/clusters/<cluster-id>/status
   ```

2. Verify backup data exists in object storage:
   ```bash
   # For AWS S3
   aws s3 ls s3://<bucket-name>/<backup-path> --recursive
   ```

3. Check permissions on target cluster:
   ```bash
   kubectl auth can-i create applicationrestore -n <namespace>
   ```

**Common Resolutions**:

- Ensure target cluster is registered and online
- Verify object storage is accessible
- Check RBAC permissions on target cluster
- Validate backup metadata is not corrupted
- Make sure target namespace exists or can be created

### Partial Resource Restoration

**Symptoms**:
- Some resources restore successfully, others fail
- PVCs restore but data is missing
- Application pods crash after restore

**Troubleshooting Steps**:

1. Check restore status for specific resource failures:
   ```bash
   kubectl get applicationrestore <restore-name> -n <namespace> -o yaml
   ```

2. Look for events related to restore:
   ```bash
   kubectl get events -n <namespace> | grep -i restore
   ```

3. Check for namespace-specific issues:
   ```bash
   kubectl describe namespace <target-namespace>
   ```

4. Verify PVC data integrity:
   ```bash
   kubectl exec -it <pod-with-pvc> -n <namespace> -- ls -la /mount/path
   ```

**Common Resolutions**:

- Fix namespace quota issues
- Modify restore options to skip existing resources if conflicts occur
- Ensure PVC storage classes exist in target cluster
- Check for any admission controllers blocking resource creation
- Delete conflicting resources before restore

### Cross-Cluster Restore Issues

**Symptoms**:
- Restore to different cluster fails
- Storage class incompatibilities
- Resource naming conflicts

**Troubleshooting Steps**:

1. Compare storage classes between source and target:
   ```bash
   # Source cluster
   kubectl get storageclass
   
   # Target cluster
   kubectl get storageclass
   ```

2. Check for namespace differences:
   ```bash
   kubectl get namespace
   ```

3. Verify cloud provider differences (if applicable):
   ```bash
   kubectl get nodes -o wide
   ```

**Common Resolutions**:

- Create equivalent storage classes on target cluster
- Use storage class mapping in restore options
- Specify a new target namespace to avoid conflicts
- Configure resource transformations for cross-cluster differences
- Set appropriate PVC resize options for cross-cloud restores

## Performance Issues

### Slow Backup Operations

**Symptoms**:
- Backups take much longer than expected
- Data transfer rate is slow
- High resource usage during backups

**Troubleshooting Steps**:

1. Check data volume size:
   ```bash
   kubectl get pvc -n <namespace> -o custom-columns=NAME:.metadata.name,SIZE:.spec.resources.requests.storage
   ```

2. Monitor network bandwidth:
   ```bash
   # On a node running Stork
   iftop -i <interface>
   ```

3. Check object storage performance:
   ```bash
   # For AWS S3
   aws s3 cp test-file s3://<bucket>/test-file --profile <profile>
   time aws s3 cp large-test-file s3://<bucket>/large-test-file --profile <profile>
   ```

4. Monitor CPU and memory for Stork and Portworx:
   ```bash
   kubectl top pods -n kube-system
   ```

**Common Resolutions**:

- Optimize network connectivity to object storage
- Configure parallel data transfers:
  ```yaml
  backupLocation:
    options:
      maxParallelUploads: 5
  ```
- Use incremental backups for large datasets
- Schedule backups during low-usage periods
- Use compression for backup data:
  ```yaml
  options:
    compression: true
  ```

### High Resource Usage

**Symptoms**:
- CPU/memory spikes during operations
- Node resource exhaustion
- Backup processes killed by OOM killer

**Troubleshooting Steps**:

1. Monitor resource usage:
   ```bash
   kubectl top pods -n <namespace>
   kubectl top nodes
   ```

2. Check container resource limits:
   ```bash
   kubectl get pods -n kube-system -o jsonpath='{.items[*].spec.containers[*].resources}' | grep stork
   ```

3. Look for OOM events:
   ```bash
   kubectl get events -n kube-system | grep -i "Out of memory"
   ```

**Common Resolutions**:

- Increase resource limits for PXBackup components:
  ```bash
  kubectl edit deployment stork -n kube-system
  # Adjust resources.limits values
  ```
- Optimize backup schedules to prevent concurrent operations
- Implement rate limiting for backup operations
- Scale underlying node pools if consistently hitting limits
- Use node selectors to place backup components on nodes with higher capacity

## Authentication and RBAC Issues

### Authentication Failures

**Symptoms**:
- Unable to log in to PXBackup UI
- API tokens are rejected
- "Invalid credentials" errors

**Troubleshooting Steps**:

1. Check Keycloak service status:
   ```bash
   kubectl get pods -n <namespace> | grep keycloak
   kubectl logs deployment/pxcentral-onprem-keycloak -n <namespace>
   ```

2. Verify user exists in the system:
   ```bash
   # Execute in Keycloak pod
   kubectl exec -it deployment/pxcentral-onprem-keycloak -n <namespace> -- \
     /opt/jboss/keycloak/bin/kcadm.sh get users -r pxcentral
   ```

3. Check for database connectivity issues:
   ```bash
   kubectl logs deployment/pxcentral-onprem-keycloak -n <namespace> | grep -i "database"
   ```

**Common Resolutions**:

- Reset user password using admin tools
- Restart Keycloak pod:
  ```bash
  kubectl rollout restart deployment/pxcentral-onprem-keycloak -n <namespace>
  ```
- Fix database connectivity issues
- For OIDC integration, verify configuration parameters
- Check for clock synchronization issues between components

### Permission Denied Errors

**Symptoms**:
- Users cannot access certain clusters or resources
- "Permission denied" or "Forbidden" errors
- Inconsistent access to functions

**Troubleshooting Steps**:

1. Check user role assignments:
   ```bash
   # API call to get user details
   GET /api/v1/users/<user-id>
   ```

2. Verify RBAC configurations:
   ```bash
   kubectl get roles,rolebindings -n <namespace>
   kubectl get clusterroles,clusterrolebindings | grep px
   ```

3. Check if resource-specific permissions are assigned correctly:
   ```bash
   # For cluster-specific access
   GET /api/v1/users/<user-id>/clusters
   ```

**Common Resolutions**:

- Assign appropriate roles to users
- Update RBAC policies for specific resources
- Check namespace restrictions for user roles
- Review audit logs for permission issues:
  ```bash
  kubectl logs deployment/pxcentral-onprem-api-server -n <namespace> | grep -i "forbidden"
  ```
- Re-sync RBAC settings if using external identity provider

## Database Issues

### MySQL Connection Problems

**Symptoms**:
- API server logs database connection errors
- Intermittent API failures
- "Database not available" errors

**Troubleshooting Steps**:

1. Check MySQL pod status:
   ```bash
   kubectl get pods -n <namespace> | grep mysql
   ```

2. Verify MySQL service is running:
   ```bash
   kubectl get svc -n <namespace> | grep mysql
   ```

3. Check database logs:
   ```bash
   kubectl logs statefulset/pxcentral-onprem-mysql -n <namespace>
   ```

4. Test database connection from API server:
   ```bash
   kubectl exec -it deployment/pxcentral-onprem-api-server -n <namespace> -- \
     curl http://pxcentral-onprem-mysql:3306 -v
   ```

**Common Resolutions**:

- Restart MySQL pod if unresponsive:
  ```bash
  kubectl rollout restart statefulset/pxcentral-onprem-mysql -n <namespace>
  ```
- Check MySQL persistent volume status:
  ```bash
  kubectl get pvc -n <namespace> | grep mysql
  ```
- Verify MySQL credentials are correct in API server configuration
- Increase connection timeouts for high-latency environments
- Check for MySQL resource constraints (CPU/memory)

### Database Backup and Recovery

If database corruption or data loss occurs:

1. Create a backup of the current database:
   ```bash
   kubectl exec -it statefulset/pxcentral-onprem-mysql -n <namespace> -- \
     mysqldump -u root -p<password> --all-databases > pxbackup-db-backup.sql
   ```

2. Restore from backup:
   ```bash
   cat pxbackup-db-backup.sql | kubectl exec -i statefulset/pxcentral-onprem-mysql -n <namespace> -- \
     mysql -u root -p<password>
   ```

3. If using PX-Backup to back up its own database:
   - Access the most recent backup
   - Restore using standard PX-Backup restore procedures
   - Target the central namespace and MySQL deployment

**Common Resolutions**:

- Implement regular MySQL backups in production
- Use MySQL replication for HA setups
- Configure periodic database exports to object storage
- Document database credentials securely for recovery scenarios

## Storage Provider Problems

### S3 Connectivity Issues

**Symptoms**:
- Backup fails with "Access Denied" or connection errors
- Slow uploads to S3
- Timeout errors

**Troubleshooting Steps**:

1. Verify S3 credentials:
   ```bash
   # Check secret containing credentials
   kubectl get secret <backup-location-secret> -n <namespace> -o yaml
   ```

2. Test S3 connectivity from within the cluster:
   ```bash
   kubectl run aws-test --image=amazon/aws-cli --rm -it -- \
     s3 ls s3://<bucket-name> --region <region>
   ```

3. Check network connectivity:
   ```bash
   kubectl run nettest --image=busybox --rm -it -- \
     ping s3.<region>.amazonaws.com
   ```

**Common Resolutions**:

- Update incorrect credentials
- Configure proper IAM roles and policies
- Create S3 VPC endpoints for private clusters
- Check for S3 bucket policies restricting access
- Verify S3 bucket region matches configuration

### Azure Blob Storage Issues

**Symptoms**:
- Connection errors to Azure
- Authentication failures
- Blob upload/download problems

**Troubleshooting Steps**:

1. Verify Azure credentials:
   ```bash
   kubectl get secret <backup-location-secret> -n <namespace> -o yaml
   ```

2. Test Azure connectivity:
   ```bash
   kubectl run az-test --image=mcr.microsoft.com/azure-cli --rm -it -- \
     storage blob list --account-name <account-name> --container <container> --account-key <key>
   ```

3. Check for network restrictions:
   ```bash
   # Check if Azure Storage firewall is enabled
   az storage account show --name <account-name> --query networkRuleSet
   ```

**Common Resolutions**:

- Update storage account keys
- Allow K8s cluster IPs in Azure Storage firewall
- Use Azure Private Link for secure connections
- Check container permissions and access level
- Verify Azure region proximity to K8s cluster

## Common Error Messages

### "Failed to create snapshot: Timed out waiting for snapshot"

**Cause**: Portworx was unable to create volume snapshots within the allocated time.

**Resolution**:
- Increase snapshot timeout:
  ```bash
  kubectl edit stork -n kube-system
  # Add or modify snapshotTimeout parameter
  ```
- Check Portworx health:
  ```bash
  PX_POD=$(kubectl get pods -n kube-system -l name=portworx -o jsonpath='{.items[0].metadata.name}')
  kubectl exec -it $PX_POD -n kube-system -- /opt/pwx/bin/pxctl status
  ```
- Verify storage system has capacity for snapshots

### "Object storage credentials not found"

**Cause**: The secret containing object storage credentials is missing or incorrect.

**Resolution**:
- Recreate backup location with correct credentials
- Verify secret exists:
  ```bash
  kubectl get secret -n <namespace> | grep backuplocation
  ```
- Check API server logs for more detailed error:
  ```bash
  kubectl logs deployment/pxcentral-onprem-api-server -n <namespace> | grep -i "credentials"
  ```

### "Error accessing Kubernetes cluster: forbidden"

**Cause**: PXBackup doesn't have sufficient permissions to access the target cluster.

**Resolution**:
- Update kubeconfig with proper RBAC permissions
- Create necessary ClusterRoles and ClusterRoleBindings:
  ```bash
  kubectl apply -f px-backup-cluster-roles.yaml
  ```
- For managed K8s, verify service account permissions
- Re-register cluster with administrator credentials

### "Database schema version mismatch"

**Cause**: PXBackup components are at different versions causing database incompatibility.

**Resolution**:
- Ensure all components are at the same version
- Follow proper upgrade procedures
- Check migration logs:
  ```bash
  kubectl logs deployment/pxcentral-onprem-api-server -n <namespace> | grep -i "migration"
  ```
- Restore database from backup if corruption occurred during upgrade

### "PVC restore failed: storage class not found"

**Cause**: Target cluster is missing the storage class referenced in the backup.

**Resolution**:
- Create equivalent storage class in target cluster:
  ```bash
  kubectl get storageclass <storage-class-name> -o yaml > sc.yaml
  # Edit as needed, then apply
  kubectl apply -f sc.yaml
  ```
- Use storage class mapping in restore options
- Choose "default storage class" option in restore settings 