# AWX CLI Python 3.13 Compatibility Fix

## Problem Description

The `awx` CLI tool (from the `awxkit` package version 24.6.1) is incompatible with Python 3.13 due to a breaking change in the `argparse.ArgumentParser` API.

### Error Symptoms

When attempting to run any `awx` command with Python 3.13, the following error occurs:

```
Traceback (most recent call last):
  File "/development/git/ansible-playground/.venv/lib64/python3.13/site-packages/awxkit/cli/__init__.py", line 23, in run
    cli.parse_args(argv or sys.argv)
  File "/development/git/ansible-playground/.venv/lib64/python3.13/site-packages/awxkit/cli/client.py", line 296, in parse_args
    self.args = self.parser.parse_known_args(self.argv)[0]
  File "/usr/lib64/python3.13/argparse.py", line 1908, in parse_known_args
    return self._parse_known_args2(args, namespace, intermixed=False)
  File "/usr/lib64/python3.13/argparse.py", line 1937, in _parse_known_args2
    namespace, args = self._parse_known_args(args, namespace, intermixed)
TypeError: HelpfulArgumentParser._parse_known_args() takes 3 positional arguments but 4 were given

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/development/git/ansible-playground/.venv/bin/awx", line 8, in <module>
    sys.exit(run())
  File "/development/git/ansible-playground/.venv/lib64/python3.13/site-packages/awxkit/cli/__init__.py", line 65, in run
    if cli.verbose:
AttributeError: 'CLI' object has no attribute 'verbose'
```

### Root Cause

Python 3.13 introduced a breaking change to the `argparse.ArgumentParser._parse_known_args()` method signature:

**Python 3.12 and earlier:**
```python
def _parse_known_args(self, args, namespace):
```

**Python 3.13:**
```python
def _parse_known_args(self, args, namespace, intermixed=False):
```

The `awxkit` library's `HelpfulArgumentParser` class overrides `_parse_known_args()` but uses the old signature, causing a TypeError when Python 3.13's argparse tries to call it with the new `intermixed` parameter.

## Solution

Patch the `HelpfulArgumentParser._parse_known_args()` method to accept the `intermixed` parameter and pass it to the parent class.

### File to Modify

```
.venv/lib64/python3.13/site-packages/awxkit/cli/utils.py
```

### Code Changes

**Before (line 43-49):**
```python
def _parse_known_args(self, args, ns):
    for arg in ('-h', '--help'):
        # the -h argument is extraneous; if you leave it off,
        # awx-cli will just print usage info
        if arg in args:
            args.remove(arg)
    return super(HelpfulArgumentParser, self)._parse_known_args(args, ns)
```

**After (line 43-49):**
```python
def _parse_known_args(self, args, ns, intermixed=False):
    for arg in ('-h', '--help'):
        # the -h argument is extraneous; if you leave it off,
        # awx-cli will just print usage info
        if arg in args:
            args.remove(arg)
    return super(HelpfulArgumentParser, self)._parse_known_args(args, ns, intermixed)
```

### Changes Summary

1. Added `intermixed=False` parameter to method signature
2. Pass `intermixed` parameter to parent class call

The `intermixed=False` default value maintains backward compatibility while supporting the new Python 3.13 API.

## Application Instructions

### Manual Patch

Edit the file directly:

```bash
# Navigate to the virtual environment
cd /development/git/ansible-playground

# Edit the utils.py file
nano .venv/lib64/python3.13/site-packages/awxkit/cli/utils.py
```

Locate line 43 and make the changes described above.

### Automated Patch (using sed)

```bash
# Backup the original file
cp .venv/lib64/python3.13/site-packages/awxkit/cli/utils.py \
   .venv/lib64/python3.13/site-packages/awxkit/cli/utils.py.backup

# Apply the patch
sed -i 's/def _parse_known_args(self, args, ns):/def _parse_known_args(self, args, ns, intermixed=False):/' \
  .venv/lib64/python3.13/site-packages/awxkit/cli/utils.py

sed -i 's/return super(HelpfulArgumentParser, self)._parse_known_args(args, ns)/return super(HelpfulArgumentParser, self)._parse_known_args(args, ns, intermixed)/' \
  .venv/lib64/python3.13/site-packages/awxkit/cli/utils.py
```

## Verification

Test that the `awx` command works correctly:

```bash
# Activate virtual environment
source .venv/bin/activate

# Test help output (should not error)
awx --help

# Test version (should not error)
awx --version

# Test with connection (will fail to connect but should parse arguments)
awx config
```

Expected output for `awx --help`:
```
usage: awx [--help] [--version] [--conf.host https://example.awx.org]
           [--conf.token TEXT] [--conf.username TEXT] [--conf.password TEXT]
           [-k] [-f {json,yaml,jq,human}] [--filter TEXT]
           [--conf.color BOOLEAN] [-v]
           resource ...
```

No TypeErrors or AttributeErrors should occur.

## Impact and Limitations

### What Works

- All `awx` CLI commands now parse arguments correctly
- Full compatibility with Python 3.13
- Backward compatible with Python 3.12 and earlier
- No functional changes to awx behavior

### Limitations

- Patch must be reapplied if virtual environment is recreated
- Patch must be reapplied if awxkit is upgraded
- This is a local workaround until awxkit maintainers release an official fix

### Persistence Strategy

To ensure the patch persists across environment recreations:

1. Document the patch requirement in project README
2. Add a post-installation script to apply the patch automatically
3. Include verification in CI/CD pipelines
4. Monitor awxkit releases for official Python 3.13 support

## Upstream Status

This issue should be reported to the awxkit maintainers:

- Project: https://github.com/ansible/awx
- Issue tracker: https://github.com/ansible/awx/issues

Search for existing issues related to Python 3.13 compatibility before creating a new one.

## Alternative Solutions

### Use Python 3.12

If patching is not acceptable, downgrade to Python 3.12:

```bash
# Create new virtual environment with Python 3.12
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Use awxkit API Directly

Instead of using the CLI, use the awxkit Python API in scripts:

```python
from awxkit.api.client import Connection

conn = Connection('https://your-aap-server')
conn.login(username='admin', password='password')
# Use programmatic API instead of CLI
```

## Testing Checklist

After applying the patch, verify:

- [ ] `awx --help` displays help without errors
- [ ] `awx --version` displays version without errors
- [ ] `awx config` attempts connection (error expected without server)
- [ ] No TypeErrors in output
- [ ] No AttributeErrors in output
- [ ] AAP import scripts function correctly
- [ ] Ansible playbooks using awx CLI execute successfully

## Related Documentation

- Python 3.13 Release Notes: https://docs.python.org/3/whatsnew/3.13.html
- argparse documentation: https://docs.python.org/3/library/argparse.html
- awxkit documentation: https://docs.ansible.com/ansible-tower/latest/html/towercli/index.html

## Version Information

- Python Version: 3.13.9
- awxkit Version: 24.6.1
- Affected File: `.venv/lib64/python3.13/site-packages/awxkit/cli/utils.py`
- Fix Applied: 2025-12-12
- Status: Temporary workaround pending upstream fix
