"""Asset generator for game design using DALL-E 3 and other models."""

import logging
from typing import List, Optional
from datetime import datetime

from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from pydantic import BaseModel, Field

from ..config import settings
from ..state import AssetRequest, GameDesignAsset, ModelType, AssetType

logger = logging.getLogger(__name__)


class AssetGenerationConfig(BaseModel):
    """Configuration for asset generation."""

    dalle3_size: str = Field(default="1024x1024", description="Image size for DALL-E 3")
    dalle3_quality: str = Field(default="standard", description="Quality: standard or hd")
    max_retries: int = Field(default=3, description="Maximum retries on failure")


class AssetGenerator:
    """Generates game design assets using AI models."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[AssetGenerationConfig] = None,
    ):
        """Initialize the asset generator.

        Args:
            api_key: OpenAI API key (defaults to settings)
            config: Asset generation configuration
        """
        self.config = config or AssetGenerationConfig()
        
        # Initialize DALL-E 3 wrapper with LangChain
        self.dalle_tool = DallEAPIWrapper(
            model="dall-e-3",
            api_key=api_key or settings.openai_api_key,
            size=self.config.dalle3_size,
            quality=self.config.dalle3_quality,
            n=1,
            max_retries=self.config.max_retries,
        )

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
        if request.target_model == ModelType.DALLE_3:
            return self._generate_with_dalle3(request)
        else:
            # For other models, generate a high-quality prompt but don't actually generate
            # This allows users to use the prompts with external tools
            return self._generate_prompt_only(request)

    def _generate_with_dalle3(self, request: AssetRequest) -> GameDesignAsset:
        """Generate an asset using DALL-E 3 via LangChain wrapper.

        Args:
            request: Asset request specification

        Returns:
            Generated asset with image URL
        """
        # Create optimized prompt for DALL-E 3
        prompt = self._create_dalle3_prompt(request)

        # Determine size based on technical specs
        size = self._get_dalle3_size(request)

        # Update the DALL-E wrapper's size if needed
        if size != self.dalle_tool.size:
            # Create a new wrapper with updated size
            self.dalle_tool = DallEAPIWrapper(
                model="dall-e-3",
                api_key=settings.openai_api_key,
                size=size,
                quality=self.config.dalle3_quality,
                n=1,
                max_retries=self.config.max_retries,
            )

        try:
            logger.debug(f"Generating with DALL-E 3: {prompt[:100]}...")
            
            # Use LangChain's DallEAPIWrapper to generate image
            # The run() method returns the image URL as a string
            image_url = self.dalle_tool.run(prompt)
            
            # Remove any whitespace/newlines from the URL
            image_url = image_url.strip()

            return GameDesignAsset(
                asset_id=request.asset_id,
                asset_type=request.asset_type,
                title=request.title,
                generated_prompt=prompt,
                model_used=ModelType.DALLE_3,
                image_url=image_url,
                metadata={
                    "prompt": prompt,
                    "size": size,
                    "quality": self.config.dalle3_quality,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                quality_score=0.85,  # DALL-E 3 generally produces high quality
            )

        except Exception as e:
            logger.error(f"DALL-E 3 generation failed: {e}")
            raise

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

    def _create_dalle3_prompt(self, request: AssetRequest) -> str:
        """Create an optimized prompt for DALL-E 3.

        DALL-E 3 works best with:
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

        # DALL-E 3 has a 4000 character limit
        if len(prompt) > 3900:
            prompt = prompt[:3900] + "..."

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

    def _get_dalle3_size(self, request: AssetRequest) -> str:
        """Determine appropriate DALL-E 3 size.

        DALL-E 3 supports: 1024x1024, 1024x1792, 1792x1024
        """
        spec_resolution = request.technical_specs.get("resolution", "1024x1024")

        # Map common resolutions to DALL-E 3 sizes
        if "1792" in spec_resolution or "portrait" in spec_resolution.lower():
            return "1024x1792"
        elif "landscape" in spec_resolution.lower():
            return "1792x1024"
        else:
            return "1024x1024"

    def _get_model_instructions(self, model_type: ModelType) -> str:
        """Get model-specific instructions for prompt usage."""
        instructions = {
            ModelType.DALLE_3: "Use with OpenAI DALL-E 3 API. Best for photorealistic and detailed images.",
            ModelType.GOOGLE_NANO: "Use with Google Imagen or similar. Fast generation, good for iteration.",
            ModelType.MIDJOURNEY: "Use in Midjourney Discord. Add --v 6 for latest version, --ar for aspect ratio.",
            ModelType.STABLE_DIFFUSION: "Use with Stable Diffusion. Consider using LoRA models for specific styles.",
            ModelType.FIREFLY: "Use with Adobe Firefly. Excellent for commercial-safe content generation.",
        }
        return instructions.get(
            model_type, "Follow your model's specific prompt format guidelines."
        )

