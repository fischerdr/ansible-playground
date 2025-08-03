#!/bin/bash
#
# Update Collection Requirements Helper Script
#
# This script provides a convenient way to update collection requirements
# and optionally install all dependencies.
#
# Usage:
#   ./scripts/update_requirements.sh
#   ./scripts/update_requirements.sh --install
#   ./scripts/update_requirements.sh --dry-run

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
DRY_RUN=false
INSTALL_DEPS=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --install)
            INSTALL_DEPS=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--dry-run] [--install] [--verbose] [--help]"
            echo "  --dry-run    Show what would be updated without making changes"
            echo "  --install    Install dependencies after updating requirements"
            echo "  --verbose    Show verbose output"
            echo "  --help       Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}" >&2
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🔄 Updating Ansible Collection Requirements${NC}"
echo "================================================"

# Check if Python script exists
if [[ ! -f "scripts/update_collection_requirements.py" ]]; then
    echo -e "${RED}❌ update_collection_requirements.py script not found${NC}" >&2
    exit 1
fi

# Check if collections directory exists
if [[ ! -d "collections" ]]; then
    echo -e "${RED}❌ Collections directory not found${NC}" >&2
    echo "Make sure you've installed collections with: ansible-galaxy collection install -r requirements.yml"
    exit 1
fi

# Build command
PYTHON_CMD="python scripts/update_collection_requirements.py"
if [[ "$DRY_RUN" == "true" ]]; then
    PYTHON_CMD="$PYTHON_CMD --dry-run"
fi
if [[ "$VERBOSE" == "true" ]]; then
    PYTHON_CMD="$PYTHON_CMD --verbose"
fi

# Run the Python script
echo -e "${YELLOW}🔍 Scanning collection requirements...${NC}"
if ! eval "$PYTHON_CMD"; then
    echo -e "${RED}❌ Failed to update collection requirements${NC}" >&2
    exit 1
fi

# Install dependencies if requested and not in dry-run mode
if [[ "$INSTALL_DEPS" == "true" && "$DRY_RUN" == "false" ]]; then
    echo -e "\n${YELLOW}📦 Installing dependencies...${NC}"
    
    echo -e "${BLUE}Installing main requirements...${NC}"
    if ! pip install -r requirements.txt; then
        echo -e "${RED}❌ Failed to install main requirements${NC}" >&2
        exit 1
    fi
    
    echo -e "${BLUE}Installing collection requirements...${NC}"
    if ! pip install -r requirements-collections.txt; then
        echo -e "${RED}❌ Failed to install collection requirements${NC}" >&2
        exit 1
    fi
    
    echo -e "${GREEN}✅ All dependencies installed successfully${NC}"
fi

echo -e "\n${GREEN}✅ Collection requirements update completed${NC}"

if [[ "$DRY_RUN" == "false" ]]; then
    echo -e "${BLUE}📋 Next steps:${NC}"
    echo "   1. Review the updated requirements-collections.txt file"
    echo "   2. Install dependencies: pip install -r requirements-collections.txt"
    echo "   3. Or use: $0 --install"
fi