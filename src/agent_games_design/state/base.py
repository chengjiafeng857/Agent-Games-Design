"""Base state definitions for the agent system."""

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """The state of the agent system.

    Attributes:
        messages: The conversation history
        current_task: The current task being worked on
        iterations: Number of iterations performed
        final_output: The final output when complete
    """

    messages: Annotated[list[BaseMessage], add_messages]
    current_task: str
    iterations: int
    final_output: str | None
