# src/__init__.py
# This file marks the 'src' directory as a Python package.
# It allows us to import modules from this directory using:
#   from src.models import CharacterSpec
#   from src.stage1_base_prompts import generate_base_prompts
#
# Package structure (matching the pipeline):
#   src/
#   ├── models.py                  - Data models (CharacterSpec dataclass)
#   ├── stage1_base_prompts.py     - Stage 1: Base 2D prompts (static)
#   ├── stage2_gemini_prompts.py   - Stage 2a: Gemini meta-prompts (static)
#   ├── stage2_llm_refiner.py      - Stage 2b: LLM-refined prompts (OpenAI API)
#   ├── stage3_common_prompts.py   - Stage 3: Checklist and design notes
#   ├── stage4_image_generation.py - Stage 4: Gemini image generation
#   └── file_utils.py              - File output utilities

# We can optionally re-export commonly used items here for convenience.
# This allows users to do: from src import CharacterSpec
# Instead of: from src.models import CharacterSpec

from .models import CharacterSpec, load_character_spec
from .stage1_base_prompts import generate_base_prompts
from .stage2_gemini_prompts import generate_gemini_prompts
from .stage2_llm_refiner import (
    refine_prompts_with_llm,
    refine_prompts_to_dict,
    preview_llm_requests,
    OPENAI_API_KEY_ENV,
)
from .stage3_common_prompts import generate_common_prompts
from .stage4_image_generation import (
    generate_tpose_images,
    generate_image_prompts_only,
    save_generated_images,
    GEMINI_API_KEY_ENV,
)
from .file_utils import write_prompts, print_prompts_to_stdout

# __all__ defines what gets exported when someone does "from src import *"
# It's good practice to explicitly list public API items.
__all__ = [
    # Data models
    "CharacterSpec",
    "load_character_spec",
    # Stage 1: Base prompts
    "generate_base_prompts",
    # Stage 2a: Gemini meta-prompts
    "generate_gemini_prompts",
    # Stage 2b: LLM refinement
    "refine_prompts_with_llm",
    "refine_prompts_to_dict",
    "preview_llm_requests",
    # Stage 3: Common prompts
    "generate_common_prompts",
    # Stage 4: Image generation
    "generate_tpose_images",
    "generate_image_prompts_only",
    "save_generated_images",
    # File utilities
    "write_prompts",
    "print_prompts_to_stdout",
    # Environment variable names for API keys
    "OPENAI_API_KEY_ENV",
    "GEMINI_API_KEY_ENV",
]
