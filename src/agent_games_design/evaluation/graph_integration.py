"""Integration of evaluation with LangGraph workflows."""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

from ..state import ReActState, WorkflowStage
from ..agents import PlanningAgent, ReActExecutor
from ..graphs.human_approval import HumanApprovalHandler
from .evaluator import WorkflowEvaluator


class EvaluatedWorkflow:
    """Wrapper for ReAct workflow with integrated LangSmith evaluation."""
    
    def __init__(self):
        """Initialize the evaluated workflow."""
        self.evaluator = WorkflowEvaluator()
        self.workflow = self._create_evaluated_workflow()
        self.approval_handler = HumanApprovalHandler()
        
    def _create_evaluated_workflow(self):
        """Create ReAct workflow with evaluation integration.
        
        Returns:
            Compiled LangGraph workflow with evaluation
        """
        # Initialize components
        planning_agent = PlanningAgent()
        approval_handler = HumanApprovalHandler()
        react_executor = ReActExecutor()
        
        def planning_node(state: ReActState) -> Dict[str, Any]:
            """Planning node with evaluation tracking."""
            # Record start time for this stage
            if not hasattr(state, '_stage_start_times'):
                state._stage_start_times = {}
            state._stage_start_times['planning'] = datetime.utcnow()
            
            updated_state = planning_agent.create_plan(state)
            return {
                "current_stage": updated_state.current_stage,
                "execution_plan": updated_state.execution_plan,
                "asset_requests": updated_state.asset_requests,
                "messages": updated_state.messages,
                "errors": updated_state.errors,
            }

        def human_approval_node(state: ReActState) -> Dict[str, Any]:
            """Human approval node with evaluation tracking."""
            if not hasattr(state, '_stage_start_times'):
                state._stage_start_times = {}
            state._stage_start_times['human_approval'] = datetime.utcnow()
            
            approval_prompt = approval_handler.get_approval_prompt()
            plan_display = approval_handler.display_plan_for_approval(state)

            return {
                "current_stage": WorkflowStage.HUMAN_APPROVAL,
                "messages": [HumanMessage(content=f"{approval_prompt}\n\n{plan_display}")],
            }

        def react_execution_node(state: ReActState) -> Dict[str, Any]:
            """ReAct execution node with evaluation tracking."""
            if not hasattr(state, '_stage_start_times'):
                state._stage_start_times = {}
            state._stage_start_times['react_execution'] = datetime.utcnow()
            
            updated_state = react_executor.execute_react_workflow(state)
            return {
                "current_stage": updated_state.current_stage,
                "react_observations": updated_state.react_observations,
                "current_thought": updated_state.current_thought,
                "guidelines_generated": updated_state.guidelines_generated,
                "total_steps": updated_state.total_steps,
            }

        def asset_generation_node(state: ReActState) -> Dict[str, Any]:
            """Asset generation node with evaluation tracking."""
            import logging
            logger = logging.getLogger(__name__)
            
            if not hasattr(state, '_stage_start_times'):
                state._stage_start_times = {}
            state._stage_start_times['asset_generation'] = datetime.utcnow()
            
            from ..agents import AssetGenerator
            asset_generator = AssetGenerator()
            
            try:
                if not state.asset_requests:
                    logger.info("No asset requests found, skipping asset generation")
                    state.current_stage = WorkflowStage.EVALUATION
                    return {
                        "current_stage": state.current_stage,
                        "generated_assets": state.generated_assets,
                        "errors": state.errors,
                    }
                
                logger.info(f"🎨 Generating {len(state.asset_requests)} assets")
                generated_assets = asset_generator.generate_assets(state.asset_requests)
                
                state.current_stage = WorkflowStage.EVALUATION
                return {
                    "current_stage": state.current_stage,
                    "generated_assets": generated_assets,
                    "errors": state.errors,
                }
                
            except Exception as e:
                logger.error(f"Asset generation failed: {e}")
                state.errors.append(f"Asset generation error: {str(e)}")
                state.current_stage = WorkflowStage.EVALUATION
                return {
                    "current_stage": state.current_stage,
                    "generated_assets": state.generated_assets,
                    "errors": state.errors,
                }

        def evaluation_node(state: ReActState) -> Dict[str, Any]:
            """Evaluation node - evaluates workflow performance using LangSmith."""
            if not hasattr(state, '_stage_start_times'):
                state._stage_start_times = {}
            state._stage_start_times['evaluation'] = datetime.utcnow()
            
            # Get workflow start time
            workflow_start_time = getattr(state, '_workflow_start_time', datetime.utcnow())
            
            # Run evaluation
            evaluation_results = self.evaluator.evaluate_workflow(
                state=state,
                workflow_name="react_game_design_workflow",
                start_time=workflow_start_time
            )
            
            # Update state
            state.current_stage = WorkflowStage.COMPLETED
            state.evaluation_scores = evaluation_results["metrics"]
            
            # Add evaluation metadata
            evaluation_metadata = {
                "evaluation_timestamp": evaluation_results["evaluation_timestamp"],
                "langsmith_run_id": evaluation_results.get("langsmith_run_id"),
                "metric_details": evaluation_results.get("metric_details", {}),
                "metric_comments": evaluation_results.get("metric_comments", {}),
            }
            
            return {
                "current_stage": state.current_stage,
                "evaluation_scores": state.evaluation_scores,
                "evaluation_metadata": evaluation_metadata,
            }

        # Conditional edge functions
        def should_continue_from_planning(state: ReActState) -> str:
            """Determine next step after planning."""
            if state.current_stage == WorkflowStage.HUMAN_APPROVAL:
                return "human_approval"
            else:
                return "planning"

        def should_continue_from_approval(state: ReActState) -> str:
            """Determine next step after human approval."""
            if state.current_stage == WorkflowStage.REACT_EXECUTION:
                return "react_execution"
            elif state.current_stage == WorkflowStage.PLANNING:
                return "planning"
            else:
                return "human_approval"

        def should_continue_from_react(state: ReActState) -> str:
            """Determine next step after ReAct execution."""
            if state.current_stage == WorkflowStage.ASSET_GENERATION:
                return "asset_generation"
            else:
                return END

        def should_continue_from_assets(state: ReActState) -> str:
            """Determine next step after asset generation."""
            if state.current_stage == WorkflowStage.EVALUATION:
                return "evaluation"
            else:
                return END

        # Create the workflow graph
        workflow = StateGraph(ReActState)

        # Add nodes
        workflow.add_node("planning", planning_node)
        workflow.add_node("human_approval", human_approval_node)
        workflow.add_node("react_execution", react_execution_node)
        workflow.add_node("asset_generation", asset_generation_node)
        workflow.add_node("evaluation", evaluation_node)

        # Set entry point
        workflow.set_entry_point("planning")

        # Add edges
        workflow.add_conditional_edges(
            "planning",
            should_continue_from_planning,
            {"human_approval": "human_approval", "planning": "planning"},
        )

        workflow.add_conditional_edges(
            "human_approval",
            should_continue_from_approval,
            {
                "react_execution": "react_execution",
                "planning": "planning",
                "human_approval": "human_approval",
            },
        )

        workflow.add_conditional_edges(
            "react_execution",
            should_continue_from_react,
            {"asset_generation": "asset_generation", END: END},
        )

        workflow.add_conditional_edges(
            "asset_generation", 
            should_continue_from_assets, 
            {"evaluation": "evaluation", END: END}
        )

        workflow.add_edge("evaluation", END)

        # Compile with memory and LangSmith configuration
        memory = MemorySaver()
        
        # Get LangSmith configuration for tracing
        langsmith_config = self.evaluator.get_langsmith_config()
        
        return workflow.compile(
            checkpointer=memory,
            **langsmith_config
        )
    
    def start_workflow(
        self, 
        user_prompt: str, 
        session_id: Optional[str] = None
    ) -> ReActState:
        """Start a new evaluated ReAct workflow.
        
        Args:
            user_prompt: The user's game design request
            session_id: Optional session identifier
            
        Returns:
            Initial ReAct state with evaluation tracking
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        initial_state = ReActState(
            user_prompt=user_prompt,
            session_id=session_id,
            current_stage=WorkflowStage.PLANNING,
            messages=[HumanMessage(content=user_prompt)],
        )
        
        # Add evaluation tracking
        initial_state._workflow_start_time = datetime.utcnow()
        initial_state._stage_start_times = {}
        
        return initial_state
    
    def execute_step(
        self, 
        state: ReActState, 
        config: Optional[Dict] = None
    ) -> ReActState:
        """Execute a single step in the evaluated workflow.
        
        Args:
            state: Current ReAct state
            config: Optional configuration for the step
            
        Returns:
            Updated ReAct state
        """
        if not config:
            # Include LangSmith tracing configuration
            langsmith_config = self.evaluator.get_langsmith_config()
            config = {
                "configurable": {
                    "thread_id": state.session_id,
                    **langsmith_config.get("configurable", {})
                }
            }

        # Execute one step of the workflow
        for update in self.workflow.stream(state, config):
            for key, value in update.items():
                if hasattr(state, key):
                    setattr(state, key, value)
            break  # Only execute one step

        return state
    
    def process_human_approval(
        self, 
        state: ReActState, 
        human_response: str
    ) -> ReActState:
        """Process human approval response with evaluation tracking.
        
        Args:
            state: Current ReAct state in approval stage
            human_response: Human's approval/rejection response
            
        Returns:
            Updated ReAct state
        """
        return self.approval_handler.process_human_response(state, human_response)
    
    def get_evaluation_summary(self, state: ReActState) -> str:
        """Get evaluation summary for completed workflow.
        
        Args:
            state: Completed ReAct state
            
        Returns:
            Human-readable evaluation summary
        """
        if not state.evaluation_scores:
            return "No evaluation results available yet."
        
        # Create mock evaluation results for summary formatting
        evaluation_results = {
            "metrics": state.evaluation_scores,
            "metric_details": getattr(state, "evaluation_metadata", {}).get("metric_details", {}),
            "metric_comments": getattr(state, "evaluation_metadata", {}).get("metric_comments", {}),
            "evaluation_timestamp": getattr(state, "evaluation_metadata", {}).get("evaluation_timestamp", ""),
            "langsmith_enabled": self.evaluator.langsmith_client.is_enabled(),
            "langsmith_run_id": getattr(state, "evaluation_metadata", {}).get("langsmith_run_id"),
        }
        
        return self.evaluator.create_evaluation_summary(evaluation_results)


def create_evaluated_workflow() -> EvaluatedWorkflow:
    """Create a ReAct workflow with integrated LangSmith evaluation.
    
    Returns:
        EvaluatedWorkflow instance ready for use
    """
    return EvaluatedWorkflow()
