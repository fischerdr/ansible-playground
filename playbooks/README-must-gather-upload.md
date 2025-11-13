# Must-Gather Upload Architecture

## Overview

This directory contains playbooks for testing and managing must-gather archive uploads to Red Hat support cases. The architecture is designed to handle **100-500GB archives** with memory-efficient streaming and enterprise-grade reliability.

## Architecture for Large Archives (100-500GB)

### Critical Design Decisions

1. **Memory-Efficient Streaming**: Archives are split BEFORE compression using streaming pipeline
2. **Red Hat API Limit**: 1GB per file maximum (we use 800MB to stay safely under limit)
3. **Independent Parts**: Each part is compressed independently for resume capability
4. **No Memory Exhaustion**: Constant memory usage regardless of archive size

### Splitting Strategy

```bash
# OLD (BROKEN for 100-500GB): Compress entire archive first, then split
tar czf - data/ | split -b 900M  # Loads full archive in memory - FAILS

# NEW (CORRECT for 100-500GB): Stream tar -> split -> compress each part
tar cf - data/ | split -b 800M --filter='gzip -9 > "$FILE.tar.gz"' - must-gather.part
```

**Why this works:**
- Streams data through pipeline (constant ~100MB memory)
- Each part independently compressed (parallel decompression possible)
- If upload fails on part 347/625, resume from that part only
- Red Hat can decompress parts individually

### Split Size Calculation

For 1489MB test archive with 800MB split size:
```
Uncompressed: 1489MB / 800MB = 1.86 parts → 2 parts
Part 000: 800MB uncompressed → ~500MB compressed (typical 1.6x ratio)
Part 001: 689MB uncompressed → ~430MB compressed
```

For 500GB production archive with 800MB split size:
```
Uncompressed: 500GB / 800MB = ~625 parts
Each part: ~800MB uncompressed → ~500MB compressed
Total upload time: ~20-50 hours @ 1Gbps with retries
```

## Playbooks

### 1. test-must-gather-upload.yml

Tests upload functionality with configurable archive sizes.

**Usage for multi-part testing:**

```bash
# Test with 1489MB archive (creates 2 parts with 800MB split)
ansible-playbook -i inventory/hosts.yml playbooks/test-must-gather-upload.yml \
  -e cluster_name=test-cluster-1 \
  -e kubeconfig_path=/path/to/kubeconfig \
  -e rh_case=01234567 \
  -e test_archive_size_mb=1489 \
  -e test_create_split_archives=true

# Production-scale test: 10GB archive → ~13 parts
ansible-playbook -i inventory/hosts.yml playbooks/test-must-gather-upload.yml \
  -e cluster_name=test-cluster-1 \
  -e kubeconfig_path=/path/to/kubeconfig \
  -e rh_case=01234567 \
  -e test_archive_size_mb=10000 \
  -e test_create_split_archives=true \
  -e split_size_mb=800

# Custom split size (e.g., 500MB for slower connections)
ansible-playbook -i inventory/hosts.yml playbooks/test-must-gather-upload.yml \
  -e cluster_name=test-cluster-1 \
  -e kubeconfig_path=/path/to/kubeconfig \
  -e rh_case=01234567 \
  -e test_archive_size_mb=5000 \
  -e test_create_split_archives=true \
  -e split_size_mb=500
```

**Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `test_archive_size_mb` | 10 | Size of test archive in MB (use 1489 for 2-part test) |
| `test_create_split_archives` | false | Set to true for multi-part upload testing |
| `split_size_mb` | 800 | Split size in MB (800MB recommended for production) |
| `rh_upload_max_retries` | 5 | Maximum retry attempts per file |
| `rh_upload_retry_backoff` | 5 | Exponential backoff base in seconds |
| `rh_upload_timeout` | 1800 | HTTP timeout in seconds (30 minutes) |

**Expected Behavior with 1489MB + split_size_mb=800:**

```
1489MB test archive:
├── must-gather.part000.tar.gz (800MB uncompressed → ~500MB compressed)
└── must-gather.part001.tar.gz (689MB uncompressed → ~430MB compressed)

Total: 2 parts
```

### 2. cleanup-test-must-gather-upload.yml

Removes test uploads from Red Hat support cases via API.

**Usage:**

```bash
# Dry run (list files that would be deleted)
ansible-playbook -i inventory/hosts.yml playbooks/cleanup-test-must-gather-upload.yml \
  -e rh_case=01234567 \
  -e dry_run=true

# Actually delete test uploads
ansible-playbook -i inventory/hosts.yml playbooks/cleanup-test-must-gather-upload.yml \
  -e rh_case=01234567 \
  -e dry_run=false

# Custom cleanup pattern
ansible-playbook -i inventory/hosts.yml playbooks/cleanup-test-must-gather-upload.yml \
  -e rh_case=01234567 \
  -e cleanup_pattern="must-gather for test-cluster-1" \
  -e dry_run=false

# Increase safety limit (default 50 files)
ansible-playbook -i inventory/hosts.yml playbooks/cleanup-test-must-gather-upload.yml \
  -e rh_case=01234567 \
  -e max_deletions=100 \
  -e dry_run=false
```

**Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `cleanup_pattern` | "TEST UPLOAD" | Pattern to match in attachment descriptions |
| `dry_run` | false | Set to true to preview deletions without actually deleting |
| `max_deletions` | 50 | Safety limit: max attachments to delete per run |

**Safety Features:**

1. **Dry run mode**: Preview deletions before committing
2. **Pattern matching**: Only deletes attachments matching pattern
3. **Safety limit**: Prevents accidental mass deletion (default 50 files)
4. **Verification**: Lists remaining attachments after deletion

## Production Recommendations

### For 100-500GB Must-Gather Archives

1. **Split size**: Use `split_size_mb=800` (stays under 1GB Red Hat API limit)
2. **Timeout**: Use `rh_upload_timeout=3600` (60 minutes per file for slow connections)
3. **Retries**: Use `rh_upload_max_retries=5` and `rh_upload_retry_backoff=5`
4. **Logging**: Always enable `log_dir` for troubleshooting failed parts
5. **Fail on partial**: Set `rh_upload_fail_on_partial=false` to allow resuming failed uploads

### Expected Upload Times

| Archive Size | Split Size | Parts | Upload Time @ 1Gbps |
|--------------|------------|-------|---------------------|
| 100GB | 800MB | ~125 | ~4-10 hours |
| 250GB | 800MB | ~320 | ~10-25 hours |
| 500GB | 800MB | ~625 | ~20-50 hours |

**Note**: Times include compression overhead, network latency, and retry attempts.

### Handling Upload Failures

If uploads fail for specific parts:

1. Check upload logs in `{{ mustgather_upload_logs }}/redhat_upload_*.log`
2. Identify failed part numbers from module output
3. Re-run playbook with `fail_on_partial=false` to continue from failures
4. Module automatically retries failed parts only

### Network Considerations

For slow or unreliable connections:

1. Reduce split size: `split_size_mb=500` (creates more, smaller parts)
2. Increase timeout: `rh_upload_timeout=7200` (2 hours)
3. Increase retry backoff: `rh_upload_retry_backoff=10` (longer delays between retries)
4. Enable detailed logging: `log_dir=/var/log/must-gather-uploads`

## Red Hat API Endpoints

The playbooks use these Red Hat Customer Portal API endpoints:

1. **OAuth Token Exchange**: `https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token`
2. **Case Details**: `GET https://api.access.redhat.com/support/v1/cases/{case_id}`
3. **List Attachments**: `GET https://api.access.redhat.com/support/v1/cases/{case_id}/attachments`
4. **Upload Attachment**: `POST https://api.access.redhat.com/support/v1/cases/{case_id}/attachments/`
5. **Delete Attachment**: `DELETE https://api.access.redhat.com/support/v1/cases/{case_id}/attachments/{uuid}`

**Authentication Methods:**

1. **Bearer Token** (preferred): OAuth token from Red Hat SSO
2. **Basic Auth** (fallback): Username/password with HTTP Basic Authentication

## Module Documentation

See [roles/must_gather_log/library/redhat_upload.py](../roles/must_gather_log/library/redhat_upload.py) for detailed module documentation.

**Key Module Parameters:**

- `case_id`: Red Hat support case number (required)
- `archive_pattern`: Glob pattern for archive files (required)
- `upload_description`: Base description for uploads (required)
- `api_token` / `api_user` + `api_pass`: Authentication (required)
- `max_file_size_bytes`: Maximum file size (default: 1GB)
- `timeout`: HTTP timeout in seconds (default: 1800)
- `log_dir`: Directory for detailed upload logs (optional but recommended)

## Troubleshooting

### "File exceeds size limit" Error

```
Error: File exceeds size limit (1200000000 bytes > 1073741824 bytes)
```

**Solution**: Reduce split size below 1GB:

```bash
-e split_size_mb=800  # Recommended
-e split_size_mb=700  # For high compression ratios
```

### "Connection timeout" Error

```
Error: Connection error: ReadTimeout
```

**Solution**: Increase timeout and reduce split size:

```bash
-e rh_upload_timeout=3600
-e split_size_mb=500
```

### "Upload failed after N attempts"

```
Error: Upload failed after 5 attempts: HTTP 503
```

**Solution**: Red Hat API is experiencing issues. Wait and retry, or increase backoff:

```bash
-e rh_upload_max_retries=10
-e rh_upload_retry_backoff=10
```

### Memory Exhaustion During Split

```
Error: Cannot allocate memory
```

**Solution**: Verify you're using the NEW streaming split method (check playbook line 186-190). The old method (`tar czf - | split`) loads entire archive in memory and will fail for large files.

## Testing Checklist

Before production deployment:

- [ ] Test with 10MB single archive (baseline)
- [ ] Test with 1489MB split archive (2 parts)
- [ ] Test with 10GB split archive (~13 parts)
- [ ] Test cleanup playbook in dry-run mode
- [ ] Test cleanup playbook with actual deletion
- [ ] Test upload failure scenarios (invalid credentials, wrong case ID)
- [ ] Test resume capability (interrupt upload mid-way)
- [ ] Verify log files are created in `log_dir`
- [ ] Verify split files are under 1GB each

## References

- [Red Hat Customer Portal API Documentation](https://access.redhat.com/articles/3626371)
- [Must-Gather Upload Role](../roles/must_gather_log/)
- [Ansible Best Practices](../CLAUDE.md)
