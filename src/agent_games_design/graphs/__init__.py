"""Graph definitions for the agent system."""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from ..agents import reasoning_agent
from ..state import AgentState

# Import ReAct workflow components
from .react_workflow import create_react_workflow
from .workflow_manager import ReActWorkflowManager
from .human_approval import HumanApprovalHandler

# Import evaluation integration (optional import)
try:
    from ..evaluation.graph_integration import EvaluatedWorkflow, create_evaluated_workflow
    EVALUATION_AVAILABLE = True
except ImportError:
    EVALUATION_AVAILABLE = False
    EvaluatedWorkflow = None
    create_evaluated_workflow = None


def should_continue(state: AgentState) -> str:
    """Determine if the agent should continue processing.

    Args:
        state: The current agent state

    Returns:
        "end" to finish, "continue" to keep processing
    """
    # End after 5 iterations or if we have a final output
    if state["iterations"] >= 5 or state.get("final_output"):
        return "end"
    return "continue"


def create_agent_graph() -> StateGraph:
    """Create the main agent graph.

    Returns:
        A compiled StateGraph
    """
    # Create the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", reasoning_agent)

    # Set entry point
    workflow.set_entry_point("agent")

    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "agent",
            "end": END,
        },
    )

    # Compile with checkpointing
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    return app


__all__ = [
    "create_agent_graph", 
    "should_continue", 
    "create_react_workflow", 
    "ReActWorkflowManager", 
    "HumanApprovalHandler",
    "EvaluatedWorkflow",
    "create_evaluated_workflow",
    "EVALUATION_AVAILABLE"
]
