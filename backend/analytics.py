"""
Analytics Module - Cohort analysis, performance metrics, trend analysis.
"""
from __future__ import annotations
from typing import Optional
from datetime import datetime, timedelta
import logging

from backend.database import CaseAnalysis, BenchmarkResult, SessionLocal

logger = logging.getLogger(__name__)


class CohortAnalyzer:
    """Analyze patient cohorts and performance trends."""
    
    @staticmethod
    def get_accuracy_by_category(days: int = 30) -> dict:
        """
        Calculate accuracy metrics by category over time period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with accuracy stats per category
        """
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            results = db.query(BenchmarkResult).filter(
                BenchmarkResult.timestamp >= cutoff_date
            ).all()
            
            categories = {}
            for r in results:
                cat = r.category
                if cat not in categories:
                    categories[cat] = {
                        "total": 0,
                        "correct": 0,
                        "level_accuracy": 0,
                        "emergency_accuracy": 0
                    }
                
                categories[cat]["total"] += 1
                if r.level_correct and r.emergency_correct:
                    categories[cat]["correct"] += 1
                if r.level_correct:
                    categories[cat]["level_accuracy"] += 1
                if r.emergency_correct:
                    categories[cat]["emergency_accuracy"] += 1
            
            # Calculate percentages
            for cat in categories:
                total = max(1, categories[cat]["total"])
                categories[cat]["accuracy"] = categories[cat]["correct"] / total
                categories[cat]["level_accuracy"] /= total
                categories[cat]["emergency_accuracy"] /= total
            
            return categories
        finally:
            db.close()
    
    @staticmethod
    def get_triage_distribution() -> dict:
        """Get distribution of triage levels in recent analyses."""
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            cases = db.query(CaseAnalysis).filter(
                CaseAnalysis.timestamp >= cutoff_date
            ).all()
            
            distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for case in cases:
                distribution[case.triage_level] += 1
            
            return {
                "distribution": distribution,
                "total": sum(distribution.values()),
                "emergency_pct": (distribution[1] + distribution[2]) / max(1, sum(distribution.values()))
            }
        finally:
            db.close()
    
    @staticmethod
    def get_emergency_cases(limit: int = 100) -> list:
        """Get recent emergency cases (L1/L2)."""
        db = SessionLocal()
        try:
            cases = db.query(CaseAnalysis).filter(
                CaseAnalysis.triage_level.in_([1, 2])
            ).order_by(CaseAnalysis.timestamp.desc()).limit(limit).all()
            
            return [
                {
                    "case_id": c.case_id,
                    "timestamp": c.timestamp.isoformat(),
                    "level": c.triage_level,
                    "emergency_type": c.emergency_type,
                    "top_diagnosis": c.top_diagnosis,
                    "red_flags": c.red_flags
                }
                for c in cases
            ]
        finally:
            db.close()
    
    @staticmethod
    def get_top_diagnoses(limit: int = 10, days: int = 30) -> list:
        """Get most common diagnoses in period."""
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            cases = db.query(CaseAnalysis).filter(
                CaseAnalysis.timestamp >= cutoff_date
            ).all()
            
            diagnosis_count = {}
            for case in cases:
                dx = case.top_diagnosis
                diagnosis_count[dx] = diagnosis_count.get(dx, 0) + 1
            
            sorted_dx = sorted(diagnosis_count.items(), key=lambda x: x[1], reverse=True)[:limit]
            return [{"diagnosis": dx, "count": count} for dx, count in sorted_dx]
        finally:
            db.close()
    
    @staticmethod
    def get_high_risk_interactions(limit: int = 50) -> list:
        """Get most common critical drug interactions."""
        db = SessionLocal()
        try:
            cases = db.query(CaseAnalysis).filter(
                CaseAnalysis.ddi_count > 0
            ).order_by(CaseAnalysis.timestamp.desc()).limit(limit).all()
            
            interaction_summary = []
            for case in cases:
                if case.drug_interactions:
                    for ddi in case.drug_interactions:
                        if ddi.get("severity") in ("CONTRAINDICATED", "MAJOR"):
                            interaction_summary.append({
                                "case_id": case.case_id,
                                "drugs": f"{ddi.get('drug_a')} × {ddi.get('drug_b')}",
                                "severity": ddi.get("severity"),
                                "mechanism": ddi.get("mechanism", "")[:100]
                            })
            
            return interaction_summary[:limit]
        finally:
            db.close()
    
    @staticmethod
    def get_performance_trends(days: int = 30) -> dict:
        """Get system performance metrics over time."""
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            cases = db.query(CaseAnalysis).filter(
                CaseAnalysis.timestamp >= cutoff_date
            ).all()
            
            if not cases:
                return {"error": "No data in period"}
            
            avg_time = sum(c.processing_time_ms for c in cases) / len(cases)
            avg_level = sum(c.triage_level for c in cases) / len(cases)
            emergency_count = sum(1 for c in cases if c.is_emergency)
            
            return {
                "avg_processing_time_ms": int(avg_time),
                "avg_triage_level": avg_level,
                "emergency_pct": emergency_count / len(cases),
                "total_cases": len(cases),
                "period_days": days
            }
        finally:
            db.close()


# Convenience functions
def get_dashboard_summary() -> dict:
    """Get summary statistics for dashboard."""
    analyzer = CohortAnalyzer()
    
    return {
        "accuracy_by_category": analyzer.get_accuracy_by_category(30),
        "triage_distribution": analyzer.get_triage_distribution(),
        "top_diagnoses": analyzer.get_top_diagnoses(10, 30),
        "performance_trends": analyzer.get_performance_trends(30),
        "emergency_cases": analyzer.get_emergency_cases(20),
        "high_risk_interactions": analyzer.get_high_risk_interactions(20),
        "timestamp": datetime.utcnow().isoformat()
    }
