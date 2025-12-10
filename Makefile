.PHONY: help install test format lint type-check quality clean

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	uv sync --extra dev

test:  ## Run tests
	uv run pytest -v

test-cov:  ## Run tests with coverage
	uv run pytest --cov=src/agent_games_design --cov-report=html --cov-report=term

format:  ## Format code with black
	uv run black src/ tests/ examples/

lint:  ## Lint code with ruff
	uv run ruff check src/ tests/ examples/

type-check:  ## Type check with mypy
	uv run mypy src/

quality: format lint type-check  ## Run all quality checks

clean:  ## Clean up generated files
	rm -rf .venv/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run-basic:  ## Run basic agent example
	uv run agent-games examples basic

run-tools:  ## Run tool usage example
	uv run agent-games examples tools

run-advanced:  ## Run advanced agent example
	uv run python examples/advanced_agent.py

cli-help:  ## Show CLI help
	uv run agent-games --help

cli-tools:  ## List available CLI tools
	uv run agent-games tools

cli-chat:  ## Start interactive chat (requires API key)
	uv run agent-games chat

run-react:  ## Run ReAct game design workflow example
	uv run python examples/react_game_design_workflow.py

cli-react:  ## Run ReAct workflow via CLI (requires API key)
	uv run agent-games react "Create a mobile puzzle game with physics mechanics"

cli-react-interactive:  ## Run ReAct workflow interactively (requires API key)
	uv run agent-games react "Create a retro platformer game" --interactive

