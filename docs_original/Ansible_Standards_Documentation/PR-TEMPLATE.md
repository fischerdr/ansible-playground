# Pull Request Template

**Instructions:** Copy this template to `.github/pull_request_template.md` or `.gitlab/merge_request_templates/default.md` in your repository.

---

## Pull Request Information

### Title Format
Use one of these prefixes:
- `feat:` New feature or capability
- `fix:` Bug fix
- `refactor:` Code refactoring (no functional changes)
- `docs:` Documentation updates
- `test:` Test additions or modifications
- `chore:` Maintenance tasks (deps, config, etc.)

**Example:** `feat: Replace oc commands with k8s modules in cluster_setup playbook`

---

## Description

### What does this PR do?
<!-- Briefly describe the changes in 2-3 sentences -->


### Why is this change needed?
<!-- Describe the problem being solved or feature being added -->


### How does this PR solve the problem?
<!-- Explain your implementation approach -->


---

## Changes Made

### Modified Files
<!-- List key files changed and why -->

- `playbooks/cluster_setup.yml` - Replaced shell commands with k8s modules
- `roles/cluster_ops/tasks/main.yml` - Added error handling
- `docs/README.md` - Updated usage examples

### Type of Change
<!-- Check all that apply -->

- [ ] New playbook/role
- [ ] Refactoring existing code
- [ ] Bug fix
- [ ] Documentation update
- [ ] Breaking change (requires version bump)

---

## Testing Performed

### Pre-Submission Checks
<!-- Verify you ran these before submitting -->

- [ ] Ran `scripts/pre_submit_check.sh` - All checks passed
- [ ] Syntax check passed (`ansible-playbook --syntax-check`)
- [ ] Ansible-lint passed (production profile)
- [ ] YAML lint passed
- [ ] Python quality checks passed (if applicable)

### Functional Testing
<!-- Describe testing performed -->

**Test Environment:**
- [ ] Local development
- [ ] Test cluster
- [ ] Staging environment
- [ ] Production (canary/rollout plan described below)

**Test Scenarios:**
<!-- Check all that were tested -->
- [ ] Happy path (normal execution)
- [ ] Error scenarios
- [ ] Edge cases
- [ ] Idempotency (ran twice, no issues)
- [ ] Check mode (`--check` flag)
- [ ] Tag-based execution

**Test Results:**
<!-- Describe what you tested and the results -->

```text
Example:
- Ran playbook against test cluster (3 nodes)
- All tasks executed successfully
- Verified resources created correctly
- Re-ran playbook - no changes reported (idempotent)
- Tested error handling by simulating failure - cleanup worked correctly
```

---

## Standards Compliance

### Code Quality Checklist
<!-- Verify your code meets standards -->

#### Required (MUST)
- [ ] All modules use FQCN (ansible.builtin.*, kubernetes.core.*)
- [ ] Shell/command tasks have `changed_when` and `failed_when`
- [ ] Critical operations wrapped in block/rescue/always
- [ ] Variables follow naming convention (`<role_name>_variable_name`)
- [ ] Tasks have meaningful, descriptive names
- [ ] Proper tags applied (role name, phase tags)
- [ ] No hardcoded credentials (use Ansible Vault)

#### Recommended (SHOULD)
- [ ] Using kubernetes.core modules instead of oc/kubectl commands
- [ ] Using structured data instead of text parsing (grep/awk/sed)
- [ ] Operations are idempotent
- [ ] Error messages are clear and actionable
- [ ] Complex logic has explanatory comments

#### Documentation
- [ ] README.md updated (if needed)
- [ ] CHANGELOG.md updated
- [ ] New variables documented in defaults/main.yml
- [ ] Complex logic has inline comments
- [ ] Usage examples provided (if new feature)

---

## Migration/Refactoring Specific
<!-- If this PR is part of migration effort -->

**Migration Pattern Applied:**
<!-- Check which pattern from MIGRATION-GUIDE.md -->
- [ ] FQCN addition
- [ ] Shell command → k8s module
- [ ] Text parsing → structured data
- [ ] Error handling addition
- [ ] Idempotency fix
- [ ] Variable extraction
- [ ] Other: _______________

**Anti-Pattern Fixed:**
<!-- Reference MIGRATION-GUIDE.md section -->

```yaml
# Before (anti-pattern):
- shell: oc get pods | grep Running | wc -l

# After (proper pattern):
- kubernetes.core.k8s_info:
    api_version: v1
    kind: Pod
  register: pods
- set_fact:
    running_count: "{{ pods.resources | selectattr('status.phase', 'equalto', 'Running') | list | length }}"
```

---

## Security Considerations

### Security Review
<!-- Check all that apply -->

- [ ] No credentials in code
- [ ] Sensitive operations use `no_log: true`
- [ ] Secrets use Ansible Vault
- [ ] File permissions explicitly set
- [ ] No SQL injection vectors
- [ ] No command injection vectors
- [ ] Input validation for user-provided variables

### Secrets/Credentials
- [ ] No secrets added in this PR
- [ ] Secrets moved to Vault (specify which: _____________)
- [ ] Existing secrets remain properly vaulted

---

## Breaking Changes

### Does this PR introduce breaking changes?
- [ ] No breaking changes
- [ ] Yes - breaking changes (describe below)

**If yes, describe:**
<!-- What breaks and what's needed to migrate -->


**Migration Path:**
<!-- How to update existing usage -->


**Version Bump Required:**
<!-- Should this trigger a major/minor/patch version bump? -->
- [ ] Major (breaking changes)
- [ ] Minor (new features, backwards compatible)
- [ ] Patch (bug fixes, backwards compatible)

---

## Deployment Considerations

### Rollout Plan
<!-- Describe deployment approach -->

- [ ] Can deploy immediately
- [ ] Requires coordination with: _______________
- [ ] Requires rollout in stages (describe below)
- [ ] Requires infrastructure changes first

**Rollout Strategy:**
<!-- If staged rollout needed -->
```text
Example:
1. Deploy to dev cluster (test for 1 week)
2. Deploy to staging cluster (test for 3 days)
3. Deploy to prod-cluster-1 (canary, monitor for 2 days)
4. Deploy to remaining prod clusters
```

### Rollback Plan
<!-- How to rollback if issues found -->

- [ ] Standard rollback (revert PR)
- [ ] Special considerations: _______________

---

## Related Items

### Related Issues/Tickets
<!-- Link to Jira, GitHub issues, etc. -->

- Fixes: #___
- Related to: #___
- Implements: JIRA-___

### Related PRs
<!-- Link related PRs if this is part of larger effort -->

- Depends on: #___
- Follows: #___
- Part of epic: #___

### Documentation
<!-- Link to design docs, RFCs, runbooks -->

- Design doc: _______________
- Runbook: _______________
- RFC: _______________

---

## Screenshots/Logs (if applicable)

### Before
<!-- Show current behavior/output -->

```text
Paste relevant output showing current behavior
```

### After
<!-- Show new behavior/output -->

```text
Paste relevant output showing new behavior
```

---

## Additional Context

### Known Issues/Limitations
<!-- Describe any known limitations of this implementation -->


### Future Improvements
<!-- Nice-to-haves that aren't in scope for this PR -->


### Questions for Reviewers
<!-- Specific questions or areas you'd like reviewers to focus on -->


---

## Reviewer Guidance

### Focus Areas
<!-- Guide reviewers on what to pay attention to -->

Please review:
- [ ] Logic correctness in: _______________
- [ ] Error handling in: _______________
- [ ] Security considerations for: _______________
- [ ] Performance implications of: _______________

### Review Checklist Reference
See [CODE-REVIEW-CHECKLIST.md](CODE-REVIEW-CHECKLIST.md) for complete review guidelines.

---

## Author Self-Review

### I have reviewed my own code and:
- [ ] Removed any debugging statements
- [ ] Removed any commented-out code
- [ ] Removed any TODO comments without ticket numbers
- [ ] Verified no merge conflicts
- [ ] Verified all commits have meaningful messages
- [ ] Verified diff makes sense and matches description

### Size Consideration
- [ ] This PR is appropriately sized (<500 lines preferred)
- [ ] If >500 lines, I have justified why it can't be split

**Line Count:** ___ additions, ___ deletions

---

## Post-Merge Actions

### Actions needed after merge:
- [ ] Update team documentation
- [ ] Notify stakeholders
- [ ] Schedule follow-up work
- [ ] Monitor deployment
- [ ] Other: _______________

---

## Acknowledgments

### Credits
<!-- Give credit where due -->

- Pair programming with: _______________
- Reviewed by: _______________
- Inspired by: _______________
- Thanks to _______________ for helping with: _______________

---

**Ready for Review:** ✅

<!-- 
Delete this section before submitting:

Tips for a great PR:
1. Keep it small and focused (one thing per PR)
2. Write clear commit messages
3. Test thoroughly before submitting
4. Fill out this template completely
5. Self-review your diff before requesting review
6. Respond promptly to reviewer feedback
7. Thank your reviewers!

Remember: Good PRs get reviewed faster!
-->
