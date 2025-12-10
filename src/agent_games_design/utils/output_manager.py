"""Output manager for workflow results and assets."""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import urllib.request
import urllib.error

from ..state import ReActState

logger = logging.getLogger(__name__)


class OutputManager:
    """Manages output files and asset downloads for workflow results."""
    
    def __init__(self, base_output_dir: str = "output"):
        """Initialize the output manager.
        
        Args:
            base_output_dir: Base directory for all outputs
        """
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(exist_ok=True, parents=True)
    
    def create_run_folder(self, user_prompt: str, timestamp: Optional[datetime] = None) -> Path:
        """Create a new folder for this workflow run.
        
        Args:
            user_prompt: User's original prompt
            timestamp: Timestamp for the run (defaults to now)
            
        Returns:
            Path to the created folder
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Create folder name from timestamp and prompt
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        
        # Clean prompt for folder name (keep alphanumeric, spaces, hyphens)
        clean_prompt = "".join(
            c for c in user_prompt[:50] 
            if c.isalnum() or c in (' ', '-', '_')
        ).strip()
        clean_prompt = clean_prompt.replace(' ', '_')
        
        folder_name = f"{timestamp_str}_{clean_prompt}"
        folder_path = self.base_output_dir / folder_name
        
        # Create the folder and assets subfolder
        folder_path.mkdir(exist_ok=True, parents=True)
        (folder_path / "assets").mkdir(exist_ok=True, parents=True)
        
        logger.info(f"Created output folder: {folder_path}")
        
        return folder_path
    
    def download_asset(
        self, 
        image_url: str, 
        asset_title: str, 
        output_folder: Path,
        asset_index: int
    ) -> Optional[Path]:
        """Download an asset from a URL to the output folder.
        
        Args:
            image_url: URL of the image to download
            asset_title: Title of the asset (for filename)
            output_folder: Folder to save to
            asset_index: Index of the asset (for unique naming)
            
        Returns:
            Path to the downloaded file, or None if failed
        """
        try:
            # Create safe filename from title
            safe_title = "".join(
                c for c in asset_title 
                if c.isalnum() or c in (' ', '-', '_')
            ).strip()
            safe_title = safe_title.replace(' ', '_')[:50]
            
            # Determine file extension from URL
            extension = ".png"  # Default to PNG
            if "." in image_url.split("?")[0]:
                url_ext = image_url.split("?")[0].split(".")[-1].lower()
                if url_ext in ["jpg", "jpeg", "png", "gif", "webp"]:
                    extension = f".{url_ext}"
            
            # Create filename with index for uniqueness
            filename = f"{asset_index:02d}_{safe_title}{extension}"
            filepath = output_folder / "assets" / filename
            
            # Download the image
            logger.info(f"Downloading asset: {asset_title}")
            logger.debug(f"  From: {image_url}")
            logger.debug(f"  To: {filepath}")
            
            # Set User-Agent to avoid 403 errors
            req = urllib.request.Request(
                image_url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                with open(filepath, 'wb') as f:
                    f.write(response.read())
            
            logger.info(f"✅ Downloaded: {filename}")
            return filepath
            
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP error downloading {asset_title}: {e.code} {e.reason}")
            return None
        except urllib.error.URLError as e:
            logger.error(f"URL error downloading {asset_title}: {e.reason}")
            return None
        except Exception as e:
            logger.error(f"Failed to download {asset_title}: {e}")
            return None
    
    def save_workflow_output(
        self, 
        state: ReActState, 
        output_folder: Optional[Path] = None
    ) -> Dict[str, Path]:
        """Save complete workflow output including markdown and assets.
        
        Args:
            state: Workflow state with results
            output_folder: Folder to save to (creates new if None)
            
        Returns:
            Dictionary with paths to saved files
        """
        # Create output folder if not provided
        if output_folder is None:
            output_folder = self.create_run_folder(state.user_prompt)
        
        saved_files = {
            "folder": output_folder,
            "markdown": None,
            "assets": []
        }
        
        # Download all assets with image URLs
        asset_paths = {}
        if state.generated_assets:
            logger.info(f"📥 Downloading {len(state.generated_assets)} assets...")
            
            for i, asset in enumerate(state.generated_assets, 1):
                if asset.image_url:
                    local_path = self.download_asset(
                        asset.image_url,
                        asset.title,
                        output_folder,
                        i
                    )
                    if local_path:
                        asset_paths[asset.asset_id] = local_path
                        saved_files["assets"].append(local_path)
        
        # Generate and save markdown
        markdown_content = self._generate_markdown(state, asset_paths, output_folder)
        markdown_path = output_folder / "README.md"
        
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        saved_files["markdown"] = markdown_path
        
        logger.info(f"💾 Saved workflow output to: {output_folder}")
        logger.info(f"   📄 Markdown: {markdown_path.name}")
        logger.info(f"   🖼️  Assets: {len(saved_files['assets'])} files")
        
        return saved_files
    
    def _generate_markdown(
        self, 
        state: ReActState, 
        asset_paths: Dict[str, Path],
        output_folder: Path
    ) -> str:
        """Generate markdown content with local asset references.
        
        Args:
            state: Workflow state
            asset_paths: Mapping of asset_id to local file path
            output_folder: Output folder (for relative paths)
            
        Returns:
            Markdown content as string
        """
        lines = []
        
        # Header
        lines.append(f"# Game Design Document")
        lines.append(f"")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Session ID:** {state.session_id}")
        lines.append(f"**Status:** {state.current_stage.value}")
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")
        
        # User Request
        lines.append(f"## 📝 User Request")
        lines.append(f"")
        lines.append(f"{state.user_prompt}")
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")
        
        # Execution Plan
        if state.execution_plan:
            lines.append(f"## 📋 Execution Plan")
            lines.append(f"")
            lines.append(f"**Total Steps:** {len(state.execution_plan)}")
            lines.append(f"**Plan Approved:** {'✅ Yes' if state.plan_approved else '❌ No'}")
            lines.append(f"")
            
            for i, step in enumerate(state.execution_plan, 1):
                lines.append(f"### {i}. {step.title}")
                lines.append(f"")
                if step.description:
                    lines.append(f"**Description:** {step.description}")
                    lines.append(f"")
                if step.expected_output:
                    lines.append(f"**Expected Output:** {step.expected_output}")
                    lines.append(f"")
                if step.estimated_time:
                    lines.append(f"**Estimated Time:** {step.estimated_time}")
                    lines.append(f"")
                if step.dependencies:
                    lines.append(f"**Dependencies:** {', '.join(step.dependencies)}")
                    lines.append(f"")
            
            lines.append(f"---")
            lines.append(f"")
        
        # Guidelines (the main content)
        if state.guidelines_generated:
            lines.append(f"## 📖 Comprehensive Guidelines")
            lines.append(f"")
            lines.append(state.guidelines_generated)
            lines.append(f"")
            lines.append(f"---")
            lines.append(f"")
        
        # Asset Requests
        if state.asset_requests:
            lines.append(f"## 🎨 Asset Requests")
            lines.append(f"")
            lines.append(f"**Total Assets:** {len(state.asset_requests)}")
            lines.append(f"")
            
            for i, asset in enumerate(state.asset_requests, 1):
                lines.append(f"### {i}. {asset.title}")
                lines.append(f"")
                lines.append(f"**Type:** {asset.asset_type.value}")
                lines.append(f"")
                if asset.description:
                    lines.append(f"**Description:** {asset.description}")
                    lines.append(f"")
                if asset.style_requirements:
                    lines.append(f"**Style Requirements:**")
                    for req in asset.style_requirements:
                        lines.append(f"- {req}")
                    lines.append(f"")
                if asset.technical_specs:
                    lines.append(f"**Technical Specifications:**")
                    for key, value in asset.technical_specs.items():
                        lines.append(f"- **{key}:** {value}")
                    lines.append(f"")
            
            lines.append(f"---")
            lines.append(f"")
        
        # Generated Assets with local images
        if state.generated_assets:
            lines.append(f"## 🖼️ Generated Assets")
            lines.append(f"")
            successful = len([a for a in state.generated_assets if a.image_url])
            downloaded = len(asset_paths)
            lines.append(f"**Total Generated:** {len(state.generated_assets)}")
            lines.append(f"**Successful:** {successful}/{len(state.generated_assets)}")
            lines.append(f"**Downloaded:** {downloaded}/{successful}")
            lines.append(f"")
            
            for i, asset in enumerate(state.generated_assets, 1):
                lines.append(f"### {i}. {asset.title}")
                lines.append(f"")
                lines.append(f"**Type:** {asset.asset_type.value}")
                lines.append(f"**Model Used:** {asset.model_used.value}")
                lines.append(f"")
                
                # Check if we have a local file
                local_path = asset_paths.get(asset.asset_id)
                
                if local_path:
                    # Use relative path from markdown file to asset
                    relative_path = local_path.relative_to(output_folder)
                    lines.append(f"**Status:** ✅ Successfully Generated & Downloaded")
                    lines.append(f"")
                    lines.append(f"**Local File:** `{relative_path}`")
                    lines.append(f"")
                    lines.append(f"![{asset.title}]({relative_path})")
                    lines.append(f"")
                    
                    # Also include original URL for reference
                    if asset.image_url:
                        lines.append(f"**Original URL:** [View Online]({asset.image_url})")
                        lines.append(f"")
                
                elif asset.image_url:
                    lines.append(f"**Status:** ✅ Generated (Download Failed)")
                    lines.append(f"")
                    lines.append(f"**Image URL:** [{asset.image_url}]({asset.image_url})")
                    lines.append(f"")
                    lines.append(f"![{asset.title}]({asset.image_url})")
                    lines.append(f"")
                
                else:
                    lines.append(f"**Status:** ❌ Generation Failed")
                    lines.append(f"")
                
                if asset.generated_prompt:
                    lines.append(f"**Generated Prompt:**")
                    lines.append(f"")
                    lines.append(f"```")
                    lines.append(asset.generated_prompt)
                    lines.append(f"```")
                    lines.append(f"")
                
                if asset.quality_score is not None:
                    lines.append(f"**Quality Score:** {asset.quality_score:.2f}/1.0")
                    lines.append(f"")
                
                if asset.metadata:
                    error = asset.metadata.get("error")
                    if error:
                        lines.append(f"**Error:** {error}")
                        lines.append(f"")
            
            lines.append(f"---")
            lines.append(f"")
        
        # Metadata
        lines.append(f"## 📊 Workflow Metadata")
        lines.append(f"")
        lines.append(f"- **Total Steps Executed:** {state.total_steps}")
        lines.append(f"- **Guidelines Generated:** {'✅ Yes' if state.guidelines_generated else '❌ No'}")
        lines.append(f"- **Assets Requested:** {len(state.asset_requests)}")
        lines.append(f"- **Assets Generated:** {len(state.generated_assets)}")
        lines.append(f"- **Assets Downloaded:** {len(asset_paths)}")
        lines.append(f"- **Workflow Stage:** {state.current_stage.value}")
        
        if state.errors:
            lines.append(f"- **Errors:** {len(state.errors)}")
            lines.append(f"")
            lines.append(f"### ⚠️ Errors Encountered")
            lines.append(f"")
            for error in state.errors:
                lines.append(f"- {error}")
        else:
            lines.append(f"- **Errors:** None ✅")
        
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")
        lines.append(f"*Generated by Agent Games Design - ReAct Workflow*")
        
        return "\n".join(lines)

