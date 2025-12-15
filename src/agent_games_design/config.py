"""Configuration management for the agent system."""

from typing import Optional, List, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class ModelConfig(BaseSettings):
    """Configuration for individual model settings."""
    
    model_name: str = Field(default="gpt-5", description="Model name")
    temperature: Optional[float] = Field(default=None, description="Temperature (None for reasoning models)")
    max_tokens: Optional[int] = Field(default=None, description="Max tokens to generate")
    thinking_effort: Optional[str] = Field(default=None, description="Thinking effort: low, medium, high (GPT-5 only)")
    enable_tools: bool = Field(default=False, description="Enable tool use")
    parallel_tool_calls: bool = Field(default=True, description="Allow parallel tool calls")
    
    # Response API settings
    use_responses_api: bool = Field(default=True, description="Use OpenAI Responses API")
    output_version: str = Field(default="responses/v1", description="Output format version")
    
    def is_reasoning_model(self) -> bool:
        """Check if this is a reasoning model (GPT-5, o-series)."""
        return any(
            prefix in self.model_name.lower() 
            for prefix in ["gpt-5", "o1", "o3", "o4"]
        )
    
    def get_model_kwargs(self) -> Dict[str, Any]:
        """Get kwargs for model initialization."""
        kwargs = {
            "model": self.model_name,
            "output_version": self.output_version,
        }
        
        # Add use_responses_api for reasoning models
        if self.is_reasoning_model() and self.use_responses_api:
            kwargs["use_responses_api"] = True
        
        # Add temperature only for non-reasoning models
        if not self.is_reasoning_model() and self.temperature is not None:
            kwargs["temperature"] = self.temperature
        
        # NOTE: thinking_effort is kept in config for future use but not passed to API
        # GPT-5 and o-series models use automatic reasoning without explicit effort control
        # Uncomment when OpenAI/LangChain officially supports this parameter:
        # if "gpt-5" in self.model_name.lower() and self.thinking_effort:
        #     kwargs["thinking_effort"] = self.thinking_effort
        
        # Add max_tokens if specified
        if self.max_tokens is not None:
            kwargs["max_tokens"] = self.max_tokens
            
        return kwargs
    
    def get_bind_tools_kwargs(self) -> Dict[str, Any]:
        """Get kwargs for bind_tools call."""
        kwargs = {}
        if self.parallel_tool_calls is not None:
            kwargs["parallel_tool_calls"] = self.parallel_tool_calls
        return kwargs


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""  # Google Gemini API key for image generation

    # LangSmith (optional)
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "agent-games-design"

    # Model Configuration - Basic
    default_model: str = "gpt-5.1"  # Can also use: gpt-4o, gpt-4o-mini, gpt-4-turbo
    
    # Legacy temperature (for backward compatibility)
    temperature: float = 0.7
    
    # ========================================
    # PLANNING AGENT CONFIGURATION
    # ========================================
    planning_model: str = "gpt-5.1"
    planning_temperature: Optional[float] = 0.3
    planning_thinking_effort: Optional[str] = "high"  # low, medium, high (GPT-5 only)
    planning_enable_tools: bool = False  # Set to True to enable tool use in planning
    planning_max_tokens: Optional[int] = None
    planning_parallel_tool_calls: bool = True
    
    # ========================================
    # REACT EXECUTION AGENT CONFIGURATION
    # ========================================
    react_execution_model: str = "gpt-5.1"
    react_temperature: Optional[float] = 0.7
    react_thinking_effort: Optional[str] = "high"  # low, medium, high (GPT-5 only)
    react_enable_tools: bool = False  # Set to True to enable external tools
    react_max_tokens: Optional[int] = None
    react_parallel_tool_calls: bool = True
    
    # ========================================
    # EVALUATION AGENT CONFIGURATION
    # ========================================
    evaluation_model: str = "gpt-5.1-mini"
    evaluation_temperature: Optional[float] = 0.5
    evaluation_thinking_effort: Optional[str] = "low"  # low, medium, high (GPT-5 only)
    evaluation_enable_tools: bool = False
    evaluation_max_tokens: Optional[int] = None
    evaluation_parallel_tool_calls: bool = True
    
    # ========================================
    # RESPONSE API SETTINGS
    # ========================================
    use_responses_api: bool = True  # Enable Responses API for all models
    output_version: str = "responses/v1"  # v0 or responses/v1

    # Application Settings
    debug: bool = False
    log_level: str = "INFO"
    
    def get_planning_config(self) -> ModelConfig:
        """Get planning agent model configuration."""
        return ModelConfig(
            model_name=self.planning_model,
            temperature=self.planning_temperature,
            thinking_effort=self.planning_thinking_effort,
            enable_tools=self.planning_enable_tools,
            max_tokens=self.planning_max_tokens,
            parallel_tool_calls=self.planning_parallel_tool_calls,
            use_responses_api=self.use_responses_api,
            output_version=self.output_version,
        )
    
    def get_react_config(self) -> ModelConfig:
        """Get ReAct execution agent model configuration."""
        return ModelConfig(
            model_name=self.react_execution_model,
            temperature=self.react_temperature,
            thinking_effort=self.react_thinking_effort,
            enable_tools=self.react_enable_tools,
            max_tokens=self.react_max_tokens,
            parallel_tool_calls=self.react_parallel_tool_calls,
            use_responses_api=self.use_responses_api,
            output_version=self.output_version,
        )
    
    def get_evaluation_config(self) -> ModelConfig:
        """Get evaluation agent model configuration."""
        return ModelConfig(
            model_name=self.evaluation_model,
            temperature=self.evaluation_temperature,
            thinking_effort=self.evaluation_thinking_effort,
            enable_tools=self.evaluation_enable_tools,
            max_tokens=self.evaluation_max_tokens,
            parallel_tool_calls=self.evaluation_parallel_tool_calls,
            use_responses_api=self.use_responses_api,
            output_version=self.output_version,
        )


# Global settings instance
settings = Settings()
