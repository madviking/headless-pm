#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Dashboard Comprehensive Testing${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Create test results directory
mkdir -p tests/test-results
mkdir -p tests/screenshots

# Check if server is running
echo -e "${YELLOW}Checking if dashboard is running on port 3001...${NC}"
if ! curl -s http://localhost:3001 > /dev/null; then
    echo -e "${RED}Dashboard is not running on port 3001!${NC}"
    echo -e "${YELLOW}Please start the dashboard with: npm run dev${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Dashboard is running${NC}"
echo ""

# Run comprehensive issue detection
echo -e "${BLUE}1. Running comprehensive issue detection tests...${NC}"
npm run test -- tests/comprehensive-issue-detection.spec.ts --reporter=list || true
echo ""

# Run API integration tests
echo -e "${BLUE}2. Running API integration tests...${NC}"
npm run test -- tests/api-integration-test.spec.ts --reporter=list || true
echo ""

# Run component-level tests
echo -e "${BLUE}3. Running component-level issue tests...${NC}"
npm run test -- tests/component-issues-test.spec.ts --reporter=list || true
echo ""

# Generate HTML report
echo -e "${BLUE}4. Generating HTML report...${NC}"
npx playwright show-report || true

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Testing Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${YELLOW}Check the following for results:${NC}"
echo -e "  - ${BLUE}tests/test-results/${NC} - Screenshots and test artifacts"
echo -e "  - ${BLUE}tests/test-results/comprehensive-test-report.json${NC} - Detailed JSON report"
echo -e "  - ${BLUE}playwright-report/index.html${NC} - HTML test report"
echo ""
echo -e "${YELLOW}To view the HTML report, run:${NC}"
echo -e "  ${GREEN}npx playwright show-report${NC}"