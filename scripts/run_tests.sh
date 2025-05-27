#!/bin/bash

# Test runner script for Hippo bot
# All tests run in Docker containers for consistency

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}🦛 Hippo Bot Test Runner${NC}"
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

# Build test container
build_test_container() {
    print_step "Building test container"
    if docker build -f Dockerfile.test -t hippo-test:latest . > /dev/null 2>&1; then
        print_success "Test container built successfully"
        return 0
    else
        print_error "Failed to build test container"
        return 1
    fi
}

# Run unit tests in container
run_unit_tests() {
    print_step "Running unit tests in Docker container"
    if docker run --rm hippo-test:latest; then
        print_success "Unit tests passed (64 tests)"
        return 0
    else
        print_error "Unit tests failed"
        return 1
    fi
}

# Run integration tests in container
run_integration_tests() {
    print_step "Running integration tests in Docker container"
    if docker run --rm hippo-test:latest python scripts/integration_test.py; then
        print_success "Integration tests passed (5 tests)"
        return 0
    else
        print_error "Integration tests failed"
        return 1
    fi
}

# Test production build
test_production_build() {
    print_step "Testing production Docker build"
    if docker build -t hippo-bot:test . > /dev/null 2>&1; then
        if docker run --rm hippo-bot:test python -c "from bot.hippo_bot import HippoBot; print('✅ Production build works')" > /dev/null 2>&1; then
            print_success "Production build verified"
            return 0
        else
            print_error "Production build import test failed"
            return 1
        fi
    else
        print_error "Production build failed"
        return 1
    fi
}

# Usage information
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --unit         Run unit tests only"
    echo "  --integration  Run integration tests only"
    echo "  --production   Test production build only"
    echo "  --all          Run all tests (default)"
    echo "  --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all tests"
    echo "  $0 --unit            # Run unit tests only"
    echo "  $0 --integration     # Run integration tests only"
    echo "  $0 --production      # Test production build only"
}

# Parse command line arguments
UNIT_TESTS=false
INTEGRATION_TESTS=false
PRODUCTION_TEST=false
ALL_TESTS=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            UNIT_TESTS=true
            ALL_TESTS=false
            shift
            ;;
        --integration)
            INTEGRATION_TESTS=true
            ALL_TESTS=false
            shift
            ;;
        --production)
            PRODUCTION_TEST=true
            ALL_TESTS=false
            shift
            ;;
        --all)
            ALL_TESTS=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
print_header

# Track overall success
SUCCESS=true

# Build test container first if we're running any container-based tests
if [[ "$ALL_TESTS" == "true" || "$UNIT_TESTS" == "true" || "$INTEGRATION_TESTS" == "true" ]]; then
    if ! build_test_container; then
        SUCCESS=false
    fi
fi

# Run tests based on options
if [[ "$ALL_TESTS" == "true" || "$UNIT_TESTS" == "true" ]]; then
    if [[ "$SUCCESS" == "true" ]]; then
        if ! run_unit_tests; then
            SUCCESS=false
        fi
    else
        print_warning "Skipping unit tests due to container build failure"
    fi
fi

if [[ "$ALL_TESTS" == "true" || "$INTEGRATION_TESTS" == "true" ]]; then
    if [[ "$SUCCESS" == "true" ]]; then
        if ! run_integration_tests; then
            SUCCESS=false
        fi
    else
        print_warning "Skipping integration tests due to previous failures"
    fi
fi

if [[ "$ALL_TESTS" == "true" || "$PRODUCTION_TEST" == "true" ]]; then
    if ! test_production_build; then
        SUCCESS=false
    fi
fi

# Final result
echo ""
echo "========================================"
if [[ "$SUCCESS" == "true" ]]; then
    print_success "All tests completed successfully! 🎉"
    exit 0
else
    print_error "Some tests failed! Please check the output above."
    exit 1
fi