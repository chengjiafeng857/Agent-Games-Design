# stage3_common_prompts.py - Stage 3: Checklist and Design Notes
#
# Pipeline Stage: Text Spec → 2D Prompts → Gemini T-pose → [CHECKLIST]
#                                                          ^^^^^^^^^^^
#                                                          THIS STAGE
#
# This module generates human-readable documents for quality validation
# and reference during the 3D modeling pipeline.
#
# These are NOT prompts for AI - they're for HUMANS to use:
#   - Checklist: Validate that generated images meet requirements
#   - Design Notes: Reference document for the character's intended look
#
# Output files:
#   - {name}_2d_refinement_criteria_{version}.txt - Image validation checklist
#   - {name}_design_notes_{version}.txt           - Human design reference

from .models import CharacterSpec

# Reuse helper functions from stage1 (DRY principle)
from .stage1_base_prompts import (
    format_color_palette,
    format_key_props,
    format_animation_focus,
    format_extra_notes,
)


# -----------------------------------------------------------------------------
# STAGE 3 GENERATORS: Human Reference Documents
# -----------------------------------------------------------------------------

def generate_2d_refinement_criteria(spec: CharacterSpec) -> str:
    """
    Generate a checklist for validating T-pose images.
    
    Before feeding a 2D image into Hunyuan.3D or other 3D tools,
    you should verify it meets certain quality criteria.
    
    This checklist helps ensure:
        - The image is suitable for 3D conversion
        - Key character features are visible
        - There are no artifacts that would confuse the 3D tool
    
    Each checkbox item addresses a common issue:
        - Cropping: 3D tools need the full body
        - T-pose: Standard pose for rigging
        - Perspective: Extreme angles confuse 3D tools
        - Background: Busy backgrounds leak into 3D model
        - Lighting: Baked-in shadows look wrong in 3D
        - etc.
    
    Args:
        spec: The character specification
        
    Returns:
        A Markdown-formatted checklist string
    """
    # Pre-format spec fields for insertion into the checklist
    color_str = format_color_palette(spec.color_palette)
    props_str = format_key_props(spec.key_props)
    
    # Build the checklist document
    # Using [ ] for checkbox items (Markdown task list syntax)
    
    checklist = f"""2D T-POSE IMAGE REFINEMENT CHECKLIST for {spec.name} ({spec.role})

GOAL: This image will be used as input to a 3D character generation tool (e.g., Hunyuan.3D). It must be clean and unambiguous.

CHECKLIST:
[ ] Full body visible, no cropping of feet or hands
[ ] Clear T-pose (arms extended horizontally, not bent)
[ ] Character facing forward, no extreme perspective
[ ] Simple, uncluttered background (flat or gradient)
[ ] Neutral, even lighting (no strong shadows or colored lights)
[ ] Silhouette matches description: {spec.silhouette}
[ ] Color palette approximately matches: {color_str}
[ ] Key props visible and readable: {props_str}
[ ] No text, watermarks, or logos
[ ] No heavy motion blur or depth-of-field effects

NOTES:

* If any box is unchecked, revise the prompt or regenerate the image.
* This image will be manually uploaded to Hunyuan.3D or similar 3D tool after approval."""
    
    return checklist


def generate_design_notes(spec: CharacterSpec) -> str:
    """
    Generate internal design notes for human reference.
    
    This document serves as a "source of truth" for the character's
    intended design. It includes:
        - All character specification details
        - Pipeline context explaining next steps
        - Reference for anyone working on the character
    
    This is useful when:
        - Multiple people work on the same character
        - You return to a project after time away
        - You need to verify the final 3D model matches intent
    
    Args:
        spec: The character specification
        
    Returns:
        A Markdown-formatted design notes document
    """
    # Pre-format all spec fields
    color_str = format_color_palette(spec.color_palette)
    props_str = format_key_props(spec.key_props)
    anim_str = format_animation_focus(spec.animation_focus)
    notes_str = format_extra_notes(spec.extra_notes)
    
    # Build the design notes document
    # This is a summary of everything about the character
    
    design_notes = f"""DESIGN NOTES for {spec.name} ({spec.role})

* Game style: {spec.game_style}
* Silhouette: {spec.silhouette}
* Color palette: {color_str}
* Key props: {props_str}
* Animation focus: {anim_str}
* Extra notes: {notes_str}

PIPELINE CONTEXT:

1. Use base 2D prompts to generate initial concepts.
2. Use Gemini NanoBanana Pro prompts to refine into a T-pose-specific image prompt.
3. Use the 2D refinement checklist to validate the final T-pose image.
4. MANUAL: Upload final 2D T-pose image to Hunyuan.3D or similar 3D tool.
5. MANUAL: Download the resulting 3D asset (.fbx/.obj) and feed into a separate assessment pipeline.

This file is for human reference and documentation of the character's intended look."""
    
    return design_notes


# -----------------------------------------------------------------------------
# MAIN EXPORT FUNCTION
# -----------------------------------------------------------------------------

def generate_common_prompts(spec: CharacterSpec) -> dict[str, str]:
    """
    Generate all Stage 3 (Common) documents for a character.
    
    This is the main function other modules should call.
    Returns a dictionary mapping document keys to document content.
    
    Args:
        spec: The character specification
        
    Returns:
        A dictionary with keys:
        - "common_2d_refinement_criteria": Image validation checklist
        - "common_design_notes": Human design reference document
        
    Usage:
        1. Generate images using Stage 1 and Stage 2 prompts
        2. Open "common_2d_refinement_criteria" and check each box
        3. If all boxes are checked, image is ready for 3D conversion
        4. Keep "common_design_notes" for reference during the pipeline
    """
    return {
        "common_2d_refinement_criteria": generate_2d_refinement_criteria(spec),
        "common_design_notes": generate_design_notes(spec),
    }

