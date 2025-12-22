# Portworx Upgrade Role - Lab Testing Guide

This document provides comprehensive procedures and checklists for testing the Portworx upgrade role in a lab environment with a real Portworx cluster.

## Overview

Lab testing validates the role against a real OpenShift cluster with Portworx installed. This is the final validation step before production deployment.

### Testing Objectives

1. Verify all 8 phases execute correctly with real cluster
2. Validate monitoring and timeout logic with actual pod upgrades
3. Test preflight validation catches real configuration issues
4. Confirm final validation detects actual cluster health problems
5. Validate report generation with real data

### Prerequisites

Before beginning lab testing, ensure:

- Access to OpenShift 4.18+ cluster with Portworx installed
- Cluster admin permissions
- Ansible environment configured with required collections
- kubeconfig file for cluster access
- Version files prepared for target Portworx version

## Lab Environment Requirements

### Minimum Cluster Specifications

- **OpenShift Version:** 4.18 or higher
- **Portworx Nodes:** At least 6 nodes total
  - Minimum 3 storage nodes
  - Minimum 3 storageless nodes (for impatient mode testing)
- **Portworx Operator:** Installed and functional
- **Current Portworx Version:** Any version (will upgrade to target)
- **Storage:** Sufficient capacity for testing (not production cluster)

### Network Requirements

- Ansible control node can reach OpenShift API
- OpenShift cluster has internet access (for operator images)
- DNS resolution working for cluster endpoints

### Permissions Required

- Cluster admin role in OpenShift
- Access to portworx namespace
- Ability to patch StorageCluster resources
- Ability to approve InstallPlans

## Pre-Lab Setup

### 1. Prepare Version Files

Create version files for your target Portworx version:

```bash
# Set your target version
export PXVER=3.5.0
export KBVER=$(oc version -o json | jq -r '.openshiftVersion' | cut -d'.' -f1,2)

# Download versions file
curl -o versions-${PXVER} "https://install.portworx.com/$PXVER/version?kbver=$KBVER"

# Create version directory in role
mkdir -p roles/portworx_upgrade/files/versions/versions-${PXVER}
mv versions-${PXVER} roles/portworx_upgrade/files/versions/versions-${PXVER}/versions
```

### 2. Configure Ansible Environment

Ensure your Ansible environment is ready:

```bash
# Verify virtual environment
source .venv/bin/activate

# Install/update collections
.venv/bin/ansible-galaxy collection install -r requirements.yml

# Verify kubernetes.core collection version
.venv/bin/ansible-galaxy collection list | grep kubernetes.core
# Should show >= 2.3.0
```

### 3. Configure kubeconfig

Set up kubeconfig for cluster access:

```bash
# Test cluster connectivity
oc whoami
oc get nodes

# Verify portworx namespace
oc get pods -n portworx

# Check current Portworx version
oc exec -n portworx -c portworx $(oc get pods -n portworx -l name=portworx -o jsonpath='{.items[0].metadata.name}') -- /opt/pwx/bin/pxctl status | grep 'PX Version'
```

### 4. Create Test Inventory

Create a minimal inventory file for testing:

```ini
# inventory/lab_test.ini
[all:vars]
ansible_connection=local
portworx_target_version=3.5.0
portworx_namespace=portworx
portworx_cluster_name=lab-px-cluster
portworx_detailed_logging=true
portworx_work_dir=/tmp/px-upgrade-test
```

### 5. Verify Role Installation

Confirm role is properly installed:

```bash
# Check role structure
ls -la roles/portworx_upgrade/

# Verify main tasks file
cat roles/portworx_upgrade/tasks/main.yml

# Run syntax check
.venv/bin/ansible-playbook playbooks/px_upgrade.yml --syntax-check
```

## Testing Sequence (Option A: Without Impatient Mode)

This sequence tests the standard upgrade flow without pod acceleration.

### Test 1: Preflight Checks Only

**Purpose:** Validate preflight checks work with real cluster data

**Command:**
```bash
.venv/bin/ansible-playbook playbooks/px_upgrade.yml \
  --tags preflight \
  -e portworx_target_version=3.5.0 \
  -vv
```

**Expected Results:**
- Environment validation passes
- Node validation completes successfully
- Pod validation identifies all Portworx pods
- Cluster health check passes
- StorageCluster configuration validated
- Backup created (if portworx_backup_resources=true)

**Success Criteria:**
- No task failures
- All assertions pass
- Backup files created in work directory

**What to Check:**
- Number of nodes detected matches actual cluster
- Pod count matches expected (1 per node)
- Current version detected correctly
- UpdateStrategy is "RollingUpdate"

### Test 2: Validation Phase Only

**Purpose:** Test final validation modules with current cluster state

**Command:**
```bash
.venv/bin/ansible-playbook playbooks/px_upgrade.yml \
  --tags validate \
  -e portworx_target_version=$(oc exec -n portworx -c portworx $(oc get pods -n portworx -l name=portworx -o jsonpath='{.items[0].metadata.name}') -- /opt/pwx/bin/pxctl status | grep 'PX Version' | awk '{print $3}') \
  -vv
```

**Expected Results:**
- Storage pool health validated
- Volume health checked
- StorageCluster conditions analyzed
- Node statistics collected

**Success Criteria:**
- All validation modules execute
- No degraded pools or volumes detected
- All nodes online and on same version
- STC Available condition is True

**What to Check:**
- Validation summary shows correct counts
- No warnings about degraded resources
- Report generated successfully

### Test 3: Full Upgrade (Dry Run)

**Purpose:** Test complete upgrade flow in check mode

**Command:**
```bash
.venv/bin/ansible-playbook playbooks/px_upgrade.yml \
  -e portworx_target_version=3.5.0 \
  --check \
  -vv
```

**Expected Results:**
- All phases execute in check mode
- No actual changes made to cluster
- Workflow logic validated

**Success Criteria:**
- Playbook completes without errors
- Check mode reports what would be changed
- No actual cluster modifications

**What to Check:**
- Operator upgrade would be triggered
- ConfigMap would be updated
- StorageCluster would be patched

### Test 4: Full Upgrade (Real Execution)

**Purpose:** Execute actual Portworx upgrade

**WARNING:** This will upgrade your Portworx cluster. Ensure you have backups and approval.

**Command:**
```bash
.venv/bin/ansible-playbook playbooks/px_upgrade.yml \
  -e portworx_target_version=3.5.0 \
  -vv
```

**Expected Results:**
- Operator upgrades (if version changed)
- ConfigMap updated with target version
- Components patch applied
- StorageCluster image updated
- Automatic rolling upgrade monitored
- All pods upgraded to target version
- Final validation passes
- Reports generated

**Success Criteria:**
- Upgrade completes within expected time (20-90 minutes)
- All nodes reach target version
- No stuck upgrades detected
- Final validation shows healthy cluster

**What to Monitor:**
- Operator logs: `oc logs -n portworx -l name=portworx-operator --tail=50 -f`
- Pod status: `watch oc get pods -n portworx -l name=portworx`
- Upgrade progress in Ansible output

### Test 5: Tag-Based Selective Execution

**Purpose:** Validate tag-based phase selection

**Commands:**
```bash
# Operator upgrade only
.venv/bin/ansible-playbook playbooks/px_upgrade.yml --tags operator -e portworx_target_version=3.5.0

# Monitoring only (assumes upgrade already triggered)
.venv/bin/ansible-playbook playbooks/px_upgrade.yml --tags monitor -e portworx_target_version=3.5.0

# Validation and reporting only
.venv/bin/ansible-playbook playbooks/px_upgrade.yml --tags validate,report -e portworx_target_version=3.5.0
```

**Expected Results:**
- Only specified phases execute
- Other phases skipped
- Tags work as documented

**Success Criteria:**
- Task filtering works correctly
- No unexpected phase execution
- Results match tag selection

## Testing Sequence (Option B: With Impatient Mode)

This sequence tests the accelerated upgrade flow for storageless nodes.

### Prerequisites for Impatient Mode Testing

- Cluster must have at least 3 storageless nodes
- Storage nodes must upgrade successfully first
- Batch size configured appropriately (5-7 recommended)

### Test 6: Impatient Mode Enabled

**Purpose:** Test batch deletion acceleration for storageless nodes

**Command:**
```bash
.venv/bin/ansible-playbook playbooks/px_upgrade.yml \
  -e portworx_target_version=3.5.0 \
  -e portworx_impatient_mode=true \
  -e portworx_impatient_batch_size=5 \
  -vv
```

**Expected Results:**
- Storage nodes upgrade normally
- Storageless nodes accelerated in batches
- Safety checks between batches
- Faster overall upgrade time

**Success Criteria:**
- Impatient mode triggers after storage nodes complete
- Batches processed sequentially
- Safety validation between batches passes
- All storageless nodes reach target version

**What to Monitor:**
- Ansible output for "Executing impatient mode" messages
- Pod deletion events: `oc get events -n portworx --sort-by='.lastTimestamp' | grep Delete`
- Recovery time between batches
- Final pod status after each batch

**Safety Validations to Watch:**
- Storage nodes validated before acceleration
- Batch size limits enforced (5-7 pods)
- Stuck detection still active
- Operator not recreated unnecessarily

### Test 7: Impatient Mode Edge Cases

**Purpose:** Test impatient mode safety mechanisms

**Test Scenarios:**

**A. Small Cluster (fewer than 5 storageless nodes):**
```bash
# Should work with small batches
.venv/bin/ansible-playbook playbooks/px_upgrade.yml \
  -e portworx_impatient_mode=true \
  -e portworx_impatient_batch_size=3 \
  -e portworx_target_version=3.5.0
```

**B. Mixed upgrade states:**
- Manually upgrade some nodes first
- Run with impatient mode
- Should only accelerate remaining nodes

## Monitoring Checklist

### Console Output to Watch

During upgrade execution, monitor for:

- [ ] Preflight validation messages (all green)
- [ ] Operator version change detection
- [ ] ConfigMap update confirmation
- [ ] Component patch application
- [ ] StorageCluster image update
- [ ] Initial pod count and versions
- [ ] Activity messages (Terminating, Pending, ContainerCreating, Running)
- [ ] Completion count increasing
- [ ] Timeout warnings (should not appear in healthy upgrade)
- [ ] Impatient mode trigger (if enabled)
- [ ] Batch processing messages (if impatient mode)
- [ ] Final validation results
- [ ] Report generation confirmation

### Kubernetes Cluster Monitoring

In separate terminal windows, watch:

**Terminal 1 - Pod Status:**
```bash
watch -n 5 'oc get pods -n portworx -l name=portworx -o wide'
```

**Terminal 2 - Events:**
```bash
oc get events -n portworx --watch --sort-by='.lastTimestamp'
```

**Terminal 3 - Operator Logs:**
```bash
oc logs -n portworx -l name=portworx-operator --tail=100 -f
```

**Terminal 4 - pxctl Status:**
```bash
watch -n 10 'oc exec -n portworx -c portworx $(oc get pods -n portworx -l name=portworx -o jsonpath="{.items[0].metadata.name}") -- /opt/pwx/bin/pxctl status'
```

### Generated Reports Review

After upgrade, review generated reports:

```bash
# List reports
ls -lh /tmp/px-upgrade-test/

# View summary report
cat /tmp/px-upgrade-test/px-upgrade-summary-*.txt

# View JSON report (if enabled)
cat /tmp/px-upgrade-test/px-upgrade-validation-*.json | jq .
```

**Check Report Contents:**
- [ ] Cluster information correct
- [ ] Timing data present
- [ ] Pod counts accurate
- [ ] Version information correct
- [ ] Validation results included
- [ ] Storage pool statistics
- [ ] Volume health summary
- [ ] Node statistics

## Expected Behaviors

### Normal Upgrade Flow (Without Impatient Mode)

**Timeline:** 20-90 minutes depending on cluster size

1. **Preflight Phase** (2-5 minutes)
   - Environment validation
   - Resource backup
   - Cluster health checks

2. **Operator Upgrade** (5-10 minutes if needed)
   - Subscription update
   - InstallPlan approval
   - Operator pod restart

3. **Trigger Phase** (1-2 minutes)
   - ConfigMap update
   - Component patch
   - StorageCluster image update

4. **Monitoring Phase** (10-70 minutes)
   - One pod at a time (operator-controlled)
   - 5-10 minutes per pod typical
   - Activity detected continuously
   - No timeout warnings

5. **Validation Phase** (2-5 minutes)
   - Storage pool health check
   - Volume health verification
   - STC conditions analysis
   - Node statistics collection

6. **Reporting Phase** (< 1 minute)
   - Summary generation
   - JSON report (if enabled)
   - File output

### With Impatient Mode (Faster for Storageless)

**Timeline:** 15-40 minutes depending on cluster composition

1. **Phases 1-4:** Same as normal flow

2. **Monitoring Phase** (modified)
   - Storage nodes upgrade normally (5-10 min each)
   - After storage nodes complete: Impatient mode triggers
   - Storageless nodes in batches (5-7 pods)
   - Batch recovery time: ~15 minutes per batch
   - Multiple batches if many storageless nodes

3. **Phases 6-7:** Same as normal flow

### Phase Transitions

Watch for these transitions in output:

```text
TASK [portworx_upgrade : Include preflight validation] ***
→ Environment validated
→ Nodes validated
→ Pods validated
→ Cluster health confirmed

TASK [portworx_upgrade : Include operator upgrade] ***
→ Current version detected
→ Target version set
→ Subscription updated

TASK [portworx_upgrade : Include monitor] ***
→ Initial pod count: X
→ Target version: Y
→ Activity detected...
→ Completed: N of X

TASK [portworx_upgrade : Include validate] ***
→ Storage pools: N online
→ Volumes: N up, 0 down
→ All nodes on target version

TASK [portworx_upgrade : Include report] ***
→ Report generated: /tmp/px-upgrade-test/px-upgrade-summary-TIMESTAMP.txt
```

## Success Criteria

### Upgrade Considered Successful When:

- [ ] All preflight checks passed
- [ ] Operator upgraded (if version changed)
- [ ] All nodes upgraded to target version
- [ ] No timeout errors occurred
- [ ] Final validation passed:
  - [ ] All storage pools online
  - [ ] No down or degraded volumes
  - [ ] All nodes online
  - [ ] STC Available condition True
- [ ] Reports generated successfully
- [ ] Cluster operational post-upgrade

### Validation Results Checklist:

**Storage Pool Health:**
- [ ] All pools status = "Up"
- [ ] No pools over 80% capacity
- [ ] Average capacity under threshold (90%)

**Volume Health:**
- [ ] Zero volumes in down state
- [ ] Zero degraded volumes
- [ ] All attached volumes healthy
- [ ] Detached volumes acceptable (unused PVCs)

**StorageCluster Conditions:**
- [ ] Available = True
- [ ] Update = False (post-upgrade)
- [ ] Degraded = False
- [ ] No Unknown conditions

**Node Statistics:**
- [ ] All nodes online
- [ ] Zero offline or degraded nodes
- [ ] 100% nodes on target version
- [ ] Storage vs storageless ratio makes sense

## Troubleshooting

### Common Issues and Solutions

#### Issue: Preflight validation fails

**Symptom:** Assertions fail during preflight phase

**Possible Causes:**
- Insufficient permissions
- Cluster not ready
- Missing StorageCluster resource

**Solutions:**
1. Verify cluster admin permissions: `oc whoami --show-context`
2. Check cluster health: `oc get nodes`
3. Verify Portworx installation: `oc get storagecluster -n portworx`
4. Review error message for specific failure

#### Issue: Operator upgrade times out

**Symptom:** Operator InstallPlan approval takes too long

**Possible Causes:**
- Operator not responding
- Network issues downloading images
- Insufficient cluster resources

**Solutions:**
1. Check operator logs: `oc logs -n portworx -l name=portworx-operator`
2. Verify InstallPlan status: `oc get installplan -n portworx`
3. Check cluster resources: `oc adm top nodes`
4. Manually approve if needed: `oc patch installplan <name> -n portworx --type merge -p '{"spec":{"approved":true}}'`

#### Issue: Pod stuck in Terminating

**Symptom:** Pod doesn't complete termination within 15 minutes

**Possible Causes:**
- Application still using storage
- Finalizer blocking deletion
- Node issues

**Solutions:**
1. Check pod events: `oc describe pod <pod-name> -n portworx`
2. Check for finalizers: `oc get pod <pod-name> -n portworx -o yaml | grep finalizers`
3. Verify node health: `oc get nodes`
4. If safe, force delete: `oc delete pod <pod-name> -n portworx --grace-period=0 --force`

#### Issue: Global timeout reached

**Symptom:** "No activity detected for 35 minutes" error

**Possible Causes:**
- Operator stuck
- All nodes failing to upgrade
- Network partition

**Solutions:**
1. Check operator logs: `oc logs -n portworx -l name=portworx-operator --tail=200`
2. Verify StorageCluster status: `oc describe storagecluster -n portworx`
3. Check for failing pods: `oc get pods -n portworx --field-selector=status.phase!=Running`
4. Review OpenShift cluster events: `oc get events --all-namespaces --sort-by='.lastTimestamp' | tail -50`

#### Issue: Validation fails post-upgrade

**Symptom:** Final validation detects degraded resources

**Possible Causes:**
- Upgrade incomplete
- Storage issues
- Network problems

**Solutions:**
1. Check pxctl status: `oc exec -n portworx $(oc get pods -n portworx -l name=portworx -o jsonpath='{.items[0].metadata.name}') -- /opt/pwx/bin/pxctl status`
2. Review pxctl alerts: `oc exec -n portworx $(oc get pods -n portworx -l name=portworx -o jsonpath='{.items[0].metadata.name}') -- /opt/pwx/bin/pxctl alerts show`
3. Check specific resources mentioned in error
4. Allow more time for cluster to stabilize (5-10 minutes)

#### Issue: Impatient mode doesn't trigger

**Symptom:** Storageless nodes don't accelerate

**Possible Causes:**
- Not enough storageless nodes
- Storage nodes not yet complete
- Impatient mode disabled

**Solutions:**
1. Verify impatient mode enabled: Check playbook variables
2. Confirm storage nodes complete: Look for "Storage nodes validated" message
3. Check storageless node count: Must be > 0
4. Review batch size configuration: Should be 3-10

### Recovery Procedures

#### Upgrade Stuck Mid-Process

If upgrade appears stuck:

1. **Don't panic** - Allow full timeout period
2. **Gather information:**
   ```bash
   oc get pods -n portworx
   oc get storagecluster -n portworx
   oc logs -n portworx -l name=portworx-operator --tail=100
   ```
3. **Check Ansible logs** for last activity
4. **Wait for timeout** - Let role's stuck detection handle it
5. **If role completes with error:** Review error message and troubleshooting steps provided

#### Complete Failure

If upgrade completely fails:

1. **Capture state:**
   ```bash
   oc get all -n portworx > /tmp/px-state.txt
   oc describe storagecluster -n portworx >> /tmp/px-state.txt
   oc logs -n portworx -l name=portworx-operator --tail=500 >> /tmp/px-operator-logs.txt
   ```

2. **Review backups** (if portworx_backup_resources=true):
   ```bash
   ls -lh /tmp/px-upgrade-test/backups/
   ```

3. **Assess cluster state:**
   - Are any nodes upgraded?
   - Is cluster still operational?
   - Are volumes accessible?

4. **Contact support** with captured state and Ansible logs

## Post-Test Validation

After successful lab testing, verify:

### 1. Cluster Health

```bash
# Overall status
oc exec -n portworx $(oc get pods -n portworx -l name=portworx -o jsonpath='{.items[0].metadata.name}') -- /opt/pwx/bin/pxctl status

# Storage pools
oc exec -n portworx $(oc get pods -n portworx -l name=portworx -o jsonpath='{.items[0].metadata.name}') -- /opt/pwx/bin/pxctl service pool show

# Volumes
oc exec -n portworx $(oc get pods -n portworx -l name=portworx -o jsonpath='{.items[0].metadata.name}') -- /opt/pwx/bin/pxctl volume list
```

### 2. Application Workloads

Test that applications using Portworx storage still work:

```bash
# Check PVCs
oc get pvc --all-namespaces

# Verify pod access to storage
oc exec <app-pod> -- ls /mnt/data
```

### 3. Performance

Verify storage performance hasn't degraded:

```bash
# Basic I/O test
oc exec <app-pod> -- dd if=/dev/zero of=/mnt/data/test bs=1M count=100
```

### 4. Documentation

Document your testing results:

- Cluster size tested
- Versions upgraded (from → to)
- Total upgrade time
- Any issues encountered
- Impatient mode effectiveness (if tested)
- Report output samples

## Next Steps

### Prepare for Production

After successful lab testing:

1. **Review learnings** from lab tests
2. **Adjust variables** based on observed behavior
3. **Plan production window** with appropriate time buffer
4. **Prepare rollback plan** (though role doesn't support rollback)
5. **Schedule change window** with stakeholders
6. **Document production procedure** specific to your environment

### Production Checklist

Before running in production:

- [ ] Lab testing completed successfully
- [ ] Version files prepared for production target version
- [ ] Backup procedures confirmed
- [ ] Change window scheduled
- [ ] Stakeholders notified
- [ ] Rollback plan documented (external to role)
- [ ] Monitoring dashboards ready
- [ ] Support contacts available

## References

- Role documentation: `roles/portworx_upgrade/README.md`
- Integration tests: `docs/portworx_upgrade/TESTING.md`
- Quick start guide: `docs/portworx_upgrade/QUICKSTART.md`
- Monitoring flow: `docs/portworx_upgrade/monitoring-flow.md`
- Manual procedures: `docs/portworx_upgrade/portworx-upgrade-manual-v2.md`
