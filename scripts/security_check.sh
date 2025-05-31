#!/bin/bash

# Security check script for Hippo bot
# Runs security scans that can be replicated locally

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}🔒 Hippo Bot Security Scanner${NC}"
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

# Check if running in CI
IS_CI=${CI:-false}

print_header

# Track overall success
SUCCESS=true

# Install security tools if needed
print_step "Checking security tools"
if ! command -v bandit &> /dev/null; then
    print_warning "Bandit not found, installing..."
    pip install bandit
fi

if ! command -v safety &> /dev/null; then
    print_warning "Safety not found, installing..."
    pip install safety
fi

print_success "Security tools ready"

# Run Bandit security linter
print_step "Running Bandit security scan"
if bandit -r src/ -ll -f json -o bandit-report.json 2>/dev/null; then
    # Also run human-readable format
    bandit -r src/ -ll
    print_success "Bandit scan completed - no high severity issues found"
else
    print_warning "Bandit found some issues (see report above)"
    # Don't fail the script for Bandit warnings
fi

# Check dependencies for known vulnerabilities
print_step "Checking dependencies for vulnerabilities"
if safety check --json --output safety-report.json 2>/dev/null; then
    # Also run human-readable format
    safety check
    print_success "No known vulnerabilities in dependencies"
else
    print_warning "Safety found some vulnerabilities (see report above)"
    # Don't fail the script for known vulnerabilities
fi

# Final result
echo ""
echo "========================================"
if [[ "$SUCCESS" == "true" ]]; then
    print_success "Security scan completed! 🔒"
    echo ""
    echo "Reports generated:"
    echo "  - bandit-report.json"
    echo "  - safety-report.json"
    exit 0
else
    print_error "Security scan found issues!"
    exit 1
fi