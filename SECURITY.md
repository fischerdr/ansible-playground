# Security Policy

## Supported Versions

This project is currently under active development. We recommend using the latest version of the codebase to ensure you have all security updates.

## Security Considerations

### Environment and Execution

- All execution environments are defined in `execution-environment.yml`
- Container runtime is set to Docker
- Only approved base images are used (CentOS Stream, Fedora Stream)
- Ansible Navigator is configured to run using Docker for isolation

### Secrets Management

- Sensitive information (API keys, passwords, tokens) must be stored in HashiCorp Vault
- No secrets should be committed to the repository
- Environment variables are used for temporary secret storage during runtime
- Vault configuration and access is managed through dedicated roles

### API Security

- All external service communications (Kubernetes, Vault, Portworx) must use HTTPS
- API tokens and credentials must be rotated regularly
- PurePX API access is restricted through the PurePX module

### File System Security

- Temporary files must be stored in the `tmp/` directory
- Cache files must be stored in the `cache/` directory
- All temporary and cache directories should be included in `.gitignore`

### Code Security

1. **Input Validation**
   - All inputs from external sources must be validated
   - Use proper error handling and logging
   - Implement appropriate access controls

2. **Logging and Monitoring**
   - All operations must be logged for audit purposes
   - Errors must be logged with appropriate detail
   - Sensitive information must not be logged

3. **Testing**
   - Security tests must be included in the test suite
   - Regular security scans of dependencies
   - Automated testing using pytest

### Best Practices

1. **Code Quality**
   - Use Python 3.9+ with type hints
   - Follow secure coding guidelines
   - Regular code reviews required
   - Use black for code formatting
   - Use flake8 for code linting
   - Use isort for import sorting

2. **Documentation**
   - Keep security documentation up to date
   - Document all security-related configurations
   - Include security considerations in role documentation

3. **Collection and Role Management**
   - Use collections from `collections/` directory
   - Use roles from `roles/` directory
   - Use FQCN for built-in module actions

## Reporting a Vulnerability

If you discover a security vulnerability in this project:

1. **Do Not** create a public GitHub issue
2. Document the vulnerability with details about how to reproduce it
3. Contact the project maintainers directly
4. Allow reasonable time for the vulnerability to be addressed before disclosure

## Security Updates

- Security patches will be released as soon as possible
- Users will be notified of security-related updates
- Follow the project's release notes for security-related changes

## Compliance

Ensure your usage of this project complies with:

- Your organization's security policies
- Relevant industry standards
- Data protection regulations

## Regular Security Reviews

The following should be reviewed regularly:

1. Dependencies for known vulnerabilities
2. Access controls and permissions
3. Secrets rotation
4. Security documentation
5. Logging and monitoring configuration
