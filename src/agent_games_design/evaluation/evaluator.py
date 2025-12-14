"""Main workflow evaluator using LangSmith."""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .langsmith_client import LangSmithClient
from .metrics import EvaluationMetrics, MetricResult
from ..state import ReActState


class WorkflowEvaluator:
    """Evaluates workflow performance and logs to LangSmith."""
    
    def __init__(self):
        """Initialize the workflow evaluator."""
        self.langsmith_client = LangSmithClient()
        self.metrics = EvaluationMetrics()
    
    def evaluate_workflow(
        self, 
        state: ReActState,
        workflow_name: str = "react_game_design_workflow",
        start_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Evaluate a complete workflow execution.
        
        Args:
            state: Final state of the workflow
            workflow_name: Name of the workflow for tracking
            start_time: When the workflow started (optional)
            
        Returns:
            Dictionary containing evaluation results
        """
        evaluation_start = datetime.utcnow()
        
        # Run individual metric evaluations
        individual_metrics = self._evaluate_individual_metrics(state)
        
        # Calculate overall score
        overall_metric = self.metrics.overall_score(individual_metrics)
        individual_metrics.append(overall_metric)
        
        # Prepare evaluation results
        evaluation_results = {
            "evaluation_timestamp": evaluation_start.isoformat(),
            "workflow_name": workflow_name,
            "session_id": state.session_id,
            "metrics": {metric.name: metric.score for metric in individual_metrics},
            "metric_details": {metric.name: metric.details for metric in individual_metrics},
            "metric_comments": {metric.name: metric.comment for metric in individual_metrics},
            "langsmith_enabled": self.langsmith_client.is_enabled(),
        }
        
        # Log to LangSmith if enabled
        run_id = None
        if self.langsmith_client.is_enabled():
            try:
                run_id = self._log_to_langsmith(
                    state=state,
                    workflow_name=workflow_name,
                    individual_metrics=individual_metrics,
                    start_time=start_time or evaluation_start
                )
                evaluation_results["langsmith_run_id"] = run_id
            except Exception as e:
                evaluation_results["langsmith_error"] = str(e)
        
        # Update state with evaluation results
        state.evaluation_scores = evaluation_results["metrics"]
        
        return evaluation_results
    
    def _evaluate_individual_metrics(self, state: ReActState) -> List[MetricResult]:
        """Evaluate individual metrics for the workflow.
        
        Args:
            state: Workflow state to evaluate
            
        Returns:
            List of metric results
        """
        metrics = []
        
        # Plan Quality
        try:
            plan_metric = self.metrics.plan_quality(state)
            metrics.append(plan_metric)
        except Exception as e:
            print(f"Warning: Failed to evaluate plan quality: {e}")
        
        # ReAct Execution Quality
        try:
            react_metric = self.metrics.react_execution_quality(state)
            metrics.append(react_metric)
        except Exception as e:
            print(f"Warning: Failed to evaluate ReAct execution quality: {e}")
        
        # Asset Generation Quality
        try:
            asset_metric = self.metrics.asset_generation_quality(state)
            metrics.append(asset_metric)
        except Exception as e:
            print(f"Warning: Failed to evaluate asset generation quality: {e}")
        
        # Workflow Efficiency
        try:
            efficiency_metric = self.metrics.workflow_efficiency(state)
            metrics.append(efficiency_metric)
        except Exception as e:
            print(f"Warning: Failed to evaluate workflow efficiency: {e}")
        
        return metrics
    
    def _log_to_langsmith(
        self,
        state: ReActState,
        workflow_name: str,
        individual_metrics: List[MetricResult],
        start_time: datetime
    ) -> Optional[str]:
        """Log evaluation results to LangSmith.
        
        Args:
            state: Workflow state
            workflow_name: Name of the workflow
            individual_metrics: List of metric results
            start_time: When the workflow started
            
        Returns:
            Run ID if successful, None otherwise
        """
        # Log the main workflow execution
        run_id = self.langsmith_client.log_workflow_execution(
            workflow_name=workflow_name,
            state=state,
            start_time=start_time,
            end_time=datetime.utcnow()
        )
        
        if not run_id:
            return None
        
        # Create feedback entries for each metric
        for metric in individual_metrics:
            try:
                self.langsmith_client.create_feedback(
                    run_id=run_id,
                    key=metric.name,
                    score=metric.score,
                    value=metric.details,
                    comment=metric.comment
                )
            except Exception as e:
                print(f"Warning: Failed to create feedback for {metric.name}: {e}")
        
        return run_id
    
    def create_evaluation_summary(self, evaluation_results: Dict[str, Any]) -> str:
        """Create a human-readable summary of evaluation results.
        
        Args:
            evaluation_results: Results from evaluate_workflow
            
        Returns:
            Formatted summary string
        """
        summary = []
        summary.append("🔍 WORKFLOW EVALUATION RESULTS")
        summary.append("=" * 40)
        
        # Overall score
        overall_score = evaluation_results["metrics"].get("overall_score", 0.0)
        summary.append(f"🎯 Overall Score: {overall_score:.3f}/1.000")
        summary.append("")
        
        # Individual metrics
        summary.append("📊 DETAILED METRICS:")
        summary.append("-" * 30)
        
        metrics_info = [
            ("Plan Quality", "plan_quality", "📋"),
            ("ReAct Execution", "react_execution_quality", "🤖"),
            ("Asset Generation", "asset_generation_quality", "🎨"),
            ("Workflow Efficiency", "workflow_efficiency", "⚡"),
        ]
        
        for display_name, metric_key, icon in metrics_info:
            score = evaluation_results["metrics"].get(metric_key, 0.0)
            comment = evaluation_results["metric_comments"].get(metric_key, "")
            
            # Create visual bar
            bar_length = 20
            filled = int(score * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            summary.append(f"{icon} {display_name:<18} {score:.3f} [{bar}]")
            if comment:
                summary.append(f"   → {comment}")
            summary.append("")
        
        # LangSmith info
        if evaluation_results.get("langsmith_enabled"):
            if evaluation_results.get("langsmith_run_id"):
                summary.append(f"📡 LangSmith Run ID: {evaluation_results['langsmith_run_id']}")
            else:
                summary.append("⚠️ LangSmith enabled but logging failed")
        else:
            summary.append("📡 LangSmith: Not configured")
        
        summary.append("")
        summary.append(f"⏰ Evaluated at: {evaluation_results['evaluation_timestamp']}")
        
        return "\n".join(summary)
    
    def get_langsmith_config(self) -> Dict[str, Any]:
        """Get LangSmith configuration for use with graphs.
        
        Returns:
            Configuration dictionary for LangGraph
        """
        return self.langsmith_client.get_tracer_config()
