"""Tests for the tools module."""

from agent_games_design.tools import calculator, text_analyzer


class TestCalculator:
    """Tests for the calculator tool."""

    def test_basic_addition(self):
        """Test basic addition."""
        result = calculator.invoke({"expression": "2 + 2"})
        assert result == "4"

    def test_complex_expression(self):
        """Test complex mathematical expression."""
        result = calculator.invoke({"expression": "2 + 2 * 3"})
        assert result == "8"

    def test_invalid_expression(self):
        """Test invalid expression handling."""
        result = calculator.invoke({"expression": "invalid"})
        assert "Error" in result


class TestTextAnalyzer:
    """Tests for the text analyzer tool."""

    def test_word_count(self):
        """Test word counting."""
        result = text_analyzer.invoke({"text": "Hello world"})
        assert result["word_count"] == 2

    def test_character_count(self):
        """Test character counting."""
        result = text_analyzer.invoke({"text": "Hello"})
        assert result["character_count"] == 5

    def test_sentence_count(self):
        """Test sentence counting."""
        result = text_analyzer.invoke({"text": "Hello. How are you? I'm fine!"})
        assert result["sentence_count"] == 3
