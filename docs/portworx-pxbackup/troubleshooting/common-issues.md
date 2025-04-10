# PXBackup Troubleshooting Guide

This document provides troubleshooting steps for common issues encountered with Portworx PXBackup in enterprise environments.

## Table of Contents

1. [Diagnostic Tools](#diagnostic-tools)
2. [Backup Failures](#backup-failures)
3. [Restore Failures](#restore-failures)
4. [Authentication Issues](#authentication-issues)
5. [Performance Issues](#performance-issues)
6. [Storage Connectivity](#storage-connectivity)
7. [Cluster Registration Problems](#cluster-registration-problems)
8. [Collecting Logs for Support](#collecting-logs-for-support)

## Diagnostic Tools

Before troubleshooting specific issues, familiarize yourself with these essential diagnostic tools:

### 1. PXBackup UI Diagnostics

The PXBackup UI provides a diagnostics section that shows:
- Component health status
- Recent errors and warnings
- Resource utilization

### 2. Kubernetes Commands

```bash
# Check PXBackup pods status
kubectl get pods -n px-backup

# Check detailed pod information
kubectl describe pod <pod-name> -n px-backup

# Check PXBackup logs
kubectl logs -f <pod-name> -n px-backup

# Check Stork pods in application clusters
kubectl get pods -n kube-system | grep stork
```

### 3. Stork CLI Tools

```bash
# Check backup status
kubectl storkctl get backups -n <namespace>

# Check backup location status
kubectl storkctl get backuplocations -n <namespace>

# Get detailed backup information
kubectl storkctl describe backup <backup-name> -n <namespace>
```

## Backup Failures

### Issue: Backup Creation Fails

**Symptoms:**
- Backup status shows "Failed" in UI
- Error messages in Stork logs

**Troubleshooting Steps:**

1. **Check Stork Logs**:
   ```bash
   kubectl logs -f $(kubectl get pods -n kube-system -l name=stork -o jsonpath='{.items[0].metadata.name}') -n kube-system
   ```

2. **Verify Backup Location Configuration**:
   ```bash
   kubectl get backuplocation <backup-location-name> -n <namespace> -o yaml
   ```
   
   Ensure:
   - Credentials are correct
   - Bucket exists and is accessible
   - Proper permissions are set

3. **Check for CSI Snapshot Issues**:
   ```bash
   kubectl get volumesnapshots -n <namespace>
   kubectl describe volumesnapshot <snapshot-name> -n <namespace>
   ```

4. **Verify Storage Capacity**:
   - Ensure sufficient storage space in the backup location
   - Check for S3 bucket quotas or limitations

5. **Check Network Connectivity**:
   ```bash
   # From stork pod
   kubectl exec -it $(kubectl get pods -n kube-system -l name=stork -o jsonpath='{.items[0].metadata.name}') -n kube-system -- curl -v <s3-endpoint>
   ```

### Issue: Scheduled Backups Not Running

**Symptoms:**
- Backups don't appear at scheduled times
- Schedule shows as active but no backups created

**Troubleshooting Steps:**

1. **Verify Schedule Configuration**:
   ```bash
   kubectl get backupschedule <schedule-name> -n <namespace> -o yaml
   ```

2. **Check Stork CronJob Status**:
   ```bash
   kubectl get cronjobs -n kube-system | grep stork
   ```

3. **Check for Job History**:
   ```bash
   kubectl get jobs -n kube-system | grep backup
   ```

4. **Verify Stork Service Account Permissions**:
   ```bash
   kubectl auth can-i create backups --as=system:serviceaccount:kube-system:stork-account -n <namespace>
   ```

## Restore Failures

### Issue: Restore Operation Fails

**Symptoms:**
- Restore status shows "Failed" in UI
- Applications not properly restored
- Error messages in Stork logs

**Troubleshooting Steps:**

1. **Check Stork Logs During Restore**:
   ```bash
   kubectl logs -f $(kubectl get pods -n kube-system -l name=stork -o jsonpath='{.items[0].metadata.name}') -n kube-system
   ```

2. **Verify Backup Data Accessibility**:
   ```bash
   kubectl storkctl get restores <restore-name> -n <namespace>
   kubectl storkctl describe restore <restore-name> -n <namespace>
   ```

3. **Check Storage Class Availability**:
   ```bash
   kubectl get storageclass
   ```
   
   Ensure the target storage class exists and is working

4. **Examine PVCs After Restore**:
   ```bash
   kubectl get pvc -n <namespace>
   kubectl describe pvc <pvc-name> -n <namespace>
   ```

5. **Check Kubernetes Resource Constraints**:
   - Ensure namespace has adequate resource quotas
   - Verify cluster has available capacity

6. **For Cross-Cluster Restores**:
   - Confirm target cluster compatibility
   - Check if the Kubernetes version is compatible
   - Verify application dependencies are met

### Issue: Application Not Working After Restore

**Symptoms:**
- Backup restore completes successfully
- Application pods running but not functioning properly

**Troubleshooting Steps:**

1. **Check Application Logs**:
   ```bash
   kubectl logs -f <app-pod-name> -n <namespace>
   ```

2. **Verify Service Connections**:
   ```bash
   kubectl get services -n <namespace>
   kubectl describe service <service-name> -n <namespace>
   ```

3. **Check Data Accessibility Within Pods**:
   ```bash
   kubectl exec -it <app-pod-name> -n <namespace> -- ls -la /path/to/data
   ```

4. **Verify Application Configurations**:
   - Check ConfigMaps and Secrets were properly restored
   - Ensure environment variables are correct

5. **Check Network Policies**:
   ```bash
   kubectl get networkpolicies -n <namespace>
   ```

## Authentication Issues

### Issue: OIDC Authentication Failures

**Symptoms:**
- Unable to log in through OIDC
- Redirect loops during authentication
- "Unauthorized" errors after successful authentication

**Troubleshooting Steps:**

1. **Check PXBackup Authentication Logs**:
   ```bash
   kubectl logs -f $(kubectl get pods -n px-backup -l app=px-central-ui -o jsonpath='{.items[0].metadata.name}') -n px-backup
   ```

2. **Verify OIDC Configuration**:
   ```bash
   kubectl get secret px-backup-oidc -n px-backup -o yaml
   ```
   
   Check:
   - Client ID and secret are correct
   - Redirect URIs match the PXBackup URL
   - Scope includes required permissions

3. **Check Network Connectivity to IdP**:
   ```bash
   kubectl exec -it <px-backup-pod> -n px-backup -- curl -v <idp-endpoint>
   ```

4. **Verify Certificate Trust**:
   - Ensure IdP certificates are trusted
   - Check for certificate expiration

5. **Browser Issues**:
   - Clear browser cookies and cache
   - Try incognito/private browsing mode
   - Check browser console for errors

### Issue: API Token Authentication Issues

**Symptoms:**
- CLI or API calls fail with 401 errors
- Token expirations happening too quickly

**Troubleshooting Steps:**

1. **Regenerate API Token**:
   - Generate a new token from the UI
   - Verify token format is correct

2. **Check Token Permissions**:
   - Ensure token has appropriate RBAC permissions
   - Verify namespace access if applicable

3. **Check API Server Logs**:
   ```bash
   kubectl logs -f $(kubectl get pods -n px-backup -l app=pxcentral-apiserver -o jsonpath='{.items[0].metadata.name}') -n px-backup
   ```

## Performance Issues

### Issue: Slow Backup Operations

**Symptoms:**
- Backups take significantly longer than expected
- Timeouts during backup operations

**Troubleshooting Steps:**

1. **Check Resource Utilization**:
   ```bash
   kubectl top pods -n kube-system | grep stork
   kubectl top pods -n px-backup
   ```

2. **Verify Network Bandwidth**:
   - Check network metrics between cluster and backup location
   - Consider testing with bandwidth measurement tools

3. **Analyze Volume Size and Data Change Rate**:
   ```bash
   kubectl get pvc -n <namespace> -o custom-columns=NAME:.metadata.name,SIZE:.spec.resources.requests.storage
   ```

4. **Consider Backup Strategy Adjustments**:
   - Implement incremental backups for large volumes
   - Schedule backups during off-peak hours
   - Split large applications into multiple backup policies

5. **S3 Performance Optimization**:
   - Use regional endpoints closest to your cluster
   - Check S3 bucket throughput limits
   - Consider S3 performance tiers if available

### Issue: High Resource Consumption

**Symptoms:**
- Stork or PXBackup pods consuming excessive CPU/memory
- Cluster performance degradation during backups

**Troubleshooting Steps:**

1. **Monitor Resource Usage**:
   ```bash
   kubectl top pods -n kube-system | grep stork
   kubectl top pods -n px-backup
   ```

2. **Adjust Resource Limits**:
   ```yaml
   # Example Stork resource adjustment
   resources:
     limits:
       cpu: "2"
       memory: "4Gi"
     requests:
       cpu: "500m"
       memory: "1Gi"
   ```

3. **Check for Runaway Processes**:
   ```bash
   kubectl exec -it <stork-pod> -n kube-system -- ps aux | sort -nrk 3,3 | head -n 10
   ```

4. **Implement Backup Windows**:
   - Schedule backups during maintenance windows
   - Stagger backup schedules across applications

## Storage Connectivity

### Issue: S3 Connectivity Problems

**Symptoms:**
- "Access Denied" or "Connection Refused" errors
- Intermittent backup failures with storage errors

**Troubleshooting Steps:**

1. **Verify S3 Credentials**:
   ```bash
   kubectl get secret <s3-credential-secret> -n <namespace> -o yaml
   ```

2. **Check Network Path to S3**:
   ```bash
   kubectl exec -it <stork-pod> -n kube-system -- curl -v <s3-endpoint>
   ```

3. **Validate Bucket Permissions**:
   - Ensure IAM roles/users have appropriate permissions
   - Check bucket policy allows necessary operations

4. **Test with S3 CLI**:
   ```bash
   kubectl exec -it <stork-pod> -n kube-system -- aws s3 ls s3://<bucket-name> --endpoint-url <endpoint-url>
   ```

5. **Check for Endpoint Restrictions**:
   - Verify S3 endpoint is accessible from cluster network
   - Check for VPC endpoint configurations if applicable

### Issue: NFS Backup Location Issues

**Symptoms:**
- "Permission denied" when writing to NFS
- Timeouts during backup operations

**Troubleshooting Steps:**

1. **Check NFS Server Connectivity**:
   ```bash
   kubectl exec -it <stork-pod> -n kube-system -- ping <nfs-server>
   kubectl exec -it <stork-pod> -n kube-system -- showmount -e <nfs-server>
   ```

2. **Verify NFS Mount Options**:
   ```bash
   kubectl describe backuplocation <backup-location-name> -n <namespace>
   ```

3. **Test Manual Mounting**:
   ```bash
   kubectl exec -it <stork-pod> -n kube-system -- mount -t nfs <nfs-server>:<export-path> /mnt
   kubectl exec -it <stork-pod> -n kube-system -- touch /mnt/testfile
   ```

4. **Check NFS Server Configuration**:
   - Verify export permissions include cluster nodes
   - Check for NFS version compatibility

## Cluster Registration Problems

### Issue: Unable to Register Kubernetes Cluster

**Symptoms:**
- Cluster registration fails
- "Cluster unreachable" errors
- Authentication failures during registration

**Troubleshooting Steps:**

1. **Verify Cluster Kubeconfig**:
   - Ensure kubeconfig is valid and current
   - Check API server accessibility

2. **Check PXBackup Service Account Permissions**:
   ```bash
   kubectl get clusterrole px-backup-cluster-role -o yaml
   kubectl get clusterrolebinding px-backup-cluster-role-binding -o yaml
   ```

3. **Verify Network Connectivity**:
   - Ensure PXBackup can reach the Kubernetes API server
   - Check for any network policies blocking access

4. **Confirm API Server Certificate Trust**:
   - Ensure API server certificates are trusted
   - Check for certificate expiration

5. **Verify Cluster Meets Requirements**:
   - Check Kubernetes version compatibility
   - Ensure required CRDs are installed

### Issue: Cluster Shows as Disconnected

**Symptoms:**
- Previously working cluster shows as disconnected
- Unable to perform backups on the cluster

**Troubleshooting Steps:**

1. **Check Cluster Connection Status**:
   ```bash
   kubectl get pods -n px-backup | grep cluster-agent
   kubectl logs -f <cluster-agent-pod> -n px-backup
   ```

2. **Verify Kubernetes API Server Health**:
   ```bash
   kubectl get --raw=/healthz
   ```

3. **Check Network Changes**:
   - Verify no firewall rules were added blocking communication
   - Check for network infrastructure changes

4. **Reestablish Connection**:
   - Refresh cluster connection from UI
   - If needed, re-register the cluster

## Collecting Logs for Support

When seeking assistance from Portworx support, collect the following logs and information:

### 1. PXBackup Cluster Logs

```bash
# Create a support bundle
kubectl exec -it $(kubectl get pods -n px-backup -l app=px-backup -o jsonpath='{.items[0].metadata.name}') -n px-backup -- /opt/pwx/bin/pxbackup-support-bundle.sh

# Alternatively, collect individual component logs
mkdir -p pxbackup-logs
kubectl logs -n px-backup -l app=px-central-ui > pxbackup-logs/ui.log
kubectl logs -n px-backup -l app=px-backup > pxbackup-logs/backup.log
kubectl logs -n px-backup -l app=pxcentral-apiserver > pxbackup-logs/api.log
kubectl logs -n px-backup -l app=pxcentral-keycloak > pxbackup-logs/keycloak.log
```

### 2. Application Cluster Logs

```bash
# Stork logs
kubectl logs -n kube-system -l name=stork > stork-logs.log

# PX-Backup operator logs (if installed)
kubectl logs -n kube-system -l name=px-backup-operator > px-backup-operator-logs.log

# Get backup/restore resource details
kubectl get backups,restores,backuplocations,backupschedules -A -o yaml > backup-resources.yaml
```

### 3. Cluster Information

```bash
# Kubernetes version and node information
kubectl version > k8s-version.txt
kubectl get nodes -o wide > nodes-info.txt

# PXBackup version
kubectl exec -it $(kubectl get pods -n px-backup -l app=px-backup -o jsonpath='{.items[0].metadata.name}') -n px-backup -- pxbackupctl version > pxbackup-version.txt
```

### 4. Error Information

- Screenshot or copy of error messages from UI
- Timestamps when the issue occurred
- Description of actions that led to the error
- Any recent changes to the environment

Package all collected information into a compressed file for sharing with support:

```bash
tar -czvf pxbackup-support-bundle-$(date +%Y%m%d).tar.gz pxbackup-logs/ stork-logs.log px-backup-operator-logs.log backup-resources.yaml k8s-version.txt nodes-info.txt pxbackup-version.txt
``` 