# Configuration Guide

This document explains how to configure the Agent Games Design system using environment variables and the OpenAI Responses API.

## Table of Contents

- [Overview](#overview)
- [API Keys](#api-keys)
- [Model Configuration](#model-configuration)
- [Thinking Effort](#thinking-effort)
- [Tool Use](#tool-use)
- [Response API Settings](#response-api-settings)
- [Agent-Specific Configuration](#agent-specific-configuration)
- [Examples](#examples)

## Overview

The Agent Games Design system uses a hierarchical configuration approach:

1. **Default Settings**: Defined in `config.py`
2. **Environment Variables**: Override defaults via `.env` file
3. **Runtime Configuration**: Can be customized programmatically via `ModelConfig`

All settings are managed through the `Settings` class in `src/agent_games_design/config.py`.

## API Keys

### Required

```env
OPENAI_API_KEY=your-openai-api-key-here
```

### Optional

```env
ANTHROPIC_API_KEY=your-anthropic-api-key-here
LANGCHAIN_API_KEY=your-langsmith-api-key-here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=agent-games-design
```

## Model Configuration

### Supported Models

The system supports the following OpenAI models:

- **GPT-5 Series** (Reasoning Models):
  - `gpt-5`: Latest GPT-5 model
  - `gpt-5-mini`: Faster, cost-effective GPT-5 variant
  - `gpt-5-chat-latest`: Chat-optimized GPT-5

- **GPT-4 Series**:
  - `gpt-4o`: GPT-4 Omni
  - `gpt-4o-mini`: Smaller GPT-4 Omni
  - `gpt-4-turbo`: GPT-4 Turbo

- **O-Series** (Reasoning Models):
  - `o1`, `o3`, `o4-*`: Advanced reasoning models

### Reasoning Models vs Standard Models

**Reasoning Models** (GPT-5, o-series) have special characteristics:

- Do NOT support `temperature` parameter
- Support `thinking_effort` parameter instead (low, medium, high)
- Automatically use OpenAI Responses API
- Designed for complex reasoning tasks

**Standard Models** (GPT-4, etc.):

- Support `temperature` parameter (0.0 - 2.0)
- Do NOT support `thinking_effort`
- Can optionally use Responses API

## Thinking Effort

**⚠️ NOTE: Currently Not Supported by OpenAI API**

The `thinking_effort` parameter is included in the configuration for future use but is **not currently passed to the OpenAI API** as it's not yet officially supported by OpenAI or LangChain.

GPT-5 and o-series reasoning models automatically handle reasoning optimization without explicit effort control parameters.

### Configuration (For Future Use)

You can still set these values in your `.env` file for when support is added:

- `low`: Faster, less resource-intensive reasoning
- `medium`: Balanced performance (default for most tasks)
- `high`: Maximum reasoning capability (recommended for complex tasks)

### When Support is Added

| Effort | Use Case | Example |
|--------|----------|---------|
| `low` | Simple evaluations, quick decisions | Evaluation agent |
| `medium` | Structured planning, moderate complexity | Planning agent |
| `high` | Complex reasoning, creative tasks | ReAct execution agent |

**Current Behavior:** All GPT-5 and o-series models use their default reasoning behavior regardless of the `thinking_effort` setting.

## Tool Use

Each agent can be configured to use tools:

```env
# Enable tools for planning agent
PLANNING_ENABLE_TOOLS=true
PLANNING_PARALLEL_TOOL_CALLS=true

# Enable tools for ReAct agent
REACT_ENABLE_TOOLS=true
REACT_PARALLEL_TOOL_CALLS=true

# Enable tools for evaluation agent
EVALUATION_ENABLE_TOOLS=true
EVALUATION_PARALLEL_TOOL_CALLS=true
```

### Available Tools

- **Planning Agent**: `game_design_analyzer`, `text_analyzer`
- **ReAct Agent**: All tools (calculator, text_analyzer, game_design_analyzer)
- **Evaluation Agent**: Analysis tools (text_analyzer, game_design_analyzer, calculator)

## Response API Settings

The system uses OpenAI's Responses API for improved output handling:

```env
# Enable Responses API (recommended)
USE_RESPONSES_API=true

# Output format version
OUTPUT_VERSION=responses/v1  # or "v0" for legacy format
```

### Benefits of Responses API v1

- Better structured outputs
- Improved error handling
- Native support for reasoning models
- Consistent content formatting

## Agent-Specific Configuration

### Planning Agent

Responsible for creating execution plans.

```env
PLANNING_MODEL=gpt-5-mini
PLANNING_TEMPERATURE=0.3
PLANNING_THINKING_EFFORT=medium
PLANNING_ENABLE_TOOLS=false
PLANNING_MAX_TOKENS=4000
PLANNING_PARALLEL_TOOL_CALLS=true
```

**Recommended Settings**:
- Lower temperature (0.3) for structured output
- Medium thinking effort for balanced planning
- Tools optional (enable for enhanced analysis)

### ReAct Execution Agent

Executes ReAct (Reasoning + Acting) workflow for guideline generation.

```env
REACT_EXECUTION_MODEL=gpt-5
REACT_TEMPERATURE=0.7
REACT_THINKING_EFFORT=high
REACT_ENABLE_TOOLS=false
REACT_MAX_TOKENS=8000
REACT_PARALLEL_TOOL_CALLS=true
```

**Recommended Settings**:
- Higher temperature (0.7) for creative output
- High thinking effort for complex reasoning
- Tools optional (enable for enhanced capabilities)

### Evaluation Agent

Evaluates workflow performance.

```env
EVALUATION_MODEL=gpt-5-mini
EVALUATION_TEMPERATURE=0.5
EVALUATION_THINKING_EFFORT=low
EVALUATION_ENABLE_TOOLS=false
EVALUATION_MAX_TOKENS=2000
EVALUATION_PARALLEL_TOOL_CALLS=true
```

**Recommended Settings**:
- Moderate temperature (0.5)
- Low thinking effort (evaluation is straightforward)
- Tools optional

## Examples

### Example 1: High-Quality Production Setup

```env
# API Keys
OPENAI_API_KEY=sk-...

# Use GPT-5 for all agents
PLANNING_MODEL=gpt-5
PLANNING_THINKING_EFFORT=medium

REACT_EXECUTION_MODEL=gpt-5
REACT_THINKING_EFFORT=high

EVALUATION_MODEL=gpt-5
EVALUATION_THINKING_EFFORT=low

# Enable Responses API
USE_RESPONSES_API=true
OUTPUT_VERSION=responses/v1
```

### Example 2: Cost-Effective Setup

```env
# API Keys
OPENAI_API_KEY=sk-...

# Use gpt-5-mini for cost savings
PLANNING_MODEL=gpt-5-mini
PLANNING_THINKING_EFFORT=low

REACT_EXECUTION_MODEL=gpt-5-mini
REACT_THINKING_EFFORT=medium

EVALUATION_MODEL=gpt-5-mini
EVALUATION_THINKING_EFFORT=low

# Enable Responses API
USE_RESPONSES_API=true
OUTPUT_VERSION=responses/v1
```

### Example 3: Tool-Enabled Setup

```env
# API Keys
OPENAI_API_KEY=sk-...

# Enable tools for enhanced capabilities
PLANNING_ENABLE_TOOLS=true
REACT_ENABLE_TOOLS=true
EVALUATION_ENABLE_TOOLS=true

# Use GPT-5 models
PLANNING_MODEL=gpt-5-mini
REACT_EXECUTION_MODEL=gpt-5
EVALUATION_MODEL=gpt-5-mini

# Thinking efforts
PLANNING_THINKING_EFFORT=medium
REACT_THINKING_EFFORT=high
EVALUATION_THINKING_EFFORT=low
```

### Example 4: Legacy GPT-4 Setup

```env
# API Keys
OPENAI_API_KEY=sk-...

# Use GPT-4 models (no thinking_effort support)
PLANNING_MODEL=gpt-4o-mini
PLANNING_TEMPERATURE=0.3

REACT_EXECUTION_MODEL=gpt-4o
REACT_TEMPERATURE=0.7

EVALUATION_MODEL=gpt-4o-mini
EVALUATION_TEMPERATURE=0.5

# Responses API works with GPT-4 too
USE_RESPONSES_API=true
OUTPUT_VERSION=responses/v1
```

## Programmatic Configuration

You can also configure models programmatically:

```python
from agent_games_design.config import ModelConfig, settings
from agent_games_design.agents import PlanningAgent, ReActExecutor

# Create custom configuration
custom_config = ModelConfig(
    model_name="gpt-5",
    thinking_effort="high",
    enable_tools=True,
    parallel_tool_calls=True,
)

# Use with agents
planning_agent = PlanningAgent(model_config=custom_config)
react_executor = ReActExecutor(model_config=custom_config)

# Or use settings defaults
planning_agent = PlanningAgent()  # Uses settings.get_planning_config()
react_executor = ReActExecutor()  # Uses settings.get_react_config()
```

## Best Practices

1. **Use GPT-5 for reasoning tasks**: The ReAct agent benefits most from GPT-5's reasoning capabilities.

2. **Optimize thinking effort**: 
   - Use `high` for creative/complex tasks (ReAct)
   - Use `medium` for structured tasks (Planning)
   - Use `low` for simple evaluations

3. **Enable tools selectively**: Tools add overhead. Enable only when needed for enhanced capabilities.

4. **Monitor costs**: GPT-5 with high thinking effort is powerful but expensive. Use gpt-5-mini where appropriate.

5. **Use Responses API v1**: It's the recommended format for new applications and works best with reasoning models.

6. **Test configurations**: Different tasks may benefit from different settings. Test to find optimal values.

## Troubleshooting

### Issue: "temperature not supported for reasoning models"

**Solution**: Remove or comment out temperature settings for GPT-5/o-series models. Use `thinking_effort` instead.

### Issue: "thinking_effort not recognized"

**Solution**: `thinking_effort` only works with GPT-5 models. For GPT-4, use `temperature` instead.

### Issue: Tools not working

**Solution**: Make sure `ENABLE_TOOLS=true` for the specific agent and verify tools are properly imported.

### Issue: Response format errors

**Solution**: Ensure you're using `OUTPUT_VERSION=responses/v1` and `USE_RESPONSES_API=true`.

## References

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
