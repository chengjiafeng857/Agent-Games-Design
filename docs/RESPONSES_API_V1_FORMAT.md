# Responses API v1 Format Fix

## Problem

When using `output_version="responses/v1"` with LangChain's `ChatOpenAI`, the response format changed from a simple string to a list of content blocks. This caused a `TypeError` in the code:

```python
TypeError: the JSON object must be str, bytes or bytearray, not list
```

### Root Cause

**Old Format (v0 / default)**:
```python
response = llm.invoke("Hello")
response.content  # str: "Hello! How can I help you?"
```

**New Format (v1 / Responses API)**:
```python
response = llm.invoke("Hello")
response.content  # list: [{"type": "text", "text": "Hello! How can I help you?"}]
```

The code was expecting `response.content` to be a string and tried to parse it directly as JSON, but with v1, it's now a list of content blocks.

## Solution

Added a `_get_response_text()` method to both `PlanningAgent` and `ReActExecutor` that handles both formats:

```python
def _get_response_text(self, response) -> str:
    """Extract text content from response, handling both v0 and v1 formats.
    
    Args:
        response: LangChain AIMessage response
        
    Returns:
        String content from the response
    """
    # Check if content is a list (Responses API v1 format)
    if isinstance(response.content, list):
        # Extract text from content blocks
        text_parts = []
        for block in response.content:
            if isinstance(block, dict):
                # Handle v1 format with type field
                if block.get("type") == "text" and "text" in block:
                    text_parts.append(block["text"])
            elif isinstance(block, str):
                # Sometimes blocks might be plain strings
                text_parts.append(block)
        return "\n".join(text_parts)
    else:
        # Old format: content is already a string
        return str(response.content)
```

## Changes Made

### 1. `planning.py`
- Added `_get_response_text()` method
- Updated `create_plan()` to extract text before parsing JSON:
  ```python
  # Extract text content from response (handles both old and new formats)
  response_text = self._get_response_text(response)
  
  # Try to extract and parse JSON from the response
  plan_data = self._extract_json_from_response(response_text)
  ```

### 2. `react_executor.py`
- Added `_get_response_text()` method
- Updated `generate_guidelines()` to extract text before parsing:
  ```python
  # Extract text content from response (handles both old and new formats)
  response_text = self._get_response_text(response)

  # Parse the response for Thought, Action, and Observation
  thought, action, final_answer = self._parse_react_response(response_text)
  ```

### 3. Documentation
- Updated `docs/GPT5_RESPONSES_API.md` with a section on "Response Format Change"
- Created `docs/RESPONSES_API_V1_FORMAT.md` (this file)

### 4. Tests
- Created `tests/test_response_format_simple.py` with 7 test cases:
  - ✅ v0 format (string) handling
  - ✅ v1 format (list) handling
  - ✅ v1 format with reasoning blocks
  - ✅ v1 format with mixed content types
  - ✅ Empty v1 format
  - ✅ Both `PlanningAgent` and `ReActExecutor`

## Benefits of v1 Format

The new list format enables:

1. **Multiple Content Types**: Text, reasoning, tool calls, images, etc.
2. **Structured Reasoning**: Access internal reasoning from GPT-5
3. **Multimodal Responses**: Better support for images and other media
4. **Tool Call Tracking**: Separate tool calls from text responses

### Example: Accessing Reasoning

```python
response = llm.invoke("What is 3^3?")

for block in response.content:
    if block["type"] == "text":
        print("Text:", block["text"])
    elif block["type"] == "reasoning":
        print("Reasoning:", block["reasoning"])
```

## Backward Compatibility

The `_get_response_text()` method handles both formats:
- ✅ Works with v0 format (string content)
- ✅ Works with v1 format (list content)
- ✅ Filters out non-text blocks (reasoning, tool calls, images)
- ✅ Joins multiple text blocks with newlines

## Testing

Run the tests to verify the fix:

```bash
uv run python tests/test_response_format_simple.py
```

Expected output:
```
============================================================
Testing Response Format Handling (v0 and v1)
============================================================
Testing PlanningAgent v0 format...
✓ v0 format test passed
Testing PlanningAgent v1 format...
✓ v1 format test passed
Testing PlanningAgent v1 format with reasoning...
✓ v1 format with reasoning test passed
Testing ReActExecutor v0 format...
✓ ReActExecutor v0 format test passed
Testing ReActExecutor v1 format...
✓ ReActExecutor v1 format test passed
Testing empty v1 format...
✓ Empty v1 format test passed
Testing mixed v1 format...
✓ Mixed v1 format test passed

============================================================
✅ ALL TESTS PASSED!
============================================================
```

## Migration Notes

If you have custom code that accesses `response.content`:

**Before**:
```python
response = llm.invoke("Hello")
text = response.content  # Assumes string
```

**After** (for v1 compatibility):
```python
response = llm.invoke("Hello")

# Option 1: Use the helper method
text = agent._get_response_text(response)

# Option 2: Handle manually
if isinstance(response.content, list):
    text = "\n".join([
        block["text"] 
        for block in response.content 
        if block.get("type") == "text"
    ])
else:
    text = str(response.content)
```

## References

- [OpenAI Responses API Migration Guide](https://platform.openai.com/docs/guides/migrate-to-responses)
- [LangChain Responses API Support](https://docs.langchain.com/oss/python/integrations/chat/openai#responses-api)
- [GPT-5 Responses API Documentation](docs/GPT5_RESPONSES_API.md)

