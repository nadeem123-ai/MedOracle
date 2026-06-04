"""
A/B Testing Framework - Compare prompts, models, and configurations with statistical significance.
"""
from __future__ import annotations
from typing import Optional, Callable
from datetime import datetime
from enum import Enum
import json
import logging
from scipy import stats

from backend.database import SessionLocal

logger = logging.getLogger(__name__)


class ExperimentStatus(str, Enum):
    """Experiment lifecycle status."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ExperimentResult:
    """Result of an A/B test comparison."""
    
    def __init__(
        self,
        experiment_id: str,
        variant_a: str,
        variant_b: str,
        metric_a: list[float],
        metric_b: list[float],
        metric_name: str = "accuracy"
    ):
        self.experiment_id = experiment_id
        self.variant_a = variant_a
        self.variant_b = variant_b
        self.metric_a = metric_a
        self.metric_b = metric_b
        self.metric_name = metric_name
    
    def calculate_significance(self, alpha: float = 0.05) -> dict:
        """
        Perform statistical significance test (t-test).
        
        Args:
            alpha: Significance level (0.05 = 95% confidence)
            
        Returns:
            Statistical test results
        """
        if len(self.metric_a) < 2 or len(self.metric_b) < 2:
            return {
                "significant": False,
                "p_value": None,
                "reason": "Insufficient samples"
            }
        
        t_stat, p_value = stats.ttest_ind(self.metric_a, self.metric_b)
        significant = p_value < alpha
        
        mean_diff = (sum(self.metric_b) / len(self.metric_b)) - \
                    (sum(self.metric_a) / len(self.metric_a))
        
        return {
            "significant": significant,
            "p_value": p_value,
            "confidence": 1 - alpha,
            "mean_a": sum(self.metric_a) / len(self.metric_a),
            "mean_b": sum(self.metric_b) / len(self.metric_b),
            "mean_diff": mean_diff,
            "winner": self.variant_b if significant and mean_diff > 0 else 
                      self.variant_a if significant and mean_diff < 0 else
                      "tie"
        }
    
    def get_summary(self) -> dict:
        """Get experiment summary."""
        sig = self.calculate_significance()
        return {
            "experiment_id": self.experiment_id,
            "variant_a": self.variant_a,
            "variant_b": self.variant_b,
            "metric_name": self.metric_name,
            "samples_a": len(self.metric_a),
            "samples_b": len(self.metric_b),
            "significance": sig,
            "timestamp": datetime.utcnow().isoformat()
        }


class ABTestManager:
    """Manage A/B testing experiments."""
    
    def __init__(self):
        self.experiments: dict[str, dict] = {}
    
    def create_experiment(
        self,
        experiment_id: str,
        variant_a_config: dict,
        variant_b_config: dict,
        hypothesis: str,
        target_samples: int = 100
    ) -> dict:
        """
        Create a new A/B test experiment.
        
        Args:
            experiment_id: Unique experiment ID
            variant_a_config: Configuration for control variant
            variant_b_config: Configuration for test variant
            hypothesis: Hypothesis statement
            target_samples: Target number of samples per variant
            
        Returns:
            Experiment metadata
        """
        experiment = {
            "id": experiment_id,
            "status": ExperimentStatus.ACTIVE.value,
            "created_at": datetime.utcnow().isoformat(),
            "hypothesis": hypothesis,
            "variant_a": variant_a_config,
            "variant_b": variant_b_config,
            "target_samples": target_samples,
            "samples_a": 0,
            "samples_b": 0,
            "results_a": [],
            "results_b": []
        }
        
        self.experiments[experiment_id] = experiment
        logger.info(f"Created experiment: {experiment_id}")
        logger.info(f"Hypothesis: {hypothesis}")
        
        return experiment
    
    def record_result(
        self,
        experiment_id: str,
        variant: str,
        metric_value: float
    ) -> bool:
        """
        Record a result for an experiment variant.
        
        Args:
            experiment_id: Experiment ID
            variant: "a" or "b"
            metric_value: Metric value to record
            
        Returns:
            True if result recorded, False if experiment complete
        """
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        exp = self.experiments[experiment_id]
        
        if variant == "a":
            exp["results_a"].append(metric_value)
            exp["samples_a"] += 1
        elif variant == "b":
            exp["results_b"].append(metric_value)
            exp["samples_b"] += 1
        else:
            raise ValueError("Variant must be 'a' or 'b'")
        
        # Check if experiment should be marked complete
        if exp["samples_a"] >= exp["target_samples"] and \
           exp["samples_b"] >= exp["target_samples"]:
            exp["status"] = ExperimentStatus.COMPLETED.value
            exp["completed_at"] = datetime.utcnow().isoformat()
        
        return exp["status"] == ExperimentStatus.ACTIVE.value
    
    def get_results(self, experiment_id: str) -> ExperimentResult:
        """Get statistical results for experiment."""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        exp = self.experiments[experiment_id]
        
        return ExperimentResult(
            experiment_id=experiment_id,
            variant_a=exp["variant_a"].get("name", "control"),
            variant_b=exp["variant_b"].get("name", "variant"),
            metric_a=exp["results_a"],
            metric_b=exp["results_b"]
        )
    
    def is_complete(self, experiment_id: str) -> bool:
        """Check if experiment reached statistical significance."""
        result = self.get_results(experiment_id)
        sig = result.calculate_significance()
        return sig["significant"]


# Prompt comparison configurations for common experiments

PROMPT_EXPERIMENTS = {
    "diagnosis_precision": {
        "hypothesis": "Structured prompt improves diagnostic precision",
        "variants": {
            "a": {
                "name": "baseline",
                "system_message": "Generate differential diagnoses",
                "temperature": 0.7
            },
            "b": {
                "name": "structured",
                "system_message": """Generate exactly 5 differential diagnoses.
Format each as JSON: {"name": "...", "icd10": "...", "confidence": 0.0-1.0}
Order by likelihood. Consider rare presentations.""",
                "temperature": 0.5
            }
        }
    },
    "triage_accuracy": {
        "hypothesis": "ESI protocol prompt improves triage accuracy",
        "variants": {
            "a": {
                "name": "baseline",
                "system_message": "Assign triage level 1-5",
                "temperature": 0.3
            },
            "b": {
                "name": "esi_protocol",
                "system_message": """Use ESI Triage Protocol:
- L1: High-risk situation (immediate threat to life)
- L2: High-risk OR resource-intensive
- L3: Acute illness/injury, stable
- L4: Minor illness/injury
- L5: Minor illness/injury, minimal resources""",
                "temperature": 0.3
            }
        }
    }
}


def create_comparison_experiment(
    experiment_name: str,
    config_a: dict,
    config_b: dict,
    comparison_fn: Callable
) -> dict:
    """
    Create and run a simple comparison experiment.
    
    Args:
        experiment_name: Name of experiment
        config_a: Config for variant A
        config_b: Config for variant B
        comparison_fn: Function to run comparison (takes config, returns metric)
        
    Returns:
        Results of comparison
    """
    logger.info(f"Starting comparison experiment: {experiment_name}")
    
    manager = ABTestManager()
    manager.create_experiment(
        experiment_id=experiment_name,
        variant_a_config=config_a,
        variant_b_config=config_b,
        hypothesis=f"Compare {experiment_name} variants",
        target_samples=50
    )
    
    results_a = []
    results_b = []
    
    # Run comparison (simplified - in production would run on actual data)
    for i in range(50):
        metric_a = comparison_fn(config_a)
        metric_b = comparison_fn(config_b)
        results_a.append(metric_a)
        results_b.append(metric_b)
    
    return {
        "experiment": experiment_name,
        "variant_a_mean": sum(results_a) / len(results_a),
        "variant_b_mean": sum(results_b) / len(results_b),
        "improvement": ((sum(results_b) / len(results_b)) - (sum(results_a) / len(results_a))) / max(1e-6, sum(results_a) / len(results_a)) * 100
    }
