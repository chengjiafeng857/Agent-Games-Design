"""Tests for the new configuration system and standard API integration."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agent_games_design.config import ModelConfig, Settings, settings
from agent_games_design.agents import PlanningAgent, ReActExecutor
from agent_games_design.tools import get_planning_tools, get_react_tools, get_evaluation_tools


class TestModelConfig:
    """Tests for ModelConfig class."""

    def test_model_config_initialization(self):
        """Test ModelConfig initialization with default values."""
        config = ModelConfig()
        
        assert config.model_name == "gpt-5"
        assert config.temperature is None
        assert config.max_tokens is None
        assert config.thinking_effort is None
        assert config.enable_tools is False
        assert config.parallel_tool_calls is True
        assert config.use_responses_api is True
        assert config.output_version == "responses/v1"

    def test_model_config_custom_values(self):
        """Test ModelConfig with custom values."""
        config = ModelConfig(
            model_name="gpt-5-mini",
            temperature=0.3,
            thinking_effort="medium",
            enable_tools=True,
            max_tokens=4000,
            parallel_tool_calls=False,
        )
        
        assert config.model_name == "gpt-5-mini"
        assert config.temperature == 0.3
        assert config.thinking_effort == "medium"
        assert config.enable_tools is True
        assert config.max_tokens == 4000
        assert config.parallel_tool_calls is False

    def test_is_reasoning_model_gpt5(self):
        """Test reasoning model detection for GPT-5."""
        config = ModelConfig(model_name="gpt-5")
        assert config.is_reasoning_model() is True
        
        config_mini = ModelConfig(model_name="gpt-5-mini")
        assert config_mini.is_reasoning_model() is True

    def test_is_reasoning_model_o_series(self):
        """Test reasoning model detection for o-series."""
        for model in ["o1", "o3", "o4-preview"]:
            config = ModelConfig(model_name=model)
            assert config.is_reasoning_model() is True

    def test_is_not_reasoning_model_gpt4(self):
        """Test non-reasoning model detection for GPT-4."""
        config = ModelConfig(model_name="gpt-4o")
        assert config.is_reasoning_model() is False
        
        config_turbo = ModelConfig(model_name="gpt-4-turbo")
        assert config_turbo.is_reasoning_model() is False

    def test_get_model_kwargs_reasoning_model(self):
        """Test model kwargs for reasoning models."""
        config = ModelConfig(
            model_name="gpt-5",
            temperature=0.7,  # Should be ignored
            thinking_effort="high",  # Kept in config but not passed to API (not yet supported)
            max_tokens=8000,
        )
        
        kwargs = config.get_model_kwargs()
        
        assert kwargs["model"] == "gpt-5"
        assert kwargs["output_version"] == "responses/v1"
        assert kwargs["use_responses_api"] is True
        # Note: thinking_effort not yet supported by OpenAI/LangChain
        assert "thinking_effort" not in kwargs
        assert kwargs["max_tokens"] == 8000
        assert "temperature" not in kwargs  # Should not include temperature

    def test_get_model_kwargs_standard_model(self):
        """Test model kwargs for standard models."""
        config = ModelConfig(
            model_name="gpt-4o",
            temperature=0.7,
            thinking_effort="high",  # Should be ignored
            max_tokens=4000,
        )
        
        kwargs = config.get_model_kwargs()
        
        assert kwargs["model"] == "gpt-4o"
        assert kwargs["output_version"] == "responses/v1"
        assert kwargs["temperature"] == 0.7
        assert kwargs["max_tokens"] == 4000
        assert "thinking_effort" not in kwargs  # Should not include thinking_effort
        assert "use_responses_api" not in kwargs  # Only for reasoning models

    def test_get_model_kwargs_no_optional_params(self):
        """Test model kwargs without optional parameters."""
        config = ModelConfig(model_name="gpt-4o")
        
        kwargs = config.get_model_kwargs()
        
        assert kwargs["model"] == "gpt-4o"
        assert kwargs["output_version"] == "responses/v1"
        assert "temperature" not in kwargs
        assert "max_tokens" not in kwargs
        assert "thinking_effort" not in kwargs

    def test_get_bind_tools_kwargs(self):
        """Test bind tools kwargs generation."""
        config = ModelConfig(parallel_tool_calls=True)
        kwargs = config.get_bind_tools_kwargs()
        assert kwargs["parallel_tool_calls"] is True
        
        config_no_parallel = ModelConfig(parallel_tool_calls=False)
        kwargs_no_parallel = config_no_parallel.get_bind_tools_kwargs()
        assert kwargs_no_parallel["parallel_tool_calls"] is False


class TestSettings:
    """Tests for Settings class."""

    def test_settings_singleton(self):
        """Test that settings is a singleton instance."""
        assert settings is not None
        assert isinstance(settings, Settings)

    def test_get_planning_config(self):
        """Test getting planning configuration."""
        config = settings.get_planning_config()
        
        assert isinstance(config, ModelConfig)
        assert config.model_name == settings.planning_model
        assert config.temperature == settings.planning_temperature
        assert config.thinking_effort == settings.planning_thinking_effort
        assert config.enable_tools == settings.planning_enable_tools
        assert config.max_tokens == settings.planning_max_tokens
        assert config.parallel_tool_calls == settings.planning_parallel_tool_calls

    def test_get_react_config(self):
        """Test getting ReAct configuration."""
        config = settings.get_react_config()
        
        assert isinstance(config, ModelConfig)
        assert config.model_name == settings.react_execution_model
        assert config.temperature == settings.react_temperature
        assert config.thinking_effort == settings.react_thinking_effort
        assert config.enable_tools == settings.react_enable_tools
        assert config.max_tokens == settings.react_max_tokens
        assert config.parallel_tool_calls == settings.react_parallel_tool_calls

    def test_get_evaluation_config(self):
        """Test getting evaluation configuration."""
        config = settings.get_evaluation_config()
        
        assert isinstance(config, ModelConfig)
        assert config.model_name == settings.evaluation_model
        assert config.temperature == settings.evaluation_temperature
        assert config.thinking_effort == settings.evaluation_thinking_effort
        assert config.enable_tools == settings.evaluation_enable_tools
        assert config.max_tokens == settings.evaluation_max_tokens
        assert config.parallel_tool_calls == settings.evaluation_parallel_tool_calls

    def test_settings_default_values(self):
        """Test default settings values."""
        assert settings.default_model == "gpt-5"
        assert settings.use_responses_api is True
        assert settings.output_version == "responses/v1"
        assert settings.planning_thinking_effort == "medium"
        assert settings.react_thinking_effort == "high"
        assert settings.evaluation_thinking_effort == "low"


class TestToolGetters:
    """Tests for tool getter functions."""

    def test_get_planning_tools(self):
        """Test getting planning tools."""
        tools = get_planning_tools()
        
        assert isinstance(tools, list)
        assert len(tools) == 2  # game_design_analyzer, text_analyzer
        
        tool_names = [tool.name for tool in tools]
        assert "game_design_analyzer" in tool_names
        assert "text_analyzer" in tool_names

    def test_get_react_tools(self):
        """Test getting ReAct tools."""
        tools = get_react_tools()
        
        assert isinstance(tools, list)
        assert len(tools) == 3  # All tools
        
        tool_names = [tool.name for tool in tools]
        assert "calculator" in tool_names
        assert "text_analyzer" in tool_names
        assert "game_design_analyzer" in tool_names

    def test_get_evaluation_tools(self):
        """Test getting evaluation tools."""
        tools = get_evaluation_tools()
        
        assert isinstance(tools, list)
        assert len(tools) == 3  # Analysis tools
        
        tool_names = [tool.name for tool in tools]
        assert "text_analyzer" in tool_names
        assert "game_design_analyzer" in tool_names
        assert "calculator" in tool_names


class TestPlanningAgentIntegration:
    """Integration tests for PlanningAgent with new configuration."""

    @patch("agent_games_design.agents.planning.ChatOpenAI")
    def test_planning_agent_default_config(self, mock_chat_openai):
        """Test PlanningAgent initialization with default config."""
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm
        
        agent = PlanningAgent()
        
        # Verify ChatOpenAI was called
        assert mock_chat_openai.called
        
        # Verify config was set
        assert agent.config is not None
        assert isinstance(agent.config, ModelConfig)

    @patch("agent_games_design.agents.planning.ChatOpenAI")
    def test_planning_agent_custom_config(self, mock_chat_openai):
        """Test PlanningAgent initialization with custom config."""
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm
        
        custom_config = ModelConfig(
            model_name="gpt-5",
            thinking_effort="high",
            enable_tools=False,
        )
        
        agent = PlanningAgent(model_config=custom_config)
        
        # Verify custom config was used
        assert agent.config.model_name == "gpt-5"
        assert agent.config.thinking_effort == "high"
        assert agent.config.enable_tools is False

    @patch("agent_games_design.agents.planning.ChatOpenAI")
    def test_planning_agent_tool_binding(self, mock_chat_openai):
        """Test PlanningAgent tool binding when enabled."""
        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        mock_chat_openai.return_value = mock_llm
        
        config = ModelConfig(
            model_name="gpt-5",
            enable_tools=True,
        )
        
        agent = PlanningAgent(model_config=config)
        
        # Verify tools were bound
        assert mock_llm.bind_tools.called
        
        # Get the tools that were passed to bind_tools
        call_args = mock_llm.bind_tools.call_args
        tools_passed = call_args[0][0]  # First positional argument
        
        assert len(tools_passed) == 2  # Planning has 2 tools
        tool_names = [tool.name for tool in tools_passed]
        assert "game_design_analyzer" in tool_names
        assert "text_analyzer" in tool_names

    @patch("agent_games_design.agents.planning.ChatOpenAI")
    def test_planning_agent_no_tool_binding(self, mock_chat_openai):
        """Test PlanningAgent without tool binding when disabled."""
        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        mock_chat_openai.return_value = mock_llm
        
        config = ModelConfig(
            model_name="gpt-5",
            enable_tools=False,
        )
        
        agent = PlanningAgent(model_config=config)
        
        # Verify tools were NOT bound
        assert not mock_llm.bind_tools.called


class TestReActExecutorIntegration:
    """Integration tests for ReActExecutor with new configuration."""

    @patch("agent_games_design.agents.react_executor.ChatOpenAI")
    def test_react_executor_default_config(self, mock_chat_openai):
        """Test ReActExecutor initialization with default config."""
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm
        
        executor = ReActExecutor()
        
        # Verify ChatOpenAI was called
        assert mock_chat_openai.called
        
        # Verify config was set
        assert executor.config is not None
        assert isinstance(executor.config, ModelConfig)

    @patch("agent_games_design.agents.react_executor.ChatOpenAI")
    def test_react_executor_custom_config(self, mock_chat_openai):
        """Test ReActExecutor initialization with custom config."""
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm
        
        custom_config = ModelConfig(
            model_name="gpt-5",
            thinking_effort="high",
            enable_tools=True,
        )
        
        executor = ReActExecutor(model_config=custom_config)
        
        # Verify custom config was used
        assert executor.config.model_name == "gpt-5"
        assert executor.config.thinking_effort == "high"
        assert executor.config.enable_tools is True

    @patch("agent_games_design.agents.react_executor.ChatOpenAI")
    def test_react_executor_tool_binding(self, mock_chat_openai):
        """Test ReActExecutor tool binding when enabled."""
        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        mock_chat_openai.return_value = mock_llm
        
        config = ModelConfig(
            model_name="gpt-5",
            enable_tools=True,
        )
        
        executor = ReActExecutor(model_config=config)
        
        # Verify tools were bound
        assert mock_llm.bind_tools.called
        
        # Get the tools that were passed to bind_tools
        call_args = mock_llm.bind_tools.call_args
        tools_passed = call_args[0][0]  # First positional argument
        
        assert len(tools_passed) == 3  # ReAct has all 3 tools
        tool_names = [tool.name for tool in tools_passed]
        assert "calculator" in tool_names
        assert "text_analyzer" in tool_names
        assert "game_design_analyzer" in tool_names


class TestResponseAPIIntegration:
    """Tests for Response API integration."""

    @patch("agent_games_design.agents.planning.ChatOpenAI")
    def test_response_api_v1_reasoning_model(self, mock_chat_openai):
        """Test Response API v1 with reasoning model."""
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm
        
        config = ModelConfig(
            model_name="gpt-5",
            use_responses_api=True,
            output_version="responses/v1",
        )
        
        agent = PlanningAgent(model_config=config)
        
        # Verify ChatOpenAI was called with correct kwargs
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["use_responses_api"] is True
        assert call_kwargs["output_version"] == "responses/v1"

    @patch("agent_games_design.agents.planning.ChatOpenAI")
    def test_response_api_v0_fallback(self, mock_chat_openai):
        """Test Response API with v0 format."""
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm
        
        config = ModelConfig(
            model_name="gpt-4o",
            use_responses_api=False,
            output_version="v0",
        )
        
        agent = PlanningAgent(model_config=config)
        
        # Verify ChatOpenAI was called with correct kwargs
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["output_version"] == "v0"


class TestThinkingEffort:
    """Tests for thinking effort configuration.
    
    Note: thinking_effort is currently stored in config but NOT passed to the API
    as it's not yet officially supported by OpenAI/LangChain.
    """

    def test_thinking_effort_stored_in_config(self):
        """Test that thinking effort is stored in config."""
        config = ModelConfig(
            model_name="gpt-5",
            thinking_effort="low",
        )
        
        # Verify it's stored in the config
        assert config.thinking_effort == "low"
        
        # But not passed to API kwargs (not yet supported)
        kwargs = config.get_model_kwargs()
        assert "thinking_effort" not in kwargs

    def test_thinking_effort_medium_stored(self):
        """Test medium thinking effort is stored."""
        config = ModelConfig(
            model_name="gpt-5",
            thinking_effort="medium",
        )
        
        assert config.thinking_effort == "medium"
        
        # Not passed to API yet
        kwargs = config.get_model_kwargs()
        assert "thinking_effort" not in kwargs

    def test_thinking_effort_high_stored(self):
        """Test high thinking effort is stored."""
        config = ModelConfig(
            model_name="gpt-5",
            thinking_effort="high",
        )
        
        assert config.thinking_effort == "high"
        
        # Not passed to API yet
        kwargs = config.get_model_kwargs()
        assert "thinking_effort" not in kwargs

    def test_thinking_effort_not_passed_for_any_model(self):
        """Test thinking effort is not passed to API for any model type."""
        # GPT-5 model
        gpt5_config = ModelConfig(
            model_name="gpt-5",
            thinking_effort="high",
        )
        gpt5_kwargs = gpt5_config.get_model_kwargs()
        assert "thinking_effort" not in gpt5_kwargs
        
        # GPT-4 model
        gpt4_config = ModelConfig(
            model_name="gpt-4o",
            thinking_effort="high",
        )
        gpt4_kwargs = gpt4_config.get_model_kwargs()
        assert "thinking_effort" not in gpt4_kwargs


class TestBackwardCompatibility:
    """Tests for backward compatibility."""

    @patch("agent_games_design.agents.planning.ChatOpenAI")
    def test_default_initialization_still_works(self, mock_chat_openai):
        """Test that default initialization without parameters still works."""
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm
        
        # This should work without any parameters (backward compatible)
        agent = PlanningAgent()
        
        assert agent is not None
        assert agent.config is not None

    @patch("agent_games_design.agents.react_executor.ChatOpenAI")
    def test_react_default_initialization(self, mock_chat_openai):
        """Test ReAct executor default initialization."""
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm
        
        # This should work without any parameters (backward compatible)
        executor = ReActExecutor()
        
        assert executor is not None
        assert executor.config is not None


# Run all tests when executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

