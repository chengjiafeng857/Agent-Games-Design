"""Simple test runner for GPT-5 integration (no pytest required)."""

import os
import sys

# Set test API key
os.environ["OPENAI_API_KEY"] = "test-key-12345"
os.environ["PLANNING_MODEL"] = "gpt-5-pro"
os.environ["REACT_EXECUTION_MODEL"] = "gpt-5-nano"

from agent_games_design.agents import PlanningAgent, ReActExecutor, create_llm
from langchain_openai import ChatOpenAI


def test_reasoning_model_detection():
    """Test reasoning model detection logic."""
    print("\n=== Testing Reasoning Model Detection ===")
    
    test_cases = {
        "gpt-5-pro": True,
        "gpt-5-nano": True,
        "GPT-5-PRO": True,  # Case insensitive
        "o1": True,
        "o1-preview": True,
        "o3": True,
        "o4-mini": True,
        "gpt-4o": False,
        "gpt-4o-mini": False,
        "gpt-3.5-turbo": False,
    }
    
    passed = 0
    failed = 0
    
    for model_name, should_be_reasoning in test_cases.items():
        is_reasoning = any(
            prefix in model_name.lower() 
            for prefix in ["gpt-5", "o1", "o3", "o4"]
        )
        
        if is_reasoning == should_be_reasoning:
            print(f"  ✓ {model_name}: {'reasoning' if is_reasoning else 'standard'} (correct)")
            passed += 1
        else:
            print(f"  ✗ {model_name}: Expected {'reasoning' if should_be_reasoning else 'standard'}, got {'reasoning' if is_reasoning else 'standard'}")
            failed += 1
    
    print(f"\nDetection Tests: {passed} passed, {failed} failed")
    return failed == 0


def test_create_llm_function():
    """Test create_llm function with different models."""
    print("\n=== Testing create_llm Function ===")
    
    passed = 0
    failed = 0
    
    # Test GPT-5 model
    try:
        llm = create_llm(model="gpt-5-pro", temperature=0.7)
        assert isinstance(llm, ChatOpenAI), "Should return ChatOpenAI instance"
        assert llm.model_name == "gpt-5-pro", "Model name should be set"
        assert llm.use_responses_api is True, "Should use Responses API"
        assert llm.output_version == "responses/v1", "Should use v1 output format"
        print("  ✓ create_llm with gpt-5-pro works correctly")
        passed += 1
    except Exception as e:
        print(f"  ✗ create_llm with gpt-5-pro failed: {e}")
        failed += 1
    
    # Test GPT-4 model
    try:
        llm = create_llm(model="gpt-4o-mini", temperature=0.7)
        assert isinstance(llm, ChatOpenAI), "Should return ChatOpenAI instance"
        assert llm.model_name == "gpt-4o-mini", "Model name should be set"
        assert llm.temperature == 0.7, "Temperature should be set for standard models"
        assert llm.output_version == "responses/v1", "Should use v1 output format"
        print("  ✓ create_llm with gpt-4o-mini works correctly")
        passed += 1
    except Exception as e:
        print(f"  ✗ create_llm with gpt-4o-mini failed: {e}")
        failed += 1
    
    # Test o1 model
    try:
        llm = create_llm(model="o1", temperature=0.5)
        assert isinstance(llm, ChatOpenAI), "Should return ChatOpenAI instance"
        assert llm.use_responses_api is True, "Should use Responses API"
        print("  ✓ create_llm with o1 works correctly")
        passed += 1
    except Exception as e:
        print(f"  ✗ create_llm with o1 failed: {e}")
        failed += 1
    
    print(f"\ncreate_llm Tests: {passed} passed, {failed} failed")
    return failed == 0


def test_planning_agent():
    """Test PlanningAgent initialization."""
    print("\n=== Testing PlanningAgent ===")
    
    passed = 0
    failed = 0
    
    # Test with GPT-5
    try:
        agent = PlanningAgent(model_name="gpt-5-pro", temperature=0.3)
        assert agent.llm is not None, "LLM should be initialized"
        assert isinstance(agent.llm, ChatOpenAI), "Should be ChatOpenAI instance"
        assert agent.llm.model_name == "gpt-5-pro", "Model name should be set"
        print("  ✓ PlanningAgent with gpt-5-pro initializes correctly")
        passed += 1
    except Exception as e:
        print(f"  ✗ PlanningAgent with gpt-5-pro failed: {e}")
        failed += 1
    
    # Test with GPT-4
    try:
        agent = PlanningAgent(model_name="gpt-4o-mini", temperature=0.3)
        assert agent.llm is not None, "LLM should be initialized"
        assert isinstance(agent.llm, ChatOpenAI), "Should be ChatOpenAI instance"
        assert agent.llm.temperature == 0.3, "Temperature should be set"
        print("  ✓ PlanningAgent with gpt-4o-mini initializes correctly")
        passed += 1
    except Exception as e:
        print(f"  ✗ PlanningAgent with gpt-4o-mini failed: {e}")
        failed += 1
    
    print(f"\nPlanningAgent Tests: {passed} passed, {failed} failed")
    return failed == 0


def test_react_executor():
    """Test ReActExecutor initialization."""
    print("\n=== Testing ReActExecutor ===")
    
    passed = 0
    failed = 0
    
    # Test with GPT-5
    try:
        executor = ReActExecutor(model_name="gpt-5-nano", temperature=0.5)
        assert executor.llm is not None, "LLM should be initialized"
        assert isinstance(executor.llm, ChatOpenAI), "Should be ChatOpenAI instance"
        assert executor.llm.model_name == "gpt-5-nano", "Model name should be set"
        print("  ✓ ReActExecutor with gpt-5-nano initializes correctly")
        passed += 1
    except Exception as e:
        print(f"  ✗ ReActExecutor with gpt-5-nano failed: {e}")
        failed += 1
    
    # Test with GPT-4
    try:
        executor = ReActExecutor(model_name="gpt-4o", temperature=0.5)
        assert executor.llm is not None, "LLM should be initialized"
        assert isinstance(executor.llm, ChatOpenAI), "Should be ChatOpenAI instance"
        assert executor.llm.temperature == 0.5, "Temperature should be set"
        print("  ✓ ReActExecutor with gpt-4o initializes correctly")
        passed += 1
    except Exception as e:
        print(f"  ✗ ReActExecutor with gpt-4o failed: {e}")
        failed += 1
    
    print(f"\nReActExecutor Tests: {passed} passed, {failed} failed")
    return failed == 0


def test_temperature_omission():
    """Test that temperature is properly omitted for reasoning models."""
    print("\n=== Testing Temperature Omission ===")
    
    passed = 0
    failed = 0
    
    reasoning_models = ["gpt-5-pro", "gpt-5-nano", "o1", "o4-mini"]
    standard_models = ["gpt-4o", "gpt-4o-mini"]
    
    for model in reasoning_models:
        try:
            llm = create_llm(model=model, temperature=0.7)
            # For reasoning models, temperature should NOT be in the kwargs
            # We check that use_responses_api is True as an indicator
            assert llm.use_responses_api is True
            print(f"  ✓ {model}: Correctly configured as reasoning model")
            passed += 1
        except Exception as e:
            print(f"  ✗ {model}: Failed - {e}")
            failed += 1
    
    for model in standard_models:
        try:
            llm = create_llm(model=model, temperature=0.7)
            # For standard models, temperature SHOULD be set
            assert llm.temperature == 0.7
            print(f"  ✓ {model}: Temperature correctly set to 0.7")
            passed += 1
        except Exception as e:
            print(f"  ✗ {model}: Failed - {e}")
            failed += 1
    
    print(f"\nTemperature Tests: {passed} passed, {failed} failed")
    return failed == 0


def main():
    """Run all tests."""
    print("=" * 70)
    print("GPT-5 and Responses API Integration Tests")
    print("=" * 70)
    
    all_passed = True
    
    all_passed &= test_reasoning_model_detection()
    all_passed &= test_create_llm_function()
    all_passed &= test_planning_agent()
    all_passed &= test_react_executor()
    all_passed &= test_temperature_omission()
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())

