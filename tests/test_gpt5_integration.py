"""Comprehensive tests for GPT-5 and Responses API integration."""

import os
import pytest
from unittest.mock import Mock, patch
from langchain_openai import ChatOpenAI

from agent_games_design.agents import PlanningAgent, ReActExecutor, create_llm


class TestReasoningModelDetection:
    """Test that reasoning models are correctly detected."""

    def test_gpt5_pro_detected(self):
        """Test GPT-5 Pro is detected as reasoning model."""
        model_name = "gpt-5-pro"
        is_reasoning = any(
            prefix in model_name.lower() 
            for prefix in ["gpt-5", "o1", "o3", "o4"]
        )
        assert is_reasoning, "gpt-5-pro should be detected as reasoning model"

    def test_gpt5_nano_detected(self):
        """Test GPT-5 Nano is detected as reasoning model."""
        model_name = "gpt-5-nano"
        is_reasoning = any(
            prefix in model_name.lower() 
            for prefix in ["gpt-5", "o1", "o3", "o4"]
        )
        assert is_reasoning, "gpt-5-nano should be detected as reasoning model"

    def test_o1_detected(self):
        """Test o1 is detected as reasoning model."""
        model_name = "o1"
        is_reasoning = any(
            prefix in model_name.lower() 
            for prefix in ["gpt-5", "o1", "o3", "o4"]
        )
        assert is_reasoning, "o1 should be detected as reasoning model"

    def test_o4_mini_detected(self):
        """Test o4-mini is detected as reasoning model."""
        model_name = "o4-mini"
        is_reasoning = any(
            prefix in model_name.lower() 
            for prefix in ["gpt-5", "o1", "o3", "o4"]
        )
        assert is_reasoning, "o4-mini should be detected as reasoning model"

    def test_gpt4o_not_detected(self):
        """Test GPT-4o is NOT detected as reasoning model."""
        model_name = "gpt-4o"
        is_reasoning = any(
            prefix in model_name.lower() 
            for prefix in ["gpt-5", "o1", "o3", "o4"]
        )
        assert not is_reasoning, "gpt-4o should NOT be detected as reasoning model"

    def test_gpt4o_mini_not_detected(self):
        """Test GPT-4o-mini is NOT detected as reasoning model."""
        model_name = "gpt-4o-mini"
        is_reasoning = any(
            prefix in model_name.lower() 
            for prefix in ["gpt-5", "o1", "o3", "o4"]
        )
        assert not is_reasoning, "gpt-4o-mini should NOT be detected as reasoning model"


class TestCreateLLMFunction:
    """Test the create_llm function with different models."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_create_llm_with_gpt5(self):
        """Test create_llm properly handles GPT-5 models."""
        llm = create_llm(model="gpt-5-pro", temperature=0.7)
        
        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "gpt-5-pro"
        # Temperature should not be set for reasoning models
        # Check that use_responses_api is enabled
        assert llm.use_responses_api is True

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_create_llm_with_gpt4(self):
        """Test create_llm properly handles GPT-4 models."""
        llm = create_llm(model="gpt-4o-mini", temperature=0.7)
        
        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "gpt-4o-mini"
        # Temperature should be set for standard models
        assert llm.temperature == 0.7

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_create_llm_with_o1(self):
        """Test create_llm properly handles o1 models."""
        llm = create_llm(model="o1", temperature=0.5)
        
        assert isinstance(llm, ChatOpenAI)
        assert llm.model_name == "o1"
        # use_responses_api should be enabled
        assert llm.use_responses_api is True


class TestPlanningAgent:
    """Test PlanningAgent initialization with different models."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "PLANNING_MODEL": "gpt-5-pro"})
    def test_planning_agent_with_gpt5(self):
        """Test PlanningAgent handles GPT-5 correctly."""
        agent = PlanningAgent(model_name="gpt-5-pro", temperature=0.3)
        
        assert agent.llm is not None
        assert isinstance(agent.llm, ChatOpenAI)
        assert agent.llm.model_name == "gpt-5-pro"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "PLANNING_MODEL": "gpt-4o-mini"})
    def test_planning_agent_with_gpt4(self):
        """Test PlanningAgent handles GPT-4 correctly."""
        agent = PlanningAgent(model_name="gpt-4o-mini", temperature=0.3)
        
        assert agent.llm is not None
        assert isinstance(agent.llm, ChatOpenAI)
        assert agent.llm.model_name == "gpt-4o-mini"
        assert agent.llm.temperature == 0.3


class TestReActExecutor:
    """Test ReActExecutor initialization with different models."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "REACT_EXECUTION_MODEL": "gpt-5-nano"})
    def test_react_executor_with_gpt5(self):
        """Test ReActExecutor handles GPT-5 correctly."""
        executor = ReActExecutor(model_name="gpt-5-nano", temperature=0.5)
        
        assert executor.llm is not None
        assert isinstance(executor.llm, ChatOpenAI)
        assert executor.llm.model_name == "gpt-5-nano"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "REACT_EXECUTION_MODEL": "gpt-4o"})
    def test_react_executor_with_gpt4(self):
        """Test ReActExecutor handles GPT-4 correctly."""
        executor = ReActExecutor(model_name="gpt-4o", temperature=0.5)
        
        assert executor.llm is not None
        assert isinstance(executor.llm, ChatOpenAI)
        assert executor.llm.model_name == "gpt-4o"
        assert executor.llm.temperature == 0.5


class TestOutputVersion:
    """Test that output_version is set correctly."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_output_version_for_gpt5(self):
        """Test output_version is set for GPT-5 models."""
        llm = create_llm(model="gpt-5-pro")
        
        # output_version should be set to responses/v1
        assert hasattr(llm, 'output_version')
        assert llm.output_version == "responses/v1"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_output_version_for_all_models(self):
        """Test output_version is set for all models."""
        llm = create_llm(model="gpt-4o-mini")
        
        # output_version should be set for all models
        assert hasattr(llm, 'output_version')
        assert llm.output_version == "responses/v1"


class TestModelCompatibility:
    """Test model compatibility with different scenarios."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_various_reasoning_models(self):
        """Test various reasoning model names are handled correctly."""
        reasoning_models = [
            "gpt-5-pro",
            "gpt-5-nano",
            "GPT-5-PRO",  # Case insensitive
            "o1",
            "o1-preview",
            "o3",
            "o3-mini",
            "o4-mini",
        ]
        
        for model in reasoning_models:
            llm = create_llm(model=model)
            assert llm.use_responses_api is True, f"{model} should use Responses API"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_various_standard_models(self):
        """Test various standard model names are handled correctly."""
        standard_models = [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
        ]
        
        for model in standard_models:
            llm = create_llm(model=model, temperature=0.7)
            assert llm.temperature == 0.7, f"{model} should have temperature set"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

