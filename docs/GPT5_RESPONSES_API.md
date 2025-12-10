# GPT-5 and Responses API Integration

## Overview

This project now uses **official LangChain support** for OpenAI's GPT-5 models and the Responses API. The custom `gpt5_pro_client.py` has been removed in favor of the native `ChatOpenAI` implementation.

## What Changed

### Before (Custom Implementation)
```python
from .gpt5_pro_client import create_gpt5_pro_compatible_llm

llm = create_gpt5_pro_compatible_llm(
    model_name="gpt-5-pro",
    temperature=0.3,  # ⚠️ Not supported by GPT-5!
    api_key=api_key,
)
```

### After (Official LangChain Support)
```python
from langchain_openai import ChatOpenAI

# ⚠️ IMPORTANT: GPT-5 models don't support temperature parameter
llm = ChatOpenAI(
    model="gpt-5-pro",
    # temperature NOT included (not supported by reasoning models)
    api_key=api_key,
    # Use the new output format for Responses API (recommended for new apps)
    output_version="responses/v1",
    # Enable Responses API for GPT-5 models
    use_responses_api=True,
)
```

### Important Constraint

**⚠️ GPT-5 and reasoning models (o1, o3, o4) DO NOT support the `temperature` parameter.**

If you try to use temperature, you'll get:
```
Error 400: 'temperature' is not supported with this model
```

Our code automatically detects reasoning models and omits the temperature parameter. See `docs/GPT5_CONSTRAINTS.md` for full details and alternatives.

### Response Format Change

**⚠️ IMPORTANT**: With `output_version="responses/v1"`, the response format has changed:

**Old Format (v0)**:
```python
response = llm.invoke("Hello")
content = response.content  # str: "Hello! How can I help you?"
```

**New Format (v1)**:
```python
response = llm.invoke("Hello")
content = response.content  # list: [{"type": "text", "text": "Hello! How can I help you?"}]
```

**To extract text from v1 responses**:
```python
def get_response_text(response) -> str:
    """Extract text content from response, handling both v0 and v1 formats."""
    if isinstance(response.content, list):
        # v1 format: content is a list of blocks
        text_parts = []
        for block in response.content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block["text"])
        return "\n".join(text_parts)
    else:
        # v0 format: content is a string
        return str(response.content)
```

This format change enables:
- Multiple content types (text, reasoning, tool calls, images)
- Structured reasoning output from GPT-5
- Better support for multimodal responses

## Benefits of the Official Implementation

1. **Better Performance**: 3% improvement in SWE-bench with same prompt and setup
2. **Agentic by Default**: Built-in tools like web search, file search, code interpreter
3. **Lower Costs**: 40-80% improvement in cache utilization
4. **Stateful Context**: Use `store: true` to maintain state from turn to turn
5. **Native Support**: No custom client maintenance needed
6. **Future-Proof**: Automatically supports new features as they're released

## Responses API Features

### Built-in Tools
- **Web Search**: Real-time information retrieval
- **File Search**: Vector-based document search
- **Code Interpreter**: Sandboxed code execution
- **Computer Use**: UI automation capabilities
- **Image Generation**: DALL-E integration
- **Remote MCP**: Model Context Protocol support

### Conversation State Management
```python
# First message
response = llm.invoke("Hi, I'm Bob.")

# Continue conversation using previous response ID
second_response = llm.invoke(
    "What is my name?",
    previous_response_id=response.response_metadata["id"],
)
```

### Reasoning Output
```python
llm = ChatOpenAI(
    model="gpt-5-nano",
    reasoning={
        "effort": "medium",  # 'low', 'medium', or 'high'
        "summary": "auto",   # 'detailed', 'auto', or None
    },
    output_version="responses/v1",
)

response = llm.invoke("What is 3^3?")

# Access reasoning summary
for block in response.content:
    if block["type"] == "reasoning":
        for summary in block["summary"]:
            print(summary["text"])
```

## Migration Guide

### Package Requirements
Updated `langchain-openai` to `>=0.3.30` for full Responses API support:

```toml
dependencies = [
    "langchain-openai>=0.3.30",
    # ... other dependencies
]
```

### Configuration
No changes needed to your `.env` file. The same `OPENAI_API_KEY` works with both APIs.

### Model Names
All GPT-5 model variants are supported:
- `gpt-5-pro`
- `gpt-5-nano`
- `gpt-5-chat-latest`
- `o1`, `o3`, `o4-mini` (reasoning models)

### Automatic Detection
LangChain automatically routes to the Responses API when:
- Model name contains "gpt-5"
- Using reasoning parameters
- Using built-in tools (web search, file search, etc.)
- Using conversation state management

## Advanced Features

### Tool Calling with Strict Mode
```python
from pydantic import BaseModel

class GetWeather(BaseModel):
    """Get the current weather in a given location"""
    location: str

llm_with_tools = llm.bind_tools([GetWeather], strict=True)
response = llm_with_tools.invoke("What's the weather in SF?")
```

### Streaming with Usage Metadata
```python
llm = ChatOpenAI(
    model="gpt-5-nano",
    stream_usage=True,  # Include token usage in stream
)

for chunk in llm.stream("Tell me about chess"):
    print(chunk.content, end="", flush=True)
```

### Structured Output
```python
class GameDesign(BaseModel):
    """A game design document"""
    title: str
    genre: str
    description: str

structured_llm = llm.with_structured_output(
    GameDesign,
    strict=True,  # Enforce schema
)

result = structured_llm.invoke("Design a space exploration game")
# result is a validated GameDesign instance
```

## References

- [OpenAI Responses API Docs](https://platform.openai.com/docs/guides/migrate-to-responses)
- [LangChain ChatOpenAI Docs](https://python.langchain.com/docs/integrations/chat/openai/)
- [LangChain Responses API Support](https://docs.langchain.com/oss/python/integrations/chat/openai#responses-api)

## Support

For issues or questions about the Responses API integration:
1. Check the [LangChain documentation](https://docs.langchain.com/)
2. Review [OpenAI's migration guide](https://platform.openai.com/docs/guides/migrate-to-responses)
3. Open an issue in the project repository

