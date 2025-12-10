# Quick Start Guide

Get started with the Agent Games Design system in minutes!

## Installation

```bash
# Install dependencies
uv sync --extra dev

# Copy environment template
cp .env.example .env

# Add your API keys to .env
# Edit .env and set OPENAI_API_KEY
```

## Run Examples

### Using CLI (Recommended)
```bash
# List available examples
uv run agent-games examples

# Run tool usage example
uv run agent-games examples tools
make run-tools

# Run basic agent (requires API key)
uv run agent-games examples basic
make run-basic

# Interactive chat (requires API key)
uv run agent-games chat
make cli-chat
```

### Direct Python Execution
```bash
# Tool usage (no API key required)
uv run python examples/tool_usage.py

# Basic agent (requires API key)
uv run python examples/basic_agent.py

# Advanced agent (requires API key)
uv run python examples/advanced_agent.py
make run-advanced
```

## Testing

```bash
# Run tests
make test

# Run tests with coverage
make test-cov
```

## Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Type check
make type-check

# Run all quality checks
make quality
```

## Project Structure

```
agent-games-design/
├── src/agent_games_design/  # Main package
│   ├── agents/             # Agent definitions
│   ├── graphs/             # LangGraph workflows
│   ├── tools/              # Agent tools
│   ├── state/              # State management
│   └── utils/              # Utilities
├── tests/                   # Tests
├── examples/               # Example scripts
└── config/                 # Configuration
```

## CLI Usage

The project includes a powerful command-line interface:

```bash
# Show help and available commands
uv run agent-games --help
make cli-help

# List available tools
uv run agent-games tools
make cli-tools

# Run a single query (requires API key)
uv run agent-games run "Calculate 15 * 23 + 47"

# Start interactive chat (requires API key)
uv run agent-games chat
make cli-chat
```

## Next Steps

1. **Customize the Agent**: Edit `src/agent_games_design/agents/__init__.py`
2. **Add Tools**: Add new tools in `src/agent_games_design/tools/__init__.py`
3. **Modify the Graph**: Edit the workflow in `src/agent_games_design/graphs/__init__.py`
4. **Extend the State**: Add fields to `AgentState` in `src/agent_games_design/state/__init__.py`
5. **Use the CLI**: Interact with agents via `uv run agent-games`

## Docker Usage

```bash
# Build and run with docker-compose
docker-compose up agent-games

# Development mode
docker-compose up dev
```

## Documentation

See [README.md](README.md) for complete documentation.

