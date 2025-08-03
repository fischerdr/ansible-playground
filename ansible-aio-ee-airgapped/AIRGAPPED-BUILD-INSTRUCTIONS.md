# Air-gapped Build Instructions

## Prerequisites

1. Transfer this entire directory to your air-gapped environment
2. Ensure Docker or Podman is available
3. Ensure ansible-builder is installed

## Directory Structure

After running the preparation script, you should have:

```
├── context/                        # Build context
├── tools/                          # Binary tools
│   ├── kubectl
│   ├── helm
│   ├── terraform
│   ├── oc
│   ├── awscliv2.zip
│   └── google-cloud-sdk.tar.gz
├── wheels/                         # Python wheels (main requirements)
│   └── *.whl files
├── wheels-collections/             # Python wheels (collection dependencies)  
│   └── *.whl files
├── collections/                    # Ansible collections
│   └── ansible_collections/
├── ansible-aio-ee-airgapped.yml   # EE definition
├── requirements-airgapped.yml     # Collections requirements
├── requirements-airgapped.txt     # Python requirements (main)
├── requirements-collections-airgapped.txt  # Collection dependencies
└── build-airgapped-ee.sh          # Build script
```

## Building the EE

### Using ansible-builder (recommended)
```bash
ansible-builder build --file ansible-aio-ee-airgapped.yml --tag ansible-aio-ee-airgapped:latest
```

### Using Docker directly
```bash
docker build -f Containerfile.ansible-aio-ee-airgapped -t ansible-aio-ee-airgapped:latest .
```

## Testing

```bash
# Test the built image
docker run --rm ansible-aio-ee-airgapped:latest ansible --version
docker run --rm ansible-aio-ee-airgapped:latest kubectl version --client
docker run --rm ansible-aio-ee-airgapped:latest helm version
```

## Troubleshooting

1. **Missing tools**: Ensure all files in tools/ directory are present
2. **Permission errors**: Check that binary files in tools/ are executable
3. **Collection errors**: Verify collections are properly downloaded in collections/
4. **Python package errors**: Check that wheels are available in wheels/ and wheels-collections/
5. **Collection dependency errors**: Ensure requirements-collections-airgapped.txt was generated during preparation
6. **Offline build failures**: Verify all required wheels are present in both wheels directories

## Updating

To update tools or dependencies:
1. Run the preparation script again in an internet-connected environment:
   ```bash
   ./prepare-airgapped-build.sh --clean --update-collection-deps
   ```
2. Transfer the updated files to your air-gapped environment
3. Rebuild the EE

## Collection Dependency Management

This air-gapped EE now includes automatic collection dependency discovery:
- Collection dependencies are discovered during preparation phase
- Python wheels for collection dependencies are downloaded separately
- Dependencies are installed during EE build without internet access
- Ensures all collection modules have required Python packages
