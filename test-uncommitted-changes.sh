#!/bin/bash
#
# Test script for uncommitted changes detection
# Usage: ./test-uncommitted-changes.sh
#

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Running tests for uncommitted changes detection..."
echo ""

# Test 1: Clean working directory
echo "Test 1: Clean working directory"
if ./check-uncommitted-changes.sh > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}: Clean directory detected correctly"
else
    echo -e "${RED}✗ FAIL${NC}: Clean directory not detected"
    exit 1
fi

# Test 2: Hook is executable
echo ""
echo "Test 2: Pre-commit hook is executable"
if [ -x .githooks/pre-commit ]; then
    echo -e "${GREEN}✓ PASS${NC}: Hook is executable"
else
    echo -e "${RED}✗ FAIL${NC}: Hook is not executable"
    exit 1
fi

# Test 3: Untracked file detection
echo ""
echo "Test 3: Untracked file detection"
echo "test" > test_temp.txt
if ! ./check-uncommitted-changes.sh > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}: Untracked file detected correctly"
    rm -f test_temp.txt
else
    echo -e "${RED}✗ FAIL${NC}: Untracked file not detected"
    rm -f test_temp.txt
    exit 1
fi

# Test 4: Modified file detection
echo ""
echo "Test 4: Modified file detection"
echo "# temporary modification" >> README.md
if ! ./check-uncommitted-changes.sh > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}: Modified file detected correctly"
    git checkout README.md
else
    echo -e "${RED}✗ FAIL${NC}: Modified file not detected"
    git checkout README.md
    exit 1
fi

# Test 5: Check script exists
echo ""
echo "Test 5: Check script exists and is executable"
if [ -x ./check-uncommitted-changes.sh ]; then
    echo -e "${GREEN}✓ PASS${NC}: Check script is executable"
else
    echo -e "${RED}✗ FAIL${NC}: Check script is not executable"
    exit 1
fi

echo ""
echo -e "${GREEN}All tests passed!${NC}"
exit 0
