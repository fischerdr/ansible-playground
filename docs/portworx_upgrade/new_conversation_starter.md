# Portworx Upgrade Role - New Conversation Starter Prompt

Use this prompt to start a new conversation with full context:

---

I'm continuing work on an enterprise Ansible Automation Platform project for automated Portworx cluster upgrades on OpenShift 4.18. This is a production-ready role handling clusters from 25-300 nodes with comprehensive monitoring and optional acceleration.

## Current Status (95% Complete)

**Location:** `/development/git/ansible-playground`
**Branch:** `feature/portworx-upgrade` (6 commits ahead)
**Role:** `roles/portworx_upgrade/`
**All tests passing:** 7 suites, 36 tests total

## Recent Work Completed

### 1. Sliding Window Global Timeout (CRITICAL FIX)

Fixed critical bug where global timeout missed stuck pods in impatient mode due to completion-based reset logic. Implemented dual-mode timeout:

- **Mode 1 (active pods):** Sliding window based on oldest pod age (from creationTimestamp)
- **Mode 2 (no active pods):** Inactivity-based for operator stall detection
- **Active pods:** upgrading + new_not_ready (excludes old_image and upgraded)
- **Files:** detect_stuck_upgrade.yml, test_global_timeout_sliding_window.yml, monitoring-flow.md

**Test scenario that was failing:**

```text
Impatient mode: 5 pods deleted, 4 complete in <20min, 1 stuck at 39.5min
OLD: Timeout resets on each completion → NO FAILURE (bug)
NEW: Tracks oldest pod age → FAIL at 39.5min > 35min (correct)
```

### 2. Distribution Tarball Created

Clean, production-ready package at `docs/portworx_upgrade/portworx-upgrade-role-1.0.0.tar.gz`:

- 87 KB, 87 files (no cache directories)
- Complete role + comprehensive documentation
- Ready for standalone git repository

### 3. Documentation Sanitized

All sensitive information removed from docs:

- No internal hostnames, IPs, UUIDs
- No emojis or icons (project standard)
- Generic examples throughout

## Key Technical Details

**Three-Tier Timeout System:**

1. Per-pod: 15-25 minutes (pod creation to Running+Ready)
2. Global: 35 minutes (sliding window or inactivity-based)
3. Impatient mode: Multi-batch user-controlled acceleration

**Pod Classification (filter_plugins/pod_classifier.py):**

- `upgraded`: New image + Running + Ready
- `old_image`: Still on old version (excluded from sliding window)
- `upgrading`: New image in active phases (Terminating, Pending, ContainerCreating)
- `new_not_ready`: New image + Running but not Ready

**Timestamp Parsing (CRITICAL):**

- BROKEN: `to_datetime(...) | int` returns 0
- CORRECT: `((timestamp | to_datetime('%Y-%m-%dT%H:%M:%SZ')).strftime('%s')) | int`

## Role Structure (Production-Ready)

```text
roles/portworx_upgrade/
├── tasks/
│   ├── preflight/       ✓ 7 validation tasks
│   ├── upgrade/         ✓ 4 upgrade phases (operator, configmap, components, STC)
│   ├── monitor/         ✓ Automatic rolling upgrade with sliding window fix
│   ├── validate/        ✓ 4 final validation tasks
│   └── report/          ✓ Summary generation
├── filter_plugins/      ✓ Custom pod classifier with tests
├── tests/               ✓ 7 test suites (36 tests, all passing)
├── playbooks/           ✓ Example px_upgrade.yml
├── aap_import/          ✓ AAP/AWX integration configs
└── docs/                ✓ Comprehensive documentation (sanitized)
```

## Python Environment (CRITICAL)

All commands MUST use `.venv` at project root:

```bash
.venv/bin/ansible-playbook
.venv/bin/ansible-lint
.venv/bin/black
.venv/bin/pytest
```

## Important Files

**Monitoring (recent fixes):**

- `roles/portworx_upgrade/tasks/monitor/detect_stuck_upgrade.yml` - Sliding window logic
- `roles/portworx_upgrade/tasks/monitor/automatic_rolling_upgrade.yml` - Activity reset (KEPT for operator stall detection)
- `roles/portworx_upgrade/filter_plugins/pod_classifier.py` - Pod classification

**Documentation:**

- `docs/portworx_upgrade/monitoring-flow.md` - 837 lines, comprehensive monitoring docs
- `docs/portworx_upgrade/portworx-upgrade-role-final.md` - Complete specification
- `roles/portworx_upgrade/README.md` - 342 lines

**Tests:**

- `roles/portworx_upgrade/tests/run_all_tests.sh` - Runs all 7 test suites

## Coding Standards

- Ansible: FQCN, lowercase true/false, block/rescue/always, proper changed_when/failed_when
- Python: 3.11+, black/isort/flake8/mypy, 100 char lines, type hints
- Documentation: No emojis/icons, sanitize sensitive info, place in docs/ directory
- Version control: No Claude Code attribution in commits

## What Could Still Be Added (Optional)

- Custom module `library/pxctl_status.py` (currently using shell)
- Additional report templates
- Version-specific files in `files/versions/`

## Recent Commits (Unstaged Work)

Unstaged changes ready to commit:

- `docs/portworx_upgrade/portworx-upgrade-role-1.0.0.tar.gz` (updated)
- `docs/portworx_upgrade/portworx-upgrade-role-1.0.0.tar.gz.sha256` (updated)
- `docs/portworx_upgrade/portworx-upgrade-manual-v2.md` (sanitized)

Last 2 commits:

- `449cca9` - Enhance debug tests with negative scenario coverage
- `596f4da` - Implement sliding window global timeout for impatient mode

## Quick Commands

```bash
# Run all tests
cd roles/portworx_upgrade/tests && ./run_all_tests.sh

# Lint
.venv/bin/ansible-lint roles/portworx_upgrade/

# Run upgrade
ansible-playbook playbooks/px_upgrade.yml -e portworx_target_version=3.5.0
```

---

**Full context available in:** `docs/porrtworx_upgrade/conversation_summary_prompt.md`

**Ready for:** Production testing, AAP deployment, role distribution, or additional enhancements.
