"""Basic example of using the agent system."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from langchain_core.messages import HumanMessage

from agent_games_design.graphs import create_agent_graph
from agent_games_design.state import AgentState


def main():
    """Run a basic agent example."""
    # Create the agent graph
    app = create_agent_graph()

    # Initial state
    initial_state: AgentState = {
        "messages": [HumanMessage(content="What is 2 + 2? Explain your reasoning.")],
        "current_task": "Simple math problem",
        "iterations": 0,
        "final_output": None,
    }

    # Run the agent
    print("🤖 Starting Agent...\n")

    config = {"configurable": {"thread_id": "example-1"}}

    for step, output in enumerate(app.stream(initial_state, config), 1):
        print(f"Step {step}:")
        print(f"Output: {output}\n")

        if "agent" in output:
            messages = output["agent"].get("messages", [])
            if messages:
                last_message = messages[-1]
                print(f"Agent Response: {last_message.content}\n")

        print("-" * 80)

    print("\n✅ Agent completed!")


if __name__ == "__main__":
    main()
