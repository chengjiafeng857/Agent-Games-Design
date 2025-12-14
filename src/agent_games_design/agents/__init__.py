"""Agent node definitions."""

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from ..state import AgentState
from ..utils import get_env_var

# Import ReAct agents
from .planning import PlanningAgent
from .react_executor import ReActExecutor
from .asset_generator import AssetGenerator, AssetGenerationConfig


def create_llm(model: str | None = None, temperature: float = 0.7) -> ChatOpenAI:
    """Create a language model instance with official Responses API support.

    Args:
        model: The model name to use (default from env)
        temperature: The temperature for generation
                    Note: Ignored for GPT-5/reasoning models (gpt-5-*, o1, o3, o4-*)

    Returns:
        A ChatOpenAI instance
    """
    if model is None:
        model = get_env_var("DEFAULT_MODEL", "gpt-4o-mini")

    # Check if this is a reasoning model (GPT-5, o-series)
    is_reasoning_model = any(
        prefix in model.lower() 
        for prefix in ["gpt-5", "o1", "o3", "o4"]
    )
    
    # Reasoning models don't support temperature parameter
    model_kwargs = {}
    if not is_reasoning_model:
        model_kwargs["temperature"] = temperature

    # Use ChatOpenAI with official Responses API support
    return ChatOpenAI(
        model=model,
        api_key=get_env_var("OPENAI_API_KEY"),
        # Use the new output format for Responses API (recommended for new apps)
        output_version="responses/v1",
        # Enable Responses API for GPT-5 models
        use_responses_api=True if is_reasoning_model else None,
        **model_kwargs,
    )


def reasoning_agent(state: AgentState) -> AgentState:
    """The reasoning agent node that processes tasks.

    Args:
        state: The current agent state

    Returns:
        Updated state with the agent's response
    """
    llm = create_llm()

    # Create system message for the agent
    system_msg = SystemMessage(
        content="You are a helpful AI assistant that reasons through problems step by step."
    )

    # Get the latest user message
    messages = [system_msg] + state["messages"]

    # Generate response
    response = llm.invoke(messages)

    # Update state
    return {
        "messages": [response],
        "current_task": state.get("current_task", ""),
        "iterations": state.get("iterations", 0) + 1,
        "final_output": state.get("final_output"),
    }


__all__ = [
    "create_llm",
    "reasoning_agent",
    "PlanningAgent",
    "ReActExecutor",
    "AssetGenerator",
    "AssetGenerationConfig",
]
