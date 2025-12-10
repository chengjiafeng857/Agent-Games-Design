"""ReAct workflow manager."""

import uuid
from typing import Dict, Any, Optional

from langchain_core.messages import HumanMessage

from ..state import ReActState, WorkflowStage
from .human_approval import HumanApprovalHandler
from .react_workflow import create_react_workflow


class ReActWorkflowManager:
    """Manager for ReAct workflow execution."""

    def __init__(self):
        """Initialize the workflow manager."""
        self.workflow = create_react_workflow()
        self.approval_handler = HumanApprovalHandler()

    def start_workflow(self, user_prompt: str, session_id: Optional[str] = None) -> ReActState:
        """Start a new ReAct workflow."""
        if not session_id:
            session_id = str(uuid.uuid4())

        initial_state = ReActState(
            user_prompt=user_prompt,
            session_id=session_id,
            current_stage=WorkflowStage.PLANNING,
            messages=[HumanMessage(content=user_prompt)],
        )

        return initial_state

    def execute_step(self, state: ReActState, config: Optional[Dict] = None) -> ReActState:
        """Execute workflow until it reaches a natural stopping point.
        
        The workflow will execute until:
        1. It reaches an END state
        2. It reaches human_approval state (waiting for external processing)
        3. An error occurs
        
        Uses invoke() which properly handles generator cleanup and avoids GeneratorExit.
        """
        if not config:
            config = {"configurable": {"thread_id": state.session_id}}

        # Invoke the workflow - it will run until completion or a stopping point
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            result = self.workflow.invoke(state, config)
            
            # LangGraph returns a dict with the updated state
            logger.debug(f"Workflow result type: {type(result)}")
            
            # Convert result dict back to ReActState
            if isinstance(result, dict):
                # Create a new ReActState from the result dict
                # Filter out LangGraph internal keys
                filtered_result = {k: v for k, v in result.items() if not k.startswith('__')}
                
                # Return a new state with the updated values
                from ..state import ReActState
                return ReActState(**filtered_result)
            else:
                # Result is already a Pydantic model
                return result
                        
        except Exception as e:
            # Log errors
            logger.error(f"Error in workflow execution: {e}", exc_info=True)
            if "'__end__'" not in str(e):
                state.errors.append(str(e))
            return state

    def process_human_approval(self, state: ReActState, human_response: str) -> ReActState:
        """Process human approval response."""
        return self.approval_handler.process_human_response(state, human_response)

    def get_workflow_status(self, state: ReActState) -> Dict[str, Any]:
        """Get current workflow status."""
        return {
            "session_id": state.session_id,
            "current_stage": state.current_stage.value,
            "total_steps": state.total_steps,
            "num_assets_requested": len(state.asset_requests),
            "num_assets_generated": len(state.generated_assets),
            "plan_approved": state.plan_approved,
            "has_guidelines": bool(state.guidelines_generated),
            "evaluation_scores": state.evaluation_scores,
            "errors": state.errors,
        }
