"""
SafetyAgent — emergency triage specialist using ESI protocols.

Runs first in the pipeline. Detects life-threatening emergencies,
assigns ESI triage level (1-5), and identifies red flags requiring
immediate intervention.

Triage Levels:
  1 (IMMEDIATE): Life-saving intervention needed (cardiac arrest, unresponsiveness)
  2 (EMERGENT): High-risk situations (ongoing chest pain, stroke symptoms, shock)
  3 (URGENT): Moderate severity (fever, abdominal pain, minor injury)
  4 (LESS_URGENT): Minor issues (minor cuts, stable vitals)
  5 (NON_URGENT): Trivial complaints (common cold)
"""
from __future__ import annotations
import time
import logging
from typing import Any, Dict

from utils.base_agent import _get_llm, parse_json_response, is_rate_limited
from utils.rate_limit_fallback import RateLimitFallback
from utils.state import ClinicalState

logger = logging.getLogger(__name__)

SAFETY_PROMPT = """You are an expert emergency triage specialist using ESI (Emergency Severity Index) protocols.

TRIAGE LEVELS:
- Level 1 (IMMEDIATE): Requires immediate life-saving intervention (STEMI, massive hemorrhage, respiratory failure, unresponsive, shock)
- Level 2 (EMERGENT): High-risk situations needing rapid evaluation (ongoing chest pain, altered mental status, uncontrolled hemorrhage, signs of shock/stroke)
- Level 3 (URGENT): Stable but needs evaluation within 1-2 hours (moderate severity, stable vitals)
- Level 4 (LESS_URGENT): Minor issues, can wait 1-2 hours
- Level 5 (NON_URGENT): Minor injuries/symptoms

HYPERTENSIVE CRISIS CLASSIFICATION:
- Hypertensive EMERGENCY (L1/L2): BP crisis WITH end-organ damage/symptoms (papilledema, altered mental status, ACS features, renal failure, pulmonary edema)
- Hypertensive URGENCY (L3): Elevated BP WITHOUT acute end-organ damage; can be managed within hours

Patient presentation:
{patient_input}

Respond with ONLY this JSON:
{{
  "level": "1" | "2" | "3" | "4" | "5",
  "label": "IMMEDIATE" | "EMERGENT" | "URGENT" | "LESS_URGENT" | "NON_URGENT",
  "reasoning": "Concise clinical reasoning for triage level",
  "emergency_type": "STEMI" | "STROKE" | "SEPSIS" | "ANAPHYLAXIS" | "TRAUMA" | "RESPIRATORY_FAILURE" | "HTN_EMERGENCY" | "NONE",
  "red_flags": ["critical finding 1", "critical finding 2"],
  "vitals_assessment": "Brief assessment of vital signs and stability",
  "is_emergency": true | false,
  "immediate_actions": ["action if L1-L2", "action 2"]
}}"""


def run_safety_agent(state: ClinicalState) -> Dict[str, Any]:
    """
    Perform emergency triage assessment on patient presentation.
    
    Uses ESI protocol to classify urgency (1-5) and detect life-threatening
    conditions requiring immediate intervention.
    
    Args:
        state: Clinical state dict containing patient_input and other context
        
    Returns:
        Dict with keys:
            - triage: Full triage assessment (level, label, emergency_type, etc.)
            - is_emergency: Boolean flag for emergency conditions (L1-L2)
            - agent_logs: Processing log entries
            - processing_time_ms: Execution time in milliseconds
            
    Raises:
        Exception: If LLM call fails or response parsing fails
    """
    t0 = time.time()
    patient_input = state.get("patient_input", "")
    
    try:
        llm = _get_llm()
        prompt = SAFETY_PROMPT.format(patient_input=patient_input)
        response = llm.invoke(prompt)
        triage = parse_json_response(response.content)
        
        elapsed = int((time.time() - t0) * 1000)
        log_entry = f"[SafetyAgent] Triage L{triage.get('level','?')} — {triage.get('label','?')} ({elapsed}ms)"
        logger.info(log_entry, extra={"triage_level": triage.get("level")})
        
        return {
            "triage": triage,
            "is_emergency": triage.get("is_emergency", False),
            "agent_logs": [log_entry],
            "processing_time_ms": {"safety_agent": elapsed},
        }
    except Exception as e:
        elapsed = int((time.time() - t0) * 1000)
        
        # Check if rate limited
        if is_rate_limited(e):
            logger.warning(f"Rate limited - using fallback triage ({elapsed}ms)")
            fallback = RateLimitFallback.get_safety_fallback(patient_input)
            fallback["processing_time_ms"] = {"safety_agent": elapsed}
            return fallback
        
        # Other errors: return safe default (most urgent)
        logger.error(f"Safety agent error: {e}", exc_info=True)
        return {
            "triage": {
                "level": "2",
                "label": "EMERGENT",
                "is_emergency": True,
                "reasoning": "Error in triage assessment",
            },
            "is_emergency": True,
            "agent_logs": [f"[SafetyAgent] Error: {str(e)[:100]}"],
            "processing_time_ms": {"safety_agent": elapsed},
        }
