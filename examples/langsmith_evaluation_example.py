"""Example of using LangSmith evaluation with ReAct workflow."""

import asyncio
import os
from datetime import datetime

from agent_games_design.evaluation import WorkflowEvaluator, create_evaluated_workflow
from agent_games_design.state import ReActState


async def main():
    """Run LangSmith evaluation example."""
    print("🔍 LangSmith Evaluation Example")
    print("=" * 50)
    
    # Check if LangSmith is configured
    langsmith_configured = (
        os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true" and
        os.getenv("LANGCHAIN_API_KEY", "") != ""
    )
    
    if langsmith_configured:
        print("✅ LangSmith is configured and enabled")
        print(f"📡 Project: {os.getenv('LANGCHAIN_PROJECT', 'agent-games-design')}")
    else:
        print("⚠️ LangSmith not configured - evaluation will run locally only")
        print("💡 To enable LangSmith:")
        print("   1. Set LANGCHAIN_TRACING_V2=true in your .env")
        print("   2. Set LANGCHAIN_API_KEY=your_api_key in your .env")
        print("   3. Optionally set LANGCHAIN_PROJECT=your_project_name")
    
    print()
    
    # Example 1: Direct evaluation of a mock workflow state
    print("📊 Example 1: Direct Workflow Evaluation")
    print("-" * 40)
    
    # Create a mock completed workflow state for demonstration
    mock_state = create_mock_completed_state()
    
    # Create evaluator and run evaluation
    evaluator = WorkflowEvaluator()
    evaluation_results = evaluator.evaluate_workflow(
        state=mock_state,
        workflow_name="example_evaluation",
        start_time=datetime.utcnow()
    )
    
    # Display results
    summary = evaluator.create_evaluation_summary(evaluation_results)
    print(summary)
    print()
    
    # Example 2: Using EvaluatedWorkflow (integrated evaluation)
    print("🔄 Example 2: Integrated Workflow with Evaluation")
    print("-" * 40)
    
    try:
        # Create evaluated workflow
        evaluated_workflow = create_evaluated_workflow()
        
        # Start a workflow (this would normally continue with user interaction)
        initial_state = evaluated_workflow.start_workflow(
            user_prompt="Create a simple mobile puzzle game with colorful graphics",
            session_id="eval_demo_session"
        )
        
        print(f"✅ Started evaluated workflow: {initial_state.session_id}")
        print(f"📍 Initial stage: {initial_state.current_stage.value}")
        
        # In a real scenario, you would continue executing the workflow
        # For this demo, we'll just show the configuration
        langsmith_config = evaluated_workflow.evaluator.get_langsmith_config()
        
        if langsmith_config:
            print(f"🔧 LangSmith tracking configured")
        else:
            print(f"🔧 Local evaluation only (LangSmith not enabled)")
        
    except Exception as e:
        print(f"❌ Error creating evaluated workflow: {e}")
    
    print()
    
    # Example 3: Configuration guidance
    print("⚙️ Configuration Guide")
    print("-" * 40)
    
    print("To use LangSmith evaluation, add to your .env file:")
    print()
    print("# LangSmith Configuration")
    print("LANGCHAIN_TRACING_V2=true")
    print("LANGCHAIN_API_KEY=your_langsmith_api_key_here")
    print("LANGCHAIN_PROJECT=agent-games-design")
    print()
    print("Then run your workflow normally - evaluation happens automatically!")
    print()
    
    # Show available metrics
    print("📈 Available Evaluation Metrics:")
    print("- plan_quality: Quality of execution plan generation")
    print("- react_execution_quality: Quality of ReAct reasoning steps")  
    print("- asset_generation_quality: Success rate and quality of assets")
    print("- workflow_efficiency: Speed and error-free execution")
    print("- overall_score: Weighted combination of all metrics")


def create_mock_completed_state() -> ReActState:
    """Create a mock workflow state for demonstration."""
    from agent_games_design.state import (
        ReActState, WorkflowStage, PlanStep, AssetRequest, 
        GameDesignAsset, ReActObservation, AssetType, ModelType
    )
    from langchain_core.messages import HumanMessage
    
    return ReActState(
        user_prompt="Create a mobile puzzle game with physics-based mechanics",
        session_id="demo_session_123",
        current_stage=WorkflowStage.COMPLETED,
        
        # Execution plan
        execution_plan=[
            PlanStep(
                step_id="research",
                title="Research Phase",
                description="Research puzzle game mechanics and physics systems",
                expected_output="Research document with findings",
                dependencies=[],
                estimated_time="2 hours",
                priority=1
            ),
            PlanStep(
                step_id="design",
                title="Game Design",
                description="Design core gameplay mechanics and user interface",
                expected_output="Design document and mockups",
                dependencies=["research"],
                estimated_time="4 hours",
                priority=1
            ),
        ],
        
        plan_approved=True,
        plan_feedback="Plan approved by reviewer",
        
        # ReAct observations
        react_observations=[
            ReActObservation(
                step_number=1,
                action_taken="research_game_mechanics",
                observation="Found several successful physics-based puzzle games with engaging mechanics",
                next_thought="Need to analyze what makes these games successful"
            ),
            ReActObservation(
                step_number=2,
                action_taken="analyze_target_audience",
                observation="Mobile puzzle game players prefer simple controls with deep gameplay",
                next_thought="Should focus on intuitive touch controls"
            ),
        ],
        
        guidelines_generated="# Game Design Guidelines\n\n## Core Mechanics\n- Physics-based puzzle solving\n- Touch-friendly controls\n- Progressive difficulty\n\n## Implementation\n1. Prototype core physics\n2. Design levels\n3. Test with users",
        
        # Asset requests and generation
        asset_requests=[
            AssetRequest(
                asset_id="hero_character",
                asset_type=AssetType.CHARACTER_CONCEPT,
                title="Hero Character",
                description="Main character for the puzzle game",
                target_model=ModelType.GOOGLE_NANO
            ),
        ],
        
        generated_assets=[
            GameDesignAsset(
                asset_id="hero_character",
                asset_type=AssetType.CHARACTER_CONCEPT,
                title="Hero Character",
                generated_prompt="Cute cartoon character for mobile puzzle game",
                model_used=ModelType.GOOGLE_NANO,
                image_url="https://example.com/generated_hero.png",
                quality_score=0.85,
                metadata={"generated_at": "2024-01-01T12:00:00Z"}
            ),
        ],
        
        total_steps=5,
        errors=[],
        
        messages=[
            HumanMessage(content="Create a mobile puzzle game with physics-based mechanics")
        ],
    )


if __name__ == "__main__":
    asyncio.run(main())
