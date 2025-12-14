"""Enum definitions for the agent system."""

from enum import Enum


class WorkflowStage(str, Enum):
    """Stages of the ReAct workflow."""

    PLANNING = "planning"
    HUMAN_APPROVAL = "human_approval"
    REACT_EXECUTION = "react_execution"
    ASSET_GENERATION = "asset_generation"
    EVALUATION = "evaluation"
    COMPLETED = "completed"


class AssetType(str, Enum):
    """Types of game design assets."""

    CHARACTER_CONCEPT = "character_concept"
    ENVIRONMENT_ART = "environment_art"
    UI_MOCKUP = "ui_mockup"
    GAME_LOGO = "game_logo"
    ICON_SET = "icon_set"
    TEXTURE = "texture"
    SPRITE = "sprite"
    BACKGROUND = "background"
    PROMOTIONAL_ART = "promotional_art"


class ModelType(str, Enum):
    """Supported model types for asset generation."""

    GOOGLE_NANO = "google_nano"
    DALLE_3 = "dalle_3"
    MIDJOURNEY = "midjourney"
    STABLE_DIFFUSION = "stable_diffusion"
    FIREFLY = "firefly"
