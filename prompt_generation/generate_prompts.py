#!/usr/bin/env python3
# generate_prompts.py - Main CLI Entry Point
#
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                      AI CHARACTER PROMPT PIPELINE                            │
# │                                                                              │
# │   TEXT SPEC  →  BASE PROMPTS  →  LLM REFINE  →  CHECKLIST  →  IMAGE GEN    │
# │   (YAML/JSON)    (Stage 1)       (Stage 2)      (Stage 3)     (Stage 4)    │
# │                                                                              │
# │   Stage 2: Uses OpenAI GPT (with web search) to refine prompts              │
# │   Stage 4: Generates T-pose images using Gemini API                         │
# │   Then manually: Upload to Hunyuan.3D → Download .fbx/.obj                  │
# └─────────────────────────────────────────────────────────────────────────────┘
#
# Usage:
#   uv run generate_prompts.py prompts -i configs/aethel.yaml   # Static prompts
#   uv run generate_prompts.py refine -i configs/aethel.yaml    # LLM-refined prompts
#   uv run generate_prompts.py images -i configs/aethel.yaml    # Generate images
#   uv run generate_prompts.py all -i configs/aethel.yaml       # Full pipeline
#
# This file is the THIN CLI LAYER that ties everything together.
# All the actual logic lives in the src/ modules.

from pathlib import Path
from typing import Annotated, Optional
from datetime import datetime
import sys
import os

# Load environment variables from .env file (if it exists)
# This allows storing API keys in a .env file instead of exporting them manually
from dotenv import load_dotenv
load_dotenv()  # Loads .env from current directory or parent directories

import typer

# -----------------------------------------------------------------------------
# IMPORTS FROM OUR MODULES
# -----------------------------------------------------------------------------
# We import from the src package, which contains all our pipeline logic.
# Each module handles one part of the pipeline.

# models.py: Character specification data model and file loading
from src.models import CharacterSpec, load_character_spec

# stage*_*.py: Prompt generators for each pipeline stage
from src.stage1_base_prompts import generate_base_prompts      # Stage 1: Base prompts
from src.stage2_gemini_prompts import generate_gemini_prompts  # Stage 2a: Gemini meta-prompts
from src.stage2_llm_refiner import (                           # Stage 2b: LLM refinement
    refine_prompts_to_dict,
    preview_llm_requests,
    OPENAI_API_KEY_ENV,
)
from src.stage3_common_prompts import generate_common_prompts  # Stage 3: Checklist/Notes
from src.stage4_image_generation import (                       # Stage 4: Image Gen
    generate_tpose_images,
    generate_image_prompts_only,
    save_generated_images,
    edit_image_with_gemini,
    regenerate_single_view,
    GeneratedImage,
    GEMINI_API_KEY_ENV,
)
from src.stage5_hunyuan3d import (                              # Stage 5: Hunyuan 3D
    generate_3d_model,
    check_required_env_vars,
    get_env_var_help,
    TENCENT_SECRET_ID_ENV,
    TENCENT_SECRET_KEY_ENV,
    VALID_PROVIDERS,
    is_sdk_available,
)
from src.providers import TENCENT_COS_BUCKET_ENV, TENCENT_COS_REGION_ENV

# file_utils.py: File output utilities
from src.file_utils import write_prompts, print_prompts_to_stdout


# -----------------------------------------------------------------------------
# TIMESTAMPED OUTPUT FOLDER
# -----------------------------------------------------------------------------

def create_timestamped_output_dir(base_dir: Path) -> Path:
    """
    Create a timestamped output directory inside the base directory.
    
    Each run gets its own folder named with the current timestamp.
    Format: YYYY-MM-DD_HH-MM-SS
    
    Example: output/2024-12-09_15-30-45/
    
    Args:
        base_dir: The base output directory (e.g., Path("output"))
        
    Returns:
        Path to the new timestamped directory
    """
    # Generate timestamp string: 2024-12-09_15-30-45
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Create the timestamped directory path
    timestamped_dir = base_dir / timestamp
    
    # Create the directory (and parents if needed)
    timestamped_dir.mkdir(parents=True, exist_ok=True)
    
    return timestamped_dir


# -----------------------------------------------------------------------------
# CLI APPLICATION SETUP
# -----------------------------------------------------------------------------
# Typer is a modern Python CLI framework built on Click.
# It uses type hints to automatically generate CLI argument parsing.

app = typer.Typer(
    # Name shown in help text
    name="generate_prompts",
    
    # Description shown when user runs --help
    help="Generate AI character prompts and images for the 2D → 3D pipeline.",
    
    # Disable shell completion script generation (simplifies the CLI)
    add_completion=False,
)


# -----------------------------------------------------------------------------
# PROMPT GENERATION FUNCTION
# -----------------------------------------------------------------------------

def generate_all_prompts(spec: CharacterSpec) -> dict[str, str]:
    """
    Generate all prompts for all pipeline stages (1-3).
    
    This function calls each stage's generator and merges the results
    into a single dictionary.
    
    Pipeline stages:
        Stage 1 (stage1_base_prompts.py):   Base 2D concept prompts
        Stage 2 (stage2_gemini_prompts.py): Gemini T-pose meta-prompts
        Stage 3 (stage3_common_prompts.py): Checklist and design notes
    
    Args:
        spec: The character specification
        
    Returns:
        A dictionary containing all prompts from all stages.
        Keys are like: "base_2d_full_body", "gemini_tpose_prompt", etc.
    """
    # Create an empty dictionary to hold all prompts
    all_prompts: dict[str, str] = {}
    
    # Stage 1: Generate base 2D prompts
    base_prompts = generate_base_prompts(spec)
    all_prompts.update(base_prompts)
    
    # Stage 2: Generate Gemini meta-prompts
    gemini_prompts = generate_gemini_prompts(spec)
    all_prompts.update(gemini_prompts)
    
    # Stage 3: Generate common documents
    common_prompts = generate_common_prompts(spec)
    all_prompts.update(common_prompts)
    
    return all_prompts


# -----------------------------------------------------------------------------
# COMMAND: prompts (Stages 1-3)
# -----------------------------------------------------------------------------

@app.command("prompts")
def generate_prompts_command(
    input_file: Annotated[
        Path,
        typer.Option(
            "--input", "-i",
            help="Path to character spec file (YAML or JSON)",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir", "-o",
            help="Base output directory for generated prompts",
        ),
    ] = Path("output"),
    version: Annotated[
        str,
        typer.Option(
            "--version", "-v",
            help="Version string suffix for filenames (e.g., v1, v2)",
        ),
    ] = "v1",
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Print prompts to stdout instead of writing files",
        ),
    ] = False,
) -> None:
    """
    Generate text prompts (Stages 1-3).
    
    Creates base 2D prompts, Gemini meta-prompts, checklist, and design notes.
    
    \b
    Example:
      uv run generate_prompts.py prompts -i configs/aethel.yaml -o prompts -v v1
    """
    # Step 1: Load the character specification
    print(f"Loading character spec from: {input_file}")
    
    try:
        spec = load_character_spec(input_file)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(code=1)
    
    print(f"Character: {spec.name} ({spec.role})")
    
    # Step 2: Generate all prompts
    print(f"Generating prompts (version: {version})...")
    prompts = generate_all_prompts(spec)
    
    # Step 3: Output
    if dry_run:
        print("\n[DRY RUN] Printing prompts to stdout:\n")
        print_prompts_to_stdout(prompts)
    else:
        # Create timestamped output directory
        run_output_dir = create_timestamped_output_dir(output_dir)
        print(f"Writing prompts to: {run_output_dir}/")
        
        written_paths = write_prompts(prompts, spec, run_output_dir, version)
        
        print(f"\nGenerated {len(written_paths)} files:")
        for path in written_paths:
            print(f"  ✓ {path}")
    
    print("\nDone!")


# -----------------------------------------------------------------------------
# COMMAND: refine (Stage 2b - LLM Refinement)
# -----------------------------------------------------------------------------

@app.command("refine")
def refine_prompts_command(
    input_file: Annotated[
        Path,
        typer.Option(
            "--input", "-i",
            help="Path to character spec file (YAML or JSON)",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir", "-o",
            help="Base output directory for refined prompts",
        ),
    ] = Path("output"),
    version: Annotated[
        str,
        typer.Option(
            "--version", "-v",
            help="Version string suffix for filenames (e.g., v1, v2)",
        ),
    ] = "v1",
    model: Annotated[
        str,
        typer.Option(
            "--model", "-m",
            help="OpenAI model to use (gpt-5, gpt-5-mini, gpt-4.1, etc.)",
        ),
    ] = "gpt-5",
    web_search: Annotated[
        bool,
        typer.Option(
            "--web-search",
            help="Enable web search for current AI art trends",
        ),
    ] = False,
    api_key: Annotated[
        Optional[str],
        typer.Option(
            "--api-key",
            help=f"OpenAI API key (or set {OPENAI_API_KEY_ENV} env var)",
            envvar=OPENAI_API_KEY_ENV,
        ),
    ] = None,
    preview_only: Annotated[
        bool,
        typer.Option(
            "--preview",
            help="Preview requests without making API calls",
        ),
    ] = False,
) -> None:
    """
    Refine prompts using OpenAI GPT (Stage 2b).
    
    Uses LLM to transform character specs into optimized image prompts.
    The refined prompts are ready to use directly in image generators.
    
    \b
    Example:
      export OPENAI_API_KEY='your-api-key'
      uv run generate_prompts.py refine -i configs/aethel.yaml -v v1
      
    \b
    With web search (for current AI art trends):
      uv run generate_prompts.py refine -i configs/aethel.yaml --web-search
      
    \b
    Preview mode (no API calls):
      uv run generate_prompts.py refine -i configs/aethel.yaml --preview
    """
    # Step 1: Load the character specification
    print(f"Loading character spec from: {input_file}")
    
    try:
        spec = load_character_spec(input_file)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(code=1)
    
    print(f"Character: {spec.name} ({spec.role})")
    
    # Step 2: Preview or refine
    if preview_only:
        # Preview mode: show what would be sent to the LLM
        print("\n[PREVIEW] Requests that would be sent to LLM:\n")
        requests = preview_llm_requests(spec)
        
        for key, request in requests.items():
            print(f"{'='*60}")
            print(f"=== {key} ===")
            print(f"{'='*60}\n")
            print(request)
            print()
        
        print("Done! (No API calls made)")
        
    else:
        # Full refinement mode
        print(f"\nRefining prompts with LLM (version: {version})...")
        
        # Check for API key
        if not api_key:
            api_key = os.environ.get(OPENAI_API_KEY_ENV)
        
        if not api_key:
            print(f"\nError: OpenAI API key required.", file=sys.stderr)
            print(f"Set the {OPENAI_API_KEY_ENV} environment variable:", file=sys.stderr)
            print(f"  export {OPENAI_API_KEY_ENV}='your-api-key'", file=sys.stderr)
            print(f"\nOr use the --api-key option:", file=sys.stderr)
            print(f"  --api-key 'your-api-key'", file=sys.stderr)
            print(f"\nOr use --preview to just see the requests.", file=sys.stderr)
            raise typer.Exit(code=1)
        
        try:
            # Refine prompts using LLM
            refined_prompts = refine_prompts_to_dict(
                spec=spec,
                api_key=api_key,
                model=model,
                use_web_search=web_search,
            )
            
            # Create timestamped output directory
            run_output_dir = create_timestamped_output_dir(output_dir)
            
            # Save refined prompts
            print(f"\nWriting refined prompts to: {run_output_dir}/")
            written_paths = write_prompts(refined_prompts, spec, run_output_dir, version)
            
            print(f"\nGenerated {len(written_paths)} refined prompt files:")
            for path in written_paths:
                print(f"  ✓ {path}")
            
        except ImportError as e:
            print(f"\nError: {e}", file=sys.stderr)
            raise typer.Exit(code=1)
            
        except Exception as e:
            print(f"\nError refining prompts: {e}", file=sys.stderr)
            raise typer.Exit(code=1)
    
    print("\nDone!")


# -----------------------------------------------------------------------------
# COMMAND: images (Stage 4)
# -----------------------------------------------------------------------------

@app.command("images")
def generate_images_command(
    input_file: Annotated[
        Path,
        typer.Option(
            "--input", "-i",
            help="Path to character spec file (YAML or JSON)",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir", "-o",
            help="Output directory for generated images",
        ),
    ] = Path("output/images"),
    version: Annotated[
        str,
        typer.Option(
            "--version", "-v",
            help="Version string suffix for filenames (e.g., v1, v2)",
        ),
    ] = "v1",
    views: Annotated[
        str,
        typer.Option(
            "--views",
            help="Comma-separated views to generate (front,side,back)",
        ),
    ] = "front,side,back",
    api_key: Annotated[
        Optional[str],
        typer.Option(
            "--api-key",
            help=f"Gemini API key (or set {GEMINI_API_KEY_ENV} env var)",
            envvar=GEMINI_API_KEY_ENV,
        ),
    ] = None,
    prompts_only: Annotated[
        bool,
        typer.Option(
            "--prompts-only",
            help="Only generate image prompts, don't call API",
        ),
    ] = False,
) -> None:
    """
    Generate T-pose images using Gemini API (Stage 4).
    
    Generates 3-view T-pose images (front, side, back) for 3D modeling.
    Requires GEMINI_API_KEY environment variable or --api-key option.
    
    \b
    Example:
      export GEMINI_API_KEY='your-api-key'
      uv run generate_prompts.py images -i configs/aethel.yaml -o output -v v1
      
    \b
    Prompts-only mode (no API calls):
      uv run generate_prompts.py images -i configs/aethel.yaml --prompts-only
    """
    # Step 1: Load the character specification
    print(f"Loading character spec from: {input_file}")
    
    try:
        spec = load_character_spec(input_file)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(code=1)
    
    print(f"Character: {spec.name} ({spec.role})")
    
    # Parse views
    view_list = [v.strip().lower() for v in views.split(",")]
    valid_views = ["front", "side", "back"]
    for v in view_list:
        if v not in valid_views:
            print(f"Error: Invalid view '{v}'. Valid views: {valid_views}", file=sys.stderr)
            raise typer.Exit(code=1)
    
    print(f"Views to generate: {', '.join(view_list)}")
    
    # Step 2: Generate images or prompts
    if prompts_only:
        # Prompts-only mode: just show the prompts that would be used
        print("\n[PROMPTS ONLY] Image generation prompts:\n")
        image_prompts = generate_image_prompts_only(spec, view_list)
        
        for key, prompt in image_prompts.items():
            print(f"{'='*60}")
            print(f"=== {key} ===")
            print(f"{'='*60}\n")
            print(prompt)
            print()
        
        print("Done! (No API calls made)")
        
    else:
        # Full image generation mode
        print(f"\nGenerating T-pose images (version: {version})...")
        
        # Check for API key
        if not api_key:
            api_key = os.environ.get(GEMINI_API_KEY_ENV)
        
        if not api_key:
            print(f"\nError: Gemini API key required.", file=sys.stderr)
            print(f"Set the {GEMINI_API_KEY_ENV} environment variable:", file=sys.stderr)
            print(f"  export {GEMINI_API_KEY_ENV}='your-api-key'", file=sys.stderr)
            print(f"\nOr use the --api-key option:", file=sys.stderr)
            print(f"  --api-key 'your-api-key'", file=sys.stderr)
            print(f"\nOr use --prompts-only to just see the prompts.", file=sys.stderr)
            raise typer.Exit(code=1)
        
        try:
            # Generate images
            images = generate_tpose_images(
                spec=spec,
                version=version,
                api_key=api_key,
                views=view_list,
            )
            
            # Create timestamped output directory
            run_output_dir = create_timestamped_output_dir(output_dir)
            
            # Save images
            print(f"\nSaving images to: {run_output_dir}/")
            saved_paths = save_generated_images(images, spec, run_output_dir, version)
            
            print(f"\nGenerated {len(saved_paths)} images:")
            for path in saved_paths:
                print(f"  ✓ {path}")
            
        except ImportError as e:
            print(f"\nError: {e}", file=sys.stderr)
            raise typer.Exit(code=1)
            
        except Exception as e:
            print(f"\nError generating images: {e}", file=sys.stderr)
            raise typer.Exit(code=1)
    
    print("\nDone!")


# -----------------------------------------------------------------------------
# COMMAND: all (Full pipeline)
# -----------------------------------------------------------------------------

@app.command("all")
def generate_all_command(
    input_file: Annotated[
        Path,
        typer.Option(
            "--input", "-i",
            help="Path to character spec file (YAML or JSON)",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir", "-o",
            help="Base output directory for all generated files",
        ),
    ] = Path("output"),
    version: Annotated[
        str,
        typer.Option(
            "--version", "-v",
            help="Version string suffix for filenames",
        ),
    ] = "v1",
    skip_refine: Annotated[
        bool,
        typer.Option(
            "--skip-refine",
            help="Skip LLM refinement (use static prompts only)",
        ),
    ] = False,
    web_search: Annotated[
        bool,
        typer.Option(
            "--web-search",
            help="Enable web search for LLM refinement",
        ),
    ] = False,
    skip_images: Annotated[
        bool,
        typer.Option(
            "--skip-images",
            help="Skip image generation (only generate prompts)",
        ),
    ] = False,
    skip_3d: Annotated[
        bool,
        typer.Option(
            "--skip-3d",
            help="Skip 3D model generation (Stage 5)",
        ),
    ] = False,
    auto_3d: Annotated[
        bool,
        typer.Option(
            "--auto-3d",
            help="Skip confirmation before 3D generation (for automation)",
        ),
    ] = False,
    use_all_views_cli: Annotated[
        bool,
        typer.Option(
            "--use-all-views",
            help="Use all 3 views (front/side/back) for 3D generation instead of just front",
        ),
    ] = False,
    provider_3d: Annotated[
        str,
        typer.Option(
            "--provider-3d",
            help="Hunyuan 3D provider: 'sdk' (default) or 'http'",
        ),
    ] = "sdk",
    timeout_3d: Annotated[
        int,
        typer.Option(
            "--timeout-3d",
            help="Timeout in seconds for 3D generation",
        ),
    ] = 600,
) -> None:
    """
    Run the full pipeline (Stages 1-5).
    
    Generates static prompts, refines with LLM, creates T-pose images,
    and generates a 3D model from the front view image.
    
    After Stage 4 (image generation), you'll be prompted to review the images
    before proceeding to 3D generation. Use --auto-3d to skip this confirmation.
    
    \b
    Required API keys:
      - OPENAI_API_KEY: For LLM refinement (Stage 2)
      - GEMINI_API_KEY: For image generation (Stage 4)
      - TENCENT_SECRET_ID/KEY: For 3D generation (Stage 5)
      - TENCENT_COS_BUCKET/REGION: For image upload to COS (Stage 5)
    
    \b
    Example (full pipeline with review):
      uv run generate_prompts.py all -i configs/aethel.yaml -v v1
    
    \b
    Example (automated, no confirmation):
      uv run generate_prompts.py all -i configs/aethel.yaml --auto-3d
    
    \b
    Example (automated with all 3 views for better 3D):
      uv run generate_prompts.py all -i configs/aethel.yaml --auto-3d --use-all-views
    
    \b
    Example (skip 3D generation):
      uv run generate_prompts.py all -i configs/aethel.yaml --skip-3d
    """
    # Step 1: Load spec
    print(f"Loading character spec from: {input_file}")
    
    try:
        spec = load_character_spec(input_file)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(code=1)
    
    print(f"Character: {spec.name} ({spec.role})")
    
    # Create timestamped output directory for this run
    run_output_dir = create_timestamped_output_dir(output_dir)
    print(f"\nOutput directory: {run_output_dir}/")
    
    # Step 2: Generate static prompts (Stages 1, 2a, 3)
    print(f"\n{'='*60}")
    print("STAGE 1 & 3: Generating static prompts...")
    print(f"{'='*60}")
    
    prompts = generate_all_prompts(spec)
    written_prompt_paths = write_prompts(prompts, spec, run_output_dir, version)
    
    print(f"Generated {len(written_prompt_paths)} static prompt files")
    
    # Step 3: LLM Refinement (Stage 2b)
    if not skip_refine:
        print(f"\n{'='*60}")
        print("STAGE 2: Refining prompts with LLM...")
        print(f"{'='*60}")
        
        openai_key = os.environ.get(OPENAI_API_KEY_ENV)
        
        if not openai_key:
            print(f"\nWarning: {OPENAI_API_KEY_ENV} not set. Skipping LLM refinement.")
            print("Set the environment variable to enable LLM refinement.")
        else:
            try:
                refined_prompts = refine_prompts_to_dict(
                    spec=spec,
                    api_key=openai_key,
                    use_web_search=web_search,
                )
                refined_paths = write_prompts(refined_prompts, spec, run_output_dir, version)
                print(f"Generated {len(refined_paths)} refined prompt files")
            except Exception as e:
                print(f"Warning: LLM refinement failed: {e}")
                print("Static prompts were still generated successfully.")
    else:
        print("\n(LLM refinement skipped)")
    
    # Step 4: Generate images (Stage 4)
    front_image_path: Optional[Path] = None
    
    if not skip_images:
        print(f"\n{'='*60}")
        print("STAGE 4: Generating T-pose images...")
        print(f"{'='*60}")
        
        gemini_key = os.environ.get(GEMINI_API_KEY_ENV)
        images_dir = run_output_dir / "images"
        
        if not gemini_key:
            print(f"\nWarning: {GEMINI_API_KEY_ENV} not set. Skipping image generation.")
            print("Set the environment variable to enable image generation.")
        else:
            try:
                images = generate_tpose_images(spec, version, gemini_key)
                saved_image_paths = save_generated_images(images, spec, images_dir, version)
                print(f"Generated {len(saved_image_paths)} images")
                
                # Find the front view image for Stage 5
                for img_path in saved_image_paths:
                    if "front" in img_path.name.lower():
                        front_image_path = img_path
                        break
                
            except Exception as e:
                print(f"Warning: Image generation failed: {e}")
                print("Prompts were still generated successfully.")
    else:
        print("\n(Image generation skipped)")
    
    # Step 5: Generate 3D model (Stage 5)
    if not skip_3d:
        # Human-in-the-loop: Ask user to review images before 3D generation
        proceed_with_3d = True
        use_all_views = use_all_views_cli  # Default from CLI option
        
        if front_image_path and front_image_path.exists() and not auto_3d:
            # Loop for regeneration options
            while True:
                print(f"\n{'='*60}")
                print("REVIEW GENERATED IMAGES")
                print(f"{'='*60}")
                print(f"\n📁 Images saved to: {images_dir}/")
                print(f"\n📷 Generated images:")
                if 'saved_image_paths' in dir() and saved_image_paths:
                    for img_path in saved_image_paths:
                        marker = "→" if img_path == front_image_path else " "
                        print(f"  {marker} {img_path.name}")
                print(f"\n🎯 Front image for 3D: {front_image_path.name}")
                print(f"\n💡 Please review the generated images before proceeding.")
                print(f"   Open the images folder to check quality and accuracy.")
                
                # Prompt for confirmation
                print()
                proceed_with_3d = typer.confirm(
                    "Proceed with 3D model generation?",
                    default=True,
                )
                
                if proceed_with_3d:
                    # Ask user whether to use front view only or all 3 views
                    print(f"\n{'='*60}")
                    print("3D GENERATION MODE")
                    print(f"{'='*60}")
                    print("\nChoose how to generate the 3D model:\n")
                    print("  [1] Front view only (faster, uses only the front image)")
                    print("  [2] All 3 views (better quality, uses front + side + back)")
                    print()
                    
                    mode_choice = typer.prompt(
                        "Your choice",
                        type=str,
                        default="1",
                    )
                    
                    use_all_views = (mode_choice == "2")
                    
                    if use_all_views:
                        print("\n✓ Using all 3 views for 3D generation (front + side + back)")
                    else:
                        print("\n✓ Using front view only for 3D generation")
                    
                    break  # User approved, proceed with 3D
                
                # User declined - offer regeneration options
                print(f"\n{'='*60}")
                print("REGENERATION OPTIONS")
                print(f"{'='*60}")
                print("\nChoose what to regenerate:\n")
                print("  [1] Regenerate front image entirely (new generation)")
                print("  [2] Modify front image with Gemini (edit with text prompt)")
                print("  [3] Regenerate side view only (from current front)")
                print("  [4] Regenerate back view only (from current front)")
                print("  [5] Regenerate side + back views (from current front)")
                print("  [6] Skip 3D generation (exit)")
                
                choice = typer.prompt(
                    "\nYour choice",
                    type=str,
                    default="6",
                )
                
                if choice == "1":
                    # Regenerate front image entirely
                    print(f"\n{'='*60}")
                    print("REGENERATING FRONT IMAGE")
                    print(f"{'='*60}")
                    
                    gemini_key = os.environ.get(GEMINI_API_KEY_ENV)
                    if not gemini_key:
                        print(f"\nError: {GEMINI_API_KEY_ENV} not set.")
                        continue
                    
                    try:
                        new_image = regenerate_single_view(
                            spec=spec,
                            view="front",
                            version=version,
                            api_key=gemini_key,
                        )
                        
                        # Save the new image, overwriting the old one
                        new_path = images_dir / new_image.get_filename(spec.name, version)
                        new_path.write_bytes(new_image.image_data)
                        front_image_path = new_path
                        
                        # Update saved_image_paths if it exists
                        if 'saved_image_paths' in dir() and saved_image_paths:
                            for i, p in enumerate(saved_image_paths):
                                if "front" in p.name.lower():
                                    saved_image_paths[i] = new_path
                                    break
                        
                        print(f"\n✓ New front image saved: {new_path.name}")
                        print("  Please review the new image.")
                        
                    except Exception as e:
                        print(f"\nError regenerating image: {e}")
                    
                    continue  # Loop back to show the review screen
                    
                elif choice == "2":
                    # Modify front image with Gemini
                    from src.stage4_image_generation import generate_view_from_reference
                    
                    print(f"\n{'='*60}")
                    print("MODIFY FRONT IMAGE WITH GEMINI")
                    print(f"{'='*60}")
                    print("\nDescribe the changes you want to make to the front image.")
                    print("Examples:")
                    print("  - 'Make the coat shorter to expose the knees'")
                    print("  - 'Change the pose to have arms more horizontal'")
                    print("  - 'Remove the hat and show the hair'")
                    print("  - 'Make the background pure white'")
                    
                    edit_prompt = typer.prompt(
                        "\nEdit prompt",
                        type=str,
                    )
                    
                    if not edit_prompt.strip():
                        print("\nNo edit prompt provided, returning to menu.")
                        continue
                    
                    gemini_key = os.environ.get(GEMINI_API_KEY_ENV)
                    if not gemini_key:
                        print(f"\nError: {GEMINI_API_KEY_ENV} not set.")
                        continue
                    
                    try:
                        print(f"\n  Editing front image with prompt: '{edit_prompt}'")
                        print(f"  Using model: gemini-3-pro-image-preview (Nano Banana Pro)")
                        
                        edited_data = edit_image_with_gemini(
                            source_image_path=front_image_path,
                            edit_prompt=edit_prompt,
                            api_key=gemini_key,
                        )
                        
                        # Save edited image with a new name to preserve original
                        edited_filename = front_image_path.stem + "_edited" + front_image_path.suffix
                        edited_path = images_dir / edited_filename
                        edited_path.write_bytes(edited_data)
                        
                        # Update front_image_path to use the edited version
                        front_image_path = edited_path
                        
                        # Update saved_image_paths if it exists
                        if 'saved_image_paths' in dir() and saved_image_paths:
                            saved_image_paths.append(edited_path)
                        
                        print(f"\n✓ Edited front image saved: {edited_path.name}")
                        
                        # Auto-regenerate side and back views from the edited front
                        print(f"\n  Regenerating side and back views from edited front...")
                        
                        for view in ["side", "back"]:
                            new_image = generate_view_from_reference(
                                spec=spec,
                                reference_image_data=edited_data,
                                target_view=view,
                                api_key=gemini_key,
                            )
                            
                            # Save the new image
                            new_path = images_dir / new_image.get_filename(spec.name, version)
                            new_path.write_bytes(new_image.image_data)
                            
                            # Update saved_image_paths
                            if 'saved_image_paths' in dir() and saved_image_paths:
                                replaced = False
                                for i, p in enumerate(saved_image_paths):
                                    if view in p.name.lower() and "edited" not in p.name.lower():
                                        saved_image_paths[i] = new_path
                                        replaced = True
                                        break
                                if not replaced:
                                    saved_image_paths.append(new_path)
                            
                            print(f"    ✓ {view} view regenerated: {new_path.name}")
                        
                        print("\n  Please review the edited images.")
                        
                    except Exception as e:
                        print(f"\nError editing/regenerating images: {e}")
                    
                    continue  # Loop back to show the review screen
                
                elif choice in ("3", "4", "5"):
                    # Regenerate side/back views from front
                    from src.stage4_image_generation import generate_view_from_reference
                    
                    views_to_regen = []
                    if choice == "3":
                        views_to_regen = ["side"]
                    elif choice == "4":
                        views_to_regen = ["back"]
                    else:  # choice == "5"
                        views_to_regen = ["side", "back"]
                    
                    print(f"\n{'='*60}")
                    print(f"REGENERATING {', '.join(v.upper() for v in views_to_regen)} VIEW(S)")
                    print(f"{'='*60}")
                    
                    gemini_key = os.environ.get(GEMINI_API_KEY_ENV)
                    if not gemini_key:
                        print(f"\nError: {GEMINI_API_KEY_ENV} not set.")
                        continue
                    
                    # Read front image data for reference
                    front_image_data = front_image_path.read_bytes()
                    
                    try:
                        for view in views_to_regen:
                            new_image = generate_view_from_reference(
                                spec=spec,
                                reference_image_data=front_image_data,
                                target_view=view,
                                api_key=gemini_key,
                            )
                            
                            # Save the new image
                            new_path = images_dir / new_image.get_filename(spec.name, version)
                            new_path.write_bytes(new_image.image_data)
                            
                            # Update saved_image_paths
                            if 'saved_image_paths' in dir() and saved_image_paths:
                                # Replace existing or append
                                replaced = False
                                for i, p in enumerate(saved_image_paths):
                                    if view in p.name.lower():
                                        saved_image_paths[i] = new_path
                                        replaced = True
                                        break
                                if not replaced:
                                    saved_image_paths.append(new_path)
                            
                            print(f"\n✓ New {view} view saved: {new_path.name}")
                        
                        print("\n  Please review the regenerated image(s).")
                        
                    except Exception as e:
                        print(f"\nError regenerating view(s): {e}")
                    
                    continue  # Loop back to show the review screen
                    
                else:
                    # Skip 3D generation (choice 6 or any other)
                    proceed_with_3d = False
                    print("\n(3D generation skipped by user)")
                    print(f"\nYou can generate the 3D model later with:")
                    print(f"  uv run generate_prompts.py hunyuan3d --image {front_image_path}")
                    break
        
        if proceed_with_3d:
            print(f"\n{'='*60}")
            print("STAGE 5: Generating 3D model with Hunyuan API...")
            print(f"{'='*60}")
            
            # Check if we have a front image from Stage 4
            if front_image_path and front_image_path.exists():
                # Check required env vars for 3D generation (with COS since we're uploading an image)
                missing_vars = check_required_env_vars(include_cos=True)
                
                if missing_vars:
                    print(f"\nWarning: Missing environment variables for 3D generation:")
                    for var in missing_vars:
                        print(f"  - {var}")
                    print("Skipping 3D model generation.")
                else:
                    # Check provider availability
                    if provider_3d == "sdk" and not is_sdk_available():
                        print("Warning: SDK provider not available, falling back to HTTP.")
                        actual_provider = "http"
                    else:
                        actual_provider = provider_3d
                    
                    try:
                        print(f"Using front image: {front_image_path}")
                        
                        # Find side and back views if using all views
                        side_image_path: Optional[Path] = None
                        back_image_path: Optional[Path] = None
                        
                        if use_all_views and 'saved_image_paths' in dir() and saved_image_paths:
                            for img_path in saved_image_paths:
                                img_name_lower = img_path.name.lower()
                                if "side" in img_name_lower:
                                    side_image_path = img_path
                                elif "back" in img_name_lower:
                                    back_image_path = img_path
                            
                            if side_image_path:
                                print(f"Using side image: {side_image_path}")
                            else:
                                print("Note: Side view image not found")
                            
                            if back_image_path:
                                print(f"Using back image: {back_image_path}")
                            else:
                                print("Note: Back view image not found")
                        
                        # Create output directory for 3D model
                        hunyuan3d_dir = run_output_dir / "hunyuan3d"
                        hunyuan3d_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Build kwargs for 3D generation
                        gen_kwargs = {
                            "image": front_image_path,
                            "output_dir": hunyuan3d_dir,
                            "timeout": timeout_3d,
                            "verbose": True,
                            "provider_type": actual_provider,
                        }
                        
                        # Add multi-view images if using all views
                        # Note: Hunyuan uses left_view for side view (profile facing left)
                        multi_view_kwargs = {}
                        if use_all_views:
                            if side_image_path and side_image_path.exists():
                                multi_view_kwargs["left_view"] = side_image_path
                            if back_image_path and back_image_path.exists():
                                multi_view_kwargs["back_view"] = back_image_path
                        
                        # Try with multi-view first, fall back to front-only if it fails
                        try:
                            result = generate_3d_model(**gen_kwargs, **multi_view_kwargs)
                        except Exception as multi_view_error:
                            if multi_view_kwargs and "InvalidParameter" in str(multi_view_error):
                                print(f"\nWarning: Multi-view failed (API may not support it yet)")
                                print("  Retrying with front view only...")
                                result = generate_3d_model(**gen_kwargs)
                            else:
                                raise
                        
                        if result.status == "DONE" and result.obj_path:
                            print(f"\n3D Model generated successfully!")
                            print(f"  OBJ: {result.obj_path}")
                            print(f"  Time: {result.elapsed_seconds:.1f}s")
                        else:
                            print(f"\nWarning: 3D generation completed with status: {result.status}")
                            if result.error_message:
                                print(f"  Error: {result.error_message}")
                                
                    except Exception as e:
                        print(f"Warning: 3D model generation failed: {e}")
                        print("Previous stages completed successfully.")
            else:
                if skip_images:
                    print("\n(3D generation skipped - no image available, Stage 4 was skipped)")
                else:
                    print("\nWarning: No front image available for 3D generation.")
                    print("Either image generation failed or no front view was created.")
    else:
        print("\n(3D model generation skipped)")
    
    print(f"\n{'='*60}")
    print("PIPELINE COMPLETE!")
    print(f"{'='*60}")
    print(f"  Output: {run_output_dir}/")
    print("\nDone!")


# -----------------------------------------------------------------------------
# COMMAND: hunyuan3d (Stage 5 - 3D Model Generation)
# -----------------------------------------------------------------------------

@app.command("hunyuan3d")
def hunyuan3d_command(
    input_file: Annotated[
        Optional[Path],
        typer.Option(
            "--input", "-i",
            help="Path to character spec file (YAML or JSON) - uses name for prompt",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    prompt: Annotated[
        Optional[str],
        typer.Option(
            "--prompt", "-p",
            help="Text prompt for 3D generation (alternative to config)",
        ),
    ] = None,
    image: Annotated[
        Optional[Path],
        typer.Option(
            "--image",
            help="Path to local image to convert to 3D",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    image_url: Annotated[
        Optional[str],
        typer.Option(
            "--image-url",
            help="URL of image to convert to 3D",
        ),
    ] = None,
    left_view: Annotated[
        Optional[Path],
        typer.Option(
            "--left-view",
            help="Path to left view image (for multi-view 3D reconstruction)",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    right_view: Annotated[
        Optional[Path],
        typer.Option(
            "--right-view",
            help="Path to right view image (for multi-view 3D reconstruction)",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    back_view: Annotated[
        Optional[Path],
        typer.Option(
            "--back-view",
            help="Path to back view image (for multi-view 3D reconstruction)",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir", "-o",
            help="Base output directory for 3D models",
        ),
    ] = Path("output/hunyuan3d"),
    timeout: Annotated[
        int,
        typer.Option(
            "--timeout",
            help="Maximum seconds to wait for job completion",
        ),
    ] = 600,
    poll_interval: Annotated[
        int,
        typer.Option(
            "--poll-interval",
            help="Initial seconds between status polls",
        ),
    ] = 10,
    provider: Annotated[
        str,
        typer.Option(
            "--provider",
            help="API provider: 'sdk' (default) or 'http' (fallback)",
        ),
    ] = "sdk",
) -> None:
    """
    Generate 3D model using Hunyuan 3D API (Stage 5).
    
    Converts a text prompt or image to a 3D model (.obj format).
    
    \b
    Input modes (use exactly ONE):
      --input/-i    Use character spec name as prompt
      --prompt/-p   Direct text prompt
      --image       Local image file (uploads to COS) - front view
      --image-url   Remote image URL
    
    \b
    Multi-view options (optional, use with --image or --image-url):
      --left-view   Left view image for better 3D reconstruction
      --right-view  Right view image for better 3D reconstruction
      --back-view   Back view image for better 3D reconstruction
    
    \b
    Provider options:
      --provider sdk   Tencent Cloud SDK (default, recommended)
      --provider http  Raw HTTP with TC3 signing (fallback)
    
    \b
    Required environment variables:
      TENCENT_SECRET_ID   - Tencent Cloud SecretId
      TENCENT_SECRET_KEY  - Tencent Cloud SecretKey
    
    \b
    For --image mode (or multi-view), also set:
      TENCENT_COS_BUCKET  - COS bucket name
      TENCENT_COS_REGION  - COS region (e.g., ap-guangzhou)
    
    \b
    Example (from character spec):
      uv run generate_prompts.py hunyuan3d -i configs/aethel.yaml
      
    \b
    Example (direct prompt):
      uv run generate_prompts.py hunyuan3d --prompt "A cute panda figurine"
      
    \b
    Example (from image):
      uv run generate_prompts.py hunyuan3d --image output/images/tpose_front.png
    
    \b
    Example (multi-view for better 3D reconstruction):
      uv run generate_prompts.py hunyuan3d --image front.png \\
        --left-view left.png --right-view right.png --back-view back.png
    
    \b
    Example (using HTTP fallback):
      uv run generate_prompts.py hunyuan3d --prompt "A robot" --provider http
    """
    # Step 1: Determine input mode
    final_prompt: Optional[str] = None
    final_image: Optional[Path] = None
    final_image_url: Optional[str] = None
    
    # Check for multi-view images
    has_multi_view = any([left_view, right_view, back_view])
    
    # Count how many inputs were provided
    input_count = sum([
        input_file is not None,
        prompt is not None,
        image is not None,
        image_url is not None,
    ])
    
    if input_count == 0:
        print("Error: Must provide exactly ONE input mode:", file=sys.stderr)
        print("  --input/-i     Character spec file", file=sys.stderr)
        print("  --prompt/-p    Direct text prompt", file=sys.stderr)
        print("  --image        Local image file", file=sys.stderr)
        print("  --image-url    Remote image URL", file=sys.stderr)
        raise typer.Exit(code=1)
    
    if input_count > 1:
        print("Error: Provide only ONE input mode.", file=sys.stderr)
        raise typer.Exit(code=1)
    
    # Validate multi-view usage (only with image or image_url)
    if has_multi_view and not (image or image_url):
        print("Error: Multi-view options (--left-view, --right-view, --back-view)", file=sys.stderr)
        print("       can only be used with --image or --image-url.", file=sys.stderr)
        raise typer.Exit(code=1)
    
    # Resolve the input
    if input_file:
        # Load character spec and use name + role as prompt
        try:
            spec = load_character_spec(input_file)
            # Build a 3D-focused prompt from the spec
            final_prompt = (
                f"3D model of {spec.name}, {spec.role}. "
                f"Style: {spec.game_style}. "
                f"Silhouette: {spec.silhouette}. "
                f"Colors: {', '.join(spec.color_palette)}."
            )
            print(f"Character: {spec.name} ({spec.role})")
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            raise typer.Exit(code=1)
    elif prompt:
        final_prompt = prompt
    elif image:
        final_image = image
    elif image_url:
        final_image_url = image_url
    
    # Step 2: Validate provider option
    if provider not in VALID_PROVIDERS:
        print(f"Error: Invalid provider '{provider}'.", file=sys.stderr)
        print(f"Valid options: {', '.join(VALID_PROVIDERS)}", file=sys.stderr)
        raise typer.Exit(code=1)
    
    # Check SDK availability if SDK provider requested
    if provider == "sdk" and not is_sdk_available():
        print("Error: SDK provider requested but SDK not installed.", file=sys.stderr)
        print("Install with: uv add tencentcloud-sdk-python-ai3d", file=sys.stderr)
        print("Or use --provider http as a fallback.", file=sys.stderr)
        raise typer.Exit(code=1)
    
    # Step 3: Check environment variables
    # COS is needed for local image uploads (main or multi-view)
    include_cos = final_image is not None or has_multi_view
    missing_vars = check_required_env_vars(include_cos=include_cos)
    
    if missing_vars:
        print(f"Error: Missing required environment variables:", file=sys.stderr)
        for var in missing_vars:
            print(f"  - {var}", file=sys.stderr)
        print(get_env_var_help(), file=sys.stderr)
        raise typer.Exit(code=1)
    
    # Step 4: Create timestamped output directory
    run_output_dir = create_timestamped_output_dir(output_dir)
    print(f"\nOutput directory: {run_output_dir}/")
    
    # Step 5: Generate 3D model
    print(f"\n{'='*60}")
    print(f"STAGE 5: Generating 3D model with Hunyuan API ({provider})...")
    print(f"{'='*60}\n")
    
    try:
        result = generate_3d_model(
            prompt=final_prompt,
            image=final_image,
            image_url=final_image_url,
            left_view=left_view,
            right_view=right_view,
            back_view=back_view,
            output_dir=run_output_dir,
            timeout=timeout,
            poll_interval=poll_interval,
            verbose=True,
            provider_type=provider,
        )
        
        if result.status == "DONE" and result.obj_path:
            print(f"\n{'='*60}")
            print("3D MODEL GENERATION COMPLETE!")
            print(f"{'='*60}")
            print(f"  Status: {result.status}")
            print(f"  Time: {result.elapsed_seconds:.1f}s")
            print(f"  Files: {len(result.all_files)}")
            print(f"\n  Main OBJ: {result.obj_path}")
            print(f"  Metadata: {result.metadata_path}")
        elif result.status == "FAIL":
            print(f"\nError: Job failed: {result.error_message}", file=sys.stderr)
            raise typer.Exit(code=1)
        else:
            print(f"\nWarning: Job completed but no .obj file found.", file=sys.stderr)
            print(f"  Status: {result.status}")
            print(f"  Files: {[str(f) for f in result.all_files]}")
            
    except TimeoutError as e:
        print(f"\nError: {e}", file=sys.stderr)
        print("Try increasing --timeout value.", file=sys.stderr)
        raise typer.Exit(code=1)
        
    except Exception as e:
        print(f"\nError generating 3D model: {e}", file=sys.stderr)
        raise typer.Exit(code=1)
    
    print("\nDone!")


# -----------------------------------------------------------------------------
# SCRIPT ENTRY POINT
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    app()
