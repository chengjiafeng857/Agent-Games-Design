"""ReAct workflow graph for game design."""

from typing import Dict, Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

from ..state import ReActState, WorkflowStage
from ..agents import PlanningAgent, ReActExecutor, AssetGenerator
from .human_approval import HumanApprovalHandler


def create_react_workflow():
    """Create the complete ReAct workflow graph.

    Returns:
        Compiled LangGraph workflow
    """
    # Initialize components
    planning_agent = PlanningAgent()
    approval_handler = HumanApprovalHandler()
    react_executor = ReActExecutor()
    asset_generator = AssetGenerator()

    def planning_node(state: ReActState) -> Dict[str, Any]:
        """Planning node - creates execution plan."""
        updated_state = planning_agent.create_plan(state)
        return {
            "current_stage": updated_state.current_stage,
            "execution_plan": updated_state.execution_plan,
            "asset_requests": updated_state.asset_requests,
            "messages": updated_state.messages,
            "errors": updated_state.errors,
        }

    def human_approval_node(state: ReActState) -> Dict[str, Any]:
        """Human approval node - displays plan for approval.
        
        If approval has already been processed externally (stage changed to REACT_EXECUTION),
        this node just passes through. Otherwise, it displays the plan.
        """
        # If already approved/rejected externally, just pass through
        if state.current_stage in [WorkflowStage.REACT_EXECUTION, WorkflowStage.PLANNING]:
            return {}  # No changes, just pass through
        
        # Otherwise, display the plan for approval
        approval_prompt = approval_handler.get_approval_prompt()
        plan_display = approval_handler.display_plan_for_approval(state)

        return {
            "current_stage": WorkflowStage.HUMAN_APPROVAL,
            "messages": [HumanMessage(content=f"{approval_prompt}\n\n{plan_display}")],
        }

    def react_execution_node(state: ReActState) -> Dict[str, Any]:
        """ReAct execution node - generates guidelines."""
        updated_state = react_executor.execute_react_workflow(state)
        return {
            "current_stage": updated_state.current_stage,
            "react_observations": updated_state.react_observations,
            "current_thought": updated_state.current_thought,
            "guidelines_generated": updated_state.guidelines_generated,
            "total_steps": updated_state.total_steps,
        }

    def asset_generation_node(state: ReActState) -> Dict[str, Any]:
        """Asset generation node - creates game assets using DALL-E 3 and other models."""
        import logging
        logger = logging.getLogger(__name__)
        
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
        """Evaluation node - evaluates workflow performance."""
        # For now, provide basic evaluation
        # In a full implementation, this would use LangSmithEvaluator
        state.current_stage = WorkflowStage.COMPLETED
        state.evaluation_scores = {"overall_score": 0.85}  # Placeholder
        return {
            "current_stage": state.current_stage,
            "evaluation_scores": state.evaluation_scores,
        }

    def should_continue_from_planning(state: ReActState) -> str:
        """Determine next step after planning."""
        if state.current_stage == WorkflowStage.HUMAN_APPROVAL:
            return "human_approval"
        else:
            # Stay in planning if there were errors
            return "planning"

    def should_continue_from_approval(state: ReActState) -> str:
        """Determine next step after human approval.
        
        The approval processing happens externally (in CLI) between workflow invocations.
        This function routes based on the state that was set by process_human_response.
        """
        if state.current_stage == WorkflowStage.REACT_EXECUTION:
            # Approval was granted, move to execution
            return "react_execution"
        elif state.current_stage == WorkflowStage.PLANNING:
            # Rejection or modification requested, go back to planning
            return "planning"
        elif state.plan_approved is True:
            # Approval was granted but stage not yet updated, go to execution
            return "react_execution"
        elif state.plan_approved is False:
            # Rejected, go back to planning
            return "planning"
        else:
            # State is still HUMAN_APPROVAL with no decision yet
            # Stay here to prevent infinite loop - workflow will end naturally
            return END

    def should_continue_from_react(state: ReActState) -> str:
        """Determine next step after ReAct execution."""
        if state.current_stage == WorkflowStage.ASSET_GENERATION:
            return "asset_generation"
        else:
            return END  # Something went wrong, end workflow

    def should_continue_from_assets(state: ReActState) -> str:
        """Determine next step after asset generation."""
        if state.current_stage == WorkflowStage.EVALUATION:
            return "evaluation"
        else:
            return END  # Something went wrong, end workflow

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
            END: END,  # Allow ending from human_approval
        },
    )

    workflow.add_conditional_edges(
        "react_execution",
        should_continue_from_react,
        {"asset_generation": "asset_generation", END: END},
    )

    workflow.add_conditional_edges(
        "asset_generation", should_continue_from_assets, {"evaluation": "evaluation", END: END}
    )

    workflow.add_edge("evaluation", END)

    # Compile with memory
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)