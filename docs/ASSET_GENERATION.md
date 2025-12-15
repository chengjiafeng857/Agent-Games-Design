# Asset Generation System

This document explains how the asset generation system works in the Agent Games Design workflow.

## Overview

The asset generation system automatically creates game design assets using AI models, primarily **Google Gemini 3 Pro Preview**, based on requests generated during the planning phase.

## Architecture

### Components

1. **AssetGenerator** (`src/agent_games_design/agents/asset_generator.py`)
   - Main class for generating assets
   - Supports multiple AI models
   - Handles retries and error recovery
   - Optimizes prompts for each model

2. **AssetRequest** (State Model)
   - Defines what asset needs to be generated
   - Includes specifications, style requirements, and technical details

3. **GameDesignAsset** (State Model)
   - Represents a generated asset
   - Contains image path/URL, prompt, metadata, and quality score

4. **Workflow Integration**
   - `asset_generation_node` in `react_workflow.py`
   - Automatically triggered after ReAct execution
   - Results saved to markdown files

## Supported Models

| Model | Status | Use Case | API |
|-------|--------|----------|-----|
| **Gemini 3 Pro** | ✅ **Fully Integrated** | High-quality image generation | Google Generative AI |
| DALL-E 3 | 🔄 Legacy (routed to Gemini) | Backward compatibility | - |
| Google Nano | 🔄 Legacy (routed to Gemini) | Backward compatibility | - |
| Midjourney | 🔄 Prompt Only | Artistic, stylized images | Discord API |
| Stable Diffusion | 🔄 Prompt Only | Customizable, open-source | Various |
| Adobe Firefly | 🔄 Prompt Only | Commercial-safe content | Adobe |

> **Note**: Gemini 3 Pro Preview (`gemini-3-pro-image-preview`) is the primary model for actual image generation. Legacy `dalle_3` and `google_nano` requests are automatically routed to Gemini.

## How It Works

### 1. Planning Phase

The `PlanningAgent` analyzes the user's request and creates `AssetRequest` objects:

```python
{
    "asset_id": "char_001",
    "asset_type": "character_concept",
    "title": "Main Character Hero",
    "description": "A brave knight with shining armor...",
    "style_requirements": ["pixel art", "8-bit style", "vibrant colors"],
    "technical_specs": {
        "resolution": "1024x1024",
        "format": "PNG",
        "style": "retro"
    },
    "target_model": "gemini_3_pro"
}
```

### 2. Asset Generation Phase

After ReAct execution and guideline generation, the workflow enters the asset generation phase:

```python
# In react_workflow.py
asset_generator = AssetGenerator()
generated_assets = asset_generator.generate_assets(state.asset_requests)
```

### 3. Gemini 3 Pro Generation

For each asset request targeting Gemini 3 Pro:

1. **Prompt Optimization**: Creates a detailed, optimized prompt
   ```
   Create a detailed character concept art: A brave knight with 
   shining armor, wielding a magical sword. Style: pixel art, 
   8-bit style, vibrant colors. Visual style: retro. 
   High quality, professional game design asset
   ```

2. **API Call**: Sends request to Google Generative AI
   ```python
   from google import genai
   from google.genai import types
   
   client = genai.Client(api_key=api_key)
   
   config = types.GenerateContentConfig(
       response_modalities=['IMAGE'],
       image_config=types.ImageConfig(
           aspect_ratio="1:1",
           image_size="2K",
       ),
   )
   
   response = client.models.generate_content(
       model="gemini-3-pro-image-preview",
       contents=[optimized_prompt],
       config=config,
   )
   ```

3. **Result Processing**: Saves image to disk and creates asset record
   ```python
   GameDesignAsset(
       asset_id="char_001",
       asset_type="character_concept",
       title="Main Character Hero",
       generated_prompt="...",
       model_used="gemini_3_pro",
       image_url="output/assets/main_character_hero_20251215_120000.jpg",
       quality_score=0.90
   )
   ```

### 4. Error Handling

The system includes robust error handling:

- **Retries**: Up to 3 attempts per asset
- **Partial Success**: Continues even if some assets fail
- **Error Tracking**: Failed assets are logged with error details
- **Graceful Degradation**: Workflow continues to completion

## Configuration

### Environment Variables

```bash
# Required for planning
OPENAI_API_KEY=sk-...

# Required for image generation
GEMINI_API_KEY=your-gemini-api-key

# Optional (defaults)
GEMINI_ASPECT_RATIO=1:1         # 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9
GEMINI_IMAGE_SIZE=2K            # 1K, 2K, 4K
MAX_RETRIES=3                   # Maximum retry attempts
```

### Programmatic Configuration

```python
from agent_games_design.agents import AssetGenerator, AssetGenerationConfig

config = AssetGenerationConfig(
    gemini_aspect_ratio="16:9",
    gemini_image_size="4K",
    max_retries=5,
    output_dir="output/game_assets"
)

generator = AssetGenerator(config=config)
```

## Asset Types

The system supports various asset types:

- `character_concept`: Character designs and concept art
- `environment_art`: Backgrounds, scenes, locations
- `ui_mockup`: User interface designs
- `game_logo`: Game titles and logos
- `icon_set`: UI icons and symbols
- `texture`: Surface textures and materials
- `sprite`: Game sprites and animations
- `background`: Background images
- `promotional_art`: Marketing and promotional images

## Gemini Aspect Ratio Mapping

The system automatically maps technical specs to Gemini aspect ratios:

| Request | Gemini Aspect Ratio |
|---------|---------------------|
| `resolution: "1024x1024"` or default | `1:1` (square) |
| `resolution: "portrait"` | `2:3` (portrait) |
| `resolution: "landscape"` | `3:2` (landscape) |
| `resolution: "wide"` or `16:9` | `16:9` (widescreen) |
| `resolution: "vertical"` or `9:16` | `9:16` (mobile) |
| `resolution: "banner"` or `21:9` | `21:9` (ultrawide) |

## Image Size Options

Gemini 3 Pro supports three resolution tiers:

| Size | Resolution | Best For |
|------|------------|----------|
| `1K` | 1024px | Quick iterations, previews |
| `2K` | 2048px | Standard quality assets (default) |
| `4K` | 4096px | High-resolution final assets |

## Output

### Console Output

```
🎮 Starting ReAct Game Design Workflow...
📝 Request: Create a platformer game

✅ Workflow completed!
📍 Status: completed
✅ Plan was approved
📋 Generated 17 execution steps
🎨 Identified 14 assets to generate
🖼️  Generated 14/14 assets successfully
  ✅ Main Character Hero (gemini_3_pro)
     File: output/assets/main_character_hero_20251215_120000.jpg
  ✅ Enemy Character (gemini_3_pro)
     File: output/assets/enemy_character_20251215_120015.jpg
  ...
```

### Markdown File

Generated assets are included in the markdown export:

```markdown
## 🖼️ Generated Assets

**Total Generated:** 14
**Successful:** 14/14

### 1. Main Character Hero

**Type:** character_concept
**Model Used:** gemini_3_pro
**Status:** ✅ Successfully Generated

**Image Path:** output/assets/main_character_hero_20251215_120000.jpg

![Main Character Hero](output/assets/main_character_hero_20251215_120000.jpg)

**Generated Prompt:**
```
A brave knight with shining armor...
```

**Quality Score:** 0.90/1.0
```

## API Usage and Costs

### Gemini 3 Pro Pricing

Gemini 3 Pro image generation pricing varies by resolution and usage tier. Check the [Google AI pricing page](https://ai.google.dev/pricing) for current rates.

| Size | Typical Cost per Image |
|------|------------------------|
| 1K | Lower |
| 2K | Medium |
| 4K | Higher |

### Rate Limits

Gemini API rate limits depend on your API tier and project quota. Check your Google Cloud Console for specific limits.

## Advanced Usage

### Custom Prompts

For fine-grained control, you can customize prompts:

```python
generator = AssetGenerator()

# Override prompt for specific asset
custom_request = AssetRequest(
    asset_id="custom_001",
    asset_type=AssetType.CHARACTER_CONCEPT,
    title="Custom Hero",
    description="Your detailed description here...",
    style_requirements=["specific", "style", "tags"],
    technical_specs={"resolution": "portrait"},
    target_model=ModelType.GEMINI_3_PRO
)

assets = generator.generate_assets([custom_request])
```

### Quality Scores

Generated assets include quality scores:

- **Gemini 3 Pro**: `0.90` (consistently high quality)
- **Failed**: `0.0` (generation failed)
- **Prompt Only**: `None` (no image generated)

### Metadata

Each asset includes metadata:

```python
asset.metadata = {
    "prompt": "...",                # Optimized prompt used
    "aspect_ratio": "1:1",          # Aspect ratio
    "image_size": "2K",             # Resolution tier
    "model": "gemini-3-pro-image-preview",  # Model name
    "timestamp": "2025-12-15T...",  # Generation time
}
```

## Troubleshooting

### No Assets Generated

**Problem**: `generated_assets` is empty

**Solutions**:
1. Check that `asset_requests` are created during planning
2. Verify `GEMINI_API_KEY` is set correctly
3. Check console for error messages
4. Review `.env` file configuration

### Gemini API Errors

**Problem**: API errors from Google

**Solutions**:
1. **Content Policy Violation**: Adjust asset description
2. **Rate Limit**: Wait and retry, or check quota
3. **Invalid Configuration**: Verify aspect_ratio and image_size values
4. **Authentication**: Ensure GEMINI_API_KEY is valid

### Low Quality Results

**Solutions**:
1. Provide more detailed descriptions
2. Include specific style requirements
3. Add reference image descriptions
4. Use `4K` image size for higher resolution

### Cost Concerns

**Solutions**:
1. Limit number of assets in planning
2. Use `1K` size for iterations, `2K` for final
3. Generate prompts only for external use
4. Test with smaller asset sets first

## Examples

### Example 1: Platformer Game

**Request**: "Create a platformer game"

**Generated Assets** (sample):
- Main Character Hero (pixel art style)
- Enemy Character (pixel art style)
- Platform Tileset (retro style)
- Background Scene (vibrant colors)
- UI Elements (clean, minimal)

### Example 2: RPG Character

**Request**: "Design a fantasy RPG character"

**Generated Assets**:
- Character Portrait (detailed, painterly)
- Character Sprite Sheet (16x16 pixels)
- Weapon Concepts (magical staff)
- Character Icon (UI style)

## Migration from DALL-E 3

If you were previously using DALL-E 3, the migration is seamless:

1. **Set Gemini API Key**: Add `GEMINI_API_KEY` to your `.env` file
2. **Legacy Compatibility**: Existing `dalle_3` requests are automatically routed to Gemini
3. **Update Planning Prompts**: Use `gemini_3_pro` for new asset requests (optional)

```python
# Old (still works - routed to Gemini)
target_model=ModelType.DALLE_3

# New (recommended)
target_model=ModelType.GEMINI_3_PRO
```

## Future Enhancements

Planned improvements:

- [ ] **Multi-model support**: Direct integration with Midjourney, Stable Diffusion
- [ ] **Batch optimization**: Parallel generation for faster completion
- [ ] **Style transfer**: Apply consistent style across all assets
- [ ] **Asset variations**: Generate multiple variations per request
- [ ] **Image editing**: Edit generated images with text prompts
- [ ] **Asset library**: Build a reusable asset collection
- [ ] **Custom models**: Support for fine-tuned models

## References

- [Google AI Studio](https://ai.google.dev/)
- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [Google Generative AI Python SDK](https://github.com/google-gemini/generative-ai-python)

---

**Last Updated**: December 15, 2025
