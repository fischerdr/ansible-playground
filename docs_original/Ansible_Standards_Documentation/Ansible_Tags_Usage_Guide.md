# Ansible Tags Usage Guide

## For Junior and Mid-Level Operators

------------------------------------------------------------------------

## 1. Purpose of Tags

Tags allow selective execution of tasks within an Ansible playbook.\
They are commonly used in Automation Controller (AAP) to control which
parts of a playbook run during a job.

Tags help operators:

- Run only installation tasks
- Restart services without reinstalling packages
- Execute validation or cleanup independently
- Reduce runtime for targeted operations

------------------------------------------------------------------------

## 2. Default Behavior (No Tags Specified)

If no tags are provided in the job template:

- All tasks run
- Tagged tasks run
- Untagged tasks run
- Blocks run

There is no filtering.

------------------------------------------------------------------------

## 3. Basic Tagged Task Example

``` yaml
- name: Install package
  ansible.builtin.dnf:
    name: httpd
    state: present
  tags:
    - install

- name: Start service
  ansible.builtin.service:
    name: httpd
    state: started
  tags:
    - service
```

### Runtime Behavior

If the job runs with:

    --tags install

Only the "Install package" task runs.

The "Start service" task is skipped.

------------------------------------------------------------------------

## 4. What Happens to Untagged Tasks?

If a job is launched with any tag filter:

- Only tasks matching the selected tag(s) run.
- Untagged tasks are skipped.

Example:

``` yaml
- name: Install package
  ansible.builtin.dnf:
    name: httpd
    state: present
  tags:
    - install

- name: Debug message
  ansible.builtin.debug:
    msg: "Hello"
```

If run with:

    --tags install

The debug task is skipped because it has no tag.

------------------------------------------------------------------------

## 5. Multi-Tag Usage

A task may have multiple tags:

``` yaml
- name: Install package
  ansible.builtin.dnf:
    name: httpd
    state: present
  tags:
    - install
    - web
    - base
```

This task runs if any of these tags are selected.

Tag matching uses OR logic.

------------------------------------------------------------------------

## 6. Tagging Blocks

### 6.1 Block-Level Tag Behavior

``` yaml
- block:
    - name: Task A
      ansible.builtin.debug:
        msg: "A"

    - name: Task B
      ansible.builtin.debug:
        msg: "B"
  tags:
    - web
```

When a tag is applied at the block level:

- The tag is inherited by all tasks inside the block.
- It behaves as if each task had that tag explicitly defined.

### Execution Outcomes

  Runtime Condition   Result
  ------------------- ------------------------------------
  No tag filter       All tasks run
  --tags web          All tasks in the block run
  --tags install      All tasks in the block are skipped

------------------------------------------------------------------------

### 6.2 Block Tags and Task Tags Combined

``` yaml
- block:
    - name: Task A
      ansible.builtin.debug:
        msg: "A"
      tags:
        - special

    - name: Task B
      ansible.builtin.debug:
        msg: "B"
  tags:
    - web
```

Effective tagging:

- Task A → web, special
- Task B → web

Execution behavior:

  Runtime Filter   Task A    Task B
  ---------------- --------- ---------
  --tags web       Runs      Runs
  --tags special   Runs      Skipped
  --tags install   Skipped   Skipped

Important: Tag evaluation still occurs per task.\
The block does not force execution; it applies inherited tags.

------------------------------------------------------------------------

### 6.3 Untagged Tasks Inside Tagged Blocks

If tasks inside a tagged block have no individual tags, they still
inherit the block's tag.

Therefore:

- They run if the block tag matches.
- They do not run if it does not match.

------------------------------------------------------------------------

## 7. Special Tag: always

The `always` tag runs regardless of tag filtering.

Example:

``` yaml
- name: Always run this
  ansible.builtin.debug:
    msg: "This always runs"
  tags:
    - always
```

Behavior:

- Runs when no tags are specified

- Runs when specific tags are specified

- Skipped only if explicitly excluded with:

        --skip-tags always

Use `always` carefully for mandatory validation, safety checks, or audit
logic.

------------------------------------------------------------------------

## 8. Skip Tags

Tags can also be excluded.

Example:

    --skip-tags install

All tasks tagged `install` are skipped.

Other tasks run normally.

------------------------------------------------------------------------

## 9. Execution Summary Table

  Scenario                              Tagged Task        Untagged Task   always
  ------------------------------------- ------------------ --------------- ---------
  No tags specified                     Runs               Runs            Runs
  --tags install                        Runs if matching   Skipped         Runs
  --skip-tags install                   Skipped            Runs            Runs
  --tags install + --skip-tags always   Runs               Skipped         Skipped

------------------------------------------------------------------------

## 10. Operational Best Practices

- Tag all operationally distinct task groups.
- Avoid mixing unrelated logic under the same tag.
- Use consistent naming conventions (install, config, validate,
    cleanup).
- Avoid leaving critical tasks untagged in controlled environments.
- Use `always` only for mandatory execution logic.

------------------------------------------------------------------------

## 11. Key Rules to Remember

1. No tag filter = everything runs.
2. Tag filter present = only matching tags run.
3. Untagged tasks do not run when filtering.
4. Multiple tags use OR logic.
5. Block tags are inherited by contained tasks.
6. `always` overrides filtering unless explicitly skipped.

------------------------------------------------------------------------

End of Document
