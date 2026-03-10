# Ansible Code Review Checklist

**Document Version:** 1.0.0  
**Last Updated:** 2025-02-10  
**Target Audience:** Code reviewers and pull request authors  
**Purpose:** Ensure consistent, high-quality Ansible code through systematic review

---

## Table of Contents

1. [How to Use This Checklist](#how-to-use-this-checklist)
2. [Pre-Submission Checklist (Author)](#pre-submission-checklist-author)
3. [Code Review Checklist (Reviewer)](#code-review-checklist-reviewer)
4. [Automated Checks](#automated-checks)
5. [Manual Review Guidelines](#manual-review-guidelines)
6. [Common Review Comments](#common-review-comments)
7. [Approval Criteria](#approval-criteria)
8. [Review Process Flow](#review-process-flow)

---

## How to Use This Checklist

### For Pull Request Authors

**Before submitting PR:**

1. Run through [Pre-Submission Checklist](#pre-submission-checklist-author)
2. Ensure all automated checks pass
3. Self-review your changes
4. Fill out PR template completely

**Example self-review:**

```bash
# Run complete quality check
./scripts/quality_check.sh

# Review your own diff
git diff main...your-branch

# Check PR description complete
cat .github/pull_request_template.md
```

### For Code Reviewers

**When reviewing PR:**

1. Verify automated checks passed
2. Use [Code Review Checklist](#code-review-checklist-reviewer)
3. Leave constructive comments
4. Approve only when all criteria met

**Review workflow:**

```markdown
1. Read PR description and understand intent
2. Check automated test results
3. Review code changes systematically
4. Test locally if complex changes
5. Leave feedback or approve
```

### Severity Levels

**BLOCKER** - Must fix before merge
- Security issues
- Breaking changes
- Syntax errors
- Test failures

**MAJOR** - Should fix before merge
- Logic errors
- Missing error handling
- Poor naming
- Missing documentation

**MINOR** - Can fix after merge
- Formatting inconsistencies
- Typos in comments
- Optimization opportunities
- Style preferences

**SUGGESTION** - Optional improvements
- Alternative approaches
- Performance tips
- Future enhancements
- Learning opportunities

---

## Pre-Submission Checklist (Author)

### Before Creating Pull Request

Copy this checklist into your PR description:

```markdown
## Pre-Submission Checklist

### Code Quality
- [ ] All files pass syntax check (`ansible-playbook --syntax-check`)
- [ ] Ansible-lint passes with production profile
- [ ] YAML lint passes
- [ ] Python files formatted with black (if applicable)
- [ ] Python imports sorted with isort (if applicable)
- [ ] No flake8 errors (if applicable)

### Testing
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Tested in check mode (`--check`)
- [ ] Tested with tags (`--tags`)
- [ ] Tested in test environment
- [ ] Manual testing completed

### Standards Compliance
- [ ] All modules use FQCN
- [ ] All shell/command tasks have `changed_when`
- [ ] All shell/command tasks have `failed_when`
- [ ] Error handling (block/rescue/always) for critical operations
- [ ] Variables follow naming conventions
- [ ] Tasks have meaningful names
- [ ] Proper tags applied

### Documentation
- [ ] README updated (if needed)
- [ ] CHANGELOG updated
- [ ] Variables documented
- [ ] Complex logic has comments
- [ ] Examples provided (if new feature)

### Kubernetes/OpenShift Specific
- [ ] Using kubernetes.core modules instead of oc/kubectl commands
- [ ] Using structured data instead of text parsing
- [ ] Proper label selectors instead of grep
- [ ] Resource verification after operations

### Self-Review
- [ ] Reviewed own diff for issues
- [ ] No debug statements left in code
- [ ] No commented-out code
- [ ] No TODO comments without ticket numbers
- [ ] No secrets or credentials in code
```

### Quick Pre-Flight Script

Create `scripts/pre_submit_check.sh`:

```bash
#!/bin/bash
# Quick pre-submission validation

set -e

echo "=== Pre-Submission Checks ==="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ISSUES=0

# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${RED}✗ Virtual environment not found${NC}"
    ISSUES=$((ISSUES + 1))
else
    echo -e "${GREEN}✓ Virtual environment found${NC}"
fi

# Activate venv
source .venv/bin/activate 2>/dev/null || true

# Syntax check
echo ""
echo "Checking syntax..."
if find playbooks roles -name "*.yml" -exec ansible-playbook --syntax-check {} \; 2>&1 | grep -q "ERROR"; then
    echo -e "${RED}✗ Syntax errors found${NC}"
    ISSUES=$((ISSUES + 1))
else
    echo -e "${GREEN}✓ Syntax check passed${NC}"
fi

# Ansible lint
echo ""
echo "Running ansible-lint..."
if ansible-lint --profile=production playbooks/ roles/ 2>&1 | grep -q "error"; then
    echo -e "${RED}✗ Ansible-lint errors found${NC}"
    ISSUES=$((ISSUES + 1))
else
    echo -e "${GREEN}✓ Ansible-lint passed${NC}"
fi

# Check for debugging statements
echo ""
echo "Checking for debug statements..."
DEBUG_FOUND=$(git diff --cached | grep -E "^\+.*import pdb|^\+.*breakpoint\(\)" || echo "")
if [ -n "$DEBUG_FOUND" ]; then
    echo -e "${RED}✗ Debug statements found${NC}"
    echo "$DEBUG_FOUND"
    ISSUES=$((ISSUES + 1))
else
    echo -e "${GREEN}✓ No debug statements${NC}"
fi

# Check for secrets
echo ""
echo "Checking for potential secrets..."
SECRET_PATTERNS="password.*=|api_key.*=|secret.*=|token.*="
SECRETS_FOUND=$(git diff --cached | grep -iE "^\+.*($SECRET_PATTERNS)" || echo "")
if [ -n "$SECRETS_FOUND" ]; then
    echo -e "${YELLOW}⚠ Potential secrets found${NC}"
    echo "$SECRETS_FOUND"
    echo "Please verify these are not actual secrets"
fi

# Check for FQCN
echo ""
echo "Checking for missing FQCN..."
NON_FQCN=$(git diff --cached --name-only | grep -E "\.ya?ml$" | xargs grep -E "^\s+[a-z_]+:" 2>/dev/null | grep -v "ansible\." | grep -v "kubernetes\." | grep -v "name:" | grep -v "when:" | grep -v "tags:" || echo "")
if [ -n "$NON_FQCN" ]; then
    echo -e "${YELLOW}⚠ Possible missing FQCN found${NC}"
    echo "Review these lines:"
    echo "$NON_FQCN" | head -5
fi

# Summary
echo ""
echo "=== Summary ==="
if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo "Ready to create pull request"
    exit 0
else
    echo -e "${RED}✗ Found $ISSUES issue(s)${NC}"
    echo "Please fix before submitting"
    exit 1
fi
```

Make it executable:

```bash
chmod +x scripts/pre_submit_check.sh
```

---

## Code Review Checklist (Reviewer)

### Phase 1: Automated Checks (2 minutes)

**Verify CI/CD passed:**

- [ ] Syntax validation passed
- [ ] Ansible-lint passed
- [ ] YAML lint passed
- [ ] Python quality checks passed (if applicable)
- [ ] All tests passed

**If any automated checks failed:** Request fixes before manual review.

### Phase 2: PR Metadata (3 minutes)

**Check PR description:**

- [ ] Clear title describing change
- [ ] Problem statement provided
- [ ] Solution approach explained
- [ ] Testing performed described
- [ ] Breaking changes noted (if any)
- [ ] Pre-submission checklist completed

**Red flags:**
- ❌ Title: "Fix stuff" or "Updates"
- ❌ Description: "See commits"
- ❌ No testing described
- ❌ Checklist not filled out

**Good examples:**
- ✅ Title: "Replace oc commands with k8s modules in cluster_setup playbook"
- ✅ Description explains why, how, and what was tested
- ✅ Checklist fully completed

### Phase 3: Code Structure Review (5 minutes)

**Directory Structure:**

- [ ] Files in correct locations
- [ ] New files follow naming conventions
- [ ] No files in root that should be in subdirectories

**Role Structure (if applicable):**

- [ ] Proper role directory structure
- [ ] tasks/main.yml is orchestrator only
- [ ] Task files named appropriately
- [ ] README.md present and complete
- [ ] defaults/main.yml has all variables

**Playbook Structure:**

- [ ] Proper playbook header comments
- [ ] Logical task organization
- [ ] Appropriate use of roles vs tasks
- [ ] pre_tasks and post_tasks used correctly

### Phase 4: Code Quality Review (10 minutes)

**FQCN Usage:**

```yaml
# Review for this pattern
✅ GOOD:
- name: Create directory
  ansible.builtin.file:
    path: /tmp/work
    state: directory

❌ BAD:
- name: Create directory
  file:
    path: /tmp/work
    state: directory
```

**Task Naming:**

```yaml
# Review for this pattern
✅ GOOD:
- name: Ensure application configuration directory exists
  ansible.builtin.file: ...

- name: Verify cluster connectivity before operations
  kubernetes.core.k8s_cluster_info: ...

❌ BAD:
- name: Create dir
  ansible.builtin.file: ...

- name: Check
  kubernetes.core.k8s_cluster_info: ...
```

**Variable Naming:**

```yaml
# Review for this pattern
✅ GOOD:
vars:
  cluster_setup_namespace: "kube-system"
  cluster_setup_timeout: 300
  cluster_setup_enable_verification: true

❌ BAD:
vars:
  ns: "kube-system"
  to: 300
  verify: true
```

**Shell Command Review:**

```yaml
# CRITICAL: Review every shell/command task

✅ ACCEPTABLE (with guards):
- name: Get node information (kubectl required for specific format)
  ansible.builtin.shell: |
    kubectl get nodes -o custom-columns=NAME:.metadata.name,STATUS:.status.conditions[-1].type
  register: nodes
  changed_when: false
  failed_when: nodes.rc != 0
  # Comment explaining why shell is necessary

❌ REJECT (should use module):
- name: Get pods
  shell: oc get pods -n {{ namespace }}
  # Should use kubernetes.core.k8s_info

❌ REJECT (missing guards):
- name: Update config
  shell: echo "setting=value" >> /etc/config
  # Missing changed_when and failed_when
```

**Comment when shell/command is used:**
```markdown
Why is shell/command being used here instead of a module?

Acceptable reasons:
- No module exists for this operation
- Module doesn't support required parameters
- External tool interaction required

Not acceptable:
- "It's easier"
- "I don't know the module"
```

### Phase 5: Kubernetes/OpenShift Patterns (5 minutes)

**Module Usage:**

```yaml
# Review for proper k8s module usage

✅ GOOD:
- name: Get deployment status
  kubernetes.core.k8s_info:
    api_version: apps/v1
    kind: Deployment
    name: myapp
    namespace: "{{ namespace }}"
  register: deployment

❌ BAD:
- name: Get deployment
  shell: oc get deployment myapp -n {{ namespace }}
  register: deployment
```

**Structured Data Usage:**

```yaml
# Review for proper data handling

✅ GOOD:
- name: Count running pods
  set_fact:
    running_count: "{{ pods.resources | selectattr('status.phase', 'equalto', 'Running') | list | length }}"

❌ BAD:
- name: Count running pods
  shell: oc get pods | grep Running | wc -l
  register: running_count
```

**Resource Creation:**

```yaml
# Review resource creation patterns

✅ GOOD:
- name: Create deployment
  kubernetes.core.k8s:
    state: present
    definition:
      apiVersion: apps/v1
      kind: Deployment
      # ... full definition

❌ BAD:
- name: Create deployment
  shell: |
    cat <<EOF | oc apply -f -
    apiVersion: apps/v1
    kind: Deployment
    ...
    EOF
```

**Comment if oc/kubectl found:**
```markdown
This should use kubernetes.core modules instead of oc/kubectl commands.

Suggested replacement:
[provide example]

See: docs/ansible/KUBERNETES-PATTERNS.md
```

### Phase 6: Error Handling Review (5 minutes)

**Critical Operations:**

```yaml
# Every critical operation should have error handling

✅ GOOD:
- name: Update cluster configuration
  block:
    - name: Apply configuration
      kubernetes.core.k8s:
        definition: "{{ config }}"
      register: result
    
    - name: Verify application succeeded
      kubernetes.core.k8s_info:
        api_version: v1
        kind: ConfigMap
        name: "{{ config_name }}"
      register: verification
      until: verification.resources | length > 0
      retries: 10
      delay: 3
  
  rescue:
    - name: Log failure details
      debug:
        msg: "Configuration update failed: {{ ansible_failed_result.msg }}"
    
    - name: Revert changes if needed
      kubernetes.core.k8s:
        state: absent
        definition: "{{ config }}"
      when: revert_on_failure | default(false)
    
    - name: Fail with context
      fail:
        msg: "Configuration update failed"
  
  always:
    - name: Cleanup temporary files
      file:
        path: /tmp/config_work
        state: absent

❌ BAD:
- name: Update cluster configuration
  kubernetes.core.k8s:
    definition: "{{ config }}"
  # No error handling
```

**Checklist:**
- [ ] Critical operations wrapped in block/rescue/always
- [ ] Rescue block provides diagnostic info
- [ ] Always block cleans up resources
- [ ] Error messages are clear and actionable

**Comment if error handling missing:**
```markdown
This critical operation needs error handling:

Please add block/rescue/always:
- rescue: Collect diagnostics, attempt recovery
- always: Clean up resources

See: docs/ansible/COMPREHENSIVE-GUIDE.md#error-handling-patterns
```

### Phase 7: Idempotency Review (5 minutes)

**Test for idempotency:**

```yaml
# Ask: Can this run multiple times safely?

✅ GOOD (idempotent):
- name: Ensure configuration file exists
  ansible.builtin.copy:
    dest: /etc/app.conf
    content: |
      setting=value
  # Only changes if content differs

❌ BAD (not idempotent):
- name: Add configuration
  ansible.builtin.shell: |
    echo "setting=value" >> /etc/app.conf
  # Adds duplicate line every run
```

**Checklist:**
- [ ] Operations won't cause issues if run multiple times
- [ ] "changed" status only when actual changes made
- [ ] No duplicate resource creation
- [ ] State-based operations (not append-based)

**Comment if not idempotent:**
```markdown
This operation is not idempotent - running multiple times will cause issues.

Problem: [describe issue]

Suggested fix: [provide idempotent approach]
```

### Phase 8: Testing Review (3 minutes)

**Test Coverage:**

- [ ] New functionality has tests
- [ ] Edge cases considered
- [ ] Error paths tested
- [ ] Test in check mode works

**Test Quality:**

```yaml
# Review test playbooks

✅ GOOD:
- name: Test cluster_setup role
  hosts: localhost
  tasks:
    - name: Test with valid input
      include_role:
        name: cluster_setup
      vars:
        cluster_setup_namespace: test-namespace
    
    - name: Verify role executed successfully
      assert:
        that:
          - cluster_setup_status == "success"
    
    - name: Test idempotency
      include_role:
        name: cluster_setup
      vars:
        cluster_setup_namespace: test-namespace
    
    - name: Verify no changes on second run
      assert:
        that:
          - not ansible_changed

❌ BAD:
# No tests at all
```

**Comment if tests missing:**
```markdown
Please add tests for this functionality:

Required tests:
- [ ] Happy path test
- [ ] Error handling test
- [ ] Idempotency test

See: tests/integration/ for examples
```

### Phase 9: Documentation Review (3 minutes)

**README.md:**

- [ ] Updated with new features
- [ ] Variable documentation complete
- [ ] Usage examples provided
- [ ] Prerequisites listed

**Inline Comments:**

```yaml
# Review comments for complex logic

✅ GOOD:
- name: Monitor upgrade with dual timeout strategy
  # Using both global and inactivity timeouts to handle:
  # 1. Overall operation taking too long (global)
  # 2. Upgrade appearing stuck with no progress (inactivity)
  # This prevents infinite waits while allowing slow but steady progress
  block:
    # ... implementation

❌ BAD:
- name: Do monitoring
  # Monitor stuff
  block:
    # ... complex logic with no explanation
```

**CHANGELOG.md:**

- [ ] Entry added to CHANGELOG
- [ ] Version incremented appropriately
- [ ] Changes categorized (Added, Changed, Fixed, etc.)

**Comment if documentation missing:**
```markdown
Please update documentation:

Required:
- [ ] Add usage example to README
- [ ] Document new variables
- [ ] Add CHANGELOG entry
- [ ] Explain complex logic in comments
```

### Phase 10: Security Review (2 minutes)

**Security Checklist:**

- [ ] No hardcoded credentials
- [ ] No secrets in code
- [ ] Sensitive data uses no_log: true
- [ ] Vault used for secrets
- [ ] Proper file permissions set

**Security Red Flags:**

```yaml
❌ REJECT:
- name: Configure database
  ansible.builtin.copy:
    content: |
      db_password=SuperSecret123
    dest: /etc/db.conf

- name: API call
  uri:
    url: https://api.example.com
    headers:
      Authorization: "Bearer hardcoded-token-here"

❌ REJECT (should use no_log):
- name: Set password
  shell: echo "{{ password }}" | some_command
  # Password visible in logs

✅ GOOD:
- name: Configure database
  ansible.builtin.template:
    src: db.conf.j2
    dest: /etc/db.conf
  vars:
    db_password: "{{ vault_db_password }}"
  no_log: true

- name: API call
  uri:
    url: https://api.example.com
    headers:
      Authorization: "Bearer {{ vault_api_token }}"
  no_log: true
```

**Comment if security issue found:**
```markdown
🔒 SECURITY ISSUE:

[Describe issue]

This is a BLOCKER - must fix before merge.

Required action: [specific fix]

See: Ansible Vault documentation
```

---

## Automated Checks

### CI/CD Pipeline Configuration

**GitHub Actions Example:**

```yaml
# .github/workflows/pr-checks.yml
name: PR Quality Checks

on:
  pull_request:
    branches: [main, develop]

jobs:
  quality-checks:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Syntax Check
        run: |
          for playbook in playbooks/*.yml; do
            ansible-playbook --syntax-check "$playbook"
          done
      
      - name: Ansible Lint
        run: |
          ansible-lint --profile=production playbooks/ roles/
      
      - name: YAML Lint
        run: |
          yamllint -c .yamllint .
      
      - name: Python Quality (if applicable)
        run: |
          if ls roles/*/library/*.py 2>/dev/null; then
            black --check roles/*/library/
            isort --check roles/*/library/
            flake8 roles/*/library/
          fi
      
      - name: Security Scan
        run: |
          # Check for potential secrets
          ! git diff origin/main | grep -iE "password.*=|api_key.*=|secret.*="
```

**GitLab CI Example:**

```yaml
# .gitlab-ci.yml
stages:
  - validate
  - test

syntax-check:
  stage: validate
  script:
    - pip install -r requirements.txt
    - find playbooks -name "*.yml" -exec ansible-playbook --syntax-check {} \;

ansible-lint:
  stage: validate
  script:
    - pip install -r requirements.txt
    - ansible-lint --profile=production playbooks/ roles/
  allow_failure: false

yaml-lint:
  stage: validate
  script:
    - pip install yamllint
    - yamllint -c .yamllint .

python-quality:
  stage: validate
  script:
    - pip install black isort flake8
    - black --check roles/*/library/ || true
    - isort --check roles/*/library/ || true
    - flake8 roles/*/library/

integration-tests:
  stage: test
  script:
    - ansible-playbook -i inventory/test tests/integration/test_suite.yml
  only:
    - merge_requests
```

### Required Status Checks

**Configure branch protection:**

```markdown
Required checks before merge:
- ✅ Syntax validation
- ✅ Ansible-lint (production profile)
- ✅ YAML lint
- ✅ Python quality (if applicable)
- ✅ Integration tests (if available)
- ✅ At least 1 approval from code owner
```

---

## Manual Review Guidelines

### How to Provide Constructive Feedback

**Good Feedback Pattern:**

```markdown
[SEVERITY] [LOCATION] Clear description of issue

Problem: [What's wrong]
Impact: [Why it matters]
Solution: [How to fix]
Reference: [Link to docs/examples]

Example:
MAJOR | roles/cluster_setup/tasks/main.yml:45

This shell command should use kubernetes.core.k8s_info instead.

Problem: Using `oc get pods | grep Running` is fragile
Impact: Breaks if output format changes, can't access pod details
Solution: 
```yaml
- kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: "{{ namespace }}"
  register: pods
- set_fact:
    running_pods: "{{ pods.resources | selectattr('status.phase', 'equalto', 'Running') | list }}"
```
Reference: docs/ansible/KUBERNETES-PATTERNS.md#getting-resources
```

**Bad Feedback (Don't Do This):**

```markdown
❌ "This is wrong"
❌ "Bad code"
❌ "Doesn't follow standards"
❌ "You should know better"
```

### Review Comment Templates

**Shell Command Found:**

```markdown
MAJOR | [file]:[line]

Shell command should use Ansible module instead.

Problem: `shell: oc [command]` bypasses Ansible's idempotency
Impact: Fragile, breaks with output changes, hard to maintain
Solution: Use kubernetes.core.k8s_info or kubernetes.core.k8s
Reference: docs/ansible/KUBERNETES-PATTERNS.md

If module truly doesn't exist, please document why shell is necessary.
```

**Missing Error Handling:**

```markdown
MAJOR | [file]:[line]

Critical operation needs error handling.

Problem: No block/rescue/always for this operation
Impact: Failures leave system in unknown state, hard to debug
Solution: Add error handling with diagnostics and cleanup
Reference: docs/ansible/COMPREHENSIVE-GUIDE.md#error-handling-patterns

Example:
```yaml
block:
  - name: [operation]
rescue:
  - name: Collect diagnostics
  - name: Cleanup partial state
always:
  - name: Remove temp files
```
```

**Missing FQCN:**

```markdown
BLOCKER | [file]:[line]

Module must use FQCN (Fully Qualified Collection Name).

Problem: `file:` should be `ansible.builtin.file:`
Impact: Required by ansible-lint production profile
Solution: Add collection namespace to module name
Reference: ANSIBLE-DEVELOPMENT-STANDARDS.md#fqcn-usage

Quick fix: ansible.builtin.[module_name]
```

**Not Idempotent:**

```markdown
MAJOR | [file]:[line]

Operation is not idempotent.

Problem: Running multiple times creates duplicates/errors
Impact: Can't safely re-run playbook, breaks CI/CD
Solution: Use state-based approach instead of append-based
Reference: docs/ansible/COMPREHENSIVE-GUIDE.md#idempotency

Example: Use `lineinfile` instead of `shell: echo >> file`
```

**Security Issue:**

```markdown
🔒 BLOCKER | [file]:[line]

Security issue: Hardcoded credential found.

Problem: Password/token in plaintext
Impact: Security vulnerability, fails compliance
Solution: Use Ansible Vault for sensitive data
Reference: ANSIBLE-DEVELOPMENT-STANDARDS.md#security

Required action:
1. Move credential to vault file
2. Add `no_log: true` to task
3. Verify credential not in git history
```

### Asking Clarifying Questions

**When to ask questions:**

```markdown
Question patterns:

Design Decisions:
"Can you explain the reasoning behind [decision]?"
"Have you considered [alternative approach]?"
"What's the expected behavior when [edge case]?"

Missing Context:
"What testing was performed for this change?"
"Is this change backwards compatible?"
"Are there any known limitations?"

Unclear Code:
"What does this variable represent?"
"Why is this timeout set to [value]?"
"Can you add a comment explaining this logic?"
```

### Suggesting Improvements

**How to suggest without demanding:**

```markdown
SUGGESTION | [file]:[line]

Consider using [alternative approach].

Current approach works but [potential issue]
Suggested alternative: [approach]
Benefits: [why it's better]

This is optional - current code is acceptable.
```

**Example suggestions:**

```markdown
SUGGESTION | Could extract this repeated logic into a separate task file for reusability.

SUGGESTION | Consider adding retry logic here for transient failures.

SUGGESTION | Variable name could be more descriptive (e.g., cluster_setup_timeout vs timeout).

SUGGESTION | This filter chain could be simplified using [alternative filter].
```

---

## Common Review Comments

### Copy-Paste Reference

**Use these for common issues:**

**1. Missing FQCN**

```text
BLOCKER: Module needs FQCN. Change `[module]:` to `ansible.builtin.[module]:` or `kubernetes.core.[module]:`
```

**2. Shell command instead of module**

```text
MAJOR: Use kubernetes.core.k8s_info instead of shell: oc get. See docs/ansible/KUBERNETES-PATTERNS.md
```

**3. Missing changed_when/failed_when**

```text
MAJOR: Shell/command task needs `changed_when: false` and `failed_when: [condition]`
```

**4. Missing error handling**

```text
MAJOR: Critical operation needs block/rescue/always. See docs/ansible/COMPREHENSIVE-GUIDE.md#error-handling
```

**5. Not idempotent**

```text
MAJOR: This operation isn't idempotent - running twice will cause issues. Use state-based approach.
```

**6. Poor task name**

```text
MINOR: Task name should be more descriptive. Use action verb + what + why pattern.
```

**7. Hard-coded value**

```text
MINOR: Extract hard-coded value to variable for reusability.
```

**8. Missing documentation**

```text
MINOR: Please document this in README.md and add inline comment explaining complex logic.
```

**9. Security issue**

```text
🔒 BLOCKER: Security issue - use Ansible Vault for credentials and add no_log: true
```

**10. Missing tests**

```text
MAJOR: Please add tests for this new functionality. See tests/integration/ for examples.
```

---

## Approval Criteria

### When to Approve

**✅ Approve when ALL of these are true:**

- [ ] All automated checks pass
- [ ] No BLOCKER issues remain
- [ ] No MAJOR issues remain (or author has plan to fix)
- [ ] Code follows standards document
- [ ] Error handling appropriate for risk level
- [ ] Testing adequate for change scope
- [ ] Documentation updated
- [ ] Security considerations addressed

### When to Request Changes

**🔄 Request changes when ANY of these are true:**

- [ ] BLOCKER issues present
- [ ] Multiple MAJOR issues
- [ ] Security vulnerabilities
- [ ] Breaking changes without migration plan
- [ ] Insufficient testing for risk level
- [ ] Code doesn't match described changes

### When to Comment Only

**💬 Comment without blocking when:**

- [ ] Only MINOR or SUGGESTION items
- [ ] Questions about approach (not issues)
- [ ] Learning opportunities to share
- [ ] Alternative approaches to consider

### Approval Response Template

```markdown
## Code Review Complete ✅

### Summary
[Brief summary of changes]

### Review Result
- ✅ All automated checks passed
- ✅ Code follows standards
- ✅ Appropriate error handling
- ✅ Testing adequate
- ✅ Documentation updated

### Comments
[Any MINOR or SUGGESTION items]

### Approval
Approved - ready to merge after [any final items addressed]

Great work on [something specific done well]!
```

### Request Changes Template

```markdown
## Code Review - Changes Requested 🔄

### Summary
[Brief summary of review]

### Blocking Issues
#### BLOCKER
- [ ] [Issue 1]
- [ ] [Issue 2]

#### MAJOR
- [ ] [Issue 3]
- [ ] [Issue 4]

### Required Actions
Please address all BLOCKER items and have a plan for MAJOR items before next review.

### Positive Notes
[Something done well - always include!]

Let me know if you have questions about any feedback!
```

---

## Review Process Flow

### Step-by-Step Process

```mermaid
graph TD
    A[PR Created] --> B{Automated Checks Pass?}
    B -->|No| C[Author Fixes Issues]
    C --> A
    B -->|Yes| D[Reviewer Assigned]
    D --> E[Reviewer Examines Code]
    E --> F{Issues Found?}
    F -->|BLOCKER/MAJOR| G[Request Changes]
    G --> H[Author Addresses Feedback]
    H --> E
    F -->|MINOR/SUGGESTION| I[Comment Only]
    F -->|None| J[Approve PR]
    I --> J
    J --> K[Merge to Main]
```

### Timeline Expectations

**For Authors:**

- Create PR: When ready for review
- Respond to feedback: Within 1 business day
- Address blockers: Before requesting re-review
- Update based on comments: Within 2 business days

**For Reviewers:**

- Initial review: Within 1 business day
- Re-review after changes: Within 1 business day
- Quick questions: Within 4 hours
- Final approval: Same day after all issues addressed

### Review SLA

```markdown
| Change Size | Review Time | Re-review Time |
|-------------|-------------|----------------|
| Tiny (<50 lines) | 30 minutes | 15 minutes |
| Small (50-200 lines) | 1-2 hours | 30 minutes |
| Medium (200-500 lines) | 2-4 hours | 1 hour |
| Large (>500 lines) | Break into smaller PRs |

Note: Times are guidelines, complex changes may need more time
```

---

## Tips for Effective Reviews

### For Reviewers

**Do:**
- ✅ Review within SLA timeframe
- ✅ Provide constructive, specific feedback
- ✅ Praise good work
- ✅ Ask questions when unclear
- ✅ Test complex changes locally
- ✅ Use severity levels consistently
- ✅ Link to documentation/examples

**Don't:**
- ❌ Nitpick style covered by linting
- ❌ Block on personal preferences
- ❌ Rush through review
- ❌ Assume malicious intent
- ❌ Rewrite PR in comments
- ❌ Be condescending or dismissive

### For Authors

**Do:**
- ✅ Run pre-submit checks first
- ✅ Fill out PR template completely
- ✅ Self-review before requesting review
- ✅ Respond to all comments
- ✅ Ask for clarification when needed
- ✅ Thank reviewers for feedback
- ✅ Learn from feedback

**Don't:**
- ❌ Get defensive about feedback
- ❌ Ignore automated check failures
- ❌ Submit without testing
- ❌ Mark conversations resolved prematurely
- ❌ Argue about security issues
- ❌ Rush fixes without testing

---

## Appendix: Quick Reference

### Severity Quick Reference

| Severity | When to Use | Examples |
|----------|-------------|----------|
| BLOCKER | Must fix before merge | Security issues, syntax errors, breaking changes |
| MAJOR | Should fix before merge | Logic errors, missing error handling, poor naming |
| MINOR | Can fix after merge | Formatting, typos, optimizations |
| SUGGESTION | Optional | Alternative approaches, performance tips |

### Common Commands Quick Reference

```bash
# Pre-submission
./scripts/pre_submit_check.sh

# Syntax check
ansible-playbook --syntax-check playbook.yml

# Lint
ansible-lint --profile=production roles/ playbooks/

# YAML lint
yamllint -c .yamllint .

# Python quality
black roles/*/library/
isort roles/*/library/
flake8 roles/*/library/

# Check mode test
ansible-playbook -i inventory/test playbook.yml --check

# Tag test
ansible-playbook playbook.yml --tags preflight,validation
```

---

**Document Version:** 1.0.0  
**Last Updated:** 2025-02-10  
**Maintained By:** Platform Engineering Team

**Feedback:** This checklist should evolve with team needs. Submit PRs with improvements!

