"""Advanced agent example with tool usage and complex workflows."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent_games_design.state import AgentState
from agent_games_design.agents import create_llm, reasoning_agent
from agent_games_design.tools import AVAILABLE_TOOLS


def tool_calling_agent(state: AgentState) -> AgentState:
    """An agent that can use tools for calculations and analysis."""
    llm = create_llm()

    # Bind tools to the LLM
    llm_with_tools = llm.bind_tools(AVAILABLE_TOOLS)

    # Create system message
    from langchain_core.messages import SystemMessage

    system_msg = SystemMessage(
        content="""You are a helpful AI assistant with access to tools. 
        You can use the calculator for math problems and text_analyzer for analyzing text.
        Always use tools when appropriate to provide accurate results."""
    )

    # Get messages and generate response
    messages = [system_msg] + state["messages"]
    response = llm_with_tools.invoke(messages)

    # Handle tool calls if any
    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            # Find and execute the tool
            for tool in AVAILABLE_TOOLS:
                if tool.name == tool_name:
                    result = tool.invoke(tool_args)
                    print(f"🔧 Tool {tool_name}: {result}")
                    break

    return {
        "messages": [response],
        "current_task": state.get("current_task", ""),
        "iterations": state.get("iterations", 0) + 1,
        "final_output": state.get("final_output"),
    }


def should_continue_advanced(state: AgentState) -> str:
    """Determine if the advanced agent should continue processing."""
    # Check if we have tool calls that need to be processed
    last_message = state["messages"][-1] if state["messages"] else None

    if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    # End after 3 iterations or if we have a final output
    if state["iterations"] >= 3 or state.get("final_output"):
        return "end"

    return "continue"


def create_advanced_agent_graph():
    """Create an advanced agent graph with tool usage."""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", tool_calling_agent)
    workflow.add_node("tools", reasoning_agent)  # For processing tool results

    # Set entry point
    workflow.set_entry_point("agent")

    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue_advanced,
        {
            "continue": "agent",
            "tools": "tools",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "tools",
        lambda state: "agent" if state["iterations"] < 5 else "end",
        {
            "agent": "agent",
            "end": END,
        },
    )

    # Compile with checkpointing
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


def main():
    """Run the advanced agent example."""
    print("🚀 Advanced Agent Example")
    print("This agent can use tools for calculations and text analysis.\n")

    # Create the advanced agent
    app = create_advanced_agent_graph()

    # Example scenarios
    scenarios = [
        "Calculate the result of 15 * 23 + 47 and then analyze the text 'Hello world! How are you today?'",
        "What is 100 divided by 7? Round to 2 decimal places.",
        "Analyze this text and count the words: 'The quick brown fox jumps over the lazy dog. This is a test sentence.'",
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"📋 Scenario {i}: {scenario}")
        print("-" * 80)

        initial_state: AgentState = {
            "messages": [HumanMessage(content=scenario)],
            "current_task": scenario,
            "iterations": 0,
            "final_output": None,
        }

        config = {"configurable": {"thread_id": f"advanced-{i}"}}

        try:
            for step, output in enumerate(app.stream(initial_state, config), 1):
                print(f"Step {step}: {list(output.keys())}")

                for node_name, node_output in output.items():
                    if "messages" in node_output and node_output["messages"]:
                        last_message = node_output["messages"][-1]
                        if hasattr(last_message, "content") and last_message.content:
                            print(f"📝 {node_name}: {last_message.content}")

                print()

        except Exception as e:
            print(f"❌ Error in scenario {i}: {e}")

        print("=" * 80)
        print()


if __name__ == "__main__":
    main()
