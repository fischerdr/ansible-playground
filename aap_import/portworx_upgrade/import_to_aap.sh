#!/bin/bash
# Import Portworx Upgrade automation into Ansible Automation Platform
#
# Prerequisites:
#   - awx CLI installed: pip install awxkit
#   - Environment variables set: CONTROLLER_HOST, CONTROLLER_USERNAME, CONTROLLER_PASSWORD
#   - Organization name set: ORG_NAME (default: "Default")
#
# Usage:
#   export CONTROLLER_HOST=https://your-aap-server
#   export CONTROLLER_USERNAME=admin
#   export CONTROLLER_PASSWORD=your-password
#   export ORG_NAME="Default"  # Optional
#   ./import_to_aap.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ORG_NAME="${ORG_NAME:-Default}"
PROJECT_NAME="Portworx Upgrade Automation"
EE_NAME="Portworx Upgrade EE"
INVENTORY_NAME="localhost-inventory"

# Git repository configuration - UPDATE THESE
GIT_URL="${GIT_URL:-https://github.com/your-org/ansible-playground.git}"
GIT_BRANCH="${GIT_BRANCH:-feature/portworx-upgrade}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Portworx Upgrade - AAP Import Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v awx &> /dev/null; then
    echo -e "${RED}ERROR: awx CLI not found. Install with: pip install awxkit${NC}"
    exit 1
fi

if [ -z "$CONTROLLER_HOST" ]; then
    echo -e "${RED}ERROR: CONTROLLER_HOST not set${NC}"
    exit 1
fi

if [ -z "$CONTROLLER_USERNAME" ]; then
    echo -e "${RED}ERROR: CONTROLLER_USERNAME not set${NC}"
    exit 1
fi

if [ -z "$CONTROLLER_PASSWORD" ]; then
    echo -e "${RED}ERROR: CONTROLLER_PASSWORD not set${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Get organization ID
echo -e "${YELLOW}Getting organization ID...${NC}"
ORG_ID=$(awx organizations list --name "$ORG_NAME" -f json | jq -r '.results[0].id')

if [ -z "$ORG_ID" ] || [ "$ORG_ID" == "null" ]; then
    echo -e "${RED}ERROR: Organization '$ORG_NAME' not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Organization: $ORG_NAME (ID: $ORG_ID)${NC}"
echo ""

# Create or update project
echo -e "${YELLOW}Creating project...${NC}"
PROJECT_ID=$(awx projects list --name "$PROJECT_NAME" -f json | jq -r '.results[0].id')

if [ "$PROJECT_ID" == "null" ] || [ -z "$PROJECT_ID" ]; then
    awx projects create \
        --name "$PROJECT_NAME" \
        --description "Ansible project for automated Portworx cluster upgrades" \
        --organization "$ORG_ID" \
        --scm_type git \
        --scm_url "$GIT_URL" \
        --scm_branch "$GIT_BRANCH" \
        --scm_update_on_launch true \
        --scm_clean true

    PROJECT_ID=$(awx projects list --name "$PROJECT_NAME" -f json | jq -r '.results[0].id')
    echo -e "${GREEN}✓ Project created (ID: $PROJECT_ID)${NC}"
else
    echo -e "${YELLOW}Project already exists (ID: $PROJECT_ID)${NC}"
fi

# Update project
echo -e "${YELLOW}Syncing project...${NC}"
awx projects update "$PROJECT_ID" --monitor
echo -e "${GREEN}✓ Project synced${NC}"
echo ""

# Create execution environment
echo -e "${YELLOW}Creating execution environment...${NC}"
EE_ID=$(awx execution_environments list --name "$EE_NAME" -f json | jq -r '.results[0].id')

if [ "$EE_ID" == "null" ] || [ -z "$EE_ID" ]; then
    awx execution_environments create \
        --name "$EE_NAME" \
        --description "Execution environment for Portworx upgrades" \
        --image "quay.io/ansible/awx-ee:latest" \
        --pull missing

    EE_ID=$(awx execution_environments list --name "$EE_NAME" -f json | jq -r '.results[0].id')
    echo -e "${GREEN}✓ Execution environment created (ID: $EE_ID)${NC}"
else
    echo -e "${YELLOW}Execution environment already exists (ID: $EE_ID)${NC}"
fi
echo ""

# Get inventory ID
echo -e "${YELLOW}Getting inventory...${NC}"
INVENTORY_ID=$(awx inventory list --name "$INVENTORY_NAME" -f json | jq -r '.results[0].id')

if [ "$INVENTORY_ID" == "null" ] || [ -z "$INVENTORY_ID" ]; then
    echo -e "${RED}WARNING: Inventory '$INVENTORY_NAME' not found. Creating...${NC}"

    awx inventory create \
        --name "$INVENTORY_NAME" \
        --description "Localhost inventory for Portworx upgrades" \
        --organization "$ORG_ID"

    INVENTORY_ID=$(awx inventory list --name "$INVENTORY_NAME" -f json | jq -r '.results[0].id')

    # Add localhost host
    awx hosts create \
        --name "localhost" \
        --inventory "$INVENTORY_ID" \
        --variables '{"ansible_connection": "local", "ansible_python_interpreter": "/usr/bin/python3"}'

    echo -e "${GREEN}✓ Inventory created (ID: $INVENTORY_ID)${NC}"
else
    echo -e "${GREEN}✓ Inventory found (ID: $INVENTORY_ID)${NC}"
fi
echo ""

# Create job templates
echo -e "${YELLOW}Creating job templates...${NC}"

# 1. Full upgrade template
JT1_NAME="Portworx Cluster Upgrade"
JT1_ID=$(awx job_templates list --name "$JT1_NAME" -f json | jq -r '.results[0].id')

if [ "$JT1_ID" == "null" ] || [ -z "$JT1_ID" ]; then
    awx job_templates create \
        --name "$JT1_NAME" \
        --description "Automated Portworx cluster upgrade with comprehensive validation" \
        --job_type run \
        --inventory "$INVENTORY_ID" \
        --project "$PROJECT_ID" \
        --playbook "playbooks/px_upgrade.yml" \
        --execution_environment "$EE_ID" \
        --ask_variables_on_launch true \
        --ask_tags_on_launch true \
        --verbosity 1

    echo -e "${GREEN}✓ Job template '$JT1_NAME' created${NC}"
else
    echo -e "${YELLOW}Job template '$JT1_NAME' already exists${NC}"
fi

# 2. Preflight check template
JT2_NAME="Portworx Upgrade - Preflight Check"
JT2_ID=$(awx job_templates list --name "$JT2_NAME" -f json | jq -r '.results[0].id')

if [ "$JT2_ID" == "null" ] || [ -z "$JT2_ID" ]; then
    awx job_templates create \
        --name "$JT2_NAME" \
        --description "Preflight validation only - no changes made" \
        --job_type run \
        --inventory "$INVENTORY_ID" \
        --project "$PROJECT_ID" \
        --playbook "playbooks/px_upgrade.yml" \
        --execution_environment "$EE_ID" \
        --job_tags "preflight" \
        --ask_variables_on_launch true \
        --allow_simultaneous true \
        --verbosity 1

    echo -e "${GREEN}✓ Job template '$JT2_NAME' created${NC}"
else
    echo -e "${YELLOW}Job template '$JT2_NAME' already exists${NC}"
fi

# 3. Impatient mode template
JT3_NAME="Portworx Cluster Upgrade - Impatient Mode"
JT3_ID=$(awx job_templates list --name "$JT3_NAME" -f json | jq -r '.results[0].id')

if [ "$JT3_ID" == "null" ] || [ -z "$JT3_ID" ]; then
    awx job_templates create \
        --name "$JT3_NAME" \
        --description "Accelerated upgrade with impatient mode enabled" \
        --job_type run \
        --inventory "$INVENTORY_ID" \
        --project "$PROJECT_ID" \
        --playbook "playbooks/px_upgrade.yml" \
        --execution_environment "$EE_ID" \
        --ask_variables_on_launch true \
        --verbosity 1

    echo -e "${GREEN}✓ Job template '$JT3_NAME' created${NC}"
else
    echo -e "${YELLOW}Job template '$JT3_NAME' already exists${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Import Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Add OpenShift/K8s credentials to job templates"
echo -e "  2. Configure surveys for each job template"
echo -e "  3. Test with preflight check: awx job_templates launch --name '$JT2_NAME' --extra_vars '{\"portworx_target_version\": \"3.5.0\"}'"
echo -e "  4. Create workflow template with approval gates (optional)"
echo ""
echo -e "Job Templates created:"
echo -e "  - $JT1_NAME"
echo -e "  - $JT2_NAME"
echo -e "  - $JT3_NAME"
echo ""
echo -e "View in AAP: ${CONTROLLER_HOST}/#/templates"
echo ""
