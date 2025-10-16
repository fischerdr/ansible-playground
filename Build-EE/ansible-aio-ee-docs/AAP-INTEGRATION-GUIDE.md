# Ansible Automation Platform (AAP) Integration Guide

This guide explains how to use the Ansible All-In-One Execution Environments with Ansible Automation Platform (AAP), including configuration, deployment, and best practices.

## 🎯 **AAP Compatibility Overview**

Both the regular and air-gapped Execution Environments are fully compatible with Ansible Automation Platform:

### **✅ AAP Requirements Met**

- **Ansible Runner**: Included for AAP job execution
- **Base Image**: Red Hat UBI 8 (AAP-supported)
- **Python Version**: 3.11 (latest AAP-supported)
- **Collections**: Comprehensive set for all major platforms
- **Environment**: Properly configured for AAP execution context

### **🚀 Supported Playbook Types**

- Cloud automation (AWS, GCP, Azure)
- Kubernetes/OpenShift operations
- Infrastructure as Code (Terraform)
- Network configuration
- System administration
- Security operations (including HashiCorp Vault)
- Container management

## 📦 **EE Deployment to AAP**

### **Method 1: Private Automation Hub**

```bash
# Build and tag for your Private Automation Hub
cd ansible-aio-ee/
./build-ansible-aio-ee.sh -t v1.0.0 -p -r your-hub.company.com/ansible-aio-ee

# For air-gapped environments
cd ansible-aio-ee-airgapped/
./build-airgapped-ee.sh -t v1.0.0 -p -r your-hub.company.com/ansible-aio-ee-airgapped
```

### **Method 2: External Registry**

```bash
# Push to external registry (Quay.io, Docker Hub, etc.)
./build-ansible-aio-ee.sh -p -r quay.io/your-org/ansible-aio-ee:v1.0.0
```

### **Method 3: Direct Import**

```bash
# Save as tar file for manual import
docker save ansible-aio-ee:latest > ansible-aio-ee-v1.0.0.tar
# Transfer and load in AAP environment
docker load < ansible-aio-ee-v1.0.0.tar
```

## 🔧 **AAP Configuration**

### **1. Execution Environment Setup in AAP**

#### **Via AAP Web UI:**

1. Navigate to **Administration** → **Execution Environments**
2. Click **Add**
3. Fill in the details:
   - **Name**: `Ansible AIO EE`
   - **Image**: `your-registry/ansible-aio-ee:v1.0.0`
   - **Description**: `Comprehensive EE with cloud tools and collections`
   - **Organization**: Select your organization
   - **Registry Credential**: If using private registry

#### **Via AAP API:**

```bash
curl -X POST https://your-aap-controller/api/v2/execution_environments/ \
  -H "Authorization: Bearer $AAP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ansible AIO EE",
    "image": "your-registry/ansible-aio-ee:v1.0.0",
    "description": "Comprehensive EE with cloud tools and collections",
    "organization": 1
  }'
```

### **2. Project Configuration**

#### **Set Default EE for Project:**

1. Navigate to **Resources** → **Projects**
2. Edit your project
3. Under **Execution Environment**, select `Ansible AIO EE`
4. Save

#### **Job Template Configuration:**

1. Navigate to **Resources** → **Templates**
2. Edit your job template
3. Under **Execution Environment**, select `Ansible AIO EE`
4. Configure additional settings as needed

## 🔐 **Credential Configuration**

### **Cloud Credentials**

#### **AWS Credentials:**

```yaml
# In AAP, create AWS credential type
- Type: Amazon Web Services
- Access Key: your-access-key
- Secret Key: your-secret-key
- STS Token: (if using temporary credentials)
```

#### **Google Cloud Credentials:**

```yaml
# Create Google Compute Engine credential
- Type: Google Compute Engine
- Service Account Email: your-service-account@project.iam.gserviceaccount.com
- RSA Private Key: -----BEGIN PRIVATE KEY-----...
- Project: your-gcp-project-id
```

#### **Kubernetes Credentials:**

```yaml
# Create Kubernetes credential
- Type: OpenShift or Kubernetes API Bearer Token
- OpenShift or Kubernetes API Endpoint: https://your-k8s-api:6443
- API Authentication Bearer Token: your-token
- Certificate Authority Data: (base64 encoded CA cert)
```

### **Vault Integration**

```yaml
# HashiCorp Vault credential
- Type: HashiCorp Vault Secret Lookup
- Server URL: https://your-vault-server:8200
- Token: your-vault-token
- API Version: v2 (for KV v2)
```

## 📋 **Example Playbook Configurations**

### **Cloud Infrastructure Playbook**

```yaml
---
- name: Deploy AWS Infrastructure
  hosts: localhost
  gather_facts: false
  vars:
    aws_region: us-east-1
  
  tasks:
    - name: Create VPC
      amazon.aws.ec2_vpc:
        name: "my-vpc"
        cidr_block: "10.0.0.0/16"
        region: "{{ aws_region }}"
        tags:
          Environment: production
        state: present
      register: vpc_result
    
    - name: Deploy with Terraform
      ansible.builtin.shell:
        cmd: terraform apply -auto-approve
        chdir: /tmp/terraform
      environment:
        AWS_REGION: "{{ aws_region }}"
```

### **Kubernetes Operations Playbook**

```yaml
---
- name: Kubernetes Application Deployment
  hosts: localhost
  gather_facts: false
  
  tasks:
    - name: Create namespace
      kubernetes.core.k8s:
        name: my-app
        api_version: v1
        kind: Namespace
        state: present
    
    - name: Deploy with Helm
      kubernetes.core.helm:
        name: my-release
        chart_ref: stable/nginx-ingress
        release_namespace: my-app
        create_namespace: true
```

### **Multi-Cloud Playbook**

```yaml
---
- name: Multi-Cloud Resource Management
  hosts: localhost
  gather_facts: false
  
  tasks:
    - name: AWS S3 Bucket
      amazon.aws.s3_bucket:
        name: my-multi-cloud-bucket
        state: present
    
    - name: GCP Storage Bucket
      google.cloud.gcp_storage_bucket:
        name: my-gcp-bucket
        project: my-gcp-project
        state: present
    
    - name: Kubernetes Deployment
      kubernetes.core.k8s:
        definition:
          apiVersion: apps/v1
          kind: Deployment
          metadata:
            name: multi-cloud-app
            namespace: default
          spec:
            replicas: 3
            selector:
              matchLabels:
                app: multi-cloud-app
            template:
              metadata:
                labels:
                  app: multi-cloud-app
              spec:
                containers:
                - name: app
                  image: nginx:latest
```

## 🚀 **Performance Optimization for AAP**

### **1. EE Image Optimization**

```yaml
# In your job template, set these environment variables:
ANSIBLE_PIPELINING: true
ANSIBLE_SSH_PIPELINING: true
ANSIBLE_GATHERING: smart
ANSIBLE_FACT_CACHING: memory
```

### **2. Concurrent Job Execution**

```yaml
# AAP Controller settings for better performance
- Max Concurrent Jobs: 20 (adjust based on resources)
- Job Timeout: 3600 (1 hour)
- Instance Groups: Configure for workload distribution
```

### **3. Resource Limits**

```yaml
# Set appropriate resource limits in AAP
Pod Spec:
  resources:
    requests:
      memory: "512Mi"
      cpu: "250m"
    limits:
      memory: "2Gi"
      cpu: "1000m"
```

## 🔍 **Monitoring and Troubleshooting**

### **AAP Job Monitoring**

1. **Job Output**: Monitor real-time execution in AAP UI
2. **Artifacts**: Collect execution artifacts for debugging
3. **Logs**: Review detailed logs in `/logs` directory within EE

### **Common Issues and Solutions**

#### **Collection Import Errors**

```bash
# Verify collections are available
ansible-galaxy collection list

# Install missing collections
ansible-galaxy collection install community.general
```

#### **Tool Not Found Errors**

```bash
# Verify tools are in PATH
which kubectl helm terraform aws gcloud oc

# Check environment variables
echo $PATH
```

#### **Permission Issues**

```bash
# Check user context
whoami
id

# Verify file permissions
ls -la /workspace
```

### **Debug Playbook for EE Validation**

```yaml
---
- name: Validate EE Environment
  hosts: localhost
  gather_facts: true
  
  tasks:
    - name: Check Python version
      ansible.builtin.debug:
        var: ansible_python_version
    
    - name: List available collections
      ansible.builtin.shell:
        cmd: ansible-galaxy collection list
      register: collections_output
    
    - name: Display collections
      ansible.builtin.debug:
        var: collections_output.stdout_lines
    
    - name: Check cloud tools
      ansible.builtin.shell:
        cmd: "{{ item }} --version"
      loop:
        - aws
        - gcloud
        - kubectl
        - helm
        - terraform
        - oc
        - vault
      register: tool_versions
      failed_when: false
    
    - name: Display tool versions
      ansible.builtin.debug:
        msg: "{{ item.cmd }}: {{ item.stdout | default('Not available') }}"
      loop: "{{ tool_versions.results }}"
```

## 📊 **AAP Integration Best Practices**

### **1. EE Management**

- **Version Control**: Tag EE images with semantic versions
- **Testing**: Test EEs thoroughly before production deployment
- **Documentation**: Maintain clear documentation of EE capabilities
- **Updates**: Regular updates for security and feature improvements

### **2. Credential Management**

- **Vault Integration**: Use HashiCorp Vault for secret management
- **Least Privilege**: Grant minimal required permissions
- **Rotation**: Implement credential rotation policies
- **Encryption**: Ensure all credentials are encrypted at rest

### **3. Performance Tuning**

- **Resource Allocation**: Right-size EE containers based on workload
- **Caching**: Implement fact caching for improved performance
- **Parallelization**: Use AAP's concurrent execution capabilities
- **Monitoring**: Implement comprehensive monitoring and alerting

### **4. Security Considerations**

- **Image Scanning**: Regularly scan EE images for vulnerabilities
- **Network Policies**: Implement proper network segmentation
- **RBAC**: Use AAP's role-based access control
- **Audit Logging**: Enable comprehensive audit logging

## 🔄 **Maintenance and Updates**

### **Regular Maintenance Tasks**

1. **Update base images** monthly for security patches
2. **Update collections** quarterly or as needed
3. **Update cloud tools** when new features are required
4. **Review and update credentials** as per security policies

### **Update Process**

```bash
# 1. Build new version
./build-ansible-aio-ee.sh -t v1.1.0

# 2. Test in development environment
# 3. Update AAP EE configuration
# 4. Deploy to production with proper rollback plan
```

## 📈 **Scaling Considerations**

### **For Large Deployments**

- **Multiple EE Variants**: Create specialized EEs for different use cases
- **Registry Management**: Implement proper image registry management
- **Resource Planning**: Plan compute resources based on concurrent job requirements
- **Network Optimization**: Optimize network connectivity for cloud operations

### **Air-gapped Environments**

- **Regular Updates**: Plan for regular offline updates
- **Tool Versioning**: Maintain strict version control for all tools
- **Testing**: Comprehensive testing before deployment
- **Documentation**: Detailed documentation for offline procedures

---

**Note**: This EE is production-ready and designed to handle the vast majority of Ansible automation use cases within AAP. The comprehensive tool set and collections make it suitable for complex, multi-cloud, and hybrid infrastructure scenarios.
