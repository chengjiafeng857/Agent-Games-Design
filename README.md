# Agent Games Design

A comprehensive AI-powered game design system featuring a **5-stage character creation pipeline** (text → 2D images → PBR-ready 3D models) and a **LangGraph-based ReAct agent** for game design workflows.

## Key Capabilities

- **Complete 2D→3D Pipeline**: From character specs to game-ready 3D models with PBR materials
- **Hunyuan 3D Integration**: Tencent's AI 3D generation with multiple output modes
- **Consistent Multi-View Generation**: Google Gemini generates matching front/side/back views
- **LLM Prompt Refinement**: GPT-5/GPT-4 with web search for current AI art trends
- **ReAct Agent System**: LangGraph-powered reasoning and acting for game design
- **GDD Parsing**: AI-powered conversion of text documents to structured configs
- **Human-in-the-Loop**: Interactive approval workflows
- **LangSmith Evaluation**: Comprehensive performance analysis

## Project Structure

```
agent-games-design/
├── prompt_generation/          # 5-stage character creation pipeline
│   ├── configs/                # Character YAML specifications
│   ├── src/
│   │   ├── stage1_base_prompts.py    # Template-based 2D prompts
│   │   ├── stage2_llm_refiner.py     # GPT refinement with web search
│   │   ├── stage2_gemini_prompts.py  # Manual Gemini meta-prompts
│   │   ├── stage3_common_prompts.py  # Checklist & design notes
│   │   ├── stage4_image_generation.py # Gemini T-pose images
│   │   ├── stage5_hunyuan3d.py       # 3D model generation
│   │   ├── providers/                 # Hunyuan3D API providers
│   │   │   ├── hunyuan3d_provider.py  # Abstract base class
│   │   │   ├── raw_http_hunyuan3d.py  # HTTP (no SDK required)
│   │   │   └── sdk_hunyuan3d.py       # Official SDK wrapper
│   │   └── models.py                  # CharacterSpec dataclass
│   ├── output/                 # Generated prompts, images, 3D models
│   └── generate_prompts.py     # Pipeline CLI entry point
├── src/agent_games_design/     # ReAct game design agent
│   ├── agents/                 # Agent node definitions
│   │   ├── planning.py         # Execution plan generation
│   │   └── react_executor.py   # Reasoning + Acting cycles
│   ├── graphs/                 # LangGraph workflows
│   ├── tools/                  # Game analyzer, text analyzer, calculator
│   ├── evaluation/             # LangSmith metrics
│   ├── config_generator.py     # GDD → YAML conversion
│   └── cli.py                  # Main CLI
├── tests/
├── examples/
└── docs/
```

## Quick Start

### Prerequisites

- Python 3.11+
- `uv` package manager ([install](https://github.com/astral-sh/uv))

### Installation

```bash
git clone <repo-url>
cd agent-games-design
uv sync --extra dev
cp .env.example .env  # Add your API keys
```

### Environment Variables

```bash
# Required for prompt generation pipeline
OPENAI_API_KEY=          # Stage 2: LLM refinement
GEMINI_API_KEY=          # Stage 4: Image generation
TENCENT_SECRET_ID=       # Stage 5: Hunyuan 3D
TENCENT_SECRET_KEY=      # Stage 5: Hunyuan 3D

# Optional: Hunyuan 3D configuration
HUNYUAN3D_ENABLE_PBR=true           # Enable PBR materials
HUNYUAN3D_FACE_COUNT=500000         # Polygon count (40000-1500000)
HUNYUAN3D_GENERATE_TYPE=Normal      # Normal|LowPoly|Geometry|Sketch
HUNYUAN3D_POLYGON_TYPE=triangle     # triangle|quadrilateral

# Optional: LangSmith evaluation
LANGSMITH_API_KEY=
LANGSMITH_TRACING=true
```

## Character Creation Pipeline

The 5-stage pipeline transforms character specifications into game-ready 3D assets:

### Stage 1: Base Prompts
Template-based 2D prompts from YAML character specs.

### Stage 2: LLM Refinement
GPT-powered prompt refinement with optional web search for current AI art trends.

### Stage 3: Checklist & Notes
Human-readable validation documents for T-pose requirements.

### Stage 4: Image Generation
Google Gemini generates consistent multi-view T-pose images (front, side, back). Front view is generated first, then used as reference for side/back to ensure character consistency.

### Stage 5: 3D Model Generation (Hunyuan 3D)
Converts 2D images to 3D models with PBR materials.

**PBR Output Features:**
- Physically accurate materials (albedo, normal, roughness, metallic maps)
- Multiple generation modes: Normal, LowPoly, Geometry, Sketch
- Configurable polygon counts (40K - 1.5M faces)
- Multi-view input support for better reconstruction
- Output formats: OBJ, GLB, MTL + textures

### Pipeline CLI Commands

```bash
# Full pipeline (recommended)
cd prompt_generation
uv run generate_prompts.py all -i configs/my_character.yaml

# Individual stages
uv run generate_prompts.py prompts -i configs/my_character.yaml    # Stage 1-3
uv run generate_prompts.py refine -i configs/my_character.yaml --web-search  # Stage 2b
uv run generate_prompts.py images -i configs/my_character.yaml     # Stage 4

# Stage 5: Hunyuan 3D generation
uv run generate_prompts.py hunyuan3d -i configs/my_character.yaml  # From spec
uv run generate_prompts.py hunyuan3d --image output/images/front.png  # From image
uv run generate_prompts.py hunyuan3d --prompt "A robot character"  # From text

# Multi-view for better 3D quality
uv run generate_prompts.py hunyuan3d --image front.png \
    --left-view left.png --right-view right.png --back-view back.png
```

### Character Specification Format

```yaml
# configs/my_character.yaml
name: "Zylos"
role: "Cybernetic Ninja"
game_style: "Dark sci-fi with neon accents"
silhouette: "Athletic build with angular cyber-armor plating"
color_palette:
  - "Matte black (primary)"
  - "Electric blue (accents)"
  - "Chrome silver (joints)"
key_props:
  - "Plasma katana sheathed on back"
  - "Holographic visor covering eyes"
animation_focus:
  - "swift slashing attacks"
  - "wall-running"
  - "stealth crouch"
extra_notes: "Minimalist design, exposed mechanical joints at elbows and knees"
```

### Pipeline Output Structure

```
output/
├── 2024-12-15_10-30-45/
│   ├── base/                    # Stage 1 prompts
│   ├── refined/                 # Stage 2 LLM-refined prompts
│   ├── gemini/                  # Stage 2a meta-prompts
│   ├── common/                  # Stage 3 checklist
│   └── images/                  # Stage 4 T-pose images
│       ├── zylos_tpose_front_v1.jpg
│       ├── zylos_tpose_side_v1.jpg
│       └── zylos_tpose_back_v1.jpg
└── hunyuan3d/
    └── 2024-12-15_11-00-00/
        ├── model.obj            # 3D geometry
        ├── material.mtl         # Material definitions
        ├── texture_albedo.png   # PBR textures
        ├── texture_normal.png
        ├── preview.glb          # Preview model
        └── metadata.json        # Job info
```

## ReAct Game Design Agent

The main agent system provides AI-powered game design workflows.

### Workflow Stages

1. **Planning**: AI creates detailed execution plans with steps, dependencies, and asset requests
2. **Human Approval**: Interactive plan review and approval
3. **ReAct Execution**: Reasoning through game design with Thought→Action→Observation cycles
4. **Asset Generation**: AI-generated game assets
5. **Evaluation**: LangSmith performance analysis

### Agent CLI Commands

```bash
# Interactive chat
uv run agent-games chat

# ReAct workflow
uv run agent-games react "Design a retro platformer" --interactive
uv run agent-games react --file my_game_idea.txt --evaluate

# Convert GDD to character config
uv run agent-games generate-config my_gdd.txt -o configs/output.yaml

# Run examples
uv run agent-games examples basic
uv run agent-games examples react
```

### GDD to Config Workflow

Convert unstructured game design documents to structured YAML:

```bash
# Input: my_character.txt
# "A grizzled space marine named Marcus with heavy power armor..."

uv run agent-games generate-config my_character.txt -o configs/marcus.yaml

# Output: Structured YAML ready for prompt pipeline
```

## Supported Models & Providers

### LLM Models
- **OpenAI**: GPT-5.2, GPT-5-mini, GPT-5-nano, GPT-4.1 (via Responses API)
- **Anthropic**: Claude models (via LangChain)

### Image Generation
- **Google Gemini**: gemini-3-pro-image-preview (primary), gemini-2.5-flash-image
- **FAL AI**: Integration available

### 3D Modeling
- **Hunyuan 3D** (Tencent Cloud):
  - Normal: Textured geometry (default)
  - LowPoly: Game-optimized reduced faces
  - Geometry: White model for sculpting
  - Sketch: Generate from line art
  - PBR materials with physically accurate properties

## Development

```bash
# Run tests
uv run pytest

# Code quality
uv run black src/ prompt_generation/
uv run ruff check src/ prompt_generation/
uv run mypy src/

# Add dependencies
uv add package-name
uv add --dev dev-package-name
```

## Documentation

- [Configuration Guide](docs/CONFIGURATION.md)
- [Asset Generation](docs/ASSET_GENERATION.md)
- [GPT-5 Responses API](docs/GPT5_RESPONSES_API.md)
- [Consistent Multi-View Generation](prompt_generation/docs/CONSISTENT_VIEWS.md)

### External Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Hunyuan 3D API](https://cloud.tencent.com/document/product/1729)
- [Google Gemini](https://ai.google.dev/)

## License

MIT License
