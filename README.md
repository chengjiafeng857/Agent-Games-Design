# Agent Games Design

A LangGraph-based agent system for designing and implementing AI-powered game agents. This project provides a well-structured foundation for building complex agent workflows using LangGraph, LangChain, and modern Python development practices.

## 🎯 Features

- **LangGraph Integration**: Build stateful, multi-step agent workflows
- **GPT-5 & Responses API**: Official LangChain support for OpenAI's latest models
- **ReAct Agent System**: Advanced reasoning and acting pattern for game design
- **Modular Architecture**: Clean separation of concerns (agents, graphs, tools, state)
- **AI Asset Generation**: Google Nano and multi-model support with high-quality prompts
- **Human-in-the-Loop**: Interactive planning approval and workflow control
- **LangSmith Evaluation**: Comprehensive workflow performance analysis
- **Type Safety**: Full type hints and Pydantic models
- **Testing**: Pytest setup with async support
- **Code Quality**: Black, Ruff, and MyPy configured
- **CLI Interface**: Comprehensive command-line tools
- **Examples**: Ready-to-run examples for quick start
- **Environment Management**: Using modern `uv` package manager

## 📁 Project Structure

```
agent-games-design/
├── src/
│   └── agent_games_design/
│       ├── __init__.py
│       ├── agents/          # Basic agent node definitions
│       │   └── __init__.py
│       ├── graphs/          # Simple LangGraph workflows
│       │   └── __init__.py
│       ├── tools/           # Tools that agents can use
│       │   └── __init__.py
│       ├── state/           # Basic state management
│       │   └── __init__.py
│       ├── utils/           # Utility functions
│       │   └── __init__.py
│       ├── react_agent/     # Advanced ReAct agent system
│       │   ├── __init__.py
│       │   ├── state.py     # ReAct state management
│       │   ├── planning_agent.py    # Planning stage agent
│       │   ├── human_approval.py   # Human approval system
│       │   ├── react_executor.py   # ReAct pattern execution
│       │   ├── asset_generator.py  # AI asset generation
│       │   ├── prompt_templates.py # High-quality prompts
│       │   ├── evaluation.py       # LangSmith evaluation
│       │   ├── workflow.py         # Complete workflow
│       │   └── cli_integration.py  # CLI integration
│       ├── config.py        # Configuration management
│       ├── logging_config.py # Logging setup
│       └── cli.py           # Command-line interface
├── tests/                   # Test files
│   ├── __init__.py
│   ├── test_tools.py
│   └── test_state.py
├── examples/                # Example scripts
│   ├── basic_agent.py
│   └── tool_usage.py
├── config/                  # Configuration files
├── .env.example            # Environment variables template
├── .gitignore
├── pyproject.toml
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- `uv` package manager ([install here](https://github.com/astral-sh/uv))

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd agent-games-design
```

2. Install dependencies using `uv`:
```bash
uv sync --extra dev
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

### Command Line Interface

The project includes a comprehensive CLI for easy interaction:

```bash
# Get help
uv run agent-games --help

# List available tools
uv run agent-games tools

# Run examples
uv run agent-games examples
uv run agent-games examples tools
uv run agent-games examples basic

# Interactive chat (requires API key)
uv run agent-games chat

# Run single query (requires API key)
uv run agent-games run "What is 2 + 2?"

# ReAct Game Design Workflow (requires API key)
uv run agent-games react "Create a mobile puzzle game with physics mechanics"
uv run agent-games react "Design a retro platformer" --interactive
```

### Running Examples

**Using CLI (Recommended):**
```bash
uv run agent-games examples tools    # Tool demonstration
uv run agent-games examples basic    # Basic agent (requires API key)
```

**Direct Python execution:**
```bash
uv run python examples/basic_agent.py
uv run python examples/tool_usage.py
uv run python examples/advanced_agent.py
uv run python examples/react_game_design_workflow.py  # Full ReAct demo
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
ANTHROPIC_API_KEY=your_anthropic_api_key_here
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=agent-games-design
DEFAULT_MODEL=gpt-4o-mini
TEMPERATURE=0.7
```

### LangSmith Integration (Optional)

For debugging and monitoring your agents:

1. Sign up for [LangSmith](https://smith.langchain.com/)
2. Get your API key
3. Set environment variables:
```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_api_key
LANGCHAIN_PROJECT=agent-games-design
```

## 🏗️ ReAct Game Design Workflow

The project includes a sophisticated **ReAct (Reasoning + Acting) agent** specifically designed for game design assignments:

### 🎯 Workflow Stages

1. **📋 Planning Stage**: AI creates detailed execution plans
2. **👤 Human Approval**: Interactive plan review and approval
3. **🤖 ReAct Execution**: Reasoning through game design challenges
4. **🎨 Asset Generation**: AI-generated game assets with multiple models
5. **📊 LangSmith Evaluation**: Comprehensive performance analysis

### 🚀 Quick Start with ReAct

```bash
# Run ReAct workflow via CLI
uv run agent-games react "Create a mobile puzzle game"

# Interactive mode with human approval
uv run agent-games react "Design a platformer game" --interactive

# Run the comprehensive example
uv run python examples/react_game_design_workflow.py
```

### 🎨 Asset Generation Models

- **Google Nano**: Primary model for fast, efficient generation
- **DALL-E 3**: High-quality photorealistic images  
- **Midjourney**: Artistic and stylized images
- **Stable Diffusion**: Customizable open-source generation
- **Adobe Firefly**: Commercial-safe creative AI

### 📊 Evaluation Metrics

- Plan Quality Score
- ReAct Execution Performance
- Asset Generation Quality
- Guidelines Completeness
- Workflow Efficiency
- Error Handling

## 🏗️ Building Custom Agents

For simple agents, use the basic system:

### 1. Define State

```python
from typing import Annotated, TypedDict
from langgraph.graph import add_messages

class MyState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    # Add custom fields
```

### 2. Create Agent Nodes

```python
def my_agent(state: MyState) -> MyState:
    # Your agent logic
    return state
```

### 3. For Game Design Projects

Use the ReAct system for comprehensive game design workflows:

```python
from agent_games_design.react_agent import ReActWorkflowManager

manager = ReActWorkflowManager()
state = manager.start_workflow("Create a strategy game")
```

## 🧪 Testing

Run all tests:
```bash
uv run pytest
```

Run with coverage:
```bash
uv run pytest --cov=src/agent_games_design --cov-report=html
```

Run specific test file:
```bash
uv run pytest tests/test_tools.py
```

## 🎨 Code Quality

### Format code with Black:
```bash
uv run black src/ tests/ examples/
```

### Lint with Ruff:
```bash
uv run ruff check src/ tests/ examples/
```

### Type check with MyPy:
```bash
uv run mypy src/
```

### Run all quality checks:
```bash
uv run black src/ tests/ examples/ && \
uv run ruff check src/ tests/ examples/ && \
uv run mypy src/
```

## 📚 Key Concepts

### LangGraph
LangGraph is a library for building stateful, multi-actor applications with LLMs. Key concepts:

- **State**: Shared data structure passed between nodes
- **Nodes**: Individual processing steps (agents, tools, etc.)
- **Edges**: Connections between nodes
- **Graphs**: Complete workflow definition

### Agent State
The `AgentState` is the shared state that flows through your graph:
- `messages`: Conversation history (automatically merged)
- `current_task`: The current task being worked on
- `iterations`: Track how many times the agent has run
- `final_output`: The final result

### Checkpointing
LangGraph supports saving and resuming agent state, useful for:
- Long-running processes
- Error recovery
- Human-in-the-loop workflows

## 🛠️ Development

### Adding Dependencies

Add a new dependency:
```bash
uv add package-name
```

Add a dev dependency:
```bash
uv add --dev package-name
```

### Project Management

Update dependencies:
```bash
uv lock
```

Sync environment with lockfile:
```bash
uv sync
```

### Docker Support

Build and run with Docker:
```bash
# Build image
docker build -t agent-games-design .

# Run with docker-compose
docker-compose up agent-games

# Development mode with hot reloading
docker-compose up dev
```

### Continuous Integration

The project includes GitHub Actions for:
- **Testing**: Automated test runs on Python 3.11 and 3.12
- **Code Quality**: Linting with Ruff, formatting with Black, type checking with MyPy
- **Security**: Safety checks for known vulnerabilities
- **Coverage**: Code coverage reporting with Codecov

### CLI Development

The CLI is defined in `src/agent_games_design/cli.py` and provides:
- Interactive chat sessions
- Single query execution  
- Tool listing and usage
- Example scenarios
- Configurable logging

## ⚙️ Configuration

The system uses a flexible configuration approach with support for:

- **Multiple Model Types**: GPT-5, GPT-4, o-series reasoning models
- **Thinking Effort Control**: Adjust reasoning depth (low, medium, high) for GPT-5 models
- **Tool Selection**: Enable/disable tools for each agent type
- **Response API Integration**: Native OpenAI Responses API support
- **Agent-Specific Settings**: Customize each agent (Planning, ReAct, Evaluation) independently

### Quick Configuration Example

```env
# Basic Setup
OPENAI_API_KEY=sk-...

# Planning Agent - Structured output
PLANNING_MODEL=gpt-5-mini
PLANNING_THINKING_EFFORT=medium
PLANNING_ENABLE_TOOLS=false

# ReAct Agent - Complex reasoning
REACT_EXECUTION_MODEL=gpt-5
REACT_THINKING_EFFORT=high
REACT_ENABLE_TOOLS=false

# Evaluation Agent - Quick evaluation
EVALUATION_MODEL=gpt-5-mini
EVALUATION_THINKING_EFFORT=low
EVALUATION_ENABLE_TOOLS=false

# Response API Settings
USE_RESPONSES_API=true
OUTPUT_VERSION=responses/v1
```

### Detailed Configuration Guide

For comprehensive configuration documentation, see **[CONFIGURATION.md](docs/CONFIGURATION.md)** which covers:

- Model selection and capabilities
- Thinking effort optimization
- Tool use configuration
- Response API settings
- Best practices and examples
- Troubleshooting

## 📖 Resources

### Official Documentation

- [Configuration Guide](docs/CONFIGURATION.md) - Detailed configuration options
- [GPT-5 Responses API](docs/GPT5_RESPONSES_API.md) - Responses API integration
- [Asset Generation](docs/ASSET_GENERATION.md) - AI asset generation guide

### External Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Documentation](https://python.langchain.com/)
- [UV Documentation](https://github.com/astral-sh/uv)
- [LangSmith](https://smith.langchain.com/)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run code quality checks
6. Submit a pull request

## 📝 License

MIT License - feel free to use this project for your own purposes.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Package management by [uv](https://github.com/astral-sh/uv)
- Powered by [LangChain](https://github.com/langchain-ai/langchain)

---

**Happy Agent Building! 🤖**

