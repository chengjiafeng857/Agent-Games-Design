"""Evaluation metrics for game design workflows."""

from typing import Dict, List, Any
from dataclasses import dataclass

from ..state import ReActState, WorkflowStage


@dataclass
class MetricResult:
    """Result of a metric evaluation."""
    
    name: str
    score: float  # 0.0 to 1.0
    details: Dict[str, Any]
    comment: str


class EvaluationMetrics:
    """Metrics for evaluating game design workflow performance."""
    
    @staticmethod
    def plan_quality(state: ReActState) -> MetricResult:
        """Evaluate the quality of the execution plan.
        
        Args:
            state: ReAct state with execution plan
            
        Returns:
            Metric result for plan quality
        """
        score = 0.0
        details = {}
        
        if not state.execution_plan:
            return MetricResult(
                name="plan_quality",
                score=0.0,
                details={"reason": "No execution plan generated"},
                comment="Failed to generate execution plan"
            )
        
        # Base score for having a plan
        score += 0.3
        details["has_plan"] = True
        
        # Evaluate plan completeness
        num_steps = len(state.execution_plan)
        details["num_steps"] = num_steps
        
        if 3 <= num_steps <= 8:
            score += 0.2  # Good number of steps
            details["step_count_quality"] = "good"
        elif num_steps > 0:
            score += 0.1  # Some steps but not ideal
            details["step_count_quality"] = "acceptable"
        
        # Evaluate step detail quality
        detailed_steps = 0
        steps_with_time_estimates = 0
        steps_with_dependencies = 0
        
        for step in state.execution_plan:
            if len(step.description) > 20:
                detailed_steps += 1
            if step.estimated_time and step.estimated_time != "Unknown":
                steps_with_time_estimates += 1
            if step.dependencies:
                steps_with_dependencies += 1
        
        # Score for detailed descriptions
        if num_steps > 0:
            detail_ratio = detailed_steps / num_steps
            score += detail_ratio * 0.2
            details["detailed_steps_ratio"] = detail_ratio
        
        # Score for time estimates
        if num_steps > 0:
            time_estimate_ratio = steps_with_time_estimates / num_steps
            score += time_estimate_ratio * 0.1
            details["time_estimate_ratio"] = time_estimate_ratio
        
        # Score for dependencies (shows planning sophistication)
        if steps_with_dependencies > 0:
            score += 0.1
            details["has_dependencies"] = True
        
        # Human approval bonus
        if state.plan_approved is True:
            score += 0.2
            details["human_approved"] = True
        elif state.plan_approved is False:
            score -= 0.1
            details["human_rejected"] = True
        
        score = min(score, 1.0)
        
        comment = f"Generated {num_steps} steps, {detailed_steps} detailed, "
        comment += f"{'approved' if state.plan_approved else 'pending approval'}"
        
        return MetricResult(
            name="plan_quality",
            score=score,
            details=details,
            comment=comment
        )
    
    @staticmethod
    def react_execution_quality(state: ReActState) -> MetricResult:
        """Evaluate the quality of ReAct execution.
        
        Args:
            state: ReAct state with execution observations
            
        Returns:
            Metric result for ReAct execution quality
        """
        score = 0.0
        details = {}
        
        if not state.react_observations:
            return MetricResult(
                name="react_execution_quality",
                score=0.0,
                details={"reason": "No ReAct observations"},
                comment="No ReAct execution performed"
            )
        
        num_observations = len(state.react_observations)
        details["num_observations"] = num_observations
        
        # Base score for having observations
        score += 0.2
        
        # Optimal iteration count (3-7 is good, too few or too many is suboptimal)
        if 3 <= num_observations <= 7:
            score += 0.3
            details["iteration_quality"] = "optimal"
        elif 1 <= num_observations <= 10:
            score += 0.15
            details["iteration_quality"] = "acceptable"
        else:
            details["iteration_quality"] = "suboptimal"
        
        # Evaluate observation quality
        detailed_observations = 0
        observations_with_thoughts = 0
        unique_actions = set()
        
        for obs in state.react_observations:
            if len(obs.observation) > 50:
                detailed_observations += 1
            if obs.next_thought:
                observations_with_thoughts += 1
            unique_actions.add(obs.action_taken.lower())
        
        # Score for detailed observations
        if num_observations > 0:
            detail_ratio = detailed_observations / num_observations
            score += detail_ratio * 0.2
            details["detailed_observations_ratio"] = detail_ratio
        
        # Score for thoughtful reasoning
        if num_observations > 0:
            thought_ratio = observations_with_thoughts / num_observations
            score += thought_ratio * 0.15
            details["thought_ratio"] = thought_ratio
        
        # Score for action diversity
        details["unique_actions"] = len(unique_actions)
        if len(unique_actions) >= 3:
            score += 0.15
            details["action_diversity"] = "high"
        elif len(unique_actions) >= 2:
            score += 0.1
            details["action_diversity"] = "medium"
        
        # Score for successful completion (guidelines generated)
        if state.guidelines_generated:
            score += 0.2
            details["generated_guidelines"] = True
        
        score = min(score, 1.0)
        
        comment = f"Completed {num_observations} ReAct steps with {len(unique_actions)} different actions"
        if state.guidelines_generated:
            comment += ", successfully generated guidelines"
        
        return MetricResult(
            name="react_execution_quality",
            score=score,
            details=details,
            comment=comment
        )
    
    @staticmethod
    def asset_generation_quality(state: ReActState) -> MetricResult:
        """Evaluate the quality of asset generation.
        
        Args:
            state: ReAct state with asset generation results
            
        Returns:
            Metric result for asset generation quality
        """
        score = 0.0
        details = {}
        
        num_requested = len(state.asset_requests)
        num_generated = len(state.generated_assets)
        
        details["num_requested"] = num_requested
        details["num_generated"] = num_generated
        
        if num_requested == 0:
            return MetricResult(
                name="asset_generation_quality",
                score=0.5,  # Neutral score if no assets requested
                details=details,
                comment="No assets were requested"
            )
        
        # Base score for having requests
        score += 0.2
        
        # Completion rate
        if num_requested > 0:
            completion_rate = num_generated / num_requested
            score += completion_rate * 0.4
            details["completion_rate"] = completion_rate
        
        # Quality of generated assets
        if state.generated_assets:
            total_quality = 0.0
            assets_with_urls = 0
            
            for asset in state.generated_assets:
                if asset.quality_score is not None:
                    total_quality += asset.quality_score
                if asset.image_url:
                    assets_with_urls += 1
            
            # Average quality score
            if state.generated_assets:
                avg_quality = total_quality / len(state.generated_assets)
                score += avg_quality * 0.3
                details["average_quality_score"] = avg_quality
            
            # Success rate (assets with actual URLs)
            success_rate = assets_with_urls / num_generated if num_generated > 0 else 0
            score += success_rate * 0.1
            details["success_rate"] = success_rate
        
        score = min(score, 1.0)
        
        comment = f"Generated {num_generated}/{num_requested} assets"
        if state.generated_assets and details.get("average_quality_score"):
            comment += f" with avg quality {details['average_quality_score']:.2f}"
        
        return MetricResult(
            name="asset_generation_quality",
            score=score,
            details=details,
            comment=comment
        )
    
    @staticmethod
    def workflow_efficiency(state: ReActState) -> MetricResult:
        """Evaluate the efficiency of workflow execution.
        
        Args:
            state: ReAct state
            
        Returns:
            Metric result for workflow efficiency
        """
        score = 0.8  # Start with high efficiency assumption
        details = {}
        
        # Penalize excessive iterations
        total_steps = state.total_steps
        details["total_steps"] = total_steps
        
        if total_steps > 15:
            score -= 0.4
            details["efficiency"] = "low"
        elif total_steps > 10:
            score -= 0.2
            details["efficiency"] = "medium"
        else:
            details["efficiency"] = "high"
        
        # Penalize plan rejections
        if state.plan_approved is False and "reject" in (state.plan_feedback or "").lower():
            score -= 0.2
            details["plan_rejected"] = True
        
        # Bonus for reaching completion
        if state.current_stage in [WorkflowStage.EVALUATION, WorkflowStage.COMPLETED]:
            score += 0.2
            details["completed_successfully"] = True
        
        # Penalize errors
        num_errors = len(state.errors)
        details["num_errors"] = num_errors
        
        if num_errors > 0:
            error_penalty = min(num_errors * 0.1, 0.3)
            score -= error_penalty
            details["error_penalty"] = error_penalty
        
        score = max(score, 0.0)
        
        comment = f"Completed in {total_steps} steps"
        if num_errors > 0:
            comment += f" with {num_errors} errors"
        
        return MetricResult(
            name="workflow_efficiency",
            score=score,
            details=details,
            comment=comment
        )
    
    @staticmethod
    def overall_score(individual_metrics: List[MetricResult]) -> MetricResult:
        """Calculate overall score from individual metrics.
        
        Args:
            individual_metrics: List of individual metric results
            
        Returns:
            Overall metric result
        """
        # Weights for different metrics
        weights = {
            "plan_quality": 0.25,
            "react_execution_quality": 0.30,
            "asset_generation_quality": 0.25,
            "workflow_efficiency": 0.20,
        }
        
        total_score = 0.0
        total_weight = 0.0
        details = {}
        
        for metric in individual_metrics:
            weight = weights.get(metric.name, 0.0)
            if weight > 0:
                total_score += metric.score * weight
                total_weight += weight
                details[f"{metric.name}_score"] = metric.score
                details[f"{metric.name}_weight"] = weight
        
        # Normalize score
        final_score = total_score / total_weight if total_weight > 0 else 0.0
        details["total_weight_used"] = total_weight
        
        return MetricResult(
            name="overall_score",
            score=final_score,
            details=details,
            comment=f"Weighted average of {len(individual_metrics)} metrics: {final_score:.3f}"
        )
