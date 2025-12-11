# Changelog

All notable changes to the Portworx Upgrade role will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-11

### Added

- Initial release of Portworx Upgrade role
- Comprehensive preflight validation (environment, nodes, pods, cluster, STC config)
- Operator-controlled rolling upgrade monitoring
- Dual timeout strategy (35min global inactivity, 25min per-pod)
- Impatient mode for accelerated storageless node upgrades
- Batch deletion support (configurable 3-10 pods per batch)
- Real-time pod image tracking via Kubernetes API
- Detailed upgrade summary reporting
- Tag-based selective execution (preflight, backup, upgrade, monitor, validate, report)
- Custom pxctl_status module for health checks
- Version file structure for target version mappings
- Complete AAP/AWX import configurations
- Automated AAP import script
- Three job templates (full upgrade, preflight, impatient mode)
- Workflow template with approval gates
- Comprehensive documentation (README, INSTALL, examples)

### Features

- **Preflight Validation**:
  - Environment validation (kubeconfig, namespace, permissions)
  - Node validation (Ready status, resource capacity)
  - Pod validation (Running status, version detection)
  - Cluster status validation (PX operational, KVDB health)
  - StorageCluster configuration validation (updateStrategy)

- **Upgrade Execution**:
  - Operator subscription channel update
  - Install plan approval automation
  - ConfigMap (px-versions) update
  - StorageCluster autoUpdateComponents patch
  - StorageCluster image update trigger

- **Monitoring**:
  - Kubernetes API-based pod image tracking
  - Activity detection (Terminating/Pending/ContainerCreating states)
  - Stuck upgrade detection with dual timeouts
  - Impatient mode batch processing
  - Safety validation between batches

- **Validation and Reporting**:
  - Final pod status validation
  - Cluster health verification
  - Version consistency checks
  - Detailed upgrade summary with timing and pod counts

- **AAP/AWX Integration**:
  - Project configuration with SCM settings
  - Execution environment definition
  - Job templates with comprehensive surveys (7 questions for full upgrade)
  - Workflow template with preflight -> approval -> upgrade flow
  - Automated import script using AWX CLI

### Technical Highlights

- Inline shell processing for pxctl commands (handles 500+ node clusters)
- No direct pod lifecycle management (monitors operator-controlled upgrades)
- Storage node validation before storageless pod acceleration
- Resource backup before upgrade (StorageCluster CRD)
- Configurable work directory for reports and logs
- Optional detailed logging mode
- Support for skipping operator upgrade phase

### Documentation

- Complete README with features, requirements, and examples
- Detailed INSTALL guide with multiple installation methods
- AAP import README with automated and manual procedures
- Inline role documentation in defaults/main.yml
- Version file structure documentation
- Example playbook included

### Requirements

- Ansible Core 2.12+
- Python 3.9+
- kubernetes.core collection >= 2.3.0
- OpenShift 4.18+
- Cluster admin permissions

### Known Limitations

- Impatient mode only for storageless nodes (by design)
- Requires operator-based Portworx deployment
- STC updateStrategy must be RollingUpdate
- KVDB pods treated as regular pods (no separate version tracking)

### Configuration

50+ configurable variables including:
- Target version (required)
- Namespace, cluster name
- Timeout values (global, per-pod)
- Impatient mode settings (enable, batch size)
- Logging and work directory paths
- Operator upgrade skip option

## [Unreleased]

### Planned

- Support for additional upgrade strategies
- Enhanced KVDB upgrade handling
- Prometheus metrics export
- Slack/Teams notification integration
- Multi-cluster upgrade orchestration
- Upgrade rollback automation

---

## Release Notes

### Version 1.0.0

This is the first production-ready release of the Portworx Upgrade role. It has been tested with:

- Portworx versions: 3.4.0.1 -> 3.5.0
- OpenShift versions: 4.18
- Cluster sizes: Up to 500 nodes
- Deployment modes: Operator-based installations

The role prioritizes safety and observability over speed, with multiple validation layers and comprehensive reporting.

### Upgrade Path

Not applicable for initial release.

Future versions will document upgrade procedures and breaking changes here.
