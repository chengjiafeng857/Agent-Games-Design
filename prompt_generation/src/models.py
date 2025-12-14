# models.py - Data Models for the Character Prompt Pipeline
#
# This module defines the core data structures used throughout the pipeline.
# We use Python's @dataclass decorator for clean, type-safe data containers.
#
# Pipeline role: This is the INPUT stage - we load character specs from files.

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import json
import logging

# We use PyYAML to parse YAML files (human-friendly config format)
import yaml

# -----------------------------------------------------------------------------
# LOGGING SETUP
# -----------------------------------------------------------------------------
# We set up a logger to warn users when optional fields are missing.
# This is better than silent failures - users know what's happening.

logging.basicConfig(
    level=logging.INFO,                          # Show INFO level and above
    format="%(levelname)s: %(message)s"          # Simple format: "WARNING: message"
)
logger = logging.getLogger(__name__)             # Create logger for this module


# -----------------------------------------------------------------------------
# CHARACTER SPECIFICATION DATACLASS
# -----------------------------------------------------------------------------
# @dataclass automatically generates __init__, __repr__, and other methods.
# This saves us from writing boilerplate code.

@dataclass
class CharacterSpec:
    """
    Data model for a character specification.
    
    This class holds all the information about a character that will be
    used to generate prompts for 2D image generation and 3D modeling.
    
    Attributes:
        name: The character's name (required, used in filenames)
        role: What the character does, e.g., "Android archaeologist"
        game_style: Visual style, e.g., "stylized sci-fi"
        silhouette: Body shape description, e.g., "tall, long coat"
        color_palette: List of main colors for the character
        key_props: List of items the character carries
        animation_focus: Types of animations planned for rigging
        extra_notes: Any additional context for prompt generation
    """
    
    # REQUIRED FIELD: Every character must have a name.
    # No default value means this field must be provided.
    name: str
    
    # OPTIONAL FIELDS: These have default values.
    # If not provided in the YAML/JSON, they'll use these defaults.
    
    # Role describes what the character does in the game world.
    role: str = ""
    
    # Game style affects the visual rendering style of prompts.
    game_style: str = ""
    
    # Silhouette is crucial for 3D modeling - it defines the character's shape.
    silhouette: str = ""
    
    # color_palette is a list of strings like ["teal", "black", "orange accents"].
    # We use field(default_factory=list) instead of = [] because:
    # - Using = [] would share the same list across ALL instances (bug!)
    # - default_factory=list creates a NEW empty list for each instance (correct!)
    color_palette: list[str] = field(default_factory=list)
    
    # key_props lists items the character carries (for prompts like "holding X").
    key_props: list[str] = field(default_factory=list)
    
    # animation_focus helps ensure the design supports planned movements.
    animation_focus: list[str] = field(default_factory=list)
    
    # extra_notes is free-form text for any additional context.
    # Optional[str] means it can be either a string or None.
    extra_notes: Optional[str] = None


# -----------------------------------------------------------------------------
# FILE LOADING FUNCTION
# -----------------------------------------------------------------------------

def load_character_spec(path: Path) -> CharacterSpec:
    """
    Load a character specification from a YAML or JSON file.
    
    This function:
    1. Reads the file from disk
    2. Parses it based on file extension (.yaml, .yml, or .json)
    3. Validates the required 'name' field exists
    4. Logs warnings for any missing optional fields
    5. Returns a CharacterSpec instance
    
    Args:
        path: Path to the character spec file (can be Path or string)
        
    Returns:
        A CharacterSpec instance populated with data from the file
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file format is unsupported or 'name' is missing
        
    Example:
        >>> spec = load_character_spec(Path("configs/aethel.yaml"))
        >>> print(spec.name)
        Aethel
    """
    
    # Step 1: Validate the file exists before trying to read it.
    # This gives a clearer error message than just letting open() fail.
    if not path.exists():
        raise FileNotFoundError(f"Character spec not found: {path}")
    
    # Step 2: Read the entire file content as a UTF-8 string.
    # encoding="utf-8" ensures we handle special characters correctly.
    content = path.read_text(encoding="utf-8")
    
    # Step 3: Determine file format by looking at the extension.
    # .suffix returns ".yaml", ".json", etc.
    # .lower() makes it case-insensitive (handles .YAML, .Yaml, etc.)
    suffix = path.suffix.lower()
    
    # Step 4: Parse the content based on file type.
    if suffix in (".yaml", ".yml"):
        # yaml.safe_load() is safer than yaml.load() - it doesn't execute code.
        # The "or {}" handles the case where the file is empty (returns None).
        data = yaml.safe_load(content) or {}
        
    elif suffix == ".json":
        # json.loads() parses a JSON string into a Python dictionary.
        data = json.loads(content)
        
    else:
        # Reject unknown file formats with a helpful error message.
        raise ValueError(
            f"Unsupported file format: {suffix}. "
            "Use .yaml, .yml, or .json"
        )
    
    # Step 5: Validate the required 'name' field.
    # A character without a name is not useful - we need it for filenames.
    if "name" not in data or not data["name"]:
        raise ValueError("Character spec must have a 'name' field")
    
    # Step 6: Log warnings for missing optional fields.
    # This helps users know what they might have forgotten.
    optional_fields = [
        "role",
        "game_style", 
        "silhouette",
        "color_palette",
        "key_props",
        "animation_focus",
        "extra_notes"
    ]
    
    for field_name in optional_fields:
        if field_name not in data:
            # logger.warning() outputs to stderr with "WARNING:" prefix.
            logger.warning(f"Missing field '{field_name}' - using default value")
    
    # Step 7: Create and return the CharacterSpec instance.
    # .get(key, default) returns the value if key exists, otherwise default.
    return CharacterSpec(
        name=data["name"],
        role=data.get("role", ""),
        game_style=data.get("game_style", ""),
        silhouette=data.get("silhouette", ""),
        color_palette=data.get("color_palette", []),
        key_props=data.get("key_props", []),
        animation_focus=data.get("animation_focus", []),
        extra_notes=data.get("extra_notes"),  # None if missing (no default needed)
    )

