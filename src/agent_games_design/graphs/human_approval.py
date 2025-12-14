"""Human approval handler for ReAct workflow."""

from ..state import ReActState, WorkflowStage


class HumanApprovalHandler:
    """Handles human approval of execution plans."""

    def display_plan_for_approval(self, state: ReActState) -> str:
        """Format the execution plan for human review."""
        output = []
        output.append("🎯 EXECUTION PLAN FOR APPROVAL")
        output.append("=" * 50)
        output.append(f"🎮 Project: {state.user_prompt}")
        output.append(f"🔍 Session ID: {state.session_id}")
        output.append("")

        output.append("📋 EXECUTION STEPS:")
        output.append("-" * 30)

        for i, step in enumerate(state.execution_plan, 1):
            output.append(f"{i}. {step.title}")
            output.append(f"   Description: {step.description}")
            output.append(f"   Expected Output: {step.expected_output}")
            output.append(f"   Estimated Time: {step.estimated_time}")
            output.append(f"   Priority: {step.priority}")
            if step.dependencies:
                output.append(f"   Dependencies: {', '.join(step.dependencies)}")
            output.append("")

        output.append("🎨 ASSETS TO GENERATE:")
        output.append("-" * 30)

        for i, asset in enumerate(state.asset_requests, 1):
            output.append(f"{i}. {asset.title} ({asset.asset_type.value})")
            output.append(f"   Description: {asset.description}")
            output.append(f"   Target Model: {asset.target_model.value}")
            if asset.style_requirements:
                output.append(f"   Style: {', '.join(asset.style_requirements)}")
            if asset.technical_specs:
                specs = ', '.join(f"{k}: {v}" for k, v in asset.technical_specs.items())
                output.append(f"   Technical Specs: {specs}")
            output.append("")

        output.append("❓ APPROVAL REQUIRED")
        output.append("-" * 20)
        output.append("• Type 'approve' or 'yes' to proceed with this plan")
        output.append("• Type 'reject' or 'no' to revise the plan")
        output.append("• Type 'modify: <your feedback>' to request changes")
        output.append("")

        return "\n".join(output)

    def process_human_response(self, state: ReActState, response: str) -> ReActState:
        """Process human approval response."""
        response_lower = response.strip().lower()

        if response_lower in ["approve", "yes", "y", "approved"]:
            # Plan approved - move to execution
            state.plan_approved = True
            state.current_stage = WorkflowStage.REACT_EXECUTION
            state.plan_feedback = "Plan approved by human reviewer"

        elif response_lower in ["reject", "no", "n", "rejected"]:
            # Plan rejected - go back to planning
            state.plan_approved = False
            state.current_stage = WorkflowStage.PLANNING
            state.plan_feedback = "Plan rejected by human reviewer"
            # Clear previous plan for regeneration
            state.execution_plan = []
            state.asset_requests = []

        elif response_lower.startswith("modify:"):
            # Plan needs modification
            feedback = response[7:].strip()  # Remove 'modify:' prefix
            state.plan_approved = False
            state.current_stage = WorkflowStage.PLANNING
            state.plan_feedback = f"Plan modification requested: {feedback}"
            # Keep the plan but mark for revision

        else:
            # Invalid response - stay in approval stage
            state.plan_feedback = f"Invalid response: {response}. Please respond with 'approve', 'reject', or 'modify: <feedback>'"

        return state

    def get_approval_prompt(self) -> str:
        """Get a prompt for requesting human approval."""
        return """
Please review the execution plan above and provide your approval decision:

This plan outlines the steps we'll take to fulfill your game design request.
Your input will help ensure the plan meets your expectations before we begin the work.
        """
