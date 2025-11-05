# Archive Preservation Feature

## Overview

The must-gather role now includes automatic archive preservation with configurable retention policies. This ensures historical archives are retained for reference while maintaining clean working directories for new collections.

## How It Works

### Preservation Process

1. **Before Cleanup**: Role searches for existing must-gather archives
2. **Copy to Archive Directory**: Archives are copied to a dedicated preservation directory
3. **Timestamped Naming**: Archives are renamed with cluster name and timestamp
4. **Apply Retention**: Old archives are cleaned up based on retention policy
5. **Clean Working Directory**: Working directories are removed for fresh collection

### Directory Structure

```
/tmp/                                          # WORK_DIR
├── must-gather-1730890000/                    # Current working directory
│   ├── cluster-name-1730890000/               # Collection subdirectory
│   │   └── (must-gather data)
│   └── must-gather.tar.gz                     # Current archive(s)
│
└── must-gather-archives/                      # Preservation directory
    ├── prod-ocp-01-case03123456-must-gather.tar.gz-2025-11-05T14-23-45Z
    ├── prod-ocp-01-case03123456-must-gather.tar.gz-2025-11-04T10-15-30Z
    ├── prod-ocp-01-case03654321-must-gather.tar.gz.part000-2025-11-03T08-45-12Z
    └── prod-ocp-01-case03654321-must-gather.tar.gz.part001-2025-11-03T08-45-12Z
```

## Configuration

### Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `mustgather_archive_dir` | `{{ WORK_DIR }}/must-gather-archives` | Archive preservation directory |
| `mustgather_archive_retention_days` | `30` | Keep archives for N days (0 = forever) |
| `mustgather_archive_retention_count` | `10` | Keep last N archives (0 = unlimited) |

### Retention Policies

The role supports two retention policies that work independently:

#### 1. Age-Based Retention

**Configuration:**
```yaml
mustgather_archive_retention_days: 30
```

**Behavior:**
- Archives older than 30 days are automatically deleted
- Set to `0` to disable age-based retention (keep forever)

#### 2. Count-Based Retention

**Configuration:**
```yaml
mustgather_archive_retention_count: 10
```

**Behavior:**
- Only the last 10 archives are retained (sorted by modification time)
- Older archives beyond the count are automatically deleted
- Set to `0` to disable count-based retention (unlimited)

### Combined Policies

Both policies can be active simultaneously:

```yaml
mustgather_archive_retention_days: 30   # Delete archives older than 30 days
mustgather_archive_retention_count: 10  # Keep only last 10 archives
```

**Result:** Archives are deleted if they are either:
- Older than 30 days, OR
- Beyond the last 10 archives (even if newer than 30 days)

## Usage Examples

### Example 1: Keep Forever, No Limit

```yaml
mustgather_archive_retention_days: 0
mustgather_archive_retention_count: 0
```

All archives are preserved indefinitely. Manual cleanup required.

### Example 2: Keep Last 5 Archives Only

```yaml
mustgather_archive_retention_days: 0
mustgather_archive_retention_count: 5
```

Only the 5 most recent archives are retained. Useful for frequent collections.

### Example 3: 90-Day Retention

```yaml
mustgather_archive_retention_days: 90
mustgather_archive_retention_count: 0
```

Archives are kept for 90 days regardless of quantity. Useful for compliance requirements.

### Example 4: Balanced Approach (Default)

```yaml
mustgather_archive_retention_days: 30
mustgather_archive_retention_count: 10
```

Keeps archives for 30 days OR last 10 collections, whichever provides more retention.

## Archive Naming Convention

Preserved archives follow this naming pattern:

```
<cluster_name>-case<rh_case>-<original_filename>-<ISO8601_timestamp>
```

**Examples:**
- `prod-ocp-01-case03123456-must-gather.tar.gz-2025-11-05T14-23-45Z`
- `prod-ocp-01-case03123456-must-gather.tar.gz.part000-2025-11-05T14-23-45Z`
- `staging-case03654321-must-gather.tar.gz-2025-11-04T10-15-30Z`

**Benefits:**
- **Cluster identification** in filename
- **Red Hat case number** for correlation with support cases
- **Sortable by timestamp** for chronological reference
- **Original filename** preserved (including split part numbers)
- **Unique across multiple collections** and support cases

## Operational Summary

After each run, the operation summary includes archive preservation information:

```
===================================================================
Must-Gather Operation Summary
===================================================================
Host: ocp-master-01
Cluster: prod-ocp-01
Red Hat Case: 03123456
Status: SUCCESS
Archive Parts: 1
Collection Size: 347.52 MB
Node Used: infra-node-01
Cleanup Performed: Yes
Preserved Archives: 8 in /tmp/must-gather-archives
Retention Policy: 30d / 10 count
===================================================================
```

## Archive Management

### List Preserved Archives

```bash
# All archives
ls -lht /tmp/must-gather-archives/

# Specific cluster
ls -lht /tmp/must-gather-archives/ | grep prod-ocp-01

# Specific Red Hat case
ls -lht /tmp/must-gather-archives/ | grep case03123456

# Specific cluster AND case
ls -lht /tmp/must-gather-archives/ | grep prod-ocp-01 | grep case03123456

# Archives older than 30 days
find /tmp/must-gather-archives/ -type f -mtime +30 -ls
```

### Retrieve Preserved Archive

```bash
# Find archive by approximate date
ls -lht /tmp/must-gather-archives/ | grep 2025-11-05

# Find archive by case number
ls -lht /tmp/must-gather-archives/ | grep case03123456

# Copy to current directory (by case)
cp /tmp/must-gather-archives/prod-ocp-01-case03123456-must-gather.tar.gz-2025-11-05T14-23-45Z .

# Copy to current directory (by date)
cp /tmp/must-gather-archives/*2025-11-05T14-23-45Z .

# Extract and examine
tar xzf prod-ocp-01-case03123456-must-gather.tar.gz-2025-11-05T14-23-45Z
```

### Manual Cleanup

```bash
# Delete archives older than 60 days
find /tmp/must-gather-archives/ -type f -mtime +60 -delete

# Delete archives for specific cluster
rm -f /tmp/must-gather-archives/prod-ocp-01-*

# Delete archives for specific case
rm -f /tmp/must-gather-archives/*-case03123456-*

# Delete archives for specific cluster and case
rm -f /tmp/must-gather-archives/prod-ocp-01-case03123456-*

# Delete all archives (emergency cleanup)
rm -rf /tmp/must-gather-archives/
```

## Disk Space Considerations

### Calculation

- **Single Collection:** 100-500 MB typical
- **Large Collection:** 1-3 GB (may be split)
- **10 Archives:** 1-5 GB estimated
- **30 Days @ 1/day:** 3-15 GB estimated

### Monitoring

```bash
# Check archive directory size
du -sh /tmp/must-gather-archives/

# Check per-cluster usage
du -sh /tmp/must-gather-archives/* | grep prod-ocp-01

# Count archives per cluster
ls -1 /tmp/must-gather-archives/ | grep prod-ocp-01 | wc -l

# Count archives per Red Hat case
ls -1 /tmp/must-gather-archives/ | grep case03123456 | wc -l

# List all cases with archive counts
ls -1 /tmp/must-gather-archives/ | sed 's/.*-case\([0-9]*\)-.*/\1/' | sort | uniq -c
```

### Recommendations

1. **High-Frequency Collections** (daily):
   - Use count-based retention: `mustgather_archive_retention_count: 7`
   - Limit to last week of collections

2. **Low-Frequency Collections** (weekly/monthly):
   - Use age-based retention: `mustgather_archive_retention_days: 90`
   - Keep 3 months of history

3. **Compliance Requirements**:
   - Align retention with compliance period
   - Consider external backup before cleanup
   - Document retention policy

4. **Storage-Constrained Environments**:
   - Use conservative count: `mustgather_archive_retention_count: 3`
   - Monitor disk usage: Add alerting at 80% capacity
   - Consider compression or offload to external storage

## Integration with skip_mustgather_deletion

The archive preservation works independently from `skip_mustgather_deletion`:

| `skip_mustgather_deletion` | Working Directory | Archive Directory |
|---------------------------|------------------|-------------------|
| `false` (default) | Cleaned up | Preserved with retention |
| `true` | Preserved | Preserved with retention |

**Use Case for `skip_mustgather_deletion: true`:**
- Debugging must-gather issues
- Manual inspection before upload
- Multi-step processing workflows

## Troubleshooting

### Issue: Preserved Archives Not Found

**Symptoms:**
- `Preserved Archives: 0` in summary
- No files in `{{ mustgather_archive_dir }}`

**Possible Causes:**
1. First run (no previous archives exist)
2. Archives in different location than expected
3. Permissions issue preventing access

**Resolution:**
```bash
# Check if directory exists
ls -la /tmp/must-gather-archives/

# Verify previous archives exist
find /tmp -name "must-gather.tar.gz*" -type f

# Check permissions
ls -la $(dirname /tmp/must-gather-archives/)
```

### Issue: Retention Not Applying

**Symptoms:**
- More archives than `retention_count`
- Archives older than `retention_days`

**Possible Causes:**
1. Retention set to `0` (disabled)
2. Archives in subdirectories (not searched)
3. Task failed silently

**Resolution:**
```bash
# Verify retention settings
grep retention /path/to/defaults/main.yml

# Manual cleanup
find /tmp/must-gather-archives/ -type f -mtime +30 -ls
find /tmp/must-gather-archives/ -type f -mtime +30 -delete
```

### Issue: Disk Space Exhausted

**Symptoms:**
- "No space left on device" error
- Archive creation fails

**Immediate Resolution:**
```bash
# Check disk usage
df -h /tmp

# Emergency cleanup (delete oldest archives)
cd /tmp/must-gather-archives/
ls -lt | tail -20 | awk '{print $9}' | xargs rm -f

# Or delete all preserved archives
rm -rf /tmp/must-gather-archives/*
```

**Preventive Measures:**
1. Reduce retention count: `mustgather_archive_retention_count: 3`
2. Reduce retention days: `mustgather_archive_retention_days: 7`
3. Monitor disk usage proactively
4. Offload archives to external storage

## Best Practices

### 1. Set Appropriate Retention Based on Collection Frequency

```yaml
# Daily collections
mustgather_archive_retention_count: 7  # Last week

# Weekly collections
mustgather_archive_retention_days: 90  # 3 months

# On-demand only
mustgather_archive_retention_count: 5  # Last 5 incidents
```

### 2. Document Retention Policy

```yaml
# Organization policy: Retain diagnostics for 90 days per SEC-POL-2025-03
mustgather_archive_retention_days: 90
mustgather_archive_retention_count: 0
```

### 3. Monitor Archive Storage

- Add disk usage monitoring for `{{ mustgather_archive_dir }}`
- Alert at 80% capacity threshold
- Review retention policy if alerts frequent

### 4. Backup Critical Archives

```bash
# Backup to external storage before automated cleanup
rsync -av /tmp/must-gather-archives/ backup-server:/archives/must-gather/
```

### 5. Use Descriptive Cluster Names

```yaml
cluster_name: "prod-ocp-east-01"  # Good: Specific, identifiable
cluster_name: "cluster"           # Bad: Generic, hard to identify
```

### 6. Correlate Archives with Support Cases

The inclusion of Red Hat case number in filenames enables easy correlation:

```bash
# Find all archives for a specific support case
ls -lht /tmp/must-gather-archives/ | grep case03123456

# Useful when:
# - Red Hat requests additional must-gather data
# - Reviewing past case resolution steps
# - Auditing uploaded diagnostics
# - Correlating issues across multiple clusters
```

## Future Enhancements

Potential improvements for consideration:

1. **External Storage Integration**: Automatic offload to S3/NFS
2. **Compression**: Recompress old archives to save space
3. **Metadata Tracking**: JSON manifest with archive metadata
4. **Selective Preservation**: Preserve only successful uploads
5. **Automatic Backup**: Copy to backup location before retention cleanup

## Related Documentation

- `README_CONDENSE.md` - Complete role documentation
- `QUICK_REFERENCE.md` - Operator quick reference
- `defaults/main.yml` - Variable definitions and defaults

