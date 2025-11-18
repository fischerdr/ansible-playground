# Copilot Instructions for Ansible Projects

## Code Style and Standards

### Python Modules and Libraries

- Follow PEP 8 coding standards for Python code
- Use docstrings with Google-style formatting for all functions and classes
- Implement proper error handling with custom exceptions when needed
- Include type hints where appropriate
- Maintain backward compatibility in module interfaces

### Ansible Roles

- Use consistent naming conventions for role variables (snake_case)
- Follow the standard Ansible role directory structure
- Define default variables in defaults/main.yml
- Document all role variables in README.md files
- Implement proper task organization with logical grouping and clear names

### Collections

- Follow Ansible collection naming conventions (namespace.collection_name)
- Include proper metadata in galaxy.yml
- Use consistent documentation structure across collection modules
- Maintain versioning according to semantic versioning standards

## Lookup Expression Formatting Rules

### General Lookup Style

All lookup expressions must follow a consistent formatting style that includes:

- Proper multi-line argument formatting
- Consistent spacing and indentation
- Clear separation of parameters
- Appropriate use of string concatenation with `~` operator
- Proper handling of complex lookup arguments

### Specific Lookup Formatting Example

When using the `lookup()` function, format expressions as follows:

```yaml
vault_crt: >-
  {{
    lookup(
      'community.hashi_vault.hashi_vault',
      'secret=static_secrets/data/env/' ~ cluster_user ~ '/vault:vault.crt',
      'url=' ~ vault_address,
      'auth_method=token',
      'token=' ~ vault_token,
      'validate_certs=true',
      'namespace=ansible'
    ) | default('')
  }}
```

### Formatting Requirements

1. **Multi-line arguments**: Each lookup parameter should be on its own line with proper indentation
2. **String concatenation**: Use `~` operator for string concatenation with appropriate spacing
3. **Parameter separation**: Separate parameters with commas and proper spacing
4. **YAML formatting**: Use `>-\n` for multi-line strings to preserve formatting
5. **Default handling**: Always include `| default('')` for lookup expressions that may fail
6. **Quoting**: Use single quotes for lookup function arguments

### Parameter Order

Lookup parameters should be ordered consistently:

1. Main lookup type or plugin name
2. Secret path or identifier
3. URL or connection information
4. Authentication method and credentials
5. Security and validation settings
6. Namespace or context information

### Complex Lookup Examples

```yaml
# Example with multiple variables
database_password: >-
  {{
    lookup(
      'community.hashi_vault.hashi_vault',
      'secret=' ~ vault_secret_path ~ '/database',
      'url=' ~ vault_url,
      'auth_method=token',
      'token=' ~ vault_token,
      'validate_certs=true'
    ) | default('')
  }}

# Example with conditional logic
ssl_cert: >-
  {{
    lookup(
      'community.hashi_vault.hashi_vault',
      'secret=' ~ ssl_secret_path,
      'url=' ~ vault_address,
      'auth_method=token',
      'token=' ~ vault_token,
      'validate_certs=true'
    ) | default('')
  }} if ssl_enabled else ''
```

### Validation Rules

- All lookup expressions must be properly formatted with correct indentation
- No single-line lookup arguments that exceed 120 character limits
- All parameters must be clearly separated and readable
- Complex lookups must maintain proper structure for easy debugging
- Default values must always be specified for lookup failures

## Playbook Structure Requirements

### Document Header Preservation

All Ansible playbooks must preserve the YAML document header (`---`) at the top of the file:

```yaml
---
- name: Example playbook
  hosts: all
  become: true
  tasks:
    - name: Example task
      debug:
        msg: "Hello World"
```

### Task File Header Preservation

All task files must preserve the document header when applicable:

```yaml
---
- name: Include additional configuration
  include_tasks: configure.yml
```

### Configuration for Copilot

To prevent Copilot from removing document headers, add this to your copilot-instructions.md file:

**Copilot Configuration Settings:**

1. Configure Copilot to respect YAML document structure
2. Ensure that the first line of all Ansible files is preserved as `---`
3. Set preference to maintain document headers for multi-document YAML files
4. Disable automatic removal of document delimiters in Ansible contexts

### Manual Override Instructions

When Copilot removes the `---` header:

1. Manually re-add the header at the beginning of each playbook file
2. Ensure that the header is followed by a newline character
3. Verify that the header is not removed during subsequent edits

### Validation Check

Before committing Ansible files, verify that:

- Playbook files start with `---`
- Task files that are part of multi-document YAML structures maintain headers
- No document headers are stripped during automated editing

## Git Workflow

### Branching Strategy

- Main branch should contain stable, production-ready code
- Feature branches should be created for new development work
- Pull requests must include automated testing results before merging
- All changes must pass linting and unit tests

### Commit Messages

- Use conventional commit format: <type>(<scope>): <subject>
- Types: feat, fix, docs, style, refactor, test, chore
- Include issue reference when applicable (fixes #123)

## Testing Strategy

### Unit Tests

- Write unit tests for custom Python modules using pytest
- Test edge cases and error conditions
- Ensure 100% coverage for critical business logic
- Run tests locally before committing changes

### Integration Tests

- Create integration tests for roles using molecule
- Validate role functionality across different platforms
- Test complete playbook execution flows
- Document test scenarios in README files

### Linting and Validation

- Use ansible-lint for playbook validation
- Apply yamllint for YAML file validation
- Run flake8 for Python code quality checks
- Ensure all documentation is consistent and up-to-date

## Documentation Requirements

### Role Documentation

- Include comprehensive README.md files in each role directory
- Document all variables with default values and descriptions
- Provide examples of usage
- List required dependencies and prerequisites

### Collection Documentation

- Maintain a collection-level README.md
- Document module interfaces clearly
- Include installation instructions for users
- Provide migration guides when applicable

### General Project Documentation

- Keep CHANGELOG.md updated with version history
- Document development environment setup
- Include troubleshooting guides for common issues

## Security Considerations

### Secrets Management

- Never commit sensitive data or credentials to the repository
- Use Ansible Vault for encrypting sensitive variables
- Implement proper access controls for vault keys
- Review all committed files for potential secrets exposure

### Code Security

- Sanitize input parameters in Python modules
- Validate all external inputs before processing
- Follow least privilege principles in playbooks
- Regular security scanning of dependencies

## Development Environment Setup

### Prerequisites

- Ansible 2.10 or higher
- Python 3.8 or higher
- Required Python packages listed in requirements.txt or galaxy.yml
- Molecule for testing (optional but recommended)

### Local Development

- Use virtual environments for Python development
- Set up pre-commit hooks for automated linting
- Configure IDE to follow project coding standards
- Ensure consistent line endings across platforms

## CI/CD Integration

### Automated Checks

- Run linters on every commit
- Execute unit tests automatically in CI pipeline
- Perform integration testing with molecule
- Validate playbook syntax before deployment

### Release Process

- Tag releases with semantic versioning
- Generate changelogs automatically from commit history
- Publish collections to Ansible Galaxy
- Maintain release notes for each version

## Best Practices

### Code Reusability

- Favor reusable modules over copy-paste solutions
- Create generic roles that can be customized through variables
- Use Ansible's built-in modules when possible before writing custom code
- Share common functionality across multiple roles or collections

### Performance Optimization

- Minimize the number of tasks per play
- Use proper caching mechanisms where applicable
- Optimize loops and conditionals
- Profile playbook execution times regularly

### Error Handling

- Implement graceful error handling in all modules
- Provide clear, actionable error messages to users
- Log errors appropriately for debugging purposes
- Include recovery procedures in role documentation

## Conflict Resolution

### Merge Conflicts

- Communicate with team members before making significant changes
- Use feature branches to isolate work
- Review pull requests thoroughly before merging
- Rebase feature branches regularly to stay up-to-date with main branch

### Version Conflicts

- Use semantic versioning consistently
- Maintain backward compatibility when possible
- Document breaking changes in release notes
- Coordinate major version updates across teams
