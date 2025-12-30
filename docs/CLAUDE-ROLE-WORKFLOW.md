# CLAUDE.md - Ansible Role Development Workflow Integration

This file provides guidance to Claude Code (claude.ai/code) when working with Ansible roles in this repository.

## Role Development Workflow

**CRITICAL:** When developing Ansible roles for production distribution, follow the comprehensive workflow documented in:

**`ANSIBLE-ROLE-DEVELOPMENT-WORKFLOW.md`**

This document defines the complete process from initial development in the monorepo through to standalone git repository creation.

### Quick Reference

**Development Phase:**

- Build roles in monorepo: `roles/<role_name>/`
- Use modular task architecture (orchestrator pattern)
- Follow coding standards from main CLAUDE.md
- Test iteratively with shared tooling

**Distribution Phase:**

- Run quality checks (ansible-lint, syntax, Python formatting)
- Create complete documentation set (README, INSTALL, CHANGELOG, LICENSE)
- Build tarball with **top-level structure** (NOT nested)
- Verify package integrity and functionality

**Production Phase:**

- Create standalone git repository from tarball
- Set up CI/CD workflows
- Tag releases properly
- Distribute to users

### Automation Scripts

Use the provided automation scripts:

```bash
# Create distribution tarball
./scripts/create_role_distribution.sh <role_name> <version>

# Complete workflow (development to production)
./scripts/role_to_production.sh <role_name> <version> [options]
```

### Critical Requirements

**Tarball Structure:**

- Role directories (defaults/, meta/, tasks/, etc.) MUST be at top level
- NOT nested under a subdirectory
- Enables dual-purpose: direct role installation OR standalone git repo

**Quality Standards:**

- All code must pass ansible-lint
- Python code must pass black, isort, flake8
- Custom modules/filters follow templates in main CLAUDE.md
- Comprehensive documentation required

**Version Control:**

- Tag releases in monorepo: `<role_name>-v<version>`
- Update CHANGELOG.md for each version
- Create annotated tags with release notes

## Integration with Main CLAUDE.md

This workflow document **supplements** the main CLAUDE.md in the monorepo. When working on roles:

1. **Development standards** - Use CLAUDE.md for:
   - Ansible coding best practices
   - Custom module/filter templates
   - Python code standards
   - Testing requirements
   - Virtual environment usage

2. **Distribution workflow** - Use ANSIBLE-ROLE-DEVELOPMENT-WORKFLOW.md for:
   - Complete development to production process
   - Documentation requirements
   - Tarball creation steps
   - Standalone repository setup
   - Quality checklists

## When to Use This Workflow

Apply this workflow when:

- Creating a new production-ready role
- Preparing existing role for external distribution
- Creating standalone git repository for a role
- Packaging role for other teams
- Releasing new role version

## Key Differences from Main CLAUDE.md

**Main CLAUDE.md:**

- Repository-wide standards
- Technical implementation details
- Tool usage and configuration
- Code quality requirements

**This Workflow:**

- End-to-end process definition
- Distribution package creation
- Standalone repository setup
- Production readiness checklists

Both documents work together to ensure high-quality, distributable Ansible roles.

---

**For complete details, always reference:**

- `ANSIBLE-ROLE-DEVELOPMENT-WORKFLOW.md` - Complete workflow
- Main `CLAUDE.md` - Coding standards and best practices
