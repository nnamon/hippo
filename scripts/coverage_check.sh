#!/bin/bash

# Coverage check script for Hippo bot
# Runs coverage analysis in Docker container

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}📊 Hippo Bot Coverage Analysis${NC}"
    echo "========================================"
}

print_step() {
    echo -e "\n${BLUE}🔄 $1...${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Configuration
MIN_COVERAGE=55
TARGET_COVERAGE=80

print_header

# Build test container if needed
print_step "Checking test container"
if ! docker images | grep -q "hippo-test.*latest"; then
    print_warning "Test container not found, building..."
    if ! docker build -f Dockerfile.test -t hippo-test:latest . > /dev/null 2>&1; then
        print_error "Failed to build test container"
        exit 1
    fi
fi
print_success "Test container ready"

# Run tests with coverage
print_step "Running tests with coverage analysis"
docker run --rm -v "$(pwd)/coverage_output:/coverage_output" hippo-test:latest \
    pytest tests/ -v --tb=short \
    --cov=src --cov-report=xml:/coverage_output/coverage.xml \
    --cov-report=term-missing --cov-report=html:/coverage_output/htmlcov \
    --cov-report=json:/coverage_output/coverage.json \
    --cov-fail-under=$MIN_COVERAGE --cov-branch

# Check if coverage passed
if [ $? -eq 0 ]; then
    print_success "Coverage check passed (minimum: ${MIN_COVERAGE}%)"
    
    # Extract actual coverage from JSON
    if [ -f "coverage_output/coverage.json" ]; then
        ACTUAL_COVERAGE=$(python -c "import json; data=json.load(open('coverage_output/coverage.json')); print(f\"{data['totals']['percent_covered']:.1f}\")")
        echo ""
        echo "Current coverage: ${ACTUAL_COVERAGE}%"
        echo "Target coverage: ${TARGET_COVERAGE}%"
        
        if (( $(echo "$ACTUAL_COVERAGE >= $TARGET_COVERAGE" | bc -l) )); then
            print_success "Excellent! Target coverage achieved! 🎉"
        else
            NEEDED=$(echo "$TARGET_COVERAGE - $ACTUAL_COVERAGE" | bc)
            print_warning "Need ${NEEDED}% more to reach target coverage"
        fi
    fi
    
    # Generate coverage comment if requested
    if [ "$1" == "--comment" ]; then
        print_step "Generating coverage comment"
        docker run --rm -v "$(pwd):/app" hippo-test:latest \
            python scripts/generate_coverage_comment.py > coverage_comment.md
        print_success "Coverage comment generated: coverage_comment.md"
    fi
    
    echo ""
    echo "Coverage reports available in:"
    echo "  - coverage_output/coverage.xml"
    echo "  - coverage_output/htmlcov/index.html"
    echo "  - coverage_output/coverage.json"
    
    # Clean up temporary output directory
    mv coverage_output/* . 2>/dev/null || true
    rmdir coverage_output 2>/dev/null || true
    
    exit 0
else
    print_error "Coverage check failed (minimum: ${MIN_COVERAGE}%)"
    
    # Clean up temporary output directory
    rm -rf coverage_output
    
    exit 1
fi