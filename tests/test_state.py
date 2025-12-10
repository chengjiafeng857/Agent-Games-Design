"""Tests for the state module."""

from langchain_core.messages import AIMessage, HumanMessage

from agent_games_design.state import AgentState


class TestAgentState:
    """Tests for the AgentState."""

    def test_state_creation(self):
        """Test creating a state."""
        state: AgentState = {
            "messages": [HumanMessage(content="Hello")],
            "current_task": "test",
            "iterations": 0,
            "final_output": None,
        }

        assert len(state["messages"]) == 1
        assert state["current_task"] == "test"
        assert state["iterations"] == 0
        assert state["final_output"] is None

    def test_state_with_multiple_messages(self):
        """Test state with multiple messages."""
        state: AgentState = {
            "messages": [
                HumanMessage(content="Hello"),
                AIMessage(content="Hi there!"),
            ],
            "current_task": "conversation",
            "iterations": 1,
            "final_output": None,
        }

        assert len(state["messages"]) == 2
        assert isinstance(state["messages"][0], HumanMessage)
        assert isinstance(state["messages"][1], AIMessage)
