"""Tools that agents can use."""

from typing import List
from langchain_core.tools import BaseTool

# Import all tools from their dedicated modules
from .calculator import calculator
from .text_analyzer import text_analyzer  
from .game_analyzer import game_design_analyzer

# List of available tools
AVAILABLE_TOOLS = [calculator, text_analyzer, game_design_analyzer]


def get_planning_tools() -> List[BaseTool]:
    """Get tools available to the planning agent.
    
    Returns:
        List of tools for planning agent
    """
    # Planning agent can use game analyzer and text analyzer
    return [game_design_analyzer, text_analyzer]


def get_react_tools() -> List[BaseTool]:
    """Get tools available to the ReAct execution agent.
    
    Returns:
        List of tools for ReAct agent
    """
    # ReAct agent has access to all tools
    return AVAILABLE_TOOLS


def get_evaluation_tools() -> List[BaseTool]:
    """Get tools available to the evaluation agent.
    
    Returns:
        List of tools for evaluation agent
    """
    # Evaluation agent can use all analysis tools
    return [text_analyzer, game_design_analyzer, calculator]


__all__ = [
    "calculator", 
    "text_analyzer", 
    "game_design_analyzer", 
    "AVAILABLE_TOOLS",
    "get_planning_tools",
    "get_react_tools",
    "get_evaluation_tools",
]
