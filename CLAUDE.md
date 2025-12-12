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

### Python Environment

**IMPORTANT:** Always use the Python virtual environment located at `/development/git/ansible-playground/.venv`

```bash
# Activate virtual environment
source .venv/bin/activate

# Verify you're using the correct Python
which python  # Should show: /development/git/ansible-playground/.venv/bin/python
```

All Python commands, pip installations, and tool executions must be run using the virtual environment Python interpreter at `.venv/bin/python`.

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

**IMPORTANT:** All linting and formatting tools must be run using the virtual environment.

```bash
# Code formatting (black) - run on Python files
.venv/bin/black .

# Import sorting (isort) - run on Python files
.venv/bin/isort .

# Python linting (flake8) - run on Python files
.venv/bin/flake8 .

# Type checking (mypy) - run on Python files
.venv/bin/mypy .

# Ansible-specific linting - run on playbooks and roles
.venv/bin/ansible-lint

# YAML linting
.venv/bin/yamllint .

# Run tests
.venv/bin/pytest

# Tox testing environments
.venv/bin/tox -e podman  # Build with Podman
.venv/bin/tox -e docker  # Build with Docker
```

**Automatic Quality Checks:**

When modifying files, automatically run appropriate tools:

- **Python files** (`.py`, custom modules in `roles/*/library/`, filter plugins in `roles/*/filter_plugins/`): Run black, isort, flake8
- **Ansible files** (playbooks `*.yml`, roles, tasks): Run ansible-lint
- **All changes**: Run ansible-lint on affected playbooks/roles(playbooks `*.yml`, roles, tasks)

### Running Playbooks

```bash
# Basic playbook execution
ansible-playbook -i inventory/<inventory-file> playbooks/<playbook-name>.yml

# Syntax check
ansible-playbook --syntax-check playbooks/<playbook-name>.yml

# Dry run
ansible-playbook -i inventory/<inventory-file> playbooks/<playbook-name>.yml --check

# View changes
ansible-playbook -i inventory/<inventory-file> playbooks/<playbook-name>.yml --diff

# Increase verbosity
ansible-playbook -i inventory/<inventory-file> playbooks/<playbook-name>.yml -vvv
```

### Role Testing Workflow

For new roles, follow this testing progression:

1. **Syntax validation**: `ansible-playbook --syntax-check playbooks/<playbook>.yml`
2. **Ansible-lint**: `.venv/bin/ansible-lint roles/<role-name>/`
3. **Tag-based testing**: Test individual phases using `--tags`

   ```bash
   ansible-playbook playbooks/px_upgrade.yml --tags preflight --check
   ```

4. **Dry-run mode**: Use `--check` to validate without changes
5. **Test environment**: Run against dev/test cluster first
6. **Production validation**: Final testing in production-like environment

## Architecture

### Directory Structure

- **`roles/`**: Reusable Ansible roles
  - `common/`: Shared functionality across roles
  - `defrag_etcd_db/`: etcd database defragmentation for OpenShift
  - `deploy_px/`: Portworx deployment automation
  - `must_gather_log/`: Must-gather log collection and Red Hat case management
  - `portworx_upgrade/`: **NEW** - Automated Portworx cluster upgrades with operator-controlled rolling updates
  - `pxbackup/`: Portworx backup operations
  - `setup_env/`: Environment setup and configuration
  - `upgrade_clusters/`: Cluster upgrade automation
  - `vault_multi_namespace_monitor/`: Multi-namespace Vault monitoring
  - `vault_fix_portworx/`: Vault integration fixes for Portworx

- **`playbooks/`**: Orchestration playbooks
  - `pxbkup/`: Portworx backup-specific playbooks (create/list backups, schedules, clusters)
  - Various cluster management playbooks (k8s_*, px_*, etcd_*)

- **`Build-EE/`**: Execution environment build configuration
  - `execution-environment.yml`: EE definition (CentOS Stream 9 base)
  - `update_collection_requirements.py`: Collection dependency management

- **`collections/`**: Local Ansible collections
- **`inventory/`**: Inventory files with `group_vars/` and `host_vars/`
- **`scripts/`**: Utility scripts
- **`.cursor/rules/`**: Development standards and best practices

- **`aap_import/`**: AAP/AWX import configurations for roles
  - Role-specific subdirectories contain JSON configurations and import scripts
  - Each role directory includes: project configs, job templates, workflows, execution environments
  - Automated import scripts (`.sh`) for quick AAP setup
  - See [aap_import/README.md](aap_import/README.md) for details

### Custom Modules

The project includes custom Python modules embedded within roles:

- **`roles/defrag_etcd_db/library/defrag_etcd.py`**: Defragments etcd databases in OpenShift by executing etcdctl commands inside etcd pods via `oc rsh`. Implements leader-aware ordering (defragments non-leader members first, leader last).

- **`roles/pxbackup/filter_plugins/lookup_helpers.py`**: Custom Jinja2 filters for Portworx backup operations.

- **`roles/portworx_upgrade/library/pxctl_status.py`**: Executes pxctl commands in Portworx pods with auth token handling and structured output parsing. Provides health status information for upgrade monitoring.

All custom modules follow Ansible 2.18+ standards with proper argument specs, return values, and comprehensive documentation.

**Custom Module Standards:**

All custom Ansible modules in this repository must follow these strict requirements:

#### Module File Structure

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
short_description: Brief description of module
description:
  - Detailed description of what the module does
  - Additional context and use cases
version_added: "1.0.0"
author:
  - Your Name (@github_handle)
options:
  param_name:
    description: Parameter description
    type: str
    required: true
  optional_param:
    description: Optional parameter description
    type: bool
    required: false
    default: false
requirements:
  - python >= 3.11
  - kubernetes >= 12.0.0
notes:
  - This module is designed for AAP execution environments
  - Requires specific cluster permissions
seealso:
  - module: related.module.name
  - name: Related documentation
    link: https://docs.example.com
'''

EXAMPLES = r'''
- name: Basic module usage
  module_name:
    param_name: value
    optional_param: true

- name: Advanced usage with error handling
  block:
    - name: Execute module
      module_name:
        param_name: "{{ cluster_name }}"
      register: result
  rescue:
    - name: Handle failure
      debug:
        msg: "Module failed: {{ result.msg }}"
'''

RETURN = r'''
changed:
  description: Whether the module made changes
  type: bool
  returned: always
  sample: true
msg:
  description: Human-readable message about what happened
  type: str
  returned: always
  sample: "Successfully processed resource"
result:
  description: Detailed result data
  type: dict
  returned: success
  sample:
    status: "completed"
    resources_processed: 5
'''

from ansible.module_utils.basic import AnsibleModule


def run_module():
    """Main module execution function"""
    
    # Define module argument specification
    module_args = dict(
        param_name=dict(type='str', required=True),
        optional_param=dict(type='bool', required=False, default=False),
    )
    
    # Initialize module
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    
    # Initialize result dictionary
    result = dict(
        changed=False,
        msg='',
        result={}
    )
    
    try:
        # Get parameters
        param_name = module.params['param_name']
        optional_param = module.params['optional_param']
        
        # Validate parameters
        if not param_name:
            module.fail_json(msg='param_name cannot be empty', **result)
        
        # Check mode - don't make actual changes
        if module.check_mode:
            result['msg'] = 'Check mode: would process resource'
            module.exit_json(**result)
        
        # Actual module logic here
        processed_data = process_resource(param_name, optional_param)
        
        # Update result
        result['changed'] = True
        result['msg'] = f'Successfully processed {param_name}'
        result['result'] = processed_data
        
        module.exit_json(**result)
        
    except Exception as e:
        module.fail_json(
            msg=f'Module execution failed: {str(e)}',
            exception=str(e),
            **result
        )


def process_resource(name, option):
    """
    Process the resource with given parameters
    
    Args:
        name: Resource name
        option: Processing option
        
    Returns:
        dict: Processed data
        
    Raises:
        Exception: If processing fails
    """
    # Implementation here
    return {'status': 'success', 'name': name}


def main():
    run_module()


if __name__ == '__main__':
    main()
```

#### Required Components

**1. Module Header:**

- Shebang: `#!/usr/bin/python`
- Encoding: `# -*- coding: utf-8 -*-`
- Copyright with GPL-3.0+ license
- Future imports: `from __future__ import absolute_import, division, print_function`
- Metaclass: `__metaclass__ = type`

**2. Documentation:**

- `DOCUMENTATION`: Module metadata, parameters, requirements
- `EXAMPLES`: Usage examples showing various scenarios
- `RETURN`: Return value documentation with types and samples

**3. Argument Specification:**

```python
module_args = dict(
    param_name=dict(type='str', required=True),
    param_with_choices=dict(
        type='str',
        required=False,
        choices=['option1', 'option2'],
        default='option1'
    ),
    param_with_validation=dict(
        type='int',
        required=False,
        default=30
    ),
)
```

**4. Module Initialization:**

```python
module = AnsibleModule(
    argument_spec=module_args,
    supports_check_mode=True,  # Always support check mode
    required_if=[
        ('state', 'present', ['resource_name']),
    ],
    mutually_exclusive=[
        ('option_a', 'option_b'),
    ],
)
```

**5. Result Dictionary:**

```python
result = dict(
    changed=False,      # Whether module made changes
    msg='',            # Human-readable message
    result={},         # Detailed result data
    # Add custom return values as needed
)
```

**6. Error Handling:**

```python
# Good - structured error handling
try:
    data = perform_operation()
    result['changed'] = True
    result['result'] = data
    module.exit_json(**result)
except SpecificException as e:
    module.fail_json(
        msg=f'Operation failed: {str(e)}',
        exception=str(e),
        **result
    )

# Bad - bare except
try:
    data = perform_operation()
except:  # NEVER DO THIS
    pass
```

#### Common Module Patterns

**Kubernetes Resource Management:**

```python
from kubernetes import client, config
from kubernetes.client.rest import ApiException

def manage_k8s_resource(module):
    """Manage Kubernetes resource"""
    try:
        # Load kubeconfig
        config.load_kube_config()
        v1 = client.CoreV1Api()
        
        namespace = module.params['namespace']
        name = module.params['name']
        
        # Check if resource exists
        try:
            existing = v1.read_namespaced_pod(name, namespace)
            resource_exists = True
        except ApiException as e:
            if e.status == 404:
                resource_exists = False
            else:
                raise
        
        # Handle check mode
        if module.check_mode:
            return {
                'changed': not resource_exists,
                'msg': f'Would create {name}' if not resource_exists else f'{name} exists'
            }
        
        # Create or update resource
        if not resource_exists:
            # Create new resource
            result = v1.create_namespaced_pod(namespace, pod_manifest)
            return {'changed': True, 'msg': f'Created {name}', 'result': result}
        else:
            # Resource exists
            return {'changed': False, 'msg': f'{name} already exists'}
            
    except ApiException as e:
        module.fail_json(msg=f'Kubernetes API error: {str(e)}', status=e.status)
```

**Command Execution in Pods:**

```python
from kubernetes import client, config
from kubernetes.stream import stream

def exec_in_pod(module, pod_name, namespace, command):
    """Execute command in Kubernetes pod"""
    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        
        # Execute command
        resp = stream(
            v1.connect_get_namespaced_pod_exec,
            pod_name,
            namespace,
            command=command,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False
        )
        
        return {
            'changed': False,  # Read-only operation
            'msg': 'Command executed successfully',
            'stdout': resp,
            'rc': 0
        }
        
    except Exception as e:
        module.fail_json(msg=f'Failed to execute command: {str(e)}')
```

**State-based Resources:**

```python
def handle_state(module):
    """Handle state parameter (present/absent)"""
    state = module.params['state']
    name = module.params['name']
    
    # Check current state
    exists = check_resource_exists(name)
    
    if state == 'present':
        if exists:
            # Resource exists, check if update needed
            if needs_update(name, module.params):
                if not module.check_mode:
                    update_resource(name, module.params)
                return {'changed': True, 'msg': f'Updated {name}'}
            else:
                return {'changed': False, 'msg': f'{name} already up to date'}
        else:
            # Resource doesn't exist, create it
            if not module.check_mode:
                create_resource(name, module.params)
            return {'changed': True, 'msg': f'Created {name}'}
    
    elif state == 'absent':
        if exists:
            if not module.check_mode:
                delete_resource(name)
            return {'changed': True, 'msg': f'Deleted {name}'}
        else:
            return {'changed': False, 'msg': f'{name} does not exist'}
```

**Idempotency Checking:**

```python
def is_update_needed(current_state, desired_state):
    """
    Compare current and desired state to determine if update is needed
    
    Args:
        current_state: Current resource state
        desired_state: Desired resource state
        
    Returns:
        bool: True if update is needed
    """
    # Compare relevant fields
    fields_to_check = ['replicas', 'image', 'version']
    
    for field in fields_to_check:
        if current_state.get(field) != desired_state.get(field):
            return True
    
    return False
```

#### Module Testing

**Unit Tests (pytest):**

```python
# tests/unit/modules/test_custom_module.py
import pytest
from unittest.mock import patch, MagicMock
from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes
import json


def set_module_args(args):
    """Prepare module arguments for testing"""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class TestCustomModule:
    
    @patch('module_name.perform_operation')
    def test_module_success(self, mock_operation):
        """Test successful module execution"""
        set_module_args({
            'param_name': 'test-value',
            'optional_param': True
        })
        
        mock_operation.return_value = {'status': 'success'}
        
        with pytest.raises(SystemExit) as exc:
            from library.module_name import main
            main()
        
        # Verify module exited successfully
        assert exc.value.code == 0
    
    @patch('module_name.perform_operation')
    def test_module_failure(self, mock_operation):
        """Test module failure handling"""
        set_module_args({
            'param_name': 'test-value'
        })
        
        mock_operation.side_effect = Exception('Test error')
        
        with pytest.raises(SystemExit) as exc:
            from library.module_name import main
            main()
        
        # Verify module failed
        assert exc.value.code != 0
```

**Integration Tests (playbook):**

```yaml
# tests/integration/test_custom_module.yml
---
- name: Test custom module
  hosts: localhost
  gather_facts: false
  
  tasks:
    - name: Test module with valid parameters
      custom_module:
        param_name: test-resource
        optional_param: true
      register: result
    
    - name: Verify result
      assert:
        that:
          - result.changed
          - result.msg is defined
          - result.result is defined
    
    - name: Test module check mode
      custom_module:
        param_name: test-resource
      check_mode: true
      register: check_result
    
    - name: Verify check mode doesn't make changes
      assert:
        that:
          - check_result.msg is defined
    
    - name: Test module error handling
      custom_module:
        param_name: ""  # Invalid parameter
      register: error_result
      ignore_errors: true
    
    - name: Verify error was caught
      assert:
        that:
          - error_result.failed
          - error_result.msg is defined
```

#### Module Best Practices

**DO:**

- Always support check mode (`supports_check_mode=True`)
- Validate all input parameters before processing
- Return meaningful error messages with context
- Use `module.fail_json()` for all failures
- Set `changed=False` for read-only operations
- Implement idempotency (same operation multiple times = same result)
- Include comprehensive DOCUMENTATION/EXAMPLES/RETURN
- Use specific exception types in error handling
- Test both success and failure paths
- Document all parameters with types and defaults

**DON'T:**

- Use bare `except:` clauses
- Print to stdout/stderr (use module.log() or result dict)
- Make changes in check mode
- Ignore errors silently
- Use global variables or state
- Assume parameters are valid without checking
- Hard-code credentials or sensitive data
- Return None or undefined for failures (use fail_json)
- Modify system state without tracking changes
- Skip documentation sections

#### Parameter Validation Patterns

```python
# Required string parameter
if not module.params.get('name'):
    module.fail_json(msg='name parameter is required')

# Validate string format
import re
if not re.match(r'^[a-z0-9-]+$', module.params['name']):
    module.fail_json(msg='name must contain only lowercase letters, numbers, and hyphens')

# Validate integer range
if not 1 <= module.params['replicas'] <= 100:
    module.fail_json(msg='replicas must be between 1 and 100')

# Validate choices (when not using choices in argument_spec)
valid_states = ['present', 'absent', 'latest']
if module.params['state'] not in valid_states:
    module.fail_json(msg=f"state must be one of: {', '.join(valid_states)}")

# Validate mutually exclusive parameters
if module.params.get('option_a') and module.params.get('option_b'):
    module.fail_json(msg='option_a and option_b are mutually exclusive')
```

#### Code Quality for Modules

All custom modules must pass:

```bash
# Format and lint before committing
.venv/bin/isort roles/<role_name>/library/*.py
.venv/bin/black roles/<role_name>/library/*.py
.venv/bin/flake8 roles/<role_name>/library/*.py

# Type checking
.venv/bin/mypy roles/<role_name>/library/*.py

# Ansible module validation
.venv/bin/ansible-test sanity --test validate-modules
```

#### Example: Complete Custom Module

See `docs/examples/custom_module_example.py` for a comprehensive example demonstrating:

- Proper structure and documentation
- Kubernetes resource management
- Command execution in pods
- State-based resource handling
- Check mode support
- Comprehensive error handling
- Unit and integration tests

### Custom Filter Plugins

Filter plugins are Python modules that extend Jinja2 templating capabilities within Ansible. They are placed in `roles/*/filter_plugins/` directories.

**Location:**

- Role-specific filters: `roles/<role_name>/filter_plugins/`
- Global filters: `filter_plugins/` at repository root

**Key Filter Plugins:**

- **`roles/pxbackup/filter_plugins/lookup_helpers.py`**: Portworx backup data manipulation and API response processing

**Filter Plugin Standards:**

All filter plugins in this repository must follow these strict requirements:

#### File Structure

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
short_description: Brief description of filter
description:
  - Detailed description of what the filter does
  - Additional context and use cases
options:
  _input:
    description: The input value to filter
    type: any
    required: true
  param_name:
    description: Optional parameter description
    type: str
    required: false
    default: default_value
notes:
  - Important usage notes
  - Behavior details
seealso:
  - module: related.module.name
  - filter: related_filter_name
'''

EXAMPLES = r'''
# Basic usage example
- name: Example task
  debug:
    msg: "{{ input_value | filter_name }}"

# Advanced usage with parameters
- name: Advanced example
  debug:
    msg: "{{ input_value | filter_name(param='value') }}"
'''

RETURN = r'''
_value:
  description: The filtered/transformed value
  type: any
  returned: always
'''

# Import statements
from ansible.errors import AnsibleFilterError
from ansible.module_utils.common._collections_compat import Mapping, Sequence


class FilterModule(object):
    """Ansible filter plugin class"""

    def filters(self):
        """Return filter mapping dictionary"""
        return {
            'filter_name': self.filter_method,
            'another_filter': self.another_method,
        }

    @staticmethod
    def filter_method(value, param=None):
        """
        Brief description of filter method
        
        Args:
            value: Input value description
            param: Optional parameter description
            
        Returns:
            Transformed value description
            
        Raises:
            AnsibleFilterError: Error condition description
        """
        # Type validation
        if not isinstance(value, expected_type):
            raise AnsibleFilterError(
                f"filter_name requires {expected_type}, got {type(value).__name__}"
            )
        
        # Implementation
        try:
            result = transform(value, param)
            return result
        except Exception as e:
            raise AnsibleFilterError(f"Error in filter_name: {str(e)}")
```

#### Required Components

**1. Module Header:**

- Shebang line: `#!/usr/bin/python`
- Encoding declaration: `# -*- coding: utf-8 -*-`
- Copyright header with GPL-3.0+ license
- Future imports: `from __future__ import absolute_import, division, print_function`
- Metaclass: `__metaclass__ = type`

**2. Documentation Sections:**

- `DOCUMENTATION`: Filter metadata, parameters, description
- `EXAMPLES`: Usage examples in Ansible playbook format
- `RETURN`: Return value documentation

**3. FilterModule Class:**

- Must be named `FilterModule`
- Must implement `filters()` method returning dict
- Dictionary maps filter names (strings) to method references

**4. Filter Methods:**

- Use `@staticmethod` when no instance state needed
- Include comprehensive docstrings with Args/Returns/Raises
- Implement strict type validation
- Raise `AnsibleFilterError` for all error conditions
- Never use bare `except:` - catch specific exceptions

**5. Error Handling:**

```python
# Good - specific error handling
if not isinstance(value, dict):
    raise AnsibleFilterError(f"Expected dict, got {type(value).__name__}")

try:
    result = process(value)
except KeyError as e:
    raise AnsibleFilterError(f"Missing required key: {str(e)}")
except Exception as e:
    raise AnsibleFilterError(f"Unexpected error: {str(e)}")

# Bad - bare except
try:
    result = process(value)
except:  # NEVER DO THIS
    return None
```

**6. Type Validation:**

```python
# Always validate input types
if not isinstance(value, (list, tuple)):
    raise AnsibleFilterError(f"Expected list, got {type(value).__name__}")

if not isinstance(param, str):
    raise AnsibleFilterError(f"Parameter must be string, got {type(param).__name__}")
```

#### Common Filter Patterns

**String Processing:**

```python
@staticmethod
def process_string(value, option=None):
    """Process string with optional parameter"""
    if not isinstance(value, str):
        raise AnsibleFilterError("Requires string input")
    
    # Process and return
    return value.upper() if option == 'upper' else value.lower()
```

**List Processing:**

```python
@staticmethod
def filter_list(value, condition):
    """Filter list based on condition"""
    if not isinstance(value, (list, tuple)):
        raise AnsibleFilterError("Requires list input")
    
    try:
        return [item for item in value if meets_condition(item, condition)]
    except Exception as e:
        raise AnsibleFilterError(f"Filter error: {str(e)}")
```

**Dictionary Manipulation:**

```python
@staticmethod
def transform_dict(value, key_map=None):
    """Transform dictionary keys or values"""
    if not isinstance(value, dict):
        raise AnsibleFilterError("Requires dict input")
    
    key_map = key_map or {}
    return {key_map.get(k, k): v for k, v in value.items()}
```

**Recursive Processing:**

```python
def recursive_transform(self, value):
    """Recursively transform nested structures"""
    if isinstance(value, dict):
        return {k: self.recursive_transform(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [self.recursive_transform(item) for item in value]
    else:
        return transform_single(value)
```

#### Testing Filter Plugins

**Unit Tests (pytest):**

```python
# tests/unit/filter_plugins/test_custom_filters.py
import pytest
from ansible.errors import AnsibleFilterError
from filter_plugins.custom_filters import FilterModule


class TestCustomFilters:
    @pytest.fixture
    def filter_module(self):
        return FilterModule()
    
    def test_filter_valid_input(self, filter_module):
        result = filter_module.filter_name("test")
        assert result == "expected"
    
    def test_filter_invalid_type(self, filter_module):
        with pytest.raises(AnsibleFilterError):
            filter_module.filter_name(123)
```

**Integration Tests (playbook):**

```yaml
# tests/integration/filter_tests.yml
---
- name: Test custom filters
  hosts: localhost
  gather_facts: false
  
  tasks:
    - name: Test basic filter
      assert:
        that:
          - "'test' | filter_name == 'expected'"
        fail_msg: "Filter test failed"
    
    - name: Test with parameters
      assert:
        that:
          - "'test' | filter_name(param='value') == 'expected'"
```

#### Filter Plugin Best Practices

**DO:**

- Always validate input types before processing
- Use descriptive error messages in AnsibleFilterError
- Provide comprehensive DOCUMENTATION/EXAMPLES/RETURN
- Use static methods when no instance state needed
- Follow PEP 8 naming conventions (snake_case for methods)
- Include detailed docstrings with type information
- Test edge cases and error conditions
- Keep filters focused on single responsibility

**DON'T:**

- Use bare `except:` clauses
- Return None for errors (raise AnsibleFilterError instead)
- Modify input values (return new objects)
- Perform I/O operations in filters
- Include business logic (filters should transform data only)
- Use global state or class variables
- Assume input types without validation

#### Performance Considerations

- Use `@staticmethod` for better performance when possible
- Avoid recursive operations on large datasets
- Cache expensive computations when appropriate
- Minimize external dependencies
- Profile filters used in loops with large datasets

#### Code Quality Tools

All filter plugins must pass:

```bash
# Format and lint before committing
.venv/bin/isort roles/<role_name>/filter_plugins/*.py
.venv/bin/black roles/<role_name>/filter_plugins/*.py
.venv/bin/flake8 roles/<role_name>/filter_plugins/*.py

# Type checking (optional but recommended)
.venv/bin/mypy roles/<role_name>/filter_plugins/*.py

# Ansible lint (will check DOCUMENTATION sections)
.venv/bin/ansible-lint roles/<role_name>/
```

#### Example: Complete Filter Plugin

See `docs/examples/filter_plugin_example.py` for a comprehensive example demonstrating:

- Proper structure and documentation
- Multiple filter types (string, list, dict processing)
- Error handling and type validation
- Static and instance methods
- Recursive operations
- Comprehensive unit tests

### Execution Environment Architecture

The project uses Execution Environments (EEs) for isolation and reproducibility:

- Base image: `quay.io/centos/centos:stream9`
- Python: 3.11 (explicitly removes Python 3.9 if present)
- Container runtime: **Docker only** (requirement enforced in build configuration)
- All dependencies are pinned in requirements files
- EE includes system packages for Kerberos, Git LFS, Podman, and build tools

### Key Collections Used

- `purepx.px_backup`: Portworx backup API integration
- `kubernetes.core`: Kubernetes cluster management (v2.3.0+)
  - Critical for StorageCluster CRD operations
  - Required for pod exec operations (pxctl commands)
- `community.hashi_vault`: HashiCorp Vault integration
- `ansible.posix`, `ansible.scm`, `ansible.utils`: Standard utilities
- Cloud collections: `amazon.aws`, `community.aws`, `google.cloud`, `community.vmware`

## Coding Standards

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
- Never ignore errors without explicit justification

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

When using `shell` or `command` modules, always define `changed_when` and `failed_when` to ensure proper idempotency and error handling:

- **changed_when**: Controls when a task reports "changed" status
  - For read-only operations (get, list, show): Use `changed_when: false` since these never modify state
  - For operations with detectable state changes: Test the output to determine if changes occurred
  - For operations that should report unusual conditions: Test for unexpected states (e.g., empty results when data is expected)

- **failed_when**: Controls when a task reports failure
  - Always consider all valid exit codes for the command
  - For grep operations: Use `failed_when: result.rc not in [0, 1]` since grep returns 1 when no matches are found
  - For operations with retry logic: Let `until` handle failures, use `failed_when` for unrecoverable errors
  - Test both return code and output content when appropriate

Examples:

```yaml
# Read-only operation - never changes state
- name: Get list of pods
  ansible.builtin.shell: kubectl get pods --no-headers
  register: pod_list
  changed_when: false
  failed_when: pod_list.rc != 0

# Grep operation - allow both success and no-match exit codes
- name: Find worker machinesets
  ansible.builtin.shell: |
    set -o pipefail &&
    oc get machineset --no-headers | grep worker
  args:
    executable: /bin/bash
  register: machineset_list
  changed_when: false
  failed_when: machineset_list.rc not in [0, 1]

# State-modifying operation - detect actual changes
- name: Apply configuration
  ansible.builtin.shell: kubectl apply -f config.yaml
  register: apply_result
  changed_when: "'configured' in apply_result.stdout or 'created' in apply_result.stdout"
  failed_when: apply_result.rc != 0

# Operation with expected output - report change if output is unusual
- name: Verify cluster members exist
  ansible.builtin.shell: etcdctl member list
  register: member_list
  changed_when: member_list.stdout_lines | length == 0
  failed_when: member_list.rc != 0
```

Common patterns:

- `changed_when: false` - For any read/query operation
- `changed_when: result.stdout_lines | length == 0` - When empty results indicate an unexpected state
- `changed_when: "'created' in result.stdout or 'updated' in result.stdout"` - When output indicates modification
- `failed_when: result.rc != 0` - For commands with simple success/failure
- `failed_when: result.rc not in [0, 1]` - For grep and similar tools
- `failed_when: result.rc != 0 or 'error' in result.stderr | lower` - When checking both exit code and output

**Task Organization:**

- Group related tasks in separate files and use `include_tasks` or `import_tasks`
- Use tags for task organization and selective execution
- Implement idempotency (tasks should be safely re-runnable)
- Use `changed_when` to accurately report changes

**Kubernetes/OpenShift Operations:**

- Use `kubernetes.core.k8s` for all Kubernetes resource management
- Always specify `api_version` and `kind` for resources
- Use `state: present` for creation/updates, `state: absent` for deletion
- Implement wait conditions with `wait: true` and `wait_timeout`
- Use `namespace` parameter explicitly (never rely on default)
- Set appropriate `failed_when` conditions
- Use `ignore_errors` sparingly and only with justification

**Variable Management:**

- Define variables in appropriate locations (defaults, vars, group_vars, host_vars)
- Use descriptive variable names (avoid single letters or abbreviations)
- Document complex variable structures in role README or defaults/main.yml
- Use `set_fact` for derived or computed values
- Avoid using `register` unless the output is actually needed

**Task Organization:**

- Group related tasks in separate files and use `include_tasks` or `import_tasks`
- Use tags for task organization and selective execution
- Implement idempotency (tasks should be safely re-runnable)
- Use `changed_when` to accurately report changes

**Kubernetes/OpenShift Operations:**

- Use `kubernetes.core.k8s` for all Kubernetes resource management
- Always specify `api_version` and `kind` for resources
- Use `state: present` for creation/updates, `state: absent` for deletion
- Implement wait conditions with `wait: true` and `wait_timeout`
- Use `namespace` parameter explicitly (never rely on default)

### Python Standards (Modules and Filters)

- Python 3.11+ syntax
- Type hints required (from `__future__ import annotations`) for type checking
- Follow PEP 8 style guide
- Maximum line length: 100 characters (not 79)
- Use `black` for formatting, `flake8` for linting, `mypy` for type checking
- Custom modules must include proper Ansible documentation (DOCUMENTATION, EXAMPLES, RETURN)
- Use meaningful variable and function names
- Include docstrings for all functions and classes

**Code Style:**

- Follow PEP 8 style guide
- Maximum line length: 100 characters (not 79)
- Use meaningful variable and function names
- Include docstrings for all functions and classes
- Type checking: Use type hints where beneficial for clarity

**Error Handling:**

```python
# Good error handling
try:
    result = perform_operation()
except SpecificException as e:
    module.fail_json(msg=f"Operation failed: {str(e)}")

# Bad error handling
try:
    result = perform_operation()
except:  # Too broad, never do this
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
- Quote strings when they contain special characters or could be ambiguous
- Use `>` or `|` for multi-line strings appropriately
- Keep lines under 120 characters when possible

**Lists vs Dictionaries:**

```yaml
# Good - clean list syntax
tasks:
  - name: First task
    command: echo "one"
  
  - name: Second task
    command: echo "two"

# Bad - don't mix dictionary and list notation
tasks:
  - name: First task
    command: echo "one"
  - { name: "Second task", command: "echo two" }  # Inconsistent style
```

## Configuration Files

- **`ansible.cfg`**: Ansible configuration
  - Inventory: `inventory/hosts.yml`
  - Fact caching: JSON files in `tmp/facts_cache/`
  - SSH retries: 8 attempts
  - Callbacks enabled: `debug`, `unixy`
  - Collections path: `./collections:/usr/share/ansible/collections`

- **`.ansible-lint`**: Ansible-lint configuration
  - Skips: line-length, var-naming rules, command-instead-of-module, name[template]

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

## Custom Module Development

### Module Structure

All custom modules must include:

1. Proper shebang and encoding: `#!/usr/bin/python` and `# -*- coding: utf-8 -*-`
2. Copyright and license header
3. DOCUMENTATION, EXAMPLES, and RETURN sections
4. Proper imports with `from __future__ import`
5. Argument spec using `AnsibleModule.argument_spec`
6. Type hints in docstrings
7. Comprehensive error handling

**Code Style:**

- Follow PEP 8 style guide
- Maximum line length: 100 characters (not 79)
- Use meaningful variable and function names
- Include docstrings for all functions and classes
- Type checking: Use type hints where beneficial for clarity

**Error Handling:**

```python
# Good error handling
try:
    result = perform_operation()
except SpecificException as e:
    module.fail_json(msg=f"Operation failed: {str(e)}")

# Bad error handling
try:
    result = perform_operation()
except:  # Too broad, never do this
    pass
```

**Testing:**

- Write unit tests for all custom modules and filters
- Use pytest for Python testing
- Test both success and failure cases
- Mock external dependencies appropriately

### YAML Best Practices

**Formatting:**

- Use 2 spaces for indentation
- Use `---` document separator at file start
- Quote strings when they contain special characters or could be ambiguous
- Use `>` or `|` for multi-line strings appropriately
- Keep lines under 120 characters when possible

**Lists vs Dictionaries:**

```yaml
# Good - clean list syntax
tasks:
  - name: First task
    command: echo "one"
  
  - name: Second task
    command: echo "two"

# Bad - don't mix dictionary and list notation
tasks:
  - name: First task
    command: echo "one"
  - { name: "Second task", command: "echo two" }  # Inconsistent style
```

### Documentation Standards

**Custom Module Documentation:**

Each custom module must have complete DOCUMENTATION with:

- `module`: Module name
- `short_description`: One-line description
- `description`: Detailed multi-line description
- `options`: All parameters with types and descriptions
- `requirements`: Python libraries or system packages needed
- `author`: Module author with contact info
- `version_added`: When the module was added

**Role Documentation:**

Roles should include:

- `README.md` in role directory with usage examples
- Comments in `defaults/main.yml` explaining variables
- Clear task names that describe what each task does
- Tags documented in role README

**Filter Plugin Documentation:**

Each filter plugin must have:

- Complete DOCUMENTATION section with filter description
- EXAMPLES showing multiple use cases
- RETURN documenting output structure and type
- Docstrings on all filter methods with Args/Returns/Raises

## AAP/AWX Integration

### AAP Project Structure

The `aap_import/` directory contains configurations for importing roles and playbooks into Ansible Automation Platform:

```text
aap_import/
├── README.md                           # Main AAP import documentation
├── <role_name>/                        # Role-specific AAP configuration
│   ├── README.md                       # Role import guide
│   ├── import_to_aap.sh               # Automated import script
│   ├── project_<name>.json            # Project configuration
│   ├── execution_environment.json     # EE configuration
│   ├── job_template_*.json            # Job template(s)
│   ├── survey_spec_*.json             # Survey specifications
│   └── workflow_*.json                # Workflow templates (optional)
```

### AAP Configuration Files

**Project Configuration** (`project_*.json`):

Defines the source control settings for pulling playbooks and roles:

```json
{
  "name": "Role Name Automation",
  "scm_type": "git",
  "scm_url": "https://github.com/org/repo.git",
  "scm_branch": "main",
  "scm_update_on_launch": true,
  "organization": "Default"
}
```

**Execution Environment** (`execution_environment.json`):

References the container image with all dependencies:

```json
{
  "name": "Role Name EE",
  "image": "quay.io/org/ansible-ee:latest",
  "pull": "always",
  "organization": "Default"
}
```

**Job Template** (`job_template_*.json`):

Defines how to run the playbook:

```json
{
  "name": "Role Name - Execute",
  "job_type": "run",
  "inventory": "Production Inventory",
  "project": "Role Name Automation",
  "playbook": "playbooks/role_playbook.yml",
  "execution_environment": "Role Name EE",
  "ask_variables_on_launch": true,
  "survey_enabled": true,
  "extra_vars": {
    "ansible_python_interpreter": "/usr/bin/python3"
  }
}
```

**Survey Specification** (`survey_spec_*.json`):

Defines runtime prompts for job templates:

```json
{
  "name": "Role Configuration",
  "description": "Configure role execution parameters",
  "spec": [
    {
      "question_name": "Target Cluster",
      "question_description": "Kubernetes cluster to target",
      "required": true,
      "type": "text",
      "variable": "target_cluster",
      "min": 1,
      "max": 100,
      "default": ""
    },
    {
      "question_name": "Enable Check Mode",
      "question_description": "Run in check mode without making changes",
      "required": true,
      "type": "multiplechoice",
      "variable": "check_mode",
      "choices": ["true", "false"],
      "default": "false"
    }
  ]
}
```

**Workflow Template** (`workflow_*.json`):

Orchestrates multiple job templates:

```json
{
  "name": "Role Name - Full Workflow",
  "description": "Complete workflow with pre-checks and execution",
  "organization": "Default",
  "inventory": "Production Inventory",
  "workflow_nodes": [
    {
      "identifier": "preflight",
      "unified_job_template": "Role Name - Preflight Check",
      "success_nodes": ["execute"]
    },
    {
      "identifier": "execute",
      "unified_job_template": "Role Name - Execute"
    }
  ]
}
```

### AAP Configuration Patterns

**Multi-Template Pattern:**

Create separate job templates for different execution modes:

- `<Role> - Check Mode`: Validation and preflight checks
- `<Role> - Execute`: Full execution
- `<Role> - Rollback`: Rollback procedures

**Workflow Pattern:**

- Orchestrates multiple job templates
- Includes approval gates for production workflows
- Defines success/failure paths and notifications
- Useful for complex multi-step operations

### Creating AAP Configurations for New Roles

When creating a new role that should be runnable in AAP, follow these steps:

1. **Create Role Subdirectory**:

   ```bash
   mkdir -p aap_import/<role_name>
   ```

2. **Required Files**:

   - `README.md` - Comprehensive import guide with prerequisites, configuration steps, and troubleshooting
   - `import_to_aap.sh` - Automated import script using `awx` CLI or API calls
   - `project_*.json` - Project configuration for the Git repository
   - `execution_environment.json` - EE configuration
   - At least one `job_template_*.json` - Primary job template

3. **Best Practices**:

   **Naming Conventions**:
   - Project: `{Role Name} Automation`
   - Job Template: `{Role Name} - {Action}`
   - Workflow: `{Role Name} - Full Workflow`
   - EE: `{Role Name} EE` or use shared EE

   **Survey Specifications**:
   - Include surveys for all required runtime variables
   - Provide sensible defaults where possible
   - Use appropriate question types (text, integer, multiple choice)
   - Mark required fields explicitly
   - Include helpful descriptions and validation

   **Security**:
   - Never commit credentials to Git
   - Use AAP credential types for sensitive data
   - Implement approval gates for production workflows
   - Limit job template execution permissions appropriately

   **Multiple Job Templates**:
   - Create separate templates for different execution modes
   - Example: full run, preflight/check mode, accelerated mode
   - Allow users to test before full execution
   - Use consistent naming patterns

4. **Automated Import Script**:

   - Use `awx` CLI for programmatic import
   - Check for existing resources before creation
   - Provide clear success/failure messages
   - Include rollback instructions in comments
   - Set environment variables for configuration:

     ```bash
     export CONTROLLER_HOST=https://your-aap-server
     export CONTROLLER_USERNAME=admin
     export CONTROLLER_PASSWORD=your-password
     ```

5. **Documentation Requirements**:

   - Prerequisites (AAP version, permissions, dependencies)
   - Step-by-step import instructions
   - Configuration variable descriptions
   - Testing procedures
   - Troubleshooting section
   - Example execution commands

6. **Testing Import Configurations**:

   - Test project sync first
   - Verify execution environment availability
   - Test job templates with check mode
   - Validate survey questions and defaults
   - Test workflows end-to-end if applicable

### Import Methods

The project supports three import methods:

1. **Automated Script** (Recommended):

   ```bash
   cd aap_import/<role_name>
   ./import_to_aap.sh
   ```

2. **AWX CLI**:

   ```bash
   awx projects create --name "..." --scm_type git --scm_url "..."
   awx job_templates create --name "..." --project "..." --playbook "..."
   ```

3. **Web UI**: Manual creation following README instructions

4. **API/Curl**: Direct API calls using the JSON configuration files

### AAP Maintenance

When updating roles:

- Update corresponding AAP configurations
- Increment version numbers in documentation
- Test import process after changes
- Update survey specifications if new variables are added
- Document breaking changes in role README

### Documentation Standards

**IMPORTANT:** Follow these rules when working with documentation:

- **No emojis or icons** - Documentation must be professional and text-only
- **Ask before creating** - Always ask the user for approval before generating or modifying documentation files
- **No unsolicited documentation** - Never proactively create README files, markdown documentation, or similar without explicit user request

**Documentation File Placement:**

All documentation and markdown files must be placed in the `docs/` directory:

- **General documentation**: Place in `docs/` root (e.g., `docs/setup_guide.md`)
- **Role-specific documentation**: Create subdirectory `docs/<role_name>/` (e.g., `docs/portworx_upgrade/architecture.md`)
- **Collection-specific documentation**: Create subdirectory `docs/<collection_name>/` (e.g., `docs/px_backup/api_guide.md`)
- **Playbook-specific documentation**: Create subdirectory `docs/<playbook_name>/` (e.g., `docs/px_upgrade_playbook/usage.md`)
- **Filter plugin documentation**: Create subdirectory `docs/filters/` (e.g., `docs/filters/custom_filters_guide.md`)

**Examples:**

```text
docs/
├── general_overview.md          # General project documentation
├── portworx_upgrade/            # Role-specific docs
│   ├── architecture.md
│   ├── troubleshooting.md
│   └── upgrade_process.md
├── pxbackup/                    # Collection-specific docs
│   └── api_reference.md
├── px_upgrade_playbook/         # Playbook-specific docs
│   └── execution_guide.md
├── filters/                     # Filter plugin docs
│   ├── custom_filters_guide.md
│   └── filter_development.md
└── examples/                    # Code examples
    ├── filter_plugin_example.py
    └── module_example.py
```

**Exceptions:**

- `CLAUDE.md` - Repository root (project instructions for Claude Code)
- `README.md` - Repository root only (main project README)
- `aap_import/README.md` - AAP import main documentation
- `aap_import/<role_name>/README.md` - Role-specific AAP import guides

This applies to all documentation including:

- README files (except repository root and aap_import directories)
- Markdown documentation (*.md)
- Code comments and docstrings (emojis prohibited)
- Commit messages (emojis prohibited)

## Claude Code Workflow Requirements

### Virtual Environment Usage

**CRITICAL:** All Python and Ansible commands MUST use the virtual environment at `/development/git/ansible-playground/.venv`

- Python interpreter: `.venv/bin/python`
- Pip: `.venv/bin/pip`
- Ansible tools: `.venv/bin/ansible`, `.venv/bin/ansible-playbook`, `.venv/bin/ansible-lint`, `.venv/bin/ansible-galaxy`
- Linting tools: `.venv/bin/black`, `.venv/bin/isort`, `.venv/bin/flake8`, `.venv/bin/mypy`

### Automatic Quality Enforcement

After making code changes, automatically run appropriate tools:

**For Python files** (`.py` files, modules in `roles/*/library/`, filter plugins in `roles/*/filter_plugins/`):

1. `.venv/bin/isort <file>` - Sort imports
2. `.venv/bin/black <file>` - Format code
3. `.venv/bin/flake8 <file>` - Check for linting issues

**For Ansible files** (playbooks, roles, tasks):

1. `.venv/bin/ansible-lint <file-or-directory>` - Lint Ansible content

These tools run automatically without requiring user approval (configured in `.claude/settings.local.json`).

### Expected Behavior

When Claude Code modifies files, it should:

1. Make the requested changes
2. Automatically run the appropriate quality tools based on file type
3. Fix any issues found by the tools
4. Report the results to the user

This ensures all code maintains consistent quality and follows project standards.

### Git Commit Messages

**IMPORTANT:** Do NOT add Claude Code attribution or co-authorship to commit messages.

Commit messages should:

- Follow conventional commit format when appropriate
- Be concise and descriptive
- Focus on the "why" rather than the "what"
- Match the repository's existing commit style
- **NOT include** any Claude Code branding, attribution, or co-authorship footers

Bad example (DO NOT USE):

```text
Add new feature

Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

Good example:

```text
Add etcd defragmentation monitoring

Implements health check validation before and after defrag operations
to ensure cluster stability.
```
