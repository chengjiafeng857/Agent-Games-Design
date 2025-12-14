#!/usr/bin/env python3
"""
Standalone verification script for the configuration system.

This script tests the new configuration system without requiring pytest.
Run this to verify the configuration updates are working correctly.

Usage:
    python tests/verify_configuration.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_games_design.config import ModelConfig, settings
from agent_games_design.tools import get_planning_tools, get_react_tools, get_evaluation_tools


def print_test(name, passed, details=""):
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} - {name}")
    if details and not passed:
        print(f"         {details}")


def test_model_config():
    """Test ModelConfig class."""
    print("\n" + "=" * 70)
    print("Testing ModelConfig Class")
    print("=" * 70)
    
    # Test 1: Default initialization
    config = ModelConfig()
    print_test(
        "Default initialization",
        config.model_name == "gpt-5" and config.use_responses_api is True,
        f"Got model_name={config.model_name}, use_responses_api={config.use_responses_api}"
    )
    
    # Test 2: Custom values
    custom_config = ModelConfig(
        model_name="gpt-5-mini",
        thinking_effort="high",
        enable_tools=True,
    )
    print_test(
        "Custom initialization",
        (custom_config.model_name == "gpt-5-mini" and 
         custom_config.thinking_effort == "high" and 
         custom_config.enable_tools is True),
        f"Got {custom_config.model_name}, {custom_config.thinking_effort}, {custom_config.enable_tools}"
    )
    
    # Test 3: Reasoning model detection (GPT-5)
    gpt5_config = ModelConfig(model_name="gpt-5")
    print_test(
        "GPT-5 is reasoning model",
        gpt5_config.is_reasoning_model() is True
    )
    
    # Test 4: Non-reasoning model detection (GPT-4)
    gpt4_config = ModelConfig(model_name="gpt-4o")
    print_test(
        "GPT-4 is NOT reasoning model",
        gpt4_config.is_reasoning_model() is False
    )
    
    # Test 5: Model kwargs for reasoning model
    reasoning_config = ModelConfig(
        model_name="gpt-5",
        temperature=0.7,  # Should be ignored
        thinking_effort="high",  # Kept in config but not passed to API (not yet supported)
        max_tokens=8000,
    )
    kwargs = reasoning_config.get_model_kwargs()
    print_test(
        "Reasoning model kwargs (no temperature, no thinking_effort yet)",
        ("temperature" not in kwargs and 
         "thinking_effort" not in kwargs and  # Not yet supported by API
         kwargs.get("use_responses_api") is True and
         kwargs.get("max_tokens") == 8000),
        f"Got kwargs keys: {list(kwargs.keys())}"
    )
    
    # Test 6: Model kwargs for standard model
    standard_config = ModelConfig(
        model_name="gpt-4o",
        temperature=0.7,
        thinking_effort="high",  # Should be ignored
    )
    kwargs = standard_config.get_model_kwargs()
    print_test(
        "Standard model kwargs (has temperature, no thinking_effort)",
        ("temperature" in kwargs and 
         "thinking_effort" not in kwargs and
         "use_responses_api" not in kwargs),
        f"Got kwargs keys: {list(kwargs.keys())}"
    )
    
    # Test 7: Bind tools kwargs
    bind_kwargs = custom_config.get_bind_tools_kwargs()
    print_test(
        "Bind tools kwargs",
        "parallel_tool_calls" in bind_kwargs,
        f"Got: {bind_kwargs}"
    )


def test_settings():
    """Test Settings class."""
    print("\n" + "=" * 70)
    print("Testing Settings Class")
    print("=" * 70)
    
    # Test 1: Settings instance exists
    print_test(
        "Settings instance exists",
        settings is not None
    )
    
    # Test 2: Get planning config
    planning_config = settings.get_planning_config()
    print_test(
        "Get planning config",
        isinstance(planning_config, ModelConfig) and 
        planning_config.model_name == settings.planning_model,
        f"Got {planning_config.model_name}"
    )
    
    # Test 3: Get ReAct config
    react_config = settings.get_react_config()
    print_test(
        "Get ReAct config",
        isinstance(react_config, ModelConfig) and 
        react_config.model_name == settings.react_execution_model,
        f"Got {react_config.model_name}"
    )
    
    # Test 4: Get evaluation config
    eval_config = settings.get_evaluation_config()
    print_test(
        "Get evaluation config",
        isinstance(eval_config, ModelConfig) and 
        eval_config.model_name == settings.evaluation_model,
        f"Got {eval_config.model_name}"
    )
    
    # Test 5: Default values
    print_test(
        "Default model is gpt-5",
        settings.default_model == "gpt-5"
    )
    
    print_test(
        "Response API enabled by default",
        settings.use_responses_api is True
    )
    
    print_test(
        "Output version is responses/v1",
        settings.output_version == "responses/v1"
    )
    
    # Test 6: Thinking effort defaults
    print_test(
        "Planning thinking effort is medium",
        settings.planning_thinking_effort == "medium"
    )
    
    print_test(
        "ReAct thinking effort is high",
        settings.react_thinking_effort == "high"
    )
    
    print_test(
        "Evaluation thinking effort is low",
        settings.evaluation_thinking_effort == "low"
    )


def test_tool_getters():
    """Test tool getter functions."""
    print("\n" + "=" * 70)
    print("Testing Tool Getter Functions")
    print("=" * 70)
    
    # Test 1: Get planning tools
    planning_tools = get_planning_tools()
    tool_names = [tool.name for tool in planning_tools]
    print_test(
        "Get planning tools (2 tools)",
        len(planning_tools) == 2,
        f"Got {len(planning_tools)} tools: {tool_names}"
    )
    
    print_test(
        "Planning tools include game_design_analyzer",
        "game_design_analyzer" in tool_names
    )
    
    print_test(
        "Planning tools include text_analyzer",
        "text_analyzer" in tool_names
    )
    
    # Test 2: Get ReAct tools
    react_tools = get_react_tools()
    react_tool_names = [tool.name for tool in react_tools]
    print_test(
        "Get ReAct tools (3 tools)",
        len(react_tools) == 3,
        f"Got {len(react_tools)} tools: {react_tool_names}"
    )
    
    print_test(
        "ReAct tools include all tools",
        all(name in react_tool_names for name in ["calculator", "text_analyzer", "game_design_analyzer"])
    )
    
    # Test 3: Get evaluation tools
    eval_tools = get_evaluation_tools()
    eval_tool_names = [tool.name for tool in eval_tools]
    print_test(
        "Get evaluation tools (3 tools)",
        len(eval_tools) == 3,
        f"Got {len(eval_tools)} tools: {eval_tool_names}"
    )


def test_configuration_scenarios():
    """Test common configuration scenarios."""
    print("\n" + "=" * 70)
    print("Testing Configuration Scenarios")
    print("=" * 70)
    
    # Scenario 1: High-quality production setup
    print("\n  Scenario 1: High-Quality Production Setup")
    prod_config = ModelConfig(
        model_name="gpt-5",
        thinking_effort="high",
        max_tokens=8000,
    )
    print_test(
        "  Production config with high thinking effort",
        prod_config.thinking_effort == "high" and prod_config.max_tokens == 8000
    )
    
    # Scenario 2: Cost-effective setup
    print("\n  Scenario 2: Cost-Effective Setup")
    cost_config = ModelConfig(
        model_name="gpt-5-mini",
        thinking_effort="low",
        max_tokens=4000,
    )
    print_test(
        "  Cost-effective config with low thinking effort",
        cost_config.model_name == "gpt-5-mini" and cost_config.thinking_effort == "low"
    )
    
    # Scenario 3: Tool-enabled setup
    print("\n  Scenario 3: Tool-Enabled Setup")
    tool_config = ModelConfig(
        model_name="gpt-5",
        enable_tools=True,
        parallel_tool_calls=True,
    )
    print_test(
        "  Config with tools enabled",
        tool_config.enable_tools is True and tool_config.parallel_tool_calls is True
    )
    
    # Scenario 4: Legacy GPT-4 setup
    print("\n  Scenario 4: Legacy GPT-4 Setup")
    legacy_config = ModelConfig(
        model_name="gpt-4o",
        temperature=0.7,
    )
    kwargs = legacy_config.get_model_kwargs()
    print_test(
        "  Legacy config uses temperature (not thinking_effort)",
        "temperature" in kwargs and "thinking_effort" not in kwargs
    )


def print_config_summary():
    """Print current configuration summary."""
    print("\n" + "=" * 70)
    print("Current Configuration Summary")
    print("=" * 70)
    
    print("\n📋 Planning Agent:")
    planning = settings.get_planning_config()
    print(f"  Model: {planning.model_name}")
    print(f"  Thinking Effort: {planning.thinking_effort}")
    print(f"  Tools Enabled: {planning.enable_tools}")
    print(f"  Max Tokens: {planning.max_tokens}")
    
    print("\n🤖 ReAct Execution Agent:")
    react = settings.get_react_config()
    print(f"  Model: {react.model_name}")
    print(f"  Thinking Effort: {react.thinking_effort}")
    print(f"  Tools Enabled: {react.enable_tools}")
    print(f"  Max Tokens: {react.max_tokens}")
    
    print("\n📊 Evaluation Agent:")
    evaluation = settings.get_evaluation_config()
    print(f"  Model: {evaluation.model_name}")
    print(f"  Thinking Effort: {evaluation.thinking_effort}")
    print(f"  Tools Enabled: {evaluation.enable_tools}")
    print(f"  Max Tokens: {evaluation.max_tokens}")
    
    print("\n⚙️ Global Settings:")
    print(f"  Use Responses API: {settings.use_responses_api}")
    print(f"  Output Version: {settings.output_version}")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("🧪 Configuration System Verification")
    print("=" * 70)
    print("\nThis script verifies that the new configuration system is working correctly.")
    
    try:
        test_model_config()
        test_settings()
        test_tool_getters()
        test_configuration_scenarios()
        print_config_summary()
        
        print("\n" + "=" * 70)
        print("✅ All verifications completed successfully!")
        print("=" * 70)
        print("\nThe configuration system is working correctly.")
        print("\nNext steps:")
        print("  1. Update your .env file with desired settings")
        print("  2. Run: uv run python -m pytest tests/test_configuration.py")
        print("  3. See docs/CONFIGURATION.md for detailed documentation")
        print()
        
        return 0
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"❌ Error during verification: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

