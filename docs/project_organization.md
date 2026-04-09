# Project Organization

**Document Version:** 2.0
**Last Updated:** 2026-04-08
**Purpose:** Defines where things go and why — structure rules, naming conventions,
and the execution model. Not a role or playbook inventory; see `CLAUDE.md` for the
current role list.

---

## Execution Model

All automation runs inside Ansible Automation Platform (AAP) Execution Environments
(EEs). This is not optional — there is no direct host execution path.

Key constraints that flow from this:

- No assumptions about host-level tooling or Python installations
- All credentials retrieved from HashiCorp Vault at runtime
- EE filesystem is ephemeral — no persistent state between runs
- All dependencies must be declared in requirements files for reproducible EE builds
- Container runtime: Podman only
- Python: 3.11 only (Python 3.9 is explicitly removed from EE builds)

The EE build configuration lives in `Build-EE/`. The active EE definition is
`Build-EE/execution-environment.yml`. See `docs/execution-environment.md` for
full dependency and configuration reference.

---

## Top-Level Directory Rules

```text
roles/          One directory per role. No role logic outside this tree.
playbooks/      Orchestration playbooks only. Organized by functional area.
inventory/      Inventory files. group_vars/ and host_vars/ live here.
collections/    Local Ansible collections (not installed via galaxy).
Build-EE/       Execution Environment build definitions and scripts.
aap_import/     AAP/AWX import configurations per role. One subdir per role.
scripts/        Standalone utility scripts. Not executed by AAP.
docs/           All project documentation. See Documentation Layout below.
library/        Symlinks to custom modules for local dev/testing only.
                Authoritative module source lives in roles/*/library/.
```

Nothing goes at the repo root except configuration files, the top-level README,
CLAUDE.md, and build/test entry points.

---

## Role Structure

Every role follows this layout without exception:

```text
roles/<role_name>/
├── defaults/main.yml       # All variables that operators may override
├── vars/main.yml           # Role-internal constants, not for override
├── tasks/
│   ├── main.yml            # Orchestrator only — delegates to phase files
│   ├── preflight.yml       # Validation before any changes
│   ├── <phase>.yml         # One file per distinct workflow phase
│   └── cleanup.yml         # Cleanup — runs in always block
├── handlers/main.yml
├── templates/              # Jinja2 templates (.j2)
├── files/                  # Static files
├── library/                # Custom Python modules for this role
├── filter_plugins/         # Custom Jinja2 filter plugins
├── meta/main.yml           # Role metadata, dependencies
└── README.md               # Authoritative role reference — always current
```

`tasks/main.yml` contains only phase delegation via `import_tasks` or
`include_tasks`. No task logic belongs in main.yml.

`README.md` is the single authoritative reference for a role — what it does,
all variables, requirements, and example playbook. If a role has docs beyond
the README, they live in `docs/roles/<role_name>/`.

---

## Playbook Organization

Playbooks orchestrate roles. They do not contain task logic.

```text
playbooks/
├── <functional_area>/      # Subdirectory for related playbook groups
│   └── <name>.yml
├── tasks/                  # Shared task files reused across playbooks
├── vars/                   # Shared variable files
└── <name>.yml              # Top-level playbooks
```

Naming convention: `<technology>_<action>.yml` — e.g., `px_upgrade.yml`,
`vault_kv2_demo.yml`, `etcd_db_backup_aap.yml`.

Test playbooks are prefixed `test_` and live alongside the playbooks they test.

---

## AAP Import Structure

Each role that is deployed to AAP has a corresponding import directory:

```text
aap_import/
└── <role_name>/
    ├── README.md                     # Import guide for this role
    ├── import_to_aap.sh              # Automated import script
    ├── execution_environment.json    # EE configuration
    ├── project_*.json                # AAP project definition
    ├── job_template_*.json           # One file per job template
    ├── survey_spec_*.json            # Survey specs for runtime variables
    └── workflow_*.json               # Workflow templates (if applicable)
```

Never commit credentials to `aap_import/`. All credential references use AAP
credential types resolved at runtime.

---

## Documentation Layout

```text
.agents/                              # Agent/AI tooling configuration (repo root)
└── skills/
    └── ansible/
        ├── SKILL.md                  # Skill entry point and router
        └── references/               # Deep reference material

docs/
├── roles/
│   └── <role_name>/                  # Role-specific docs beyond README
├── archive/                          # Superseded or point-in-time docs
├── examples/                         # Code templates and reference examples
├── must-gather-log/                  # must_gather_log role distribution
├── portworx-pxbackup/                # PX-Backup product documentation
├── portworx_upgrade/                 # portworx_upgrade role documentation
├── execution-environment.md          # EE dependency and config reference
└── project_organization.md           # This file
```

Rules:

- Role documentation beyond the README goes in `docs/roles/<role_name>/`
- General standards and patterns go in `docs/.agents/skills/ansible/references/`
- `docs/archive/` holds superseded docs — they are not deleted, just retired
- The `docs/examples/` directory contains production-ready code templates
  referenced by CLAUDE.md; do not restructure without updating those references
- `CLAUDE.md` lives at the repo root only — not in `docs/`

---

## Naming Conventions

**Roles:** `snake_case` — e.g., `portworx_upgrade`, `vault_fix_portworx`

**Playbooks:** `<technology>_<action>.yml` in snake_case

**Variables:**

- Role defaults and vars: `<role_prefix>_<name>` — e.g., `px_upgrade_timeout`
- Group vars: descriptive, scoped to the group
- No single-letter variables, no unexplained abbreviations

**Custom modules:** `snake_case.py` in `roles/<role>/library/`

**Filter plugins:** `snake_case.py` in `roles/<role>/filter_plugins/`

**AAP import configs:** Follow `aap_import/portworx_upgrade/` as the reference
implementation.

---

## Dependency Management

| File | Purpose |
|------|---------|
| `requirements.yml` | Ansible collections for local dev |
| `requirements.txt` | Python packages for local dev |
| `requirements-dev.txt` | Dev-only Python packages |
| `Build-EE/*/requirements.yml` | Collections pinned for EE builds |
| `Build-EE/*/requirements.txt` | Python packages pinned for EE builds |

EE build requirements are separate from local dev requirements intentionally —
EE builds are reproducible artifacts and must be explicitly versioned.
