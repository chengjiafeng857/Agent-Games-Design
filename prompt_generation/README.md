# AI Character Prompt Generator

A clean, teachable Python CLI tool that generates structured text prompts for the **2D → 3D character pipeline**.

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      AI CHARACTER PROMPT PIPELINE                            │
│                                                                              │
│   TEXT SPEC  →  BASE PROMPTS  →  LLM REFINE  →  CHECKLIST  →  IMAGE GEN    │
│   (YAML/JSON)    (Stage 1)       (Stage 2)      (Stage 3)     (Stage 4)    │
│                                                                     ↓        │
│                                                               HUNYUAN 3D    │
│                                                               (Stage 5)     │
│                                                                              │
│   Stage 2: Uses OpenAI GPT-5 (with web search tool) to refine prompts       │
│   Stage 4: Generates T-pose images (front/side/back) via Gemini API         │
│   Stage 5: Converts images/prompts to 3D models via Hunyuan API → .obj      │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Install dependencies with uv
uv sync

# Set up API keys (copy template and edit)
cp .env.example .env
# Edit .env and add your API keys

# Generate static prompts (Stages 1, 2a, 3) - no API key needed
uv run generate_prompts.py prompts -i configs/aethel.yaml

# Refine prompts with OpenAI GPT (Stage 2b)
uv run generate_prompts.py refine -i configs/aethel.yaml

# Refine with web search (for current AI art trends)
uv run generate_prompts.py refine -i configs/aethel.yaml --web-search

# Generate T-pose images (Stage 4)
uv run generate_prompts.py images -i configs/aethel.yaml

# Generate 3D model with Hunyuan API (Stage 5) 
uv run generate_prompts.py hunyuan3d -i configs/aethel.yaml
uv run generate_prompts.py hunyuan3d --image output/images/tpose_front.png
uv run generate_prompts.py hunyuan3d --prompt "A cute panda figurine"

# Run FULL pipeline (all stages)
uv run generate_prompts.py all -i configs/aethel.yaml

# Preview mode (no API calls)
uv run generate_prompts.py refine -i configs/aethel.yaml --preview
uv run generate_prompts.py images -i configs/aethel.yaml --prompts-only
```

## API Keys Setup

### Option 1: `.env` File (Recommended)

Copy the template and add your keys:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# OpenAI (Stage 2 - LLM Refinement)
OPENAI_API_KEY=sk-your-openai-key-here

# Google Gemini (Stage 4 - Image Generation)
GEMINI_API_KEY=your-gemini-key-here

# Tencent Cloud (Stage 5 - Hunyuan 3D) - Required
TENCENT_SECRET_ID=your-tencent-secret-id
TENCENT_SECRET_KEY=your-tencent-secret-key

# Tencent COS (Stage 5 - for --image uploads) - Required for image mode
TENCENT_COS_BUCKET=your-bucket-1250000000
TENCENT_COS_REGION=ap-guangzhou

# Hunyuan 3D Settings (Stage 5 - Optional)
HUNYUAN3D_ENABLE_PBR=false
HUNYUAN3D_FACE_COUNT=500000
HUNYUAN3D_GENERATE_TYPE=Normal
HUNYUAN3D_POLYGON_TYPE=triangle
```

> ⚠️ Never commit `.env` to version control! It's already in `.gitignore`.

### Option 2: Environment Variables

```bash
export OPENAI_API_KEY='sk-...'
export GEMINI_API_KEY='AI...'
export TENCENT_SECRET_ID='your-id'
export TENCENT_SECRET_KEY='your-key'
export TENCENT_COS_BUCKET='bucket-1250000000'
export TENCENT_COS_REGION='ap-guangzhou'
```

### Required Keys

| Stage | API Key | Description | Get Key |
|-------|---------|-------------|---------|
| Stage 2 (refine) | `OPENAI_API_KEY` | OpenAI GPT-5 with web search | [platform.openai.com](https://platform.openai.com/api-keys) |
| Stage 4 (images) | `GEMINI_API_KEY` | Google Gemini image gen | [aistudio.google.com](https://aistudio.google.com/apikey) |
| Stage 5 (hunyuan3d) | `TENCENT_SECRET_ID` | Tencent Cloud credentials | [console.cloud.tencent.com/cam/capi](https://console.cloud.tencent.com/cam/capi) |
| Stage 5 (hunyuan3d) | `TENCENT_SECRET_KEY` | Tencent Cloud credentials | [console.cloud.tencent.com/cam/capi](https://console.cloud.tencent.com/cam/capi) |
| Stage 5 (--image) | `TENCENT_COS_BUCKET` | COS bucket for image uploads | [console.cloud.tencent.com/cos](https://console.cloud.tencent.com/cos) |
| Stage 5 (--image) | `TENCENT_COS_REGION` | COS region (e.g., ap-guangzhou) | See bucket settings |

### Hunyuan 3D Settings (Optional)

These environment variables control the Hunyuan 3D generation settings:

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `HUNYUAN3D_ENABLE_PBR` | `true`, `false` | `false` | Enable PBR (Physically Based Rendering) materials |
| `HUNYUAN3D_FACE_COUNT` | `40000` - `1500000` | `500000` | Polygon face count for the generated model |
| `HUNYUAN3D_GENERATE_TYPE` | `Normal`, `LowPoly`, `Geometry`, `Sketch` | `Normal` | Generation mode (see below) |
| `HUNYUAN3D_POLYGON_TYPE` | `triangle`, `quadrilateral` | `triangle` | Polygon type (LowPoly mode only) |

**GenerateType Options:**

- **Normal** - Textured geometry model (default)
- **LowPoly** - Intelligently reduced faces for game-ready models
- **Geometry** - White model without texture (for sculpting)
- **Sketch** - Generate from sketch/line art (can combine prompt + image)

### OpenAI Models Supported

The refiner uses the **Responses API** with GPT-5:

| Model | Description |
|-------|-------------|
| `gpt-5` | Flagship reasoning model (default) |
| `gpt-5-mini` | Faster, cost-efficient |
| `gpt-5-nano` | Fastest, lowest cost |
| `gpt-4.1` | Smart non-reasoning model (1M context) |

With `--web-search` enabled, the model uses the `web_search` tool to find current AI art trends and best practices.

## Project Structure (Teachable Code)

```
prompt_generation/
├── generate_prompts.py          # Main CLI entry point (thin layer)
├── src/
│   ├── __init__.py                # Package exports
│   ├── models.py                  # CharacterSpec dataclass + file loading
│   ├── stage1_base_prompts.py     # Stage 1: Base 2D prompts (static)
│   ├── stage2_gemini_prompts.py   # Stage 2a: Gemini meta-prompts (static)
│   ├── stage2_llm_refiner.py      # Stage 2b: LLM-refined prompts (OpenAI)
│   ├── stage3_common_prompts.py   # Stage 3: Checklist and design notes
│   ├── stage4_image_generation.py # Stage 4: Gemini image generation
│   ├── stage5_hunyuan3d.py        # Stage 5: Hunyuan 3D orchestration
│   ├── providers/                 # Hunyuan 3D API providers
│   │   ├── __init__.py            # Provider factory + exports
│   │   ├── hunyuan3d_provider.py  # Provider abstraction (ABC)
│   │   ├── raw_http_hunyuan3d.py  # Raw HTTP + TC3 signing
│   │   ├── sdk_hunyuan3d.py       # Tencent Cloud SDK provider
│   │   └── tencent_cos.py         # COS image uploader (HTTP + SDK)
│   └── file_utils.py              # File output utilities
├── tests/                         # pytest tests
│   ├── conftest.py                # Test fixtures
│   ├── test_hunyuan3d_provider.py # Provider tests
│   └── test_stage5_hunyuan3d.py   # Orchestration tests
├── configs/
│   ├── _template.yaml           # Character spec template with docs
│   └── aethel.yaml              # Example character spec
├── pyproject.toml               # Project config for uv
├── requirements.txt             # Dependencies
└── README.md                    # This file
```

### Module Responsibilities

| Module | Pipeline Stage | Description |
|--------|----------------|-------------|
| `models.py` | Input | `CharacterSpec` dataclass + YAML/JSON loading |
| `stage1_base_prompts.py` | Stage 1 | Base 2D prompts (static templates) |
| `stage2_gemini_prompts.py` | Stage 2a | Meta-prompts for manual Gemini use |
| `stage2_llm_refiner.py` | **Stage 2b** | **LLM-refined prompts via OpenAI API** |
| `stage3_common_prompts.py` | Stage 3 | Checklist and design notes for humans |
| `stage4_image_generation.py` | Stage 4 | Gemini API image generation (3 views) |
| `stage5_hunyuan3d.py` | **Stage 5** | **Hunyuan 3D API → local .obj** |
| `providers/` | Stage 5 | Provider abstraction + implementations |
| `file_utils.py` | Output | File writing and path resolution |

## Output Structure

Each run creates a **timestamped folder** inside `output/`:

```
output/
├── 2024-12-09_15-30-45/              # Run 1
│   ├── base/                         # Stage 1: Base 2D prompts (static)
│   │   ├── aethel_2d_base_v1.txt
│   │   └── aethel_2d_sheet_v1.txt
│   ├── gemini/                       # Stage 2a: Gemini meta-prompts (static)
│   │   ├── aethel_2d_refiner_v1.txt
│   │   └── aethel_tpose_prompt_v1.txt
│   ├── refined/                      # Stage 2b: LLM-refined prompts (OpenAI)
│   │   ├── aethel_refined_concept_v1.txt
│   │   ├── aethel_refined_tpose_front_v1.txt
│   │   ├── aethel_refined_tpose_side_v1.txt
│   │   └── aethel_refined_tpose_back_v1.txt
│   ├── common/                       # Stage 3: Checklist & notes
│   │   ├── aethel_2d_refinement_criteria_v1.txt
│   │   └── aethel_design_notes_v1.txt
│   └── images/                       # Stage 4: Generated T-pose images
│       ├── aethel_tpose_front_v1.png
│       ├── aethel_tpose_side_v1.png
│       └── aethel_tpose_back_v1.png
├── hunyuan3d/                        # Stage 5: 3D model output
│   └── 2024-12-09_16-00-12/          # Timestamped run
│       ├── model.obj                 # Main 3D model
│       ├── material.mtl              # Material file
│       ├── texture.png               # Textures (if any)
│       ├── preview.png               # Preview image from API
│       └── metadata.json             # Job info and file manifest
└── 2024-12-09_16-00-12/              # Run 2 (different timestamp)
    └── ...
```

## CLI Commands

### `prompts` - Generate Static Prompts (Stages 1, 2a, 3)

```bash
uv run generate_prompts.py prompts -i configs/aethel.yaml
uv run generate_prompts.py prompts -i configs/aethel.yaml --dry-run  # Preview
```

### `refine` - LLM Prompt Refinement (Stage 2b)

```bash
# Basic refinement
uv run generate_prompts.py refine -i configs/aethel.yaml

# With web search for current AI art trends
uv run generate_prompts.py refine -i configs/aethel.yaml --web-search

# Choose model
uv run generate_prompts.py refine -i configs/aethel.yaml --model gpt-4o-mini

# Preview requests (no API calls)
uv run generate_prompts.py refine -i configs/aethel.yaml --preview
```

### `images` - Generate T-pose Images (Stage 4)

```bash
# Generate images
uv run generate_prompts.py images -i configs/aethel.yaml

# Specific views only
uv run generate_prompts.py images -i configs/aethel.yaml --views front,side

# Preview prompts (no API calls)
uv run generate_prompts.py images -i configs/aethel.yaml --prompts-only
```

### `hunyuan3d` - Generate 3D Model (Stage 5) ⭐ NEW

Convert text prompts or images to 3D models using the Hunyuan 3D API.

```bash
# From character spec (uses name + role as prompt)
uv run generate_prompts.py hunyuan3d -i configs/aethel.yaml

# Direct text prompt
uv run generate_prompts.py hunyuan3d --prompt "A cute panda figurine"

# From local image (uploads to Tencent COS)
uv run generate_prompts.py hunyuan3d --image output/images/tpose_front.png

# From remote image URL
uv run generate_prompts.py hunyuan3d --image-url "https://example.com/image.png"

# Multi-view for better 3D reconstruction
uv run generate_prompts.py hunyuan3d --image front.png \
  --left-view left.png --right-view right.png --back-view back.png

# With custom timeout (default: 600 seconds)
uv run generate_prompts.py hunyuan3d --prompt "A robot" --timeout 900

# Using Tencent Cloud SDK instead of raw HTTP (optional)
uv run generate_prompts.py hunyuan3d --prompt "A robot" --provider sdk
```

**Input Modes** (use exactly ONE):

- `--input/-i` - Character spec file (uses name + role as prompt)
- `--prompt/-p` - Direct text description
- `--image` - Local image file (front view, requires COS credentials)
- `--image-url` - Remote image URL

**Multi-View Options** (optional, use with `--image` or `--image-url`):

- `--left-view` - Left view image for better 3D reconstruction
- `--right-view` - Right view image for better 3D reconstruction
- `--back-view` - Back view image for better 3D reconstruction

**Provider Options:**

- `--provider http` - Raw HTTP with TC3 signing (default, no SDK needed)
- `--provider sdk` - Tencent Cloud SDK (requires: `uv add tencentcloud-sdk-python-ai3d`)

**Generation Settings** (via environment variables):

- `HUNYUAN3D_ENABLE_PBR` - Enable PBR materials (`true`/`false`, default: `false`)
- `HUNYUAN3D_FACE_COUNT` - Polygon count (`40000`-`1500000`, default: `500000`)
- `HUNYUAN3D_GENERATE_TYPE` - Generation mode:
  - `Normal` - Textured geometry model (default)
  - `LowPoly` - Intelligently reduced faces
  - `Geometry` - White model without texture
  - `Sketch` - Generate from sketch/line art
- `HUNYUAN3D_POLYGON_TYPE` - For LowPoly mode: `triangle` (default) or `quadrilateral`

**Output:**

- Downloads and extracts the 3D model (`.obj`, `.glb`, `.mtl`, textures)
- Identifies the main `.obj` file (largest by size)
- Creates `metadata.json` with job info and file manifest
- Prints the path to the main `.obj` file

### `all` - Full Pipeline (All Stages)

```bash
# Full pipeline
uv run generate_prompts.py all -i configs/aethel.yaml

# With web search for refinement
uv run generate_prompts.py all -i configs/aethel.yaml --web-search

# Skip LLM refinement (static prompts only)
uv run generate_prompts.py all -i configs/aethel.yaml --skip-refine

# Skip image generation (prompts only)
uv run generate_prompts.py all -i configs/aethel.yaml --skip-images
```

## Character Spec Format

**Start with the template:**

```bash
cp configs/_template.yaml configs/my_character.yaml
```

Example character spec:

```yaml
name: "Aethel"
role: "Android archaeologist"
game_style: "stylized sci-fi, slightly realistic"
silhouette: "tall, long coat, mechanical arm"
color_palette:
  - "teal"
  - "black"
  - "orange accents"
key_props:
  - "data tablet"
  - "arm-mounted scanner"
animation_focus:
  - "walk"
  - "idle scanning"
  - "simple attack"
extra_notes: "Set in a neon-lit cyber-ruin environment, neutral expression."
```

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | ✅ Yes | Character name (used in filenames) |
| `role` | No | Character's role/occupation |
| `game_style` | No | Visual art style |
| `silhouette` | No | Body shape and distinctive features |
| `color_palette` | No | List of main colors |
| `key_props` | No | Important items/accessories |
| `animation_focus` | No | Planned animation types |
| `extra_notes` | No | Additional context |

## Prompt Stages Explained

### Stage 1: Base 2D Prompts (Static)

Simple template-based prompts as a starting point.

### Stage 2a: Gemini Meta-Prompts (Static)

Meta-prompts you can manually paste into Gemini for refinement.

### Stage 2b: LLM-Refined Prompts (OpenAI GPT-5) ⭐

**The key feature!** Uses OpenAI GPT-5 via the Responses API to transform your character spec into optimized image generation prompts.

**Models:**

- **gpt-5**: Flagship reasoning model (default)
- **gpt-5-mini**: Faster, cost-efficient
- **gpt-4.1**: Smart non-reasoning model

**With `--web-search` enabled:**

- Uses the `web_search` tool to find current AI art prompt trends
- Searches for popular style keywords that work with image generators
- Finds reference images of similar character types

The LLM generates:

1. `refined_concept` - Optimized concept art prompt
2. `refined_tpose_front` - Front view T-pose prompt
3. `refined_tpose_side` - Side view T-pose prompt  
4. `refined_tpose_back` - Back view T-pose prompt

These refined prompts are ready to use directly in image generators!

### Stage 3: Checklist & Notes

Human-readable documents for validation:

- **2D Refinement Criteria**: Checklist to validate T-pose images
- **Design Notes**: Internal reference document

### Stage 4: Image Generation (Gemini API)

Generates actual T-pose images using Gemini 3 Pro Image Preview:

- Front view
- Side view  
- Back view

### Stage 5: Hunyuan 3D Model Generation ⭐ NEW

**Fully automated** 2D → 3D conversion using the Hunyuan 3D API:

1. **Upload** - Upload local images to Tencent COS (if using `--image`)
2. **Submit** - Send prompt or image(s) to Hunyuan 3D API
3. **Poll** - Wait for job completion with exponential backoff
4. **Download** - Fetch the generated 3D model (ZIP with OBJ/GLB/MTL/textures)
5. **Extract** - Unpack files and identify the main `.obj`
6. **Metadata** - Write `metadata.json` with job info

**Features:**

- **Multi-view support** - Provide left/right/back views for better 3D reconstruction
- **Configurable settings** - Control PBR materials, polygon count, generation mode
- **Multiple providers** - Raw HTTP (default) or Tencent Cloud SDK
- **Automatic COS upload** - Local images are uploaded via SDK for reliability

**Technical Details:**

- Uses raw HTTP with TC3-HMAC-SHA256 authentication (or optional SDK)
- Local images are uploaded to Tencent COS via SDK (public-read ACL)
- Supports text prompts, single image, or multi-view images
- Automatic retry with exponential backoff
- Configurable timeout (default: 10 minutes)

## Workflow

1. **Define Character** → Create YAML spec in `configs/`
2. **Refine Prompts** → Run `refine` command with OpenAI
3. **Generate Images** → Run `images` command with Gemini
4. **Validate** → Use `2d_refinement_criteria` checklist
5. **Convert to 3D** → Run `hunyuan3d` command with validated T-pose ← **Automated!**
6. **Use Model** → Local `.obj` ready for import into Blender, Unity, etc.

Or run `all` to do prompts + images in one command, then `hunyuan3d` to convert!

## Code Design (For Learners)

This codebase is designed to be **teachable**:

- **Single Responsibility**: Each module does ONE thing
- **Extensive Comments**: Every function has line-by-line explanations
- **Type Hints**: All functions have full type annotations
- **Dataclasses**: Modern Python data modeling with `@dataclass`
- **Clean Separation**: CLI layer is thin, logic is in `src/`

### Key Python Concepts Demonstrated

| Concept | Where |
|---------|-------|
| `@dataclass` | `src/models.py` - CharacterSpec |
| `pathlib.Path` | `src/file_utils.py` - file operations |
| Type hints | Everywhere - `def func(x: str) -> dict[str, str]` |
| `logging` | `src/models.py` - warning messages |
| f-strings | All prompt templates |
| Dictionary merging | `generate_prompts.py` - `dict.update()` |
| CLI with Typer | `generate_prompts.py` - `@app.command()` |
| API clients | `stage2_llm_refiner.py`, `stage4_image_generation.py` |

## License

MIT
