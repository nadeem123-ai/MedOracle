"""
Real-Time Alerts System - Critical findings notification and management.
"""
from __future__ import annotations
from typing import Optional, List
from datetime import datetime
import logging
from enum import Enum

from backend.database import Alert, SessionLocal

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlertType(str, Enum):
    """Types of alerts that can be triggered."""
    EMERGENCY = "emergency"  # Triage L1 or L2
    DDI_CONTRAINDICATED = "ddi_contraindicated"  # Major drug interaction
    ALLERGY_RISK = "allergy_risk"  # Allergy flag
    GUIDELINE_DEVIATION = "guideline_deviation"  # Treatment not per guidelines


class AlertManager:
    """Manage clinical alerts and notifications."""
    
    @staticmethod
    def create_alert(
        case_id: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        user_id: Optional[str] = None
    ) -> Alert:
        """
        Create a new alert.
        
        Args:
            case_id: Associated case ID
            alert_type: Type of alert
            severity: Severity level
            message: Alert message
            user_id: User who should be notified
            
        Returns:
            Created alert record
        """
        db = SessionLocal()
        try:
            alert = Alert(
                case_id=case_id,
                alert_type=alert_type.value,
                severity=severity.value,
                message=message,
                user_id=user_id,
                resolved=False
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)
            
            logger.warning(
                f"Alert created: {alert_type.value} ({severity.value}) - {message}"
            )
            
            # In production, send notifications here
            AlertManager._send_notification(alert)
            
            return alert
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    @staticmethod
    def evaluate_case_alerts(case_result: dict) -> List[str]:
        """
        Evaluate a case analysis result and create appropriate alerts.
        
        Args:
            case_result: Clinical analysis result dict
            
        Returns:
            List of created alert IDs
        """
        alerts_created = []
        case_id = case_result.get("case_id", "unknown")
        user_id = case_result.get("user_id")
        
        # Check for emergency conditions
        triage_level = case_result.get("triage", {}).get("level")
        if triage_level in (1, 2):
            alert = AlertManager.create_alert(
                case_id,
                AlertType.EMERGENCY,
                AlertSeverity.CRITICAL if triage_level == 1 else AlertSeverity.HIGH,
                f"Emergency: ESI Level {triage_level} patient",
                user_id
            )
            alerts_created.append(str(alert.id))
        
        # Check for contraindicated drug interactions
        drug_interactions = case_result.get("drug_interactions", [])
        for ddi in drug_interactions:
            if ddi.get("severity") == "CONTRAINDICATED":
                alert = AlertManager.create_alert(
                    case_id,
                    AlertType.DDI_CONTRAINDICATED,
                    AlertSeverity.CRITICAL,
                    f"CONTRAINDICATED: {ddi.get('drug_a')} + {ddi.get('drug_b')}",
                    user_id
                )
                alerts_created.append(str(alert.id))
            elif ddi.get("severity") == "MAJOR":
                alert = AlertManager.create_alert(
                    case_id,
                    AlertType.DDI_CONTRAINDICATED,
                    AlertSeverity.HIGH,
                    f"MAJOR interaction: {ddi.get('drug_a')} + {ddi.get('drug_b')}",
                    user_id
                )
                alerts_created.append(str(alert.id))
        
        # Check for red flags
        red_flags = case_result.get("triage", {}).get("red_flags", [])
        for flag in red_flags:
            if flag in ("chest pain", "difficulty breathing", "altered mental status", "unresponsive"):
                alert = AlertManager.create_alert(
                    case_id,
                    AlertType.EMERGENCY,
                    AlertSeverity.HIGH,
                    f"Red flag present: {flag}",
                    user_id
                )
                alerts_created.append(str(alert.id))
        
        return alerts_created
    
    @staticmethod
    def get_unresolved_alerts(user_id: Optional[str] = None, limit: int = 100) -> list:
        """Get all unresolved alerts."""
        db = SessionLocal()
        try:
            query = db.query(Alert).filter(Alert.resolved == False)
            if user_id:
                query = query.filter(Alert.user_id == user_id)
            
            alerts = query.order_by(Alert.timestamp.desc()).limit(limit).all()
            
            return [
                {
                    "id": a.id,
                    "case_id": a.case_id,
                    "alert_type": a.alert_type,
                    "severity": a.severity,
                    "message": a.message,
                    "timestamp": a.timestamp.isoformat()
                }
                for a in alerts
            ]
        finally:
            db.close()
    
    @staticmethod
    def resolve_alert(alert_id: int):
        """Mark an alert as resolved."""
        db = SessionLocal()
        try:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if alert:
                alert.resolved = True
                db.commit()
                logger.info(f"Alert {alert_id} resolved")
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            db.rollback()
        finally:
            db.close()
    
    @staticmethod
    def _send_notification(alert: Alert):
        """
        Send alert notification (placeholder for production implementation).
        
        In production, implement:
        - Email notifications
        - SMS alerts for critical
        - Slack/Teams integration
        - Push notifications
        """
        logger.info(
            f"[NOTIFICATION] To: {alert.user_id}, "
            f"Type: {alert.alert_type}, "
            f"Severity: {alert.severity}, "
            f"Message: {alert.message}"
        )
        # Placeholder - implement actual notification service
