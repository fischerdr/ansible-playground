# Ansible Skill

**Trigger**: Use this skill when developing, reviewing, or maintaining Ansible roles,
playbooks, custom modules, or filter plugins in this enterprise AAP project.

**Scope**: Ansible roles, playbooks, task files, custom Python modules within
`roles/*/library/`, filter plugins within `roles/*/filter_plugins/`, Vault integration
patterns, Kubernetes/OpenShift automation via Ansible, and AAP/AWX integration.
Does not cover standalone Python scripts in `scripts/`.

---

## Execution Environment Boundary

All Python and Ansible tooling MUST execute from `.venv/bin/`. System Python and
system Ansible are not supported.

```bash
.venv/bin/ansible-playbook
.venv/bin/ansible-lint
.venv/bin/ansible-galaxy
.venv/bin/python
.venv/bin/black && .venv/bin/isort && .venv/bin/flake8
```

Container runtime: Podman only. Python: 3.11 only.

---

## Non-Negotiable Rules

**1. FQCN on every module — no exceptions**

```yaml
# Correct
ansible.builtin.file:
kubernetes.core.k8s:
community.hashi_vault.vault_read:

# Never
file:
k8s:
```

**2. Never use oc/kubectl in shell for Kubernetes operations**

```yaml
# Never
- shell: oc get pods -n {{ namespace }}

# Always
- kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: "{{ namespace }}"
```

Exception: only with explicit user confirmation and justification.

**3. Orchestrator pattern — tasks/main.yml delegates only**

```yaml
# Correct — main.yml is a phase map, nothing else
- name: "Phase 1: Preflight"
  ansible.builtin.import_tasks: preflight.yml
  tags: [always, preflight]

# Never — no logic in main.yml
- name: Do something
  shell: some command
```

**4. block/rescue/always for all critical operations**

**5. changed_when/failed_when on every shell/command task**

```yaml
# Read-only
changed_when: false

# State change detected by output
changed_when: "'created' in result.stdout"

# Grep and similar
failed_when: result.rc not in [0, 1]
```

**6. No emojis anywhere — documentation, commits, task names**

**7. No oc/kubectl attribution in git commits**

---

## Quality Gates — Run After Every Change

```bash
# Ansible content
.venv/bin/ansible-lint roles/<role_name>/
.venv/bin/yamllint roles/<role_name>/

# Python modules/filters
.venv/bin/isort roles/<role_name>/library/
.venv/bin/black roles/<role_name>/library/
.venv/bin/flake8 roles/<role_name>/library/
.venv/bin/mypy roles/<role_name>/library/
```

Fix all issues before presenting output to user.

---

## Role Structure Pattern

```text
roles/<role_name>/
├── defaults/main.yml       # All overridable defaults
├── vars/main.yml           # Role-internal constants
├── tasks/
│   ├── main.yml            # Orchestrator only — phase delegation
│   ├── preflight.yml       # Validation before changes
│   ├── <phase>.yml         # One file per workflow phase
│   └── cleanup.yml         # Always runs
├── handlers/main.yml
├── templates/              # Jinja2 templates
├── files/                  # Static files
├── library/                # Custom Python modules
├── filter_plugins/         # Custom Jinja2 filters
├── meta/main.yml
└── README.md               # Authoritative role reference
```

---

## Reference Map — Load When Needed

| Topic | Reference |
|-------|-----------|
| Daily standards quick reference | `references/ANSIBLE-DEVELOPMENT-STANDARDS.md` |
| Kubernetes/OpenShift patterns | `references/KUBERNETES-PATTERNS.md` |
| Deep examples and case studies | `references/COMPREHENSIVE-GUIDE.md` |
| Custom modules and filter plugins | `references/ANSIBLE-ROLE-STANDARDS.md` |
| Tags usage and conventions | `references/Ansible_Tags_Usage_Guide.md` |
| Vault security integration | `references/SecurityGuidelinesvault.md` |
| Vault migration patterns | `references/VaultSecurityMigrationGuide.md` |
| Role development workflow | `references/ANSIBLE-ROLE-DEVELOPMENT-WORKFLOW.md` |
| Role distribution and packaging | `references/ansible-role-development-pattern.md` |
| Code review process | `references/CODE-REVIEW-CHECKLIST.md` |
| PR template | `references/PR-TEMPLATE.md` |
| Team migration guide | `references/MIGRATION-GUIDE.md` |
| Markdown linting rules | `references/MARKDOWN_STANDARDS.md` |
| AI agent code standards | `references/AGENTS.md` |
| Development methodology | `references/DEVELOPMENT_STANDARDS.md` |

Load the specific reference for the task at hand. Do not load all references by default.
