"""Example of using tools with the agent."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_games_design.tools import calculator, text_analyzer


def main():
    """Demonstrate tool usage."""
    print("🔧 Tool Usage Examples\n")

    # Calculator example
    print("Calculator Tool:")
    result = calculator.invoke({"expression": "2 + 2 * 3"})
    print("  Expression: 2 + 2 * 3")
    print(f"  Result: {result}\n")

    # Text analyzer example
    print("Text Analyzer Tool:")
    text = "Hello world! This is a test. How are you?"
    result = text_analyzer.invoke({"text": text})
    print(f"  Text: {text}")
    print(f"  Analysis: {result}\n")


if __name__ == "__main__":
    main()
