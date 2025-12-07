#!/bin/bash
#
# Utility script to check for uncommitted changes
# Usage: ./check-uncommitted-changes.sh
# Exit code: 0 if no uncommitted changes, 1 if uncommitted changes detected
#

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "Checking for uncommitted changes..."

# Check for modified or staged files
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo -e "${RED}✗ Uncommitted changes detected!${NC}"
    echo ""
    echo "Modified files:"
    git status --short
    echo ""
    echo "Please commit or stash your changes before proceeding."
    exit 1
fi

# Check for untracked files
UNTRACKED=$(git ls-files --others --exclude-standard)
if [ -n "$UNTRACKED" ]; then
    echo -e "${YELLOW}⚠ Untracked files detected:${NC}"
    echo "$UNTRACKED" | sed 's/^/  /'
    echo ""
    echo "Consider adding these files to .gitignore or staging them."
    exit 1
fi

# All good
echo -e "${GREEN}✓ Working directory is clean${NC}"
exit 0
