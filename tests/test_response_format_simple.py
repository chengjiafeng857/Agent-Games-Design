"""
Simple test for response format handling (v0 string and v1 list formats).
Run directly with: uv run python tests/test_response_format_simple.py
"""

from agent_games_design.agents import PlanningAgent, ReActExecutor


class MockResponse:
    """Mock response object for testing."""
    
    def __init__(self, content):
        self.content = content


def test_planning_agent_v0_format():
    """Test that PlanningAgent handles v0 string format."""
    print("Testing PlanningAgent v0 format...")
    agent = PlanningAgent(model_name="gpt-4o-mini")
    
    # v0 format: content is a string
    response = MockResponse(content="This is a plain string response")
    text = agent._get_response_text(response)
    
    assert isinstance(text, str), f"Expected str, got {type(text)}"
    assert text == "This is a plain string response", f"Unexpected text: {text}"
    print("✓ v0 format test passed")


def test_planning_agent_v1_format():
    """Test that PlanningAgent handles v1 list format."""
    print("Testing PlanningAgent v1 format...")
    agent = PlanningAgent(model_name="gpt-4o-mini")
    
    # v1 format: content is a list of content blocks
    response = MockResponse(content=[
        {"type": "text", "text": "Hello "},
        {"type": "text", "text": "World"},
    ])
    text = agent._get_response_text(response)
    
    assert isinstance(text, str), f"Expected str, got {type(text)}"
    assert text == "Hello \nWorld", f"Unexpected text: {text}"
    print("✓ v1 format test passed")


def test_planning_agent_v1_format_with_reasoning():
    """Test that PlanningAgent handles v1 format with reasoning blocks."""
    print("Testing PlanningAgent v1 format with reasoning...")
    agent = PlanningAgent(model_name="gpt-4o-mini")
    
    # v1 format with reasoning and text
    response = MockResponse(content=[
        {"type": "reasoning", "reasoning": "internal reasoning here"},
        {"type": "text", "text": "Final answer"},
    ])
    text = agent._get_response_text(response)
    
    assert isinstance(text, str), f"Expected str, got {type(text)}"
    assert text == "Final answer", f"Unexpected text: {text}"
    assert "reasoning" not in text, "Reasoning should be filtered out"
    print("✓ v1 format with reasoning test passed")


def test_react_executor_v0_format():
    """Test that ReActExecutor handles v0 string format."""
    print("Testing ReActExecutor v0 format...")
    executor = ReActExecutor(model_name="gpt-4o-mini")
    
    # v0 format: content is a string
    response = MockResponse(content="Thought: I need to analyze\nAction: research")
    text = executor._get_response_text(response)
    
    assert isinstance(text, str), f"Expected str, got {type(text)}"
    assert "Thought:" in text, "Missing 'Thought:' in text"
    assert "Action:" in text, "Missing 'Action:' in text"
    print("✓ ReActExecutor v0 format test passed")


def test_react_executor_v1_format():
    """Test that ReActExecutor handles v1 list format."""
    print("Testing ReActExecutor v1 format...")
    executor = ReActExecutor(model_name="gpt-4o-mini")
    
    # v1 format: content is a list of content blocks
    response = MockResponse(content=[
        {"type": "text", "text": "Thought: I need to analyze"},
        {"type": "text", "text": "\nAction: research"},
    ])
    text = executor._get_response_text(response)
    
    assert isinstance(text, str), f"Expected str, got {type(text)}"
    assert "Thought:" in text, "Missing 'Thought:' in text"
    assert "Action:" in text, "Missing 'Action:' in text"
    print("✓ ReActExecutor v1 format test passed")


def test_empty_v1_format():
    """Test handling of empty v1 format list."""
    print("Testing empty v1 format...")
    agent = PlanningAgent(model_name="gpt-4o-mini")
    
    response = MockResponse(content=[])
    text = agent._get_response_text(response)
    
    assert isinstance(text, str), f"Expected str, got {type(text)}"
    assert text == "", f"Expected empty string, got: {text}"
    print("✓ Empty v1 format test passed")


def test_mixed_v1_format():
    """Test handling of v1 format with mixed block types."""
    print("Testing mixed v1 format...")
    agent = PlanningAgent(model_name="gpt-4o-mini")
    
    response = MockResponse(content=[
        {"type": "tool_call", "id": "123", "name": "search"},
        {"type": "text", "text": "Result: "},
        {"type": "image", "url": "http://example.com/image.png"},
        {"type": "text", "text": "Analysis complete"},
    ])
    text = agent._get_response_text(response)
    
    assert isinstance(text, str), f"Expected str, got {type(text)}"
    assert "Result: " in text, "Missing 'Result: ' in text"
    assert "Analysis complete" in text, "Missing 'Analysis complete' in text"
    assert "tool_call" not in text, "tool_call should be filtered out"
    assert "image" not in text, "image should be filtered out"
    print("✓ Mixed v1 format test passed")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Response Format Handling (v0 and v1)")
    print("=" * 60)
    
    try:
        test_planning_agent_v0_format()
        test_planning_agent_v1_format()
        test_planning_agent_v1_format_with_reasoning()
        test_react_executor_v0_format()
        test_react_executor_v1_format()
        test_empty_v1_format()
        test_mixed_v1_format()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

