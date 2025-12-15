"""Asset generator for game design using Gemini 3 Pro Preview and other models."""

import logging
import base64
import os
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from ..config import settings
from ..state import AssetRequest, GameDesignAsset, ModelType, AssetType

logger = logging.getLogger(__name__)


class AssetGenerationConfig(BaseModel):
    """Configuration for asset generation."""

    # Gemini 3 Pro settings
    gemini_aspect_ratio: str = Field(
        default="1:1",
        description="Aspect ratio for Gemini. Options: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9"
    )
    gemini_image_size: str = Field(
        default="2K",
        description="Image resolution for Gemini. Options: 1K, 2K, 4K"
    )
    max_retries: int = Field(default=3, description="Maximum retries on failure")
    output_dir: str = Field(default="output/assets", description="Directory to save generated images")


class AssetGenerator:
    """Generates game design assets using AI models."""

    # Gemini 3 Pro Image Preview model name
    GEMINI_MODEL = "gemini-3-pro-image-preview"

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[AssetGenerationConfig] = None,
    ):
        """Initialize the asset generator.

        Args:
            api_key: Gemini API key (defaults to settings)
            config: Asset generation configuration
        """
        self.config = config or AssetGenerationConfig()
        self.api_key = api_key or settings.gemini_api_key
        
        if not self.api_key:
            logger.warning(
                "Gemini API key not set. Set GEMINI_API_KEY environment variable "
                "or pass api_key to AssetGenerator."
            )
        
        # Ensure output directory exists (use absolute path)
        self.output_dir = Path(self.config.output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_assets(
        self, asset_requests: List[AssetRequest]
    ) -> List[GameDesignAsset]:
        """Generate all requested assets.

        Args:
            asset_requests: List of asset requests to fulfill

        Returns:
            List of generated assets
        """
        generated_assets = []

        logger.info(f"🎨 Starting asset generation for {len(asset_requests)} requests")

        for i, request in enumerate(asset_requests, 1):
            try:
                logger.info(
                    f"🖼️  Generating asset {i}/{len(asset_requests)}: {request.title}"
                )

                asset = self._generate_single_asset(request)
                generated_assets.append(asset)

                logger.info(
                    f"✅ Successfully generated: {request.title} using {asset.model_used}"
                )

            except Exception as e:
                logger.error(f"❌ Failed to generate {request.title}: {e}")
                # Create a failed asset entry
                failed_asset = GameDesignAsset(
                    asset_id=request.asset_id,
                    asset_type=request.asset_type,
                    title=request.title,
                    generated_prompt=f"Failed: {str(e)}",
                    model_used=request.target_model,
                    image_url=None,
                    metadata={"error": str(e), "timestamp": datetime.utcnow().isoformat()},
                    quality_score=0.0,
                )
                generated_assets.append(failed_asset)

        logger.info(
            f"🎉 Asset generation complete: {len([a for a in generated_assets if a.image_url])} successful, "
            f"{len([a for a in generated_assets if not a.image_url])} failed"
        )

        return generated_assets

    def _generate_single_asset(self, request: AssetRequest) -> GameDesignAsset:
        """Generate a single asset based on the request.

        Args:
            request: Asset request specification

        Returns:
            Generated asset
        """
        # Route to appropriate generator based on target model
        # Gemini 3 Pro is the primary model, also handle legacy DALLE_3 and GOOGLE_NANO
        if request.target_model in [ModelType.GEMINI_3_PRO, ModelType.DALLE_3, ModelType.GOOGLE_NANO]:
            return self._generate_with_gemini(request)
        else:
            # For other models, generate a high-quality prompt but don't actually generate
            # This allows users to use the prompts with external tools
            return self._generate_prompt_only(request)

    def _generate_with_gemini(self, request: AssetRequest) -> GameDesignAsset:
        """Generate an asset using Gemini 3 Pro Preview.

        Args:
            request: Asset request specification

        Returns:
            Generated asset with image URL
        """
        # Import google-genai here to allow the rest of the code to work without it
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise ImportError(
                "google-genai package is required for image generation.\n"
                "Install it with: pip install google-genai\n"
                "Or: uv add google-genai"
            )

        if not self.api_key:
            raise ValueError(
                "Gemini API key not set. Set GEMINI_API_KEY environment variable "
                "or pass api_key to AssetGenerator."
            )

        # Create optimized prompt for Gemini
        prompt = self._create_gemini_prompt(request)

        # Determine aspect ratio based on technical specs
        aspect_ratio = self._get_gemini_aspect_ratio(request)
        image_size = self.config.gemini_image_size

        try:
            logger.debug(f"Generating with Gemini 3 Pro: {prompt[:100]}...")
            
            # Create Gemini client
            client = genai.Client(api_key=self.api_key)
            
            # Configure image generation settings
            config = types.GenerateContentConfig(
                response_modalities=['IMAGE'],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size=image_size,
                ),
            )
            
            # Generate the image
            response = client.models.generate_content(
                model=self.GEMINI_MODEL,
                contents=[prompt],
                config=config,
            )
            
            # Extract image from response
            image_data = None
            for part in response.parts:
                if part.inline_data is not None:
                    image_data = part.inline_data.data
                    break
            
            if image_data is None:
                raise Exception("No image was generated. The API returned an empty response.")
            
            # Save image to file and get URL/path
            image_path = self._save_image(request, image_data)
            
            return GameDesignAsset(
                asset_id=request.asset_id,
                asset_type=request.asset_type,
                title=request.title,
                generated_prompt=prompt,
                model_used=ModelType.GEMINI_3_PRO,
                image_url=str(image_path),
                metadata={
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "image_size": image_size,
                    "model": self.GEMINI_MODEL,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                quality_score=0.90,  # Gemini 3 Pro produces high quality images
            )

        except Exception as e:
            logger.error(f"Gemini 3 Pro generation failed: {e}")
            raise

    def _save_image(self, request: AssetRequest, image_data: bytes) -> Path:
        """Save generated image to file.

        Args:
            request: Asset request specification
            image_data: Raw image bytes

        Returns:
            Absolute path to saved image file
        """
        # Create safe filename from title
        safe_title = "".join(c if c.isalnum() or c in "._- " else "_" for c in request.title)
        safe_title = safe_title.replace(" ", "_").lower()
        
        # Add timestamp for uniqueness
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_title}_{timestamp}.jpg"
        
        # Save to output directory (absolute path)
        file_path = (self.output_dir / filename).resolve()
        file_path.write_bytes(image_data)
        
        logger.info(f"💾 Saved image to: {file_path}")
        return file_path

    def _generate_prompt_only(self, request: AssetRequest) -> GameDesignAsset:
        """Generate a high-quality prompt for external use.

        Args:
            request: Asset request specification

        Returns:
            Asset with generated prompt (no image URL)
        """
        prompt = self._create_optimized_prompt(request)

        return GameDesignAsset(
            asset_id=request.asset_id,
            asset_type=request.asset_type,
            title=request.title,
            generated_prompt=prompt,
            model_used=request.target_model,
            image_url=None,
            metadata={
                "note": f"Use this prompt with {request.target_model.value}",
                "timestamp": datetime.utcnow().isoformat(),
            },
            quality_score=None,
        )

    def _create_gemini_prompt(self, request: AssetRequest) -> str:
        """Create an optimized prompt for Gemini 3 Pro.

        Gemini 3 Pro works best with:
        - Detailed, descriptive prompts
        - Natural language
        - Specific style instructions
        - Clear composition guidance
        """
        parts = []

        # Start with asset type context
        parts.append(f"Create {self._get_asset_type_description(request.asset_type)}:")

        # Main description
        parts.append(request.description)

        # Style requirements
        if request.style_requirements:
            style_text = ", ".join(request.style_requirements)
            parts.append(f"Style: {style_text}")

        # Technical specs that affect visual output
        tech_style = request.technical_specs.get("style", "")
        if tech_style:
            parts.append(f"Visual style: {tech_style}")

        # Reference context
        if request.reference_images:
            ref_text = "; ".join(request.reference_images)
            parts.append(f"Reference inspiration: {ref_text}")

        # Format for game design
        parts.append("High quality, professional game design asset")

        prompt = ". ".join(parts)

        # Gemini can handle long prompts, but keep it reasonable
        if len(prompt) > 4000:
            prompt = prompt[:4000] + "..."

        return prompt

    def _create_optimized_prompt(self, request: AssetRequest) -> str:
        """Create an optimized prompt for any model.

        Args:
            request: Asset request specification

        Returns:
            Formatted prompt string
        """
        sections = []

        # Header
        sections.append(f"# {request.title}")
        sections.append(f"Asset Type: {request.asset_type.value}")
        sections.append(f"Target Model: {request.target_model.value}")
        sections.append("")

        # Description
        sections.append("## Description")
        sections.append(request.description)
        sections.append("")

        # Style requirements
        if request.style_requirements:
            sections.append("## Style Requirements")
            for req in request.style_requirements:
                sections.append(f"- {req}")
            sections.append("")

        # Technical specs
        if request.technical_specs:
            sections.append("## Technical Specifications")
            for key, value in request.technical_specs.items():
                sections.append(f"- {key}: {value}")
            sections.append("")

        # References
        if request.reference_images:
            sections.append("## References")
            for ref in request.reference_images:
                sections.append(f"- {ref}")
            sections.append("")

        # Model-specific instructions
        sections.append("## Generation Instructions")
        sections.append(self._get_model_instructions(request.target_model))

        return "\n".join(sections)

    def _get_asset_type_description(self, asset_type: AssetType) -> str:
        """Get descriptive text for asset type."""
        descriptions = {
            AssetType.CHARACTER_CONCEPT: "a detailed character concept art",
            AssetType.ENVIRONMENT_ART: "an immersive environment scene",
            AssetType.UI_MOCKUP: "a clean user interface mockup",
            AssetType.GAME_LOGO: "a memorable game logo design",
            AssetType.ICON_SET: "a set of cohesive game icons",
            AssetType.TEXTURE: "a seamless texture pattern",
            AssetType.SPRITE: "a game sprite with clear silhouette",
            AssetType.BACKGROUND: "a atmospheric background image",
            AssetType.PROMOTIONAL_ART: "eye-catching promotional artwork",
        }
        return descriptions.get(asset_type, "a game design asset")

    def _get_gemini_aspect_ratio(self, request: AssetRequest) -> str:
        """Determine appropriate Gemini aspect ratio.

        Gemini supports: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9
        """
        spec_resolution = request.technical_specs.get("resolution", "1024x1024")

        # Map common resolutions/descriptions to Gemini aspect ratios
        if "portrait" in spec_resolution.lower():
            return "2:3"
        elif "landscape" in spec_resolution.lower():
            return "3:2"
        elif "wide" in spec_resolution.lower() or "16:9" in spec_resolution:
            return "16:9"
        elif "vertical" in spec_resolution.lower() or "9:16" in spec_resolution:
            return "9:16"
        elif "banner" in spec_resolution.lower() or "21:9" in spec_resolution:
            return "21:9"
        else:
            return self.config.gemini_aspect_ratio  # Default from config

    def _get_model_instructions(self, model_type: ModelType) -> str:
        """Get model-specific instructions for prompt usage."""
        instructions = {
            ModelType.GEMINI_3_PRO: "Use with Google Gemini 3 Pro Preview. High-quality image generation with excellent detail.",
            ModelType.GOOGLE_NANO: "Use with Google Gemini 3 Pro Preview. High-quality image generation.",
            ModelType.DALLE_3: "Use with OpenAI DALL-E 3 API (legacy). Best for photorealistic and detailed images.",
            ModelType.MIDJOURNEY: "Use in Midjourney Discord. Add --v 6 for latest version, --ar for aspect ratio.",
            ModelType.STABLE_DIFFUSION: "Use with Stable Diffusion. Consider using LoRA models for specific styles.",
            ModelType.FIREFLY: "Use with Adobe Firefly. Excellent for commercial-safe content generation.",
        }
        return instructions.get(
            model_type, "Follow your model's specific prompt format guidelines."
        )
