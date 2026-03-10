# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Quick Start

**CRITICAL:** Before doing anything, read these documents:

1. [ANSIBLE-DEVELOPMENT-STANDARDS.md](ANSIBLE-DEVELOPMENT-STANDARDS.md) - Core standards
2. [AGENTS.md](AGENTS.md) - AI agent guidelines
3. This document - Claude-specific instructions

---

## Repository Overview

This is an enterprise Ansible Automation Platform (AAP) project for managing Kubernetes clusters, HashiCorp Vault integration, and Portworx backup operations. All automation is executed through Ansible Automation Platform using Execution Environments (EEs) only.

**Key Technologies:**

- Ansible Core 2.18.4
- Python 3.11
- Kubernetes/OpenShift
- HashiCorp Vault
- Portworx Backup (via purepx.px_backup collection)
- Docker/Podman container runtime (required)

**Key Documentation:**

- `ANSIBLE-DEVELOPMENT-STANDARDS.md` - Daily reference
- `docs/ansible/COMPREHENSIVE-GUIDE.md` - Detailed examples
- `docs/ansible/MIGRATION-GUIDE.md` - Team transition plan
- `docs/ansible/KUBERNETES-PATTERNS.md` - K8s automation patterns
- `docs/ansible/CODE-REVIEW-CHECKLIST.md` - Review process
- `AGENTS.md` - AI agent standards

---

## Claude-Specific Workflow

### Before Making Any Changes

**1. Read Relevant Documentation**

```bash
# Always start by reading:
view ANSIBLE-DEVELOPMENT-STANDARDS.md
view AGENTS.md

# For specific topics:
view docs/ansible/KUBERNETES-PATTERNS.md  # For K8s work
view docs/ansible/COMPREHENSIVE-GUIDE.md  # For complex patterns
```

**2. Read Existing Code**

```bash
# Examine similar files to understand patterns
view roles/<similar_role>/tasks/main.yml
view roles/<similar_role>/defaults/main.yml

# Check existing playbooks
view playbooks/<similar_playbook>.yml
```

**3. Understand Current State**

```bash
# Check file structure
view roles/
view playbooks/

# Read configuration
view ansible.cfg
view requirements.yml
```

### When Creating New Code

**Step-by-step process:**

```text
1. READ EXISTING PATTERNS
   view roles/existing_role/  # Study structure
   
2. READ STANDARDS
   view ANSIBLE-DEVELOPMENT-STANDARDS.md  # Verify requirements
   
3. EXPLAIN APPROACH
   "I'll create a role following the orchestrator pattern because..."
   
4. GENERATE CODE
   [Follow standards exactly]
   
5. VALIDATE
   [Check against standards mentally]
   
6. CREATE FILES
   create_file for each file needed
   
7. RUN QUALITY CHECKS
   bash_tool: .venv/bin/ansible-lint roles/new_role/
```

### When Modifying Existing Code

**Step-by-step process:**

```text
1. READ CURRENT CODE
   view <file_to_modify>
   
2. UNDERSTAND CONTEXT
   view related files if needed
   
3. EXPLAIN CHANGES
   "I'll modify X to do Y because..."
   
4. SHOW BEFORE/AFTER
   "Current code: [show snippet]"
   "Updated code: [show changes]"
   
5. MAKE CHANGES
   str_replace to modify files
   
6. VALIDATE
   bash_tool: .venv/bin/ansible-lint <file>
```

---

## Critical Rules for Claude

### Rule 1: ALWAYS Use FQCN

```yaml
# CORRECT - Claude should ALWAYS generate this
- name: Create directory
  ansible.builtin.file:
    path: /tmp/work
    state: directory

# WRONG - Claude should NEVER generate this
- name: Create directory
  file:  # Missing FQCN - FORBIDDEN
    path: /tmp/work
    state: directory
```

**Enforcement:** Every Ansible module Claude generates MUST have FQCN.

### Rule 2: NEVER Use oc/kubectl in Shell

```yaml
# WRONG - Claude should NEVER generate this
- name: Get pods
  shell: oc get pods -n {{ namespace }}
  register: pods

# CORRECT - Claude should ALWAYS use modules
- name: Get pod information
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: "{{ namespace }}"
  register: pods
```

**Exception:** Only if explicitly justified and user confirms.

### Rule 3: ALWAYS Include Error Handling

```yaml
# CORRECT - Claude should ALWAYS generate this for critical operations
- name: Critical operation
  block:
    - name: Execute operation
      kubernetes.core.k8s:
        definition: "{{ resource }}"
  
  rescue:
    - name: Handle failure
      debug:
        msg: "Failed: {{ ansible_failed_result.msg }}"
  
  always:
    - name: Cleanup
      file:
        path: /tmp/work
        state: absent
```

### Rule 4: Use Orchestrator Pattern for tasks/main.yml

```yaml
# CORRECT - tasks/main.yml should ONLY orchestrate
---
- name: "Phase 1: Preflight"
  ansible.builtin.import_tasks: preflight.yml
  tags: [always, preflight, my_role]

- name: "Phase 2: Execute"
  ansible.builtin.import_tasks: execute.yml
  tags: [execution, my_role]

# WRONG - Claude should NEVER put logic in main.yml
---
- name: Do something
  shell: some command
  
- name: Do another thing
  file: ...
```

### Rule 5: Meaningful Task Names

```yaml
# CORRECT
- name: Ensure application configuration directory exists with correct permissions
- name: Wait for deployment to reach ready state with all replicas available
- name: Verify cluster connectivity before beginning upgrade operations

# WRONG - Claude should NEVER generate these
- name: Create dir
- name: Wait
- name: Check
```

---

## Development Commands

### Python Environment

**CRITICAL:** Always use the Python virtual environment located at `/development/git/ansible-playground/.venv`

```bash
# Activate virtual environment
source .venv/bin/activate

# Verify you're using the correct Python
which python  # Should show: /development/git/ansible-playground/.venv/bin/python
```

All Python commands, pip installations, and tool executions MUST be run using the virtual environment.

### Setup and Installation

```bash
# Install Python dependencies (using venv)
.venv/bin/python -m pip install -r requirements.txt

# Install Ansible collections
.venv/bin/ansible-galaxy collection install -r requirements.yml

# Build execution environment
chmod +x build.sh
./build.sh
```

### Testing and Quality

**Claude should ALWAYS run these after generating code:**

```bash
# Ansible-specific linting
.venv/bin/ansible-lint roles/<role_name>/

# YAML linting
.venv/bin/yamllint roles/<role_name>/

# Syntax check
.venv/bin/ansible-playbook --syntax-check playbooks/<playbook>.yml

# Python quality (if custom modules)
.venv/bin/black roles/<role_name>/library/
.venv/bin/isort roles/<role_name>/library/
.venv/bin/flake8 roles/<role_name>/library/
```

**After generating code, Claude should:**

1. Run ansible-lint
2. Fix any issues found
3. Run again until clean
4. Report results to user

---

## Architecture

### Directory Structure

- `roles/` - Reusable Ansible roles
  - `common/` - Shared functionality
  - `defrag_etcd_db/` - etcd defragmentation for OpenShift
  - `deploy_px/` - Portworx deployment
  - `must_gather_log/` - Log collection and Red Hat case management
  - `portworx_upgrade/` - **NEW** - Automated Portworx upgrades
  - `pxbackup/` - Portworx backup operations
  - `setup_env/` - Environment setup
  - `upgrade_clusters/` - Cluster upgrade automation
  - `vault_multi_namespace_monitor/` - Multi-namespace Vault monitoring
  - `vault_fix_portworx/` - Vault integration fixes

- `playbooks/` - Orchestration playbooks
- `docs/` - All documentation (README files, guides)
- `scripts/` - Utility scripts
- `aap_import/` - AAP/AWX import configurations

**Documentation placement:**

- Role-specific: `docs/<role_name>/`
- General: `docs/` root
- Project root: Only `CLAUDE.md`, `README.md`, `ANSIBLE-DEVELOPMENT-STANDARDS.md`, `AGENTS.md`

### Custom Modules

Custom modules live in `roles/<role_name>/library/` and must follow Ansible 2.18+ standards with:

- Complete DOCUMENTATION
- EXAMPLES section
- RETURN value documentation
- Type hints (Python 3.11+)
- Proper argument specs

---

## Coding Standards

### Ansible Best Practices

**Required conventions Claude MUST follow:**

```yaml
# 1. FQCN everywhere
ansible.builtin.<module>
kubernetes.core.<module>

# 2. Descriptive task names
- name: "Action verb + what + context"

# 3. Proper boolean values
true/false  # NOT True/False, YES/NO

# 4. changed_when/failed_when for shell/command
- name: Read-only operation
  shell: command
  changed_when: false
  failed_when: result.rc != 0

# 5. Error handling
block:
  - main tasks
rescue:
  - error handling
always:
  - cleanup
```

### Kubernetes-Specific Standards

**Claude should ALWAYS prefer modules over shell:**

```yaml
# Command translations Claude should automatically apply:

# oc get pods → kubernetes.core.k8s_info
# oc apply → kubernetes.core.k8s
# oc delete → kubernetes.core.k8s: state: absent
# oc scale → kubernetes.core.k8s with definition
# oc rsh → kubernetes.core.k8s_exec
```

**Reference:** `docs/ansible/KUBERNETES-PATTERNS.md` for complete examples.

### Python Standards

**Claude-generated Python code must have:**

```python
# 1. Type hints
def function_name(param: str, count: int = 5) -> List[str]:
    pass

# 2. Docstrings
"""
Brief description.

Args:
    param: Description
    count: Description

Returns:
    Description
"""

# 3. Specific exceptions
try:
    operation()
except SpecificException as e:
    handle(e)
# NOT: except:

# 4. Following PEP 8
# Use black, isort, flake8
```

---

## Documentation Standards

### No Emojis

**CRITICAL:** Claude must NEVER use emojis in any generated code, documentation, or commit messages.

```markdown
# WRONG - NEVER generate emojis
## 🚀 Quick Start
- ✅ Feature 1
- ❌ Bad pattern

# CORRECT - Professional tone
## Quick Start
- Feature 1
- Avoid this pattern
```

**Exception:** Only in summary documents explicitly marked as internal/team communication.

### Code Block Languages

**All code blocks MUST specify language:**

```markdown
# CORRECT - Claude should always generate this
\`\`\`yaml
- name: Example
\`\`\`

\`\`\`python
def example():
    pass
\`\`\`

# WRONG - Claude should NEVER omit language
\`\`\`
- name: Example
\`\`\`
```

### README Structure

**When creating README.md, Claude should use this structure:**

```markdown
# Role/Playbook Name

## Description
Brief purpose description

## Requirements
- Ansible version
- Collections
- Prerequisites

## Role Variables
### Required
| Variable | Type | Description |
|----------|------|-------------|

### Optional
| Variable | Type | Default | Description |
|----------|------|---------|-------------|

## Example Playbook
\`\`\`yaml
Example usage
\`\`\`

## License
```

---

## Claude Workflow Examples

### Example 1: Creating a New Role

```text
User: "Create a new role for backing up etcd"

Claude's process:

1. READ EXISTING PATTERNS
   view roles/defrag_etcd_db/  # Similar role
   view ANSIBLE-DEVELOPMENT-STANDARDS.md

2. EXPLAIN APPROACH
   "I'll create a role following these patterns:
   - Orchestrator pattern in tasks/main.yml
   - Preflight validation
   - Error handling with block/rescue/always
   - Variable naming: etcd_backup_*"

3. CREATE ROLE STRUCTURE
   create_file roles/etcd_backup/README.md
   create_file roles/etcd_backup/defaults/main.yml
   create_file roles/etcd_backup/tasks/main.yml
   create_file roles/etcd_backup/tasks/preflight.yml
   create_file roles/etcd_backup/tasks/execute.yml
   create_file roles/etcd_backup/meta/main.yml

4. VALIDATE
   bash_tool: .venv/bin/ansible-lint roles/etcd_backup/

5. FIX ISSUES (if any)
   str_replace to fix issues found

6. REPORT
   "Role created successfully. Structure follows project standards.
   Next steps: [testing recommendations]"
```

### Example 2: Converting oc Command to Module

```text
User: "Convert this to use proper modules"
[Shows: shell: oc get pods]

Claude's process:

1. IDENTIFY PATTERN
   "This is using shell command instead of kubernetes.core.k8s_info"

2. CHECK DOCUMENTATION
   view docs/ansible/KUBERNETES-PATTERNS.md

3. SHOW CONVERSION
   "Converting from shell to native module:
   
   Before:
   - shell: oc get pods -n {{ namespace }}
   
   After:
   - kubernetes.core.k8s_info:
       api_version: v1
       kind: Pod
       namespace: "{{ namespace }}"
   
   Benefits:
   - Structured data instead of text parsing
   - Idempotent and reliable
   - Can access any pod field"

4. APPLY CHANGE
   str_replace to make the change

5. VALIDATE
   bash_tool: .venv/bin/ansible-lint <file>
```

### Example 3: Adding Error Handling

```text
User: "Add proper error handling to this task"

Claude's process:

1. READ CURRENT CODE
   view <file>

2. IDENTIFY SCOPE
   "This is a critical operation that needs:
   - Pre-validation
   - Error recovery
   - Cleanup"

3. SHOW PATTERN
   "Adding block/rescue/always pattern:
   
   block:
     - Pre-check
     - Main operation
     - Verification
   rescue:
     - Collect diagnostics
     - Attempt recovery
   always:
     - Cleanup temporary resources"

4. IMPLEMENT
   str_replace to wrap in block/rescue/always

5. VALIDATE
   bash_tool: .venv/bin/ansible-lint <file>
```

---

## Git Commit Messages

**IMPORTANT:** Do NOT add Claude Code attribution or co-authorship to commit messages.

```text
# WRONG - Claude should NEVER generate this
feat: Add new feature

Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>

# CORRECT - Clean, descriptive commit
feat: Replace oc commands with kubernetes.core modules

Converted shell commands to native Kubernetes modules in cluster_setup role
for better reliability and maintainability.
```

---

## Quality Assurance Checklist

**Before completing any task, Claude should verify:**

### Ansible Code

- [ ] All modules use FQCN
- [ ] Task names are descriptive
- [ ] No oc/kubectl in shell (unless justified)
- [ ] shell/command have changed_when/failed_when
- [ ] Critical operations have error handling
- [ ] Variables follow naming convention
- [ ] Documentation updated

### Python Code

- [ ] Type hints on all functions
- [ ] Docstrings present
- [ ] Specific exception handling
- [ ] Follows PEP 8
- [ ] Passes black, isort, flake8

### Documentation

- [ ] Code blocks specify language
- [ ] No emojis
- [ ] Professional tone
- [ ] Complete examples
- [ ] README structure followed

### Testing

- [ ] ansible-lint passes
- [ ] yamllint passes
- [ ] Syntax check passes
- [ ] Python quality checks pass (if applicable)

---

## Common Pitfalls for Claude

### Pitfall 1: Not Reading Existing Code

```text
WRONG: Generate code based on general knowledge
RIGHT: 
1. view existing similar code
2. Identify patterns used
3. Match those patterns exactly
```

### Pitfall 2: Using Shell Commands for K8s

```text
WRONG: shell: oc get pods
RIGHT: kubernetes.core.k8s_info: kind: Pod

Exception: Only if no module exists AND user confirms
```

### Pitfall 3: Missing Error Handling

```text
WRONG: Just the main operation task
RIGHT: block/rescue/always for critical operations
```

### Pitfall 4: Not Running Quality Checks

```text
WRONG: Generate code and present it
RIGHT:
1. Generate code
2. Run ansible-lint
3. Fix issues
4. Run again
5. Present clean code
```

### Pitfall 5: Assuming File Locations

```text
WRONG: "I'll update roles/myapp/tasks/main.yml"
RIGHT: 
1. view roles/myapp/tasks/main.yml  # Verify exists
2. Read content
3. Make changes
```

---

## Integration with Documentation

### Quick Reference Mapping

**When user asks about:**

| Topic | Reference Document |
|-------|-------------------|
| Quick standards lookup | ANSIBLE-DEVELOPMENT-STANDARDS.md |
| Detailed examples | docs/ansible/COMPREHENSIVE-GUIDE.md |
| K8s automation | docs/ansible/KUBERNETES-PATTERNS.md |
| Team migration | docs/ansible/MIGRATION-GUIDE.md |
| Code review | docs/ansible/CODE-REVIEW-CHECKLIST.md |
| AI guidelines | AGENTS.md |

**Claude should suggest relevant documents:**

```text
User: "How do I monitor an operator-controlled upgrade?"

Claude: "Let me check the Kubernetes patterns guide..."
view docs/ansible/KUBERNETES-PATTERNS.md
[Find operator section]
"According to the KUBERNETES-PATTERNS.md documentation, 
operator-controlled upgrades should use the monitoring pattern..."
[Provide example from documentation]
```

---

## Special Cases

### Current Project: Portworx Upgrade Role

**When working on `roles/portworx_upgrade/`:**

1. Read specification: `docs/portworx_upgrade/portworx_upgrade-role-final.md`
2. Key requirements:
   - Operator-controlled (monitor, don't control)
   - Dual timeout (35min global, 25min per pod)
   - Monitor `spec.containers[0].image` changes
   - Validate STC updateStrategy first
   - autoUpdateComponents before image update

3. Implementation order:
   - Structure and variables
   - Preflight validation
   - Upgrade trigger
   - Monitoring tasks
   - Validation and reporting

### Multi-Cluster Operations

**Pattern to follow:**

```yaml
- name: Multi-cluster operation
  hosts: k8s_clusters
  serial: 1  # One at a time
  gather_facts: false
  
  tasks:
    - name: Verify connectivity
      kubernetes.core.k8s_cluster_info:
    
    - name: Execute operation
      # ... operation tasks
```

### Custom Module Development

**When creating custom modules:**

1. Check if module already exists
2. Use `roles/<role_name>/library/<module_name>.py`
3. Follow Ansible module standards
4. Include DOCUMENTATION, EXAMPLES, RETURN
5. Add type hints
6. Write tests

---

## Summary

**Core principles Claude must follow:**

1. **Read first, generate second** - Always examine existing code
2. **Follow standards exactly** - ANSIBLE-DEVELOPMENT-STANDARDS.md is law
3. **Use native modules** - Avoid shell commands for K8s
4. **Include error handling** - block/rescue/always for critical ops
5. **Run quality checks** - ansible-lint before presenting code
6. **Document everything** - Code, README, CHANGELOG
7. **No emojis** - Professional tone always
8. **Explain changes** - What, why, how

**When in doubt:**

1. Read AGENTS.md
2. Read ANSIBLE-DEVELOPMENT-STANDARDS.md
3. Check docs/ansible/ for specific patterns
4. Ask user for clarification

---

**Document Version:** 2.0.0  
**Last Updated:** 2025-02-10  
**Previous Version:** 1.0.0 (basic repository guide)
**This Version:** Complete integration with Ansible standards documentation

**Maintained By:** Platform Engineering Team
