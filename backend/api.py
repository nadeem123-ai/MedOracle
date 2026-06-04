"""
MedOracle FastAPI Backend - Production REST API
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import Optional
import uuid

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from pipeline import run_pipeline
from backend.database import (
    CaseAnalysis, save_case_analysis, get_case_history, 
    get_accuracy_by_category, get_db, SessionLocal, BenchmarkResult
)
from backend.auth import get_current_user, create_access_token, User, require_role
from backend.monitoring import monitor, setup_logging, TimingContext

# Setup logging
setup_logging("INFO")
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MedOracle API",
    description="Production-grade clinical decision support REST API",
    version="2.0.0"
)

# CORS configuration for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic Models ──────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """User login request."""
    email: str
    password: str
    role: Optional[str] = "user"


class LoginResponse(BaseModel):
    """Login response with JWT token."""
    access_token: str
    token_type: str
    user_id: str


class AnalysisRequest(BaseModel):
    """Clinical analysis request."""
    patient_input: str
    medications: list[str]
    category: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Clinical analysis response."""
    case_id: str
    triage_level: int
    triage_label: str
    diagnoses: list
    treatment: dict
    drug_interactions: list
    processing_time_ms: int
    is_emergency: bool


class HealthResponse(BaseModel):
    """System health status."""
    status: str
    uptime_seconds: int
    total_requests: int
    error_rate: float


# ── Authentication Endpoints ──────────────────────────────────────────────────

@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login endpoint - returns JWT token.
    
    In production, verify credentials against a user database.
    This is a demo implementation.
    """
    with TimingContext("login"):
        # Demo: accept any email with "demo" password
        if request.password != "demo":
            monitor.log_audit(request.email, "login", "auth", "failed")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user_id = str(uuid.uuid4())[:8]
        token = create_access_token(user_id, request.email, request.role)
        
        monitor.log_audit(user_id, "login", "auth", "success")
        
        return LoginResponse(
            access_token=token,
            token_type="bearer",
            user_id=user_id
        )


# ── Analysis Endpoints ────────────────────────────────────────────────────────

@app.post("/analysis/run", response_model=AnalysisResponse)
async def run_analysis(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Run clinical analysis on patient presentation.
    
    Requires authentication. Results are persisted to database.
    """
    case_id = str(uuid.uuid4())[:12]
    
    try:
        with TimingContext(f"analysis_{case_id}"):
            # Run pipeline
            result = run_pipeline(request.patient_input, request.medications)
            
            # Add case_id and user_id
            result["case_id"] = case_id
            result["user_id"] = current_user.user_id
            result["category"] = request.category
            
            # Save to database
            db_record = save_case_analysis(result, current_user.user_id)
            
            # Log audit trail
            monitor.log_audit(
                current_user.user_id,
                "analysis",
                case_id,
                "success",
                {"triage_level": result.get("triage", {}).get("level")}
            )
            
            # Log metrics
            monitor.log_analysis(
                case_id,
                result.get("triage", {}).get("level", 3),
                sum(result.get("processing_time_ms", {}).values()),
                current_user.user_id,
                request.category
            )
            
            return AnalysisResponse(
                case_id=case_id,
                triage_level=result.get("triage", {}).get("level", 3),
                triage_label=result.get("triage", {}).get("label", "URGENT"),
                diagnoses=result.get("diagnoses", []),
                treatment=result.get("treatment", {}),
                drug_interactions=result.get("drug_interactions", []),
                processing_time_ms=sum(result.get("processing_time_ms", {}).values()),
                is_emergency=result.get("is_emergency", False)
            )
    
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        monitor.log_audit(current_user.user_id, "analysis", case_id, "failed", {"error": str(e)})
        raise HTTPException(status_code=500, detail="Analysis failed")


@app.get("/analysis/history")
async def get_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get user's case analysis history."""
    with TimingContext("get_history"):
        cases = get_case_history(current_user.user_id, limit)
        return {
            "count": len(cases),
            "cases": [
                {
                    "case_id": c.case_id,
                    "timestamp": c.timestamp.isoformat(),
                    "triage_level": c.triage_level,
                    "top_diagnosis": c.top_diagnosis,
                    "is_emergency": c.is_emergency,
                    "processing_time_ms": c.processing_time_ms
                }
                for c in cases
            ]
        }


@app.get("/analytics/accuracy")
async def get_accuracy(
    current_user: User = Depends(require_role("clinician"))
):
    """Get accuracy metrics by category (clinician+ only)."""
    with TimingContext("get_accuracy"):
        accuracy_data = get_accuracy_by_category(current_user.user_id)
        return {
            "accuracy_by_category": accuracy_data,
            "user_id": current_user.user_id
        }


# ── Health & Monitoring ──────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """System health status endpoint."""
    health = monitor.get_health()
    return HealthResponse(**health)


@app.get("/metrics")
async def get_metrics(
    current_user: User = Depends(require_role("admin"))
):
    """Get detailed system metrics (admin only)."""
    return monitor.metrics


# ── Middleware for logging ──────────────────────────────────────────────────────

@app.middleware("http")
async def log_requests(request, call_next):
    """Middleware to log all HTTP requests."""
    import time
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    
    monitor.log_request(
        endpoint=request.url.path,
        method=request.method,
        status_code=response.status_code,
        response_time_ms=int(process_time),
        user_id=getattr(request.state, "user_id", None)
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response


# ── Root endpoint ────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """API root endpoint with documentation."""
    return {
        "name": "MedOracle  API",
        "version": "2.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health"
    }


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
