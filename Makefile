# Gondolin developer shortcuts.
#
# These targets wrap the most common `lake` / Python check invocations so
# developers don't have to remember every flag. None of these are required
# for CI — they exist purely for local ergonomics.
#
# Usage:
#   make            # show this help
#   make build      # lake build NN.Library
#   make test       # lake test
#   make checks     # all Python hygiene checks (matches CI hygiene job)
#   make docs       # generate API docs under .lake/build/doc/
#   make verify     # lake exe verify -- list (sanity-check the verifier registry)
#   make setup      # run scripts/dev/setup.sh (one-time toolchain setup)
#   make sbom       # generate sbom.json from lake-manifest.json
#   make clean      # lake clean

LAKE ?= lake
PYTHON ?= python3

.PHONY: help build test checks lint docs verify setup sbom clean

help:
	@awk 'BEGIN{FS=":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo

build: ## Build the curated NN.Library surface
	$(LAKE) build NN.Library

test: ## Run the curated test suite
	$(LAKE) test

lint: ## Run the Gondolin repo policy linter (Lean)
	$(LAKE) lint

checks: ## Run every Python hygiene check (mirrors CI hygiene job)
	$(PYTHON) scripts/checks/check_case_collisions.py
	$(PYTHON) scripts/checks/trust_boundaries_check.py
	$(PYTHON) scripts/checks/proof_debt.py --strict
	$(PYTHON) scripts/checks/api_surface.py --check
	$(PYTHON) scripts/checks/docs_link_check.py
	$(PYTHON) scripts/checks/docstring_coverage.py --min-coverage 80
	$(PYTHON) scripts/checks/lake_manifest_audit.py
	$(PYTHON) scripts/checks/lean_toolchain_pin.py
	$(PYTHON) scripts/checks/ci_workflow_lint.py
	$(PYTHON) scripts/checks/lean_imports_audit.py

docs: ## Generate API documentation under .lake/build/doc/
	DISABLE_EQUATIONS=1 $(LAKE) build NN:docs

verify: ## List registered verifier subcommands
	$(LAKE) exe verify -- list

setup: ## One-time developer environment setup (elan, toolchain, cache)
	bash scripts/dev/setup.sh

sbom: ## Generate a minimal SPDX SBOM as sbom.json
	$(PYTHON) scripts/release/sbom_generate.py --pretty --output sbom.json
	@echo "Wrote sbom.json"

clean: ## Remove Lake build artifacts
	$(LAKE) clean
