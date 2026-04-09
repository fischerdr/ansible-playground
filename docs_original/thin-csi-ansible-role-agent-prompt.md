# Agent Prompt: Thin-CSI Ansible Role Creation

**Purpose:** This document is a prompt to feed to an AI agent to generate an Ansible role that implements the thin-csi storage standards for Hydra OpenShift clusters backed by VMware vSphere.

---

## Context

You are generating an Ansible role that automates the end-to-end configuration of thin-csi storage for Hydra OpenShift clusters. The role covers VMware vCenter configuration and OpenShift StorageClass management based on the thin-csi storage standards defined for the Hydra platform.

The three supported use cases are:

| Use Case Identifier | Description |
|---------------------|-------------|
| `LOGMONSHARED` | Monitoring and logging stateful sets |
| `ASTRO` | Astronomer / Airflow stateful sets |
| `CUSTOMER` | Customer-facing stateful sets |

Each use case has its own dedicated DS Cluster, LUN, vCenter tag, storage policy, and OpenShift StorageClass. They are never shared across use cases.

---

## Role Requirements

### Structure

Generate a single Ansible role named `hydra_thin_csi` with the following directory structure:

```
hydra_thin_csi/
├── defaults/
│   └── main.yml
├── tasks/
│   └── main.yml
│   └── verify_vcenter.yml
│   └── tag_lun.yml
│   └── create_storage_policy.yml
│   └── create_storageclass.yml
│   └── summary.yml
├── templates/
│   └── storageclass.yml.j2
├── vars/
│   └── main.yml
├── meta/
│   └── main.yml
└── README.md
```

### Collections Required

The role must use the following Ansible collections:

- `community.vmware` — all vCenter interactions (tags, storage policies, datastore verification)
- `kubernetes.core` — all OpenShift interactions (reading MachineSets, applying StorageClasses)

Include a `requirements.yml` at the role root listing both collections with minimum version constraints.

---

## Input Variables

The role is invoked with a single use case at runtime. All three use cases share the same role — the use case is passed as a variable. The following variables must be defined:

### Required at Runtime

| Variable | Description | Example |
|----------|-------------|---------|
| `thin_csi_usecase` | Use case identifier (uppercase) | `LOGMONSHARED` |
| `openshift_cluster_name` | OpenShift cluster identifier | `cld-elf-d-eusw1c-1-hxfsl` |
| `vcenter_hostname` | vCenter FQDN | `vcenter.example.com` |
| `vcenter_datacenter` | vCenter datacenter name | `DC1` |
| `thin_csi_lun_name` | Full datastore (LUN) name in vCenter | `PHX-E2-SDDC2-DS01-...` |
| `thin_csi_ds_cluster_name` | DS Cluster name in vCenter | `LOGMONSHARED-PHX-E2-SDDC2-DS01-<cluster>` |

### Derived Variables (role computes these internally)

The role must derive the following from `thin_csi_usecase` and `openshift_cluster_name`. Do not require the operator to set these manually:

| Variable | Derived Value |
|----------|---------------|
| `thin_csi_tag_name` | `hydra-{{ thin_csi_usecase \| lower }}-{{ openshift_cluster_name }}` |
| `thin_csi_policy_name` | `hydra-{{ thin_csi_usecase \| lower }}-{{ openshift_cluster_name }}` |
| `thin_csi_storageclass_name` | `hydra-{{ thin_csi_usecase \| lower }}-thin-csi` |

### Credential Variables (sourced from HashiCorp Vault)

Credentials must never be defined in vars files or passed as plaintext. The role must retrieve them from HashiCorp Vault using the `community.hashi_vault.hashi_vault` lookup. The following secrets are required:

| Variable | Vault Path (example) |
|----------|----------------------|
| `vcenter_username` | `secret/hydra/vcenter/username` |
| `vcenter_password` | `secret/hydra/vcenter/password` |
| `ocp_api_token` | `secret/hydra/openshift/api_token` |
| `ocp_api_url` | `secret/hydra/openshift/api_url` |

Include a comment block in `defaults/main.yml` documenting the expected Vault paths and that these must be configured per environment before running the role.

---

## Task Breakdown

### Task 1 — Verify vCenter DS Cluster and LUN Visibility (`verify_vcenter.yml`)

This is the first task block and must pass completely before any configuration tasks run. If any check fails, the role must **fail immediately and halt the play** with a clear error message identifying exactly what failed and on which host.

The verification must:

1. **Read OpenShift MachineSets** using `kubernetes.core.k8s_info` to extract all unique ESXi host cluster names referenced across all MachineSets in the OpenShift cluster. The role must handle both:
   - Single ESXi host cluster (all MachineSets reference the same cluster)
   - Multiple ESXi host clusters (large installs where MachineSets span more than one ESXi cluster)

2. **Verify the DS Cluster exists** in vCenter using `community.vmware.vmware_datastore_cluster_info` and confirm it matches the expected name derived from the naming standard.

3. **Verify the target LUN is present** in the DS Cluster using `community.vmware.vmware_datastore_info`.

4. **Verify LUN visibility across all ESXi host clusters** identified from the MachineSet read. For each ESXi host cluster, confirm the LUN is accessible. This must work correctly whether there is one ESXi host cluster or multiple.

5. **Verify Storage DRS is disabled** on the DS Cluster. Fail if it is enabled.

Fail conditions (halt immediately with descriptive message):
- DS Cluster not found in vCenter
- LUN not found in the DS Cluster
- LUN not visible to one or more ESXi host clusters identified from MachineSets
- Storage DRS is enabled on the DS Cluster

---

### Task 2 — Apply vCenter Tag to LUN (`tag_lun.yml`)

1. Ensure the tag category exists in vCenter using `community.vmware.vmware_tag_manager`. Create it if absent.
2. Ensure the tag `hydra-{{ thin_csi_usecase | lower }}-{{ openshift_cluster_name }}` exists in vCenter using `community.vmware.vmware_tag`. Create it if absent.
3. Apply the tag to the target LUN datastore using `community.vmware.vmware_tag_manager`. This task must be idempotent — if the tag is already applied, skip without error.
4. Register the result and record whether the tag was created, already existed, or was applied for the summary output.

---

### Task 3 — Create vCenter Storage Policy (`create_storage_policy.yml`)

1. Check whether a storage policy named `hydra-{{ thin_csi_usecase | lower }}-{{ openshift_cluster_name }}` already exists in vCenter using `community.vmware.vmware_vm_storage_policy_info`.
2. If it does not exist, create it using `community.vmware.vmware_vm_storage_policy` and associate it with the tag created in Task 2.
3. If it already exists, verify it is associated with the correct tag. If the association has drifted, fail with a descriptive message — do not silently overwrite an existing policy association.
4. Register the result for the summary output.

---

### Task 4 — Create or Update OpenShift StorageClass (`create_storageclass.yml`)

Use the `kubernetes.core.k8s` module with the `kubeconfig` or bearer token from Vault.

1. Render the StorageClass manifest from the Jinja2 template `storageclass.yml.j2`.
2. Check whether the StorageClass `hydra-{{ thin_csi_usecase | lower }}-thin-csi` already exists using `kubernetes.core.k8s_info`.
3. **If it does not exist:** apply the rendered manifest.
4. **If it exists and matches the desired state:** skip with a log message confirming it is already correct.
5. **If it exists but has drifted** (e.g. `StoragePolicyName` does not match the expected value): apply the updated manifest and log that a drift correction was made.
6. Register the result (created / already correct / drift corrected) for the summary output.

#### StorageClass Template (`storageclass.yml.j2`)

The template must produce the following manifest:

```yaml
allowVolumeExpansion: true
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  annotations:
    storageclass.kubernetes.io/is-default-class: "false"
  name: hydra-{{ thin_csi_usecase | lower }}-thin-csi
parameters:
  StoragePolicyName: hydra-{{ thin_csi_usecase | lower }}-{{ openshift_cluster_name }}
provisioner: csi.vsphere.vmware.com
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
```

---

### Task 5 — Summary Output (`summary.yml`)

At the end of a successful run, the role must print a structured summary using `ansible.builtin.debug`. The summary must cover all four areas:

```
=============================================
 Hydra Thin-CSI Role — Run Summary
=============================================
Use Case        : {{ thin_csi_usecase }}
OpenShift Cluster: {{ openshift_cluster_name }}

[ vCenter Verification ]
  DS Cluster      : {{ thin_csi_ds_cluster_name }} — VERIFIED
  LUN             : {{ thin_csi_lun_name }} — VERIFIED
  Storage DRS     : DISABLED (pass)
  ESXi Host Clusters checked: {{ esxi_host_clusters | join(', ') }}
  LUN visibility  : VERIFIED across all ESXi host clusters

[ vCenter Tags ]
  Tag             : {{ thin_csi_tag_name }} — {{ tag_result }}

[ vCenter Storage Policy ]
  Policy          : {{ thin_csi_policy_name }} — {{ policy_result }}

[ OpenShift StorageClass ]
  StorageClass    : {{ thin_csi_storageclass_name }} — {{ storageclass_result }}
=============================================
```

Where result values are one of: `CREATED`, `ALREADY CORRECT`, `DRIFT CORRECTED`.

---

## Idempotency Requirements

The role must be fully idempotent. Running the role multiple times against the same environment must produce no unintended changes. Specifically:

- Tags already applied to the LUN must not be re-applied
- Storage policies that already exist with the correct tag association must not be recreated
- StorageClasses that already match the desired state must not be modified
- Only genuine drift (mismatched `StoragePolicyName`) should trigger an update to an existing StorageClass

---

## Error Handling Requirements

- All failures must use `ansible.builtin.fail` with a `msg` that clearly states what failed, the variable values involved, and what the operator should check to resolve the issue
- Vault lookup failures must produce a descriptive error indicating which secret path could not be retrieved
- The role must never silently continue past a failed verification

---

## README Requirements

Generate a `README.md` for the role that includes:

- Role description and purpose
- Requirements (collections, Vault configuration)
- All input variables with descriptions, whether required or optional, and example values
- Example playbook showing how to invoke the role for each use case
- Notes on the transition period for DS Cluster naming (storage team alignment pending)
- Limitations (no RWX support, existing PVCs cannot change StorageClass in-place)

---

## Naming Standards Reference

All names generated by this role must comply with the following conventions defined in the thin-csi storage standards document:

| Object | Convention |
|--------|------------|
| DS Cluster | `<USECASE>-<DATASTORAGECLUSTERNAME>-<OPENSHIFT-CLUSTER-NAME>` |
| vCenter Tag | `hydra-<usecase>-<openshift-cluster-name>` |
| Storage Policy | `hydra-<usecase>-<openshift-cluster-name>` |
| OpenShift StorageClass | `hydra-<usecase>-thin-csi` |
| StoragePolicyName (SC param) | `hydra-<usecase>-<openshift-cluster-name>` |

Where `<usecase>` is always lowercase in generated names (e.g. `logmonshared`, `astro`, `customer`).

---

## Example Invocation

The agent must include an example playbook in the README demonstrating how to call the role for each use case:

```yaml
- name: Configure thin-csi storage for LOGMONSHARED
  hosts: localhost
  roles:
    - role: hydra_thin_csi
      vars:
        thin_csi_usecase: LOGMONSHARED
        openshift_cluster_name: "{{ lookup('env', 'OCP_CLUSTER_NAME') }}"
        vcenter_hostname: "vcenter.example.com"
        vcenter_datacenter: "DC1"
        thin_csi_lun_name: "PHX-E2-SDDC2-DS01-LOGMONSHARED-LUN001"
        thin_csi_ds_cluster_name: "LOGMONSHARED-PHX-E2-SDDC2-DS01-{{ openshift_cluster_name }}"
```
