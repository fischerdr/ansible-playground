# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is an enterprise Ansible Automation Platform (AAP) project for managing Kubernetes clusters, HashiCorp Vault integration, and Portworx backup operations. All automation is executed through Ansible Automation Platform using Execution Environments (EEs) only.

**Key Technologies:**

- Ansible Core 2.18.4
- Python 3.11
- Kubernetes/OpenShift
- HashiCorp Vault
- Portworx Backup (via purepx.px_backup collection)
- Docker/Podman container runtime (required)

## Current Project: Portworx Upgrade Role

**Active Development:** Creating a new role `roles/portworx_upgrade/` for automated Portworx cluster upgrades on OpenShift 4.18.

**Specification:** The complete specification is in `docs/portworx_upgrade/portworx_upgrade-role-final.md` at the repository root.

**Key Implementation Notes:**

- Operator-controlled rolling upgrade (role monitors, doesn't control)
- Two timeout mechanisms: 35min global inactivity, 25min per pod
- Monitor pod image field changes: `spec.containers[0].image`
- Impatient mode ONLY for storageless nodes
- STC updateStrategy validation required in preflight checks
- autoUpdateComponents patch before STC image update

**Implementation Order:**

1. Role structure and variables (defaults/main.yml, vars/main.yml)
2. Preflight validation tasks (nodes, pods, cluster status, STC config)
3. Upgrade trigger tasks (operator, configmap, update_components, storagecluster)
4. Monitoring tasks (automatic rolling upgrade, stuck detection, impatient mode)
5. Validation and reporting tasks

When working on this role, always reference the specification document for exact requirements.

## Development Commands

## Python and Ansible Execution Environment

### Authoritative Execution Boundary

**IMPORTANT:** All Python and Ansible tooling for this repository MUST execute from the project-local virtual environment located at `.venv` in the repository root. The virtual environment is the single supported runtime boundary for development, automation, and CI.

System Python, system Ansible, or globally installed tools are not supported.

### Virtual Environment Usage Model

The authoritative interpreters and binaries are those located under:

- `.venv/bin/python`
- `.venv/bin/pip`
- `.venv/bin/ansible`
- `.venv/bin/ansible-playbook`
- `.venv/bin/ansible-galaxy`

Shell activation (`source .venv/bin/activate`) is permitted for interactive developer workflows, but correctness is defined by the resolved binary path, not shell state. Scripts, automation, and CI pipelines MUST invoke tools explicitly from `.venv/bin/`.

### Initial Environment Setup

If the virtual environment does not exist, create it using the provided setup script:

```bash
# Unix / Linux / macOS
./setup.sh

# Windows
setup.bat
````

This step is mandatory before running any Python or Ansible commands.

### Dependency and Tool Installation

All dependency installation must be performed using the virtual environment:

```bash
# Install Python dependencies
.venv/bin/python -m pip install -r requirements.txt

# Install Ansible collections
.venv/bin/ansible-galaxy collection install -r requirements.yml

# Build the execution environment artifact
chmod +x build.sh && ./build.sh
```

No dependency installation is permitted outside `.venv`.

### Running Python Code

All Python execution MUST use the virtual environment interpreter:

```bash
.venv/bin/python src/dialogs/about_dialog.py
.venv/bin/python tools/extract_dfm_images.py delphi-source/forms/fmAbout.dfm
```

### Linting, Testing, and Quality Gates

All quality and verification tools MUST be executed from `.venv/bin/`.

Available tools include:

- `black`
- `isort`
- `flake8`
- `mypy`
- `pytest`
- `tox`
- `ansible-lint`
- `yamllint`

When modifying files, the following checks are required:

- Python files (`.py`, custom modules under `roles/*/library/`, filter plugins under `roles/*/filter_plugins/`):

  - `black`
  - `isort`
  - `flake8`

- Ansible content (playbooks, roles, tasks, handlers):

  - `ansible-lint`

Local execution is expected to match CI behavior.

### Running Ansible Playbooks

All Ansible commands MUST resolve to binaries under `.venv/bin/`.

```bash
# Basic execution
.venv/bin/ansible-playbook -i inventory/<inventory-file> playbooks/<playbook-name>.yml

# Validation and inspection
.venv/bin/ansible-playbook --syntax-check <playbook>.yml
.venv/bin/ansible-playbook -i <inventory> <playbook>.yml --check
.venv/bin/ansible-playbook -i <inventory> <playbook>.yml --diff
.venv/bin/ansible-playbook -i <inventory> <playbook>.yml -vvv
```

Any deviation from this execution model is considered unsupported and may lead to non-reproducible behavior.

### Role Testing Workflow

1. **Syntax validation**: `ansible-playbook --syntax-check playbooks/<playbook>.yml`
2. **Ansible-lint**: `.venv/bin/ansible-lint roles/<role-name>/`
3. **Tag-based testing**: `ansible-playbook playbooks/px_upgrade.yml --tags preflight --check`
4. **Dry-run mode**: Use `--check` to validate without changes
5. **Test environment**: Run against dev/test cluster first
6. **Production validation**: Final testing in production-like environment

## Architecture

### Directory Structure

- **`roles/`**: Reusable Ansible roles (common, defrag_etcd_db, deploy_px, must_gather_log, portworx_upgrade, pxbackup, setup_env, upgrade_clusters, vault_multi_namespace_monitor, vault_fix_portworx)
- **`playbooks/`**: Orchestration playbooks
- **`Build-EE/`**: Execution environment build configuration
- **`collections/`**: Local Ansible collections
- **`inventory/`**: Inventory files with `group_vars/` and `host_vars/`
- **`scripts/`**: Utility scripts
- **`aap_import/`**: AAP/AWX import configurations for roles (see [aap_import/README.md](aap_import/README.md))

### Custom Modules

The project includes custom Python modules embedded within roles:

- **`roles/defrag_etcd_db/library/defrag_etcd.py`**: Defragments etcd databases in OpenShift
- **`roles/must_gather_log/library/redhat_sso_device_auth.py`**: Automates Red Hat SSO device authorization via OAuth2 flow
- **`roles/pxbackup/filter_plugins/lookup_helpers.py`**: Custom Jinja2 filters for Portworx backup operations
- **`roles/portworx_upgrade/library/pxctl_status.py`**: Executes pxctl commands in Portworx pods

All custom modules follow Ansible 2.18+ standards with proper argument specs, return values, and comprehensive documentation.

**Custom Module Standards:**

All custom Ansible modules must follow these requirements. See the full template below for structure.

#### Module File Structure Template

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Your Name <your.email@example.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: module_name
short_description: Brief description
description:
  - Detailed description
version_added: "1.0.0"
author:
  - Your Name (@github_handle)
options:
  param_name:
    description: Parameter description
    type: str
    required: true
requirements:
  - python >= 3.11
'''

EXAMPLES = r'''
- name: Basic usage
  module_name:
    param_name: value
'''

RETURN = r'''
changed:
  description: Whether the module made changes
  type: bool
  returned: always
msg:
  description: Human-readable message
  type: str
  returned: always
result:
  description: Detailed result data
  type: dict
  returned: success
'''

from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
        param_name=dict(type='str', required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(changed=False, msg='', result={})

    try:
        # Module logic here
        if module.check_mode:
            result['msg'] = 'Check mode: would process resource'
            module.exit_json(**result)

        # Actual processing
        result['changed'] = True
        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=f'Module execution failed: {str(e)}', **result)

def main():
    run_module()

if __name__ == '__main__':
    main()
```

#### Required Components

**1. Module Header:** Shebang, encoding, copyright, future imports, metaclass

**2. Documentation:** DOCUMENTATION, EXAMPLES, RETURN sections

**3. Module Initialization:** Always support check mode, validate parameters, use structured error handling

**4. Error Handling:**

```python
# Good - specific exceptions
try:
    data = perform_operation()
except SpecificException as e:
    module.fail_json(msg=f'Operation failed: {str(e)}', **result)

# Bad - bare except (NEVER DO THIS)
try:
    data = perform_operation()
except:
    pass
```

#### Common Patterns

**Kubernetes Resource Management:**

```python
from kubernetes import client, config
from kubernetes.client.rest import ApiException

def manage_k8s_resource(module):
    config.load_kube_config()
    v1 = client.CoreV1Api()

    try:
        existing = v1.read_namespaced_pod(name, namespace)
        resource_exists = True
    except ApiException as e:
        if e.status == 404:
            resource_exists = False
        else:
            raise

    if module.check_mode:
        return {'changed': not resource_exists, 'msg': f'Would create {name}'}
```

**Command Execution in Pods:**

```python
from kubernetes.stream import stream

resp = stream(
    v1.connect_get_namespaced_pod_exec,
    pod_name, namespace,
    command=command,
    stderr=True, stdin=False, stdout=True, tty=False
)
return {'changed': False, 'msg': 'Command executed', 'stdout': resp}
```

**State-based Resources (present/absent):**

Implement idempotency: check current state, only make changes if needed, respect check mode.

#### Best Practices

**DO:**

- Always support check mode
- Validate all input parameters
- Return meaningful error messages
- Use `module.fail_json()` for failures
- Set `changed=False` for read-only operations
- Implement idempotency
- Include comprehensive DOCUMENTATION/EXAMPLES/RETURN
- Test both success and failure paths

**DON'T:**

- Use bare `except:` clauses
- Print to stdout/stderr
- Make changes in check mode
- Assume parameters are valid without checking
- Hard-code credentials
- Skip documentation sections

#### Code Quality

All modules must pass:

```bash
.venv/bin/isort roles/<role_name>/library/*.py
.venv/bin/black roles/<role_name>/library/*.py
.venv/bin/flake8 roles/<role_name>/library/*.py
.venv/bin/mypy roles/<role_name>/library/*.py
.venv/bin/ansible-test sanity --test validate-modules
```

**For complete working examples:** See `docs/examples/custom_module_example.py` for a production-ready Kubernetes resource manager module demonstrating all patterns above, and `docs/examples/module_testing_example.py` for comprehensive testing examples.

### Custom Filter Plugins

Filter plugins are Python modules that extend Jinja2 templating within Ansible.

**Location:**

- Role-specific: `roles/<role_name>/filter_plugins/`
- Global: `filter_plugins/` at repository root

**Filter Plugin Standards:**

All filter plugins must follow these requirements:

#### File Structure Template

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Your Name <your.email@example.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
filter: filter_name
author: Author Name (@github_handle)
version_added: "1.0.0"
short_description: Brief description
description:
  - Detailed description
options:
  _input:
    description: The input value
    type: any
    required: true
'''

EXAMPLES = r'''
- debug:
    msg: "{{ input_value | filter_name }}"
'''

RETURN = r'''
_value:
  description: The filtered value
  type: any
  returned: always
'''

from ansible.errors import AnsibleFilterError

class FilterModule(object):
    def filters(self):
        return {'filter_name': self.filter_method}

    @staticmethod
    def filter_method(value, param=None):
        if not isinstance(value, expected_type):
            raise AnsibleFilterError(f"Expected {expected_type}, got {type(value).__name__}")

        try:
            return transform(value, param)
        except Exception as e:
            raise AnsibleFilterError(f"Error in filter_name: {str(e)}")
```

#### Required Components

1. **Module Header:** Shebang, encoding, copyright, future imports, metaclass
2. **Documentation:** DOCUMENTATION, EXAMPLES, RETURN sections
3. **FilterModule Class:** Must be named `FilterModule`, implement `filters()` method
4. **Filter Methods:** Use `@staticmethod`, validate types, raise `AnsibleFilterError` for errors

#### Best Practices

**DO:** Validate input types, use descriptive error messages, provide comprehensive documentation, use static methods when possible, test edge cases

**DON'T:** Use bare `except:`, return None for errors (raise AnsibleFilterError), modify input values, perform I/O operations, assume input types

**For complete working examples:** See `docs/examples/filter_plugin_example.py` for 7 production-ready filter functions demonstrating all patterns, type validation, and comprehensive error handling.

### Execution Environment Architecture

- Base image: `quay.io/centos/centos:stream9`
- Python: 3.11 (explicitly removes Python 3.9 if present)
- Container runtime: **Docker only** (requirement enforced in build configuration)
- All dependencies pinned in requirements files

### Key Collections Used

- `purepx.px_backup`: Portworx backup API integration
- `kubernetes.core`: Kubernetes cluster management (v2.3.0+) - critical for StorageCluster CRD operations
- `community.hashi_vault`: HashiCorp Vault integration
- `ansible.posix`, `ansible.scm`, `ansible.utils`: Standard utilities
- Cloud collections: `amazon.aws`, `community.aws`, `google.cloud`, `community.vmware`

## Coding Standards

**Comprehensive Examples Available:** The `docs/examples/` directory contains production-ready code templates and detailed examples. See `docs/examples/README.md` for a complete guide to all available examples.

### Ansible Best Practices

**Required Conventions:**

- Always use FQCN (Fully Qualified Collection Names) for all modules
- Use lowercase `true`/`false` for boolean values
- Include clear description comment blocks at the start of playbooks
- Use meaningful play and task names
- Use `no_log: true` for sensitive operations (tokens, credentials)

**Error Handling:**

- Use `block`/`rescue`/`always` for error handling
- Provide clear error messages
- Set appropriate `failed_when` conditions
- Use `ignore_errors` sparingly and only with justification
- Register results for important operations

**Variables:**

- Define required variables at the start of playbooks
- Use `assert` tasks to validate required variables
- Document optional variables with default values
- Follow proper variable scoping (host_vars, group_vars, playbook vars)

**Idempotency:**

- Design all tasks to be idempotent
- Use `changed_when` and `failed_when` directives appropriately
- Avoid `shell` and `command` modules unless absolutely necessary
- Prefer Ansible's built-in modules for specific tasks

**Proper use of changed_when and failed_when:**

When using `shell` or `command` modules, always define these directives:

- **changed_when**: For read-only ops (get, list, show): Use `changed_when: false`. For state changes: Test output to detect changes.
- **failed_when**: Consider all valid exit codes. For grep: `failed_when: result.rc not in [0, 1]`

Common patterns:

- `changed_when: false` - Any read/query operation
- `changed_when: "'created' in result.stdout or 'updated' in result.stdout"` - Output indicates modification
- `failed_when: result.rc != 0` - Simple success/failure
- `failed_when: result.rc not in [0, 1]` - Grep and similar tools

**For comprehensive examples:** See `docs/examples/changed_when_failed_when_examples.yml` for 30+ practical examples covering all common patterns including read-only operations, grep, state changes, retries, and multi-line commands with pipefail.

**Task Organization:**

- Group related tasks in separate files and use `include_tasks` or `import_tasks`
- Use tags for task organization and selective execution
- Use `changed_when` to accurately report changes

**Modular Role Architecture Pattern:**

The project uses a modular orchestrator pattern for complex roles (see `must_gather_log` role as reference implementation):

- **Orchestrator Pattern**: Main task file (`tasks/main.yml`) delegates to specialized task files
- **Separation of Concerns**: Each workflow component is a separate task file with single responsibility
- **Reusable Components**: Task files can be included individually using `tasks_from` parameter
- **Independent Testing**: Each component is independently testable and maintainable

Example structure:

```yaml
# tasks/main.yml - Simple orchestrator
- name: "Phase 1: Preparation"
  ansible.builtin.include_tasks: cleanup.yml
  tags: [preparation, cleanup]

- name: "Phase 2: Credential Management"
  ansible.builtin.include_tasks: sftp_credential_management.yml
  when: credentials_required | default(true) | bool
  tags: [credentials]

- name: "Phase 3: Main Operation"
  ansible.builtin.include_tasks: main_operation.yml
  tags: [execute]
```

Benefits:

- Clear workflow visualization in main.yml
- Reduced file size (easier code review)
- Components can be called directly: `ansible.builtin.include_role: name=role_name tasks_from=specific_task.yml`
- Simplified testing with targeted tag execution

**Kubernetes/OpenShift Operations:**

- Use `kubernetes.core.k8s` for all Kubernetes resource management
- Always specify `api_version` and `kind` for resources
- Use `state: present` for creation/updates, `state: absent` for deletion
- Implement wait conditions with `wait: true` and `wait_timeout`
- Use `namespace` parameter explicitly (never rely on default)

**Variable Management:**

- Define variables in appropriate locations (defaults, vars, group_vars, host_vars)
- Use descriptive variable names (avoid single letters or abbreviations)
- Document complex variable structures in role README or defaults/main.yml
- Use `set_fact` for derived or computed values
- Avoid using `register` unless the output is actually needed

### Python Standards (Modules and Filters)

- Python 3.11+ syntax
- Type hints required (from `__future__ import annotations`) for type checking
- Follow PEP 8 style guide
- Maximum line length: 100 characters (not 79)
- Use `black` for formatting, `flake8` for linting, `mypy` for type checking
- Custom modules must include proper Ansible documentation (DOCUMENTATION, EXAMPLES, RETURN)
- Use meaningful variable and function names
- Include docstrings for all functions and classes

**Error Handling:**

```python
# Good
try:
    result = perform_operation()
except SpecificException as e:
    module.fail_json(msg=f"Operation failed: {str(e)}")

# Bad - too broad
try:
    result = perform_operation()
except:  # NEVER DO THIS
    pass
```

**Testing:**

- Write unit tests for all custom modules and filters
- Use pytest for Python testing
- Test both success and failure cases
- Mock external dependencies appropriately

### Security

- Use Ansible Vault to encrypt sensitive data
- Never log sensitive information (use `no_log: true`)
- Validate all external input using `assert` module
- Use HTTPS for all API communication
- Implement proper privilege escalation with `become` only when necessary

### YAML Best Practices

**Formatting:**

- Use 2 spaces for indentation
- Use `---` document separator at file start
- Quote strings when they contain special characters
- Use `>` or `|` for multi-line strings appropriately
- Keep lines under 120 characters when possible

**Consistency:**

```yaml
# Good - consistent list syntax
tasks:
  - name: First task
    command: echo "one"
  - name: Second task
    command: echo "two"

# Bad - mixed notation
tasks:
  - name: First task
    command: echo "one"
  - { name: "Second task", command: "echo two" }
```

## Configuration Files

- **`ansible.cfg`**: Ansible configuration (inventory, fact caching, SSH retries, callbacks)
- **`.ansible-lint`**: Ansible-lint configuration (skips: line-length, var-naming, command-instead-of-module)
- **`.flake8`**: Python linting configuration
- **`tox.ini`**: Test automation for Podman and Docker builds

## Important Notes

### Execution Environment Requirements

- Container runtime **must** be Podman
- EE isolation must be considered in all automation decisions
- Python 3.11 is the only supported Python version
- All dependencies must be declared in requirements files for reproducible builds

### Platform Context

This project is designed for **Ansible Automation Platform (AAP)** deployment:

- All playbooks run inside Execution Environments
- Vault-based secret management is standard
- Enterprise security standards apply to all code
- Systems-level reasoning required for scaling considerations

### Communication Style

When working with this codebase, maintain a formal, professional tone appropriate for enterprise environments. Emphasize maintainability, clarity, and operational soundness in all changes.

## AAP/AWX Integration

### AAP Project Structure

The `aap_import/` directory contains configurations for importing roles and playbooks into Ansible Automation Platform. Each role subdirectory includes:

- `README.md` - Role import guide
- `import_to_aap.sh` - Automated import script
- `project_*.json` - Project configuration
- `execution_environment.json` - EE configuration
- `job_template_*.json` - Job template(s)
- `survey_spec_*.json` - Survey specifications
- `workflow_*.json` - Workflow templates (optional)

### AAP Configuration Patterns

**Multi-Template Pattern:** Create separate job templates for different execution modes (Check Mode, Execute, Rollback)

**Workflow Pattern:** Orchestrate multiple job templates with approval gates and success/failure paths

### Creating AAP Configurations for New Roles

1. Create subdirectory: `mkdir -p aap_import/<role_name>`
2. Add required files (README, import script, JSON configs)
3. Follow naming conventions: `{Role Name} Automation`, `{Role Name} - {Action}`
4. Include surveys for runtime variables with sensible defaults
5. Never commit credentials; use AAP credential types
6. Test: project sync, EE availability, job templates, workflows

### Import Methods

1. **Automated Script**: `cd aap_import/<role_name> && ./import_to_aap.sh`
2. **AWX CLI**: `awx projects create --name "..." --scm_type git --scm_url "..."`
3. **Web UI**: Manual creation following README
4. **API/Curl**: Direct API calls using JSON files

## Documentation Standards

**IMPORTANT:** Follow these rules when working with documentation:

- **No emojis or icons** - Documentation must be professional and text-only
- **Ask before creating** - Always ask the user for approval before generating or modifying documentation files
- **No unsolicited documentation** - Never proactively create README files, markdown documentation, or similar without explicit user request

**Documentation File Placement:**

All documentation and markdown files must be placed in the `docs/` directory:

- **General documentation**: `docs/` root (e.g., `docs/setup_guide.md`)
- **Role-specific**: `docs/<role_name>/` (e.g., `docs/portworx_upgrade/architecture.md`)
- **Collection-specific**: `docs/<collection_name>/` (e.g., `docs/px_backup/api_guide.md`)
- **Playbook-specific**: `docs/<playbook_name>/` (e.g., `docs/px_upgrade_playbook/usage.md`)
- **Filter plugins**: `docs/filters/` (e.g., `docs/filters/custom_filters_guide.md`)

**Exceptions:**

- `CLAUDE.md` - Repository root (project instructions for Claude Code)
- `README.md` - Repository root only (main project README)
- `aap_import/README.md` - AAP import main documentation
- `aap_import/<role_name>/README.md` - Role-specific AAP import guides

## Claude Code Workflow Requirements

### Virtual Environment Usage

**CRITICAL:** All Python and Ansible commands MUST use the virtual environment at `.venv`

- Python: `.venv/bin/python`
- Pip: `.venv/bin/pip`
- Ansible: `.venv/bin/ansible`, `.venv/bin/ansible-playbook`, `.venv/bin/ansible-lint`, `.venv/bin/ansible-galaxy`
- Linting: `.venv/bin/black`, `.venv/bin/isort`, `.venv/bin/flake8`, `.venv/bin/mypy`

### Automatic Quality Enforcement

**For Python files:** Run isort, black, flake8 automatically
**For Ansible files:** Run ansible-lint automatically

These tools run without user approval (configured in `.claude/settings.local.json`).

### Expected Behavior

When Claude Code modifies files:

1. Make the requested changes
2. Automatically run appropriate quality tools
3. Fix any issues found
4. Report results to user

### Git Commit Messages

**IMPORTANT:** Do NOT add Claude Code attribution or co-authorship to commit messages.

Commit messages should:

- Follow conventional commit format when appropriate
- Be concise and descriptive
- Focus on the "why" rather than the "what"
- Match the repository's existing commit style
- **NOT include** any Claude Code branding, attribution, or co-authorship footers

Good example:

```text
Add etcd defragmentation monitoring

Implements health check validation before and after defrag operations
to ensure cluster stability.
```

---

## Markdown Code Block Language Specification

**Rule**: All fenced code blocks MUST have a language identifier specified to comply with MD040/fenced-code-language linting rules.

### Requirements

- Every code block using triple backticks (```) MUST include a language identifier
- If no specific language applies, use `text` as the default language identifier
- Never create code blocks with opening ``` without a language specifier

### Examples

**Correct**:

```python
print("Hello World")
```

```bash
echo "Hello World"
```

```text
This is plain text content
No specific language applies
```

**Incorrect**:

```
This violates MD040
```

### Common Language Identifiers

- Programming: `python`, `bash`, `javascript`, `java`, `yaml`, `json`, `xml`
- Output/Logs: `text`, `console`, `log`
- Documentation: `markdown`, `html`, `css`
- Configuration: `ini`, `toml`, `conf`
- When in doubt: `text`

This rule is clear, actionable, and includes examples of both correct and incorrect usage. It fits well with your existing Ansible documentation standards and will prevent MD040 violations in any markdown files Claude creates for you.

---
