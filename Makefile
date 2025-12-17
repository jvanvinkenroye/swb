.PHONY: help install test lint format type-check clean dev run-example

help:
	@echo "SWB API Client - Development Commands"
	@echo ""
	@echo "Available targets:"
	@echo "  install      - Install package and dependencies"
	@echo "  dev          - Install package with development dependencies"
	@echo "  test         - Run tests with coverage"
	@echo "  lint         - Run ruff linter"
	@echo "  format       - Format code with ruff"
	@echo "  type-check   - Run mypy type checker"
	@echo "  clean        - Remove build artifacts and cache files"
	@echo "  run-example  - Run basic usage example"
	@echo "  all          - Run format, lint, type-check, and test"

install:
	uv pip install -e .

dev:
	uv sync --dev

test:
	pytest -v --cov=swb --cov-report=term-missing --cov-report=html

lint:
	ruff check .

format:
	ruff format .
	ruff check --fix .

type-check:
	mypy src/swb

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -f .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run-example:
	python examples/basic_usage.py

all: format lint type-check test
	@echo "All checks passed!"
