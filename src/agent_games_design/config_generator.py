"""Module for generating character configuration from text GDD."""

import logging
from typing import List, Optional

import yaml
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from .config import settings

logger = logging.getLogger(__name__)


class CharacterConfig(BaseModel):
    """Character configuration model matching aethel.yaml structure with strict criteria."""
    
    name: str = Field(
        description="The character's name. Criteria: 1-3 words, alphanumeric/spaces/hyphens only, no special chars."
    )
    role: str = Field(
        description="What the character does. Criteria: 2-5 words, [adjective] + [occupation], "
                    "no full sentences/backstory. Example: 'Android archaeologist'"
    )
    game_style: str = Field(
        description="Visual art style. Criteria: 2-6 words, [genre/era] + [rendering style], "
                    "no color descriptions. Example: 'stylized sci-fi, slightly realistic'"
    )
    silhouette: str = Field(
        description="Body shape/outline. Criteria: 3-8 words, [body type] + [distinctive features], "
                    "no colors/textures. Example: 'tall, long coat, mechanical arm'"
    )
    color_palette: List[str] = Field(
        default_factory=list, 
        description="List of 2-5 main colors. Format: [color name] or [color name + usage]. "
                    "Example: ['teal', 'black', 'orange accents']"
    )
    key_props: List[str] = Field(
        default_factory=list, 
        description="List of 1-4 items carried on body. Format: [item] + [body location]. "
                    "MUST specify location (hip, back, belt). NOT held in hands. "
                    "Example: ['data tablet on left hip', 'arm-mounted scanner']"
    )
    animation_focus: List[str] = Field(
        default_factory=list, 
        description="List of 2-6 animation types. Simple verbs. "
                    "Example: ['walk', 'idle scanning', 'simple attack']"
    )
    extra_notes: Optional[str] = Field(
        None, 
        description="Additional context (1-3 sentences). Include environment/setting or expression. "
                    "Example: 'Set in a neon-lit cyber-ruin environment, neutral expression.'"
    )


class CharacterList(BaseModel):
    """Container for multiple character configurations."""
    characters: List[CharacterConfig] = Field(description="List of characters identified in the text")


def generate_config_from_text(text: str, model_name: Optional[str] = None) -> List[tuple[str, str]]:
    """
    Generate YAML configurations from a text description using an LLM.
    Supports detecting multiple characters.
    
    Args:
        text: The text description of the character(s) (GDD).
        model_name: The OpenAI model to use (defaults to settings.default_model).
        
    Returns:
        A list of tuples, where each tuple contains:
        - The character's sanitized name (for filename).
        - The YAML string configuration.
    """
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set.")

    model = model_name or settings.default_model
    logger.info(f"Generating config using model: {model}")

    llm = ChatOpenAI(
        model=model,
        temperature=0.0,
        api_key=settings.openai_api_key
    )
    
    structured_llm = llm.with_structured_output(CharacterList)
    
    prompt = (
        "You are an expert Game Technical Artist. Extract ALL character specifications from the input text "
        "and format them EXACTLY according to the schema constraints.\n\n"
        "STRICT GUIDELINES:\n"
        "1. Name: 1-3 words only. No titles like 'Mr.' unless part of the name.\n"
        "2. Role: Noun phrase only (e.g., 'Cybernetic Ninja'), NO full sentences.\n"
        "3. Game Style: describing rendering style (e.g., 'stylized, cel-shaded'), NOT colors.\n"
        "4. Silhouette: Focus on SHAPE. No colors or inner details.\n"
        "5. Key Props: MUST include body location (e.g., 'on back', 'on belt'). Items must be attached, NOT held.\n"
        "6. Animation Focus: Simple verbs (e.g., 'run', 'attack').\n"
        "7. Inference: If details are missing, infer them based on the character's role and style.\n"
        "8. MULTIPLE CHARACTERS: If the text describes multiple distinct characters (e.g. a protagonist and a sidekick), extract ALL of them.\n\n"
        f"Input Text:\n{text}"
    )
    
    try:
        result: CharacterList = structured_llm.invoke(prompt)
        
        configs = []
        for char_config in result.characters:
            # Convert to dictionary and exclude None values
            config_dict = char_config.model_dump(exclude_none=True)
            
            # Generate YAML
            yaml_str = yaml.dump(config_dict, sort_keys=False, allow_unicode=True)
            
            # Sanitize name for filename use
            safe_name = "".join(c for c in char_config.name if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
            
            configs.append((safe_name, yaml_str))
            
        return configs
        
    except Exception as e:
        logger.error(f"Error generating config: {e}")
        raise RuntimeError(f"Failed to generate config from text: {e}")
