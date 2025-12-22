# Changelog

All notable changes to the Portworx Upgrade role will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-12-21

### Added

- Phase 7 Validation Enhancements:
  - Storage pool health validation module (`tasks/validate/storage_pool_health.yml`)
  - Volume health validation module (`tasks/validate/volume_health.yml`)
  - StorageCluster conditions analysis module (`tasks/validate/stc_conditions.yml`)
  - Node statistics validation module (`tasks/validate/node_statistics.yml`)
- Integration testing suite with 17+ test cases
- JSON reporting capability (`tasks/report/generate_detailed_json.yml`)
- Comprehensive integration test suite:
  - Storage pool health tests (4 test cases)
  - Volume health tests (6 test cases)
  - STC conditions tests (6 test cases)
  - Node statistics tests (1 test case)
  - Master test runner script (`tests/integration/run_validation_tests.sh`)

### Enhanced

- Validation modules now use specialized parsing strategies:
  - JSON parsing for storage pool provision status
  - Text parsing with regex for volume lists
  - Kubernetes API queries for StorageCluster conditions
  - IP-based node identification for statistics
- Enhanced upgrade summary template with detailed validation results
- Detailed troubleshooting guidance in all validation modules

### Fixed

- Critical volume health regex patterns (issue with "up - attached" format detection)
- Node statistics IP regex (simplified from full IPv4 pattern to flexible partial match)
- Validation logic for degraded volumes and storage pools

### Configuration

New validation configuration variables:

- `portworx_validation_fail_on_pool_issues: true` - Fail on degraded storage pools
- `portworx_validation_pool_capacity_threshold: 90` - Capacity warning threshold
- `portworx_validation_fail_on_down_volumes: true` - Fail on down volumes
- `portworx_validation_fail_on_degraded_volumes: true` - Fail on degraded volumes
- `portworx_validation_fail_on_stc_unavailable: false` - Fail on unavailable STC
- `portworx_create_json_report: false` - Generate machine-readable JSON report

### Documentation

- Added TESTING.md - Integration test suite documentation
- Added LAB_TESTING.md - Lab testing procedures and checklist
- Updated README.md with Phase 7 validation module details
- Updated all session context documentation

### Testing

- All integration tests passing (17+ test cases)
- Mock data validation for all parsing strategies
- Ansible-lint compliance verified
- Regex patterns validated with positive and negative test cases

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
