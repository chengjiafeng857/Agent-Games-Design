# stage2_gemini_prompts.py - Stage 2: Gemini NanoBanana Pro T-pose Refinement
#
# Pipeline Stage: Text Spec → 2D Prompts → [GEMINI T-POSE] → Checklist
#                                           ^^^^^^^^^^^^^^^
#                                           THIS STAGE
#
# This module generates META-PROMPTS for Gemini NanoBanana Pro.
# A meta-prompt is a prompt that asks an AI to generate ANOTHER prompt.
#
# Why meta-prompts? 
#   - Gemini can refine and improve our base prompts
#   - It can generate T-pose-specific prompts optimized for 3D modeling
#   - The output can be directly used in 2D image generators
#
# Output files:
#   - {name}_2d_refiner_{version}.txt   - Meta-prompt for prompt refinement
#   - {name}_tpose_prompt_{version}.txt - Meta-prompt for T-pose generation

from .models import CharacterSpec

# Import helper functions from stage1 to avoid code duplication
# DRY principle: Don't Repeat Yourself
from .stage1_base_prompts import (
    format_color_palette,
    format_key_props,
    format_animation_focus,
    format_extra_notes,
)


# -----------------------------------------------------------------------------
# STAGE 2 PROMPT GENERATORS
# -----------------------------------------------------------------------------

def generate_gemini_2d_refiner(spec: CharacterSpec) -> str:
    """
    Generate a meta-prompt for Gemini to refine 2D image prompts.
    
    This prompt asks Gemini to act as an "expert prompt engineer" and
    rewrite our character spec into a polished, optimized prompt for
    2D image generation models.
    
    The output from Gemini will be a refined prompt that you can
    paste directly into Midjourney, DALL-E, Stable Diffusion, etc.
    
    Key requirements we ask Gemini to ensure:
        - Clear silhouette (important for 3D modeling reference)
        - Neutral pose (easier to convert to 3D)
        - Simple background (easier to extract character)
        - No overlays or text (clean reference image)
    
    Args:
        spec: The character specification
        
    Returns:
        A meta-prompt string to paste into Gemini NanoBanana Pro
    """
    # Pre-format all the spec fields
    color_str = format_color_palette(spec.color_palette)
    props_str = format_key_props(spec.key_props)
    anim_str = format_animation_focus(spec.animation_focus)
    notes_str = format_extra_notes(spec.extra_notes)
    
    # Build the meta-prompt using a multi-line f-string
    # We structure it as:
    #   1. Role assignment (tell Gemini who to be)
    #   2. Task description (what to do)
    #   3. Character spec data (the information to work with)
    
    prompt = f"""You are an expert game art prompt engineer. Given the following character specification, rewrite and refine a prompt for a 2D image model to produce a clean, full-body front-view concept of this character. The result must be suitable as reference for 3D modeling (clear silhouette, neutral pose, simple background, no overlays or text). Output only the final refined prompt, with no explanation.

Character spec:

* Name: {spec.name}
* Role: {spec.role}
* Game style: {spec.game_style}
* Silhouette: {spec.silhouette}
* Color palette: {color_str}
* Key props: {props_str}
* Animation focus: {anim_str}
* Extra notes: {notes_str}"""
    
    return prompt


def generate_gemini_tpose_prompt(spec: CharacterSpec) -> str:
    """
    Generate a meta-prompt for Gemini to create a T-pose image prompt.
    
    T-pose is the standard pose for 3D character modeling:
        - Arms extended horizontally (like the letter T)
        - Facing forward
        - Neutral expression
        - Full body visible
    
    This pose is essential for:
        - 3D model rigging (placing bones/joints)
        - Texture mapping (applying colors/materials)
        - Animation setup (defining default pose)
    
    The meta-prompt instructs Gemini to generate a detailed prompt
    specifically optimized for producing a clean T-pose reference image.
    
    Args:
        spec: The character specification
        
    Returns:
        A meta-prompt string for T-pose generation
    """
    # Pre-format all the spec fields
    color_str = format_color_palette(spec.color_palette)
    props_str = format_key_props(spec.key_props)
    anim_str = format_animation_focus(spec.animation_focus)
    notes_str = format_extra_notes(spec.extra_notes)
    
    # Build the meta-prompt with specific T-pose requirements
    # We list the requirements explicitly so Gemini includes them
    
    prompt = f"""You are a prompt engineer helping a game artist generate a T-pose reference image for 3D character modeling. Using the character specification below, produce a single, detailed prompt for a 2D image model that will generate a full-body T-pose of this character. Requirements:

* Neutral T-pose (arms extended horizontally).
* Full body visible, front view.
* Legs clearly visible, no cropping of feet or hands.
* Simple, clean background (flat grey or white).
* Even, neutral lighting (no heavy shadows or dramatic color lighting).
* No UI, overlays in the image.
* Design consistent with the game style and color palette.

Output only the final T-pose image prompt, no explanation.

Character spec:

* Name: {spec.name}
* Role: {spec.role}
* Game style: {spec.game_style}
* Silhouette: {spec.silhouette}
* Color palette: {color_str}
* Key props: {props_str}
* Animation focus: {anim_str}
* Extra notes: {notes_str}"""
    
    return prompt


# -----------------------------------------------------------------------------
# MAIN EXPORT FUNCTION
# -----------------------------------------------------------------------------

def generate_gemini_prompts(spec: CharacterSpec) -> dict[str, str]:
    """
    Generate all Stage 2 (Gemini) prompts for a character.
    
    This is the main function other modules should call.
    Returns a dictionary mapping prompt keys to prompt content.
    
    Args:
        spec: The character specification
        
    Returns:
        A dictionary with keys:
        - "gemini_2d_refiner": Meta-prompt for refining 2D prompts
        - "gemini_tpose_prompt": Meta-prompt for T-pose generation
        
    Usage workflow:
        1. Run this to generate the meta-prompts
        2. Copy "gemini_2d_refiner" into Gemini → get refined 2D prompt
        3. Copy "gemini_tpose_prompt" into Gemini → get T-pose prompt
        4. Use Gemini's output in your 2D image generator
    """
    return {
        "gemini_2d_refiner": generate_gemini_2d_refiner(spec),
        "gemini_tpose_prompt": generate_gemini_tpose_prompt(spec),
    }

