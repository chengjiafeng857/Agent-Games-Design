# Asset Generation System

This document explains how the asset generation system works in the Agent Games Design workflow.

## Overview

The asset generation system automatically creates game design assets using AI models, primarily **DALL-E 3**, based on requests generated during the planning phase.

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
   - Contains image URL, prompt, metadata, and quality score

4. **Workflow Integration**
   - `asset_generation_node` in `react_workflow.py`
   - Automatically triggered after ReAct execution
   - Results saved to markdown files

## Supported Models

| Model | Status | Use Case | API |
|-------|--------|----------|-----|
| **DALL-E 3** | ✅ **Fully Integrated** | High-quality photorealistic images | OpenAI |
| Google Nano | 🔄 Prompt Only | Fast generation, iteration | Google Imagen |
| Midjourney | 🔄 Prompt Only | Artistic, stylized images | Discord API |
| Stable Diffusion | 🔄 Prompt Only | Customizable, open-source | Various |
| Adobe Firefly | 🔄 Prompt Only | Commercial-safe content | Adobe |

> **Note**: Currently, only DALL-E 3 generates actual images. Other models generate optimized prompts for manual use.

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
    "target_model": "dalle_3"
}
```

### 2. Asset Generation Phase

After ReAct execution and guideline generation, the workflow enters the asset generation phase:

```python
# In react_workflow.py
asset_generator = AssetGenerator()
generated_assets = asset_generator.generate_assets(state.asset_requests)
```

### 3. DALL-E 3 Generation

For each asset request targeting DALL-E 3:

1. **Prompt Optimization**: Creates a detailed, optimized prompt
   ```
   Create a detailed character concept art: A brave knight with 
   shining armor, wielding a magical sword. Style: pixel art, 
   8-bit style, vibrant colors. Visual style: retro. 
   High quality, professional game design asset
   ```

2. **API Call**: Sends request to OpenAI
   ```python
   response = client.images.generate(
       model="dall-e-3",
       prompt=optimized_prompt,
       size="1024x1024",
       quality="standard",
       style="vivid",
       n=1
   )
   ```

3. **Result Processing**: Extracts image URL and metadata
   ```python
   GameDesignAsset(
       asset_id="char_001",
       asset_type="character_concept",
       title="Main Character Hero",
       generated_prompt="...",  # DALL-E 3 revised prompt
       model_used="dalle_3",
       image_url="https://...",
       quality_score=0.85
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
# Required
OPENAI_API_KEY=sk-...

# Optional (defaults)
DALLE3_SIZE=1024x1024          # 1024x1024, 1024x1792, 1792x1024
DALLE3_QUALITY=standard        # standard or hd
DALLE3_STYLE=vivid             # vivid or natural
MAX_RETRIES=3                  # Maximum retry attempts
```

### Programmatic Configuration

```python
from agent_games_design.agents import AssetGenerator, AssetGenerationConfig

config = AssetGenerationConfig(
    dalle3_size="1024x1792",
    dalle3_quality="hd",
    dalle3_style="natural",
    max_retries=5
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

## DALL-E 3 Size Mapping

The system automatically maps technical specs to DALL-E 3 sizes:

| Request | DALL-E 3 Size |
|---------|---------------|
| `resolution: "1024x1024"` | `1024x1024` (square) |
| `resolution: "portrait"` | `1024x1792` (portrait) |
| `resolution: "1792x1024"` | `1792x1024` (landscape) |
| `resolution: "landscape"` | `1792x1024` (landscape) |

## DALL-E 3 Style Selection

The system analyzes style requirements to choose between `vivid` and `natural`:

**Natural Style** (subtle, realistic):
- Keywords: "realistic", "photographic", "subtle", "natural", "muted"
- Best for: Realistic scenes, subtle artwork

**Vivid Style** (artistic, vibrant):
- Default choice
- Best for: Stylized art, vibrant colors, game assets

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
  ✅ Main Character Hero (dalle_3)
     URL: https://oaidalleapiprodscus.blob.core.windows.net/...
  ✅ Enemy Character (dalle_3)
     URL: https://oaidalleapiprodscus.blob.core.windows.net/...
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
**Model Used:** dalle_3
**Status:** ✅ Successfully Generated

**Image URL:** [https://...]

![Main Character Hero](https://...)

**Generated Prompt:**
```
A brave knight with shining armor...
```

**Quality Score:** 0.85/1.0
```

## API Usage and Costs

### DALL-E 3 Pricing (as of 2025)

| Size | Quality | Cost per Image |
|------|---------|----------------|
| 1024x1024 | Standard | ~$0.040 |
| 1024x1024 | HD | ~$0.080 |
| 1024x1792 | Standard | ~$0.080 |
| 1024x1792 | HD | ~$0.120 |

**Example**: Generating 14 standard quality 1024x1024 images costs approximately **$0.56**.

### Rate Limits

DALL-E 3 rate limits (varies by tier):
- **Free Tier**: Not supported
- **Tier 1**: 5 RPM (requests per minute)
- **Tier 2**: 7 RPM
- **Tier 3+**: Higher limits

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
    technical_specs={"resolution": "1024x1792"},
    target_model=ModelType.DALLE_3
)

assets = generator.generate_assets([custom_request])
```

### Quality Scores

Generated assets include quality scores:

- **DALL-E 3**: `0.85` (consistently high quality)
- **Failed**: `0.0` (generation failed)
- **Prompt Only**: `None` (no image generated)

### Metadata

Each asset includes metadata:

```python
asset.metadata = {
    "original_prompt": "...",      # User's original request
    "size": "1024x1024",            # Image dimensions
    "quality": "standard",          # Quality setting
    "style": "vivid",               # Style setting
    "timestamp": "2025-10-21T...",  # Generation time
    "attempt": 1                    # Attempt number
}
```

## Troubleshooting

### No Assets Generated

**Problem**: `generated_assets` is empty

**Solutions**:
1. Check that `asset_requests` are created during planning
2. Verify `OPENAI_API_KEY` is set correctly
3. Check console for error messages
4. Review `.env` file configuration

### DALL-E 3 API Errors

**Problem**: 400/500 errors from OpenAI

**Solutions**:
1. **Content Policy Violation**: Adjust asset description
2. **Rate Limit**: Wait and retry, or upgrade tier
3. **Invalid Size**: Use supported sizes (1024x1024, 1024x1792, 1792x1024)
4. **Prompt Too Long**: Descriptions are auto-truncated to 3900 chars

### Low Quality Results

**Solutions**:
1. Provide more detailed descriptions
2. Include specific style requirements
3. Add reference image descriptions
4. Use HD quality: `dalle3_quality="hd"`

### Cost Concerns

**Solutions**:
1. Limit number of assets in planning
2. Use "standard" quality instead of "hd"
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

## Future Enhancements

Planned improvements:

- [ ] **Multi-model support**: Direct integration with Midjourney, Stable Diffusion
- [ ] **Batch optimization**: Parallel generation for faster completion
- [ ] **Style transfer**: Apply consistent style across all assets
- [ ] **Asset variations**: Generate multiple variations per request
- [ ] **Local storage**: Download and save images locally
- [ ] **Asset library**: Build a reusable asset collection
- [ ] **Custom models**: Support for fine-tuned models

## References

- [DALL-E 3 API Documentation](https://platform.openai.com/docs/guides/images)
- [OpenAI Pricing](https://openai.com/pricing)
- [Image Generation Best Practices](https://platform.openai.com/docs/guides/images/usage)

---

**Last Updated**: October 21, 2025

