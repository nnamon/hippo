# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hippo is a Telegram bot that reminds users to drink water with cute cartoons and poems. The bot operates on user-configurable schedules and tracks hydration metrics to generate personalized cartoon states (6 hydration levels from dehydrated to fully engorged).

## Architecture

This is a Python-based Telegram bot project with the following core components:

- **User Management**: Handle Telegram user subscriptions and configuration
- **Scheduling System**: Support both interval-based (every 15 mins) and time-based (18th minute every hour) reminders
- **Hydration Tracking**: Persist user water drinking metrics and calculate hydration states
- **Content Generation**: Generate poems and select appropriate cartoon images based on hydration state
- **Cartoon Theming**: Support multiple cartoon sets with 6 states each, user-selectable themes

## Implementation Notes

- The project is implemented in Python 3.9+ using python-telegram-bot framework
- SQLite database for user data and hydration metrics persistence
- Cartoon images organized in themed arrays of 6 hydration states (0%, 20%, 40%, 60%, 80%, 100%)
- Bot uses async architecture with job queue for scheduled reminders
- Deployment via Docker containers on Digital Ocean

## Commands for Development

### Makefile Workflow (Recommended)

The project includes a comprehensive Makefile that automates all development tasks. **Benefits:**
- **Consistency**: Same commands work across all environments
- **Simplicity**: Single commands for complex workflows
- **Integration**: Seamlessly integrates with Docker and existing scripts
- **Productivity**: Reduces context switching and typing
- **Reliability**: Tested, standardized procedures

**Quick Start:**
```bash
make dev-setup    # Complete development environment setup
make test         # Run all tests (unit + integration)
make run          # Start the bot with Docker Compose
make logs         # View bot logs
```

**Development Commands:**
```bash
make install      # Install Python dependencies locally
make install-dev  # Install with development tools (black, flake8, mypy)
make format       # Format code with black and isort
make lint         # Run code linting with flake8 and mypy
make validate     # Run linting + all tests (full validation)
```

**Testing Commands:**
```bash
make test              # All tests (unit + integration)
make test-unit         # Unit tests only (faster)
make test-integration  # Integration tests only
make test-coverage     # Tests with HTML coverage report
make quick-test        # Fast unit test run with minimal output
make ci-test           # CI/CD pipeline simulation
```

**Application Management:**
```bash
make run           # Start bot in background (production mode)
make run-dev       # Start bot in foreground (development mode)
make stop          # Stop the running bot
make restart       # Restart the bot (stop + start)
make status        # Check bot health and container status
make logs          # Follow live logs
make logs-tail     # View last 100 log lines
```

**Database Operations:**
```bash
make db-debug      # Run comprehensive database analysis
make db-shell      # Open SQLite shell for database
make db-backup     # Create timestamped database backup
make db-restore BACKUP_FILE=path/to/backup.db  # Restore from backup
```

**Maintenance:**
```bash
make clean         # Clean Docker containers and images
make clean-all     # Deep clean including volumes
make reset         # Reset everything and rebuild
make version       # Show version and status information
make help          # Show all available commands
```

### Traditional Commands (Alternative)

**Install Dependencies:**
```bash
pip install -r requirements.txt
pip install -r requirements-test.txt  # For testing
```

**Run the Bot:**
```bash
python main.py
```

## Testing Infrastructure

The project uses a comprehensive testing system with **Docker-based containers** for consistent environments across local development and CI/CD:

### Test Execution Methods

**All testing is done in Docker containers to ensure consistent environments between local development and CI/CD.**

#### Recommended: Makefile Commands

```bash
# Complete test suite (recommended for development)
make test              # Build test container + run all tests + integration tests

# Specific test types
make test-unit         # Unit tests only (faster for development)
make test-integration  # Integration tests only
make test-coverage     # Generate detailed HTML coverage report
make quick-test        # Fast unit tests with minimal output

# CI/CD simulation
make ci-test           # Full CI pipeline (build + test + integration)
make validate          # Code quality + tests (linting + testing)
```

#### Traditional Docker Commands (Alternative)

```bash
# Build test container with all dependencies
docker build -f Dockerfile.test -t hippo-test .

# Run all unit tests with coverage (89 tests)
docker run --rm hippo-test

# Run integration tests (5 component tests)  
docker run --rm hippo-test python scripts/integration_test.py

# Test production Docker build
docker build -t hippo-bot:test .
docker run --rm hippo-bot:test python -c "from bot.hippo_bot import HippoBot; print('✅ Production build works')"

# Alternative: Use test runner script (also uses Docker internally)
./scripts/run_tests.sh
```

### Test Coverage Status

- **Current Coverage**: 77.8% overall (focused on business logic)
- **Minimum Required**: 55% (CI enforced)
- **Target Coverage**: 80% overall
- **Coverage Tracking**: XML, HTML, JSON reports + Codecov integration
- **Total Tests**: 89 unit tests + 5 integration tests
- **Coverage Strategy**: Infrastructure code excluded via pragma comments to focus metrics on testable business logic

### Test Categories

1. **Unit Tests** (`tests/test_*.py`) - **89 tests total**:
   - **Bot Commands** (29 tests): Command handlers, callbacks, reset functionality, quote commands, stats displays
   - **Content Manager** (17 + 11 dynamic + 5 quote tests): Poem generation, themes, emoji classification, quote functionality
   - **Database** (17 tests): User management, hydration tracking, data persistence, active reminders
   - **Reminder System** (15 tests): Scheduling, timezone handling, waking hours

2. **Integration Tests** (`scripts/integration_test.py`) - **5 tests**:
   - **Bot Imports**: Verify all components import successfully
   - **Database Integration**: End-to-end database operations
   - **Content Manager Integration**: Poem/theme functionality
   - **Reminder System Integration**: Component interaction testing
   - **Dynamic Poem Generation**: API integration and caching

3. **Container Tests**:
   - **Test Container**: Dockerfile.test with pytest + pytest-cov + pytest-asyncio
   - **Production Container**: Full bot build verification
   - **Import Validation**: Ensure all production imports work

4. **Security Tests** (CI only):
   - **Bandit**: Python security linter for code vulnerabilities
   - **Safety**: Dependency vulnerability scanning
   - **Code Quality**: Flake8 linting with error tolerance

### GitHub Actions CI/CD Pipeline

**Single Comprehensive Workflow** (`.github/workflows/test.yml`)

**Triggers**: Pushes to `main`/`develop`, PRs, manual dispatch

**Jobs**:
1. **🧪 Unit Tests**: Python environment with pytest + coverage (55% minimum)
2. **🐳 Docker Tests**: 
   - Build test container (Dockerfile.test)
   - Run unit tests in container environment  
   - Run integration tests in container
   - Validate production Docker build
3. **🔒 Security**: Bandit + Safety scans (continue-on-error)
4. **📊 Summary**: Combined results with pass/fail status

**Key Features**:
- **Coverage Reporting**: Codecov integration with PR comments
- **Artifact Management**: 30-day retention of coverage reports
- **Container-First**: Docker tests match production environment exactly
- **Fail-Fast**: Unit tests must pass before Docker tests run

### Coverage Reporting

- **Automatic PR Comments**: Detailed coverage breakdown posted on every PR
- **Historical Tracking**: Codecov integration for trends and analysis  
- **Multiple Formats**: HTML, XML, JSON reports with 30-day artifact retention
- **File-by-File Analysis**: Color-coded coverage status with improvement recommendations

### Testing Best Practices

#### For New Features
1. **Write tests first** or alongside implementation
2. **Aim for 70%+ coverage** on new files
3. **Test happy paths and error conditions**
4. **Use async testing properly** with pytest-asyncio
5. **Mock external dependencies** (Telegram API, etc.)

#### For Bug Fixes
1. **Write a failing test** that reproduces the bug
2. **Fix the implementation** to make the test pass
3. **Ensure no regression** in existing tests

#### Before Submitting PRs
1. **Run local tests**: `python run_tests.py --all`
2. **Check coverage**: Ensure no significant coverage drops
3. **Review test output**: Address any failing tests or warnings
4. **Verify GitHub Actions**: All checks must pass before merge

**Project Structure:**
```
src/
├── bot/                    # Bot logic and handlers
├── database/               # SQLite models and operations  
└── content/                # Poems and image management
tests/                      # Comprehensive test suite
├── conftest.py            # Shared test fixtures and configuration
├── test_bot_commands.py   # Bot command and callback tests
├── test_content_manager.py # Content and theme management tests
├── test_database.py       # Database operations tests
└── test_reminder_system.py # Reminder scheduling tests
scripts/
├── integration_test.py        # Integration test suite 
├── run_tests.sh              # Main test runner script (Docker-based)
├── generate_coverage_comment.py # Coverage PR comment generator
├── debug_database.py         # Database debug and analysis tool
└── debug.sh                  # Convenient debug wrapper script
.github/workflows/          # CI/CD automation
├── test.yml               # Main testing workflow
└── pr-checks.yml          # Quick PR validation
assets/
├── images/                # Cartoon image files by theme
├── bluey/                 # Default theme assets
├── desert/                # Alternative theme assets
├── spring/                # Alternative theme assets
└── vivid/                 # Alternative theme assets
requirements-test.txt      # Testing dependencies
pytest.ini                 # Pytest configuration
.coveragerc                # Coverage analysis configuration
Dockerfile.test            # Docker image for testing
COVERAGE.md                # Coverage documentation and guidelines
```

## Configuration

- Copy `config.env.example` to `config.env` and add your Telegram bot token
- Bot token obtained from @BotFather on Telegram
- Database file (`hippo.db`) created automatically on first run

## Debugging and Monitoring

### Database Debug Tools

The project includes comprehensive database debugging tools for troubleshooting and monitoring:

**Quick Debug (Recommended):**
```bash
make db-debug         # Comprehensive database analysis with Makefile
```

**Alternative Methods:**
```bash
./scripts/debug.sh    # Direct script execution

# Manual debug
DATABASE_PATH=./data/hippo.db python scripts/debug_database.py

# From inside Docker container (after rebuild)
docker exec hippo-water-bot python scripts/debug_database.py

# Interactive database shell
make db-shell         # Open SQLite shell with Makefile
```

**Debug Output Includes:**
- 🗄️ **Database Information**: File size, location, record counts
- 👥 **User Details**: All registered users with settings and status
- 📊 **User Statistics**: Success rates, event counts, last activity
- 🌊 **Hydration Levels**: Current hydration status for all users
- ⏰ **Active Reminders**: Outstanding reminders and expiration status
- 💧 **Recent Events**: Last 50 hydration events (confirmed/missed)

**Use Cases:**
- Monitor bot health and user engagement
- Troubleshoot reminder delivery issues
- Analyze user hydration patterns
- Identify expired or stuck reminders
- Verify database persistence after container restarts

## Development Workflow

**CRITICAL: Always use feature branches and pull requests. NEVER commit directly to main.**

### Required Workflow (with Makefile)
1. **Create feature branch**: `git checkout -b feature/description-of-work`
2. **Implement changes** on the feature branch
3. **Write/update tests**: Add tests for new functionality or bug fixes
4. **Run validation**: `make validate` to run linting and all tests
5. **Test functionality**: Test the bot implementation manually as appropriate
6. **Commit changes** to feature branch with descriptive messages
7. **Push branch**: `git push -u origin feature/branch-name`
8. **Verify GitHub Actions**: Ensure all CI/CD checks pass (tests, coverage, security)
9. **Test with running bot**: Before creating a PR, ask the user to verify the changes work with the running bot
10. **Create Pull Request**: Use `gh pr create` with proper title and description ONLY after user confirms the implementation works
11. **Review coverage comments**: Address any coverage concerns in the automated PR comment
12. **Only merge** after review/approval and all checks passing

### Alternative Workflow (Traditional)
1. **Create feature branch**: `git checkout -b feature/description-of-work`
2. **Implement changes** on the feature branch
3. **Write/update tests**: Add tests for new functionality or bug fixes
4. **Run Docker tests**: `./scripts/run_tests.sh` to verify everything works
5. **Test functionality**: Test the bot implementation manually as appropriate
6. **Commit changes** to feature branch with descriptive messages
7. **Push branch**: `git push -u origin feature/branch-name`
8. **Verify GitHub Actions**: Ensure all CI/CD checks pass (tests, coverage, security)
9. **Test with running bot**: Before creating a PR, ask the user to verify the changes work with the running bot
10. **Create Pull Request**: Use `gh pr create` with proper title and description ONLY after user confirms the implementation works
11. **Review coverage comments**: Address any coverage concerns in the automated PR comment
12. **Only merge** after review/approval and all checks passing

### Important Development Practices

#### Commit Frequently
**Save progress often with commits** to enable easy rollback of changes:
- Commit working states before making major changes
- Use descriptive commit messages that explain what was changed
- This allows you to revert to a known-good state if something breaks
- Example: `git commit -m "Add user hydration tracking before refactoring reminder system"`

#### Test-Driven Development
**IMPORTANT: Always include tests when adding new functionality**:
- Write tests for new features alongside implementation
- Use existing test patterns in `tests/` directory as templates
- Ensure new code maintains or improves overall coverage
- Run tests locally before pushing: `make test` (recommended) or `./scripts/run_tests.sh`
- Use `make quick-test` for rapid feedback during development
- Use `make test-coverage` to verify coverage improvements

#### Debugging Failed Tests
**When GitHub Actions fail (Makefile approach)**:
1. **Check the PR comment**: Automatic coverage analysis identifies issues
2. **Run tests locally**: `make test` or `make ci-test` to reproduce issues
3. **Quick debugging**: `make quick-test` for fast feedback
4. **View detailed logs**: Use `gh run view --log-failed` for GitHub Actions logs
5. **Test specific components**: `make test-unit` or `make test-integration`
6. **Generate coverage report**: `make test-coverage` for detailed analysis

**Traditional approach**:
1. **Check the PR comment**: Automatic coverage analysis identifies issues
2. **Run tests locally**: `./scripts/run_tests.sh` to reproduce issues
3. **View detailed logs**: Use `gh run view --log-failed` for GitHub Actions logs
4. **Test in Docker**: `docker run --rm hippo-test` to match CI environment
5. **Test specific components**: `./scripts/run_tests.sh --unit` or `./scripts/run_tests.sh --integration`

### Branch Naming Convention
- `feature/` - New features or enhancements
- `fix/` - Bug fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation updates

## MCP Tools Note

- The MCP Puppeteer tool runs inside a Docker container
- When accessing local services with Puppeteer, use `http://host.docker.internal:PORT` instead of `http://localhost:PORT`
- This allows the Docker container to access the host machine's services