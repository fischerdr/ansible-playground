#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Your Name <your.email@example.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: k8s_resource_manager
short_description: Manage Kubernetes resources with state checking
description:
  - Creates, updates, or deletes Kubernetes resources
  - Implements proper idempotency and check mode support
  - Handles resource existence checking and state management
version_added: "1.0.0"
author:
  - Your Name (@github_handle)
options:
  name:
    description: Name of the Kubernetes resource
    type: str
    required: true
  namespace:
    description: Namespace for the resource
    type: str
    required: true
  resource_type:
    description: Type of Kubernetes resource
    type: str
    required: true
    choices: ['pod', 'service', 'deployment', 'configmap']
  state:
    description: Desired state of the resource
    type: str
    required: false
    default: present
    choices: ['present', 'absent']
  replicas:
    description: Number of replicas (for deployments)
    type: int
    required: false
    default: 1
  image:
    description: Container image (for pods/deployments)
    type: str
    required: false
requirements:
  - python >= 3.11
  - kubernetes >= 12.0.0
notes:
  - This module is designed for AAP execution environments
  - Requires cluster-admin or appropriate RBAC permissions
  - Supports check mode for dry-run testing
seealso:
  - module: kubernetes.core.k8s
  - name: Kubernetes Python Client
    link: https://github.com/kubernetes-client/python
"""

EXAMPLES = r"""
- name: Create a pod
  k8s_resource_manager:
    name: my-pod
    namespace: default
    resource_type: pod
    state: present
    image: nginx:latest

- name: Update deployment with new image
  k8s_resource_manager:
    name: my-deployment
    namespace: production
    resource_type: deployment
    state: present
    replicas: 3
    image: myapp:v2.0

- name: Delete a service
  k8s_resource_manager:
    name: my-service
    namespace: default
    resource_type: service
    state: absent

- name: Check mode - verify what would be created
  k8s_resource_manager:
    name: test-pod
    namespace: default
    resource_type: pod
    state: present
    image: alpine:latest
  check_mode: true

- name: Advanced usage with error handling
  block:
    - name: Create resource with validation
      k8s_resource_manager:
        name: "{{ app_name }}"
        namespace: "{{ app_namespace }}"
        resource_type: deployment
        state: present
        replicas: 5
        image: "{{ app_image }}"
      register: result

    - name: Display result
      debug:
        msg: "Resource {{ result.resource_name }} is {{ result.resource_state }}"

  rescue:
    - name: Handle failure
      debug:
        msg: "Failed to manage resource: {{ result.msg }}"

  always:
    - name: Log operation
      debug:
        msg: "Operation completed at {{ ansible_date_time.iso8601 }}"
"""

RETURN = r"""
changed:
  description: Whether the module made changes
  type: bool
  returned: always
  sample: true
msg:
  description: Human-readable message about what happened
  type: str
  returned: always
  sample: "Successfully created pod my-pod in namespace default"
resource_name:
  description: Name of the resource that was managed
  type: str
  returned: always
  sample: "my-pod"
resource_state:
  description: Current state of the resource
  type: str
  returned: always
  sample: "present"
resource_details:
  description: Detailed resource information from Kubernetes API
  type: dict
  returned: success
  sample:
    apiVersion: "v1"
    kind: "Pod"
    metadata:
      name: "my-pod"
      namespace: "default"
    status:
      phase: "Running"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException

    HAS_KUBERNETES = True
except ImportError:
    HAS_KUBERNETES = False


def manage_k8s_resource(module):  # noqa: C901
    """
    Manage Kubernetes resource lifecycle

    Args:
        module: AnsibleModule instance with parameters

    Returns:
        dict: Result dictionary with changed status and details

    Raises:
        ApiException: If Kubernetes API calls fail
    """
    name = module.params["name"]
    namespace = module.params["namespace"]
    resource_type = module.params["resource_type"]
    state = module.params["state"]
    replicas = module.params.get("replicas", 1)
    image = module.params.get("image")

    result = {
        "changed": False,
        "msg": "",
        "resource_name": name,
        "resource_state": state,
        "resource_details": {},
    }

    try:
        # Load kubeconfig
        config.load_kube_config()
        v1 = client.CoreV1Api()
        apps_v1 = client.AppsV1Api()

        # Check if resource exists
        resource_exists = False
        current_resource = None

        try:
            if resource_type == "pod":
                current_resource = v1.read_namespaced_pod(name, namespace)
                resource_exists = True
            elif resource_type == "service":
                current_resource = v1.read_namespaced_service(name, namespace)
                resource_exists = True
            elif resource_type == "deployment":
                current_resource = apps_v1.read_namespaced_deployment(name, namespace)
                resource_exists = True
            elif resource_type == "configmap":
                current_resource = v1.read_namespaced_config_map(name, namespace)
                resource_exists = True
        except ApiException as e:
            if e.status == 404:
                resource_exists = False
            else:
                raise

        # Handle state: absent
        if state == "absent":
            if resource_exists:
                if module.check_mode:
                    result["changed"] = True
                    result["msg"] = (
                        f"Would delete {resource_type} {name} in namespace {namespace}"
                    )
                    return result

                # Delete the resource
                if resource_type == "pod":
                    v1.delete_namespaced_pod(name, namespace)
                elif resource_type == "service":
                    v1.delete_namespaced_service(name, namespace)
                elif resource_type == "deployment":
                    apps_v1.delete_namespaced_deployment(name, namespace)
                elif resource_type == "configmap":
                    v1.delete_namespaced_config_map(name, namespace)

                result["changed"] = True
                result["msg"] = (
                    f"Deleted {resource_type} {name} from namespace {namespace}"
                )
            else:
                result["changed"] = False
                result["msg"] = (
                    f"{resource_type} {name} does not exist in namespace {namespace}"
                )

            return result

        # Handle state: present
        if state == "present":
            if resource_exists:
                # Check if update is needed
                needs_update = False

                if resource_type == "deployment":
                    current_replicas = current_resource.spec.replicas
                    current_image = current_resource.spec.template.spec.containers[
                        0
                    ].image

                    if replicas != current_replicas:
                        needs_update = True
                    if image and image != current_image:
                        needs_update = True

                if needs_update:
                    if module.check_mode:
                        result["changed"] = True
                        result["msg"] = (
                            f"Would update {resource_type} {name} in namespace {namespace}"
                        )
                        return result

                    # Update the resource
                    if resource_type == "deployment":
                        current_resource.spec.replicas = replicas
                        if image:
                            current_resource.spec.template.spec.containers[0].image = (
                                image
                            )
                        apps_v1.patch_namespaced_deployment(
                            name, namespace, current_resource
                        )

                    result["changed"] = True
                    result["msg"] = (
                        f"Updated {resource_type} {name} in namespace {namespace}"
                    )
                else:
                    result["changed"] = False
                    result["msg"] = (
                        f"{resource_type} {name} already exists and is up to date"
                    )

                # Add resource details
                result["resource_details"] = {
                    "name": current_resource.metadata.name,
                    "namespace": current_resource.metadata.namespace,
                    "created": str(current_resource.metadata.creation_timestamp),
                }

            else:
                # Resource doesn't exist, create it
                if module.check_mode:
                    result["changed"] = True
                    result["msg"] = (
                        f"Would create {resource_type} {name} in namespace {namespace}"
                    )
                    return result

                # Create the resource
                if resource_type == "pod":
                    pod_manifest = client.V1Pod(
                        metadata=client.V1ObjectMeta(name=name, namespace=namespace),
                        spec=client.V1PodSpec(
                            containers=[
                                client.V1Container(
                                    name=name, image=image if image else "nginx:latest"
                                )
                            ]
                        ),
                    )
                    created_resource = v1.create_namespaced_pod(namespace, pod_manifest)

                elif resource_type == "deployment":
                    deployment_manifest = client.V1Deployment(
                        metadata=client.V1ObjectMeta(name=name, namespace=namespace),
                        spec=client.V1DeploymentSpec(
                            replicas=replicas,
                            selector=client.V1LabelSelector(match_labels={"app": name}),
                            template=client.V1PodTemplateSpec(
                                metadata=client.V1ObjectMeta(labels={"app": name}),
                                spec=client.V1PodSpec(
                                    containers=[
                                        client.V1Container(
                                            name=name,
                                            image=image if image else "nginx:latest",
                                        )
                                    ]
                                ),
                            ),
                        ),
                    )
                    created_resource = apps_v1.create_namespaced_deployment(
                        namespace, deployment_manifest
                    )

                result["changed"] = True
                result["msg"] = (
                    f"Created {resource_type} {name} in namespace {namespace}"
                )
                result["resource_details"] = {
                    "name": created_resource.metadata.name,
                    "namespace": created_resource.metadata.namespace,
                    "created": str(created_resource.metadata.creation_timestamp),
                }

        return result

    except ApiException as e:
        module.fail_json(
            msg=f"Kubernetes API error: {str(e)}",
            status=e.status,
            reason=e.reason,
            **result,
        )
    except Exception as e:
        module.fail_json(msg=f"Unexpected error: {str(e)}", **result)


def run_module():
    """Main module execution function"""

    # Define module argument specification
    module_args = dict(
        name=dict(type="str", required=True),
        namespace=dict(type="str", required=True),
        resource_type=dict(
            type="str",
            required=True,
            choices=["pod", "service", "deployment", "configmap"],
        ),
        state=dict(
            type="str", required=False, default="present", choices=["present", "absent"]
        ),
        replicas=dict(type="int", required=False, default=1),
        image=dict(type="str", required=False),
    )

    # Initialize module
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("resource_type", "pod", ["image"]),
            ("resource_type", "deployment", ["image"]),
        ],
    )

    # Check for kubernetes library
    if not HAS_KUBERNETES:
        module.fail_json(
            msg="kubernetes library is required for this module", changed=False
        )

    # Validate parameters
    if not module.params["name"]:
        module.fail_json(msg="name parameter cannot be empty", changed=False)

    if not module.params["namespace"]:
        module.fail_json(msg="namespace parameter cannot be empty", changed=False)

    # Validate replicas range
    if module.params.get("replicas"):
        if not 1 <= module.params["replicas"] <= 100:
            module.fail_json(msg="replicas must be between 1 and 100", changed=False)

    # Execute main logic
    result = manage_k8s_resource(module)

    # Return result
    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
