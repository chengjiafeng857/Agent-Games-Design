"""ReAct executor for game design workflow."""

import re
from typing import Optional, Tuple

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from ..config import settings, ModelConfig
from ..state import (
    ReActState, 
    ReActObservation, 
    WorkflowStage
)


class ReActExecutor:
    """Executes the ReAct (Reasoning + Acting) pattern for game design."""

    def __init__(self, model_config: Optional[ModelConfig] = None):
        """Initialize the ReAct executor.

        Args:
            model_config: Model configuration (defaults to settings.get_react_config())
        """
        # Get configuration from settings if not provided
        self.config = model_config or settings.get_react_config()
        
        # Build model kwargs from configuration
        model_kwargs = self.config.get_model_kwargs()
        
        # Initialize ChatOpenAI with standard LangChain approach
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            **model_kwargs,
        )
        
        # Bind tools if enabled
        if self.config.enable_tools:
            from ..tools import get_react_tools
            tools = get_react_tools()
            bind_kwargs = self.config.get_bind_tools_kwargs()
            self.llm = self.llm.bind_tools(tools, **bind_kwargs)
        
        self.max_iterations = 10  # Prevent infinite loops

    def execute_react_workflow(self, state: ReActState) -> ReActState:
        """Execute the complete ReAct workflow.

        Args:
            state: Current ReAct state with approved execution plan

        Returns:
            Updated state with generated guidelines and observations
        """
        system_prompt = self._get_react_system_prompt()
        initial_message = self._create_initial_react_message(state)

        messages = [system_prompt, initial_message]
        current_iteration = 0

        while current_iteration < self.max_iterations:
            current_iteration += 1

            # Get AI response
            response = self.llm.invoke(messages)
            messages.append(response)

            # Extract text content from response (handles both old and new formats)
            response_text = self._get_response_text(response)

            # Parse the response for Thought, Action, and Observation
            thought, action, final_answer = self._parse_react_response(response_text)

            if final_answer:
                # We have a final answer - workflow complete
                state.guidelines_generated = final_answer
                state.current_stage = WorkflowStage.ASSET_GENERATION
                break

            if action:
                # Execute the action and get observation
                observation = self._execute_action(action, state)

                # Record the ReAct step
                react_obs = ReActObservation(
                    step_number=current_iteration,
                    action_taken=action,
                    observation=observation,
                    next_thought=thought,
                )
                state.react_observations.append(react_obs)

                # Add observation to conversation
                obs_message = HumanMessage(content=f"Observation: {observation}")
                messages.append(obs_message)

            # Update current thought
            if thought:
                state.current_thought = thought

            # Safety check - if we're not making progress, break
            if len(state.react_observations) > 0 and not action:
                break

        # Update total steps
        state.total_steps = current_iteration

        # If we didn't get a final answer, create one from observations
        if not state.guidelines_generated:
            state.guidelines_generated = self._synthesize_guidelines_from_observations(state)
            state.current_stage = WorkflowStage.ASSET_GENERATION

        return state

    def _get_react_system_prompt(self) -> SystemMessage:
        """Get the system prompt for ReAct execution."""
        return SystemMessage(
            content="""
You are a Game Design Expert using the ReAct (Reasoning + Acting) methodology to create a comprehensive game design with guidelines.

Use this format for your responses:
Thought: [Your reasoning about what to do next]
Action: [Specific action to take - research, analyze, define, etc.]

OR when you have enough information:
Final Answer: [Complete step-by-step game design guidelines]

Available actions:
- research_game_mechanics: Research relevant game mechanics
- analyze_target_audience: Analyze target user base
- study_similar_games: Research comparable games
- define_core_gameplay: Define core game loops
- create_progression_system: Design player advancement
- design_ui_ux: Design user interface
- plan_technical_architecture: Plan implementation
- create_art_direction: Define visual style
- art_assets_prompts: Define specific prompts for the art assets
- develop_narrative: Create story elements

Guidelines for your Final Answer:
- Provide comprehensive, step-by-step implementation guidelines
- Include specific recommendations for each aspect
- Consider both creative and technical aspects
- Make guidelines actionable and practical
- Organize content logically with clear headers
- Include estimated timelines and priorities
        """
        )

    def _create_initial_react_message(self, state: ReActState) -> HumanMessage:
        """Create the initial message to start ReAct execution."""
        plan_summary = "\n".join(
            [f"- {step.title}: {step.description}" for step in state.execution_plan]
        )

        assets_summary = "\n".join(
            [
                f"- {asset.title} ({asset.asset_type.value}): {asset.description}"
                for asset in state.asset_requests
            ]
        )

        return HumanMessage(
            content=f"""
I need you to create comprehensive, step-by-step game design guidelines for this project:

USER REQUEST: {state.user_prompt}

APPROVED EXECUTION PLAN:
{plan_summary}

ASSETS TO BE GENERATED:
{assets_summary}

Please use the ReAct methodology to research, analyze, and develop detailed guidelines. Start by thinking about what aspects of the project you need to research first.
        """
        )

    def _get_response_text(self, response) -> str:
        """Extract text content from response, handling both v0 and v1 formats.
        
        Args:
            response: LangChain AIMessage response
            
        Returns:
            String content from the response
        """
        # Check if content is a list (Responses API v1 format)
        if isinstance(response.content, list):
            # Extract text from content blocks
            text_parts = []
            for block in response.content:
                if isinstance(block, dict):
                    # Handle v1 format with type field
                    if block.get("type") == "text" and "text" in block:
                        text_parts.append(block["text"])
                elif isinstance(block, str):
                    # Sometimes blocks might be plain strings
                    text_parts.append(block)
            return "\n".join(text_parts)
        else:
            # Old format: content is already a string
            return str(response.content)

    def _parse_react_response(
        self, response: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse a ReAct response to extract Thought, Action, and Final Answer.

        Args:
            response: The AI response text

        Returns:
            Tuple of (thought, action, final_answer)
        """
        thought = None
        action = None
        final_answer = None

        # Extract Thought
        thought_match = re.search(
            r"Thought:\s*(.+?)(?=\n(?:Action|Observation|Final Answer)|\Z)",
            response,
            re.DOTALL | re.IGNORECASE,
        )
        if thought_match:
            thought = thought_match.group(1).strip()

        # Extract Action
        action_match = re.search(
            r"Action:\s*(.+?)(?=\n(?:Observation|Thought|Final Answer)|\Z)",
            response,
            re.DOTALL | re.IGNORECASE,
        )
        if action_match:
            action = action_match.group(1).strip()

        # Extract Final Answer
        final_match = re.search(r"Final Answer:\s*(.+)", response, re.DOTALL | re.IGNORECASE)
        if final_match:
            final_answer = final_match.group(1).strip()

        return thought, action, final_answer

    def _execute_action(self, action: str, state: ReActState) -> str:
        """Execute a ReAct action and return the observation.

        Args:
            action: The action to execute
            state: Current ReAct state

        Returns:
            Observation text from executing the action
        """
        action_lower = action.lower()

        if "research_game_mechanics" in action_lower:
            return self._research_game_mechanics(action, state)
        elif "analyze_target_audience" in action_lower:
            return self._analyze_target_audience(action, state)
        elif "study_similar_games" in action_lower:
            return self._study_similar_games(action, state)
        elif "define_core_gameplay" in action_lower:
            return self._define_core_gameplay(action, state)
        elif "create_progression_system" in action_lower:
            return self._create_progression_system(action, state)
        elif "plan_monetization" in action_lower:
            return self._plan_monetization(action, state)
        elif "design_ui_ux" in action_lower:
            return self._design_ui_ux(action, state)
        elif "plan_technical_architecture" in action_lower:
            return self._plan_technical_architecture(action, state)
        elif "create_art_direction" in action_lower:
            return self._create_art_direction(action, state)
        elif "develop_narrative" in action_lower:
            return self._develop_narrative(action, state)
        else:
            return f"Executed general research action: {action}. Gathered relevant information for the project."

    def _research_game_mechanics(self, action: str, state: ReActState) -> str:
        """Research game mechanics relevant to the project."""
        return f"""Researched game mechanics for the project:
- Identified core mechanical systems that align with the game concept
- Analyzed interaction patterns and feedback loops
- Evaluated complexity vs. accessibility balance
- Considered platform-specific mechanical constraints
- Researched innovative mechanics in similar games
- Mechanics should support the overall game vision and theme
- Important to prototype and test mechanics early in development"""

    def _analyze_target_audience(self, action: str, state: ReActState) -> str:
        """Analyze target audience for the game."""
        return f"""Analyzed target audience characteristics:
- Identified primary demographic: age range, gaming experience, platform preferences
- Analyzed player motivations and pain points
- Researched spending patterns and monetization preferences
- Studied engagement patterns and session lengths
- Identified accessibility requirements and considerations
- Analyzed cultural and regional preferences if relevant
- Market size and competition landscape evaluated
- User acquisition and retention strategies outlined"""

    def _study_similar_games(self, action: str, state: ReActState) -> str:
        """Study similar games for best practices."""
        return f"""Studied comparable games in the market:
- Analyzed successful games in the same genre/category
- Identified common design patterns and player expectations
- Studied monetization models and their effectiveness
- Reviewed user feedback and common complaints
- Analyzed art styles, UI/UX patterns, and technical approaches
- Identified market gaps and opportunities for differentiation
- Found inspiration for unique features and differentiation
- Documented technical and design lessons learned"""

    def _define_core_gameplay(self, action: str, state: ReActState) -> str:
        """Define core gameplay elements."""
        return f"""Defined core gameplay elements:
- Primary gameplay loop identified and refined
- Secondary systems and their interaction with core loop
- Player goals, challenges, and rewards structure
- Key player actions and input methods
- Victory/failure conditions and game progression
- Pacing and difficulty progression planned
- Core mechanics interaction patterns defined"""

    def _create_progression_system(self, action: str, state: ReActState) -> str:
        """Create player progression system."""
        return f"""Created player progression framework:
- Short-term and long-term progression goals defined
- Skill development and mastery curve planned
- Unlock system for content, features, and customization
- Achievement and milestone system designed
- Player retention mechanics and comeback systems
- Long-term engagement and retention hooks identified
- Balance between challenge and reward established"""

    def _plan_monetization(self, action: str, state: ReActState) -> str:
        """Plan monetization strategy."""
        return f"""Planned monetization approach:
- Revenue model selection based on game type and audience
- In-app purchase strategy and pricing tiers
- Advertisement integration points and frequency
- Premium content and cosmetic item strategies  
- Subscription model considerations if applicable
- Ethical considerations and player fairness addressed
- Pricing strategy and market positioning determined"""

    def _design_ui_ux(self, action: str, state: ReActState) -> str:
        """Design user interface and experience."""
        return f"""Designed UI/UX framework:
- Information architecture and screen flow designed
- Input methods and control scheme optimized
- Visual hierarchy and accessibility considerations
- Platform-specific UI guidelines and constraints
- Responsive design for different screen sizes
- Onboarding and tutorial experience designed
- Feedback systems and visual indicators specified"""

    def _plan_technical_architecture(self, action: str, state: ReActState) -> str:
        """Plan technical implementation."""
        return f"""Planned technical architecture:
- Engine and framework selection with rationale
- Platform deployment strategy and requirements
- Performance optimization targets and constraints
- Backend services and infrastructure needs
- Data storage and synchronization requirements
- Security and privacy implementation plan
- Scalability and maintenance requirements planned
- Integration points and third-party services documented"""

    def _create_art_direction(self, action: str, state: ReActState) -> str:
        """Create art direction guidelines."""
        return f"""Created art direction framework:
- Visual style and aesthetic direction defined
- Color palette and visual mood established
- Character design principles and style guides
- Environment art style and technical constraints
- UI visual design language and component library
- Animation style and technical requirements specified
- Brand consistency and visual identity guidelines created"""

    def _develop_narrative(self, action: str, state: ReActState) -> str:
        """Develop narrative elements."""
        return f"""Developed narrative framework:
- Core story concept and thematic elements defined
- Character development and relationship dynamics
- World-building and lore integration with gameplay
- Dialogue system and writing style guidelines
- Narrative progression and pacing considerations
- Environmental storytelling and lore integration designed
- Localization and cultural considerations addressed"""

    def _synthesize_guidelines_from_observations(self, state: ReActState) -> str:
        """Create guidelines from ReAct observations if no final answer was reached."""
        observations_text = "\n".join(
            [
                f"Step {obs.step_number}: {obs.action_taken} - {obs.observation}"
                for obs in state.react_observations
            ]
        )

        return f"""# Game Design Guidelines

## Project Overview
Based on the user request: {state.user_prompt}

## Research and Analysis Summary
{observations_text}

## Implementation Recommendations
1. Start with core gameplay mechanics and test early
2. Develop assets in parallel with gameplay programming  
3. Iterate on user feedback throughout development
4. Plan for testing and iteration cycles
        """
