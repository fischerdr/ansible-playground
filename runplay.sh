ansible-playbook k8s_vault_sa_setup.yml \
  -e cluster_name=your-cluster-name \
  -e vault_token=your-vault-token \
  -e vault_namespace=your-vault-namespace \
  -e k8s_namespace=your-k8s-namespace