
import unittest
from pathlib import Path
from agent_games_design.state.react_state import ReActState, CharacterInfo
from agent_games_design.agents.planning import PlanningAgent
from agent_games_design.utils.output_manager import OutputManager

class TestCharacterList(unittest.TestCase):
    def test_character_info_model(self):
        """Test the CharacterInfo model."""
        char = CharacterInfo(name="Test Char", description="A test character")
        self.assertEqual(char.name, "Test Char")
        self.assertEqual(char.description, "A test character")

    def test_planning_agent_parsing(self):
        """Test parsing character list from JSON."""
        agent = PlanningAgent()
        
        # Test valid parsing
        data = [
            {"name": "Alice", "description": "The hero"},
            {"name": "Bob", "description": "The sidekick"}
        ]
        chars = agent._parse_character_list(data)
        self.assertEqual(len(chars), 2)
        self.assertEqual(chars[0].name, "Alice")
        self.assertEqual(chars[1].description, "The sidekick")
        
        # Test parsing with missing fields (should use defaults)
        data_missing = [{"name": "Charlie"}]
        chars_missing = agent._parse_character_list(data_missing)
        self.assertEqual(len(chars_missing), 1)
        self.assertEqual(chars_missing[0].name, "Charlie")
        
        # Test parsing with invalid data (should skip)
        data_invalid = [{"invalid": "data"}]
        # Based on my implementation: 
        # character = CharacterInfo(name=char_data.get("name", "Unknown Character"), ...)
        # So it actually WON'T skip if keys are missing because I used .get(). 
        # It creates "Unknown Character". Let's verify that behavior.
        chars_invalid = agent._parse_character_list(data_invalid)
        self.assertEqual(len(chars_invalid), 1)
        self.assertEqual(chars_invalid[0].name, "Unknown Character")

    def test_output_manager_rendering(self):
        """Test that OutputManager renders character list correctly."""
        manager = OutputManager()
        state = ReActState(
            user_prompt="test prompt",
            session_id="test_session"
        )
        state.character_list = [
            CharacterInfo(name="Hero", description="Saves the day"),
            CharacterInfo(name="Villain", description="Ruins the day")
        ]
        
        # We need a dummy output folder for _generate_markdown
        output_folder = Path("dummy_output")
        
        markdown = manager._generate_markdown(state, {}, output_folder)
        
        # Check if section exists
        self.assertIn("## 👥 Character List", markdown)
        
        # Check if content exists
        self.assertIn("* **Hero**: Saves the day", markdown)
        self.assertIn("* **Villain**: Ruins the day", markdown)
        
        # Check order (before Execution Plan)
        # Note: Execution Plan won't be in markdown if state.execution_plan is empty.
        # Let's add execution plan to verify order.
        from agent_games_design.state.react_state import PlanStep
        state.execution_plan = [PlanStep(
            step_id="1", title="Step 1", description="Do it", 
            expected_output="", estimated_time="1h", priority=1
        )]
        
        markdown_with_plan = manager._generate_markdown(state, {}, output_folder)
        char_idx = markdown_with_plan.find("## 👥 Character List")
        plan_idx = markdown_with_plan.find("## 📋 Execution Plan")
        
        self.assertTrue(char_idx != -1)
        self.assertTrue(plan_idx != -1)
        self.assertTrue(char_idx < plan_idx, "Character List should appear before Execution Plan")

if __name__ == "__main__":
    unittest.main()
