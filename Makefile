.PHONY: install-dev format check lint run help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install-dev: ## Install dev dependencies (black, ruff)
	uv pip install -e ".[dev]"

format: ## Format code with black
	black .

check: ## Check formatting without changing files
	black --check .
	ruff check .

lint: ## Run ruff linter
	ruff check .

run: ## Start the RAG system
	bash run.sh
