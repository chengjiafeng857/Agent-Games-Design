"""Text analysis tool for content statistics."""

from langchain_core.tools import tool


@tool
def text_analyzer(text: str) -> dict[str, int]:
    """Analyze text and return statistics.

    Args:
        text: The text to analyze

    Returns:
        Dictionary with text statistics
    """
    words = text.split()
    return {
        "word_count": len(words),
        "character_count": len(text),
        "sentence_count": text.count(".") + text.count("!") + text.count("?"),
    }
