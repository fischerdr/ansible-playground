# Ansible Migration Guide: From Shell Scripts to Enterprise Automation

**Document Version:** 1.0.0  
**Last Updated:** 2025-02-10  
**Target Audience:** Teams transitioning from shell-script-style Ansible to enterprise patterns  
**Purpose:** Step-by-step guide for refactoring existing automation code

---

## Table of Contents

1. [Introduction](#introduction)
2. [Assessment Phase](#assessment-phase)
3. [Progressive Adoption Timeline](#progressive-adoption-timeline)
4. [Common Anti-Patterns and Fixes](#common-anti-patterns-and-fixes)
5. [Refactoring Strategies](#refactoring-strategies)
6. [Migration Checklists](#migration-checklists)
7. [Team Training Plan](#team-training-plan)
8. [Measuring Success](#measuring-success)

---

## Introduction

### Purpose of This Guide

This guide helps teams migrate from shell-script-style Ansible automation to enterprise-grade patterns. If your playbooks look like this:

```yaml
- shell: oc get pods | grep Running
- shell: oc patch deployment...
- shell: sleep 30
```

This guide will help you transform them to this:

```yaml
- kubernetes.core.k8s_info:
    kind: Pod
    label_selectors: [app=myapp]
  register: pods
```

### Who Should Use This Guide

**This guide is for teams who:**
- Write Ansible playbooks that mostly use `shell` and `command` modules
- Treat Ansible as a remote command executor rather than declarative automation
- Have playbooks that fail unpredictably or aren't idempotent
- Use text parsing (grep, awk, sed) extensively in playbooks
- Want to adopt enterprise Ansible standards

**This guide assumes:**
- Basic Ansible knowledge (playbooks, roles, tasks)
- Access to a test environment
- Ability to refactor code incrementally
- Management support for quality improvements

### Migration Philosophy

**Key Principles:**

1. **Progressive, not big-bang** - Migrate incrementally, one pattern at a time
2. **Test continuously** - Every change must pass tests before moving forward
3. **Learn by doing** - Refactor actual code, don't just read documentation
4. **Measure progress** - Track improvements in quality metrics
5. **Build habits** - Focus on changing mindset, not just code

**What This Is NOT:**

- ❌ Rewrite everything from scratch
- ❌ Stop all development for migration
- ❌ Achieve perfection immediately
- ❌ Follow standards blindly without understanding

**What This IS:**

- ✅ Gradually improve code quality
- ✅ Build better habits over time
- ✅ Reduce technical debt systematically
- ✅ Apply standards with understanding

---

## Assessment Phase

### Step 1: Inventory Your Current State

Before migrating, understand what you have. Run this assessment:

```bash
#!/bin/bash
# assess_current_state.sh

echo "=== Ansible Code Assessment ==="
echo ""

# Count total playbooks and roles
PLAYBOOKS=$(find . -name "*.yml" -path "*/playbooks/*" | wc -l)
ROLES=$(find . -type d -path "*/roles/*" -maxdepth 2 | grep -v "/tasks\|/handlers" | wc -l)

echo "Total Playbooks: $PLAYBOOKS"
echo "Total Roles: $ROLES"
echo ""

# Count shell/command usage
SHELL_USAGE=$(grep -r "shell:" playbooks/ roles/ 2>/dev/null | wc -l)
COMMAND_USAGE=$(grep -r "command:" playbooks/ roles/ 2>/dev/null | wc -l)
TOTAL_SHELL=$((SHELL_USAGE + COMMAND_USAGE))

echo "Shell module usage: $SHELL_USAGE"
echo "Command module usage: $COMMAND_USAGE"
echo "Total shell-style tasks: $TOTAL_SHELL"
echo ""

# Check for common anti-patterns
echo "=== Anti-Pattern Detection ==="

# Using oc/kubectl in shell
OC_COMMANDS=$(grep -r "shell:.*oc " playbooks/ roles/ 2>/dev/null | wc -l)
KUBECTL_COMMANDS=$(grep -r "shell:.*kubectl " playbooks/ roles/ 2>/dev/null | wc -l)
echo "oc commands in shell: $OC_COMMANDS"
echo "kubectl commands in shell: $KUBECTL_COMMANDS"

# Text parsing
GREP_USAGE=$(grep -r "grep" playbooks/ roles/ 2>/dev/null | wc -l)
AWK_USAGE=$(grep -r "awk" playbooks/ roles/ 2>/dev/null | wc -l)
SED_USAGE=$(grep -r "sed" playbooks/ roles/ 2>/dev/null | wc -l)
echo "grep usage: $GREP_USAGE"
echo "awk usage: $AWK_USAGE"
echo "sed usage: $SED_USAGE"

# Missing FQCN
NON_FQCN=$(grep -r "^\s*[a-z_]*:" playbooks/ roles/ 2>/dev/null | grep -v "ansible\." | grep -v "kubernetes\." | wc -l)
echo "Tasks without FQCN: $NON_FQCN"

# Missing changed_when/failed_when
SHELL_NO_CHANGED=$(grep -A5 "shell:\|command:" playbooks/ roles/ 2>/dev/null | grep -c "changed_when\|failed_when" || echo 0)
SHELL_WITH_CHANGED=$(grep -c "shell:\|command:" playbooks/ roles/ 2>/dev/null || echo 0)
echo "Shell tasks with proper guards: $SHELL_NO_CHANGED/$SHELL_WITH_CHANGED"

echo ""
echo "=== Migration Priority Score ==="
TOTAL_ISSUES=$((OC_COMMANDS + KUBECTL_COMMANDS + GREP_USAGE + AWK_USAGE + NON_FQCN))
echo "Total issues found: $TOTAL_ISSUES"

if [ $TOTAL_ISSUES -gt 100 ]; then
    echo "Priority: HIGH - Significant refactoring needed"
elif [ $TOTAL_ISSUES -gt 50 ]; then
    echo "Priority: MEDIUM - Moderate refactoring needed"
else
    echo "Priority: LOW - Minor improvements needed"
fi
```

Run this assessment and save the output:

```bash
./assess_current_state.sh > assessment_$(date +%Y%m%d).txt
```

### Step 2: Identify High-Value Targets

**Prioritize migration based on:**

1. **Frequency of use** - Playbooks run most often
2. **Criticality** - Production automation vs dev tools
3. **Maintainability pain** - Code that breaks frequently
4. **Team impact** - Code touched by multiple people

**Create a priority list:**

```markdown
# Migration Priority List

## High Priority (Migrate First)
1. Production cluster upgrade playbook (runs weekly, critical)
   - Issues: 50+ shell commands, no error handling
   - Impact: High - affects all clusters
   
2. Storage provisioning role (used by 5 teams)
   - Issues: Text parsing, not idempotent
   - Impact: High - blocks other work

## Medium Priority (Migrate Second)
3. Monitoring setup playbook (runs monthly)
   - Issues: Manual waits, no verification
   - Impact: Medium - important but infrequent

## Low Priority (Migrate Last)
4. One-off migration scripts
   - Issues: Quick and dirty, many hacks
   - Impact: Low - rarely used
```

### Step 3: Establish Baseline Metrics

**Track these metrics before and after migration:**

```yaml
# metrics_baseline.yml
assessment_date: 2025-02-10
team_size: 5

code_metrics:
  total_playbooks: 45
  total_roles: 12
  lines_of_yaml: 8500
  
anti_patterns:
  shell_command_usage: 234
  oc_kubectl_commands: 156
  text_parsing_usage: 89
  missing_fqcn: 567
  missing_guards: 198
  
quality_metrics:
  ansible_lint_errors: 45
  ansible_lint_warnings: 123
  syntax_errors: 0
  
operational_metrics:
  average_playbook_runtime: 25 minutes
  failure_rate: 12%
  false_positive_failures: 8%
  time_to_debug_failure: 45 minutes
  
team_metrics:
  onboarding_time_days: 14
  code_review_time_hours: 4
  confidence_level: 3/10
```

Save this as your baseline. You'll measure improvements against it.

---

## Progressive Adoption Timeline

### Overview: 8-Week Migration Plan

This timeline assumes:
- Team of 3-5 engineers
- 2-4 hours per week dedicated to migration
- Continued feature development (this is incremental)

**Week-by-week breakdown:**

```
Week 1-2: Foundation & Quick Wins
Week 3-4: Kubernetes Module Adoption
Week 5-6: Error Handling & Idempotency
Week 7-8: Advanced Patterns & Testing
```

### Week 1-2: Foundation & Quick Wins

**Goals:**
1. Stop writing new anti-patterns
2. Fix obvious issues in new code
3. Set up quality tools

**Tasks:**

**Day 1-2: Tool Setup**

```bash
# Set up pre-commit hooks
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/ansible/ansible-lint
    rev: v24.2.0
    hooks:
      - id: ansible-lint
        args: ["--profile=production"]
EOF

pip install pre-commit
pre-commit install

# Initial lint (will show many errors - that's expected)
ansible-lint playbooks/ roles/ || true
```

**Day 3-5: Quick Win #1 - Add FQCN**

Pick one small playbook and add FQCN to all modules:

```yaml
# Before
- name: Create directory
  file:
    path: /tmp/work
    state: directory

# After
- name: Create directory
  ansible.builtin.file:
    path: /tmp/work
    state: directory
```

**Tool to help:**

```bash
# find_non_fqcn.sh
#!/bin/bash
# Find tasks without FQCN

grep -rn "^\s*[a-z_]*:" playbooks/ roles/ | \
  grep -v "ansible\." | \
  grep -v "kubernetes\." | \
  grep -v "name:" | \
  grep -v "when:" | \
  grep -v "tags:" | \
  grep -v "vars:"
```

**Day 6-10: Quick Win #2 - Add changed_when/failed_when**

Find all shell/command tasks and add guards:

```yaml
# Before
- name: Get pods
  shell: oc get pods -n {{ namespace }}
  register: pods

# After
- name: Get pods
  ansible.builtin.shell: |
    oc get pods -n {{ namespace }}
  register: pods
  changed_when: false  # Read-only operation
  failed_when: pods.rc != 0
```

**Tool to help:**

```bash
# find_unguarded_shell.sh
#!/bin/bash
# Find shell/command without changed_when

for file in $(find playbooks/ roles/ -name "*.yml"); do
    # Extract shell/command tasks
    awk '/- name:/ {name=$0; getline; if (/shell:|command:/) {
        getline; getline; getline; getline;
        if (!/changed_when/ && !/failed_when/) print FILENAME ":" name
    }}' "$file"
done
```

**Week 1-2 Checklist:**

- [ ] Pre-commit hooks installed
- [ ] Team trained on FQCN requirement
- [ ] At least 1 playbook fully FQCN compliant
- [ ] At least 10 shell tasks have changed_when/failed_when
- [ ] Baseline metrics documented
- [ ] Team standup: share learnings

**Expected Results:**
- Ansible-lint errors reduced by ~20%
- Team understands why FQCN and guards matter
- Quality tools catching issues automatically

### Week 3-4: Kubernetes Module Adoption

**Goals:**
1. Replace oc/kubectl commands with k8s modules
2. Understand structured data vs text parsing
3. Refactor 2-3 critical playbooks

**Day 1-3: Training Session**

**Team Workshop (2 hours):**

```markdown
# Workshop: Kubernetes Modules

## Part 1: Understanding the Problem (30 min)
- Show example of brittle shell script
- Demo how it breaks with formatting changes
- Explain structured data benefits

## Part 2: Hands-on Exercise (60 min)
Task: Refactor this playbook together

Before (shell-based):
```yaml
- name: Get running pods
  shell: oc get pods -n {{ ns }} | grep Running | wc -l
  register: count
```

After (module-based):
```yaml
- name: Get pod information
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: "{{ ns }}"
  register: pods

- name: Count running pods
  set_fact:
    count: "{{ pods.resources | selectattr('status.phase', 'equalto', 'Running') | list | length }}"
```

## Part 3: Practice (30 min)
Each person refactors one shell command to k8s module
Share results with team
```

**Day 4-10: Refactoring Sprint**

**Pattern #1: Getting Resources**

Create a conversion guide:

```yaml
# CONVERSION GUIDE: Getting Resources

# Pattern 1: List all resources
# Before:
- shell: oc get pods -n {{ namespace }} --no-headers
  register: pods
# After:
- kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: "{{ namespace }}"
  register: pods

# Pattern 2: Get specific resource
# Before:
- shell: oc get deployment myapp -n {{ namespace }} -o json
  register: deploy
# After:
- kubernetes.core.k8s_info:
    api_version: apps/v1
    kind: Deployment
    name: myapp
    namespace: "{{ namespace }}"
  register: deploy

# Pattern 3: Get resources with labels
# Before:
- shell: oc get pods -n {{ namespace }} -l app=myapp --no-headers
  register: pods
# After:
- kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: "{{ namespace }}"
    label_selectors:
      - "app=myapp"
  register: pods

# Pattern 4: Count resources
# Before:
- shell: oc get pods -n {{ namespace }} | grep Running | wc -l
  register: count
# After:
- kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: "{{ namespace }}"
  register: pods
- set_fact:
    count: "{{ pods.resources | selectattr('status.phase', 'equalto', 'Running') | list | length }}"
```

**Pattern #2: Creating/Updating Resources**

```yaml
# CONVERSION GUIDE: Creating/Updating Resources

# Pattern 1: Create from YAML
# Before:
- shell: oc apply -f /tmp/deployment.yaml
# After:
- kubernetes.core.k8s:
    state: present
    src: /tmp/deployment.yaml

# Pattern 2: Create from template
# Before:
- shell: |
    cat <<EOF | oc apply -f -
    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: myconfig
    data:
      key: value
    EOF
# After:
- kubernetes.core.k8s:
    state: present
    definition:
      apiVersion: v1
      kind: ConfigMap
      metadata:
        name: myconfig
      data:
        key: value

# Pattern 3: Update (patch) resource
# Before:
- shell: |
    oc patch deployment myapp -n {{ namespace }} \
      --type merge -p '{"spec":{"replicas":3}}'
# After:
- kubernetes.core.k8s:
    api_version: apps/v1
    kind: Deployment
    name: myapp
    namespace: "{{ namespace }}"
    definition:
      spec:
        replicas: 3

# Pattern 4: Scale deployment
# Before:
- shell: oc scale deployment myapp -n {{ namespace }} --replicas=3
# After:
- kubernetes.core.k8s:
    api_version: apps/v1
    kind: Deployment
    name: myapp
    namespace: "{{ namespace }}"
    definition:
      spec:
        replicas: 3
```

**Day 11-14: Pair Programming Sessions**

**Schedule:**
- 2 hours per day
- Pairs rotate daily
- Each pair refactors one playbook
- Team reviews at end of day

**Pair Session Format:**

```markdown
## Pair Programming Session

**Duration:** 2 hours
**Pair:** Engineer A + Engineer B
**Target:** playbooks/cluster_setup.yml

### Hour 1: Assessment & Planning
- Read through playbook together
- Identify all shell/command tasks
- List which patterns apply
- Prioritize which to fix first

### Hour 2: Refactoring
- Refactor 1-2 patterns
- Test each change
- Commit incrementally
- Document any blockers

### Standup Report:
- What we refactored: _______
- What we learned: _______
- What we're blocked on: _______
- Next session focus: _______
```

**Week 3-4 Checklist:**

- [ ] Team workshop completed
- [ ] Conversion guide created
- [ ] 2-3 critical playbooks refactored
- [ ] All new code uses k8s modules
- [ ] At least 50% of oc/kubectl commands replaced
- [ ] Team comfortable with k8s_info and k8s modules

**Expected Results:**
- 50-70% reduction in oc/kubectl shell commands
- Team understands structured data benefits
- Playbooks more reliable and maintainable

### Week 5-6: Error Handling & Idempotency

**Goals:**
1. Add proper error handling to all critical paths
2. Ensure playbooks are idempotent
3. Add verification steps

**Day 1-3: Error Handling Patterns**

**Pattern #1: Basic block/rescue/always**

```yaml
# BEFORE: No error handling
- name: Update deployment
  kubernetes.core.k8s:
    definition: "{{ deployment_def }}"

- name: Wait
  pause:
    seconds: 30

- name: Check status
  shell: oc get deployment myapp

# AFTER: Proper error handling
- name: Update deployment with error handling
  block:
    - name: Update deployment
      kubernetes.core.k8s:
        definition: "{{ deployment_def }}"
        wait: true
        wait_timeout: 300
      register: update_result
    
    - name: Verify deployment succeeded
      kubernetes.core.k8s_info:
        api_version: apps/v1
        kind: Deployment
        name: myapp
        namespace: "{{ namespace }}"
      register: deployment
      until:
        - deployment.resources[0].status.readyReplicas is defined
        - deployment.resources[0].status.readyReplicas == deployment.resources[0].spec.replicas
      retries: 30
      delay: 10
  
  rescue:
    - name: Log failure details
      debug:
        msg: "Deployment failed: {{ ansible_failed_result.msg }}"
    
    - name: Get deployment events
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Event
        namespace: "{{ namespace }}"
      register: events
    
    - name: Display relevant events
      debug:
        msg: "{{ events.resources | selectattr('involvedObject.name', 'equalto', 'myapp') | list }}"
    
    - name: Fail with context
      fail:
        msg: "Deployment update failed. See debug output for details."
  
  always:
    - name: Cleanup temporary files
      file:
        path: /tmp/deployment_work
        state: absent
```

**Day 4-7: Idempotency Fixes**

**Common idempotency problems:**

```yaml
# PROBLEM 1: Always shows as changed
# BEFORE:
- name: Configure setting
  shell: |
    echo "setting=value" >> /etc/config

# AFTER:
- name: Ensure setting is configured
  lineinfile:
    path: /etc/config
    regexp: '^setting='
    line: 'setting=value'

# PROBLEM 2: Creates duplicates
# BEFORE:
- name: Add firewall rule
  shell: iptables -A INPUT -p tcp --dport 8080 -j ACCEPT

# AFTER:
- name: Ensure firewall rule exists
  iptables:
    chain: INPUT
    protocol: tcp
    destination_port: 8080
    jump: ACCEPT
    state: present

# PROBLEM 3: No change detection
# BEFORE:
- name: Update config
  shell: |
    cat > /etc/app.conf <<EOF
    port=8080
    host=0.0.0.0
    EOF

# AFTER:
- name: Ensure config is correct
  copy:
    dest: /etc/app.conf
    content: |
      port=8080
      host=0.0.0.0
  # Only shows changed if content actually differs
```

**Day 8-14: Add Verification**

**Pattern: Post-operation verification**

```yaml
# Add verification after every critical operation

- name: Critical operation with verification
  block:
    # 1. Pre-check
    - name: Verify prerequisites
      assert:
        that:
          - prerequisite_met
        fail_msg: "Prerequisites not met"
    
    # 2. Execute
    - name: Perform operation
      kubernetes.core.k8s:
        definition: "{{ resource_def }}"
      register: operation_result
    
    # 3. Verify
    - name: Verify operation completed correctly
      kubernetes.core.k8s_info:
        api_version: "{{ operation_result.result.apiVersion }}"
        kind: "{{ operation_result.result.kind }}"
        name: "{{ operation_result.result.metadata.name }}"
        namespace: "{{ operation_result.result.metadata.namespace }}"
      register: verification
      until:
        - verification.resources[0].status.phase == "Running"
      retries: 30
      delay: 10
    
    # 4. Validate result
    - name: Validate resource is healthy
      assert:
        that:
          - verification.resources[0].status.conditions | selectattr('type', 'equalto', 'Ready') | selectattr('status', 'equalto', 'True') | list | length > 0
        fail_msg: "Resource is not healthy"
        success_msg: "Operation completed and verified successfully"
```

**Week 5-6 Checklist:**

- [ ] All critical playbooks have block/rescue/always
- [ ] Idempotency issues identified and fixed
- [ ] Verification steps added after operations
- [ ] Team trained on error handling patterns
- [ ] No playbooks with bare shell commands in critical paths

**Expected Results:**
- Playbooks are truly idempotent (can run multiple times safely)
- Failures provide actionable error messages
- Operations are verified automatically

### Week 7-8: Advanced Patterns & Testing

**Goals:**
1. Implement monitoring-based automation
2. Add comprehensive testing
3. Document patterns for team

**Day 1-5: Monitoring Patterns**

```yaml
# Pattern: Monitor long-running operations

- name: Monitor operation with dual timeout
  vars:
    operation_start: "{{ ansible_date_time.epoch }}"
    last_activity: "{{ ansible_date_time.epoch }}"
    global_timeout: 2100  # 35 minutes
    inactivity_timeout: 2100
  
  block:
    - name: Check operation progress
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Pod
        namespace: "{{ namespace }}"
        label_selectors:
          - "operation={{ operation_id }}"
      register: operation_pods
    
    - name: Analyze progress
      set_fact:
        completed_pods: "{{ operation_pods.resources | selectattr('status.phase', 'equalto', 'Succeeded') | list }}"
        total_pods: "{{ operation_pods.resources | length }}"
    
    - name: Check for activity
      set_fact:
        has_activity: "{{ completed_pods | length != previous_completed | default(0) }}"
    
    - name: Update activity time
      set_fact:
        last_activity: "{{ ansible_date_time.epoch }}"
      when: has_activity
    
    - name: Check timeouts
      assert:
        that:
          - (ansible_date_time.epoch | int) - (operation_start | int) <= global_timeout
          - (ansible_date_time.epoch | int) - (last_activity | int) <= inactivity_timeout
        fail_msg: "Operation timeout exceeded"
    
    - name: Wait if not complete
      pause:
        seconds: 15
      when: completed_pods | length < total_pods
  
  until: completed_pods | length == total_pods
  retries: "{{ (global_timeout / 15) | int }}"
  delay: 15
```

**Day 6-10: Testing Implementation**

```bash
# Create test framework

mkdir -p tests/{unit,integration}

# tests/run_tests.sh
#!/bin/bash

echo "=== Running Test Suite ==="

# Phase 1: Syntax
echo "Phase 1: Syntax validation..."
for playbook in playbooks/*.yml; do
    ansible-playbook --syntax-check "$playbook" || exit 1
done

# Phase 2: Linting
echo "Phase 2: Linting..."
ansible-lint playbooks/ roles/ || exit 1

# Phase 3: Check mode
echo "Phase 3: Check mode testing..."
for playbook in playbooks/*.yml; do
    ansible-playbook -i inventory/test "$playbook" --check || exit 1
done

# Phase 4: Integration (if test environment available)
if [ -n "$TEST_CLUSTER" ]; then
    echo "Phase 4: Integration testing..."
    ansible-playbook -i inventory/test tests/integration/test_suite.yml || exit 1
fi

echo "✅ All tests passed"
```

**Day 11-14: Documentation & Knowledge Sharing**

```markdown
# Team Patterns Document

## Pattern Library

### Pattern 1: Get Resource with Retry
**Use when:** Resource might not exist immediately
**Example:**
```yaml
- name: Wait for resource to exist
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    name: "{{ pod_name }}"
    namespace: "{{ namespace }}"
  register: pod
  until: pod.resources | length > 0
  retries: 30
  delay: 10
```

### Pattern 2: Monitor Rolling Update
**Use when:** Operator controls upgrade, need to monitor
**Example:**
[Include complete example]

### Pattern 3: Multi-Cluster Operation
**Use when:** Same operation across multiple clusters
**Example:**
[Include complete example]
```

**Week 7-8 Checklist:**

- [ ] Monitoring patterns implemented in 2+ playbooks
- [ ] Test framework created and running
- [ ] Pattern library documented
- [ ] Team knowledge sharing session completed
- [ ] All playbooks have tests

**Expected Results:**
- Sophisticated monitoring for long operations
- Automated testing catches issues
- Team has patterns to copy for new development

---

## Common Anti-Patterns and Fixes

### Anti-Pattern #1: Text Parsing Hell

**Problem:**

```yaml
# Brittle, breaks with formatting changes
- name: Get pod names
  shell: oc get pods -n {{ namespace }} | awk '{print $1}' | tail -n +2
  register: pod_names

- name: Get pod IPs
  shell: oc get pods -n {{ namespace }} | awk '{print $6}' | tail -n +2
  register: pod_ips
```

**Why it's bad:**
- Breaks if column order changes
- Breaks if field widths change
- Can't access other pod information
- Error messages are cryptic

**Solution:**

```yaml
# Robust, uses structured data
- name: Get pod information
  kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
    namespace: "{{ namespace }}"
  register: pods

- name: Extract pod names
  set_fact:
    pod_names: "{{ pods.resources | map(attribute='metadata.name') | list }}"

- name: Extract pod IPs
  set_fact:
    pod_ips: "{{ pods.resources | map(attribute='status.podIP') | list }}"

- name: Create name-to-IP mapping
  set_fact:
    pod_map: "{{ dict(pod_names | zip(pod_ips)) }}"
```

**Migration Strategy:**

1. Find all grep/awk/sed usage
2. Identify what data is being extracted
3. Use k8s_info to get structured data
4. Use Jinja2 filters to extract fields
5. Test thoroughly

### Anti-Pattern #2: Sleep Instead of Wait

**Problem:**

```yaml
# Hope it's done after sleeping
- name: Update deployment
  shell: oc apply -f deployment.yaml

- name: Wait for deployment
  pause:
    seconds: 30

- name: Check if ready
  shell: oc get deployment myapp
```

**Why it's bad:**
- Wastes time if operation is quick
- Fails if operation takes longer
- No verification operation actually succeeded
- False sense of success

**Solution:**

```yaml
# Actually wait for completion
- name: Update deployment
  kubernetes.core.k8s:
    state: present
    src: deployment.yaml
    wait: true
    wait_timeout: 300
  register: deployment

- name: Verify deployment is ready
  kubernetes.core.k8s_info:
    api_version: apps/v1
    kind: Deployment
    name: myapp
    namespace: "{{ namespace }}"
  register: deploy_status
  until:
    - deploy_status.resources[0].status.availableReplicas is defined
    - deploy_status.resources[0].status.availableReplicas == deploy_status.resources[0].spec.replicas
  retries: 60
  delay: 5
```

**Migration Strategy:**

1. Find all `pause` tasks
2. Determine what condition being waited for
3. Replace with proper wait logic
4. Add verification
5. Test with both fast and slow operations

### Anti-Pattern #3: No Error Handling

**Problem:**

```yaml
# If anything fails, everything stops with no context
- name: Operation 1
  shell: oc do-something

- name: Operation 2
  shell: oc do-something-else

- name: Operation 3
  shell: oc final-thing
```

**Why it's bad:**
- No cleanup on failure
- No diagnostic information
- Hard to debug failures
- May leave system in bad state

**Solution:**

```yaml
# Comprehensive error handling
- name: Multi-step operation with error handling
  block:
    - name: Operation 1
      kubernetes.core.k8s:
        definition: "{{ op1_def }}"
      register: op1_result
    
    - name: Operation 2
      kubernetes.core.k8s:
        definition: "{{ op2_def }}"
      register: op2_result
    
    - name: Operation 3
      kubernetes.core.k8s:
        definition: "{{ op3_def }}"
      register: op3_result
  
  rescue:
    - name: Collect diagnostic information
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Event
        namespace: "{{ namespace }}"
      register: events
    
    - name: Display failure context
      debug:
        msg: |
          Operation failed
          Last successful: {{ ansible_failed_task.name }}
          Error: {{ ansible_failed_result.msg }}
          Recent events: {{ events.resources | map(attribute='message') | list }}
    
    - name: Cleanup partial state
      kubernetes.core.k8s:
        api_version: v1
        kind: Pod
        name: "{{ item }}"
        namespace: "{{ namespace }}"
        state: absent
      loop:
        - op1-pod
        - op2-pod
      when: cleanup_on_failure | default(true)
    
    - name: Fail with complete information
      fail:
        msg: "Operation failed at step: {{ ansible_failed_task.name }}"
  
  always:
    - name: Record operation attempt
      lineinfile:
        path: /var/log/operations.log
        line: "{{ ansible_date_time.iso8601 }} - {{ operation_name }} - {{ 'success' if ansible_failed_task is not defined else 'failed' }}"
        create: yes
```

**Migration Strategy:**

1. Identify critical operation sequences
2. Wrap in block/rescue/always
3. Add diagnostic collection in rescue
4. Add cleanup in always
5. Test failure scenarios

### Anti-Pattern #4: Hard-Coded Values

**Problem:**

```yaml
# Values embedded everywhere
- name: Scale deployment
  shell: oc scale deployment myapp -n production --replicas=3

- name: Update config
  shell: |
    oc patch configmap myconfig -n production \
      -p '{"data":{"timeout":"30"}}'
```

**Why it's bad:**
- Can't reuse for different environments
- Hard to test
- Changes require code edits
- Error-prone copy-paste

**Solution:**

```yaml
# Parameterized and configurable
- name: Scale deployment
  kubernetes.core.k8s:
    api_version: apps/v1
    kind: Deployment
    name: "{{ app_name }}"
    namespace: "{{ app_namespace }}"
    definition:
      spec:
        replicas: "{{ app_replicas }}"

- name: Update configuration
  kubernetes.core.k8s:
    api_version: v1
    kind: ConfigMap
    name: "{{ config_name }}"
    namespace: "{{ app_namespace }}"
    definition:
      data:
        timeout: "{{ app_timeout }}"

# Variables in separate files
# group_vars/production.yml
app_namespace: production
app_replicas: 3
app_timeout: 30

# group_vars/staging.yml
app_namespace: staging
app_replicas: 1
app_timeout: 60
```

**Migration Strategy:**

1. Find hard-coded values
2. Extract to variables
3. Use inventory for environment-specific values
4. Create variable documentation
5. Test across environments

### Anti-Pattern #5: Monolithic Playbooks

**Problem:**

```yaml
# 800 line playbook doing everything
- name: Mega playbook
  hosts: localhost
  tasks:
    # 100 lines of validation
    # 200 lines of setup
    # 300 lines of main operation
    # 200 lines of cleanup
```

**Why it's bad:**
- Hard to understand
- Can't test parts independently
- Can't reuse logic
- Difficult to maintain

**Solution:**

```yaml
# Modular role-based design
# playbooks/main_operation.yml
- name: Execute main operation
  hosts: localhost
  
  roles:
    - role: validate_environment
      tags: [validation]
    
    - role: setup_prerequisites
      tags: [setup]
    
    - role: execute_operation
      tags: [execution]
    
    - role: cleanup
      tags: [cleanup]
      when: cleanup_enabled | default(true)

# Can now run parts:
# ansible-playbook main_operation.yml --tags validation
# ansible-playbook main_operation.yml --tags execution
```

**Migration Strategy:**

1. Identify logical sections in playbook
2. Extract each section to a role
3. Create orchestrator playbook
4. Add appropriate tags
5. Test each role independently

---

Continue in next response...

## Refactoring Strategies

### Strategy 1: The Strangler Fig Pattern

**Concept:** Gradually replace old code with new code, running both in parallel until migration is complete.

**Application to Ansible:**

```yaml
# Step 1: Original playbook (keep running)
# playbooks/cluster_setup.yml
- name: Cluster setup (original)
  hosts: localhost
  tasks:
    - name: Setup cluster (old way)
      shell: /scripts/setup_cluster.sh
      when: use_legacy_setup | default(true)
    
    # New implementation runs in parallel
    - name: Setup cluster (new way)
      include_role:
        name: cluster_setup
      when: not (use_legacy_setup | default(true))

# Step 2: Test new implementation
# Set use_legacy_setup: false in test environment
# Verify both produce same results

# Step 3: Gradually roll out
# production-cluster1: use_legacy_setup: false
# Test for 1 week
# production-cluster2: use_legacy_setup: false
# Test for 1 week
# All clusters: use_legacy_setup: false

# Step 4: Remove old code
# Delete shell script and legacy logic
```

**Benefits:**
- Low risk - can roll back instantly
- Gradual validation
- Production testing with safety net
- Team builds confidence

### Strategy 2: Feature Branch Per Pattern

**Concept:** Each anti-pattern type gets its own feature branch for focused migration.

**Workflow:**

```bash
# Branch 1: FQCN Migration
git checkout -b migration/fqcn
# Add FQCN to all modules
# Test thoroughly
# Merge to main

# Branch 2: Kubernetes Modules
git checkout -b migration/k8s-modules
# Replace oc commands with k8s modules
# Test thoroughly
# Merge to main

# Branch 3: Error Handling
git checkout -b migration/error-handling
# Add block/rescue/always
# Test thoroughly
# Merge to main
```

**Benefits:**
- Focused work
- Easier code reviews
- Clear progress tracking
- Can work in parallel

### Strategy 3: One Playbook Per Week

**Concept:** Dedicate one playbook per week for complete refactoring.

**Weekly Schedule:**

```markdown
## Week 1: cluster_upgrade.yml
- Monday: Assessment and planning
- Tuesday: Refactor shell commands
- Wednesday: Add error handling
- Thursday: Add tests
- Friday: Code review and merge

## Week 2: storage_provisioning.yml
- [Repeat process]

## Week 3: monitoring_setup.yml
- [Repeat process]
```

**Template:**

```markdown
# Playbook Refactoring Checklist

## Playbook: _______________
## Week of: _______________

### Monday: Assessment
- [ ] Run assessment script
- [ ] Document current issues
- [ ] Identify patterns to apply
- [ ] Estimate effort
- [ ] Create refactoring plan

### Tuesday-Thursday: Refactoring
- [ ] Replace shell commands with modules
- [ ] Add FQCN everywhere
- [ ] Add changed_when/failed_when
- [ ] Add error handling (block/rescue/always)
- [ ] Add verification steps
- [ ] Extract hard-coded values to variables
- [ ] Add proper tags
- [ ] Test after each change

### Friday: Quality & Review
- [ ] Run full test suite
- [ ] Ansible-lint passes
- [ ] Code review with team
- [ ] Update documentation
- [ ] Merge to main
- [ ] Celebrate! 🎉 (ok this one emoji is allowed)

### Success Criteria
- [ ] No shell/command for k8s operations
- [ ] All modules use FQCN
- [ ] Proper error handling
- [ ] Idempotent (can run multiple times)
- [ ] Tests passing
- [ ] Team reviewed and approved
```

### Strategy 4: Pair Programming Rotation

**Concept:** Rotate pairs daily to spread knowledge and maintain momentum.

**Rotation Schedule:**

```markdown
## 2-Week Rotation

### Week 1
Monday:    Alice + Bob    → Refactor playbook A
Tuesday:   Bob + Carol    → Refactor playbook B
Wednesday: Carol + Dave   → Refactor playbook C
Thursday:  Dave + Alice   → Refactor playbook D
Friday:    Mob session    → Review week's work

### Week 2
Monday:    Alice + Carol  → Refactor playbook E
Tuesday:   Bob + Dave     → Refactor playbook F
Wednesday: Carol + Bob    → Refactor playbook G
Thursday:  Dave + Carol   → Refactor playbook H
Friday:    Mob session    → Review and retrospective
```

**Pair Session Structure:**

```markdown
## Pair Programming Session Guide

### Setup (10 minutes)
- Pull latest code
- Review target playbook
- Agree on refactoring priorities

### Work (90 minutes)
- Driver: Writes code
- Navigator: Reviews, suggests, documents
- Switch roles every 30 minutes
- Commit and test frequently

### Wrap-up (20 minutes)
- Run full tests
- Document learnings
- Create PR
- Brief next pair

### Knowledge Capture
Document in shared wiki:
- Patterns encountered
- Solutions applied
- Blockers found
- Tips for next pair
```

---

## Migration Checklists

### Pre-Migration Checklist

Before starting migration, ensure:

**Technical Prerequisites:**

- [ ] Development environment set up
- [ ] Virtual environment configured
- [ ] All tools installed (ansible-lint, yamllint, etc.)
- [ ] Pre-commit hooks configured
- [ ] Test environment available
- [ ] Baseline metrics documented

**Team Prerequisites:**

- [ ] Team trained on new patterns
- [ ] Migration plan reviewed and approved
- [ ] Time allocated (2-4 hours/week per person)
- [ ] Code review process defined
- [ ] Communication plan established

**Documentation:**

- [ ] Standards document available
- [ ] Migration guide shared with team
- [ ] Pattern library started
- [ ] Success criteria defined

### Playbook Migration Checklist

For each playbook being migrated:

**Phase 1: Assessment**

- [ ] Playbook runs successfully in current state
- [ ] Baseline metrics captured
- [ ] All anti-patterns documented
- [ ] Dependencies identified
- [ ] Impact analysis completed

**Phase 2: FQCN & Basic Standards**

- [ ] All modules use FQCN
- [ ] All tasks have meaningful names
- [ ] Proper indentation (2 spaces)
- [ ] Comments added for complex logic
- [ ] Variables follow naming conventions

**Phase 3: Module Replacement**

- [ ] All oc/kubectl commands replaced with k8s modules
- [ ] Text parsing replaced with structured data
- [ ] Shell/command only where absolutely necessary
- [ ] All shell/command tasks have changed_when
- [ ] All shell/command tasks have failed_when

**Phase 4: Error Handling**

- [ ] Critical operations wrapped in block/rescue/always
- [ ] Rescue blocks collect diagnostics
- [ ] Always blocks perform cleanup
- [ ] Clear error messages
- [ ] Failure scenarios tested

**Phase 5: Idempotency**

- [ ] Playbook can run multiple times safely
- [ ] Only shows "changed" when actually changed
- [ ] Creates resources idempotently
- [ ] Updates resources idempotently
- [ ] Deletes resources idempotently

**Phase 6: Verification**

- [ ] Operations verified after execution
- [ ] Health checks added
- [ ] Status checks meaningful
- [ ] Timeouts appropriate
- [ ] Retries configured properly

**Phase 7: Testing**

- [ ] Syntax check passes
- [ ] Ansible-lint passes
- [ ] Check mode works
- [ ] Tag-based execution works
- [ ] Integration tests pass
- [ ] Tested in test environment
- [ ] Reviewed by peer

**Phase 8: Documentation**

- [ ] Variables documented
- [ ] Usage examples provided
- [ ] Tags documented
- [ ] Dependencies listed
- [ ] CHANGELOG updated

**Phase 9: Deployment**

- [ ] Merged to main branch
- [ ] Deployed to test environment
- [ ] Monitored for issues
- [ ] Rolled out to production
- [ ] Post-deployment verification

### Role Migration Checklist

For roles being created or refactored:

**Structure:**

- [ ] Proper directory structure
- [ ] README.md complete
- [ ] CHANGELOG.md initialized
- [ ] defaults/main.yml with all variables
- [ ] meta/main.yml with metadata
- [ ] tasks/main.yml as orchestrator

**Task Files:**

- [ ] preflight.yml for environment checks
- [ ] validate.yml for input validation
- [ ] execute.yml for main operations
- [ ] verify.yml for post-execution checks
- [ ] report.yml for result reporting (if needed)

**Quality:**

- [ ] All tasks use FQCN
- [ ] Meaningful task names
- [ ] Proper tags on all tasks
- [ ] Error handling implemented
- [ ] Idempotent operations
- [ ] Variables properly scoped

**Testing:**

- [ ] Test playbook created
- [ ] Unit tests for custom modules (if any)
- [ ] Integration tests
- [ ] All tests passing

**Documentation:**

- [ ] README with examples
- [ ] Variable documentation
- [ ] Tag documentation
- [ ] Troubleshooting guide

---

## Team Training Plan

### Week 1-2: Foundations

**Session 1: Why We're Migrating (1 hour)**

**Agenda:**
1. Current state assessment review (15 min)
2. Pain points discussion (15 min)
3. Benefits of new approach (15 min)
4. Migration plan overview (15 min)

**Materials:**
- Current code examples with issues highlighted
- Refactored examples showing improvements
- Migration timeline
- Success criteria

**Outcomes:**
- Team understands the why
- Team buys into the plan
- Questions answered
- Concerns addressed

**Session 2: FQCN & Basic Standards (1 hour)**

**Hands-on Exercise:**
```yaml
# Exercise: Fix this playbook
---
- name: Bad playbook
  hosts: localhost
  tasks:
    - name: task 1
      file:
        path: /tmp/test
        state: directory
    
    - name: run command
      command: oc get pods
      register: result

# Expected result:
---
- name: Fixed playbook
  hosts: localhost
  tasks:
    - name: Ensure working directory exists
      ansible.builtin.file:
        path: /tmp/test
        state: directory
        mode: '0755'
    
    - name: Get pod information
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Pod
      register: result
```

**Homework:**
- Fix FQCN in 1 existing playbook
- Share results with team

### Week 3-4: Kubernetes Modules

**Session 3: Understanding Structured Data (2 hours)**

**Part 1: The Problem with Text (30 min)**

Live demonstration:
```bash
# Show how this breaks
oc get pods | awk '{print $1}'
# Change terminal width
oc get pods | awk '{print $1}'
# Different output!
```

**Part 2: Structured Data (30 min)**

Live demonstration:
```yaml
- kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
  register: pods

- debug:
    msg: "{{ pods.resources | map(attribute='metadata.name') | list }}"
# Same output regardless of formatting
```

**Part 3: Hands-on Refactoring (60 min)**

Pairs refactor real playbook together

**Session 4: Common Patterns (1 hour)**

Walk through pattern library:
- Getting resources
- Creating resources
- Updating resources
- Monitoring operations
- Handling errors

Each person picks 1 pattern to become "expert" on

### Week 5-6: Error Handling

**Session 5: block/rescue/always (1.5 hours)**

**Part 1: Why Error Handling Matters (15 min)**

Show real production failure:
- What happened
- Why it was hard to debug
- How proper error handling would have helped

**Part 2: Pattern Practice (45 min)**

```yaml
# Exercise: Add error handling
- name: Operation without error handling
  kubernetes.core.k8s:
    definition: "{{ resource }}"

# Add block/rescue/always
```

**Part 3: Failure Scenario Testing (30 min)**

- Intentionally cause failures
- Watch error handling work
- See diagnostic information
- Understand cleanup

### Week 7-8: Advanced Patterns

**Session 6: Monitoring & Testing (2 hours)**

**Part 1: Monitoring Patterns (60 min)**
- Dual timeout strategy
- Activity vs progress
- Proper wait conditions

**Part 2: Testing (60 min)**
- Syntax validation
- Linting
- Check mode
- Integration tests

---

## Measuring Success

### Quantitative Metrics

**Track these metrics monthly:**

```yaml
# Monthly Migration Metrics

month: 2025-02
total_playbooks: 45
migrated_playbooks: 12  # Up from 0

code_quality:
  shell_command_usage: 156      # Down from 234
  oc_kubectl_commands: 78       # Down from 156
  text_parsing_usage: 34        # Down from 89
  missing_fqcn: 123             # Down from 567
  missing_guards: 45            # Down from 198
  ansible_lint_errors: 12       # Down from 45
  ansible_lint_warnings: 67     # Down from 123

operational_metrics:
  average_playbook_runtime: 20min   # Down from 25min
  failure_rate: 8%                  # Down from 12%
  false_positive_failures: 3%       # Down from 8%
  time_to_debug_failure: 25min      # Down from 45min

team_metrics:
  onboarding_time_days: 10      # Down from 14
  code_review_time_hours: 2.5   # Down from 4
  confidence_level: 6/10        # Up from 3/10
```

**Target Goals (End of 8 Weeks):**

```yaml
target_metrics:
  migrated_playbooks: 15-20
  shell_command_usage: <50
  oc_kubectl_commands: <20
  missing_fqcn: 0
  ansible_lint_errors: 0
  failure_rate: <5%
  confidence_level: 7+/10
```

### Qualitative Metrics

**Track team sentiment:**

```markdown
## Weekly Retrospective Questions

1. What went well this week?
2. What was challenging?
3. What did we learn?
4. What should we change?
5. Confidence level (1-10): ___

## Monthly Survey

Rate 1-5 (1=strongly disagree, 5=strongly agree):

- I understand why we're migrating
- The new patterns are clearer than the old
- I feel confident writing new automation
- Code reviews are catching issues early
- Playbooks are more reliable now
- Debugging is easier than before
- I would recommend these practices to others

Open feedback:
- What's working well?
- What's not working?
- What support do you need?
```

### Success Indicators

**You know migration is succeeding when:**

✅ **Code Quality**
- New code naturally follows standards
- Pre-commit hooks rarely block commits
- Lint errors decreasing month over month
- Code reviews focus on logic, not style

✅ **Operational Excellence**
- Fewer production failures
- Failures easier to debug
- Less time spent firefighting
- More time for new features

✅ **Team Dynamics**
- Team confidence increasing
- Knowledge spreading (not siloed)
- Junior engineers productive faster
- Less "tribal knowledge" required

✅ **Culture Shift**
- Team questions shell scripts in code review
- Engineers suggest better patterns
- Automation treated as "real code"
- Quality is everyone's concern

### Celebrating Milestones

**Recognize progress:**

```markdown
## Migration Milestones

### Milestone 1: First Clean Playbook
When: First playbook passes all quality checks
Celebration: Team lunch, share learnings

### Milestone 2: 50% Migrated
When: Half of critical playbooks refactored
Celebration: Demo to leadership, blog post

### Milestone 3: Zero Lint Errors
When: All playbooks pass ansible-lint
Celebration: Team outing, present at company tech talk

### Milestone 4: Migration Complete
When: All playbooks meet standards
Celebration: Team retrospective, document lessons learned, plan next improvements
```

---

## Common Challenges & Solutions

### Challenge 1: "This Will Take Forever"

**Symptom:**
Team feels overwhelmed by amount of legacy code

**Solution:**
- Start with highest-value targets
- Use 80/20 rule: 20% of playbooks used 80% of time
- Celebrate small wins
- Track and show progress

**Example:**
```markdown
Week 1: 0/45 playbooks migrated
Week 4: 3/45 playbooks migrated
Week 8: 8/45 playbooks migrated

But those 8 playbooks represent:
- 60% of all automation runs
- 80% of production deployments
- Most common failure points eliminated
```

### Challenge 2: "We Don't Have Time"

**Symptom:**
Migration keeps getting deprioritized

**Solution:**
- Make it part of regular work, not separate
- "Refactor when you touch it" rule
- Track time saved by better code
- Show ROI

**Time Investment vs Savings:**
```markdown
## Time Analysis

Investment:
- Week 1-2: 8 hours (setup, training)
- Week 3-4: 10 hours (initial refactoring)
- Week 5-6: 8 hours (error handling)
- Week 7-8: 6 hours (testing, docs)
Total: 32 hours over 8 weeks

Savings (monthly):
- Debug time: -20 hours/month
- False positives: -10 hours/month
- Onboarding: -16 hours/month (per new person)
- Code review: -8 hours/month

Break even: 1 month
ROI after 6 months: 300%
```

### Challenge 3: "It Works Now, Why Change?"

**Symptom:**
Team resistant to refactoring working code

**Solution:**
- Show concrete examples of current problems
- Demo benefits of better approach
- Start with pain points everyone feels
- Make it optional, let results speak

**Compelling Examples:**
```markdown
## Recent Incidents Caused by Shell Scripts

Incident 1: Production Outage (2 hours)
Cause: grep pattern matched more than expected
Impact: Deleted wrong pods
Prevention: Using k8s label selectors

Incident 2: Failed Deployment (4 hours)
Cause: Text parsing broke when pod names changed
Impact: Deployment appeared successful but wasn't
Prevention: Using structured API responses

Incident 3: Debug Marathon (6 hours)
Cause: No error context when shell command failed
Impact: Team spent hours reproducing issue
Prevention: Proper error handling with diagnostics
```

### Challenge 4: "The New Way Is More Verbose"

**Symptom:**
Complaints that k8s modules require more code

**Solution:**
- Show total lines including error handling
- Emphasize robustness over brevity
- Demonstrate maintainability benefits
- Teach Jinja2 filters for conciseness

**Comparison:**
```yaml
# Shell approach (looks shorter)
- shell: oc get pods | grep Running | wc -l
# 1 line, but breaks easily

# Module approach (more robust)
- kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
  register: pods
- set_fact:
    running: "{{ pods.resources | selectattr('status.phase', 'equalto', 'Running') | list | length }}"
# 6 lines, but:
# - Never breaks from formatting
# - Can access any pod field
# - Proper error handling
# - Self-documenting
```

### Challenge 5: "Our Situation Is Different"

**Symptom:**
Belief that standards don't apply to team's special cases

**Solution:**
- Acknowledge special cases exist
- Show how standards adapt
- Provide extension points
- Document justified exceptions

**Framework:**
```markdown
## Justifying Exceptions

When considering an exception to standards, document:

1. What standard would you violate?
2. Why is this case special?
3. What have you tried?
4. What's the risk if you don't make exception?
5. What's the cost of the exception?
6. How will you mitigate issues?
7. When will you revisit this?

Example justification:
- Standard: Use k8s modules, not oc commands
- Exception: Need to use oc debug for this specific troubleshooting task
- Why: kubernetes.core.k8s_exec doesn't support --as parameter needed
- Tried: Looking for alternative modules (none found)
- Risk: Can't troubleshoot permission issues
- Cost: One shell command in troubleshooting role
- Mitigation: Document clearly, check for module updates quarterly
- Revisit: Next Kubernetes collection update

Approved by: Tech Lead
Date: 2025-02-10
```

---

## Next Steps After Migration

### Continuous Improvement

**Once base migration complete:**

1. **Establish Standards for New Code**
   - All new playbooks follow standards
   - Pre-commit hooks enforced
   - Code review checklist mandatory

2. **Create Patterns Library**
   - Document common patterns
   - Provide templates
   - Share across team

3. **Regular Audits**
   - Monthly code quality review
   - Identify drift from standards
   - Update standards as needed

4. **Knowledge Sharing**
   - Monthly tech talks
   - Pattern presentations
   - Cross-team sharing

### Advanced Topics

**After mastering basics, explore:**

1. **Custom Modules**
   - When and how to create
   - Module best practices
   - Testing custom modules

2. **Complex Orchestration**
   - Multi-cluster operations
   - Conditional workflows
   - State machines

3. **Testing Strategies**
   - Molecule for role testing
   - Integration test frameworks
   - CI/CD pipelines

4. **Performance Optimization**
   - Async operations
   - Parallel execution
   - Caching strategies

---

## Conclusion

### Key Takeaways

**Migration is a Journey:**
- Takes time and patience
- Progress over perfection
- Small improvements compound
- Team learns together

**Success Factors:**
1. Management support
2. Team buy-in
3. Incremental approach
4. Continuous measurement
5. Celebrating progress

**Long-term Benefits:**
- More reliable automation
- Faster development
- Easier maintenance
- Better team morale
- Competitive advantage

### Your Migration Plan

```markdown
## Our Custom Migration Plan

Team: _____________
Start Date: _____________
Target Completion: _____________

Week 1-2: _____________
Week 3-4: _____________
Week 5-6: _____________
Week 7-8: _____________

Success Criteria:
- [ ] _____________
- [ ] _____________
- [ ] _____________

Team Commitment:
- Hours per week: _____________
- Meeting schedule: _____________
- Communication plan: _____________

Support Needed:
- Management: _____________
- Training: _____________
- Tools: _____________
```

### Resources

**Reference Documents:**
- [Ansible Development Standards](../../ANSIBLE-DEVELOPMENT-STANDARDS.md)
- [Comprehensive Guide](COMPREHENSIVE-GUIDE.md)
- [Code Review Checklist](CODE-REVIEW-CHECKLIST.md)
- [Kubernetes Patterns](KUBERNETES-PATTERNS.md)

**External Resources:**
- Ansible Documentation: https://docs.ansible.com
- Kubernetes Collection: https://docs.ansible.com/ansible/latest/collections/kubernetes/core/
- Best Practices: https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html

---

**Document Version:** 1.0.0  
**Last Updated:** 2025-02-10  
**Maintained By:** Platform Engineering Team

**Feedback Welcome:**
This is a living document. Share your migration experiences, challenges, and successes to help improve this guide for others.

---

**Good luck with your migration! You've got this! 🚀**

