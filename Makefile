.DEFAULT_GOAL := help

SHELL := /bin/bash

UV ?= uv
PYTHON := $(UV) run python
HOST ?= 127.0.0.1
PORT ?= 8000
DEMO_SEED ?= /tmp/ksp-investigateai-demo-seed.json
BENCHMARK_REPORT ?= /tmp/ksp-investigateai-benchmark.json
BENCHMARK_ITERATIONS ?= 25

PYTHON_PATHS := src functions data tests benchmarks main.py

.PHONY: help install api api-reload health web web-install web-build web-lint web-typecheck \
        test test-unit test-api test-catalyst smoke demo-seed demo-smoke benchmark \
        compile diff-check format-check format check clean clean-python clean-frontend \
        clean-runtime clean-checkpoints

help: ## Show available development commands
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make \\033[36m<TARGET>\\033[0m\\n\\nTargets:\\n"} /^[a-zA-Z0-9_-]+:.*##/ {printf "  \\033[36m%-20s\\033[0m %s\\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install and lock Python dependencies with uv
	$(UV) sync

api: ## Start the backend API on HOST and PORT
	$(UV) run uvicorn main:app --host $(HOST) --port $(PORT)

api-reload: ## Start the backend API with auto-reload for local development
	$(UV) run uvicorn main:app --host $(HOST) --port $(PORT) --reload

health: ## Check the running backend liveness endpoint
	@curl --fail --silent --show-error http://$(HOST):$(PORT)/health
	@printf '\n'

web: ## Start the Next.js frontend development server
	npm --prefix client run dev

web-install: ## Install locked frontend dependencies with npm ci
	npm --prefix client ci

web-build: ## Build the Next.js frontend
	npm --prefix client run build

web-lint: ## Run the configured frontend ESLint checks
	npm --prefix client run lint

web-typecheck: ## Run the configured frontend TypeScript check
	npm --prefix client run typecheck

test: ## Run the complete Python test suite
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

test-unit: ## Run Python unit tests only
	$(PYTHON) -m unittest discover -s tests/unit -p 'test_*.py' -v

test-api: ## Run FastAPI and typed API boundary tests
	$(PYTHON) -m unittest tests.integration.api.test_fastapi_boundary tests.unit.api.test_api -v

test-catalyst: ## Run Catalyst adapter, repository, and persistence tests
	$(PYTHON) -m unittest tests.unit.adapters.test_boundaries tests.unit.adapters.test_catalyst_repositories tests.unit.services.test_investigations -v

compile: ## Compile Python sources without writing source changes
	$(PYTHON) -m compileall -q $(PYTHON_PATHS)

diff-check: ## Check Git diff whitespace integrity
	git diff --check

format-check: ## Run the configured source-format checks
	@echo "No Python formatter is configured; running compile and whitespace checks instead."
	@$(MAKE) --no-print-directory compile diff-check

format: format-check ## Alias for the repository's formatting checks

check: compile format-check test ## Run compilation, formatting checks, and all tests

smoke: ## Run the provider-independent synthetic scenario smoke check
	$(PYTHON) scripts/smoke_demo.py

demo-seed: ## Generate the deterministic synthetic demo seed
	$(PYTHON) scripts/seed_demo.py --output $(DEMO_SEED)

demo-smoke: demo-seed ## Generate and validate the deterministic synthetic demo seed
	$(PYTHON) scripts/smoke_demo.py --seed-file $(DEMO_SEED)

benchmark: ## Run the reproducible local benchmark
	$(PYTHON) scripts/benchmark.py --iterations $(BENCHMARK_ITERATIONS) --output $(BENCHMARK_REPORT)

clean: clean-python clean-frontend ## Remove generated caches without deleting local checkpoints

clean-python: ## Remove Python bytecode and test caches
	find src functions data tests benchmarks -type d -name '__pycache__' -prune -exec rm -rf {} +
	find src functions data tests benchmarks -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
	rm -rf .pytest_cache .coverage htmlcov

clean-frontend: ## Remove generated Next.js build and TypeScript caches
	rm -rf client/.next client/tsconfig.tsbuildinfo

clean-runtime: ## Remove ignored local runtime state, including checkpoints
	rm -rf .local

clean-checkpoints: ## Remove only local investigation checkpoints
	rm -rf .local/checkpoints
