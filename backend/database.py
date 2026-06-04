"""
Database Layer - SQLAlchemy ORM for case persistence and analytics.

Models:
  - CaseAnalysis: Individual case analysis records
  - BenchmarkResult: Benchmark test results
  - UserAudit: User access and action audit log
  - Alert: Critical findings and alerts
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
import os

from sqlalchemy import create_engine, Column, String, DateTime, Integer, Float, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import logging

logger = logging.getLogger(__name__)

# Database URL - use SQLite by default, PostgreSQL for production
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./MedOracle.db")

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DB_URL else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class CaseAnalysis(Base):
    """Individual clinical case analysis record."""
    __tablename__ = "case_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, unique=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    patient_input = Column(String)
    medications = Column(JSON)
    
    # Triage results
    triage_level = Column(Integer)
    triage_label = Column(String)
    is_emergency = Column(Boolean)
    emergency_type = Column(String)
    red_flags = Column(JSON)
    
    # Diagnosis
    diagnoses = Column(JSON)
    top_diagnosis = Column(String)
    top_icd10 = Column(String)
    
    # Treatment
    treatment = Column(JSON)
    evidence_grade = Column(String)
    
    # Drug interactions
    drug_interactions = Column(JSON)
    ddi_count = Column(Integer)
    
    # Performance
    processing_time_ms = Column(Integer)
    
    # Metadata
    user_id = Column(String, nullable=True)
    category = Column(String, nullable=True)
    notes = Column(String, nullable=True)


class BenchmarkResult(Base):
    """Benchmark test results for accuracy tracking."""
    __tablename__ = "benchmark_results"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    case_name = Column(String)
    category = Column(String)
    expected_level = Column(Integer)
    actual_level = Column(Integer)
    level_correct = Column(Boolean)
    expected_emergency = Column(Boolean)
    actual_emergency = Column(Boolean)
    emergency_correct = Column(Boolean)
    accuracy = Column(Float)
    user_id = Column(String, nullable=True)


class UserAudit(Base):
    """Audit trail for user actions and access."""
    __tablename__ = "user_audit"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(String, index=True)
    action = Column(String)  # "analyze", "benchmark", "export", "login"
    resource = Column(String)  # case_id, benchmark_id, etc.
    status = Column(String)  # "success", "failure"
    details = Column(JSON, nullable=True)


class Alert(Base):
    """Critical findings and alerts."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    case_id = Column(String, index=True)
    alert_type = Column(String)  # "emergency", "ddi", "contraindication", "guideline_deviation"
    severity = Column(String)  # "critical", "high", "medium", "low"
    message = Column(String)
    resolved = Column(Boolean, default=False)
    user_id = Column(String, nullable=True)


class SystemHealth(Base):
    """System health and performance metrics."""
    __tablename__ = "system_health"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    avg_response_time_ms = Column(Float)
    total_cases_analyzed = Column(Integer)
    avg_accuracy = Column(Float)
    api_uptime_pct = Column(Float)
    active_users = Column(Integer)


# Create all tables
Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_case_analysis(case_data: dict, user_id: Optional[str] = None) -> CaseAnalysis:
    """Save case analysis to database."""
    db = SessionLocal()
    try:
        case_record = CaseAnalysis(
            case_id=case_data.get("case_id", f"case_{datetime.utcnow().timestamp()}"),
            patient_input=case_data.get("patient_input", "")[:1000],
            medications=case_data.get("medications", []),
            triage_level=int(case_data.get("triage", {}).get("level", 3)),
            triage_label=case_data.get("triage", {}).get("label", "URGENT"),
            is_emergency=case_data.get("is_emergency", False),
            emergency_type=case_data.get("triage", {}).get("emergency_type", "NONE"),
            red_flags=case_data.get("triage", {}).get("red_flags", []),
            diagnoses=case_data.get("diagnoses", []),
            top_diagnosis=case_data.get("diagnoses", [{}])[0].get("name", "Unknown"),
            top_icd10=case_data.get("diagnoses", [{}])[0].get("icd10", ""),
            treatment=case_data.get("treatment", {}),
            evidence_grade=case_data.get("treatment", {}).get("evidence_grade", "?"),
            drug_interactions=case_data.get("drug_interactions", []),
            ddi_count=len(case_data.get("drug_interactions", [])),
            processing_time_ms=sum(case_data.get("processing_time_ms", {}).values()),
            user_id=user_id,
        )
        db.add(case_record)
        db.commit()
        db.refresh(case_record)
        logger.info(f"Case {case_record.case_id} saved to database")
        return case_record
    except Exception as e:
        logger.error(f"Error saving case: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def get_case_history(user_id: Optional[str] = None, limit: int = 100) -> list[CaseAnalysis]:
    """Retrieve case history from database."""
    db = SessionLocal()
    try:
        query = db.query(CaseAnalysis)
        if user_id:
            query = query.filter(CaseAnalysis.user_id == user_id)
        return query.order_by(CaseAnalysis.timestamp.desc()).limit(limit).all()
    finally:
        db.close()


def get_accuracy_by_category(user_id: Optional[str] = None) -> dict:
    """Calculate accuracy metrics by category."""
    db = SessionLocal()
    try:
        query = db.query(BenchmarkResult)
        if user_id:
            query = query.filter(BenchmarkResult.user_id == user_id)
        
        results = query.all()
        categories = {}
        
        for r in results:
            cat = r.category
            if cat not in categories:
                categories[cat] = {"correct": 0, "total": 0}
            categories[cat]["total"] += 1
            if r.level_correct and r.emergency_correct:
                categories[cat]["correct"] += 1
        
        return {
            cat: {
                "accuracy": categories[cat]["correct"] / max(1, categories[cat]["total"]),
                "count": categories[cat]["total"]
            }
            for cat in categories
        }
    finally:
        db.close()
