"""Planning agent for game design workflow."""

import json
import uuid
from typing import List, Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from ..config import settings, ModelConfig
from ..state import (
    ReActState, 
    PlanStep, 
    AssetRequest, 
    WorkflowStage, 
    AssetType, 
    ModelType,
    CharacterInfo
)


class PlanningAgent:
    """Agent responsible for creating detailed execution plans."""

    def __init__(self, model_config: Optional[ModelConfig] = None):
        """Initialize the planning agent.

        Args:
            model_config: Model configuration (defaults to settings.get_planning_config())
        """
        # Get configuration from settings if not provided
        self.config = model_config or settings.get_planning_config()
        
        # Build model kwargs from configuration
        model_kwargs = self.config.get_model_kwargs()
        
        # Initialize ChatOpenAI with standard LangChain approach
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            **model_kwargs,
        )
        
        # Bind tools if enabled
        if self.config.enable_tools:
            from ..tools import get_planning_tools
            tools = get_planning_tools()
            bind_kwargs = self.config.get_bind_tools_kwargs()
            self.llm = self.llm.bind_tools(tools, **bind_kwargs)

    def create_plan(self, state: ReActState) -> ReActState:
        """Create a detailed execution plan based on the user prompt.

        Args:
            state: Current ReAct state

        Returns:
            Updated state with execution plan
        """
        system_prompt = self._get_planning_system_prompt()
        user_message = self._create_planning_user_message(state.user_prompt)

        messages = [system_prompt, user_message]
        response = self.llm.invoke(messages)

        try:
            # Extract text content from response (handles both old and new formats)
            response_text = self._get_response_text(response)
            
            # Try to extract and parse JSON from the response
            plan_data = self._extract_json_from_response(response_text)
            
            if plan_data:
                execution_plan = self._parse_plan_steps(plan_data.get("plan_steps", []))
                asset_requests = self._parse_asset_requests(plan_data.get("asset_requests", []))
                character_list = self._parse_character_list(plan_data.get("character_list", []))

                # Update state
                state.execution_plan = execution_plan
                state.asset_requests = asset_requests
                state.character_list = character_list
                state.current_stage = WorkflowStage.HUMAN_APPROVAL
                state.messages.append(response)
            else:
                # No valid JSON found, use fallback
                raise json.JSONDecodeError("No valid JSON found in response", "", 0)

        except (json.JSONDecodeError, KeyError) as e:
            # Fallback to basic plan - don't add to errors if fallback works
            state.execution_plan = self._create_fallback_plan(state.user_prompt)
            state.current_stage = WorkflowStage.HUMAN_APPROVAL
            # Only log as debug, not as error since fallback is working

        return state

    def _get_planning_system_prompt(self) -> SystemMessage:
        """Get the system prompt for planning."""
        return SystemMessage(
            content="""
You are an expert Game Design Planning Agent. Your role is to create comprehensive, actionable execution plans for game design assignments.

CRITICAL: You MUST respond with ONLY valid JSON. No explanations, no markdown, no code blocks - just pure JSON.

INSTRUCTIONS:
1. Analyze the user's game design request thoroughly
2. Break down the work into logical, sequential steps
3. Identify all key characters in the game concept
4. Identify all assets that need to be generated
5. Provide detailed specifications for each asset
6. Consider dependencies between tasks
7. Estimate realistic timeframes

ASSET GENERATION RULES (CRITICAL):
1. **Character Assets**: Should be 'character_concept' or 'mock-up' style. Focus on personality, pose, and design.
2. **Non-Character Assets (Environment, Props, UI)**: MUST be "production-ready" texture assets.
   - Do NOT generate random concept art or mock-ups for these unless specifically asked for 'concept'.
   - Include maps: Diffuse/Albedo, Normal, Roughness/Metallic, Ambient Occlusion where applicable.
   - For UI, specify "production-ready UI element" or "sprite sheet".
   - For Environment, specify "seamless texture", "material", or "HDRI" as appropriate.

RESPONSE FORMAT - Return ONLY this JSON structure (no markdown, no code blocks):
{
    "analysis": "Brief analysis of the request and approach",
    "plan_steps": [
        {
            "step_id": "unique_id",
            "title": "Step Title", 
            "description": "Detailed description of what to do",
            "expected_output": "What should be produced",
            "dependencies": ["step_id1", "step_id2"],
            "estimated_time": "X hours/days",
            "priority": 1-5
        }
    ],
    "character_list": [
        {
            "name": "Character Name",
            "description": "Brief description of role and personality"
        }
    ],
    "asset_requests": [
        {
            "asset_id": "unique_id",
            "asset_type": "character_concept|environment_art|ui_mockup|game_logo|icon_set|texture|sprite|background|promotional_art",
            "title": "Asset Name",
            "description": "Detailed asset description. For non-characters, specify PBR maps needed.", 
            "style_requirements": ["requirement1", "requirement2"],
            "technical_specs": {
                "resolution": "1024x1024",
                "format": "PNG",
                "style": "pixel art",
                "maps": ["diffuse", "normal", "roughness"]
            },
            "reference_images": ["description1", "description2"],
            "target_model": "gemini_3_pro|google_nano|dalle_3|midjourney|stable_diffusion|firefly"
        }
    ]
}

ASSET TYPES AVAILABLE:
- character_concept: Character designs and concept art (Mock-ups OK)
- environment_art: Production-ready environment assets (textures, materials, backgrounds) - NO MOCKUPS
- ui_element: Production-ready UI elements/sprites - NO GENERIC MOCKUPS
- game_logo: Production-ready Game titles and logos
- icon_set: Production-ready UI icons and symbols
- texture: Seamless surface textures and materials
- sprite-sheet: Game sprites and animations (production-ready sheets)
- background: High-resolution background images
- promotional_art: Marketing and promotional images

MODELS AVAILABLE (in priority order):
- gemini_3_pro: HIGH-QUALITY IMAGE GENERATION - USE THIS FOR ALL VISUAL ASSETS (primary choice using Google Gemini 3 Pro Preview)
- google_nano: Alias for gemini_3_pro (legacy compatibility)
- dalle_3: Legacy DALL-E 3 (now handled by Gemini)
- midjourney: Prompt generation only (artistic/stylized prompts)
- stable_diffusion: Prompt generation only (customizable prompts)
- firefly: Prompt generation only (commercial-safe prompts)

IMPORTANT: Use "gemini_3_pro" as the target_model for ALL asset requests to generate actual images.
Other models (midjourney, stable_diffusion, firefly) will only generate prompts for manual use.

PLANNING PRINCIPLES:
1. Start with research and concept development
2. Move from general to specific
3. Create foundational assets before detailed ones
4. Plan for iterations and refinements
5. Consider technical constraints
6. Include quality assurance steps
        """
        )

    def _create_planning_user_message(self, user_prompt: str) -> HumanMessage:
        """Create the user message for planning."""
        return HumanMessage(
            content=f"""
Please create a comprehensive execution plan for this game design assignment:

USER REQUEST: {user_prompt}

Analyze the request and create a detailed step-by-step plan that includes:
1. Research and concept development phase
2. Asset generation requirements
3. Implementation guidelines
4. Quality assurance steps

Focus on creating high-quality, production-ready game design materials.
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

    def _extract_json_from_response(self, content: str) -> Optional[dict]:
        """Extract JSON from various response formats.
        
        Handles:
        - Pure JSON
        - JSON in markdown code blocks
        - JSON with surrounding text
        """
        import re
        
        # Try 1: Parse as pure JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Try 2: Extract from markdown code blocks
        # Look for ```json ... ``` or ``` ... ```
        code_block_patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
        ]
        
        for pattern in code_block_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                for match in matches:
                    try:
                        return json.loads(match)
                    except json.JSONDecodeError:
                        continue
        
        # Try 3: Look for JSON object anywhere in the text
        # Find anything that looks like { ... }
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, content, re.DOTALL)
        
        for match in matches:
            try:
                parsed = json.loads(match)
                # Verify it has the expected structure
                if isinstance(parsed, dict) and ('plan_steps' in parsed or 'asset_requests' in parsed or 'analysis' in parsed):
                    return parsed
            except json.JSONDecodeError:
                continue
        
        # No valid JSON found
        return None

    def _parse_plan_steps(self, plan_steps_data: List[dict]) -> List[PlanStep]:
        """Parse plan steps from JSON response."""
        steps = []
        for step_data in plan_steps_data:
            try:
                step = PlanStep(
                    step_id=step_data.get("step_id", str(uuid.uuid4())),
                    title=step_data.get("title", "Unknown Step"),
                    description=step_data.get("description", ""),
                    expected_output=step_data.get("expected_output", ""),
                    dependencies=step_data.get("dependencies", []),
                    estimated_time=step_data.get("estimated_time", "Unknown"),
                    priority=step_data.get("priority", 3),
                )
                steps.append(step)
            except Exception as e:
                # Skip invalid steps but log the error
                continue

        # If no valid steps, create basic fallback
        if not steps:
            steps = self._create_fallback_plan("")

        return steps

    def _parse_asset_requests(self, asset_requests_data: List[dict]) -> List[AssetRequest]:
        """Parse asset requests from JSON response."""
        requests = []
        for request_data in asset_requests_data:
            try:
                # Validate asset type
                asset_type_str = request_data.get("asset_type", "character_concept")
                try:
                    asset_type = AssetType(asset_type_str)
                except ValueError:
                    asset_type = AssetType.CHARACTER_CONCEPT

                # Validate model type
                model_type_str = request_data.get("target_model", "google_nano")
                try:
                    target_model = ModelType(model_type_str)
                except ValueError:
                    target_model = ModelType.GOOGLE_NANO

                request = AssetRequest(
                    asset_id=request_data.get("asset_id", str(uuid.uuid4())),
                    asset_type=asset_type,
                    title=request_data.get("title", "Untitled Asset"),
                    description=request_data.get("description", ""),
                    style_requirements=request_data.get("style_requirements", []),
                    technical_specs=request_data.get("technical_specs", {}),
                    reference_images=request_data.get("reference_images", []),
                    target_model=target_model,
                )
                requests.append(request)
            except Exception as e:
                # Skip invalid requests but continue
                continue

        return requests

    def _parse_character_list(self, character_data: List[dict]) -> List[CharacterInfo]:
        """Parse character list from JSON response."""
        characters = []
        for char_data in character_data:
            try:
                character = CharacterInfo(
                    name=char_data.get("name", "Unknown Character"),
                    description=char_data.get("description", "No description provided")
                )
                characters.append(character)
            except Exception:
                continue
        
        return characters

    def _create_fallback_plan(self, user_prompt: str) -> List[PlanStep]:
        """Create a basic fallback plan if parsing fails."""
        return [
            PlanStep(
                step_id="research",
                title="Research and Analysis",
                description="Analyze the game design requirements and research similar projects",
                expected_output="Research document with key findings and references",
                dependencies=[],
                estimated_time="2 hours",
                priority=1,
            ),
            PlanStep(
                step_id="concept",
                title="Concept Development",
                description="Develop core concepts and design direction",
                expected_output="Concept documentation and initial sketches",
                dependencies=["research"],
                estimated_time="3 hours",
                priority=1,
            ),
            PlanStep(
                step_id="assets",
                title="Asset Generation",
                description="Generate required game assets based on concepts",
                expected_output="Complete set of game assets",
                dependencies=["concept"],
                estimated_time="4 hours",
                priority=2,
            ),
            PlanStep(
                step_id="guidelines",
                title="Implementation Guidelines",
                description="Create detailed implementation guidelines",
                expected_output="Step-by-step implementation guide",
                dependencies=["assets"],
                estimated_time="2 hours",
                priority=2,
            ),
        ]
