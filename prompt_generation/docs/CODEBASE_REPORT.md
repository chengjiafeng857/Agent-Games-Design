# Codebase Report: AI Character Prompt Generator

## Project Overview

This is a **Python CLI tool** that generates 3D game character models through a multi-stage AI pipeline. It transforms simple character descriptions (YAML specs) into production-ready 3D models by leveraging multiple AI services.

**Primary Use Case**: Rapid game character creation for game developers and artists.

**Domain**: Game development, character design, AI art generation, 3D modeling

---

## Technology Stack

| Category | Technologies |
|----------|-------------|
| **Language** | Python 3.11+ |
| **CLI Framework** | Typer |
| **AI Services** | OpenAI GPT-5, Google Gemini, Tencent Hunyuan 3D |
| **Cloud Services** | Tencent Cloud COS (storage) |
| **Data Format** | YAML/JSON configs → Python dataclasses |
| **Package Manager** | uv (modern pip alternative) |
| **Testing** | pytest |

---

## Directory Structure

```
prompt_generation/
├── generate_prompts.py           # Main CLI entry point (~800 LOC)
│
├── src/                          # Core pipeline logic
│   ├── __init__.py               # Package exports
│   ├── models.py                 # CharacterSpec dataclass + file loading
│   ├── stage1_base_prompts.py    # Stage 1: Base 2D prompts (static)
│   ├── stage2_gemini_prompts.py  # Stage 2a: Gemini meta-prompts (static)
│   ├── stage2_llm_refiner.py     # Stage 2b: LLM-refined prompts via OpenAI
│   ├── stage3_common_prompts.py  # Stage 3: Checklist and design notes
│   ├── stage4_image_generation.py# Stage 4: Gemini image generation
│   ├── stage5_hunyuan3d.py       # Stage 5: 3D model orchestration
│   ├── file_utils.py             # File I/O and path utilities
│   ├── archive/                  # Legacy/archived code
│   └── providers/                # Hunyuan 3D API implementations
│       ├── __init__.py           # Provider factory and exports
│       ├── hunyuan3d_provider.py # Abstract base class
│       ├── raw_http_hunyuan3d.py # Raw HTTP + TC3 signing
│       ├── sdk_hunyuan3d.py      # Tencent Cloud SDK wrapper
│       ├── tencent_cos.py        # COS image uploader
│       └── openai_compat_hunyuan3d.py # OpenAI-compatible wrapper
│
├── configs/                      # Character specifications
│   ├── _template.yaml            # Template with documentation
│   ├── aethel.yaml               # Example character spec
│   ├── empty.yaml                # Minimal example
│   └── generated_config_*.yaml   # Auto-generated configs
│
├── tests/                        # pytest test suite
│   ├── conftest.py               # Fixtures and mock data
│   ├── test_stage5_hunyuan3d.py  # Stage 5 tests
│   ├── test_hunyuan3d_provider.py# Provider tests
│   └── test_consistent_views.py  # Multi-view consistency tests
│
├── docs/                         # Documentation
│   ├── CODEBASE_REPORT.md        # This file
│   ├── CONSISTENT_VIEWS.md       # Multi-view generation strategy
│   ├── QUICK_START_CONSISTENT_VIEWS.md
│   ├── CHANGES_CONSISTENT_VIEWS.md
│   └── IMPLEMENTATION_SUMMARY.md
│
├── output/                       # Generated outputs (timestamped)
│   └── YYYY-MM-DD_HH-MM-SS/
│       ├── base/                 # Stage 1 output
│       ├── gemini/               # Stage 2a output
│       ├── refined/              # Stage 2b output
│       ├── common/               # Stage 3 output
│       ├── images/               # Stage 4 output (PNG)
│       └── hunyuan3d/            # Stage 5 output (3D models)
│
├── .env.example                  # API key template
├── pyproject.toml                # uv project config
├── requirements.txt              # pip dependencies
└── README.md                     # Main documentation
```

**Total Core Logic**: ~3,100 lines of code

---

## 5-Stage Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PIPELINE OVERVIEW                           │
└─────────────────────────────────────────────────────────────────────┘

YAML Spec → Stage 1 → Stage 2a/2b → Stage 3 → Stage 4 → Stage 5 → 3D Model
            (base     (meta/LLM     (checklist) (images)  (Hunyuan3D)
            prompts)   refine)
```

### Stage Details

| Stage | Module | Purpose | API Required |
|-------|--------|---------|--------------|
| **1** | `stage1_base_prompts.py` | Template-based prompt generation | None (static) |
| **2a** | `stage2_gemini_prompts.py` | Meta-prompts for Gemini | None (static) |
| **2b** | `stage2_llm_refiner.py` | GPT-5 prompt refinement with web search | OpenAI |
| **3** | `stage3_common_prompts.py` | Quality checklists and design notes | None (static) |
| **4** | `stage4_image_generation.py` | T-pose images (front, side, back) | Google Gemini |
| **5** | `stage5_hunyuan3d.py` | 3D model generation | Tencent Hunyuan 3D |

### Data Flow

```
┌──────────────┐
│  YAML Spec   │
│ (Character)  │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Stage 1    │────▶│  Stage 2a/b  │────▶│   Stage 3    │
│ Base Prompts │     │ LLM Refine   │     │  Checklists  │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐     ┌──────────────┐
                     │   Stage 4    │────▶│   Stage 5    │
                     │   Images     │     │  3D Models   │
                     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │  .obj/.mtl   │
                                          │   Textures   │
                                          └──────────────┘
```

---

## Key Components

### Data Models (`src/models.py`)

```python
@dataclass
class CharacterSpec:
    name: str                           # Required
    role: str = ""                      # Optional
    game_style: str = ""                # Optional
    silhouette: str = ""                # Optional
    color_palette: list[str] = field(default_factory=list)
    key_props: list[str] = field(default_factory=list)
    animation_focus: list[str] = field(default_factory=list)
    extra_notes: Optional[str] = None
```

### Provider Architecture (`src/providers/`)

Abstract base class with multiple implementations:

```python
class Hunyuan3DProvider(ABC):
    @abstractmethod
    def submit(...) -> Hunyuan3DJobResult: ...

    @abstractmethod
    def poll(job_id: str, timeout: int) -> Hunyuan3DJobResult: ...

    @abstractmethod
    def download_result(...) -> Path: ...

# Implementations
class SDKHunyuan3DProvider(Hunyuan3DProvider):    # Tencent SDK
class RawHttpHunyuan3DProvider(Hunyuan3DProvider): # Raw HTTP + TC3 auth
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `prompts` | Generate static prompts (Stages 1, 2a, 3) |
| `refine` | Refine prompts with OpenAI GPT (Stage 2b) |
| `images` | Generate T-pose images with Gemini (Stage 4) |
| `hunyuan3d` | Generate 3D models (Stage 5) |
| `all` | Run entire pipeline |

---

## Architectural Patterns

### 1. Provider Abstraction
Abstract base class with SDK and HTTP implementations allows easy extension and fallback options.

### 2. Dataclass-First Design
Type-safe data models throughout: `CharacterSpec`, `RefinedPrompts`, `Hunyuan3DResult`.

### 3. Factory Pattern
`get_provider()` function returns appropriate provider class based on configuration.

### 4. Consistent Multi-View Generation
Front view generated from text prompt serves as reference for side/back views.

### 5. Single Responsibility
Each module handles exactly one pipeline stage.

---

## Configuration

### Character Specification (YAML)

```yaml
name: "Aethel"                           # REQUIRED
role: "Android archaeologist"            # OPTIONAL
game_style: "stylized sci-fi"            # OPTIONAL
silhouette: "tall, long coat"            # OPTIONAL
color_palette:                           # OPTIONAL
  - "teal"
  - "black"
key_props:                               # OPTIONAL
  - "data tablet"
  - "arm-mounted scanner"
animation_focus:                         # OPTIONAL
  - "walk"
  - "idle scanning"
extra_notes: "..."                       # OPTIONAL
```

### Environment Variables

| Variable | Stage | Required |
|----------|-------|----------|
| `OPENAI_API_KEY` | 2b | Optional |
| `GEMINI_API_KEY` | 4 | Optional |
| `TENCENT_SECRET_ID` | 5 | Required for 3D |
| `TENCENT_SECRET_KEY` | 5 | Required for 3D |
| `TENCENT_COS_BUCKET` | 5 | For local image upload |
| `TENCENT_COS_REGION` | 5 | For local image upload |
| `HUNYUAN3D_ENABLE_PBR` | 5 | Optional |
| `HUNYUAN3D_FACE_COUNT` | 5 | Optional (default: 500000) |

---

## Dependencies

### Required

```
pyyaml>=6.0                    # YAML parsing
typer>=0.12.0                  # CLI framework
python-dotenv>=1.0.0           # .env loading
openai>=1.0.0                  # OpenAI API
google-genai>=1.0.0            # Google Gemini API
Pillow>=10.0.0                 # Image handling
```

### Optional

```
tencentcloud-sdk-python        # Tencent Cloud SDK
tencentcloud-sdk-python-ai3d   # Hunyuan 3D SDK
httpx                          # HTTP client
```

### External API Services

| Service | Purpose | Authentication |
|---------|---------|----------------|
| OpenAI API | GPT-5 prompt refinement | API key |
| Google Gemini | Image generation | API key |
| Tencent Hunyuan 3D | 3D model generation | SecretId/SecretKey |
| Tencent COS | Image storage | SecretId/SecretKey |

---

## Output Structure

```
output/2025-12-14_19-46-10/
├── base/
│   └── {name}_2d_base_v1.txt
├── gemini/
│   └── {name}_gemini_2d_refiner_v1.txt
├── refined/
│   ├── {name}_refined_concept_v1.txt
│   └── {name}_refined_tpose_front_v1.txt
├── common/
│   ├── {name}_2d_refinement_criteria_v1.txt
│   └── {name}_design_notes_v1.txt
├── images/
│   ├── {name}_tpose_front_v1.png
│   ├── {name}_tpose_side_v1.png
│   └── {name}_tpose_back_v1.png
└── hunyuan3d/
    ├── model.obj
    ├── material.mtl
    ├── texture.png
    ├── preview.png
    └── metadata.json
```

---

## Testing

### Test Files

| File | Coverage |
|------|----------|
| `test_stage5_hunyuan3d.py` | Stage 5 orchestration |
| `test_hunyuan3d_provider.py` | Provider implementations |
| `test_consistent_views.py` | Multi-view consistency |
| `conftest.py` | Fixtures and mocks |

### Test Fixtures

- `sample_obj_bytes()` - Synthetic OBJ file
- `sample_mtl_bytes()` - Synthetic MTL file
- `sample_zip_bytes()` - ZIP with model files
- `mock_env_vars` - Environment setup
- `mock_submit_response()` - API response mocks

---

## Usage Examples

### Generate All Stages

```bash
uv run generate_prompts.py all -i configs/aethel.yaml
```

### Generate Static Prompts Only

```bash
uv run generate_prompts.py prompts -i configs/aethel.yaml
```

### Refine with GPT-5 and Web Search

```bash
uv run generate_prompts.py refine -i configs/aethel.yaml --web-search
```

### Generate Images Only

```bash
uv run generate_prompts.py images -i configs/aethel.yaml
```

### Generate 3D Model

```bash
uv run generate_prompts.py hunyuan3d -i configs/aethel.yaml
```

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [README.md](../README.md) | Main documentation and quick start |
| [CONSISTENT_VIEWS.md](CONSISTENT_VIEWS.md) | Multi-view generation strategy |
| [QUICK_START_CONSISTENT_VIEWS.md](QUICK_START_CONSISTENT_VIEWS.md) | Quick start for consistent views |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | Technical implementation details |
| [CHANGES_CONSISTENT_VIEWS.md](CHANGES_CONSISTENT_VIEWS.md) | Changelog for consistency feature |

---

## Summary

This codebase implements a **production-ready, extensible system** for automated game character generation with:

- **Clean Architecture**: Single responsibility modules, provider abstraction
- **Type Safety**: Dataclass-first design with comprehensive type hints
- **Extensibility**: Pluggable providers, factory pattern
- **Documentation**: Extensive inline comments (designed for learning)
- **Error Handling**: Custom exceptions, detailed error messages
- **Testing**: pytest suite with fixtures and mocks

---

*Generated: 2025-12-14*
