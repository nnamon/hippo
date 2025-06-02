# Makefile for Hippo Bot - Water Reminder Telegram Bot
# 
# This Makefile provides convenient commands for development, testing, and deployment
# All operations use Docker containers for consistency across environments

# Variables
DOCKER_IMAGE = hippo-bot
DOCKER_TEST_IMAGE = hippo-test
DOCKER_COMPOSE_FILE = docker-compose.yml
CONTAINER_NAME = hippo-water-bot

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

# Default target
.PHONY: help
help: ## Show this help message
	@echo "🦛 Hippo Bot - Makefile Commands"
	@echo "=================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(BLUE)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make test          # Run all tests"
	@echo "  make test-unit     # Run only unit tests"
	@echo "  make build         # Build Docker images"
	@echo "  make run           # Start the bot"
	@echo "  make logs          # View bot logs"

# Development Commands
.PHONY: install
install: ## Install Python dependencies locally
	@echo -e "$(BLUE)📦 Installing dependencies...$(NC)"
	pip install -r requirements.txt
	pip install -r requirements-test.txt

.PHONY: install-dev
install-dev: install ## Install development dependencies
	@echo -e "$(BLUE)🔧 Installing development tools...$(NC)"
	pip install black flake8 isort mypy

.PHONY: format
format: ## Format code with black and isort
	@echo -e "$(BLUE)🎨 Formatting code...$(NC)"
	black src/ tests/ --line-length 100
	isort src/ tests/ --profile black

.PHONY: lint
lint: ## Run code linting
	@echo -e "$(BLUE)🔍 Running linters...$(NC)"
	flake8 src/ tests/ --max-line-length=100 --extend-ignore=E203,W503
	mypy src/ --ignore-missing-imports

# Docker Commands
.PHONY: build
build: ## Build Docker images
	@echo -e "$(BLUE)🐳 Building Docker images...$(NC)"
	docker build -t $(DOCKER_IMAGE) .
	docker build -f Dockerfile.test -t $(DOCKER_TEST_IMAGE) .
	@echo -e "$(GREEN)✅ Docker images built successfully$(NC)"

.PHONY: build-prod
build-prod: ## Build production Docker image
	@echo -e "$(BLUE)🐳 Building production Docker image...$(NC)"
	docker build -t $(DOCKER_IMAGE):latest .
	@echo -e "$(GREEN)✅ Production image built$(NC)"

.PHONY: build-test
build-test: ## Build test Docker image
	@echo -e "$(BLUE)🐳 Building test Docker image...$(NC)"
	docker build -f Dockerfile.test -t $(DOCKER_TEST_IMAGE) .
	@echo -e "$(GREEN)✅ Test image built$(NC)"

# Testing Commands
.PHONY: test
test: build-test ## Run all tests (unit + integration)
	@echo -e "$(BLUE)🧪 Running all tests...$(NC)"
	./scripts/run_tests.sh
	@echo -e "$(GREEN)✅ All tests completed$(NC)"

.PHONY: test-unit
test-unit: build-test ## Run unit tests only
	@echo -e "$(BLUE)🧪 Running unit tests...$(NC)"
	docker run --rm $(DOCKER_TEST_IMAGE)

.PHONY: test-integration
test-integration: build-test ## Run integration tests only
	@echo -e "$(BLUE)🧪 Running integration tests...$(NC)"
	docker run --rm $(DOCKER_TEST_IMAGE) python scripts/integration_test.py

.PHONY: test-coverage
test-coverage: build-test ## Run tests with detailed coverage report
	@echo -e "$(BLUE)📊 Running tests with coverage...$(NC)"
	docker run --rm $(DOCKER_TEST_IMAGE) python -m pytest --cov=src --cov-report=html --cov-report=term-missing tests/
	@echo -e "$(GREEN)✅ Coverage report generated$(NC)"

.PHONY: test-watch
test-watch: build-test ## Run tests in watch mode (requires pytest-watch)
	@echo -e "$(BLUE)👀 Running tests in watch mode...$(NC)"
	docker run --rm -v $(PWD):/app $(DOCKER_TEST_IMAGE) ptw -- --testmon

# Application Commands
.PHONY: run
run: ## Start the bot with Docker Compose (rebuilds container)
	@echo -e "$(BLUE)🚀 Starting Hippo Bot...$(NC)"
	docker-compose up --build -d
	@echo -e "$(GREEN)✅ Bot started in background$(NC)"
	@echo "Use 'make logs' to view output or 'make status' to check health"

.PHONY: run-dev
run-dev: ## Run bot in development mode (foreground, rebuilds container)
	@echo -e "$(BLUE)🚀 Starting Hippo Bot in development mode...$(NC)"
	docker-compose up --build

.PHONY: stop
stop: ## Stop the running bot
	@echo -e "$(BLUE)🛑 Stopping Hippo Bot...$(NC)"
	docker-compose down
	@echo -e "$(GREEN)✅ Bot stopped$(NC)"

.PHONY: restart
restart: stop run ## Restart the bot
	@echo -e "$(GREEN)🔄 Bot restarted$(NC)"

.PHONY: logs
logs: ## View bot logs
	@echo -e "$(BLUE)📜 Viewing bot logs...$(NC)"
	docker-compose logs -f hippo-bot

.PHONY: logs-tail
logs-tail: ## View last 100 lines of logs
	@echo -e "$(BLUE)📜 Viewing recent bot logs...$(NC)"
	docker-compose logs --tail=100 hippo-bot

.PHONY: status
status: ## Check bot status and health
	@echo -e "$(BLUE)📊 Checking bot status...$(NC)"
	docker-compose ps
	@echo ""
	@docker-compose exec hippo-bot python -c "import sqlite3; print('✅ Database accessible')" 2>/dev/null || echo "❌ Database not accessible"

# Database Commands
.PHONY: db-debug
db-debug: ## Run database debug analysis
	@echo -e "$(BLUE)🗄️ Running database debug...$(NC)"
	./scripts/debug.sh

.PHONY: db-shell
db-shell: ## Open SQLite shell for database
	@echo -e "$(BLUE)🗄️ Opening database shell...$(NC)"
	docker run --rm -v $(PWD)/data:/data -it alpine/sqlite sqlite3 /data/hippo.db

.PHONY: db-backup
db-backup: ## Backup database
	@echo -e "$(BLUE)💾 Backing up database...$(NC)"
	@mkdir -p backups
	cp data/hippo.db backups/hippo-$(shell date +%Y%m%d_%H%M%S).db
	@echo -e "$(GREEN)✅ Database backed up to backups/$(NC)"

.PHONY: db-restore
db-restore: ## Restore database from backup (requires BACKUP_FILE variable)
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo -e "$(RED)❌ Please specify BACKUP_FILE: make db-restore BACKUP_FILE=path/to/backup.db$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(BLUE)📥 Restoring database from $(BACKUP_FILE)...$(NC)"
	cp $(BACKUP_FILE) data/hippo.db
	@echo -e "$(GREEN)✅ Database restored$(NC)"

# Maintenance Commands
.PHONY: clean
clean: ## Clean up Docker containers and images
	@echo -e "$(BLUE)🧹 Cleaning up...$(NC)"
	docker-compose down --remove-orphans
	docker system prune -f
	@echo -e "$(GREEN)✅ Cleanup completed$(NC)"

.PHONY: clean-all
clean-all: ## Clean up everything including volumes
	@echo -e "$(BLUE)🧹 Deep cleaning (including volumes)...$(NC)"
	docker-compose down --volumes --remove-orphans
	docker system prune -af
	@echo -e "$(GREEN)✅ Deep cleanup completed$(NC)"

.PHONY: reset
reset: clean-all build ## Reset everything and rebuild
	@echo -e "$(GREEN)🔄 Environment reset completed$(NC)"

# Deployment Commands
.PHONY: deploy
deploy: test build-prod ## Run tests and build for deployment
	@echo -e "$(BLUE)🚀 Preparing for deployment...$(NC)"
	@echo -e "$(GREEN)✅ Ready for deployment$(NC)"
	@echo "Next steps:"
	@echo "  1. Tag image: docker tag $(DOCKER_IMAGE):latest your-registry/$(DOCKER_IMAGE):v1.0.0"
	@echo "  2. Push image: docker push your-registry/$(DOCKER_IMAGE):v1.0.0"
	@echo "  3. Deploy with: docker-compose up -d"

.PHONY: version
version: ## Show version information
	@echo -e "$(BLUE)📋 Version Information$(NC)"
	@echo "Docker images:"
	@docker images $(DOCKER_IMAGE) 2>/dev/null || echo "❌ $(DOCKER_IMAGE) not built"
	@docker images $(DOCKER_TEST_IMAGE) 2>/dev/null || echo "❌ $(DOCKER_TEST_IMAGE) not built"
	@echo ""
	@echo "Container status:"
	@docker-compose ps 2>/dev/null || echo "❌ No containers running"

# Development Workflow Commands
.PHONY: dev-setup
dev-setup: install build ## Complete development setup
	@echo -e "$(GREEN)✅ Development environment ready!$(NC)"
	@echo "Next steps:"
	@echo "  1. Copy config.env.example to config.env"
	@echo "  2. Add your Telegram bot token to config.env"
	@echo "  3. Run: make run"

.PHONY: dev-test
dev-test: lint test ## Run linting and all tests
	@echo -e "$(GREEN)✅ All development checks passed$(NC)"

.PHONY: quick-test
quick-test: ## Quick test run (unit tests only)
	@echo -e "$(BLUE)⚡ Running quick tests...$(NC)"
	docker run --rm $(DOCKER_TEST_IMAGE) python -m pytest tests/ -x --tb=short

# CI/CD Helpers
.PHONY: ci-test
ci-test: build-test ## CI/CD test pipeline
	@echo -e "$(BLUE)🏗️ Running CI test pipeline...$(NC)"
	docker run --rm $(DOCKER_TEST_IMAGE)
	docker run --rm $(DOCKER_TEST_IMAGE) python scripts/integration_test.py
	@echo -e "$(GREEN)✅ CI tests passed$(NC)"

.PHONY: validate
validate: lint test ## Validate code quality and tests
	@echo -e "$(GREEN)✅ Code validation completed$(NC)"

# Special targets
.DEFAULT_GOAL := help
.PHONY: all
all: clean build test ## Clean, build, and test everything
	@echo -e "$(GREEN)✅ Complete build and test cycle finished$(NC)"