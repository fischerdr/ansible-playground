#!/usr/bin/env bash
# migrate_docs.sh
# Migrates docs_original/ into the new docs/ structure created from the reorganization tarball.
# Run from the repo root after extracting the reorganization tarball.
#
# Pre-conditions:
#   - docs_original/   exists (your original docs/ renamed before extraction)
#   - docs/            exists (new structure from tarball)
#   - .agents/         exists (from tarball)
#   - CLAUDE.md        exists (from tarball, replaced)
#
# What this script does:
#   1. Copies untouched subtrees from docs_original/ into docs/
#   2. Removes .cursor/ directory
#   3. Removes .github/copilot-instructions.md
#   4. Removes docs_original/ after successful migration

set -euo pipefail

ORIG="docs_original"
NEW="docs"

# ── Preflight ────────────────────────────────────────────────────────────────

echo "==> Checking pre-conditions..."

if [[ ! -d "${ORIG}" ]]; then
    echo "ERROR: ${ORIG}/ not found. Run from repo root with docs_original/ present."
    exit 1
fi

if [[ ! -d "${NEW}" ]]; then
    echo "ERROR: ${NEW}/ not found. Extract the reorganization tarball first."
    exit 1
fi

if [[ ! -f "CLAUDE.md" ]]; then
    echo "ERROR: CLAUDE.md not found at repo root."
    exit 1
fi

if [[ ! -d ".agents" ]]; then
    echo "ERROR: .agents/ not found at repo root."
    exit 1
fi

echo "    Pre-conditions OK"

# ── Copy untouched subtrees from docs_original/ ──────────────────────────────

echo ""
echo "==> Copying untouched subtrees from ${ORIG}/..."

SUBTREES=(
    "examples"
    "must-gather-log"
    "portworx-pxbackup"
    "portworx_upgrade"
)

for subtree in "${SUBTREES[@]}"; do
    src="${ORIG}/${subtree}"
    dst="${NEW}/${subtree}"
    if [[ -d "${src}" ]]; then
        cp -r "${src}" "${dst}"
        echo "    Copied: ${src} -> ${dst}"
    else
        echo "    WARN: ${src} not found in ${ORIG}/, skipping"
    fi
done

# ── Remove .cursor/ ───────────────────────────────────────────────────────────

echo ""
echo "==> Removing .cursor/..."

if [[ -d ".cursor" ]]; then
    rm -rf .cursor
    echo "    Removed: .cursor/"
else
    echo "    .cursor/ not found, skipping"
fi

# ── Remove copilot-instructions.md ───────────────────────────────────────────

echo ""
echo "==> Removing .github/copilot-instructions.md..."

COPILOT=".github/copilot-instructions.md"
if [[ -f "${COPILOT}" ]]; then
    rm "${COPILOT}"
    echo "    Removed: ${COPILOT}"
else
    echo "    ${COPILOT} not found, skipping"
fi

# ── Verify final docs/ structure ─────────────────────────────────────────────

echo ""
echo "==> Verifying final docs/ structure..."

EXPECTED=(
    "docs/.agents/skills/ansible/SKILL.md"
    "docs/archive"
    "docs/examples"
    "docs/execution-environment.md"
    "docs/must-gather-log"
    "docs/portworx-pxbackup"
    "docs/portworx_upgrade"
    "docs/project_organization.md"
    "docs/roles/must_gather_log/redhat_upload_logic_flow.md"
    "docs/roles/pxbackup/backup_schedule_playbooks.md"
    "docs/roles/setup_env/setup_env_integration_guide.md"
    "docs/roles/setup_env/setup_env_extra_clusters_enhancement.md"
    "docs/roles/vault_multi_namespace_monitor/Vault_Monitor_ROLE_DOCUMENTATION.md"
)

MISSING=0
for path in "${EXPECTED[@]}"; do
    if [[ ! -e "${path}" ]]; then
        echo "    MISSING: ${path}"
        MISSING=$((MISSING + 1))
    fi
done

if [[ ${MISSING} -gt 0 ]]; then
    echo ""
    echo "ERROR: ${MISSING} expected path(s) missing. Review above before removing ${ORIG}/."
    exit 1
fi

echo "    All expected paths present"

# ── Remove docs_original/ ─────────────────────────────────────────────────────

echo ""
echo "==> Removing ${ORIG}/..."
rm -rf "${ORIG}"
echo "    Removed: ${ORIG}/"

# ── Done ─────────────────────────────────────────────────────────────────────

echo ""
echo "==> Migration complete. Final structure:"
echo ""
find docs/ .agents/ -type f | sort
echo ""
echo "Done."
