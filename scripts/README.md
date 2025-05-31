# Hippo Bot Scripts

This directory contains all scripts used for testing, CI/CD, and development workflows. These scripts are designed to work both locally and in GitHub Actions, ensuring consistent behavior across environments.

## Available Scripts

### 🧪 `run_tests.sh`
Main test runner that executes all tests in Docker containers.

```bash
./scripts/run_tests.sh           # Run all tests (default)
./scripts/run_tests.sh --unit    # Run unit tests only
./scripts/run_tests.sh --integration  # Run integration tests only
./scripts/run_tests.sh --production   # Test production build only
./scripts/run_tests.sh --help    # Show usage information
```

**What it does:**
- Builds test container from `Dockerfile.test`
- Runs 64 unit tests with pytest
- Runs 5 integration tests
- Validates production Docker build
- All tests run in containers for consistency

### 📊 `coverage_check.sh`
Analyzes test coverage and generates reports.

```bash
./scripts/coverage_check.sh           # Run coverage analysis
./scripts/coverage_check.sh --comment # Also generate PR comment
```

**What it does:**
- Runs tests with coverage tracking
- Enforces minimum coverage (55%)
- Shows progress toward target coverage (80%)
- Generates XML, HTML, and JSON reports
- Optionally creates PR comment markdown

### 🔒 `security_check.sh`
Performs security scans on code and dependencies.

```bash
./scripts/security_check.sh  # Run all security checks
```

**What it does:**
- Runs Bandit static security analysis
- Checks dependencies with Safety
- Generates JSON reports
- Non-blocking warnings (informational)

### 🧬 `integration_test.py`
Python script that tests component integration.

```bash
python scripts/integration_test.py  # Run integration tests
```

**What it does:**
- Tests bot component imports
- Validates database operations
- Checks content manager integration
- Tests reminder system components
- Verifies dynamic poem generation

### 💬 `generate_coverage_comment.py`
Generates formatted coverage reports for PR comments.

```bash
python scripts/generate_coverage_comment.py  # Generate markdown comment
```

**What it does:**
- Reads coverage.json
- Creates detailed markdown report
- Shows file-by-file coverage
- Highlights uncovered lines
- Provides improvement suggestions

## CI/CD Integration

All these scripts are used by GitHub Actions in `.github/workflows/ci.yml`:

```yaml
- run: ./scripts/run_tests.sh --all       # Test job
- run: ./scripts/security_check.sh        # Security job
- run: python scripts/generate_coverage_comment.py  # PR comments
```

## Local Development

To replicate CI behavior locally:

```bash
# Run full CI suite
./scripts/run_tests.sh --all && ./scripts/security_check.sh

# Check coverage before pushing
./scripts/coverage_check.sh

# Debug specific test failures
./scripts/run_tests.sh --unit
docker run --rm -it hippo-test:latest pytest tests/test_content_manager.py -v
```

## Requirements

- Docker installed and running
- Python 3.9+ (for security checks)
- Bash shell (scripts are POSIX-compliant)

## Troubleshooting

### macOS Keychain Issues
If you see "keychain cannot be accessed" errors:
```bash
security -v unlock-keychain ~/Library/Keychains/login.keychain-db
```

### Permission Denied
Make scripts executable:
```bash
chmod +x scripts/*.sh
```

### Docker Not Found
Ensure Docker Desktop is running or Docker daemon is started:
```bash
docker --version  # Should show version
```