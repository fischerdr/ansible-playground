 tree -a --gitignore --prune --dirsfirst -n -I .git
.
├── aap_import
│   ├── portworx_upgrade
│   │   ├── execution_environment.json
│   │   ├── import_to_aap.sh
│   │   ├── job_template_portworx_preflight.json
│   │   ├── job_template_portworx_upgrade_impatient.json
│   │   ├── job_template_portworx_upgrade.json
│   │   ├── project_portworx_upgrade.json
│   │   ├── README.md
│   │   └── workflow_template_portworx_upgrade.json
│   └── README.md
├── Build-EE
│   ├── ansible-aio-ee-airgapped
│   │   ├── ansible-aio-ee-airgapped.yml
│   │   ├── ansible-aio-ee.yml
│   │   ├── ansible-minimal-ee.yml
│   │   ├── build-airgapped-ee.sh
│   │   ├── prepare-airgapped-build.sh
│   │   ├── requirements-collections.txt
│   │   ├── requirements-minimal.yml
│   │   ├── requirements.txt
│   │   ├── requirements.yml
│   │   ├── validate-aap-compatibility.yml
│   │   └── validate-ee-min-compat.yml
│   ├── ansible-aio-ee-docs
│   │   ├── AAP-INTEGRATION-GUIDE.md
│   │   ├── AIRGAPPED-BUILD-INSTRUCTIONS.md
│   │   ├── airgapped_execution_environment_integration.md
│   │   ├── dependency_management.md
│   │   ├── DIRECTORY-USAGE-GUIDE.md
│   │   ├── EE-CAPABILITIES-SUMMARY.md
│   │   ├── execution_environment_integration.md
│   │   ├── INTEGRATION-SUMMARY.md
│   │   ├── README-airgapped-ee.md
│   │   ├── README-ansible-aio-ee.md
│   │   └── VAULT-CLI-ADDITION-SUMMARY.md
│   ├── execution-environment-orig.yml
│   ├── execution-environment.yml
│   ├── update_collection_requirements.py
│   └── update_requirements.sh
├── .cursor
│   └── rules
│       ├── ansible.mdc
│       ├── ansible-project.mdc
│       ├── ansible-update-claude.mdc
│       ├── ansible-update-gpt.mdc
│       ├── bash.mdc
│       ├── black.mdc
│       ├── click.mdc
│       ├── docker.mdc
│       ├── flake8.mdc
│       ├── github-actions.mdc
│       ├── git.mdc
│       ├── isort.mdc
│       ├── mkdocs.mdc
│       ├── mypy.mdc
│       ├── project.mdc
│       ├── pylint.mdc
│       ├── python.mdc
│       ├── rich.mdc
│       └── setuptools.mdc
├── docs
│   ├── Ansible_Standards_Documentation
│   │   ├── AGENTS.md
│   │   ├── ANSIBLE-DEVELOPMENT-STANDARDS.md
│   │   ├── Ansible_Tags_Usage_Guide.md
│   │   ├── CLAUDE.md
│   │   ├── CODE-REVIEW-CHECKLIST.md
│   │   ├── COMPREHENSIVE-GUIDE.md
│   │   ├── DOCUMENTS-CREATED.md
│   │   ├── FINAL-COMPLETION-SUMMARY.md
│   │   ├── KUBERNETES-PATTERNS.md
│   │   ├── MIGRATION-GUIDE.md
│   │   └── PR-TEMPLATE.md
│   ├── examples
│   │   ├── .ansible-lint
│   │   ├── changed_when_failed_when_examples.yml
│   │   ├── custom_module_example.py
│   │   ├── filter_plugin_example.py
│   │   ├── module_testing_example.py
│   │   └── README.md
│   ├── must-gather-log
│   │   ├── must-gather-log-role-3.0.0.tar.gz
│   │   └── TARBALL_README.md
│   ├── portworx-pxbackup
│   │   ├── architecture
│   │   │   ├── components-guide.md
│   │   │   ├── README.md
│   │   │   └── storage-integration.md
│   │   ├── deployment
│   │   │   ├── multi-datacenter.md
│   │   │   └── README.md
│   │   ├── diagrams
│   │   │   └── README.md
│   │   ├── images
│   │   │   ├── pxbackup-architecture.png
│   │   │   ├── pxbackup-architecture.svg
│   │   │   ├── pxbackup-centralized.png
│   │   │   ├── pxbackup-centralized.svg
│   │   │   ├── pxbackup-hub-spoke.png
│   │   │   ├── pxbackup-hub-spoke.svg
│   │   │   ├── pxbackup-multi-tenant.png
│   │   │   └── pxbackup-multi-tenant.svg
│   │   ├── installation
│   │   │   └── deployment-guide.md
│   │   ├── operation
│   │   │   └── README.md
│   │   ├── security
│   │   │   └── README.md
│   │   ├── troubleshooting
│   │   │   ├── common-issues.md
│   │   │   └── troubleshooting-guide.md
│   │   ├── usage
│   │   │   └── user-guide.md
│   │   └── README.md
│   ├── portworx_upgrade
│   │   ├── CONTINUATION_PROMPT.md
│   │   ├── conversation_summary_prompt.md
│   │   ├── DISTRIBUTION-README.md
│   │   ├── example-playbook.yml
│   │   ├── LAB_TESTING.md
│   │   ├── monitoring-flow.md
│   │   ├── new_conversation_starter.md
│   │   ├── operator_refactoring_summary.md
│   │   ├── portworx-upgrade-manual-v2.md
│   │   ├── portworx-upgrade-role-1.0.0.tar.gz
│   │   ├── portworx-upgrade-role-1.0.0.tar.gz.sha256
│   │   ├── portworx-upgrade-role-final.md
│   │   ├── QUICKSTART.md
│   │   ├── sequential-operator-upgrade.md
│   │   └── TESTING.md
│   ├── ansible-role-development-pattern.md
│   ├── ANSIBLE-ROLE-DEVELOPMENT-WORKFLOW.md
│   ├── ANSIBLE-ROLE-STANDARDS.md
│   ├── Ansible_Standards_Documentation.zip
│   ├── awxkit_python313_compatibility_fix.md
│   ├── backup_schedule_playbooks.md
│   ├── CLAUDE-ROLE-WORKFLOW.md
│   ├── DEVELOPMENT_STANDARDS.md
│   ├── execution-environment.md
│   ├── Guidelines-vaultandansible-copy.md
│   ├── MARKDOWN_STANDARDS.md
│   ├── project_organization.md
│   ├── redhat_upload_logic_flow.md
│   ├── SecurityGuidelinesvault.md
│   ├── setup_env_extra_clusters_enhancement.md
│   ├── setup_env_integration_guide.md
│   ├── thin-csi-ansible-role-agent-prompt.md
│   ├── Vault_Monitor_ROLE_DOCUMENTATION.md
│   ├── VaultSecurityMigrationGuide.md
│   └── VERIFICATION_CHECKLIST.md
├── .github
│   ├── workflows
│   │   └── tests.yml
│   ├── ansible-code-bot.yml
│   └── copilot-instructions.md
├── inventory
│   ├── group_vars
│   │   ├── combined
│   │   │   ├── combined.yaml
│   │   │   ├── sched_policy_defaults.yaml
│   │   │   └── scheduled_backup.yaml
│   │   └── all.yml
│   ├── hosts.yml
│   └── inventory_vault_monitor.yml
├── .kilo
│   └── plans
│       └── 1775231473685-misty-wizard.md
├── library
│   ├── redhat_upload.py -> ../roles/must_gather_log/library/redhat_upload.py
│   └── test_upload.py -> ../roles/must_gather_log/library/test_upload.py
├── playbooks
│   ├── pxbkup
│   │   ├── pxbkup_create_backupsched.yml
│   │   ├── pxbkup_create_backup.yml
│   │   ├── pxbkup_create_cluster.yml
│   │   ├── pxbkup_create_multiple_backupscheds.yml
│   │   ├── pxbkup_create_sakubeconfig.yml
│   │   ├── pxbkup_list_all_backups.yml
│   │   ├── pxbkup_list_backup_locations.yml
│   │   ├── pxbkup_list_backupsched.yml
│   │   ├── pxbkup_list_cloudcreds.yml
│   │   ├── pxbkup_list_clusters.yml
│   │   ├── pxbkup_list_schedPol.yml
│   │   ├── pxbkup-setupcluster.yml
│   │   └── pxbkup_update_all_schedules.yml
│   ├── tasks
│   │   ├── generate_output.yml
│   │   ├── process_namespace.yml
│   │   └── px_operator_upgrade_step.yml
│   ├── vars
│   │   └── main.yml
│   ├── vault_multi_namespace_monitor
│   │   ├── ansible.cfg
│   │   ├── COMPARISON.md
│   │   ├── inventory.yml
│   │   ├── playbook.yml
│   │   ├── README.md
│   │   ├── requirements.yml
│   │   ├── run_tests.sh
│   │   ├── SUMMARY.md
│   │   ├── test_playbook.yml
│   │   └── vault_test_tasks.yml
│   ├── check_s3_credentials.yml
│   ├── cleanup-test-must-gather-upload.yml
│   ├── debug_info.yml
│   ├── debugvars.yml
│   ├── etcd_db_backup_aap.yml
│   ├── k8s_check_pxs3.yml
│   ├── k8s_nfs_label_sched.yml
│   ├── k8s_nonnfs_label_sched.yml
│   ├── k8s_resource_inventory.yml
│   ├── k8s_show_mixed_pv_type.yml
│   ├── must-gather-ocp-logs.yml
│   ├── ocp_zone_label_updater.yml
│   ├── px_deploy_operator.yml
│   ├── px_update_operator.yml
│   ├── px_upgrade.yml
│   ├── redhat-sftp-token-refresh.yml
│   ├── setup_k8s_environment.yml
│   ├── test_e2e_sftp_token.yml
│   ├── test_env_roles.yml
│   ├── test-must-gather-upload-uri.yml
│   ├── test-must-gather-upload.yml
│   ├── test_portworx_validation.yml
│   ├── test_redhat_upload.yml
│   ├── test_setup_env_extra_clusters.yml
│   ├── test_setup_env.yml
│   ├── test-sso-grant-types.yml
│   ├── test_vault_kv2_access.yml
│   ├── update_px_s3_certs.yml
│   └── vault_kv2_demo.yml
├── roles
│   ├── common
│   │   ├── defaults
│   │   │   └── main.yml
│   │   ├── filter_plugins
│   │   │   └── custom_filters.py
│   │   ├── tasks
│   │   │   ├── create_single_backup_schedule.yml
│   │   │   ├── main.yml
│   │   │   ├── pull_kubeconfig_vault.yml
│   │   │   ├── pxbkup_auth.yml
│   │   │   └── setup_cluster_variables.yml
│   │   └── templates
│   │       └── .gitkeep
│   ├── configure_clusters
│   │   └── tasks
│   │       ├── setup_machinesets_original.yml
│   │       └── setup_machines.yml
│   ├── create_cluster
│   │   └── tasks
│   │       ├── create_cluster_original.yml
│   │       └── create_cluster.yml
│   ├── defrag_etcd_db
│   │   ├── defaults
│   │   │   └── main.yml
│   │   ├── library
│   │   │   ├── defrag_etcd_claude.py
│   │   │   ├── defrag_etcd_k8s.py
│   │   │   ├── defrag_etcd_orig.py
│   │   │   └── defrag_etcd.py
│   │   ├── meta
│   │   │   └── main.yml
│   │   ├── tasks
│   │   │   ├── etcd_status.yml
│   │   │   └── main.yml
│   │   └── README.md
│   ├── hydra_thin_csi
│   │   ├── defaults
│   │   │   └── main.yml
│   │   ├── meta
│   │   │   └── main.yml
│   │   ├── tasks
│   │   │   ├── execute.yml
│   │   │   ├── main.yml
│   │   │   ├── preflight.yml
│   │   │   ├── report.yml
│   │   │   ├── validate.yml
│   │   │   └── verify.yml
│   │   ├── templates
│   │   │   └── storageclass.yml.j2
│   │   ├── vars
│   │   │   └── main.yml
│   │   ├── CHANGELOG.md
│   │   ├── LICENSE
│   │   ├── README.md
│   │   └── requirements.yml
│   ├── must_gather_log
│   │   ├── defaults
│   │   │   └── main.yml
│   │   ├── library
│   │   │   └── redhat_sso_device_auth.py
│   │   ├── meta
│   │   │   └── main.yml
│   │   ├── tasks
│   │   │   ├── check_token_expiry.yml
│   │   │   ├── cleanup.yml
│   │   │   ├── main.yml
│   │   │   ├── must_gather_collection.yml
│   │   │   ├── must_gather_upload_prod.yml
│   │   │   ├── must_gather_upload.yml
│   │   │   ├── redhat_sftp_token_generation.yml
│   │   │   ├── sftp_credential_management.yml
│   │   │   ├── vault_retrieve_sftp_credentials.yml
│   │   │   └── vault_store_sftp_token.yml
│   │   ├── CHANGELOG.md
│   │   ├── group_vars_example.yml
│   │   └── README.md
│   ├── ocp_zone_label_updater
│   │   ├── defaults
│   │   │   └── main.yml
│   │   ├── meta
│   │   │   └── main.yml
│   │   ├── tasks
│   │   │   ├── execute.yml
│   │   │   ├── main.yml
│   │   │   ├── preflight.yml
│   │   │   ├── report.yml
│   │   │   ├── validate.yml
│   │   │   └── verify.yml
│   │   └── vars
│   │       └── main.yml
│   ├── portworx_upgrade
│   │   ├── aap_import
│   │   │   ├── AAP_IMPORT_MAIN.md
│   │   │   ├── execution_environment.json
│   │   │   ├── import_to_aap.sh
│   │   │   ├── job_template_portworx_preflight.json
│   │   │   ├── job_template_portworx_upgrade_impatient.json
│   │   │   ├── job_template_portworx_upgrade.json
│   │   │   ├── project_portworx_upgrade.json
│   │   │   ├── README.md
│   │   │   └── workflow_template_portworx_upgrade.json
│   │   ├── defaults
│   │   │   └── main.yml
│   │   ├── files
│   │   │   └── versions
│   │   │       ├── README.md
│   │   │       └── versions-3.4.0.1
│   │   ├── filter_plugins
│   │   │   ├── operator_version.py
│   │   │   ├── pod_classifier.py
│   │   │   ├── test_pod_classifier.py
│   │   │   └── test_rolling_upgrade_scenario.py
│   │   ├── handlers
│   │   │   └── main.yml
│   │   ├── meta
│   │   │   └── main.yml
│   │   ├── playbooks
│   │   │   └── px_upgrade.yml
│   │   ├── tasks
│   │   │   ├── monitor
│   │   │   │   ├── automatic_rolling_upgrade.yml
│   │   │   │   ├── detect_stuck_upgrade.yml
│   │   │   │   └── main.yml
│   │   │   ├── preflight
│   │   │   │   ├── backup_resources.yml
│   │   │   │   ├── main.yml
│   │   │   │   ├── validate_cluster_status.yml
│   │   │   │   ├── validate_environment.yml
│   │   │   │   ├── validate_nodes.yml
│   │   │   │   ├── validate_pod_distribution.yml
│   │   │   │   ├── validate_pods.yml
│   │   │   │   └── validate_stc_config.yml
│   │   │   ├── report
│   │   │   │   ├── generate_detailed_json.yml
│   │   │   │   ├── generate_summary.yml
│   │   │   │   └── main.yml
│   │   │   ├── upgrade
│   │   │   │   ├── operator
│   │   │   │   │   ├── determine_target.yml
│   │   │   │   │   ├── discover_current_version.yml
│   │   │   │   │   ├── discover_next_candidate.yml
│   │   │   │   │   ├── enforce_manual_mode.yml
│   │   │   │   │   ├── finalize_upgrade.yml
│   │   │   │   │   ├── main.yml
│   │   │   │   │   ├── process_single_step.yml
│   │   │   │   │   ├── sequential_upgrade_loop.yml
│   │   │   │   │   ├── update_version_state.yml
│   │   │   │   │   └── wait_for_csv.yml
│   │   │   │   ├── configmap.yml
│   │   │   │   ├── operator.yml
│   │   │   │   ├── storagecluster.yml
│   │   │   │   └── update_components.yml
│   │   │   ├── validate
│   │   │   │   ├── cluster_health.yml
│   │   │   │   ├── final_pod_validation.yml
│   │   │   │   ├── main.yml
│   │   │   │   ├── node_statistics.yml
│   │   │   │   ├── stc_conditions.yml
│   │   │   │   ├── storage_pool_health.yml
│   │   │   │   ├── version_consistency.yml
│   │   │   │   └── volume_health.yml
│   │   │   └── main.yml
│   │   ├── templates
│   │   │   └── upgrade_summary.j2
│   │   ├── tests
│   │   │   ├── integration
│   │   │   │   ├── run_tests.yml
│   │   │   │   ├── run_validation_tests.sh
│   │   │   │   ├── test_jinja2_standalone.py
│   │   │   │   ├── test_jinja2_template.yml
│   │   │   │   ├── test_logic_standalone.py
│   │   │   │   ├── test_post_step_validation.py
│   │   │   │   ├── test_sequential_upgrade.yml
│   │   │   │   ├── test_subscription_discovery.py
│   │   │   │   ├── test_validation_nodes_simple.yml
│   │   │   │   ├── test_validation_nodes.yml
│   │   │   │   ├── test_validation_nodes.yml.broken
│   │   │   │   ├── test_validation_stc_conditions.yml
│   │   │   │   ├── test_validation_storage_pools.yml
│   │   │   │   └── test_validation_volumes.yml
│   │   │   ├── unit
│   │   │   │   └── test_operator_version_filters.py
│   │   │   ├── run_all_tests.sh
│   │   │   ├── test_activity_detection.yml
│   │   │   ├── test_directory_creation.yml
│   │   │   ├── test_global_timeout_sliding_window.yml
│   │   │   ├── test_impatient_mode.yml
│   │   │   ├── test_per_pod_timeout.yml
│   │   │   ├── test_storage_classification.py
│   │   │   ├── test_storage_detection.yml
│   │   │   ├── test_timestamp_debug.yml
│   │   │   ├── test_validate_nodes_debug.yml
│   │   │   └── test_validate_nodes.yml
│   │   ├── vars
│   │   │   └── main.yml
│   │   ├── ansible-lint
│   │   ├── CHANGELOG.md
│   │   ├── .gitignore
│   │   ├── INSTALL.md
│   │   ├── LICENSE
│   │   ├── README.md
│   │   └── requirements.yml
│   ├── pxbackup
│   │   ├── defaults
│   │   │   └── main.yml
│   │   ├── filter_plugins
│   │   │   └── lookup_helpers.py
│   │   ├── meta
│   │   │   └── main.yml
│   │   ├── tasks
│   │   │   ├── auth.yml
│   │   │   ├── cluster_variables.yml
│   │   │   ├── create_sa_kubeconfig.yml
│   │   │   ├── create_update_cluster.yml
│   │   │   ├── main.yml
│   │   │   ├── process_cluster.yml
│   │   │   ├── retrieve_master_kubeconfig.yml
│   │   │   ├── setup_bkup_sched.yml
│   │   │   ├── setup_schedule_policies.yml
│   │   │   └── verify_backup_locations.yml
│   │   └── README.md
│   ├── setup_env
│   │   ├── defaults
│   │   │   └── main.yml
│   │   ├── handlers
│   │   │   └── main.yml
│   │   ├── meta
│   │   │   └── main.yml
│   │   ├── tasks
│   │   │   ├── configure_vault.yml
│   │   │   ├── main.yml
│   │   │   ├── parse_cluster_name.yml
│   │   │   ├── process_extra_clusters.yml
│   │   │   ├── process_single_cluster.yml
│   │   │   ├── retrieve_credentials.yml
│   │   │   ├── test_connection.yml
│   │   │   └── write_credentials.yml
│   │   ├── vars
│   │   │   └── main.yml
│   │   └── README.md
│   ├── test_env_role
│   │   └── tasks
│   │       └── main.yml
│   ├── upgrade_clusters
│   │   ├── defaults
│   │   │   └── main.yml
│   │   └── tasks
│   │       └── etcd_backup_aap.yml
│   ├── vault_fix_portworx
│   │   ├── defaults
│   │   │   └── main.yml
│   │   ├── meta
│   │   │   └── main.yml
│   │   ├── tasks
│   │   │   ├── main.yml
│   │   │   ├── px_vault_ns_setup_aap.yml
│   │   │   ├── px_vault_ns_setup.yml
│   │   │   ├── px_vault_setup_aap.yml
│   │   │   ├── px_vault_setup.yml
│   │   │   ├── vault_login_aap.yml
│   │   │   └── vault_login.yaml
│   │   ├── templates
│   │   │   ├── child-ns-storage-engine-nonprod-policy-template.hcl.j2
│   │   │   ├── child-ns-storage-engine-prod-policy-template.hcl.j2
│   │   │   ├── cluster-policy-template.hcl.j2
│   │   │   ├── role-config.json.j2
│   │   │   ├── storage-child-ns-nonprod-policy-template.hcl.j2
│   │   │   ├── storage-child-ns-prod-policy-template.hcl.j2
│   │   │   └── storage-policy-template.hcl.j2
│   │   └── README.md
│   ├── vault_kv2_demo
│   │   ├── defaults
│   │   │   └── main.yml
│   │   ├── meta
│   │   │   └── main.yml
│   │   ├── tasks
│   │   │   ├── cleanup.yml
│   │   │   ├── main.yml
│   │   │   ├── read_kv2_secrets.yml
│   │   │   ├── setup_k8s_auth.yml
│   │   │   ├── setup_k8s_serviceaccount.yml
│   │   │   ├── setup_kv2_engine.yml
│   │   │   ├── setup_vault_namespace.yml
│   │   │   ├── test_k8s_auth.yml
│   │   │   ├── validate_inputs.yml
│   │   │   └── write_kv2_secrets.yml
│   │   ├── ansible-vault-kv2-demo-role.tar.gz
│   │   ├── PACKAGE-CONTENTS.md
│   │   └── README.md
│   └── vault_multi_namespace_monitor
│       ├── defaults
│       │   └── main.yml
│       ├── handlers
│       │   └── main.yml
│       ├── meta
│       │   └── main.yml
│       ├── tasks
│       │   ├── main.yml
│       │   └── vault_test_tasks.yml
│       ├── vars
│       │   └── main.yml
│       └── README.md
├── scripts
│   ├── utils
│   │   └── convert_svg.sh
│   ├── createansiblerole.sh
│   ├── generateansiblerole.sh
│   ├── role-create-debugetcd.sh
│   ├── test-python-urllib-proxy.py
│   ├── test_redhat_auto_approve.py
│   └── test-redhat-upload.sh
├── ansible.cfg
├── ansible_full.cfg
├── .ansible-lint
├── ansible-navigator.yml
├── ansible-role-example.tar.gz
├── build.sh
├── CLAUDE.md
├── .cursorignore
├── extra_vars_bkuploc.json
├── extra_vars_bkupsched.json
├── extra_vars_clusters.json
├── extra_vars_create_backup.json
├── extra_vars.json
├── extra_vars_s3config.json
├── extra_vars_schedulepolicy.json
├── .flake8
├── .gitignore
├── LICENSE
├── .mypy.ini
├── README.md
├── requirements-collections.txt
├── requirements-dev.txt
├── requirements-setup-env.yml
├── requirements.txt
├── requirements.yml
├── run_container.sh
├── run_vault_monitor.sh
├── SECURITY.md
├── test_all.yml
├── test_dependency_resolution.py
├── tox.ini
└── upgradedoc3.2.1.1.md

121 directories, 456 files
