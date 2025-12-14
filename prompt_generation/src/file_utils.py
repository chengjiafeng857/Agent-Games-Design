# file_utils.py - File Output Utilities
#
# This module handles all file I/O operations for the prompt pipeline:
#   - Resolving output paths based on prompt keys
#   - Creating directories as needed
#   - Writing prompt files to disk
#   - Printing prompts to stdout (for --dry-run mode)
#
# Separation of concerns: This module knows nothing about prompt content,
# only about how to save strings to the right file paths.

from pathlib import Path

from .models import CharacterSpec


# -----------------------------------------------------------------------------
# OUTPUT PATH CONFIGURATION
# -----------------------------------------------------------------------------
# This dictionary maps prompt keys to their output locations.
# Format: "key": ("subdirectory", "filename_template")
#
# The filename template uses placeholders:
#   {name}    - Character name (lowercase, underscores)
#   {version} - Version string (e.g., "v1")
#
# Example: "base_2d_full_body" with name="Aethel", version="v1"
#          -> prompts/base/aethel_2d_base_v1.txt

PROMPT_FILE_MAP: dict[str, tuple[str, str]] = {
    # Stage 1: Base 2D prompts (static templates) -> base/
    "base_2d_full_body": ("base", "{name}_2d_base_{version}.txt"),
    "base_2d_sheet": ("base", "{name}_2d_sheet_{version}.txt"),
    
    # Stage 2a: Gemini meta-prompts (static) -> gemini/
    "gemini_2d_refiner": ("gemini", "{name}_2d_refiner_{version}.txt"),
    "gemini_tpose_prompt": ("gemini", "{name}_tpose_prompt_{version}.txt"),
    
    # Stage 2b: LLM-refined prompts (from OpenAI) -> refined/
    # These are the actual prompts to use for image generation!
    "refined_concept": ("refined", "{name}_refined_concept_{version}.txt"),
    "refined_tpose_front": ("refined", "{name}_refined_tpose_front_{version}.txt"),
    "refined_tpose_side": ("refined", "{name}_refined_tpose_side_{version}.txt"),
    "refined_tpose_back": ("refined", "{name}_refined_tpose_back_{version}.txt"),
    
    # Stage 3: Common documents -> common/
    "common_2d_refinement_criteria": ("common", "{name}_2d_refinement_criteria_{version}.txt"),
    "common_design_notes": ("common", "{name}_design_notes_{version}.txt"),
}


# -----------------------------------------------------------------------------
# PATH RESOLUTION
# -----------------------------------------------------------------------------

def sanitize_filename(name: str) -> str:
    """
    Sanitize a character name for use in filenames.
    
    Rules:
        - Convert to lowercase
        - Replace spaces with underscores
        - (Could add more rules like removing special characters)
    
    Args:
        name: The raw character name (e.g., "Aethel", "Dr. Strange")
        
    Returns:
        A safe filename string (e.g., "aethel", "dr._strange")
        
    Example:
        >>> sanitize_filename("Aethel")
        "aethel"
        >>> sanitize_filename("Space Marine")
        "space_marine"
    """
    return name.lower().replace(" ", "_")


def resolve_output_path(
    base_dir: Path, 
    spec: CharacterSpec, 
    version: str, 
    key: str
) -> Path:
    """
    Resolve the full output path for a given prompt key.
    
    This function looks up the key in PROMPT_FILE_MAP and constructs
    the complete file path by combining:
        - base_dir (e.g., "prompts")
        - subdirectory (e.g., "base", "gemini", "common")
        - filename (with {name} and {version} filled in)
    
    Args:
        base_dir: The base output directory (e.g., Path("prompts"))
        spec: The character specification (used for name)
        version: The version string (e.g., "v1")
        key: The prompt key (e.g., "base_2d_full_body")
        
    Returns:
        A Path object like: prompts/base/aethel_2d_base_v1.txt
        
    Raises:
        ValueError: If the key is not in PROMPT_FILE_MAP
        
    Example:
        >>> path = resolve_output_path(Path("prompts"), spec, "v1", "base_2d_full_body")
        >>> print(path)
        prompts/base/aethel_2d_base_v1.txt
    """
    # Step 1: Look up the key in our mapping
    if key not in PROMPT_FILE_MAP:
        raise ValueError(f"Unknown prompt key: {key}")
    
    # Step 2: Unpack the tuple (subdirectory, filename_template)
    subdir, filename_template = PROMPT_FILE_MAP[key]
    
    # Step 3: Sanitize the character name for use in filename
    name_safe = sanitize_filename(spec.name)
    
    # Step 4: Fill in the template placeholders
    # str.format() replaces {name} with name_safe, {version} with version
    filename = filename_template.format(name=name_safe, version=version)
    
    # Step 5: Build and return the complete path
    # Path / str creates a new Path: Path("prompts") / "base" / "file.txt"
    return base_dir / subdir / filename


# -----------------------------------------------------------------------------
# FILE WRITING
# -----------------------------------------------------------------------------

def write_prompts(
    prompts: dict[str, str],
    spec: CharacterSpec,
    base_dir: Path,
    version: str
) -> list[Path]:
    """
    Write all prompts to their respective files.
    
    This function:
        1. Iterates through all prompts in the dictionary
        2. Resolves the output path for each prompt
        3. Creates the directory if it doesn't exist
        4. Writes the content to the file
        5. Returns a list of all written file paths
    
    Args:
        prompts: Dictionary mapping keys to prompt content
        spec: The character specification
        base_dir: The base output directory
        version: The version string for filenames
        
    Returns:
        List of Path objects for all written files
        
    Example:
        >>> paths = write_prompts(prompts, spec, Path("prompts"), "v1")
        >>> for p in paths:
        ...     print(p)
        prompts/base/aethel_2d_base_v1.txt
        prompts/gemini/aethel_tpose_prompt_v1.txt
        ...
    """
    # Keep track of all files we write
    written_paths: list[Path] = []
    
    # Iterate through each prompt in the dictionary
    for key, content in prompts.items():
        
        # Step 1: Figure out where this prompt should be saved
        output_path = resolve_output_path(base_dir, spec, version, key)
        
        # Step 2: Create the parent directory if it doesn't exist
        # .parent gets the directory part: prompts/base/file.txt -> prompts/base
        # mkdir() creates the directory
        # parents=True also creates parent directories if needed
        # exist_ok=True doesn't error if directory already exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Step 3: Write the prompt content to the file
        # encoding="utf-8" ensures special characters are handled correctly
        output_path.write_text(content, encoding="utf-8")
        
        # Step 4: Add to our list of written files
        written_paths.append(output_path)
    
    return written_paths


# -----------------------------------------------------------------------------
# DRY RUN OUTPUT
# -----------------------------------------------------------------------------

def print_prompts_to_stdout(prompts: dict[str, str]) -> None:
    """
    Print all prompts to stdout instead of writing files.
    
    This is used when the --dry-run flag is passed.
    It allows users to preview what would be written without
    actually creating any files.
    
    Format:
        ============================================================
        === prompt_key ===
        ============================================================
        
        (prompt content here)
        
    Args:
        prompts: Dictionary mapping keys to prompt content
        
    Example output:
        === base_2d_full_body ===
        full-body concept art of a Android archaeologist...
    """
    # Iterate through each prompt and print it
    for key, content in prompts.items():
        
        # Print a visual separator (60 equal signs)
        print(f"\n{'=' * 60}")
        
        # Print the prompt key as a header
        print(f"=== {key} ===")
        
        # Another separator
        print(f"{'=' * 60}\n")
        
        # Print the actual prompt content
        print(content)
        
        # Add a blank line after each prompt for readability
        print()

