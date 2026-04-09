# Ansible Role Standards and Best Practices

**Document Version:** 1.0.0  
**Last Updated:** 2024-12-30  
**Purpose:** Comprehensive standards for Ansible role development including modules, filters, playbooks, and tasks

---

## Table of Contents

1. [Standard Role Structure](#standard-role-structure)
2. [Common Utility Modules](#common-utility-modules)
3. [Standard Filter Plugins](#standard-filter-plugins)
4. [Playbook Design Patterns](#playbook-design-patterns)
5. [Task Organization Standards](#task-organization-standards)
6. [Variable Management](#variable-management)
7. [Error Handling Patterns](#error-handling-patterns)
8. [Testing Standards](#testing-standards)
9. [Documentation Requirements](#documentation-requirements)

---

## Standard Role Structure

### Complete Role Directory Layout

Every production Ansible role should follow this structure:

```text
<role_name>/
├── README.md                      # Role documentation
├── CHANGELOG.md                   # Version history
├── LICENSE                        # License file (Apache-2.0 recommended)
├── .ansible-lint                  # Role-specific lint config (optional)
├── requirements.yml               # Ansible collection dependencies
├── requirements.txt               # Python dependencies (if needed)
├── defaults/
│   └── main.yml                  # Default variables (user-configurable)
├── vars/
│   └── main.yml                  # Internal constants (not user-configurable)
├── meta/
│   └── main.yml                  # Role metadata and dependencies
├── tasks/
│   ├── main.yml                  # Main orchestrator
│   ├── preflight.yml             # Pre-flight checks
│   ├── validation.yml            # Input validation
│   ├── prepare.yml               # Environment preparation
│   ├── execute.yml               # Main execution
│   ├── verify.yml                # Post-execution verification
│   ├── cleanup.yml               # Cleanup operations
│   └── report.yml                # Result reporting
├── handlers/
│   └── main.yml                  # Event handlers
├── templates/
│   ├── config.j2                 # Configuration templates
│   └── report.j2                 # Report templates
├── files/
│   ├── scripts/                  # Static scripts
│   └── configs/                  # Static configuration files
├── library/                       # Custom Ansible modules
│   ├── <module_name>.py
│   └── README.md                 # Module documentation
├── filter_plugins/                # Custom Jinja2 filters
│   ├── <filter_name>.py
│   └── README.md                 # Filter documentation
├── module_utils/                  # Shared Python utilities (optional)
│   └── <utility_name>.py
└── tests/                         # Role tests (optional)
    ├── test.yml                  # Test playbook
    └── inventory                 # Test inventory
```

### Required Files (Minimum)

Every role MUST have:

1. `defaults/main.yml` - Default variables
2. `meta/main.yml` - Role metadata
3. `tasks/main.yml` - Main entry point
4. `README.md` - Documentation
5. `CHANGELOG.md` - Version history

### Optional But Recommended

1. `handlers/main.yml` - For service restarts, notifications
2. `templates/` - For dynamic configuration files
3. `vars/main.yml` - For internal constants
4. `library/` - For custom modules
5. `filter_plugins/` - For custom filters

---

## Common Utility Modules

### Standard Utility Modules to Include

Every enterprise Ansible role ecosystem should have these common utility modules:

### 1. Resource Checker Module

**Purpose:** Check if a resource exists (file, directory, service, etc.)

**Location:** `library/resource_checker.py`

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: resource_checker
short_description: Check if a resource exists
description:
  - Checks various resource types (file, directory, service, process)
  - Returns existence status without making changes
  - Idempotent and check-mode compatible
version_added: "1.0.0"
author:
  - Your Name (@github_handle)
options:
  path:
    description: Path to file or directory
    type: str
  service:
    description: Service name to check
    type: str
  process:
    description: Process name to check
    type: str
  resource_type:
    description: Type of resource to check
    type: str
    required: true
    choices: [file, directory, service, process, port]
  port:
    description: Port number to check
    type: int
requirements:
  - python >= 3.11
'''

EXAMPLES = r'''
- name: Check if file exists
  resource_checker:
    path: /etc/config.conf
    resource_type: file

- name: Check if service is running
  resource_checker:
    service: httpd
    resource_type: service

- name: Check if port is listening
  resource_checker:
    port: 8080
    resource_type: port
'''

RETURN = r'''
exists:
  description: Whether the resource exists
  type: bool
  returned: always
details:
  description: Additional details about the resource
  type: dict
  returned: always
'''

import os
import subprocess
from ansible.module_utils.basic import AnsibleModule

def check_file(path):
    """Check if file exists."""
    return os.path.isfile(path)

def check_directory(path):
    """Check if directory exists."""
    return os.path.isdir(path)

def check_service(service_name):
    """Check if service is running."""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False

def check_process(process_name):
    """Check if process is running."""
    try:
        result = subprocess.run(
            ['pgrep', '-f', process_name],
            capture_output=True
        )
        return result.returncode == 0
    except Exception:
        return False

def check_port(port):
    """Check if port is listening."""
    try:
        result = subprocess.run(
            ['ss', '-tuln'],
            capture_output=True,
            text=True
        )
        return f':{port}' in result.stdout
    except Exception:
        return False

def run_module():
    module_args = dict(
        path=dict(type='str'),
        service=dict(type='str'),
        process=dict(type='str'),
        port=dict(type='int'),
        resource_type=dict(
            type='str',
            required=True,
            choices=['file', 'directory', 'service', 'process', 'port']
        )
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    resource_type = module.params['resource_type']
    result = dict(changed=False, exists=False, details={})

    try:
        if resource_type == 'file':
            path = module.params.get('path')
            if not path:
                module.fail_json(msg="path is required for file type")
            result['exists'] = check_file(path)
            result['details']['path'] = path

        elif resource_type == 'directory':
            path = module.params.get('path')
            if not path:
                module.fail_json(msg="path is required for directory type")
            result['exists'] = check_directory(path)
            result['details']['path'] = path

        elif resource_type == 'service':
            service = module.params.get('service')
            if not service:
                module.fail_json(msg="service is required for service type")
            result['exists'] = check_service(service)
            result['details']['service'] = service

        elif resource_type == 'process':
            process = module.params.get('process')
            if not process:
                module.fail_json(msg="process is required for process type")
            result['exists'] = check_process(process)
            result['details']['process'] = process

        elif resource_type == 'port':
            port = module.params.get('port')
            if not port:
                module.fail_json(msg="port is required for port type")
            result['exists'] = check_port(port)
            result['details']['port'] = port

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=f'Resource check failed: {str(e)}', **result)

def main():
    run_module()

if __name__ == '__main__':
    main()
```

### 2. Wait For Condition Module

**Purpose:** Wait for a condition to be met (more flexible than wait_for)

**Location:** `library/wait_for_condition.py`

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: wait_for_condition
short_description: Wait for a condition to be met
description:
  - Polls a condition until it becomes true or timeout is reached
  - Supports various condition types (command, file, port, url)
  - Configurable timeout and polling interval
version_added: "1.0.0"
author:
  - Your Name (@github_handle)
options:
  condition_type:
    description: Type of condition to check
    type: str
    required: true
    choices: [command, file, port, url, custom]
  command:
    description: Command to run (must exit 0 when condition met)
    type: str
  file_path:
    description: File path to check for existence
    type: str
  port:
    description: Port number to check
    type: int
  host:
    description: Host to check (for port/url checks)
    type: str
    default: localhost
  url:
    description: URL to check (HTTP 200 response expected)
    type: str
  timeout:
    description: Maximum time to wait in seconds
    type: int
    default: 300
  delay:
    description: Seconds to wait before first check
    type: int
    default: 0
  sleep:
    description: Seconds between checks
    type: int
    default: 5
requirements:
  - python >= 3.11
'''

EXAMPLES = r'''
- name: Wait for service to start
  wait_for_condition:
    condition_type: command
    command: systemctl is-active my-service
    timeout: 300

- name: Wait for file to appear
  wait_for_condition:
    condition_type: file
    file_path: /tmp/ready.flag
    timeout: 120

- name: Wait for port to be open
  wait_for_condition:
    condition_type: port
    host: localhost
    port: 8080
    timeout: 180

- name: Wait for URL to respond
  wait_for_condition:
    condition_type: url
    url: http://localhost:8080/health
    timeout: 300
'''

RETURN = r'''
elapsed:
  description: Time elapsed waiting in seconds
  type: int
  returned: always
attempts:
  description: Number of attempts made
  type: int
  returned: always
condition_met:
  description: Whether the condition was met
  type: bool
  returned: always
'''

import time
import subprocess
import os
from ansible.module_utils.basic import AnsibleModule

def check_command(command):
    """Check if command exits 0."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False

def check_file(file_path):
    """Check if file exists."""
    return os.path.exists(file_path)

def check_port(host, port):
    """Check if port is open."""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def check_url(url):
    """Check if URL returns 200."""
    try:
        import urllib.request
        response = urllib.request.urlopen(url, timeout=10)
        return response.status == 200
    except Exception:
        return False

def run_module():
    module_args = dict(
        condition_type=dict(
            type='str',
            required=True,
            choices=['command', 'file', 'port', 'url', 'custom']
        ),
        command=dict(type='str'),
        file_path=dict(type='str'),
        port=dict(type='int'),
        host=dict(type='str', default='localhost'),
        url=dict(type='str'),
        timeout=dict(type='int', default=300),
        delay=dict(type='int', default=0),
        sleep=dict(type='int', default=5)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    condition_type = module.params['condition_type']
    timeout = module.params['timeout']
    delay = module.params['delay']
    sleep_interval = module.params['sleep']

    result = dict(
        changed=False,
        elapsed=0,
        attempts=0,
        condition_met=False
    )

    if module.check_mode:
        result['msg'] = 'Check mode: would wait for condition'
        module.exit_json(**result)

    # Initial delay
    if delay > 0:
        time.sleep(delay)

    start_time = time.time()
    end_time = start_time + timeout

    try:
        while time.time() < end_time:
            result['attempts'] += 1
            condition_met = False

            if condition_type == 'command':
                command = module.params.get('command')
                if not command:
                    module.fail_json(msg="command required for command type")
                condition_met = check_command(command)

            elif condition_type == 'file':
                file_path = module.params.get('file_path')
                if not file_path:
                    module.fail_json(msg="file_path required for file type")
                condition_met = check_file(file_path)

            elif condition_type == 'port':
                port = module.params.get('port')
                host = module.params.get('host')
                if not port:
                    module.fail_json(msg="port required for port type")
                condition_met = check_port(host, port)

            elif condition_type == 'url':
                url = module.params.get('url')
                if not url:
                    module.fail_json(msg="url required for url type")
                condition_met = check_url(url)

            if condition_met:
                result['condition_met'] = True
                result['elapsed'] = int(time.time() - start_time)
                result['msg'] = f'Condition met after {result["attempts"]} attempts'
                module.exit_json(**result)

            time.sleep(sleep_interval)

        # Timeout reached
        result['elapsed'] = timeout
        module.fail_json(
            msg=f'Timeout reached after {result["attempts"]} attempts',
            **result
        )

    except Exception as e:
        result['elapsed'] = int(time.time() - start_time)
        module.fail_json(msg=f'Error checking condition: {str(e)}', **result)

def main():
    run_module()

if __name__ == '__main__':
    main()
```

### 3. JSON/YAML Data Validator Module

**Purpose:** Validate structured data against schemas

**Location:** `library/data_validator.py`

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: data_validator
short_description: Validate JSON/YAML data structures
description:
  - Validates data against required fields and types
  - Supports nested structures
  - Returns validation errors if any
version_added: "1.0.0"
author:
  - Your Name (@github_handle)
options:
  data:
    description: Data structure to validate
    type: dict
    required: true
  schema:
    description: Schema definition for validation
    type: dict
    required: true
  strict:
    description: Fail on unknown fields
    type: bool
    default: false
requirements:
  - python >= 3.11
'''

EXAMPLES = r'''
- name: Validate configuration
  data_validator:
    data: "{{ config }}"
    schema:
      required_fields:
        - name
        - version
        - enabled
      field_types:
        name: str
        version: str
        enabled: bool
        timeout: int

- name: Validate with nested structure
  data_validator:
    data: "{{ cluster_config }}"
    schema:
      required_fields:
        - cluster.name
        - cluster.nodes
      field_types:
        cluster.name: str
        cluster.nodes: list
'''

RETURN = r'''
valid:
  description: Whether data is valid
  type: bool
  returned: always
errors:
  description: List of validation errors
  type: list
  returned: when validation fails
'''

from ansible.module_utils.basic import AnsibleModule

def validate_data(data, schema, strict=False):
    """Validate data against schema."""
    errors = []
    required_fields = schema.get('required_fields', [])
    field_types = schema.get('field_types', {})

    # Check required fields
    for field in required_fields:
        if '.' in field:
            # Nested field
            parts = field.split('.')
            current = data
            for part in parts:
                if not isinstance(current, dict) or part not in current:
                    errors.append(f"Required field missing: {field}")
                    break
                current = current[part]
        else:
            if field not in data:
                errors.append(f"Required field missing: {field}")

    # Check field types
    for field, expected_type in field_types.items():
        if '.' in field:
            # Nested field
            parts = field.split('.')
            current = data
            for part in parts[:-1]:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    break
            if isinstance(current, dict) and parts[-1] in current:
                value = current[parts[-1]]
                if not validate_type(value, expected_type):
                    errors.append(
                        f"Field {field} has wrong type. "
                        f"Expected {expected_type}, got {type(value).__name__}"
                    )
        else:
            if field in data:
                value = data[field]
                if not validate_type(value, expected_type):
                    errors.append(
                        f"Field {field} has wrong type. "
                        f"Expected {expected_type}, got {type(value).__name__}"
                    )

    # Check for unknown fields if strict mode
    if strict:
        known_fields = set(required_fields) | set(field_types.keys())
        for field in data.keys():
            if field not in known_fields:
                errors.append(f"Unknown field: {field}")

    return errors

def validate_type(value, expected_type):
    """Check if value matches expected type."""
    type_map = {
        'str': str,
        'int': int,
        'float': float,
        'bool': bool,
        'list': list,
        'dict': dict
    }
    
    if expected_type not in type_map:
        return True  # Unknown type, skip validation
    
    return isinstance(value, type_map[expected_type])

def run_module():
    module_args = dict(
        data=dict(type='dict', required=True),
        schema=dict(type='dict', required=True),
        strict=dict(type='bool', default=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    data = module.params['data']
    schema = module.params['schema']
    strict = module.params['strict']

    result = dict(changed=False, valid=True)

    try:
        errors = validate_data(data, schema, strict)
        
        if errors:
            result['valid'] = False
            result['errors'] = errors
            module.fail_json(
                msg=f'Validation failed with {len(errors)} error(s)',
                **result
            )
        else:
            result['msg'] = 'Data validation successful'
            module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=f'Validation error: {str(e)}', **result)

def main():
    run_module()

if __name__ == '__main__':
    main()
```

---

## Standard Filter Plugins

### Common Filter Plugins to Include

### 1. Data Transformation Filters

**Location:** `filter_plugins/data_transforms.py`

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
filter: data_transforms
author: Your Name (@github_handle)
version_added: "1.0.0"
short_description: Common data transformation filters
description:
  - Collection of filters for data manipulation
  - Includes merge, flatten, group_by, and more
'''

from ansible.errors import AnsibleFilterError
from collections import defaultdict

class FilterModule(object):
    """Data transformation filters."""

    def filters(self):
        return {
            'deep_merge': self.deep_merge,
            'flatten_dict': self.flatten_dict,
            'group_by_key': self.group_by_key,
            'extract_keys': self.extract_keys,
            'safe_get': self.safe_get,
            'to_snake_case': self.to_snake_case,
            'to_camel_case': self.to_camel_case
        }

    @staticmethod
    def deep_merge(dict1, dict2):
        """Recursively merge two dictionaries.
        
        Args:
            dict1: First dictionary
            dict2: Second dictionary (takes precedence)
            
        Returns:
            Merged dictionary
        """
        if not isinstance(dict1, dict) or not isinstance(dict2, dict):
            raise AnsibleFilterError(
                f"deep_merge requires two dicts, got {type(dict1).__name__} "
                f"and {type(dict2).__name__}"
            )

        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = FilterModule.deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    @staticmethod
    def flatten_dict(data, separator='.', parent_key=''):
        """Flatten nested dictionary.
        
        Args:
            data: Dictionary to flatten
            separator: Key separator (default: '.')
            parent_key: Parent key prefix
            
        Returns:
            Flattened dictionary
        """
        if not isinstance(data, dict):
            raise AnsibleFilterError(
                f"flatten_dict requires dict, got {type(data).__name__}"
            )

        items = []
        for key, value in data.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else key
            if isinstance(value, dict):
                items.extend(
                    FilterModule.flatten_dict(value, separator, new_key).items()
                )
            else:
                items.append((new_key, value))
        return dict(items)

    @staticmethod
    def group_by_key(items, key):
        """Group list of dicts by a key.
        
        Args:
            items: List of dictionaries
            key: Key to group by
            
        Returns:
            Dictionary with grouped items
        """
        if not isinstance(items, list):
            raise AnsibleFilterError(
                f"group_by_key requires list, got {type(items).__name__}"
            )

        result = defaultdict(list)
        for item in items:
            if not isinstance(item, dict):
                raise AnsibleFilterError(
                    f"Items must be dicts, got {type(item).__name__}"
                )
            if key not in item:
                raise AnsibleFilterError(f"Key '{key}' not found in item")
            result[item[key]].append(item)
        return dict(result)

    @staticmethod
    def extract_keys(items, keys):
        """Extract specific keys from list of dicts.
        
        Args:
            items: List of dictionaries
            keys: List of keys to extract
            
        Returns:
            List of dictionaries with only specified keys
        """
        if not isinstance(items, list):
            raise AnsibleFilterError(
                f"extract_keys requires list, got {type(items).__name__}"
            )
        if not isinstance(keys, list):
            raise AnsibleFilterError(
                f"keys must be list, got {type(keys).__name__}"
            )

        result = []
        for item in items:
            if not isinstance(item, dict):
                raise AnsibleFilterError(
                    f"Items must be dicts, got {type(item).__name__}"
                )
            result.append({k: item.get(k) for k in keys if k in item})
        return result

    @staticmethod
    def safe_get(data, path, default=None):
        """Safely get nested value from dictionary.
        
        Args:
            data: Dictionary to query
            path: Dot-separated path (e.g., 'a.b.c')
            default: Default value if path not found
            
        Returns:
            Value at path or default
        """
        if not isinstance(data, dict):
            raise AnsibleFilterError(
                f"safe_get requires dict, got {type(data).__name__}"
            )

        keys = path.split('.')
        current = data
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        return current

    @staticmethod
    def to_snake_case(value):
        """Convert string to snake_case.
        
        Args:
            value: String to convert
            
        Returns:
            snake_case string
        """
        if not isinstance(value, str):
            raise AnsibleFilterError(
                f"to_snake_case requires str, got {type(value).__name__}"
            )

        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', value)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    @staticmethod
    def to_camel_case(value):
        """Convert string to camelCase.
        
        Args:
            value: String to convert
            
        Returns:
            camelCase string
        """
        if not isinstance(value, str):
            raise AnsibleFilterError(
                f"to_camel_case requires str, got {type(value).__name__}"
            )

        components = value.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
```

### 2. Time and Date Filters

**Location:** `filter_plugins/time_utils.py`

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
filter: time_utils
author: Your Name (@github_handle)
version_added: "1.0.0"
short_description: Time and date manipulation filters
description:
  - Filters for working with timestamps and durations
'''

from ansible.errors import AnsibleFilterError
from datetime import datetime, timedelta

class FilterModule(object):
    """Time and date filters."""

    def filters(self):
        return {
            'to_timestamp': self.to_timestamp,
            'from_timestamp': self.from_timestamp,
            'duration_seconds': self.duration_seconds,
            'format_duration': self.format_duration,
            'add_time': self.add_time,
            'time_diff': self.time_diff
        }

    @staticmethod
    def to_timestamp(date_string, format='%Y-%m-%d %H:%M:%S'):
        """Convert date string to Unix timestamp.
        
        Args:
            date_string: Date string to convert
            format: Date format (default: '%Y-%m-%d %H:%M:%S')
            
        Returns:
            Unix timestamp (int)
        """
        if not isinstance(date_string, str):
            raise AnsibleFilterError(
                f"to_timestamp requires str, got {type(date_string).__name__}"
            )

        try:
            dt = datetime.strptime(date_string, format)
            return int(dt.timestamp())
        except ValueError as e:
            raise AnsibleFilterError(f"Invalid date format: {str(e)}")

    @staticmethod
    def from_timestamp(timestamp, format='%Y-%m-%d %H:%M:%S'):
        """Convert Unix timestamp to date string.
        
        Args:
            timestamp: Unix timestamp
            format: Output format (default: '%Y-%m-%d %H:%M:%S')
            
        Returns:
            Formatted date string
        """
        if not isinstance(timestamp, (int, float)):
            raise AnsibleFilterError(
                f"from_timestamp requires int/float, got {type(timestamp).__name__}"
            )

        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime(format)
        except (ValueError, OSError) as e:
            raise AnsibleFilterError(f"Invalid timestamp: {str(e)}")

    @staticmethod
    def duration_seconds(start, end, format='%Y-%m-%d %H:%M:%S'):
        """Calculate duration in seconds between two timestamps.
        
        Args:
            start: Start time string
            end: End time string
            format: Time format
            
        Returns:
            Duration in seconds (int)
        """
        try:
            start_dt = datetime.strptime(start, format)
            end_dt = datetime.strptime(end, format)
            return int((end_dt - start_dt).total_seconds())
        except ValueError as e:
            raise AnsibleFilterError(f"Invalid date format: {str(e)}")

    @staticmethod
    def format_duration(seconds):
        """Format duration in seconds to human-readable string.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted string (e.g., "2h 30m 15s")
        """
        if not isinstance(seconds, (int, float)):
            raise AnsibleFilterError(
                f"format_duration requires int/float, got {type(seconds).__name__}"
            )

        seconds = int(seconds)
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")

        return " ".join(parts)

    @staticmethod
    def add_time(date_string, days=0, hours=0, minutes=0, seconds=0,
                 format='%Y-%m-%d %H:%M:%S'):
        """Add time to a date string.
        
        Args:
            date_string: Date string
            days: Days to add
            hours: Hours to add
            minutes: Minutes to add
            seconds: Seconds to add
            format: Date format
            
        Returns:
            New date string
        """
        try:
            dt = datetime.strptime(date_string, format)
            delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
            new_dt = dt + delta
            return new_dt.strftime(format)
        except ValueError as e:
            raise AnsibleFilterError(f"Invalid date format: {str(e)}")

    @staticmethod
    def time_diff(start, end, unit='seconds', format='%Y-%m-%d %H:%M:%S'):
        """Calculate time difference in specified unit.
        
        Args:
            start: Start time string
            end: End time string
            unit: Output unit (seconds, minutes, hours, days)
            format: Time format
            
        Returns:
            Time difference in specified unit
        """
        try:
            start_dt = datetime.strptime(start, format)
            end_dt = datetime.strptime(end, format)
            diff_seconds = (end_dt - start_dt).total_seconds()

            units = {
                'seconds': 1,
                'minutes': 60,
                'hours': 3600,
                'days': 86400
            }

            if unit not in units:
                raise AnsibleFilterError(f"Invalid unit: {unit}")

            return diff_seconds / units[unit]
        except ValueError as e:
            raise AnsibleFilterError(f"Invalid date format: {str(e)}")
```

### 3. String Manipulation Filters

**Location:** `filter_plugins/string_utils.py`

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
filter: string_utils
author: Your Name (@github_handle)
version_added: "1.0.0"
short_description: String manipulation filters
description:
  - Common string operations
'''

from ansible.errors import AnsibleFilterError
import re

class FilterModule(object):
    """String manipulation filters."""

    def filters(self):
        return {
            'sanitize_name': self.sanitize_name,
            'truncate_middle': self.truncate_middle,
            'mask_sensitive': self.mask_sensitive,
            'extract_pattern': self.extract_pattern,
            'version_compare': self.version_compare
        }

    @staticmethod
    def sanitize_name(value, replacement='_'):
        """Sanitize string for use as name/identifier.
        
        Args:
            value: String to sanitize
            replacement: Character to replace invalid chars with
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            raise AnsibleFilterError(
                f"sanitize_name requires str, got {type(value).__name__}"
            )

        # Replace invalid characters
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', replacement, value)
        # Remove consecutive replacements
        sanitized = re.sub(f'{re.escape(replacement)}+', replacement, sanitized)
        # Remove leading/trailing replacements
        sanitized = sanitized.strip(replacement)
        # Ensure starts with letter or underscore
        if sanitized and not sanitized[0].isalpha() and sanitized[0] != '_':
            sanitized = '_' + sanitized

        return sanitized.lower()

    @staticmethod
    def truncate_middle(value, max_length, separator='...'):
        """Truncate string in the middle.
        
        Args:
            value: String to truncate
            max_length: Maximum length
            separator: Separator for truncation
            
        Returns:
            Truncated string
        """
        if not isinstance(value, str):
            raise AnsibleFilterError(
                f"truncate_middle requires str, got {type(value).__name__}"
            )

        if len(value) <= max_length:
            return value

        sep_len = len(separator)
        if max_length < sep_len:
            return separator[:max_length]

        available = max_length - sep_len
        left_len = available // 2
        right_len = available - left_len

        return value[:left_len] + separator + value[-right_len:]

    @staticmethod
    def mask_sensitive(value, visible_chars=4, mask_char='*'):
        """Mask sensitive string (e.g., tokens, passwords).
        
        Args:
            value: String to mask
            visible_chars: Number of chars to leave visible at end
            mask_char: Character to use for masking
            
        Returns:
            Masked string
        """
        if not isinstance(value, str):
            raise AnsibleFilterError(
                f"mask_sensitive requires str, got {type(value).__name__}"
            )

        if len(value) <= visible_chars:
            return mask_char * len(value)

        masked_len = len(value) - visible_chars
        return (mask_char * masked_len) + value[-visible_chars:]

    @staticmethod
    def extract_pattern(value, pattern, group=0):
        """Extract pattern from string using regex.
        
        Args:
            value: String to search
            pattern: Regex pattern
            group: Group number to extract
            
        Returns:
            Extracted string or None
        """
        if not isinstance(value, str):
            raise AnsibleFilterError(
                f"extract_pattern requires str, got {type(value).__name__}"
            )

        try:
            match = re.search(pattern, value)
            if match:
                return match.group(group)
            return None
        except re.error as e:
            raise AnsibleFilterError(f"Invalid regex pattern: {str(e)}")

    @staticmethod
    def version_compare(version1, version2, operator='=='):
        """Compare two version strings.
        
        Args:
            version1: First version string
            version2: Second version string
            operator: Comparison operator (==, !=, <, <=, >, >=)
            
        Returns:
            Boolean result of comparison
        """
        from packaging import version
        
        try:
            v1 = version.parse(version1)
            v2 = version.parse(version2)

            operators = {
                '==': lambda a, b: a == b,
                '!=': lambda a, b: a != b,
                '<': lambda a, b: a < b,
                '<=': lambda a, b: a <= b,
                '>': lambda a, b: a > b,
                '>=': lambda a, b: a >= b
            }

            if operator not in operators:
                raise AnsibleFilterError(f"Invalid operator: {operator}")

            return operators[operator](v1, v2)
        except Exception as e:
            raise AnsibleFilterError(f"Version comparison error: {str(e)}")
```

---

## Playbook Design Patterns

### Standard Playbook Structure

```yaml
---
# Playbook: <playbook_name>.yml
# Purpose: Brief description of what this playbook does
# Author: Your Name
# Last Updated: 2024-12-30

- name: Descriptive play name
  hosts: target_hosts
  gather_facts: true  # or false if not needed
  become: false       # Only true if privilege escalation needed

  # Variables defined at play level
  vars:
    playbook_version: "1.0.0"
    work_dir: "/tmp/ansible-work"

  # Pre-tasks: Run before roles
  pre_tasks:
    - name: Validate required variables
      ansible.builtin.assert:
        that:
          - required_var is defined
          - required_var | length > 0
        fail_msg: "required_var must be defined and non-empty"
        success_msg: "All required variables are present"

    - name: Display playbook information
      ansible.builtin.debug:
        msg: |
          Playbook: {{ ansible_play_name }}
          Version: {{ playbook_version }}
          Target: {{ inventory_hostname }}
          User: {{ ansible_user_id }}

  # Roles: Main automation logic
  roles:
    - role: common
      tags: [common, base]
      
    - role: <your_role>
      tags: [<your_role>, main]
      vars:
        role_specific_var: "value"

  # Tasks: Additional tasks after roles
  tasks:
    - name: Final verification
      ansible.builtin.command: echo "Playbook completed successfully"
      changed_when: false

  # Post-tasks: Cleanup and reporting
  post_tasks:
    - name: Generate summary report
      ansible.builtin.template:
        src: summary.j2
        dest: "{{ work_dir }}/summary.txt"
        mode: '0644'

    - name: Display completion message
      ansible.builtin.debug:
        msg: "Playbook execution completed at {{ ansible_date_time.iso8601 }}"

  # Handlers: Event-driven tasks
  handlers:
    - name: restart service
      ansible.builtin.service:
        name: myservice
        state: restarted
      listen: "restart services"
```

### Multi-Stage Playbook Pattern

```yaml
---
# Multi-stage deployment playbook

- name: "Stage 1: Preparation"
  hosts: all
  gather_facts: true
  tags: [preparation, stage1]

  tasks:
    - name: Prepare environment
      ansible.builtin.include_role:
        name: preparation
        apply:
          tags: [preparation]

- name: "Stage 2: Validation"
  hosts: all
  gather_facts: false
  tags: [validation, stage2]

  tasks:
    - name: Validate prerequisites
      ansible.builtin.include_role:
        name: validation
        apply:
          tags: [validation]

- name: "Stage 3: Execution"
  hosts: all
  gather_facts: false
  tags: [execution, stage3]

  tasks:
    - name: Execute main tasks
      ansible.builtin.include_role:
        name: execution
        apply:
          tags: [execution]

- name: "Stage 4: Verification"
  hosts: all
  gather_facts: false
  tags: [verification, stage4]

  tasks:
    - name: Verify results
      ansible.builtin.include_role:
        name: verification
        apply:
          tags: [verification]
```

### Error Handling Playbook Pattern

```yaml
---
- name: Playbook with comprehensive error handling
  hosts: all
  gather_facts: true
  
  vars:
    max_retries: 3
    retry_delay: 5

  tasks:
    - name: Execute with error handling
      block:
        - name: Attempt main operation
          ansible.builtin.include_role:
            name: main_operation
          register: operation_result

        - name: Verify operation succeeded
          ansible.builtin.assert:
            that:
              - operation_result is succeeded
            fail_msg: "Operation failed"
            success_msg: "Operation successful"

      rescue:
        - name: Log error
          ansible.builtin.debug:
            msg: "Error occurred: {{ ansible_failed_result.msg }}"

        - name: Attempt recovery
          ansible.builtin.include_role:
            name: recovery
          when: enable_recovery | default(true)

        - name: Fail if recovery not possible
          ansible.builtin.fail:
            msg: "Recovery failed, manual intervention required"
          when: not enable_recovery | default(true)

      always:
        - name: Cleanup temporary files
          ansible.builtin.file:
            path: "{{ work_dir }}"
            state: absent
          when: cleanup_enabled | default(true)

        - name: Generate failure report
          ansible.builtin.template:
            src: failure_report.j2
            dest: "/var/log/ansible/failure-{{ ansible_date_time.epoch }}.log"
          when: ansible_failed_task is defined
```

---

## Task Organization Standards

### Task File Header Template

```yaml
---
# Task File: <task_file_name>.yml
# Purpose: Brief description of what these tasks do
# Dependencies: List any dependencies
# Variables Used:
#   - var1: Description
#   - var2: Description
# Returns:
#   - fact_name: Description of registered fact

```

### Modular Task Organization

#### Main Orchestrator (tasks/main.yml)

```yaml
---
# Role: <role_name>
# Main orchestrator - delegates to specialized task files

# Phase 1: Input Validation
- name: "Phase 1: Validate input parameters"
  ansible.builtin.include_tasks: validate_input.yml
  tags: [validation, input]

# Phase 2: Preflight Checks
- name: "Phase 2: Run preflight checks"
  ansible.builtin.include_tasks: preflight_checks.yml
  tags: [validation, preflight]
  when: skip_preflight | default(false) | bool == false

# Phase 3: Preparation
- name: "Phase 3: Prepare environment"
  ansible.builtin.include_tasks: prepare_environment.yml
  tags: [preparation]

# Phase 4: Execution
- name: "Phase 4: Execute main workflow"
  ansible.builtin.include_tasks: execute_workflow.yml
  tags: [execution]

# Phase 5: Verification
- name: "Phase 5: Verify results"
  ansible.builtin.include_tasks: verify_results.yml
  tags: [verification]
  when: skip_verification | default(false) | bool == false

# Phase 6: Cleanup
- name: "Phase 6: Cleanup resources"
  ansible.builtin.include_tasks: cleanup.yml
  tags: [cleanup]
  when: skip_cleanup | default(false) | bool == false

# Phase 7: Reporting
- name: "Phase 7: Generate report"
  ansible.builtin.include_tasks: generate_report.yml
  tags: [reporting]
  when: enable_reporting | default(true) | bool
```

#### Validation Task File (tasks/validate_input.yml)

```yaml
---
# Validate input parameters

- name: Validate required variables are defined
  ansible.builtin.assert:
    that:
      - <role_name>_required_var is defined
      - <role_name>_required_var | length > 0
    fail_msg: "<role_name>_required_var must be defined and non-empty"
    success_msg: "Required variables validated"
  tags: [validation]

- name: Validate variable types
  ansible.builtin.assert:
    that:
      - <role_name>_timeout is number
      - <role_name>_enabled is boolean
      - <role_name>_items is iterable
    fail_msg: "Variable types validation failed"
    success_msg: "Variable types validated"
  tags: [validation]

- name: Validate variable values
  ansible.builtin.assert:
    that:
      - <role_name>_timeout > 0
      - <role_name>_timeout <= 3600
    fail_msg: "timeout must be between 1 and 3600 seconds"
    success_msg: "Variable values validated"
  tags: [validation]

- name: Set validation fact
  ansible.builtin.set_fact:
    <role_name>_input_validated: true
    cacheable: false
```

#### Preflight Checks Task File (tasks/preflight_checks.yml)

```yaml
---
# Preflight checks before main execution

- name: Check system requirements
  block:
    - name: Check disk space
      ansible.builtin.shell: |
        set -o pipefail
        df -h {{ <role_name>_work_dir | dirname }} | awk 'NR==2 {print $4}'
      register: disk_space
      changed_when: false
      failed_when: false

    - name: Verify sufficient disk space
      ansible.builtin.assert:
        that:
          - disk_space.stdout | regex_replace('[^0-9]', '') | int > <role_name>_min_disk_gb
        fail_msg: "Insufficient disk space"
        success_msg: "Sufficient disk space available"

  tags: [preflight, system]

- name: Check external dependencies
  block:
    - name: Check required commands exist
      ansible.builtin.command: which {{ item }}
      loop: "{{ <role_name>_required_commands }}"
      register: command_check
      changed_when: false
      failed_when: command_check.rc != 0

    - name: Check service status
      ansible.builtin.systemd:
        name: "{{ <role_name>_required_service }}"
      register: service_status
      when: <role_name>_required_service is defined

  tags: [preflight, dependencies]

- name: Verify API connectivity
  ansible.builtin.uri:
    url: "{{ <role_name>_api_url }}/health"
    method: GET
    status_code: 200
    timeout: 10
  register: api_check
  retries: 3
  delay: 5
  until: api_check.status == 200
  tags: [preflight, api]

- name: Set preflight fact
  ansible.builtin.set_fact:
    <role_name>_preflight_passed: true
    cacheable: false
```

#### Execution with Error Handling (tasks/execute_workflow.yml)

```yaml
---
# Main execution workflow with error handling

- name: Execute main workflow
  block:
    - name: Create working directory
      ansible.builtin.file:
        path: "{{ <role_name>_work_dir }}"
        state: directory
        mode: '0755'

    - name: Execute primary operation
      ansible.builtin.command: "{{ <role_name>_command }}"
      register: execution_result
      changed_when: "'SUCCESS' in execution_result.stdout"
      failed_when: execution_result.rc != 0
      retries: "{{ <role_name>_max_retries }}"
      delay: "{{ <role_name>_retry_delay }}"
      until: execution_result.rc == 0

    - name: Process execution results
      ansible.builtin.set_fact:
        <role_name>_execution_status: "success"
        <role_name>_execution_time: "{{ execution_result.delta }}"
        <role_name>_execution_output: "{{ execution_result.stdout }}"
        cacheable: false

  rescue:
    - name: Log execution failure
      ansible.builtin.debug:
        msg: |
          Execution failed:
          Command: {{ <role_name>_command }}
          Error: {{ execution_result.stderr | default('Unknown error') }}
          Exit Code: {{ execution_result.rc | default('N/A') }}

    - name: Attempt recovery procedure
      ansible.builtin.include_tasks: recovery_procedure.yml
      when: <role_name>_enable_recovery | default(false)

    - name: Set failure fact
      ansible.builtin.set_fact:
        <role_name>_execution_status: "failed"
        <role_name>_execution_error: "{{ execution_result.stderr | default('Unknown error') }}"
        cacheable: false

    - name: Fail with detailed message
      ansible.builtin.fail:
        msg: |
          Workflow execution failed. Details:
          Status: {{ <role_name>_execution_status }}
          Error: {{ <role_name>_execution_error }}
          Recovery attempted: {{ <role_name>_enable_recovery | default(false) }}

  always:
    - name: Record execution timestamp
      ansible.builtin.set_fact:
        <role_name>_execution_timestamp: "{{ ansible_date_time.iso8601 }}"
        cacheable: false

  tags: [execution]
```

---

## Variable Management

### defaults/main.yml Template

```yaml
---
# defaults/main.yml - User-configurable variables

# General Settings
<role_name>_version: "1.0.0"
<role_name>_enabled: true
<role_name>_debug_mode: false

# Execution Settings
<role_name>_timeout: 300
<role_name>_max_retries: 3
<role_name>_retry_delay: 5

# Directory Settings
<role_name>_work_dir: "/tmp/ansible-<role_name>"
<role_name>_log_dir: "/var/log/<role_name>"
<role_name>_config_dir: "/etc/<role_name>"

# Feature Flags
<role_name>_skip_preflight: false
<role_name>_skip_verification: false
<role_name>_skip_cleanup: false
<role_name>_enable_reporting: true
<role_name>_enable_recovery: false

# Resource Limits
<role_name>_min_disk_gb: 10
<role_name>_max_connections: 100
<role_name>_memory_limit_mb: 2048

# API Settings (if applicable)
<role_name>_api_url: "http://localhost:8080"
<role_name>_api_timeout: 30
<role_name>_api_verify_ssl: true

# Notification Settings
<role_name>_notify_on_success: false
<role_name>_notify_on_failure: true
<role_name>_notification_email: "admin@example.com"

# Advanced Settings
<role_name>_parallel_execution: false
<role_name>_batch_size: 10
<role_name>_verbose_output: false
```

### vars/main.yml Template

```yaml
---
# vars/main.yml - Internal constants (not user-configurable)

# Internal Version Info
<role_name>_internal_version: "1.0.0"
<role_name>_last_updated: "2024-12-30"

# Internal Paths (derived from defaults)
<role_name>_temp_dir: "{{ <role_name>_work_dir }}/tmp"
<role_name>_backup_dir: "{{ <role_name>_work_dir }}/backups"
<role_name>_log_file: "{{ <role_name>_log_dir }}/<role_name>.log"

# Required Commands
<role_name>_required_commands:
  - curl
  - jq
  - tar
  - gzip

# Status Values (constants)
<role_name>_status_pending: "pending"
<role_name>_status_running: "running"
<role_name>_status_success: "success"
<role_name>_status_failed: "failed"

# Exit Codes
<role_name>_exit_success: 0
<role_name>_exit_failure: 1
<role_name>_exit_timeout: 124

# Regex Patterns
<role_name>_version_pattern: '^\d+\.\d+\.\d+$'
<role_name>_name_pattern: '^[a-zA-Z0-9_-]+$'

# Default Templates
<role_name>_config_template: "config.j2"
<role_name>_report_template: "report.j2"
```

---

## Error Handling Patterns

### Comprehensive Error Handling Block

```yaml
---
# Comprehensive error handling pattern

- name: Critical operation with full error handling
  block:
    # Pre-execution checks
    - name: Validate prerequisites
      ansible.builtin.assert:
        that:
          - prerequisite_met
        fail_msg: "Prerequisites not met"

    # Main operation
    - name: Execute main task
      ansible.builtin.command: "{{ main_command }}"
      register: main_result
      changed_when: main_result.rc == 0
      failed_when: main_result.rc not in [0, 2]  # 2 = acceptable warning

    # Post-execution verification
    - name: Verify operation results
      ansible.builtin.assert:
        that:
          - main_result is succeeded
          - "'SUCCESS' in main_result.stdout"
        fail_msg: "Operation verification failed"

  rescue:
    # Error classification
    - name: Classify error type
      ansible.builtin.set_fact:
        error_type: "{% if main_result.rc == 1 %}critical{% elif main_result.rc == 124 %}timeout{% else %}unknown{% endif %}"
        error_details:
          command: "{{ main_command }}"
          exit_code: "{{ main_result.rc | default('N/A') }}"
          stderr: "{{ main_result.stderr | default('No error output') }}"
          stdout: "{{ main_result.stdout | default('No output') }}"

    # Error logging
    - name: Log error details
      ansible.builtin.lineinfile:
        path: "{{ error_log }}"
        line: |
          [{{ ansible_date_time.iso8601 }}] {{ error_type | upper }} ERROR
          Command: {{ error_details.command }}
          Exit Code: {{ error_details.exit_code }}
          Error: {{ error_details.stderr }}
        create: true
        mode: '0644'

    # Recovery attempt (conditional)
    - name: Attempt automatic recovery
      ansible.builtin.include_tasks: recovery.yml
      when:
        - enable_auto_recovery | default(false)
        - error_type != 'critical'

    # Notification
    - name: Send failure notification
      ansible.builtin.mail:
        to: "{{ admin_email }}"
        subject: "Ansible Task Failure: {{ inventory_hostname }}"
        body: |
          Task failed on {{ inventory_hostname }}
          Error Type: {{ error_type }}
          Details: {{ error_details | to_nice_json }}
      when: send_notifications | default(false)
      delegate_to: localhost

    # Final failure
    - name: Fail with comprehensive message
      ansible.builtin.fail:
        msg: |
          Operation failed with {{ error_type }} error
          
          Command: {{ error_details.command }}
          Exit Code: {{ error_details.exit_code }}
          
          Error Output:
          {{ error_details.stderr }}
          
          Standard Output:
          {{ error_details.stdout }}
          
          Recovery Attempted: {{ enable_auto_recovery | default(false) }}
          Timestamp: {{ ansible_date_time.iso8601 }}

  always:
    # Cleanup (always runs)
    - name: Cleanup temporary files
      ansible.builtin.file:
        path: "{{ item }}"
        state: absent
      loop:
        - "{{ temp_dir }}"
        - "{{ lock_file }}"
      when: cleanup_enabled | default(true)

    # Metrics collection
    - name: Record execution metrics
      ansible.builtin.set_fact:
        execution_metrics:
          start_time: "{{ execution_start_time }}"
          end_time: "{{ ansible_date_time.iso8601 }}"
          duration: "{{ (ansible_date_time.epoch | int) - (execution_start_time | int) }}"
          status: "{% if ansible_failed_task is defined %}failed{% else %}success{% endif %}"
        cacheable: false

    # Status update
    - name: Update status file
      ansible.builtin.copy:
        content: "{{ execution_metrics | to_nice_json }}"
        dest: "{{ status_file }}"
        mode: '0644'
```

### Retry Pattern with Exponential Backoff

```yaml
---
# Retry with exponential backoff

- name: Operation with intelligent retry
  block:
    - name: Attempt operation with retries
      ansible.builtin.uri:
        url: "{{ api_endpoint }}"
        method: POST
        body: "{{ request_body }}"
        body_format: json
        status_code: [200, 201]
        timeout: "{{ request_timeout }}"
      register: api_response
      retries: 5
      delay: "{{ 2 ** (item | default(0)) }}"  # Exponential backoff: 1, 2, 4, 8, 16 seconds
      until: api_response.status in [200, 201]
      loop: "{{ range(0, 5) | list }}"
      loop_control:
        pause: "{{ 2 ** item }}"

  rescue:
    - name: Handle persistent failure
      ansible.builtin.debug:
        msg: "API request failed after {{ api_response.attempts }} attempts"

    - name: Fail gracefully
      ansible.builtin.fail:
        msg: "Unable to reach API after multiple retries"
```

---

## Testing Standards

### Role Testing Structure

```text
<role_name>/tests/
├── test.yml                    # Main test playbook
├── inventory                   # Test inventory
├── group_vars/
│   └── all.yml                # Test variables
├── integration/                # Integration tests
│   ├── test_basic.yml
│   ├── test_advanced.yml
│   └── test_error_handling.yml
└── unit/                       # Unit tests (Python)
    ├── test_modules.py
    └── test_filters.py
```

### Test Playbook Template (tests/test.yml)

```yaml
---
# Test playbook for <role_name>

- name: Test <role_name> role
  hosts: localhost
  gather_facts: true
  
  vars:
    test_work_dir: "/tmp/ansible-test-<role_name>"

  pre_tasks:
    - name: Create test environment
      ansible.builtin.file:
        path: "{{ test_work_dir }}"
        state: directory
        mode: '0755'

  roles:
    - role: <role_name>
      vars:
        <role_name>_work_dir: "{{ test_work_dir }}"
        <role_name>_debug_mode: true

  post_tasks:
    - name: Verify role execution
      ansible.builtin.assert:
        that:
          - <role_name>_execution_status == "success"
        fail_msg: "Role execution failed"
        success_msg: "Role executed successfully"

    - name: Cleanup test environment
      ansible.builtin.file:
        path: "{{ test_work_dir }}"
        state: absent
```

---

## Documentation Requirements

### README.md Sections (Required)

1. **Title and Description**
2. **Requirements** (Ansible version, collections, Python deps)
3. **Role Variables** (defaults and vars)
4. **Dependencies** (other roles)
5. **Example Playbook**
6. **Tags** (available tags)
7. **Return Values/Facts**
8. **Troubleshooting**
9. **License**
10. **Author Information**

### meta/main.yml Template

```yaml
---
galaxy_info:
  role_name: <role_name>
  namespace: <your_namespace>
  author: Your Name
  description: Brief description
  company: Your Company
  license: Apache-2.0
  
  min_ansible_version: "2.12"
  
  platforms:
    - name: EL
      versions:
        - "8"
        - "9"
    - name: Ubuntu
      versions:
        - focal
        - jammy
  
  galaxy_tags:
    - system
    - automation
    - kubernetes

dependencies: []
  # Example dependency:
  # - role: common
  #   vars:
  #     common_var: value
```

---

## Summary

### Essential Components Checklist

**Every production role should have:**

- [ ] Modular task architecture (orchestrator pattern)
- [ ] Comprehensive error handling (block/rescue/always)
- [ ] Input validation tasks
- [ ] Preflight checks
- [ ] Post-execution verification
- [ ] Proper variable scoping (defaults vs vars)
- [ ] Custom modules (if needed for specific operations)
- [ ] Custom filters (if needed for data transformation)
- [ ] Complete documentation (README, CHANGELOG, INSTALL)
- [ ] Test playbooks
- [ ] Tags for selective execution
- [ ] Idempotent tasks (changed_when/failed_when)
- [ ] Security best practices (no_log for sensitive data)

### Common Standards Across All Roles

1. **Always use FQCN** for modules
2. **Always support check mode** where applicable
3. **Always handle errors** with block/rescue/always
4. **Always validate input** before execution
5. **Always log operations** appropriately
6. **Always clean up** temporary resources
7. **Always document** variables and return values
8. **Always test** before production deployment

---

**Document Owner:** Platform Engineering Team  
**Last Updated:** 2024-12-30  
**Next Review:** 2025-03-30
