# obsidian-project-sync Development Makefile

.PHONY: help install install-dev test test-cov lint format clean build publish docs

help:
	@echo "Available targets:"
	@echo "  install      - Install package in development mode"
	@echo "  install-dev  - Install with development dependencies"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage"
	@echo "  lint         - Run linting (flake8, mypy)"
	@echo "  format       - Format code (black, isort)"
	@echo "  clean        - Clean build artifacts"
	@echo "  build        - Build package"
	@echo "  publish      - Publish to PyPI"
	@echo "  docs         - Generate documentation"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest

test-cov:
	pytest --cov=obsidian_project_sync --cov-report=html --cov-report=term

lint:
	flake8 obsidian_project_sync tests
	mypy obsidian_project_sync

format:
	black obsidian_project_sync tests
	isort obsidian_project_sync tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

publish: build
	python -m twine upload dist/*

docs:
	@echo "📚 Documentation is in README.md"
	@echo "💡 Consider adding sphinx documentation in the future"

# Development workflow
dev-setup: install-dev
	@echo "🚀 Development setup complete!"
	@echo "📝 Next steps:"
	@echo "  1. Copy .env.example to .env (if testing locally)"
	@echo "  2. Run 'make test' to verify setup"
	@echo "  3. Run 'obsidian-sync init' in a test project"

# Release workflow
release-check:
	@echo "🔍 Pre-release checklist:"
	@echo "  ✓ Version updated in pyproject.toml?"
	@echo "  ✓ CHANGELOG.md updated?"
	@echo "  ✓ All tests passing?"
	@echo "  ✓ Documentation updated?"
	@echo ""
	@echo "Run 'make test-cov lint' to verify quality"

# Example usage
example:
	@echo "🧪 Example usage:"
	@echo "  mkdir test-project && cd test-project"
	@echo "  obsidian-sync init"
	@echo "  cp .env.example .env  # Configure your API settings"
	@echo "  obsidian-sync test"
	@echo "  obsidian-sync"