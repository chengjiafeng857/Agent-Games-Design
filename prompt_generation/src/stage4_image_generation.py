# stage4_image_generation.py - Stage 4: Gemini Image Generation
#
# Pipeline Stage: Text Spec → 2D Prompts → Gemini T-pose → Checklist → [IMAGE GEN]
#                                                                       ^^^^^^^^^^
#                                                                       THIS STAGE
#
# This module uses the Google Gemini API to generate actual T-pose images
# in three views: front, side, and back.
#
# REQUIRES:
#   - GEMINI_API_KEY environment variable set
#   - google-genai package installed (pip install google-genai)
#
# Output files:
#   - output/{name}_tpose_front_{version}.jpg
#   - output/{name}_tpose_side_{version}.jpg
#   - output/{name}_tpose_back_{version}.jpg

import os
import io
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from .models import CharacterSpec
from .stage1_base_prompts import (
    format_color_palette,
    format_key_props,
    format_extra_notes,
)


# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

# Environment variable name for the API key
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"

# Model name for image generation
# gemini-3-pro-image-preview (Nano Banana Pro) - Advanced image generation model
# Supports: 1K, 2K, 4K resolutions, up to 14 reference images, thinking mode
IMAGE_MODEL = "gemini-3-pro-image-preview"

# gemini-2.5-flash-image (Nano Banana) - Fast image generation model
# Used for side view generation with Google Search grounding
IMAGE_MODEL_FLASH = "gemini-2.5-flash-image"

# Image generation settings
# Aspect ratios: "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"
IMAGE_ASPECT_RATIO = "1:1"  # Square format works best for character refs

# Image size: "1K", "2K", "4K" (must be uppercase)
IMAGE_SIZE = "2K"  # 2K resolution for good quality


# -----------------------------------------------------------------------------
# DATA CLASSES
# -----------------------------------------------------------------------------

@dataclass
class GeneratedImage:
    """
    Holds a generated image and its metadata.
    
    Attributes:
        view: The view type ("front", "side", "back")
        image_data: Raw image bytes (PNG format)
        prompt_used: The prompt that generated this image
    """
    view: str
    image_data: bytes
    prompt_used: str
    
    def get_filename(self, character_name: str, version: str) -> str:
        """Generate the output filename for this image."""
        # Sanitize name: lowercase, replace spaces with underscores
        safe_name = character_name.lower().replace(" ", "_")
        return f"{safe_name}_tpose_{self.view}_{version}.jpg"


# -----------------------------------------------------------------------------
# API KEY HANDLING
# -----------------------------------------------------------------------------

def get_api_key() -> str:
    """
    Get the Gemini API key from environment variable.
    
    Returns:
        The API key string
        
    Raises:
        ValueError: If the API key is not set
    """
    api_key = os.environ.get(GEMINI_API_KEY_ENV)
    
    if not api_key:
        raise ValueError(
            f"Gemini API key not found. "
            f"Please set the {GEMINI_API_KEY_ENV} environment variable.\n"
            f"Example: export {GEMINI_API_KEY_ENV}='your-api-key-here'"
        )
    
    return api_key


# -----------------------------------------------------------------------------
# PROMPT BUILDERS FOR EACH VIEW
# -----------------------------------------------------------------------------

def build_tpose_prompt(spec: CharacterSpec, view: str) -> str:
    """
    Build a T-pose image generation prompt for a specific view.
    
    Args:
        spec: The character specification
        view: One of "front", "side", or "back"
        
    Returns:
        A detailed prompt string for image generation
    """
    # Format spec fields
    color_str = format_color_palette(spec.color_palette)
    props_str = format_key_props(spec.key_props)
    notes_str = format_extra_notes(spec.extra_notes)
    # Note: animation_focus is intentionally not included in image prompts
    # It's a design consideration for ensuring the character supports planned movements,
    # not a visual element to render in the reference image
    
    # Common base for all views - natural prose style
    # Build character description from spec fields
    base_prompt = (
        f"Full body T-pose character reference of {spec.name}, "
        f"a {spec.role} rendered in {spec.game_style} style. "
        f"The character has a distinctive silhouette: {spec.silhouette}. "
        f"Color scheme features {color_str}. "
    )
    
    # Add props if present (items the character carries)
    if props_str:
        base_prompt += f"Has {props_str} as equipment, do not hold in hands, keep them visible."
    
    # Add extra notes as additional context (environment, mood, etc.)
    if notes_str:
        base_prompt += f"{notes_str} "
    
    # View-specific additions
    view_specifics = {
        "front": (
            "FRONT VIEW facing the camera directly. "
            "Arms extended horizontally in T-pose. "
            "Symmetrical pose, feet shoulder-width apart. "
        ),
        "side": (
            "SIDE VIEW (profile) facing left. "
            "Arms extended horizontally in T-pose. "
            "Full profile showing depth of character design. "
        ),
        "back": (
            "BACK VIEW facing away from camera. "
            "Arms extended horizontally in T-pose. "
            "Showing back details of costume and design. "
        ),
    }
    
    # Quality and technical requirements
    # CRITICAL: Knees must be visible for 3D rigging - this is essential for character animation
    technical_requirements = (
        "Clean white or light gray background. "
        "Even, neutral studio lighting. "
        "No shadows on background. "
        "Full body visible from head to feet. "
        # Knee visibility requirements for 3D rigging
        "IMPORTANT FOR 3D RIGGING: Structure of both knees must be completely visible and unobstructed. "
        "If character wears a long coat or robe, it must be open, short, or pulled back to expose the full leg structure. "
        "Show clear leg anatomy: thighs, knees, shins, and feet must all be visible. "
        "No clothing covering or hiding the knee joints. "
        "High detail, game-ready character design. "
        "No text, logos, or watermarks. "
        "Professional character concept art quality."
    )
    
    # Combine all parts
    prompt = base_prompt + view_specifics.get(view, "") + technical_requirements
    
    return prompt


# -----------------------------------------------------------------------------
# GEMINI API INTEGRATION
# -----------------------------------------------------------------------------

def generate_image_with_gemini(
    prompt: str,
    api_key: str,
    aspect_ratio: str = IMAGE_ASPECT_RATIO,
    image_size: str = IMAGE_SIZE,
) -> bytes:
    """
    Generate an image using the Gemini 3 Pro Image Preview model.
    
    This function uses the google-genai SDK with the gemini-3-pro-image-preview
    model (also known as "Nano Banana Pro") for high-quality image generation.
    
    Args:
        prompt: The image generation prompt
        api_key: The Gemini API key
        aspect_ratio: Image aspect ratio (default: "1:1")
            Options: "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"
        image_size: Output resolution (default: "2K")
            Options: "1K", "2K", "4K" (must be uppercase)
        
    Returns:
        Image data as bytes (PNG format)
        
    Raises:
        ImportError: If google-genai is not installed
        Exception: If the API call fails
    """
    # Import here to allow the rest of the code to work without the package
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError(
            "google-genai package is required for image generation.\n"
            "Install it with: pip install google-genai\n"
            "Or: uv add google-genai"
        )
    
    # Create the Gemini client with the API key
    client = genai.Client(api_key=api_key)
    
    # Configure image generation settings
    config = types.GenerateContentConfig(
        response_modalities=['IMAGE'],  # Only request image output
        image_config=types.ImageConfig(
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        ),
    )
    
    # Generate the image using gemini-3-pro-image-preview
    response = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=[prompt],
        config=config,
    )
    
    # Extract the image from the response
    for part in response.parts:
        if part.inline_data is not None:
            # inline_data.data is already raw bytes (not base64 encoded)
            # The image is typically JPEG format (mime_type: image/jpeg)
            return part.inline_data.data
    
    raise Exception("No image was generated. The API returned an empty response.")


def generate_image_with_gemini_and_text(
    prompt: str,
    api_key: str,
    aspect_ratio: str = IMAGE_ASPECT_RATIO,
    image_size: str = IMAGE_SIZE,
) -> tuple[bytes, Optional[str]]:
    """
    Generate an image with optional text response using Gemini 3 Pro Image Preview.
    
    This variant returns both the generated image and any accompanying text
    that the model generates (useful for understanding the model's reasoning).
    
    Args:
        prompt: The image generation prompt
        api_key: The Gemini API key
        aspect_ratio: Image aspect ratio (default: "1:1")
        image_size: Output resolution (default: "2K")
        
    Returns:
        Tuple of (image_data, text_response)
        - image_data: Image as PNG bytes
        - text_response: Any text the model generated, or None
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError(
            "google-genai package is required for image generation.\n"
            "Install it with: pip install google-genai\n"
            "Or: uv add google-genai"
        )
    
    # Create the Gemini client
    client = genai.Client(api_key=api_key)
    
    # Configure for both text and image output
    config = types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        image_config=types.ImageConfig(
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        ),
    )
    
    # Generate content
    response = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=[prompt],
        config=config,
    )
    
    # Extract both text and image from response
    image_data = None
    text_response = None
    
    for part in response.parts:
        if part.text is not None:
            text_response = part.text
        elif part.inline_data is not None:
            # inline_data.data is already raw bytes (not base64 encoded)
            # The image is typically JPEG format (mime_type: image/jpeg)
            image_data = part.inline_data.data
    
    if image_data is None:
        raise Exception("No image was generated. The API returned an empty response.")
    
    return image_data, text_response


def edit_image_with_gemini(
    source_image_path: Path,
    edit_prompt: str,
    api_key: str,
    aspect_ratio: str = IMAGE_ASPECT_RATIO,
    image_size: str = IMAGE_SIZE,
) -> bytes:
    """
    Edit an existing image using Gemini 3 Pro Image Preview with a text prompt.
    
    This function takes an existing image and a text prompt describing the
    desired modifications, then returns the edited image.
    
    Args:
        source_image_path: Path to the source image to edit
        edit_prompt: Text prompt describing the desired edits
        api_key: The Gemini API key
        aspect_ratio: Image aspect ratio (default: "1:1")
        image_size: Output resolution (default: "2K")
        
    Returns:
        Edited image data as bytes (JPEG format)
        
    Raises:
        ImportError: If google-genai is not installed
        FileNotFoundError: If source image doesn't exist
        Exception: If the API call fails
        
    Example:
        >>> edited = edit_image_with_gemini(
        ...     Path("front.jpg"),
        ...     "Make the coat shorter to expose the knees",
        ...     api_key="your-key"
        ... )
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError(
            "google-genai package is required for image editing.\n"
            "Install it with: pip install google-genai\n"
            "Or: uv add google-genai"
        )
    
    if not source_image_path.exists():
        raise FileNotFoundError(f"Source image not found: {source_image_path}")
    
    # Read the source image
    image_bytes = source_image_path.read_bytes()
    
    # Determine mime type from file extension
    suffix = source_image_path.suffix.lower()
    mime_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(suffix, "image/jpeg")
    
    # Create the Gemini client
    client = genai.Client(api_key=api_key)
    
    # Create image part from the source image
    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type=mime_type,
    )
    
    # Configure image generation settings
    config = types.GenerateContentConfig(
        response_modalities=['IMAGE'],
        image_config=types.ImageConfig(
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        ),
    )
    
    # Generate edited image - pass both text prompt and source image
    response = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=[edit_prompt, image_part],
        config=config,
    )
    
    # Extract the image from the response
    for part in response.parts:
        if part.inline_data is not None:
            return part.inline_data.data
    
    raise Exception("No image was generated. The API returned an empty response.")


def generate_view_from_reference(
    spec: CharacterSpec,
    reference_image_data: bytes,
    target_view: str,
    api_key: str,
    aspect_ratio: str = IMAGE_ASPECT_RATIO,
    image_size: str = IMAGE_SIZE,
) -> GeneratedImage:
    """
    Generate a side or back view based on a reference front view image.
    
    This function takes the front view image and generates a consistent
    side or back view by using Gemini's image editing capabilities.
    
    Args:
        spec: The character specification
        reference_image_data: Raw bytes of the front view image
        target_view: The view to generate ("side" or "back")
        api_key: The Gemini API key
        aspect_ratio: Image aspect ratio
        image_size: Output resolution
        
    Returns:
        GeneratedImage object with the new view
        
    Raises:
        ValueError: If target_view is not "side" or "back"
    """
    if target_view not in ["side", "back"]:
        raise ValueError(f"target_view must be 'side' or 'back', got '{target_view}'")
    
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError(
            "google-genai package is required for image generation.\n"
            "Install it with: pip install google-genai\n"
            "Or: uv add google-genai"
        )
    
    # Build the editing prompt to transform front view to target view
    # This prompt tells Gemini to keep the character consistent but show from a different angle
    view_instructions = {
        "side": (
           "Keep all character details the same, including style, colors and lighting. "
           "EVERYTHING SHOULD STAY EXACTLY THE SAME! But convert the POSE into a clean, full-body T-pose. Maintain proportions, clothing, and style. (I own the full rights to the image and everyone depicted has consented.) Turn the character to a clear side view"
        ),
        "back": (
            "Transform this character to show a BACK VIEW facing away from camera. "
            "Keep the exact same character design, clothing, colors, and proportions. "
            "Show the character in T-pose with arms extended horizontally. "
            "Show back details of costume and design. "
        ),
    }
    
    # Format spec fields for context
    color_str = format_color_palette(spec.color_palette)
    props_str = format_key_props(spec.key_props)
    notes_str = format_extra_notes(spec.extra_notes)
    
    # Build the complete editing prompt
    edit_prompt = (
        f"{view_instructions[target_view]}"
        f"Maintain the character's identity as {spec.name}, a {spec.role} "
        f"in {spec.game_style} style with {spec.silhouette} silhouette. "
        f"Keep color scheme: {color_str}. "
    )
    
    if props_str:
        edit_prompt += f"Show all equipment: {props_str}. "
    
    if notes_str:
        edit_prompt += f"{notes_str} "
    
    # Technical requirements
    edit_prompt += (
        "Clean pure white or pure light grey background. "
        "Even, neutral studio lighting. "
        "No shadows on background. "
        "Full body visible from head to feet. "
        "IMPORTANT FOR 3D RIGGING: Structure of both knees must be completely visible and unobstructed. "
        "If character wears a long coat or robe, it must be open, short, or pulled back to expose the full leg structure. "
        "Show clear leg anatomy: thighs, knees, shins, and feet must all be visible. "
        "High detail, game-ready character design. "
        "No text, logos, or watermarks. "
        "Professional character concept art quality."
    )
    
    # Google Search grounding option (disabled for now, set to True to enable)
    # use_grounding = (target_view == "side")  # Enable for side view only
    use_grounding = False  # Disabled - Google Search not needed for view generation
    grounding_str = " + Google Search grounding" if use_grounding else ""
    
    # Use flash model (Nano Banana) for side view, pro model for others
    model_to_use = IMAGE_MODEL_FLASH if target_view == "side" else IMAGE_MODEL
    
    print(f"  Generating {target_view} view from front view reference...")
    print(f"  Using model: {model_to_use} (temperature=1{grounding_str})")
    
    # Create the Gemini client
    client = genai.Client(api_key=api_key)
    
    # Create image part from the reference image
    image_part = types.Part.from_bytes(
        data=reference_image_data,
        mime_type="image/jpeg",
    )
    
    # Configure image generation settings
    # Note: Flash model (gemini-2.5-flash-image) doesn't support image_size parameter
    # Only Pro model (gemini-3-pro-image-preview) supports 1K/2K/4K resolution
    is_flash_model = (model_to_use == IMAGE_MODEL_FLASH)
    
    # When using Google Search grounding, we MUST include 'TEXT' in response_modalities
    # because the model needs to output text to show grounding metadata and search results
    if use_grounding:
        if is_flash_model:
            # Flash model with Google Search - no image_size support
            config = types.GenerateContentConfig(
                temperature=1,
                response_modalities=['TEXT', 'IMAGE'],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                ),
                tools=[{"google_search": {}}],
            )
        else:
            # Pro model with Google Search
            config = types.GenerateContentConfig(
                temperature=1,
                response_modalities=['TEXT', 'IMAGE'],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size=image_size,
                ),
                tools=[{"google_search": {}}],
            )
    else:
        if is_flash_model:
            # Flash model - no image_size support
            config = types.GenerateContentConfig(
                temperature=1,
                response_modalities=['IMAGE'],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                ),
            )
        else:
            # Pro model - full features
            config = types.GenerateContentConfig(
                temperature=1,
                response_modalities=['IMAGE'],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size=image_size,
                ),
            )
    
    # Generate the new view based on the reference image
    response = client.models.generate_content(
        model=model_to_use,
        contents=[edit_prompt, image_part],
        config=config,
    )
    
    # Extract the image from the response
    for part in response.parts:
        if part.inline_data is not None:
            return GeneratedImage(
                view=target_view,
                image_data=part.inline_data.data,
                prompt_used=edit_prompt,
            )
    
    raise Exception("No image was generated. The API returned an empty response.")


def regenerate_single_view(
    spec: "CharacterSpec",
    view: str,
    version: str,
    api_key: Optional[str] = None,
    aspect_ratio: str = IMAGE_ASPECT_RATIO,
    image_size: str = IMAGE_SIZE,
) -> GeneratedImage:
    """
    Regenerate a single view image.
    
    Args:
        spec: The character specification
        view: The view to generate ("front", "side", or "back")
        version: Version string for filenames
        api_key: Optional API key (uses env var if not provided)
        aspect_ratio: Image aspect ratio
        image_size: Output resolution
        
    Returns:
        GeneratedImage object with the new image
    """
    if api_key is None:
        api_key = get_api_key()
    
    prompt = build_tpose_prompt(spec, view)
    print(f"  Regenerating {view} view...")
    print(f"  Using model: {IMAGE_MODEL}")
    
    image_data = generate_image_with_gemini(
        prompt=prompt,
        api_key=api_key,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
    )
    
    return GeneratedImage(
        view=view,
        image_data=image_data,
        prompt_used=prompt,
    )


# -----------------------------------------------------------------------------
# MAIN GENERATION FUNCTION
# -----------------------------------------------------------------------------

def generate_tpose_images(
    spec: CharacterSpec,
    version: str,
    api_key: Optional[str] = None,
    views: list[str] = ["front", "side", "back"],
    aspect_ratio: str = IMAGE_ASPECT_RATIO,
    image_size: str = IMAGE_SIZE,
) -> list[GeneratedImage]:
    """
    Generate T-pose images for all specified views using Gemini 3 Pro Image Preview.
    
    This function uses a sequential approach to ensure consistency:
    1. Generate front view from text prompt
    2. Generate side and back views based on the front view image
    
    This ensures all views are consistent since they're based on the same front view.
    
    Args:
        spec: The character specification
        version: Version string for filenames
        api_key: Optional API key (uses env var if not provided)
        views: List of views to generate (default: all three)
        aspect_ratio: Image aspect ratio (default: "1:1")
            Options: "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"
        image_size: Output resolution (default: "2K")
            Options: "1K", "2K", "4K" (must be uppercase)
        
    Returns:
        List of GeneratedImage objects
        
    Example:
        >>> images = generate_tpose_images(spec, "v1")
        >>> for img in images:
        ...     print(f"Generated {img.view} view")
    """
    # Get API key from parameter or environment
    if api_key is None:
        api_key = get_api_key()
    
    generated_images: list[GeneratedImage] = []
    
    print(f"  Using model: {IMAGE_MODEL}")
    print(f"  Resolution: {image_size}, Aspect ratio: {aspect_ratio}")
    print(f"  Strategy: Sequential generation (front → side/back) for consistency")
    
    # Step 1: Generate front view first (this is the reference)
    front_image: Optional[GeneratedImage] = None
    
    if "front" in views:
        print(f"  Generating front view (reference)...")
        
        # Build the prompt for front view
        front_prompt = build_tpose_prompt(spec, "front")
        
        # Generate the front view image
        front_image_data = generate_image_with_gemini(
            prompt=front_prompt,
            api_key=api_key,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        )
        
        # Create the GeneratedImage object
        front_image = GeneratedImage(
            view="front",
            image_data=front_image_data,
            prompt_used=front_prompt,
        )
        
        generated_images.append(front_image)
        print(f"    ✓ front view generated")
    
    # Step 2: Generate other views based on front view (if front was generated)
    for view in views:
        if view == "front":
            continue  # Already generated above
        
        if view in ["side", "back"] and front_image is not None:
            # Generate this view based on the front view for consistency
            generated_image = generate_view_from_reference(
                spec=spec,
                reference_image_data=front_image.image_data,
                target_view=view,
                api_key=api_key,
                aspect_ratio=aspect_ratio,
                image_size=image_size,
            )
            
            generated_images.append(generated_image)
            print(f"    ✓ {view} view generated (based on front view)")
        else:
            # Fallback: Generate independently if front view not available
            print(f"  Generating {view} view independently (no front reference)...")
            
            prompt = build_tpose_prompt(spec, view)
            
            image_data = generate_image_with_gemini(
                prompt=prompt,
                api_key=api_key,
                aspect_ratio=aspect_ratio,
                image_size=image_size,
            )
            
            generated_image = GeneratedImage(
                view=view,
                image_data=image_data,
                prompt_used=prompt,
            )
            
            generated_images.append(generated_image)
            print(f"    ✓ {view} view generated")
    
    return generated_images


# -----------------------------------------------------------------------------
# FILE SAVING
# -----------------------------------------------------------------------------

def save_generated_images(
    images: list[GeneratedImage],
    spec: CharacterSpec,
    output_dir: Path,
    version: str,
) -> list[Path]:
    """
    Save generated images to the output directory.
    
    Creates the output directory if it doesn't exist,
    then saves each image as a PNG file.
    
    Args:
        images: List of GeneratedImage objects
        spec: The character specification
        output_dir: Base output directory (e.g., Path("output"))
        version: Version string for filenames
        
    Returns:
        List of paths to saved files
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    saved_paths: list[Path] = []
    
    for image in images:
        # Generate filename
        filename = image.get_filename(spec.name, version)
        file_path = output_dir / filename
        
        # Write image data to file
        file_path.write_bytes(image.image_data)
        
        saved_paths.append(file_path)
    
    return saved_paths


# -----------------------------------------------------------------------------
# PROMPT-ONLY MODE (NO API CALLS)
# -----------------------------------------------------------------------------

def generate_image_prompts_only(
    spec: CharacterSpec,
    views: list[str] = ["front", "side", "back"],
) -> dict[str, str]:
    """
    Generate just the image prompts without making API calls.
    
    Useful for:
        - Testing prompt generation
        - Manual image generation in other tools
        - When API key is not available
    
    Args:
        spec: The character specification
        views: List of views to generate prompts for
        
    Returns:
        Dictionary mapping view names to prompts
    """
    prompts = {}
    
    for view in views:
        prompt_key = f"image_prompt_{view}"
        prompts[prompt_key] = build_tpose_prompt(spec, view)
    
    return prompts

