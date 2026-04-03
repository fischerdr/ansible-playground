---
# ocp_zone_label_updater: Corrections from Source Code Review

## Context

After reviewing the reference Python implementation (`openshift_zone_updater.py` and
`k8s_utils.py` in the `pyplayground` repository), three corrections to
`plans/ansible-playbook-prompt.md` were identified. Apply these corrections during or after
implementing the role to ensure the Ansible implementation matches the proven Python logic.

---

## Correction 1: resourcePool Path Parsing (Phase 3, Task 3.1, Section A)

**Current plan says:**
> Zone = path segment at index 2 (zero-indexed) after splitting on `/`
> Skip if `split('/') | length < 4`

**Correct behaviour (from `parse_resource_pool_path` in k8s_utils.py):**
The Python strips the leading `/` before splitting, then takes `parts[2]`.

```python
parts = resource_pool.strip("/").split("/")
if len(parts) >= 3:
    return parts[2]
```

**Ansible Jinja2 equivalent:**

```yaml
# Extract zone from resourcePool path
# Input:  /vcenterdc/host/hostclustername/Resources
# Output: hostclustername
vars:
  _parts: "{{ resource_pool | regex_replace('^/', '') | split('/') }}"
  _zone: "{{ _parts[2] }}"

# Length guard (skip if malformed):
when: _parts | length >= 3
```

**Change required in execute.yml:**
- Length guard: `>= 3` parts (after strip), not `< 4` parts (before strip)
- Use `regex_replace('^/', '')` before `split('/')` to match Python behaviour
- `parts[2]` is always index 2 on the stripped result

---

## Correction 2: Machine Label Patch Path (Phase 3, Task 3.1, Section C)

**Current plan says:**
> Patch each valid Machine's `metadata.labels` with zone label

**Correct patch path (from `update_zone_label` in k8s_utils.py, line ~1363):**

```python
# Machine patch body
patch_data = {"spec": {"metadata": {"labels": {label_key: new_value}}}}
```

The Machine zone label lives at `spec.metadata.labels`, **not** top-level `metadata.labels`.

**Ansible patch definition for Machine:**

```yaml
- name: Patch zone label on Machine {{ item.machine_name }}
  kubernetes.core.k8s:
    state: patched
    api_version: "machine.openshift.io/v1beta1"
    kind: Machine
    name: "{{ item.machine_name }}"
    namespace: "{{ ocp_zone_label_updater_namespace }}"
    definition:
      spec:
        metadata:
          labels:
            "{{ ocp_zone_label_updater_label_key }}": "{{ item.zone }}"
```

Compare with MachineSet (one level deeper at `spec.template.spec.metadata.labels`):

```yaml
definition:
  spec:
    template:
      spec:
        metadata:
          labels:
            "{{ ocp_zone_label_updater_label_key }}": "{{ item.zone }}"
```

And Node (top-level `metadata.labels`):

```yaml
definition:
  metadata:
    labels:
      "{{ ocp_zone_label_updater_label_key }}": "{{ item.zone }}"
```

---

## Correction 3: verify.yml — Machine Label Assert Path (Phase 4, Task 4.1)

**Consequence of Correction 2:**
The verify.yml assertion for Machine labels must check `spec.metadata.labels`, not
`metadata.labels`.

**Correct assert for Machine:**

```yaml
- name: Assert zone label on Machine {{ item.machine_name }}
  ansible.builtin.assert:
    that:
      - >-
        item_machine.resources[0].spec.metadata.labels[ocp_zone_label_updater_label_key]
        is defined
      - >-
        item_machine.resources[0].spec.metadata.labels[ocp_zone_label_updater_label_key]
        == item.zone
    fail_msg: >
      ocp_zone_label_updater verify failed: Machine {{ item.machine_name }}
      does not have label {{ ocp_zone_label_updater_label_key }} = {{ item.zone }}.
```

---

## Summary Table

| # | File | Location | Issue | Fix |
|---|------|----------|-------|-----|
| 1 | execute.yml | Zone map build loop | Length guard uses `< 4` (no strip); index description ambiguous | Strip leading `/` first; guard `>= 3`; index `[2]` on stripped parts |
| 2 | execute.yml | Machine patch | "Machine's `metadata.labels`" is ambiguous | Machine zone label is at `spec.metadata.labels` |
| 3 | verify.yml | Machine assert | Assert checks wrong label path | Assert `spec.metadata.labels[label_key]` for Machines |

---

## Reference: Label Paths by Resource Type

| Resource | Patch path | Python constant |
|----------|-----------|-----------------|
| MachineSet | `spec.template.spec.metadata.labels` | `{"spec": {"template": {"spec": {"metadata": {"labels": {...}}}}}}` |
| Machine | `spec.metadata.labels` | `{"spec": {"metadata": {"labels": {...}}}}` |
| Node | `metadata.labels` | `{"metadata": {"labels": {...}}}` |
