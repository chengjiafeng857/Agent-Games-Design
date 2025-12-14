# Migration Guide: Standard OpenAI Response API

This guide helps you migrate from the old configuration approach to the new standard OpenAI Response API with LangChain.

## What Changed?

### 1. Configuration Structure

**Old Approach:**
```python
# Manual model initialization with temperature checks
final_model = model_name or settings.planning_model
final_temp = temperature if temperature is not None else settings.planning_temperature

is_reasoning_model = any(
    prefix in final_model.lower() 
    for prefix in ["gpt-5", "o1", "o3", "o4"]
)

model_kwargs = {}
if not is_reasoning_model:
    model_kwargs["temperature"] = final_temp

self.llm = ChatOpenAI(
    model=final_model,
    api_key=settings.openai_api_key,
    output_version="responses/v1",
    use_responses_api=True if is_reasoning_model else None,
    **model_kwargs,
)
```

**New Approach:**
```python
# Clean configuration-based initialization
self.config = model_config or settings.get_planning_config()
model_kwargs = self.config.get_model_kwargs()

self.llm = ChatOpenAI(
    api_key=settings.openai_api_key,
    **model_kwargs,
)

# Optional: Bind tools if enabled
if self.config.enable_tools:
    from ..tools import get_planning_tools
    tools = get_planning_tools()
    bind_kwargs = self.config.get_bind_tools_kwargs()
    self.llm = self.llm.bind_tools(tools, **bind_kwargs)
```

### 2. Agent Initialization

**Old Approach:**
```python
# Initialize with individual parameters
planning_agent = PlanningAgent(
    model_name="gpt-5-mini",
    temperature=0.3
)

react_executor = ReActExecutor(
    model_name="gpt-5",
    temperature=0.7
)
```

**New Approach:**
```python
# Option 1: Use default configuration from settings
planning_agent = PlanningAgent()  # Uses settings.get_planning_config()
react_executor = ReActExecutor()  # Uses settings.get_react_config()

# Option 2: Provide custom configuration
from agent_games_design.config import ModelConfig

custom_config = ModelConfig(
    model_name="gpt-5",
    thinking_effort="high",
    enable_tools=True,
)

planning_agent = PlanningAgent(model_config=custom_config)
react_executor = ReActExecutor(model_config=custom_config)
```

### 3. Environment Variables

**New Variables Added:**

```env
# Thinking effort for GPT-5 models
PLANNING_THINKING_EFFORT=medium
REACT_THINKING_EFFORT=high
EVALUATION_THINKING_EFFORT=low

# Tool enablement
PLANNING_ENABLE_TOOLS=false
REACT_ENABLE_TOOLS=false
EVALUATION_ENABLE_TOOLS=false

# Max tokens (optional)
PLANNING_MAX_TOKENS=4000
REACT_MAX_TOKENS=8000
EVALUATION_MAX_TOKENS=2000

# Parallel tool calls
PLANNING_PARALLEL_TOOL_CALLS=true
REACT_PARALLEL_TOOL_CALLS=true
EVALUATION_PARALLEL_TOOL_CALLS=true

# Response API settings (now centralized)
USE_RESPONSES_API=true
OUTPUT_VERSION=responses/v1
```

## Migration Steps

### Step 1: Update Environment Variables

1. Copy the new variables from `.env.example` (if it exists) or from [CONFIGURATION.md](CONFIGURATION.md)
2. Add thinking effort settings for your GPT-5 models
3. Configure tool enablement as needed
4. Set Response API preferences

### Step 2: Update Agent Initialization Code

If you have custom code that initializes agents:

```python
# Before
from agent_games_design.agents import PlanningAgent

agent = PlanningAgent(model_name="gpt-5", temperature=0.3)

# After - Option 1 (use settings)
from agent_games_design.agents import PlanningAgent

agent = PlanningAgent()  # Uses settings.get_planning_config()

# After - Option 2 (custom config)
from agent_games_design.config import ModelConfig
from agent_games_design.agents import PlanningAgent

config = ModelConfig(
    model_name="gpt-5",
    thinking_effort="medium",
    enable_tools=False,
)
agent = PlanningAgent(model_config=config)
```

### Step 3: Update Tests

If you have custom tests, update the mock patches:

```python
# Before
@patch("agent_games_design.react_agent.planning_agent.ChatOpenAI")
def test_planning(self, mock_llm_class):
    # test code

# After
@patch("agent_games_design.agents.planning.ChatOpenAI")
def test_planning(self, mock_llm_class):
    # test code
```

### Step 4: Verify Configuration

Run a simple test to verify your configuration:

```python
from agent_games_design.config import settings

# Check planning config
planning_config = settings.get_planning_config()
print(f"Planning model: {planning_config.model_name}")
print(f"Thinking effort: {planning_config.thinking_effort}")
print(f"Tools enabled: {planning_config.enable_tools}")

# Check ReAct config
react_config = settings.get_react_config()
print(f"ReAct model: {react_config.model_name}")
print(f"Thinking effort: {react_config.thinking_effort}")
print(f"Tools enabled: {react_config.enable_tools}")
```

## Breaking Changes

### 1. Agent Constructor Signatures

**PlanningAgent:**
- Old: `__init__(model_name: Optional[str] = None, temperature: Optional[float] = None)`
- New: `__init__(model_config: Optional[ModelConfig] = None)`

**ReActExecutor:**
- Old: `__init__(model_name: Optional[str] = None, temperature: Optional[float] = None)`
- New: `__init__(model_config: Optional[ModelConfig] = None)`

### 2. Temperature Handling

- Temperature is now automatically handled based on model type
- Reasoning models (GPT-5, o-series) use `thinking_effort` instead
- Standard models (GPT-4, etc.) use `temperature`
- No need to manually check model type

### 3. Tool Binding

- Tools are now bound during initialization if `enable_tools=True`
- No need to manually call `bind_tools()` in most cases
- Tool selection is managed through configuration

## New Features

### 1. Thinking Effort Control

For GPT-5 models, you can now control reasoning depth:

```env
REACT_THINKING_EFFORT=high  # Maximum reasoning capability
```

### 2. Per-Agent Tool Configuration

Enable tools selectively:

```env
PLANNING_ENABLE_TOOLS=false   # No tools for planning
REACT_ENABLE_TOOLS=true       # Enable tools for ReAct
EVALUATION_ENABLE_TOOLS=false # No tools for evaluation
```

### 3. Centralized Response API Settings

```env
USE_RESPONSES_API=true
OUTPUT_VERSION=responses/v1
```

### 4. ModelConfig Helper Class

Encapsulates all model configuration logic:

```python
from agent_games_design.config import ModelConfig

config = ModelConfig(
    model_name="gpt-5",
    thinking_effort="high",
    enable_tools=True,
    parallel_tool_calls=True,
    max_tokens=8000,
)

# Get properly formatted kwargs for ChatOpenAI
model_kwargs = config.get_model_kwargs()

# Get kwargs for bind_tools
bind_kwargs = config.get_bind_tools_kwargs()
```

## Troubleshooting

### Issue: Agent fails to initialize

**Cause**: Missing required environment variables

**Solution**: Ensure `OPENAI_API_KEY` is set and model configurations are valid:

```bash
export OPENAI_API_KEY=sk-...
```

### Issue: "thinking_effort not recognized"

**Cause**: Using thinking_effort with non-GPT-5 models

**Solution**: Only use thinking_effort with GPT-5 models. For GPT-4, use temperature instead:

```env
# For GPT-4
PLANNING_MODEL=gpt-4o
PLANNING_TEMPERATURE=0.3
# Don't set PLANNING_THINKING_EFFORT

# For GPT-5
PLANNING_MODEL=gpt-5
PLANNING_THINKING_EFFORT=medium
# Temperature is ignored for GPT-5
```

### Issue: Tools not working

**Cause**: Tools not enabled in configuration

**Solution**: Enable tools for the specific agent:

```env
REACT_ENABLE_TOOLS=true
```

### Issue: Import errors

**Cause**: Old import paths

**Solution**: Update imports:

```python
# Old
from agent_games_design.react_agent.planning_agent import PlanningAgent

# New
from agent_games_design.agents import PlanningAgent
```

## Backward Compatibility

The new system maintains backward compatibility in these areas:

1. **Environment Variables**: Old variables (like `PLANNING_MODEL`, `PLANNING_TEMPERATURE`) still work
2. **Basic Usage**: Default initialization still works without changes
3. **Response Format**: Both v0 and responses/v1 formats are supported

However, to take advantage of new features (thinking effort, tool selection), you should migrate to the new configuration approach.

## Next Steps

1. Review the [Configuration Guide](CONFIGURATION.md) for detailed configuration options
2. Test your application with the new configuration
3. Optimize thinking effort settings for your use case
4. Consider enabling tools for enhanced agent capabilities

## Questions?

If you encounter issues during migration, please:

1. Check the [Configuration Guide](CONFIGURATION.md)
2. Review the examples in this guide
3. Verify your environment variables
4. Check the [Troubleshooting section](CONFIGURATION.md#troubleshooting)

