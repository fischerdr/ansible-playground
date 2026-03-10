# Ansible Code Examples

This directory contains comprehensive examples for developing custom Ansible modules, filter plugins, and following best practices in this project.

## Available Examples

### 1. Custom Module Example

**File:** `custom_module_example.py`

A complete, production-ready example of a custom Ansible module demonstrating:

- Proper module structure with DOCUMENTATION, EXAMPLES, and RETURN sections
- Kubernetes resource management (pods, deployments, services, configmaps)
- State-based resource handling (present/absent)
- Comprehensive error handling and validation
- Check mode support for dry-run testing
- Idempotency implementation
- Multiple resource types in a single module
- Update detection and change reporting

**Key Features:**
- Full argument specification with validation
- Kubernetes API integration with proper error handling
- Resource existence checking before operations
- Proper change detection for updates
- Support for replicas and image updates
- Comprehensive return value documentation

**Usage:**
```python
# Copy template structure for new modules
# Adapt to your specific use case
# Follow the patterns for error handling, validation, and state management
```

### 2. Filter Plugin Example

**File:** `filter_plugin_example.py`

A comprehensive filter plugin with multiple filter functions:

**Filters Included:**
- `extract_field` - Extract specific fields from list of dictionaries
- `filter_by_status` - Filter items by status field
- `transform_keys` - Transform dictionary keys using a mapping
- `normalize_list` - Deduplicate and normalize lists
- `deep_merge` - Recursively merge dictionaries
- `safe_get` - Safely access nested dictionary values with dot notation
- `to_key_value_pairs` - Convert dictionary to list of key-value pairs

**Key Features:**
- Comprehensive type validation
- Proper error handling with AnsibleFilterError
- Static methods for better performance
- Recursive operations for nested data
- Complete documentation with examples
- Runnable test code at the bottom

**Usage:**
```yaml
# Extract field from pods
- set_fact:
    pod_names: "{{ pods | extract_field('name') }}"

# Filter by status
- set_fact:
    running_pods: "{{ pods | filter_by_status('Running') }}"

# Deep merge configurations
- set_fact:
    final_config: "{{ base_config | deep_merge(override_config) }}"
```

### 3. Module Testing Example

**File:** `module_testing_example.py`

Comprehensive testing patterns for custom Ansible modules:

**Includes:**
- Unit test examples with pytest and mock
- Test fixtures and helper functions
- Multiple test scenarios (success, failure, idempotency)
- Check mode testing
- Error handling tests
- Integration test playbook examples
- pytest configuration examples

**Test Scenarios Covered:**
- Valid argument validation
- Missing required parameters
- Invalid parameter values
- Successful resource creation
- Resource already exists (idempotency)
- Resource deletion
- Check mode behavior
- Kubernetes API errors
- Deployment updates
- Replicas validation

**Usage:**
```bash
# Run unit tests
pytest tests/unit/test_k8s_resource_manager.py

# Run with coverage
pytest --cov=library --cov-report=html tests/unit/

# Run integration tests
ansible-playbook tests/integration/test_custom_module.yml
```

### 4. changed_when and failed_when Examples

**File:** `changed_when_failed_when_examples.yml`

Comprehensive examples of proper changed_when and failed_when usage:

**Categories:**
1. **Read-only operations** - Always use `changed_when: false`
2. **Grep operations** - Handle both 0 and 1 exit codes
3. **State-modifying operations** - Detect changes from output
4. **Expected output validation** - Report unexpected states
5. **Retry operations** - Use with until/retries
6. **Multiple valid exit codes** - Handle various success conditions
7. **Combined output and exit code checks** - Comprehensive error detection
8. **Complex conditionals** - Advanced logic for change detection
9. **Multi-line commands** - Proper pipefail usage

**Common Patterns:**

```yaml
# Read-only
changed_when: false
failed_when: result.rc != 0

# Grep operations
changed_when: false
failed_when: result.rc not in [0, 1]

# State changes
changed_when: "'created' in result.stdout or 'updated' in result.stdout"
failed_when: result.rc != 0

# Unexpected state
changed_when: result.stdout_lines | length == 0
failed_when: result.rc != 0
```

## How to Use These Examples

### For Custom Modules

1. Copy `custom_module_example.py` structure
2. Modify DOCUMENTATION section with your module's parameters
3. Update EXAMPLES with your use cases
4. Implement your logic in the main function
5. Keep the error handling and validation patterns
6. Add comprehensive tests using patterns from `module_testing_example.py`

### For Filter Plugins

1. Copy `filter_plugin_example.py` structure
2. Add your filter methods to the FilterModule class
3. Update the `filters()` method to include your filters
4. Implement proper type validation
5. Use AnsibleFilterError for all error conditions
6. Document with DOCUMENTATION, EXAMPLES, RETURN sections

### For Playbook Tasks

1. Reference `changed_when_failed_when_examples.yml`
2. Find the pattern that matches your use case
3. Copy the relevant example
4. Adapt to your specific command
5. Test thoroughly to ensure proper change detection

## Quality Standards

All custom code must pass:

```bash
# Python formatting and linting
.venv/bin/isort <file>.py
.venv/bin/black <file>.py
.venv/bin/flake8 <file>.py
.venv/bin/mypy <file>.py

# Ansible linting
.venv/bin/ansible-lint <playbook>.yml

# Testing
.venv/bin/pytest tests/unit/
ansible-playbook tests/integration/<test>.yml
```

## Best Practices Summary

### Custom Modules

- Always support check mode
- Validate all input parameters
- Return meaningful error messages
- Implement idempotency
- Use specific exception types
- Include comprehensive documentation
- Test both success and failure paths

### Filter Plugins

- Validate input types before processing
- Use descriptive error messages
- Provide comprehensive documentation
- Use static methods when possible
- Never modify input values
- Avoid I/O operations in filters
- Test edge cases

### Ansible Tasks

- Use `changed_when: false` for read-only operations
- Handle all valid exit codes in `failed_when`
- Use `set -o pipefail` for multi-command pipelines
- Test output content for change detection
- Document why you're using specific patterns
- Consider retries with `until` for transient failures

## Additional Resources

- Main project documentation: `CLAUDE.md` (repository root)
- Ansible module development: https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html
- Filter plugin development: https://docs.ansible.com/ansible/latest/dev_guide/developing_plugins.html#filter-plugins
- pytest documentation: https://docs.pytest.org/
- Kubernetes Python client: https://github.com/kubernetes-client/python

## Contributing

When adding new examples:

1. Follow the existing structure and format
2. Include comprehensive documentation
3. Add multiple realistic use cases
4. Include error handling examples
5. Update this README with the new example
6. Ensure all code passes quality checks
