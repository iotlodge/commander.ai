#!/bin/bash
# Test runner for commander.ai Phase 1 (TAVILYFIX)

set -e

echo "=================================="
echo "TAVILYFIX Phase 1 Test Suite"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest not found. Installing...${NC}"
    uv pip install pytest pytest-asyncio
fi

echo -e "${BLUE}Running Unit Tests...${NC}"
echo "-----------------------------------"

# Run unit tests (fast, no external dependencies)
pytest tests/ \
    -v \
    -m "not integration" \
    --tb=short \
    || true

echo ""
echo -e "${BLUE}Unit Tests Complete${NC}"
echo ""

# Ask if user wants to run integration tests
read -p "Run integration tests? (requires TAVILY_API_KEY, Qdrant, internet) [y/N]: " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BLUE}Running Integration Tests...${NC}"
    echo "-----------------------------------"

    # Check for TAVILY_API_KEY
    if [ -z "$TAVILY_API_KEY" ]; then
        echo -e "${RED}⚠️  TAVILY_API_KEY not set in environment${NC}"
        echo "   Make sure it's in your .env file"
        echo ""
    fi

    # Run integration tests
    pytest tests/integration/ \
        -v \
        -m integration \
        --tb=short \
        || true

    echo ""
    echo -e "${BLUE}Integration Tests Complete${NC}"
fi

echo ""
echo "=================================="
echo -e "${GREEN}✅ Test Run Complete${NC}"
echo "=================================="
echo ""
echo "Next steps:"
echo "  - Review test results above"
echo "  - Fix any failing tests"
echo "  - Run 'pytest tests/ --cov=backend' for coverage report"
echo ""
