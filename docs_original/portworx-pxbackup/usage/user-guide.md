# PXBackup User Guide

This guide provides detailed instructions on how to use Portworx PXBackup for protecting and recovering your Kubernetes applications and data.

## Table of Contents

1. [Accessing the PXBackup Interface](#accessing-the-pxbackup-interface)
2. [Managing Clusters](#managing-clusters)
3. [Configuring Backup Locations](#configuring-backup-locations)
4. [Creating and Managing Backups](#creating-and-managing-backups)
5. [Setting Up Backup Schedules](#setting-up-backup-schedules)
6. [Performing Restores](#performing-restores)
7. [Managing Users and RBAC](#managing-users-and-rbac)
8. [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
9. [Enterprise Deployment Scenarios](#enterprise-deployment-scenarios)

## Accessing the PXBackup Interface

### Web UI Access

1. Open a web browser and navigate to the PXBackup Central URL:
   ```
   https://<pxbackup-central-url>
   ```

2. Log in with your credentials:
   - For local authentication: Enter your username and password
   - For OIDC authentication: Click the SSO button and follow your organization's authentication flow

3. Upon successful login, you'll see the PXBackup dashboard with summary information:
   - Registered clusters
   - Recent backup activities
   - Backup locations
   - Overall system health

### API Access

PXBackup provides a comprehensive REST API for automation:

1. Obtain an API token:
   ```bash
   curl -X POST \
     https://<pxbackup-central-url>/api/v1/auth/login \
     -H 'Content-Type: application/json' \
     -d '{"username": "your_username", "password": "your_password"}'
   ```

2. Store the returned token for subsequent API calls:
   ```bash
   export PX_TOKEN="your_token"
   ```

3. Include the token in the Authorization header for all API requests:
   ```bash
   curl -X GET \
     https://<pxbackup-central-url>/api/v1/clusters \
     -H "Authorization: Bearer $PX_TOKEN"
   ```

## Managing Clusters

### Registering a New Cluster

To register a new cluster for backup management:

1. Navigate to **Clusters > Register Cluster** in the PXBackup UI

2. Enter the cluster details:
   - **Cluster Name**: A descriptive name for the cluster
   - **Cluster Type**: Kubernetes (default)
   - **Kubeconfig**: Upload your kubeconfig file or paste the contents

3. Configure access permissions:
   - Select which user roles can access this cluster

4. Click **Register Cluster**

5. PXBackup will validate the connection and register the cluster

### Viewing Registered Clusters

1. Navigate to **Clusters** in the main menu

2. The cluster list shows:
   - Cluster names
   - Status (Online/Offline)
   - Number of applications backed up
   - Total number of backups
   - Storage utilization

3. Click on a cluster name to view detailed information:
   - Cluster resources (Namespace, PVCs, Applications)
   - Backup history
   - Restore points

### Removing a Cluster

1. Navigate to **Clusters** in the main menu

2. Find the cluster you want to remove and click the options menu (⋮)

3. Select **Delete Cluster**

4. Confirm the deletion in the prompt

   > **Note**: Removing a cluster does not delete existing backups for that cluster

## Configuring Backup Locations

### Adding Amazon S3 Storage

1. Navigate to **Settings > Backup Locations > Add Backup Location**

2. Select **Amazon S3** as the provider

3. Enter the following information:
   - **Location Name**: A descriptive name
   - **Access Key**: Your AWS access key
   - **Secret Key**: Your AWS secret key
   - **Region**: AWS region (e.g., us-east-1)
   - **Bucket Name**: S3 bucket name
   - **Endpoint** (optional): For S3-compatible storage

4. Click **Verify Connection** to test the configuration

5. Click **Add Location** to save

### Adding Azure Blob Storage

1. Navigate to **Settings > Backup Locations > Add Backup Location**

2. Select **Azure Blob Storage** as the provider

3. Enter the following information:
   - **Location Name**: A descriptive name
   - **Storage Account**: Azure storage account name
   - **Storage Key**: Azure storage access key
   - **Container Name**: Azure blob container name

4. Click **Verify Connection** to test the configuration

5. Click **Add Location** to save

### Adding Google Cloud Storage

1. Navigate to **Settings > Backup Locations > Add Backup Location**

2. Select **Google Cloud Storage** as the provider

3. Enter the following information:
   - **Location Name**: A descriptive name
   - **Project ID**: Your GCP project ID
   - **JSON Key**: Upload or paste your GCP service account key
   - **Bucket Name**: GCS bucket name

4. Click **Verify Connection** to test the configuration

5. Click **Add Location** to save

### Adding Cloudian S3 Storage

1. Navigate to **Settings > Backup Locations > Add Backup Location**

2. Select **S3 Compatible** as the provider

3. Enter the following information:
   - **Location Name**: A descriptive name (e.g., "DC1-Cloudian-S3")
   - **Access Key**: Your Cloudian S3 access key
   - **Secret Key**: Your Cloudian S3 secret key
   - **Region**: Region code (typically "us-east-1" for Cloudian)
   - **Bucket Name**: S3 bucket name
   - **Endpoint**: Your Cloudian S3 endpoint URL (e.g., "https://s3.dc1.yourdomain.com")
   - **Disable SSL Verification**: Leave unchecked unless using self-signed certificates

4. Click **Verify Connection** to test the configuration

5. Click **Add Location** to save

### Managing Backup Locations

1. Navigate to **Settings > Backup Locations**

2. From here you can:
   - Edit existing locations
   - Delete unused locations
   - View storage statistics
   - Check connection status

## Creating and Managing Backups

### Creating an Ad-hoc Backup

#### Backing Up a Namespace

1. Navigate to **Clusters > [Cluster Name] > Namespaces**

2. Find the namespace you want to back up and click the **Backup** button

3. Configure backup options:
   - **Backup Name**: Auto-generated, can be customized
   - **Backup Location**: Select from configured locations
   - **Pre/Post Execution Hooks**: Optional scripts to run before/after backup
   - **Include Resources**: Select resource types to include
   - **Exclude Resources**: Pattern-based exclusion for specific resources

4. Click **Start Backup**

5. Monitor the backup progress on the **Backups** screen

#### Backing Up Specific PVCs

1. Navigate to **Clusters > [Cluster Name] > PVCs**

2. Select the checkbox next to PVCs you want to back up

3. Click the **Backup Selected** button

4. Configure backup options as above

5. Click **Start Backup**

#### Backing Up an Application

1. Navigate to **Clusters > [Cluster Name] > Applications**

2. Find the application you want to back up and click the **Backup** button

3. Configure backup options as above

4. Click **Start Backup**

### Viewing Backup Details

1. Navigate to **Backups** in the main menu

2. Browse the list of backups with their status:
   - Completed
   - Failed
   - In Progress

3. Click on a backup to view details:
   - Resources included
   - Size and duration
   - Logs
   - Object storage location

### Deleting Backups

1. Navigate to **Backups** in the main menu

2. Select the checkbox next to backups you want to delete

3. Click the **Delete Selected** button

4. Confirm the deletion

   > **Note**: This will remove both the metadata and the actual backup data from storage

## Setting Up Backup Schedules

### Creating a Backup Schedule

1. Navigate to **Clusters > [Cluster Name]**

2. Select **Schedules > Create Schedule**

3. Configure schedule details:
   - **Schedule Name**: A descriptive name
   - **Resources to Back Up**: Select namespaces, PVCs, or applications
   - **Backup Location**: Select from configured locations
   - **Schedule**: Configure using cron expression or UI
     - **Simple**: Select frequency (hourly, daily, weekly)
     - **Advanced**: Enter custom cron expression
   - **Retention Policy**: Number of backups to retain
   - **Backup Options**: Same as ad-hoc backup options

4. Click **Create Schedule**

### Managing Backup Schedules

1. Navigate to **Schedules** in the main menu

2. View all configured schedules across clusters

3. Actions available:
   - **Edit**: Modify schedule configuration
   - **Pause/Resume**: Temporarily stop or restart schedule
   - **View History**: See past executions
   - **Delete**: Remove the schedule

### Schedule Execution History

1. Navigate to **Schedules > [Schedule Name] > History**

2. View details of each execution:
   - Execution time
   - Status
   - Duration
   - Backup size

## Performing Restores

### Restoring a Namespace

1. Navigate to **Backups** in the main menu

2. Find the backup containing the namespace you want to restore

3. Click the **Restore** button

4. Configure restore options:
   - **Restore Name**: Auto-generated, can be customized
   - **Target Cluster**: Select destination cluster (can be different from source)
   - **Target Namespace**: Keep original or specify a new namespace
   - **Resource Options**:
     - **Replace Existing Resources**: Overwrite if resources exist
     - **Skip Existing Resources**: Leave existing resources untouched
   - **PVC Options**:
     - **Reuse Volume**: Use existing volumes if available
     - **Create New Volume**: Always create new volumes
   - **Resource Filtering**: Include/exclude specific resources

5. Click **Start Restore**

6. Monitor the restore progress on the **Restores** screen

### Restoring Specific Resources

1. Navigate to **Backups > [Backup Name] > Resources**

2. Select the checkbox next to resources you want to restore

3. Click the **Restore Selected** button

4. Configure restore options as above

5. Click **Start Restore**

### Restoring to a Different Cluster

1. Follow the same restore process as above

2. In the restore options, select a different target cluster

3. Configure namespace mapping if needed

4. Complete the restore process

### Viewing Restore Details

1. Navigate to **Restores** in the main menu

2. Browse the list of restores with their status:
   - Completed
   - Failed
   - In Progress

3. Click on a restore to view details:
   - Resources restored
   - Duration
   - Logs
   - Any errors encountered

## Managing Users and RBAC

### User Management

1. Navigate to **Settings > Users** (available to administrators only)

2. View existing users:
   - Username
   - Role
   - Last login time

3. Actions available:
   - **Add User**: Create a new local user account
   - **Edit User**: Modify user details or role
   - **Delete User**: Remove a user
   - **Reset Password**: Force password reset

### Role-Based Access Control

1. Navigate to **Settings > Roles**

2. View existing roles:
   - Pre-defined roles (Admin, Operator, Viewer)
   - Custom roles

3. Creating a custom role:
   - Click **Create Role**
   - Assign permissions for each resource type:
     - View
     - Create/Edit
     - Delete
     - Execute (for backups and restores)
   - Specify cluster access restrictions
   - Specify namespace restrictions

4. Assigning roles to users:
   - Navigate to **Settings > Users**
   - Edit a user
   - Assign appropriate roles
   - Configure cluster-specific permissions if needed

## Monitoring and Troubleshooting

### Dashboard and Monitoring

1. The PXBackup dashboard provides an overview of:
   - Backup success rate
   - Storage utilization
   - Recent activity
   - System health

2. Navigate to **Reports** for detailed metrics:
   - Backup size trends
   - Backup duration statistics
   - Success/failure rates
   - Storage growth

### Alert Configuration

1. Navigate to **Settings > Alerts**

2. Configure alert conditions:
   - Backup failures
   - Storage capacity thresholds
   - System health issues

3. Configure notification methods:
   - Email
   - Slack
   - Webhook

### Viewing Logs

1. Navigate to **Settings > Logs**

2. Filter logs by:
   - Time range
   - Log level
   - Component
   - Operation type

3. Export logs for offline analysis

### Common Troubleshooting Steps

1. For backup failures:
   - Check the backup logs for specific errors
   - Verify storage location connectivity
   - Check cluster connectivity
   - Ensure sufficient permissions

2. For restore failures:
   - Verify target cluster has enough resources
   - Check for naming conflicts
   - Ensure storage location is accessible
   - Review restore logs for specific errors

3. For performance issues:
   - Check network bandwidth between components
   - Verify storage performance
   - Review resource allocation for PXBackup components 

## Enterprise Deployment Scenarios

### Cross-Datacenter OpenShift Deployment

This section covers configurations for large-scale cross-datacenter deployments on OpenShift with Cloudian S3 storage.

#### Architecture Overview

In this scenario:
- PXBackup instances are deployed in multiple datacenters
- Each instance backs up to local Cloudian S3 storage
- Cross-datacenter backups ensure disaster recovery
- OpenShift clusters host applications with large namespace counts

#### Configuring Cross-Datacenter Backup Locations

1. **Primary Datacenter Configuration**:
   - Configure local Cloudian S3 storage as described in [Adding Cloudian S3 Storage](#adding-cloudian-s3-storage)
   - Add remote datacenter's Cloudian S3 as a secondary backup location
   
2. **Secondary Datacenter Configuration**:
   - Configure local Cloudian S3 storage
   - Add primary datacenter's Cloudian S3 as a secondary backup location

3. **Cross-Datacenter Backup Strategy**:
   - For critical workloads: Configure backup schedules to both local and remote storage
   - For standard workloads: Use local storage with periodic replication to remote storage

#### Performance Tuning for Large Clusters

For OpenShift clusters with 1000+ namespaces:

1. **Resource Allocation**:
   
   Navigate to **Settings > System Configuration** and adjust resources:
   - API Server: Minimum 4 CPU cores, 8GB RAM
   - Database: Minimum 4 CPU cores, 8GB RAM, 100GB storage
   - Stork components: Minimum 2 CPU cores, 4GB RAM per cluster

2. **Database Optimization**:
   
   For MySQL database performance:
   - Increase connection pool size
   - Configure appropriate buffer sizes
   - Enable query caching
   - Implement regular database maintenance

3. **Backup Scheduling Strategies**:
   
   For large namespace counts:
   - Group namespaces into logical backup sets
   - Stagger backup schedules to distribute load
   - Use time windows during off-peak hours
   - Consider priority-based scheduling for critical vs. non-critical namespaces

   Example schedule grouping:
   - Group A: Namespaces 1-250 (Daily backups at 20:00)
   - Group B: Namespaces 251-500 (Daily backups at 22:00)
   - Group C: Namespaces 501-750 (Daily backups at 00:00)
   - Group D: Namespaces 751-1000 (Daily backups at 02:00)

4. **Network Considerations**:
   
   For cross-datacenter operations:
   - Ensure sufficient bandwidth between datacenters
   - Configure appropriate timeouts for operations
   - Implement network quality monitoring
   - Consider WAN optimizers for poor network conditions

5. **Storage Efficiency**:
   
   For managing large backup volumes:
   - Enable incremental backups
   - Configure appropriate compression settings
   - Implement tiered storage strategies in Cloudian
   - Define retention policies to manage storage growth

#### OpenShift-Specific Configurations

1. **Security Context Constraints**:
   
   PXBackup requires privileged access for volume operations:
   ```bash
   oc adm policy add-scc-to-user privileged -z px-backup -n px-backup-namespace
   ```

2. **Route Configuration**:
   
   Expose PXBackup UI through OpenShift routes:
   ```bash
   oc create route edge px-backup-ui --service=px-backup-ui --hostname=pxbackup.apps.your-openshift-domain.com
   ```

3. **Network Policies**:
   
   Configure appropriate NetworkPolicy objects to allow:
   - Communication between PXBackup components
   - Access to Cloudian S3 endpoints
   - Cross-datacenter communication for PXBackup instances

4. **Resource Quotas**:
   
   Set appropriate resource quotas for the PXBackup namespace:
   ```bash
   oc create -f px-backup-resource-quota.yaml
   ```

5. **Monitoring Integration**:
   
   Integrate with OpenShift monitoring:
   - Deploy ServiceMonitors for Prometheus integration
   - Configure Grafana dashboards for PXBackup metrics
   - Set up AlertManager rules for backup failures

#### Maintenance Considerations

1. **Backup Verification**:
   
   For large deployments, implement regular backup verification:
   - Schedule regular test restores to validate backup integrity
   - Automate validation of application functionality post-restore
   - Document verification procedures and results

2. **Capacity Planning**:
   
   Monitor and plan for growth:
   - Track backup size trends over time
   - Project storage needs based on data growth
   - Implement Cloudian bucket lifecycle policies
   - Regularly review and adjust retention policies

3. **Disaster Recovery Testing**:
   
   Validate cross-datacenter recovery:
   - Perform scheduled DR tests
   - Document recovery time objectives (RTO)
   - Optimize procedures to meet recovery goals
   - Test failover of PXBackup system itself 