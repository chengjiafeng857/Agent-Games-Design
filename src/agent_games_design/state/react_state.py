"""ReAct workflow state definitions."""

from typing import Annotated, List, Optional, Dict, Any

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field

from .enums import WorkflowStage, AssetType, ModelType


class PlanStep(BaseModel):
    """A single step in the execution plan."""

    step_id: str = Field(description="Unique identifier for the step")
    title: str = Field(description="Brief title of the step")
    description: str = Field(description="Detailed description of what to do")
    expected_output: str = Field(description="What output is expected from this step")
    dependencies: List[str] = Field(default=[], description="Step IDs this depends on")
    estimated_time: str = Field(description="Estimated time to complete")
    priority: int = Field(ge=1, le=5, description="Priority level (1=highest, 5=lowest)")


class CharacterInfo(BaseModel):
    """Information about a character in the game."""

    name: str = Field(description="Name of the character")
    description: str = Field(description="Brief description of the character")


class AssetRequest(BaseModel):
    """Request for generating a specific asset."""

    asset_id: str = Field(description="Unique identifier for the asset")
    asset_type: AssetType = Field(description="Type of asset to generate")
    title: str = Field(description="Title/name of the asset")
    description: str = Field(description="Detailed description of the asset")
    style_requirements: List[str] = Field(
        default=[], description="Style and aesthetic requirements"
    )
    technical_specs: Dict[str, Any] = Field(default={}, description="Technical specifications")
    reference_images: List[str] = Field(
        default=[], description="URLs or descriptions of reference images"
    )
    target_model: ModelType = Field(description="Preferred model for generation")


class GameDesignAsset(BaseModel):
    """Generated game design asset."""

    asset_id: str = Field(description="Unique identifier matching the request")
    asset_type: AssetType = Field(description="Type of asset")
    title: str = Field(description="Title of the asset")
    generated_prompt: str = Field(description="The prompt used for generation")
    model_used: ModelType = Field(description="Model that generated this asset")
    image_url: Optional[str] = Field(default=None, description="URL to generated image")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    quality_score: Optional[float] = Field(default=None, description="Quality assessment score")


class ReActObservation(BaseModel):
    """Observation from a ReAct step."""

    step_number: int = Field(description="Step number in the ReAct sequence")
    action_taken: str = Field(description="What action was performed")
    observation: str = Field(description="What was observed/learned")
    next_thought: Optional[str] = Field(default=None, description="Next reasoning step")


class ReActState(BaseModel):
    """Complete state for the ReAct agent workflow."""

    # Core workflow state
    current_stage: WorkflowStage = Field(default=WorkflowStage.PLANNING)
    user_prompt: str = Field(description="Original user prompt about game design")
    session_id: str = Field(description="Unique session identifier")

    # Planning stage
    execution_plan: List[PlanStep] = Field(default=[], description="Detailed execution plan")
    plan_approved: Optional[bool] = Field(
        default=None, description="Whether plan was approved by human"
    )
    plan_feedback: Optional[str] = Field(default=None, description="Human feedback on the plan")

    # ReAct execution
    react_observations: List[ReActObservation] = Field(
        default=[], description="ReAct step observations"
    )
    current_thought: Optional[str] = Field(default=None, description="Current reasoning thought")
    guidelines_generated: Optional[str] = Field(
        default=None, description="Generated step-by-step guidelines"
    )
    character_list: List[CharacterInfo] = Field(
        default=[], description="List of characters identified in the design"
    )

    # Asset generation
    asset_requests: List[AssetRequest] = Field(
        default=[], description="Requests for assets to generate"
    )
    generated_assets: List[GameDesignAsset] = Field(default=[], description="Generated assets")

    # Evaluation and metadata
    evaluation_scores: Dict[str, float] = Field(
        default={}, description="LangSmith evaluation scores"
    )
    total_steps: int = Field(default=0, description="Total steps executed")
    errors: List[str] = Field(default=[], description="Any errors encountered")

    # LangGraph conversation tracking
    messages: Annotated[List[BaseMessage], add_messages] = Field(
        default=[], description="Conversation messages"
    )

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True
