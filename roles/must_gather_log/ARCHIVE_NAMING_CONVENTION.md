# Archive Naming Convention

## Format

```
<cluster_name>-case<rh_case>-<original_filename>-<ISO8601_timestamp>
```

## Components

| Component | Description | Example |
|-----------|-------------|---------|
| `cluster_name` | OpenShift cluster identifier | `prod-ocp-01` |
| `case` | Literal text "case" | `case` |
| `rh_case` | Red Hat support case number | `03123456` |
| `original_filename` | Name of the archive file | `must-gather.tar.gz` |
| `ISO8601_timestamp` | Timestamp when preserved | `2025-11-05T14-23-45Z` |

## Examples

### Single Archive

```
prod-ocp-01-case03123456-must-gather.tar.gz-2025-11-05T14-23-45Z
│           │           │                  │
│           │           │                  └─ Preservation timestamp
│           │           └──────────────────── Original filename
│           └──────────────────────────────── Red Hat case number (with "case" prefix)
└──────────────────────────────────────────── Cluster name
```

### Split Archives (Multi-Part)

When archives exceed 900MB and are automatically split:

```
prod-ocp-01-case03123456-must-gather.tar.gz.part000-2025-11-05T14-23-45Z
prod-ocp-01-case03123456-must-gather.tar.gz.part001-2025-11-05T14-23-45Z
prod-ocp-01-case03123456-must-gather.tar.gz.part002-2025-11-05T14-23-45Z
```

All parts share the same:
- Cluster name
- Case number
- Base filename
- Preservation timestamp

Only the part number (`.part000`, `.part001`, etc.) differs.

## Real-World Examples

### Production Environment

```
prod-ocp-east-01-case03123456-must-gather.tar.gz-2025-11-05T14-23-45Z
staging-ocp-west-02-case03654321-must-gather.tar.gz-2025-11-04T10-15-30Z
dev-ocp-central-03-case03789012-must-gather.tar.gz.part000-2025-11-03T08-45-12Z
```

### Multiple Collections for Same Case

When multiple must-gather collections are performed for the same support case:

```
prod-ocp-01-case03123456-must-gather.tar.gz-2025-11-05T14-23-45Z  # First collection
prod-ocp-01-case03123456-must-gather.tar.gz-2025-11-06T09-30-12Z  # Second collection (next day)
prod-ocp-01-case03123456-must-gather.tar.gz-2025-11-06T15-45-33Z  # Third collection (same day)
```

**Note:** Timestamps ensure uniqueness even for multiple collections on the same case.

### Multiple Clusters for Same Case

When investigating an issue affecting multiple clusters:

```
prod-ocp-east-01-case03123456-must-gather.tar.gz-2025-11-05T14-23-45Z
prod-ocp-west-01-case03123456-must-gather.tar.gz-2025-11-05T14-30-12Z
prod-ocp-central-01-case03123456-must-gather.tar.gz-2025-11-05T14-35-55Z
```

**Benefit:** Easily identify all archives related to the same support case across multiple clusters.

## Benefits

### 1. Cluster Identification

```bash
# Find all archives for a specific cluster
ls -lht /tmp/must-gather-archives/ | grep prod-ocp-01
```

### 2. Case Correlation

```bash
# Find all archives for a specific support case
ls -lht /tmp/must-gather-archives/ | grep case03123456

# Find archives for specific case across all clusters
ls -lht /tmp/must-gather-archives/ | grep case03123456
```

### 3. Combined Search

```bash
# Find archives for specific cluster AND case
ls -lht /tmp/must-gather-archives/ | grep prod-ocp-01 | grep case03123456

# Find archives for case on specific date
ls -lht /tmp/must-gather-archives/ | grep case03123456 | grep 2025-11-05
```

### 4. Chronological Sorting

```bash
# List archives chronologically (newest first)
ls -lt /tmp/must-gather-archives/

# List archives chronologically (oldest first)
ls -ltr /tmp/must-gather-archives/
```

### 5. Audit Trail

The filename provides complete context without needing external documentation:
- **What cluster:** `prod-ocp-01`
- **What case:** `case03123456`
- **What data:** `must-gather.tar.gz`
- **When preserved:** `2025-11-05T14-23-45Z`

## Search Patterns

### By Cluster

```bash
# All archives for production clusters
ls -1 /tmp/must-gather-archives/ | grep "^prod-"

# All archives for specific cluster
ls -1 /tmp/must-gather-archives/ | grep "prod-ocp-01"

# Count archives per cluster
ls -1 /tmp/must-gather-archives/ | cut -d'-' -f1-3 | sort | uniq -c
```

### By Case

```bash
# All archives for specific case
ls -1 /tmp/must-gather-archives/ | grep "case03123456"

# List all unique case numbers
ls -1 /tmp/must-gather-archives/ | sed 's/.*-case\([0-9]*\)-.*/\1/' | sort -u

# Count archives per case
ls -1 /tmp/must-gather-archives/ | sed 's/.*-case\([0-9]*\)-.*/\1/' | sort | uniq -c
```

### By Date

```bash
# Archives from specific date
ls -1 /tmp/must-gather-archives/ | grep "2025-11-05"

# Archives from specific month
ls -1 /tmp/must-gather-archives/ | grep "2025-11-"

# Archives from today (using date command)
ls -1 /tmp/must-gather-archives/ | grep "$(date -u +%Y-%m-%d)"
```

### By Archive Type

```bash
# Single archives (not split)
ls -1 /tmp/must-gather-archives/ | grep -v "\.part[0-9]"

# Split archives (multi-part)
ls -1 /tmp/must-gather-archives/ | grep "\.part[0-9]"

# Count split vs single archives
echo "Single: $(ls -1 /tmp/must-gather-archives/ | grep -v "\.part[0-9]" | wc -l)"
echo "Split:  $(ls -1 /tmp/must-gather-archives/ | grep "\.part[0-9]" | wc -l)"
```

## Filename Length Considerations

### Typical Length

```
prod-ocp-01-case03123456-must-gather.tar.gz-2025-11-05T14-23-45Z
│ (11)     │ (13)       │ (18)            │ (25)
└────────────────────────────────────────────────────────────────── Total: ~72 characters
```

### Maximum Expected Length

With longest reasonable values:
```
production-ocp-east-region-01-case99999999-must-gather.tar.gz.part999-2025-12-31T23-59-59Z
│ (30)                         │ (18)       │ (28)                │ (25)
└──────────────────────────────────────────────────────────────────────────────────────── Total: ~106 characters
```

**Note:** Well within filesystem limits (typically 255 characters).

## Parsing Examples

### Extract Components from Filename

```bash
# Filename
FILENAME="prod-ocp-01-case03123456-must-gather.tar.gz-2025-11-05T14-23-45Z"

# Extract cluster name (everything before first "-case")
CLUSTER=$(echo "$FILENAME" | sed 's/-case.*//')
# Result: prod-ocp-01

# Extract case number (between "case" and next "-")
CASE=$(echo "$FILENAME" | sed 's/.*-case\([0-9]*\)-.*/\1/')
# Result: 03123456

# Extract timestamp (everything after last "-")
TIMESTAMP=$(echo "$FILENAME" | rev | cut -d'-' -f1-5 | rev)
# Result: 2025-11-05T14-23-45Z

# Check if split archive
if [[ "$FILENAME" =~ \.part[0-9]+ ]]; then
  echo "Split archive"
  PART_NUM=$(echo "$FILENAME" | grep -oP '\.part\K[0-9]+')
  echo "Part number: $PART_NUM"
fi
```

### Generate Archive Report

```bash
#!/bin/bash
# Report on preserved archives

ARCHIVE_DIR="/tmp/must-gather-archives"

echo "==================================="
echo "Must-Gather Archive Report"
echo "==================================="
echo ""

echo "Total archives: $(ls -1 $ARCHIVE_DIR | wc -l)"
echo ""

echo "Archives by cluster:"
ls -1 $ARCHIVE_DIR | sed 's/-case.*//' | sort | uniq -c | sort -rn
echo ""

echo "Archives by case:"
ls -1 $ARCHIVE_DIR | sed 's/.*-case\([0-9]*\)-.*/\1/' | sort | uniq -c | sort -rn
echo ""

echo "Oldest archive:"
ls -lt $ARCHIVE_DIR | tail -1 | awk '{print $9}'
echo ""

echo "Newest archive:"
ls -lt $ARCHIVE_DIR | head -1 | awk '{print $9}'
echo ""

echo "Total disk usage:"
du -sh $ARCHIVE_DIR
```

## Migration from Previous Naming Convention

If you have archives using the old naming convention without case numbers:

### Old Format

```
prod-ocp-01-must-gather.tar.gz-2025-11-05T14-23-45Z
```

### Identify Old Format Archives

```bash
# Find archives without case numbers
ls -1 /tmp/must-gather-archives/ | grep -v "case[0-9]"
```

### Manual Renaming (if case number known)

```bash
# Example: Rename archive to include case number
OLD="prod-ocp-01-must-gather.tar.gz-2025-11-05T14-23-45Z"
NEW="prod-ocp-01-case03123456-must-gather.tar.gz-2025-11-05T14-23-45Z"

mv "/tmp/must-gather-archives/$OLD" "/tmp/must-gather-archives/$NEW"
```

### Bulk Renaming with Unknown Case

If case numbers are unknown, consider adding a placeholder:

```bash
# Add "case00000000" as placeholder for unknown cases
for file in /tmp/must-gather-archives/*-must-gather.tar.gz-*; do
  if [[ ! "$file" =~ -case[0-9]+ ]]; then
    newfile=$(echo "$file" | sed 's/-must-gather/-case00000000-must-gather/')
    mv "$file" "$newfile"
    echo "Renamed: $(basename $file) -> $(basename $newfile)"
  fi
done
```

## Best Practices

### 1. Use Descriptive Cluster Names

```yaml
# Good: Specific and identifiable
cluster_name: "prod-ocp-east-01"
cluster_name: "staging-ocp-west-02"

# Bad: Generic and ambiguous
cluster_name: "cluster"
cluster_name: "ocp"
```

### 2. Validate Case Numbers

Ensure `rh_case` variable is set correctly:

```yaml
# Good: Valid Red Hat case number
rh_case: "03123456"

# Bad: Will create confusing filenames
rh_case: ""
rh_case: "unknown"
```

### 3. Document Case-to-Incident Mapping

Maintain external documentation mapping Red Hat cases to internal incident numbers:

```
Internal INC123456 → Red Hat case03123456 → Archives: *-case03123456-*
Internal INC789012 → Red Hat case03654321 → Archives: *-case03654321-*
```

### 4. Automated Correlation

Use the naming convention in automation:

```bash
#!/bin/bash
# Retrieve all archives for a given Red Hat case

CASE_NUMBER="$1"
ARCHIVE_DIR="/tmp/must-gather-archives"

if [ -z "$CASE_NUMBER" ]; then
  echo "Usage: $0 <case_number>"
  exit 1
fi

echo "Finding archives for case $CASE_NUMBER..."
ls -lht "$ARCHIVE_DIR" | grep "case$CASE_NUMBER"
```

## Related Documentation

- `ARCHIVE_PRESERVATION.md` - Complete archive preservation documentation
- `README_CONDENSE.md` - Role usage and configuration
- `QUICK_REFERENCE.md` - Quick reference for operators

