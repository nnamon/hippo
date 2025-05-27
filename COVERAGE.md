# Coverage Report

![Coverage](https://img.shields.io/badge/coverage-58.5%25-red)

## Overview

This document provides details about test coverage for the Hippo Bot project. We use pytest-cov for comprehensive coverage analysis including statement and branch coverage.

## Current Coverage Status

| File | Coverage | Lines Covered | Total Lines |
|------|----------|---------------|-------------|
| src/content/manager.py | 🟢 97.8% | 45/46 | Very Good |
| src/bot/reminder_system.py | 🟡 76.0% | 117/154 | Good |
| src/database/models.py | 🟡 69.4% | 136/196 | Needs Attention |
| src/bot/hippo_bot.py | 🔴 42.6% | 178/418 | Needs Attention |

**Overall Coverage: 58.5%** (476/814 lines)

## Coverage Goals

- **Target**: 80% overall coverage
- **Minimum**: 70% per file
- **Critical components**: 90%+ coverage

## How to Run Coverage Analysis

### Local Development

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Generate detailed coverage analysis
python coverage_analysis.py

# Run with test runner
python run_tests.py --coverage
```

### Docker Environment

```bash
# Build and run tests in Docker with coverage
docker build -f Dockerfile.test -t hippo-test .
docker run --rm hippo-test python coverage_analysis.py
```

### CI/CD Pipeline

Coverage is automatically generated and reported in our GitHub Actions workflows:
- Unit tests generate coverage reports
- Coverage is uploaded to Codecov
- HTML reports are stored as artifacts

## Coverage Reports

### Available Report Formats

1. **Terminal Output**: Real-time coverage during test runs
2. **HTML Report**: Detailed interactive report in `htmlcov/index.html`
3. **XML Report**: Machine-readable format in `coverage.xml`
4. **JSON Report**: Structured data in `coverage.json`

### Viewing HTML Reports

After running tests with coverage:

```bash
# Open the HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Areas Needing Attention

### Low Coverage Files (< 70%)

1. **src/bot/hippo_bot.py (42.6%)**
   - Main bot logic with many conditional paths
   - Error handling and edge cases need testing
   - Bot initialization and webhook setup
   - Focus on command handlers and callback functions

2. **src/database/models.py (69.4%)**
   - Database connection error handling
   - Edge cases in data validation
   - Transaction rollback scenarios

### Coverage Improvement Strategy

1. **Add integration tests** for bot command flows
2. **Test error conditions** and exception handling
3. **Cover edge cases** in user data validation
4. **Add tests for webhook and bot setup** functionality
5. **Test database transaction failures** and recovery

## Branch Coverage

We track branch coverage in addition to line coverage:
- **Current Branch Coverage**: 82.0% (141/172 branches)
- **Goal**: 85%+ branch coverage

Branch coverage ensures that:
- All if/else conditions are tested
- Exception paths are covered
- Loop conditions are validated

## Coverage Configuration

Coverage settings are configured in:
- **pytest.ini**: Basic coverage settings and thresholds
- **.coveragerc**: Detailed coverage configuration
- **GitHub Actions**: CI/CD coverage reporting

### Key Settings

- **Minimum Coverage**: 60% (configurable)
- **Branch Coverage**: Enabled
- **Omitted Files**: Tests, migrations, generated code
- **Fail Under**: Tests fail if coverage drops below threshold

## Codecov Integration

Coverage reports are automatically uploaded to Codecov for:
- **Pull Request Comments**: Coverage changes for each PR
- **Historical Tracking**: Coverage trends over time
- **File-level Analysis**: Detailed per-file coverage
- **Diff Coverage**: Coverage of changed lines only

## Best Practices

### Writing Tests for Coverage

1. **Test happy paths first**: Core functionality
2. **Add error cases**: Exception handling
3. **Cover edge conditions**: Boundary values
4. **Test async code properly**: Use pytest-asyncio
5. **Mock external dependencies**: Database, APIs, etc.

### Coverage Maintenance

1. **Monitor coverage trends**: Don't let it decrease
2. **Review uncovered lines**: Understand why they're missed
3. **Add tests for new features**: Maintain coverage levels
4. **Remove dead code**: Eliminate untestable code paths

## Excluding Code from Coverage

Use `# pragma: no cover` for:
- Debug code
- Platform-specific code
- External library workarounds
- Defensive programming checks

```python
def debug_function():  # pragma: no cover
    print("Debug information")
```

## Coverage Metrics History

| Date | Coverage | Change | Notes |
|------|----------|---------|-------|
| 2024-12-XX | 58.5% | Initial | First comprehensive test suite |

---

*Coverage report generated automatically by GitHub Actions. Last updated: {{date}}*