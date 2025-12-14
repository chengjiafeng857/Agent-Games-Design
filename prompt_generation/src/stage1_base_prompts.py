# stage1_base_prompts.py - Stage 1: Base 2D Concept Prompts
#
# Pipeline Stage: TEXT SPEC → [2D PROMPTS] → Gemini T-pose → Checklist
#                              ^^^^^^^^^^^
#                              THIS STAGE
#
# This module generates base prompts for any 2D image generation model.
# These prompts are generic and can be used with Midjourney, DALL-E, 
# Stable Diffusion, or any other text-to-image tool.
#
# Output files:
#   - {name}_2d_base_{version}.txt   - Full-body concept prompt
#   - {name}_2d_sheet_{version}.txt  - Multi-view character sheet prompt

from typing import Optional

from .models import CharacterSpec


# -----------------------------------------------------------------------------
# HELPER FUNCTIONS: Format CharacterSpec fields for use in prompts
# -----------------------------------------------------------------------------
# These functions convert raw data into natural-sounding prompt phrases.
# Keeping them separate makes the code easier to test and modify.

def format_color_palette(colors: list[str]) -> str:
    """
    Format a list of colors into a comma-separated string.
    
    Args:
        colors: List of color strings, e.g., ["teal", "black", "orange accents"]
        
    Returns:
        A formatted string like "teal, black, orange accents"
        Returns "unspecified" if the list is empty.
        
    Example:
        >>> format_color_palette(["red", "blue"])
        "red, blue"
        >>> format_color_palette([])
        "unspecified"
    """
    # Handle empty list case - return a placeholder
    if not colors:
        return "unspecified"
    
    # Join list items with ", " separator
    # ["a", "b", "c"] -> "a, b, c"
    return ", ".join(colors)


def format_key_props(props: list[str]) -> str:
    """
    Format a list of props into a natural English phrase.
    
    We want prompts to read naturally, so we add "a/an" and "and".
    
    Args:
        props: List of prop strings, e.g., ["data tablet", "scanner"]
        
    Returns:
        A natural phrase like "a data tablet and a scanner"
        Returns empty string if no props.
        
    Examples:
        >>> format_key_props([])
        ""
        >>> format_key_props(["sword"])
        "a sword"
        >>> format_key_props(["sword", "shield"])
        "a sword and a shield"
        >>> format_key_props(["sword", "shield", "helmet"])
        "a sword, a shield, and a helmet"
    """
    # Case 1: Empty list - return empty string to allow conditional checks
    if not props:
        return ""
    
    # Case 2: Single item - just add "a"
    if len(props) == 1:
        return f"a {props[0]}"
    
    # Case 3: Two items - use "and" between them
    if len(props) == 2:
        return f"a {props[0]} and a {props[1]}"
    
    # Case 4: Three or more items - use Oxford comma style
    # ["X", "Y", "Z"] -> "a X, a Y, and a Z"
    
    # Add "a " to each item except the last
    items_with_article = [f"a {prop}" for prop in props[:-1]]
    
    # Join them with commas, then add ", and a <last item>"
    return ", ".join(items_with_article) + f", and a {props[-1]}"


def format_animation_focus(anims: list[str]) -> str:
    """
    Format animation types into a comma-separated string.
    
    Args:
        anims: List of animation types, e.g., ["walk", "idle", "attack"]
        
    Returns:
        A formatted string like "walk, idle, attack"
        Returns "standard animations" if the list is empty.
    """
    if not anims:
        return "standard animations"
    
    return ", ".join(anims)


def format_extra_notes(notes: Optional[str]) -> str:
    """
    Format extra notes, handling None values.
    
    Args:
        notes: Optional string with extra notes
        
    Returns:
        The notes string, or empty string if notes is None/empty
    """
    # In Python, empty strings and None are both "falsy"
    # So "if notes" handles both cases
    # Return empty string to allow conditional checks in calling code
    return notes if notes else ""


# -----------------------------------------------------------------------------
# STAGE 1 PROMPT GENERATORS
# -----------------------------------------------------------------------------

def generate_base_2d_full_body(spec: CharacterSpec) -> str:
    """
    Generate a base 2D full-body concept art prompt.
    
    This prompt is designed to create a single, clear character image
    that can be used as initial concept art or reference.
    
    Template structure:
        "full-body concept art of a {role}, {style}, {silhouette}, 
         color palette {colors}, holding {props}, front view, 
         neutral pose, simple background, high detail, 
         game-ready character concept, no text, no logo"
         
    Args:
        spec: The character specification
        
    Returns:
        A formatted prompt string ready to paste into any 2D image generator
    """
    # Pre-format the spec fields using our helper functions
    color_str = format_color_palette(spec.color_palette)
    props_str = format_key_props(spec.key_props)
    
    # Build the prompt using an f-string
    # We break it into multiple lines for readability (Python joins them)
    prompt = (
        f"full-body concept art of a {spec.role}, "      # WHO: Character role
        f"{spec.game_style}, "                            # STYLE: Visual style
        f"{spec.silhouette}, "                            # SHAPE: Body description
        f"color palette {color_str}, "                    # COLORS: Main colors
    )
    
    # Add props if present
    if props_str:
        prompt += f"holding {props_str}, "
    
    prompt += (
        f"front view, "                                   # ANGLE: Camera angle
        f"neutral pose, "                                 # POSE: Standing pose
        f"simple background, "                            # BG: Clean background
        f"high detail, "                                  # QUALITY: Detail level
        f"game-ready character concept, "                 # PURPOSE: Game art
        f"no text, no logo"                               # EXCLUDE: Unwanted elements
    )
    
    return prompt


def generate_base_2d_sheet(spec: CharacterSpec) -> str:
    """
    Generate a base 2D character sheet prompt (multi-view).
    
    Character sheets show the character from multiple angles on one canvas.
    This is useful for establishing consistent design across views.
    
    Template structure:
        "character sheet of {name}, a {role}, {style}, 
         including front and side views on a single canvas, 
         clear {silhouette}, neutral pose, simple light background, 
         high detail, consistent design, no text, no logo"
         
    Args:
        spec: The character specification
        
    Returns:
        A formatted prompt string for generating a character sheet
    """
    prompt = (
        f"character sheet of {spec.name}, "              # WHO: Character name
        f"a {spec.role}, "                               # ROLE: What they do
        f"{spec.game_style}, "                           # STYLE: Visual style
        f"including front and side views on a single canvas, "  # VIEWS: Multiple angles
        f"clear {spec.silhouette}, "                     # SHAPE: Distinct silhouette
        f"neutral pose, "                                # POSE: Standard pose
        f"simple light background, "                     # BG: Clean background
        f"high detail, "                                 # QUALITY: Detail level
        f"consistent design, "                           # CONSISTENCY: Same across views
        f"no text, no logo"                              # EXCLUDE: Unwanted elements
    )
    
    return prompt


# -----------------------------------------------------------------------------
# MAIN EXPORT FUNCTION
# -----------------------------------------------------------------------------

def generate_base_prompts(spec: CharacterSpec) -> dict[str, str]:
    """
    Generate all Stage 1 (Base 2D) prompts for a character.
    
    This is the main function other modules should call.
    It returns a dictionary mapping prompt keys to prompt content.
    
    Args:
        spec: The character specification
        
    Returns:
        A dictionary with keys:
        - "base_2d_full_body": Full-body concept prompt
        - "base_2d_sheet": Multi-view character sheet prompt
        
    Example:
        >>> prompts = generate_base_prompts(spec)
        >>> print(prompts["base_2d_full_body"])
        "full-body concept art of a..."
    """
    return {
        "base_2d_full_body": generate_base_2d_full_body(spec),
        "base_2d_sheet": generate_base_2d_sheet(spec),
    }

