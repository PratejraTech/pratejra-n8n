#!/bin/bash
# Purpose: Test suite for PRD creation and validation
# Created/Updated: 2025-11-19 19:57:09
# Agent: Init Agent

set -e

TEST_COUNT=0
PASS_COUNT=0
FAIL_COUNT=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_check() {
    TEST_COUNT=$((TEST_COUNT + 1))
    if [ "$1" -eq 0 ]; then
        echo -e "${GREEN}✓ Test $TEST_COUNT: PASSED${NC} - $2"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "${RED}✗ Test $TEST_COUNT: FAILED${NC} - $2"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

echo "=========================================="
echo "PRD Test Suite"
echo "=========================================="
echo ""

# Phase 1 Tests: Directory Structure
echo "Phase 1: Testing Directory Structure"
echo "-----------------------------------"

test_check $([ -d ".cursor/docs" ] && echo 0 || echo 1) "Directory .cursor/docs exists"
test_check $([ -d ".agents" ] && echo 0 || echo 1) "Directory .agents exists"
test_check $([ -d ".agents/contexts" ] && echo 0 || echo 1) "Directory .agents/contexts exists"
test_check $([ -d ".agents/logs" ] && echo 0 || echo 1) "Directory .agents/logs exists"
test_check $([ -d ".agents/prd_steps" ] && echo 0 || echo 1) "Directory .agents/prd_steps exists"
test_check $([ -f ".agents/prd_steps/phase1-directory-structure.md" ] && echo 0 || echo 1) "Phase 1 step file exists"

echo ""

# Phase 2 Tests: PRD File
if [ -f ".cursor/docs/PRD.md" ]; then
    echo "Phase 2: Testing PRD File"
    echo "-------------------------"
    
    test_check $(grep -q "# Product Requirements Document" ".cursor/docs/PRD.md" && echo 0 || echo 1) "PRD has main title"
    test_check $(grep -q "## Executive Summary" ".cursor/docs/PRD.md" && echo 0 || echo 1) "PRD has Executive Summary section"
    test_check $(grep -q "## Platform Architecture" ".cursor/docs/PRD.md" && echo 0 || echo 1) "PRD has Platform Architecture section"
    test_check $(grep -q "## Workflow System" ".cursor/docs/PRD.md" && echo 0 || echo 1) "PRD has Workflow System section"
    test_check $(grep -q "## Agent System" ".cursor/docs/PRD.md" && echo 0 || echo 1) "PRD has Agent System section"
    test_check $(grep -q "## Data Management" ".cursor/docs/PRD.md" && echo 0 || echo 1) "PRD has Data Management section"
    test_check $(grep -q "## Configuration Management" ".cursor/docs/PRD.md" && echo 0 || echo 1) "PRD has Configuration Management section"
    test_check $(grep -q "## Error Handling & Operations" ".cursor/docs/PRD.md" && echo 0 || echo 1) "PRD has Error Handling section"
    test_check $(grep -q "## Development Workflow" ".cursor/docs/PRD.md" && echo 0 || echo 1) "PRD has Development Workflow section"
    test_check $(grep -q "## Change Management Process" ".cursor/docs/PRD.md" && echo 0 || echo 1) "PRD has Change Management Process section"
    test_check $(grep -q "## Future Roadmap" ".cursor/docs/PRD.md" && echo 0 || echo 1) "PRD has Future Roadmap section"
    
    # Check PRD file size (should be substantial)
    PRD_SIZE=$(wc -c < ".cursor/docs/PRD.md")
    test_check $([ "$PRD_SIZE" -gt 5000 ] && echo 0 || echo 1) "PRD file has substantial content (>5KB)"
    
    echo ""
fi

# Phase 3 Tests: Change Management
if [ -f ".agents/PRD.md" ]; then
    echo "Phase 3: Testing Change Management"
    echo "----------------------------------"
    
    test_check $(grep -q "# PRD Change Log" ".agents/PRD.md" && echo 0 || echo 1) "Change log has main title"
    test_check $(grep -q "## Change Log Structure" ".agents/PRD.md" && echo 0 || echo 1) "Change log has structure section"
    test_check $(grep -qE "Timestamp|Agent|Region|Change Description" ".agents/PRD.md" && echo 0 || echo 1) "Change log has required fields"
    
    echo ""
fi

# Phase 4 Tests: Step Files
echo "Phase 4: Testing Step Files"
echo "----------------------------"

if [ -f ".agents/prd_steps/phase1-directory-structure.md" ]; then
    test_check $(grep -q "Phase 1" ".agents/prd_steps/phase1-directory-structure.md" && echo 0 || echo 1) "Phase 1 step file has phase identifier"
    test_check $(grep -q "System State" ".agents/prd_steps/phase1-directory-structure.md" && echo 0 || echo 1) "Phase 1 step file documents system state"
fi

if [ -f ".agents/prd_steps/phase2-prd-creation.md" ]; then
    test_check $(grep -q "Phase 2" ".agents/prd_steps/phase2-prd-creation.md" && echo 0 || echo 1) "Phase 2 step file exists and has phase identifier"
fi

if [ -f ".agents/prd_steps/phase3-change-management.md" ]; then
    test_check $(grep -q "Phase 3" ".agents/prd_steps/phase3-change-management.md" && echo 0 || echo 1) "Phase 3 step file exists and has phase identifier"
fi

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Total Tests: $TEST_COUNT"
echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "${RED}Failed: $FAIL_COUNT${NC}"
    exit 1
else
    echo -e "${GREEN}Failed: $FAIL_COUNT${NC}"
    exit 0
fi

