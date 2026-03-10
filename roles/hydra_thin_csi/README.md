# Ansible Role: hydra_thin_csi

## Description

The `hydra_thin_csi` role configures thin-csi storage for Hydra OpenShift clusters backed by VMware vSphere.  
It automates vCenter datastore tagging, storage policy creation, and OpenShift `StorageClass` management for the three supported Hydra thin-csi use cases (`LOGMONSHARED`, `ASTRO`, `CUSTOMER`), ensuring they follow the platform naming and isolation standards.

## Requirements

- Ansible Core: 2.12+ (AAP EE compatible)
- Python: 3.11+
- Collections:
  - `community.vmware` (for vCenter interactions)
  - `kubernetes.core` (for OpenShift API interactions)
  - `community.hashi_vault` (for credential retrieval from HashiCorp Vault)
- Target environment:
  - Hydra OpenShift cluster reachable from the Execution Environment
  - VMware vCenter with appropriate API access
  - HashiCorp Vault configured with the required secrets

## Role Variables

### Required Variables

| Variable                                      | Type   | Description                                                                                          |
|-----------------------------------------------|--------|------------------------------------------------------------------------------------------------------|
| `hydra_thin_csi_usecase`                      | string | Use case identifier (`LOGMONSHARED`, `ASTRO`, or `CUSTOMER`).                                       |
| `hydra_thin_csi_openshift_cluster_name`       | string | OpenShift cluster identifier used in naming (e.g. `cld-elf-d-eusw1c-1-hxfsl`).                      |
| `hydra_thin_csi_vcenter_hostname`             | string | vCenter FQDN.                                                                                        |
| `hydra_thin_csi_vcenter_datacenter`           | string | vCenter datacenter name.                                                                            |
| `hydra_thin_csi_lun_name`                     | string | Full datastore (LUN) name in vCenter.                                                               |
| `hydra_thin_csi_ds_cluster_name`              | string | DS Cluster name in vCenter for this use case and cluster.                                           |

> **Note:** vCenter and OpenShift credentials are retrieved from HashiCorp Vault and must **not** be defined directly as variables.

### Optional Variables

| Variable                                      | Type    | Default | Description                                                                                          |
|-----------------------------------------------|---------|---------|------------------------------------------------------------------------------------------------------|
| `hydra_thin_csi_enable_verification`          | bool    | `true`  | Whether to run post-change verification tasks (if added).                                           |
| `hydra_thin_csi_enable_reporting`             | bool    | `true`  | Whether to emit the structured run summary.                                                         |
| `hydra_thin_csi_report_format`                | string  | `"text"`| Format hint for future extended reporting (reserved; summary is always text debug).                 |

### Derived/Internal Variables

The role computes the following internal variables and they **must not** be overridden:

- `__hydra_thin_csi_tag_name` – `hydra-{{ hydra_thin_csi_usecase | lower }}-{{ hydra_thin_csi_openshift_cluster_name }}`
- `__hydra_thin_csi_policy_name` – `hydra-{{ hydra_thin_csi_usecase | lower }}-{{ hydra_thin_csi_openshift_cluster_name }}`
- `__hydra_thin_csi_storageclass_name` – `hydra-{{ hydra_thin_csi_usecase | lower }}-thin-csi`

### Vault-Backed Credential Variables

The role retrieves credentials using the `community.hashi_vault.hashi_vault` lookup. The actual Vault paths are environment-specific but are expected to follow patterns such as:

- vCenter username – e.g. `secret/hydra/vcenter/username`
- vCenter password – e.g. `secret/hydra/vcenter/password`
- OpenShift API token – e.g. `secret/hydra/openshift/api_token`
- OpenShift API URL – e.g. `secret/hydra/openshift/api_url`

These paths must be configured per environment; see your platform Vault documentation for the authoritative paths.

## Example Playbooks

### LOGMONSHARED

```yaml
---
- name: Configure thin-csi storage for LOGMONSHARED
  hosts: localhost
  gather_facts: false

  roles:
    - role: hydra_thin_csi
      vars:
        hydra_thin_csi_usecase: LOGMONSHARED
        hydra_thin_csi_openshift_cluster_name: "{{ lookup('env', 'OCP_CLUSTER_NAME') }}"
        hydra_thin_csi_vcenter_hostname: "vcenter.example.com"
        hydra_thin_csi_vcenter_datacenter: "DC1"
        hydra_thin_csi_lun_name: "PHX-E2-SDDC2-DS01-LOGMONSHARED-LUN001"
        hydra_thin_csi_ds_cluster_name: "LOGMONSHARED-PHX-E2-SDDC2-DS01-{{ hydra_thin_csi_openshift_cluster_name }}"
```

### ASTRO

```yaml
---
- name: Configure thin-csi storage for ASTRO
  hosts: localhost
  gather_facts: false

  roles:
    - role: hydra_thin_csi
      vars:
        hydra_thin_csi_usecase: ASTRO
        hydra_thin_csi_openshift_cluster_name: "{{ lookup('env', 'OCP_CLUSTER_NAME') }}"
        hydra_thin_csi_vcenter_hostname: "vcenter.example.com"
        hydra_thin_csi_vcenter_datacenter: "DC1"
        hydra_thin_csi_lun_name: "PHX-E2-SDDC2-DS01-ASTRO-LUN001"
        hydra_thin_csi_ds_cluster_name: "ASTRO-PHX-E2-SDDC2-DS01-{{ hydra_thin_csi_openshift_cluster_name }}"
```

### CUSTOMER

```yaml
---
- name: Configure thin-csi storage for CUSTOMER workloads
  hosts: localhost
  gather_facts: false

  roles:
    - role: hydra_thin_csi
      vars:
        hydra_thin_csi_usecase: CUSTOMER
        hydra_thin_csi_openshift_cluster_name: "{{ lookup('env', 'OCP_CLUSTER_NAME') }}"
        hydra_thin_csi_vcenter_hostname: "vcenter.example.com"
        hydra_thin_csi_vcenter_datacenter: "DC1"
        hydra_thin_csi_lun_name: "PHX-E2-SDDC2-DS01-CUSTOMER-LUN001"
        hydra_thin_csi_ds_cluster_name: "CUSTOMER-PHX-E2-SDDC2-DS01-{{ hydra_thin_csi_openshift_cluster_name }}"
```

## Notes and Limitations

- Each use case has a dedicated DS Cluster, LUN, vCenter tag, storage policy, and StorageClass; they are **never** shared across use cases.
- The role is designed for **RWO** thin-csi volumes only; RWX is **not** supported.
- Existing PVCs cannot change `StorageClass` in-place; migration of existing workloads is out of scope.
- DS Cluster naming is subject to storage team standardization; this role assumes DS Cluster names follow the documented Hydra convention.

## License

MIT
