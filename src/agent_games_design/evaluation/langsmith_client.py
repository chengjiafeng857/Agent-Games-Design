"""LangSmith client for tracking and evaluating workflows."""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from langsmith import Client
from langchain_core.tracers.langchain import LangChainTracer

from ..config import settings
from ..state import ReActState


class LangSmithClient:
    """Client for LangSmith tracking and evaluation."""
    
    def __init__(self):
        """Initialize LangSmith client."""
        self.client: Optional[Client] = None
        self.tracer: Optional[LangChainTracer] = None
        
        if settings.langchain_tracing_v2 and settings.langchain_api_key:
            try:
                self.client = Client(
                    api_url="https://api.smith.langchain.com",
                    api_key=settings.langchain_api_key
                )
                self.tracer = LangChainTracer(
                    project_name=settings.langchain_project,
                    client=self.client
                )
                self.enabled = True
            except Exception as e:
                print(f"Warning: Failed to initialize LangSmith client: {e}")
                self.enabled = False
        else:
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if LangSmith is properly configured and enabled."""
        return self.enabled and self.client is not None
    
    def create_run(
        self, 
        name: str,
        inputs: Dict[str, Any],
        run_type: str = "chain",
        **kwargs
    ) -> Optional[str]:
        """Create a new run in LangSmith.
        
        Args:
            name: Name of the run
            inputs: Input data for the run
            run_type: Type of run (chain, tool, llm, etc.)
            **kwargs: Additional run metadata
            
        Returns:
            Run ID if successful, None otherwise
        """
        if not self.is_enabled():
            return None
            
        try:
            run_id = str(uuid.uuid4())
            
            self.client.create_run(
                id=run_id,
                name=name,
                run_type=run_type,
                inputs=inputs,
                project_name=settings.langchain_project,
                start_time=datetime.utcnow(),
                **kwargs
            )
            
            return run_id
        except Exception as e:
            print(f"Warning: Failed to create LangSmith run: {e}")
            return None
    
    def update_run(
        self,
        run_id: str,
        outputs: Optional[Dict[str, Any]] = None,
        end_time: Optional[datetime] = None,
        error: Optional[str] = None,
        **kwargs
    ):
        """Update an existing run with outputs and end time.
        
        Args:
            run_id: ID of the run to update
            outputs: Output data from the run
            end_time: When the run ended
            error: Error message if the run failed
            **kwargs: Additional metadata to update
        """
        if not self.is_enabled() or not run_id:
            return
            
        try:
            self.client.update_run(
                run_id=run_id,
                outputs=outputs,
                end_time=end_time or datetime.utcnow(),
                error=error,
                **kwargs
            )
        except Exception as e:
            print(f"Warning: Failed to update LangSmith run: {e}")
    
    def log_workflow_execution(
        self,
        workflow_name: str,
        state: ReActState,
        start_time: datetime,
        end_time: Optional[datetime] = None
    ) -> Optional[str]:
        """Log a complete workflow execution to LangSmith.
        
        Args:
            workflow_name: Name of the workflow
            state: Final state of the workflow
            start_time: When the workflow started
            end_time: When the workflow ended
            
        Returns:
            Run ID if successful
        """
        if not self.is_enabled():
            return None
            
        inputs = {
            "user_prompt": state.user_prompt,
            "session_id": state.session_id,
        }
        
        outputs = {
            "current_stage": state.current_stage.value,
            "plan_approved": state.plan_approved,
            "guidelines_generated": bool(state.guidelines_generated),
            "num_assets_requested": len(state.asset_requests),
            "num_assets_generated": len(state.generated_assets),
            "total_steps": state.total_steps,
            "errors": state.errors,
        }
        
        extra = {
            "session_metadata": {
                "execution_plan_steps": len(state.execution_plan),
                "react_observations": len(state.react_observations),
                "evaluation_scores": state.evaluation_scores,
            }
        }
        
        try:
            run_id = self.create_run(
                name=workflow_name,
                inputs=inputs,
                run_type="chain",
                extra=extra
            )
            
            if run_id:
                self.update_run(
                    run_id=run_id,
                    outputs=outputs,
                    end_time=end_time or datetime.utcnow()
                )
                
            return run_id
            
        except Exception as e:
            print(f"Warning: Failed to log workflow execution: {e}")
            return None
    
    def create_feedback(
        self,
        run_id: str,
        key: str,
        score: float,
        value: Optional[Any] = None,
        comment: Optional[str] = None
    ):
        """Create feedback for a run.
        
        Args:
            run_id: ID of the run to provide feedback for
            key: Feedback key/metric name
            score: Numeric score (0.0 to 1.0)
            value: Optional feedback value
            comment: Optional comment
        """
        if not self.is_enabled() or not run_id:
            return
            
        try:
            self.client.create_feedback(
                run_id=run_id,
                key=key,
                score=score,
                value=value,
                comment=comment
            )
        except Exception as e:
            print(f"Warning: Failed to create feedback: {e}")
    
    def get_tracer_config(self) -> Dict[str, Any]:
        """Get configuration for LangChain tracer.
        
        Returns:
            Configuration dict for use with LangGraph
        """
        if not self.is_enabled():
            return {}
            
        return {
            "configurable": {
                "callbacks": [self.tracer] if self.tracer else [],
                "project_name": settings.langchain_project,
            }
        }
