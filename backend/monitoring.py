"""
Monitoring & Logging - Structured logging, metrics, audit trails.
"""
from __future__ import annotations
import logging
import json
from datetime import datetime
from typing import Optional, Any
import time

# Configure structured logging
def setup_logging(log_level: str = "INFO"):
    """Setup structured logging for production."""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("MedOracle.log"),
            logging.StreamHandler()
        ]
    )


class PerformanceMonitor:
    """Track API and pipeline performance metrics."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics = {
            "total_requests": 0,
            "total_errors": 0,
            "avg_response_time": 0,
            "start_time": datetime.utcnow()
        }
    
    def log_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: int,
        user_id: Optional[str] = None
    ):
        """Log API request with metrics."""
        self.metrics["total_requests"] += 1
        
        if status_code >= 400:
            self.metrics["total_errors"] += 1
        
        self.logger.info(
            json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "event": "api_request",
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "response_time_ms": response_time_ms,
                "user_id": user_id
            })
        )
    
    def log_analysis(
        self,
        case_id: str,
        triage_level: int,
        processing_time_ms: int,
        user_id: Optional[str] = None,
        category: Optional[str] = None
    ):
        """Log clinical analysis completion."""
        self.logger.info(
            json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "event": "analysis_complete",
                "case_id": case_id,
                "triage_level": triage_level,
                "processing_time_ms": processing_time_ms,
                "user_id": user_id,
                "category": category
            })
        )
    
    def log_audit(
        self,
        user_id: str,
        action: str,
        resource: str,
        status: str,
        details: Optional[dict] = None
    ):
        """Log user action audit trail."""
        self.logger.info(
            json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "event": "audit",
                "user_id": user_id,
                "action": action,
                "resource": resource,
                "status": status,
                "details": details
            })
        )
    
    def get_health(self) -> dict:
        """Get system health status."""
        uptime_seconds = (datetime.utcnow() - self.metrics["start_time"]).total_seconds()
        error_rate = self.metrics["total_errors"] / max(1, self.metrics["total_requests"])
        
        return {
            "status": "healthy" if error_rate < 0.05 else "degraded",
            "uptime_seconds": int(uptime_seconds),
            "total_requests": self.metrics["total_requests"],
            "error_rate": error_rate,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global monitor instance
monitor = PerformanceMonitor()


class TimingContext:
    """Context manager for measuring execution time."""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_ms = int((time.time() - self.start_time) * 1000)
        logging.getLogger(__name__).debug(
            f"[TIMING] {self.name}: {elapsed_ms}ms"
        )
