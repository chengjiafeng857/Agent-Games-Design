# GPT-5 and Reasoning Models - Important Constraints

## Overview

GPT-5 models (and o-series reasoning models like o1, o3, o4-mini) have **different constraints** compared to standard GPT-4 models. This document outlines the key differences and how to work with them.

## ⚠️ Critical Constraint: No Temperature Parameter

### The Issue
GPT-5 and reasoning models **DO NOT** support the `temperature` parameter. If you try to use it, you'll get:

```
Error code: 400 - {'error': {'message': "Unsupported parameter: 'temperature' is not supported with this model.", 'type': 'invalid_request_error', 'param': 'temperature', 'code': None}}
```

### Why?
Reasoning models use **fixed internal reasoning processes** that don't allow temperature control. The model's reasoning effort and variability are controlled through other mechanisms.

### Solution
Our code now **automatically detects reasoning models** and omits the temperature parameter:

```python
from langchain_openai import ChatOpenAI

# ✅ CORRECT - No temperature for GPT-5
llm = ChatOpenAI(
    model="gpt-5-pro",
    # temperature NOT included
    api_key=api_key,
    output_version="responses/v1",
    use_responses_api=True,
)

# ❌ WRONG - This will fail
llm = ChatOpenAI(
    model="gpt-5-pro",
    temperature=0.7,  # ❌ Not supported!
    api_key=api_key,
)
```

## Supported Parameters

### For GPT-5 Models

#### ✅ Supported Parameters
- `model` - Model name (e.g., "gpt-5-pro", "gpt-5-nano")
- `api_key` - Your OpenAI API key
- `max_tokens` - Maximum tokens to generate
- `stop` - Stop sequences
- `use_responses_api` - Enable Responses API (recommended: True)
- `output_version` - Output format version (recommended: "responses/v1")
- `reasoning` - Reasoning configuration (see below)
- `store` - Whether to store the response
- `previous_response_id` - For conversation continuity

#### ❌ Unsupported Parameters
- `temperature` - Not supported
- `top_p` - Not supported
- `frequency_penalty` - Not supported
- `presence_penalty` - Not supported

### Controlling Reasoning Behavior

Instead of `temperature`, use the `reasoning` parameter:

```python
llm = ChatOpenAI(
    model="gpt-5-pro",
    reasoning={
        "effort": "medium",  # Options: "low", "medium", "high"
        "summary": "auto",   # Options: "auto", "concise", "detailed", None
    },
    output_version="responses/v1",
)
```

**Reasoning Effort Levels:**
- `"low"` - Faster responses, less reasoning
- `"medium"` - Balanced performance
- `"high"` - Maximum reasoning, slower but more thorough

**Summary Options:**
- `"auto"` - Model decides summary detail level
- `"concise"` - Brief reasoning summary
- `"detailed"` - Full reasoning explanation
- `None` - No reasoning summary

## Model Detection

Our code automatically detects reasoning models by checking if the model name contains:
- `gpt-5` (e.g., "gpt-5-pro", "gpt-5-nano")
- `o1` (e.g., "o1", "o1-preview")
- `o3` (e.g., "o3", "o3-mini")
- `o4` (e.g., "o4-mini")

```python
# This is handled automatically in all our agent classes
is_reasoning_model = any(
    prefix in model_name.lower() 
    for prefix in ["gpt-5", "o1", "o3", "o4"]
)

if is_reasoning_model:
    # Don't include temperature
    llm = ChatOpenAI(model=model_name, ...)
else:
    # Include temperature for standard models
    llm = ChatOpenAI(model=model_name, temperature=0.7, ...)
```

## Examples

### ✅ Correct Usage

```python
# GPT-5 Pro - No temperature
llm = ChatOpenAI(
    model="gpt-5-pro",
    api_key=api_key,
    output_version="responses/v1",
    use_responses_api=True,
)

# GPT-5 with reasoning control
llm = ChatOpenAI(
    model="gpt-5-pro",
    reasoning={
        "effort": "high",
        "summary": "detailed",
    },
    output_version="responses/v1",
)

# o4-mini with reasoning
llm = ChatOpenAI(
    model="o4-mini",
    reasoning={
        "effort": "medium",
        "summary": "auto",
    },
    output_version="responses/v1",
)

# Standard model - Temperature OK
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,  # ✅ Supported for non-reasoning models
)
```

### ❌ Incorrect Usage

```python
# ❌ WRONG - Temperature not supported
llm = ChatOpenAI(
    model="gpt-5-pro",
    temperature=0.7,  # This will cause a 400 error
)

# ❌ WRONG - top_p not supported
llm = ChatOpenAI(
    model="gpt-5-nano",
    top_p=0.9,  # Not supported
)

# ❌ WRONG - Penalty parameters not supported
llm = ChatOpenAI(
    model="o4-mini",
    frequency_penalty=0.5,  # Not supported
    presence_penalty=0.5,   # Not supported
)
```

## Configuration Files

If you're setting model configuration in `.env` or config files:

```bash
# .env file
PLANNING_MODEL=gpt-5-pro
PLANNING_TEMPERATURE=0.3  # ⚠️ Will be ignored for gpt-5-pro

REACT_EXECUTION_MODEL=gpt-4o-mini
REACT_TEMPERATURE=0.5  # ✅ Will be used for gpt-4o-mini
```

Our code automatically handles this - the temperature is simply ignored for reasoning models.

## Alternative Models

If you need temperature control, consider these alternatives:

### Standard GPT-4 Models (Support Temperature)
- `gpt-4o` - Latest standard model
- `gpt-4o-mini` - Smaller, faster
- `gpt-4-turbo` - Previous generation

### When to Use Each

**Use GPT-5/Reasoning Models When:**
- You need advanced reasoning
- Complex problem-solving required
- Accuracy more important than speed
- Working on code, math, logic problems

**Use Standard GPT-4 When:**
- You need temperature control
- Creative writing tasks
- Want more randomness/variability
- Need faster responses
- Cost optimization is important

## Migration Guide

### If You're Getting Temperature Errors

1. **Check your model name**: Is it a GPT-5 or o-series model?
2. **Remove temperature**: Don't pass it to reasoning models
3. **Use reasoning parameter**: Control behavior through `reasoning` dict
4. **Or switch models**: Use `gpt-4o` if you need temperature

### Quick Fix Examples

```python
# Before (will fail with GPT-5)
llm = ChatOpenAI(
    model="gpt-5-pro",
    temperature=0.7,
)

# After - Option 1: Remove temperature
llm = ChatOpenAI(
    model="gpt-5-pro",
)

# After - Option 2: Use reasoning parameter
llm = ChatOpenAI(
    model="gpt-5-pro",
    reasoning={"effort": "medium"},
)

# After - Option 3: Switch to standard model
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7,
)
```

## References

- [OpenAI Responses API Documentation](https://platform.openai.com/docs/api-reference/responses)
- [Reasoning Models Guide](https://platform.openai.com/docs/guides/reasoning)
- [Model Comparison](https://platform.openai.com/docs/models)

## Summary

🔴 **DO NOT** use `temperature` with GPT-5, o1, o3, or o4 models  
🟢 **DO** use the `reasoning` parameter to control reasoning behavior  
🔵 **AUTOMATIC** detection in our codebase - no manual handling needed  
🟡 **ALTERNATIVE** Use GPT-4o models if you need temperature control

