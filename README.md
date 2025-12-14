# Agent Games Design

A LangGraph-based agent system for implementing detailed game execution plans, asset generation including 3d modeling, and evaluation. 

## 🎯 Features

- **LangGraph Integration**: Build stateful, multi-step agent workflows
- **GPT-5 & Responses API**: Official LangChain support for OpenAI's latest models
- **ReAct Agent System**: Advanced reasoning and acting pattern for game design
- **Modular Architecture**: Clean separation of concerns (agents, graphs, tools, state)
- **GDD Parsing**: AI-powered conversion of text GDDs to structured configs
- **AI Asset Generation**: Google Nano and multi-model support with high-quality prompts
- **Human-in-the-Loop**: Interactive planning approval and workflow control
- **LangSmith Evaluation**: Comprehensive workflow performance analysis
- **Type Safety**: Full type hints and Pydantic models
- **Code Quality**: Black, Ruff, and MyPy configured
- **CLI Interface**: Comprehensive command-line tools

## 📁 Project Structure

```
agent-games-design/
├── src/
│   └── agent_games_design/
│       ├── __init__.py
│       ├── agents/          # Agent node definitions
│       │   ├── planning.py       # Planning stage agent
│       │   ├── react_executor.py # ReAct execution agent
│       │   └── asset_generator.py # Asset generation agent
│       ├── graphs/          # LangGraph workflow definitions
│       │   ├── react_workflow.py # Main ReAct workflow
│       │   ├── human_approval.py # Approval logic
│       │   └── workflow_manager.py
│       ├── tools/           # Tools that agents can use
│       │   ├── game_analyzer.py
│       │   ├── text_analyzer.py
│       │   └── calculator.py
│       ├── state/           # State management
│       ├── utils/           # Utility functions
│       ├── evaluation/      # LangSmith evaluation logic
│       ├── cli.py           # Main CLI entry point
│       ├── config.py        # Configuration management
│       ├── config_generator.py # GDD parsing logic
│       └── logging_config.py
├── prompt_generation/       # Standalone prompt pipeline
│   ├── configs/             # Character config templates
│   ├── src/                 # Pipeline stages
│   └── generate_prompts.py  # Pipeline entry point
├── tests/                   # Test files
├── examples/                # Example scripts
├── docs/                    # Documentation
├── .env.example            
└── pyproject.toml
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
# Edit .env and add your API keys (OPENAI_API_KEY required)
```

### Command Line Interface

The project includes a comprehensive CLI for easy interaction:

```bash
# Get help
uv run agent-games --help

# interactive chat
uv run agent-games chat

# ReAct Game Design Workflow
uv run agent-games react "Create a mobile puzzle game with physics mechanics"
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

## � Character Config Generation (New)

The system can now parse unstructured **Game Design Documents (GDDs)** directly into structured configuration files for the prompt generation pipeline.

### Workflow

1. **Write GDD**: Create a text file with your character description (e.g., `my_character.txt`).
   ```text
   Name: Zylos
   Role: Cybernetic Ninja
   Style: Dark sci-fi, neon accents
   Weapons: Plasma katana on back
   ```

2. **Generate Config**: Use the `generate-config` command to convert it to YAML.
   ```bash
   uv run agent-games generate-config my_character.txt -o configs/my_character.yaml
   ```
   *The AI will automatically structure the data, verify constraints, and infer missing details.*

3. **Generate Prompts**: Use the generated config in the prompt pipeline.
   ```bash
   uv run prompt_generation/generate_prompts.py prompts -i configs/my_character.yaml
   ```

## 🏗️ ReAct Game Design Workflow

The project includes a sophisticated **ReAct (Reasoning + Acting) agent** specifically designed for game design assignments:

### Workflow Stages
1. **📋 Planning Stage**: AI creates detailed execution plans
2. **👤 Human Approval**: Interactive plan review and approval
3. **🤖 ReAct Execution**: Reasoning through game design challenges
4. **🎨 Asset Generation**: AI-generated game assets with multiple models
5. **📊 LangSmith Evaluation**: Comprehensive performance analysis

```bash
# Run ReAct workflow
uv run agent-games react "Design a retro platformer" --interactive
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

## 🔧 Configuration

See **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)** for detailed configuration options, including:
- Model selection (GPT-5, GPT-4, etc.)
- Thinking effort control
- Tool settings
- Response API integration

## 🧪 Testing & Quality

```bash
# Run tests
uv run pytest

# Format code
uv run black src/
uv run ruff check src/
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

## � Resources

- [Configuration Guide](docs/CONFIGURATION.md)
- [GPT-5 Responses API](docs/GPT5_RESPONSES_API.md)
- [Asset Generation](docs/ASSET_GENERATION.md)

### External Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Documentation](https://python.langchain.com/)
- [UV Documentation](https://github.com/astral-sh/uv)
- [LangSmith](https://smith.langchain.com/)

## 🤝 Contributing

Contributions are welcome! Please follow the code quality standards (Black, Ruff, MyPy) and add tests for new features.

## 📝 License

MIT License - feel free to use this project for your own purposes.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Package management by [uv](https://github.com/astral-sh/uv)
- Powered by [LangChain](https://github.com/langchain-ai/langchain)

---

**Happy Agent Building! 🤖**
