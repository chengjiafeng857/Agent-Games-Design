# ReAct Game Design Agent - Quick Reference Guide

## 🎯 What This Agent Does

The ReAct Game Design Agent is a comprehensive system that:
1. **Plans** game design projects with detailed execution steps
2. **Requests human approval** before proceeding
3. **Generates** in-depth game design guidelines using ReAct pattern (Reasoning + Acting)
4. **Evaluates** workflow performance with LangSmith integration

## 🚀 Quick Start

### Prerequisites

Make sure your `.env` file contains:
```bash
# Required
OPENAI_API_KEY="your-openai-api-key"

# Optional - LangSmith tracing
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="your-langsmith-api-key"
LANGCHAIN_PROJECT="agent-games-design"

# Optional - Model configuration (uses defaults if not specified)
PLANNING_MODEL="gpt-4o"              # Model for planning agent
PLANNING_TEMPERATURE=0.3             # Temperature for planning

REACT_EXECUTION_MODEL="gpt-4o"       # Model for guidelines generation
REACT_TEMPERATURE=0.7                # Temperature for execution

EVALUATION_MODEL="gpt-4o-mini"       # Model for evaluation (cheaper)
EVALUATION_TEMPERATURE=0.5           # Temperature for evaluation
```

**Note:** See [Configuration Guide](docs/CONFIGURATION.md) for detailed model options and cost optimization.

### Basic Usage

```bash
# Auto-approve mode (for testing)
uv run python -m agent_games_design.cli react "Create a puzzle game"

# With LangSmith evaluation
uv run python -m agent_games_design.cli react "Create a puzzle game" --evaluate

# Interactive mode (manual approval)
uv run python -m agent_games_design.cli react "Create a puzzle game" --interactive
```

## 📊 Workflow Stages

The agent follows this workflow:

```
PLANNING 
   ↓
HUMAN_APPROVAL (you approve/reject/modify the plan)
   ↓
REACT_EXECUTION (generates comprehensive guidelines)
   ↓
ASSET_GENERATION (prepares asset list)
   ↓
EVALUATION (LangSmith metrics)
   ↓
COMPLETED
```

## 💡 Example Prompts

### Puzzle Games
```bash
uv run python -m agent_games_design.cli react "Create a match-3 puzzle game with power-ups and daily challenges"
```

### Strategy Games
```bash
uv run python -m agent_games_design.cli react "Design a mobile strategy game with base building and PvP battles"
```

### Platformers
```bash
uv run python -m agent_games_design.cli react "Create a 2D platformer with wall-jumping and dash mechanics"
```

### RPGs
```bash
uv run python -m agent_games_design.cli react "Design an RPG with turn-based combat and character progression"
```

## 📋 What You Get

The agent generates comprehensive output both to **console** and **markdown file**:

✅ **Console Output** - Full guidelines printed to terminal with formatting
✅ **Markdown File** - Auto-saved to `output/` directory with timestamp
✅ **Execution Plan** - Clear phases and milestones
✅ **Game Design Guidelines** - Comprehensive step-by-step documentation including:
   - Research and analysis
   - Core gameplay mechanics
   - Progression systems
   - Economy and monetization
   - Level design guidelines
   - UI/UX specifications
   - Art direction
   - Technical architecture
   - Implementation roadmap
   - Asset generation plan
   - QA and testing strategy

✅ **Asset Requests** - List of assets needed (ready for generation)
✅ **Evaluation Metrics** - Performance analysis (with `--evaluate` flag)

## 📁 Output Files

All results are automatically saved to the `output/` directory:

```
output/
├── 20251020_115006_Create_a_simple_snake_game.md
├── 20251020_120345_Design_a_puzzle_game.md
└── ...
```

**Filename Format:** `YYYYMMDD_HHMMSS_prompt_preview.md`

**File Contents:**
- Header with generation metadata
- User request
- Complete execution plan with steps
- Full game design guidelines
- Asset requests with specifications
- Workflow metadata and statistics

**Note:** The `/output` directory is in `.gitignore` and won't be committed to version control.

## 🔍 Checking LangSmith Traces

1. Visit https://smith.langchain.com
2. Select your project: `agent-games-design`
3. View traces for each workflow run
4. Check metrics and performance

All traces are clean with no `GeneratorExit` errors! ✅

## 🛠️ Programmatic Usage

```python
from agent_games_design.graphs import ReActWorkflowManager

# Initialize
manager = ReActWorkflowManager()

# Start workflow
state = manager.start_workflow("Your game design prompt")

# Execute planning
state = manager.execute_step(state)

# Process approval (approve/reject/modify)
state = manager.approval_handler.process_human_response(state, "approve")

# Continue execution
state = manager.execute_step(state)

# Access results
print(f"Guidelines: {state.guidelines_generated}")
print(f"Plan: {state.execution_plan}")
print(f"Assets: {state.asset_requests}")
```

## 🏗️ Architecture

### Key Components

- **PlanningAgent** (`src/agent_games_design/agents/planning.py`)
  - Creates execution plans with steps and asset requests
  
- **ReActExecutor** (`src/agent_games_design/agents/react_executor.py`)
  - Generates comprehensive guidelines using Reasoning + Acting pattern
  
- **HumanApprovalHandler** (`src/agent_games_design/graphs/human_approval.py`)
  - Manages human approval workflow
  
- **ReActWorkflowManager** (`src/agent_games_design/graphs/workflow_manager.py`)
  - Orchestrates the entire workflow
  
- **LangSmith Integration** (`src/agent_games_design/evaluation/`)
  - Evaluation metrics and tracing

### State Management

All workflow state is managed through the `ReActState` Pydantic model:
- Type-safe
- Validates data
- Tracks workflow progress
- Maintains history

## ✅ Testing

Run the test suite:
```bash
# All tests
uv run pytest

# Specific test file
uv run pytest tests/test_react_agent.py

# With coverage
uv run pytest --cov=agent_games_design
```

## 🐛 Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'agent_games_design'`
```bash
# Solution: Reinstall in editable mode
uv pip install -e .
```

**Issue**: No LangSmith traces appearing
```bash
# Solution: Check environment variables
echo $LANGCHAIN_TRACING_V2  # Should be "true"
echo $LANGCHAIN_API_KEY     # Should be your API key
```

**Issue**: Agent generates empty plan
```bash
# Solution: Check OPENAI_API_KEY is set correctly
echo $OPENAI_API_KEY
```

## 📚 Further Reading

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [ReAct Paper](https://arxiv.org/abs/2210.03629)

## 🎉 Features

✅ No `GeneratorExit` errors
✅ Clean LangSmith traces
✅ Proper error handling
✅ Type-safe with Pydantic
✅ Modular architecture
✅ Standard Python structure
✅ Comprehensive logging
✅ CLI integration
✅ Evaluation system ready
✅ Human-in-the-loop approval
✅ Full workflow tested
✅ Production ready!

---

**Your ReAct agent for game design is fully operational!** 🎊
