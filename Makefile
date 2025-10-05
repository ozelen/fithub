.PHONY: help install test test-local test-ci lint format security clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync --extra test

test: ## Run all tests with PostgreSQL containers
	DJANGO_SETTINGS_MODULE=fithub.test_settings uv run pytest

test-fast: ## Run tests with SQLite (faster, no Docker required)
	DJANGO_SETTINGS_MODULE=fithub.test_settings_sqlite uv run pytest

test-local: ## Run tests with local PostgreSQL database (requires PostgreSQL running)
	DJANGO_SETTINGS_MODULE=fithub.settings uv run pytest

test-ci: ## Run tests for CI (with coverage and PostgreSQL containers)
	DJANGO_SETTINGS_MODULE=fithub.test_settings uv run pytest --cov=. --cov-report=xml --cov-report=html

test-ci-fast: ## Run tests for CI with SQLite (faster)
	DJANGO_SETTINGS_MODULE=fithub.test_settings_sqlite uv run pytest --cov=. --cov-report=xml --cov-report=html

lint: ## Run linting checks
	uv run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=.venv,venv,__pycache__,.git
	uv run flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --exclude=.venv,venv,__pycache__,.git

format: ## Format code with black and isort
	uv run black .
	uv run isort .

format-check: ## Check code formatting
	uv run black --check .
	uv run isort --check-only .

security: ## Run security checks
	uv run bandit -r . -f json -o bandit-report.json
	uv run safety check --json --output safety-report.json

migrate: ## Run database migrations
	uv run manage.py migrate

migrate-test: ## Run database migrations for tests
	DJANGO_SETTINGS_MODULE=fithub.test_settings uv run manage.py migrate

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf bandit-report.json
	rm -rf safety-report.json

dev: ## Start development server
	uv run manage.py runserver

shell: ## Start Django shell
	uv run manage.py shell

superuser: ## Create superuser
	uv run manage.py createsuperuser
