# Portworx Version Files

This directory contains version files that define the component images for specific Portworx releases.

## Obtaining Version Files

Version files must be downloaded from the Portworx installation service for your target version and Kubernetes version.

### Download Command

```bash
export PXVER=3.5.0
export KBVER=$(oc version | awk '/Server Version/ {print $3}')
curl -o versions-${PXVER} "https://install.portworx.com/$PXVER/version?kbver=$KBVER"
```

### Example

```bash
# For Portworx 3.5.0 on OpenShift 4.18
export PXVER=3.5.0
export KBVER=4.18.0
curl -o versions-3.5.0 "https://install.portworx.com/3.5.0/version?kbver=4.18.0"
```

## File Format

Version files are YAML documents containing:

- `version`: The Portworx version (e.g., "3.5.0")
- `components`: A dictionary of component names to container image references

Example:

```yaml
version: 3.5.0
components:
  stork: openstorage/stork:25.5.0
  autopilot: portworx/autopilot:1.3.18
  # ... additional components
```

## Usage in Role

The role uses these version files to update the `px-versions` ConfigMap in the portworx namespace:

1. Role variable `portworx_target_version` is set (e.g., "3.5.0")
2. Role looks for `files/versions/versions-{{ portworx_target_version }}`
3. ConfigMap `px-versions` is deleted and recreated with content from version file
4. Portworx operator uses this ConfigMap to determine component images during upgrade

## Required Version Files

Place version files in this directory following the naming convention:

- `versions-3.4.0.1` - For Portworx 3.4.0.1
- `versions-3.5.0` - For Portworx 3.5.0
- `versions-3.6.0` - For Portworx 3.6.0

## Notes

- Version files are specific to both Portworx version AND Kubernetes version
- Always download fresh version files for your target environment
- Do not manually edit version files (component versions are validated by Portworx)
