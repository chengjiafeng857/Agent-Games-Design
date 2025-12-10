"""CLI integration utilities for ReAct workflow."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from ..graphs import ReActWorkflowManager
from ..state import ReActState, WorkflowStage
from .output_manager import OutputManager

logger = logging.getLogger(__name__)


class SimpleReActCLI:
    """Simple CLI handler for ReAct workflow."""
    
    def __init__(self, output_dir: str = "output"):
        """Initialize the CLI handler.
        
        Args:
            output_dir: Base directory for output files
        """
        self.manager = ReActWorkflowManager()
        self.output_manager = OutputManager(output_dir)
    
    async def run_workflow(self, prompt: str, interactive: bool = False) -> Dict[str, Any]:
        """Run a complete ReAct workflow.
        
        Args:
            prompt: The game design prompt
            interactive: Whether to run in interactive mode
            
        Returns:
            Results dictionary
        """
        # Start workflow
        state = self.manager.start_workflow(prompt)
        
        # Execute until we hit human_approval state
        state = self.manager.execute_step(state)
        
        # Check if we're at human approval stage
        if state.current_stage == WorkflowStage.HUMAN_APPROVAL:
            # Handle human approval
            if interactive:
                # In interactive mode, wait for user input
                approval_display = self._get_approval_display(state)
                print(approval_display)
                response = input("Your response: ").strip()
                state = self.manager.approval_handler.process_human_response(state, response)
            else:
                # Auto-approve for non-interactive mode
                print("🤖 Auto-approving plan (non-interactive mode)")
                state = self.manager.approval_handler.process_human_response(state, "approve")
        
        # Continue executing workflow until completion
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        print(f"\n🔄 Continuing workflow from {state.current_stage.value}...")
        
        while (state.current_stage not in [WorkflowStage.COMPLETED, WorkflowStage.EVALUATION] 
               and iteration < max_iterations):
            # Don't re-execute if we're stuck at human approval without approval
            if state.current_stage == WorkflowStage.HUMAN_APPROVAL and not state.plan_approved:
                break
            
            previous_stage = state.current_stage
            state = self.manager.execute_step(state)
            
            # Log stage transition
            if state.current_stage != previous_stage:
                print(f"  ✓ {previous_stage.value} → {state.current_stage.value}")
            
            iteration += 1
            
            # Break if we hit an error
            if state.errors:
                print(f"⚠️ Errors encountered: {state.errors}")
                break
        
        if iteration >= max_iterations:
            print(f"⚠️ Warning: Max iterations reached. Workflow may be incomplete.")
        
        print(f"✅ Workflow completed at stage: {state.current_stage.value}\n")
        
        # Save output to organized folder structure
        saved_files = self.output_manager.save_workflow_output(state)
        
        # Also return formatted results for backward compatibility
        results = self._format_results(state)
        results["saved_files"] = {
            "folder": str(saved_files["folder"]),
            "markdown": str(saved_files["markdown"]),
            "assets": [str(p) for p in saved_files["assets"]]
        }
        
        return results
    
    def _get_approval_display(self, state: ReActState) -> str:
        """Get approval display text."""
        return self.manager.approval_handler.display_plan_for_approval(state)
    
    def _format_results(self, state: ReActState) -> Dict[str, Any]:
        """Format workflow results."""
        return {
            "session_id": state.session_id,
            "user_prompt": state.user_prompt,
            "plan_approved": state.plan_approved,
            "guidelines": state.guidelines_generated,
            "execution_plan": [
                {
                    "title": step.title,
                    "description": step.description,
                    "expected_output": step.expected_output,
                }
                for step in state.execution_plan
            ],
            "asset_requests": [
                {
                    "title": asset.title,
                    "type": asset.asset_type.value,
                    "description": asset.description,
                }
                for asset in state.asset_requests
            ],
            "generated_assets": [
                {
                    "title": asset.title,
                    "type": asset.asset_type.value,
                    "model_used": asset.model_used.value,
                    "image_url": asset.image_url,
                    "generated_prompt": asset.generated_prompt,
                    "quality_score": asset.quality_score,
                }
                for asset in state.generated_assets
            ],
            "status": state.current_stage.value,
            "errors": state.errors,
        }
    
    def save_to_markdown(self, state: ReActState, output_dir: str = "output") -> str:
        """Save workflow results to a markdown file.
        
        Args:
            state: The workflow state
            output_dir: Directory to save the file (default: "output")
            
        Returns:
            Path to the saved file
        """
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Clean the prompt for filename (remove special chars, limit length)
        clean_prompt = "".join(c for c in state.user_prompt[:50] if c.isalnum() or c in (' ', '-', '_')).strip()
        clean_prompt = clean_prompt.replace(' ', '_')
        filename = f"{timestamp}_{clean_prompt}.md"
        filepath = output_path / filename
        
        # Generate markdown content
        markdown_content = self._generate_markdown(state)
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return str(filepath)
    
    def _generate_markdown(self, state: ReActState) -> str:
        """Generate markdown content from workflow results."""
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
                if asset.priority:
                    lines.append(f"**Priority:** {asset.priority}/5")
                    lines.append(f"")
            
            lines.append(f"---")
            lines.append(f"")
        
        # Generated Assets
        if state.generated_assets:
            lines.append(f"## 🖼️  Generated Assets")
            lines.append(f"")
            lines.append(f"**Total Generated:** {len(state.generated_assets)}")
            successful = len([a for a in state.generated_assets if a.image_url])
            lines.append(f"**Successful:** {successful}/{len(state.generated_assets)}")
            lines.append(f"")
            
            for i, asset in enumerate(state.generated_assets, 1):
                lines.append(f"### {i}. {asset.title}")
                lines.append(f"")
                lines.append(f"**Type:** {asset.asset_type.value}")
                lines.append(f"**Model Used:** {asset.model_used.value}")
                lines.append(f"")
                
                if asset.image_url:
                    lines.append(f"**Status:** ✅ Successfully Generated")
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
