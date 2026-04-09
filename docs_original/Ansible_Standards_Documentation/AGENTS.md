# AI Agent Development Standards

**Document Version:** 1.0.0  
**Last Updated:** 2025-02-10  
**Target Audience:** AI agents (Claude, GPT, etc.) assisting with code development  
**Purpose:** Standards for AI agents to produce consistent, high-quality code

---

## Overview

This document defines standards that AI agents should follow when generating or modifying code in this repository. These standards are designed to be machine-readable and actionable by AI assistants.

### Document Scope

**Applies to:** All AI agents assisting with code development
**Code types:** Ansible playbooks, roles, Python modules, shell scripts, documentation
**Enforcement:** AI agents should validate their output against these standards

---

## General Principles

### Principle 1: Follow Existing Patterns

**Rule:** Always examine existing code before generating new code.

```yaml
# Before generating code:
1. Read relevant existing files
2. Identify patterns used
3. Match coding style
4. Use same conventions
```

**Example workflow:**

```text
User asks: "Create a new role for database backup"

Agent should:
1. Read existing role structure (e.g., roles/pxbackup/)
2. Examine tasks/main.yml orchestrator pattern
3. Review variable naming (role_name_variable_name)
4. Match documentation style
5. Generate new role following observed patterns
```

### Principle 2: Never Assume - Always Verify

**Rule:** Don't rely on memory or training data - verify current state.

```yaml
# Before making changes:
- Use tools to read files
- Check current directory structure
- Verify file existence
- Read configuration files
```

**Example:**

```text
Wrong: "I'll update the deployment.yml file..."
Right: "Let me first check if deployment.yml exists and read its current content..."
```

### Principle 3: Explain Changes

**Rule:** Always explain what you're doing and why.

```yaml
# When making changes:
1. Explain the problem being solved
2. Describe the approach
3. Show what will change
4. Highlight any trade-offs
```

### Principle 4: Test Before Delivering

**Rule:** Validate generated code before presenting it.

```yaml
# Validation checklist:
- Syntax is correct
- Follows project standards
- Includes error handling
- Has proper documentation
- Uses correct file paths
```

---

## Ansible-Specific Standards

### Standard 1: FQCN Usage

**Rule:** All Ansible modules MUST use Fully Qualified Collection Names.

```yaml
# Correct
- name: Create directory
  ansible.builtin.file:
    path: /tmp/work
    state: directory

# Incorrect - NEVER generate this
- name: Create directory
  file:  # Missing FQCN
    path: /tmp/work
    state: directory
```

**Validation:**

```python
def validate_fqcn(task):
    """Check if task uses FQCN."""
    if 'ansible.' not in task or 'kubernetes.' not in task:
        return False
    return True
```

### Standard 2: Task Naming

**Rule:** Task names MUST be descriptive and use action verbs.

```yaml
# Correct
- name: Ensure application configuration directory exists
- name: Verify cluster connectivity before operations
- name: Wait for deployment to reach ready state

# Incorrect - NEVER generate these
- name: Create dir
- name: Check
- name: Do stuff
```

**Pattern:** `<Action verb> <what> <context/why>`

### Standard 3: Shell Command Prohibition

**Rule:** AVOID shell/command modules for Kubernetes operations.

```yaml
# Wrong - NEVER generate this
- name: Get pods
  shell: oc get pods -n {{ namespace }}
  register: pods

# Correct - ALWAYS prefer this
- name: Get pod information
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: "{{ namespace }}"
  register: pods
```

**When shell IS acceptable:**

```yaml
# Only when no module exists AND you explain why
- name: Execute pxctl command (no module available)
  ansible.builtin.shell: |
    pxctl status
  changed_when: false
  failed_when: result.rc != 0
  # Comment explaining why shell is necessary
```

### Standard 4: Error Handling

**Rule:** Critical operations MUST have block/rescue/always.

```yaml
# Correct - ALWAYS include error handling
- name: Critical operation
  block:
    - name: Execute operation
      kubernetes.core.k8s:
        definition: "{{ resource }}"
  
  rescue:
    - name: Handle failure
      debug:
        msg: "Operation failed: {{ ansible_failed_result.msg }}"
    
    - name: Cleanup
      # Cleanup code
  
  always:
    - name: Remove temporary files
      file:
        path: /tmp/work
        state: absent
```

### Standard 5: Variable Naming

**Rule:** Variables MUST follow role-prefixed naming.

```yaml
# Correct
vars:
  my_role_namespace: "production"
  my_role_timeout: 300
  my_role_enable_debug: false

# Incorrect - NEVER use these patterns
vars:
  ns: "production"  # Too short
  timeout: 300      # No prefix
  debug: false      # Ambiguous
```

---

## Python Standards

### Standard 1: Type Hints

**Rule:** All Python functions MUST have type hints.

```python
# Correct
def process_pods(pods: List[Dict[str, Any]], namespace: str) -> List[str]:
    """Process pods and return names."""
    return [pod['metadata']['name'] for pod in pods]

# Incorrect - NEVER generate without types
def process_pods(pods, namespace):
    return [pod['metadata']['name'] for pod in pods]
```

### Standard 2: Docstrings

**Rule:** All functions/classes MUST have docstrings.

```python
# Correct
def validate_cluster(cluster_name: str, timeout: int = 300) -> bool:
    """
    Validate cluster connectivity and health.
    
    Args:
        cluster_name: Name of the cluster to validate
        timeout: Connection timeout in seconds (default: 300)
    
    Returns:
        True if cluster is healthy, False otherwise
    
    Raises:
        ConnectionError: If cluster is unreachable
    """
    pass
```

### Standard 3: Error Handling

**Rule:** Catch specific exceptions, not bare except.

```python
# Correct
try:
    result = kubernetes_api.get_pod(name, namespace)
except kubernetes.client.ApiException as e:
    if e.status == 404:
        logger.warning(f"Pod {name} not found")
        return None
    raise

# Incorrect - NEVER use bare except
try:
    result = kubernetes_api.get_pod(name, namespace)
except:
    pass
```

---

## File Organization Standards

### Standard 1: Role Structure

**Rule:** New roles MUST follow this structure:

```text
<role_name>/
├── README.md                 # REQUIRED
├── CHANGELOG.md              # REQUIRED
├── defaults/
│   └── main.yml             # REQUIRED
├── tasks/
│   ├── main.yml             # REQUIRED (orchestrator only)
│   ├── preflight.yml
│   ├── validate.yml
│   ├── execute.yml
│   └── verify.yml
├── meta/
│   └── main.yml             # REQUIRED
└── templates/               # Optional
```

### Standard 2: Task File Organization

**Rule:** tasks/main.yml MUST be orchestrator only.

```yaml
# Correct - tasks/main.yml as orchestrator
---
- name: "Phase 1: Preflight Checks"
  ansible.builtin.import_tasks: preflight.yml
  tags: [always, preflight, my_role]

- name: "Phase 2: Validation"
  ansible.builtin.import_tasks: validate.yml
  tags: [always, validation, my_role]

# Incorrect - NEVER put logic in main.yml
---
- name: Check something
  shell: some command
  
- name: Do something
  file: ...
  
# (100 more lines of tasks)
```

---

## Documentation Standards

### Standard 1: README Structure

**Rule:** Every role/playbook MUST have a README with these sections:

```markdown
# Title

## Description
Brief description of purpose

## Requirements
- Ansible version
- Collections needed
- Prerequisites

## Role Variables
### Required Variables
| Variable | Type | Description |
| ... | ... | ... |

### Optional Variables
| Variable | Type | Default | Description |
| ... | ... | ... | ... |

## Example Playbook
\`\`\`yaml
Example usage
\`\`\`

## License
```

### Standard 2: Inline Comments

**Rule:** Complex logic MUST have explanatory comments.

```yaml
# Correct - explain WHY
- name: Wait for pods with dual timeout
  # Using both global and inactivity timeouts because:
  # 1. Operator-controlled upgrades can be slow (global timeout)
  # 2. Stuck upgrades show no progress (inactivity timeout)
  block:
    # ... implementation

# Incorrect - obvious comments
- name: Create file
  # This creates a file
  file: ...
```

### Standard 3: Code Block Languages

**Rule:** All markdown code blocks MUST specify language.

```markdown
Correct:
\`\`\`yaml
- name: Example
\`\`\`

\`\`\`python
def example():
    pass
\`\`\`

Incorrect - NEVER omit language:
\`\`\`
- name: Example
\`\`\`
```

---

## AI Agent Workflow

### When Generating New Code

**Step-by-step process:**

```text
1. READ EXISTING CODE
   - Examine similar files
   - Identify patterns
   - Note conventions

2. PLAN THE IMPLEMENTATION
   - Explain approach
   - Identify files to modify
   - Anticipate issues

3. GENERATE CODE
   - Follow observed patterns
   - Include error handling
   - Add documentation

4. VALIDATE OUTPUT
   - Check syntax
   - Verify standards compliance
   - Test logic

5. EXPLAIN CHANGES
   - What was done
   - Why this approach
   - What to test
```

### When Modifying Existing Code

**Step-by-step process:**

```text
1. READ CURRENT CODE
   - Understand existing logic
   - Identify change scope
   - Note dependencies

2. PLAN MODIFICATIONS
   - Explain what will change
   - Show before/after
   - Highlight impacts

3. MAKE CHANGES
   - Preserve existing patterns
   - Maintain consistency
   - Update related code

4. VALIDATE CHANGES
   - Still follows standards
   - Doesn't break existing functionality
   - Documentation updated

5. PROVIDE CONTEXT
   - What changed and why
   - Testing recommendations
   - Migration notes if needed
```

### When User Asks Questions

**Response pattern:**

```text
1. UNDERSTAND CONTEXT
   - Read relevant files if needed
   - Clarify ambiguities
   - Ask questions if unclear

2. PROVIDE ANSWER
   - Direct answer first
   - Explanation second
   - Examples if helpful

3. OFFER NEXT STEPS
   - Related information
   - What to do next
   - Potential issues to watch
```

---

## Quality Validation Rules

### Automated Checks

**Before presenting code, validate:**

```yaml
ansible_checks:
  - fqcn_used: true
  - has_task_names: true
  - shell_commands_justified: true
  - error_handling_present: true
  - variables_prefixed: true

python_checks:
  - has_type_hints: true
  - has_docstrings: true
  - specific_exceptions: true
  - follows_pep8: true

documentation_checks:
  - readme_present: true
  - code_blocks_have_language: true
  - examples_provided: true
```

### Manual Review Points

**Things AI cannot fully validate:**

```text
1. Logic correctness
   - Is the approach sound?
   - Are there edge cases?
   - Will this work in production?

2. Security implications
   - Are credentials handled safely?
   - Is input validated?
   - Are permissions correct?

3. Performance impact
   - Will this scale?
   - Are there bottlenecks?
   - Is it efficient?

4. User intent match
   - Does this solve the actual problem?
   - Is this what user wanted?
   - Are there better approaches?
```

---

## Common Mistakes to Avoid

### Mistake 1: Assuming File Locations

```text
Wrong: "I'll update the file at roles/myapp/tasks/main.yml"
Right: "Let me first check if that file exists..."
[Use tool to verify file exists]
[Read file content]
"I can see the file exists. Here's what I'll change..."
```

### Mistake 2: Not Reading Existing Patterns

```text
Wrong: Generate code based on general knowledge
Right: 
1. Read existing similar code
2. Identify patterns used in project
3. Generate code matching those patterns
```

### Mistake 3: Ignoring Project Context

```text
Wrong: Use generic best practices
Right:
1. Check project's CLAUDE.md or similar
2. Read project standards documents
3. Follow project-specific conventions
```

### Mistake 4: Not Explaining Trade-offs

```text
Wrong: "Here's the code" [no explanation]
Right: 
"I'm using approach X because:
- Benefit 1
- Benefit 2
Alternative approach Y was considered but:
- Trade-off 1
- Trade-off 2"
```

### Mistake 5: Overconfidence

```text
Wrong: "This will definitely work"
Right: "This should work, but please:
1. Test in development first
2. Watch for [potential issue]
3. Verify [specific aspect]"
```

---

## Special Considerations

### Kubernetes/OpenShift Automation

**Rules for K8s automation:**

```yaml
rules:
  # 1. NEVER use oc/kubectl in shell
  - avoid: "shell: oc get pods"
    use: "kubernetes.core.k8s_info: kind: Pod"
  
  # 2. NEVER parse text output
  - avoid: "shell: oc get pods | grep Running"
    use: "k8s_info + selectattr filter"
  
  # 3. ALWAYS use structured data
  - use: "pod.resources[0].status.phase"
    not: "shell output parsing"
  
  # 4. Monitor operator-controlled resources
  - pattern: "Monitor, don't control"
    explanation: "Operator manages pods, we observe"
```

### Multi-Cluster Operations

**Rules for multi-cluster:**

```yaml
rules:
  # 1. Process sequentially by default
  - pattern: "serial: 1"
    why: "Safety - verify each cluster before next"
  
  # 2. Use inventory groups
  - pattern: "hosts: k8s_clusters"
    not: "hardcoded cluster list"
  
  # 3. Verify connectivity first
  - always: "kubernetes.core.k8s_cluster_info"
    before: "any cluster operations"
```

### Custom Module Development

**Rules for custom modules:**

```python
rules = {
    # 1. MUST have complete docstrings
    "documentation": "DOCUMENTATION, EXAMPLES, RETURN",
    
    # 2. MUST have type hints
    "type_hints": "all functions and methods",
    
    # 3. MUST support check mode
    "check_mode": "if module.check_mode: module.exit_json(changed=False)",
    
    # 4. MUST use AnsibleModule
    "module_utils": "from ansible.module_utils.basic import AnsibleModule",
}
```

---

## Output Format Standards

### When Presenting Code

**Format:**

```text
1. EXPLANATION
   Brief description of what code does

2. CODE BLOCK
   ```language
   actual code
   ```

1. KEY POINTS
   - Important aspect 1
   - Important aspect 2
   - Testing note

2. NEXT STEPS
   What to do with this code

```text

### When Explaining Concepts

**Format:**

```text
1. DIRECT ANSWER
   Answer the question directly in 1-2 sentences

2. EXPLANATION
   Provide detailed explanation

3. EXAMPLE
   Show practical example

4. RELATED INFO
   Link to related concepts or documents
```

### When Debugging Issues

**Format:**

```text
1. PROBLEM IDENTIFICATION
   What's wrong

2. ROOT CAUSE
   Why it's happening

3. SOLUTION
   How to fix

4. PREVENTION
   How to avoid in future
```

---

## Integration with Development Tools

### Pre-commit Hook Integration

**AI should remind users:**

```text
"Before committing these changes:
1. Run: ./scripts/pre_submit_check.sh
2. Fix any issues found
3. Verify all tests pass"
```

### CI/CD Awareness

**AI should consider:**

```text
"This change will:
1. Trigger ansible-lint in CI
2. Run syntax validation
3. Execute integration tests

Make sure to:
- Test locally first
- Check CI results after push"
```

### Documentation Updates

**AI should remind:**

```text
"Remember to update:
1. README.md (if user-facing change)
2. CHANGELOG.md (always)
3. Inline comments (if complex logic)"
```

---

## Continuous Improvement

### Learning from Feedback

**When user corrects AI:**

```text
1. Acknowledge the correction
2. Understand why it was wrong
3. Apply learning to future responses
4. Don't repeat the same mistake
```

### Adapting to Project Evolution

**AI should:**

```text
1. Notice when patterns change
2. Adopt new conventions
3. Ask about ambiguities
4. Suggest improvements appropriately
```

---

## Summary Checklist

**Before presenting any code, verify:**

- [ ] Read existing code for patterns
- [ ] Used FQCN for all Ansible modules
- [ ] Task names are descriptive
- [ ] Avoided shell/command for K8s
- [ ] Included error handling
- [ ] Variables are properly named
- [ ] Added documentation
- [ ] Explained the approach
- [ ] Noted testing recommendations
- [ ] Highlighted potential issues

**For Python code, verify:**

- [ ] Type hints on all functions
- [ ] Docstrings present
- [ ] Specific exception handling
- [ ] Follows PEP 8
- [ ] No bare except clauses

**For documentation, verify:**

- [ ] Code blocks have language specified
- [ ] Examples are complete
- [ ] Structure follows standards
- [ ] No emojis (professional tone)

---

## Version History

- v1.0.0 (2025-02-10): Initial version

---

**Document Maintenance:**

This document should be updated as:

- New patterns emerge
- Standards evolve
- Common mistakes identified
- Tools and processes change

**AI Agent Note:**

This document is your contract with developers. Follow these standards rigorously to maintain trust and produce high-quality output.
