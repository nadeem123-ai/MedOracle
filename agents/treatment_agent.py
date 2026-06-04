"""
TreatmentAgent — generates evidence-graded treatment plans (Level A–D).
Runs last after diagnosis + drug agents complete.
"""
from __future__ import annotations
import time
import logging
from typing import Any, Dict
from utils.base_agent import _get_llm, parse_json_response, is_rate_limited
from utils.rate_limit_fallback import RateLimitFallback
from utils.state import ClinicalState

logger = logging.getLogger(__name__)

TREATMENT_PROMPT = """You are an evidence-based medicine specialist. Create a comprehensive treatment plan.

Patient: {patient_input}
Top diagnosis: {top_diagnosis} (ICD-10: {icd10})
Triage level: {triage_level}
Current medications: {medications}
High-risk interactions: {interactions}
RAG context: {rag_context}

Respond ONLY with this JSON:
{{
  "evidence_grade": "A" | "B" | "C" | "D",
  "grade_explanation": "Why this grade (A=RCT, B=cohort, C=case series, D=expert opinion)",
  "immediate": ["action 1 (within minutes)", "action 2"],
  "short_term": ["action within hours-days", "action"],
  "long_term": ["follow-up plan", "monitoring"],
  "medications_recommended": [
    {{
      "drug": "Drug name",
      "dose": "Dose and route",
      "frequency": "Frequency",
      "duration": "Duration",
      "rationale": "Why this drug"
    }}
  ],
  "contraindications": ["list contraindications given patient's meds"],
  "monitoring": ["what to monitor", "target values"],
  "patient_education": ["key points for patient"],
  "referrals": ["specialist referrals needed"],
  "prognosis": "Expected outcome with treatment"
}}"""


def run_treatment_agent(state: ClinicalState) -> Dict[str, Any]:
    t0 = time.time()
    
    try:
        llm = _get_llm()
        
        diagnoses = state.get("diagnoses", [])
        top_dx = diagnoses[0] if diagnoses else {}
        triage = state.get("triage", {})
        interactions = state.get("drug_interactions", [])
        high_risk = [i.get("drug_a","") for i in interactions if i.get("severity") in ("CONTRAINDICATED","MAJOR")]
        
        prompt = TREATMENT_PROMPT.format(
            patient_input=state.get("patient_input", ""),
            top_diagnosis=top_dx.get("name", "Unknown"),
            icd10=top_dx.get("icd10", ""),
            triage_level=triage.get("level", "3"),
            medications=", ".join(state.get("medications", [])) or "None",
            interactions=", ".join(high_risk) or "None",
            rag_context=state.get("rag_context", "No additional context")[:500],
        )
        response = llm.invoke(prompt)
        treatment = parse_json_response(response.content)
        
        elapsed = int((time.time() - t0) * 1000)
        log_entry = f"[TreatmentAgent] Evidence Grade {treatment.get('evidence_grade','?')} plan generated ({elapsed}ms)"
        logger.info(log_entry)
        
        return {
            "treatment": treatment,
            "agent_logs": [log_entry],
            "processing_time_ms": {"treatment_agent": elapsed},
        }
    except Exception as e:
        elapsed = int((time.time() - t0) * 1000)
        
        # Check if rate limited
        if is_rate_limited(e):
            logger.warning(f"Rate limited - using template treatment ({elapsed}ms)")
            diagnoses = state.get("diagnoses", [])
            top_dx = diagnoses[0].get("name", "Unknown") if diagnoses else "Unknown"
            triage_level = state.get("triage", {}).get("level", 3)
            fallback = RateLimitFallback.get_treatment_fallback(int(triage_level), top_dx)
            fallback["processing_time_ms"] = {"treatment_agent": elapsed}
            return fallback
        
        # Other errors: return safe default
        logger.error(f"Treatment agent error: {e}", exc_info=True)
        return {
            "treatment": {
                "evidence_grade": "?",
                "plan": "Treatment plan generation failed",
                "medications_recommended": [],
                "key_actions": []
            },
            "agent_logs": [f"[TreatmentAgent] Error: {str(e)[:100]}"],
            "processing_time_ms": {"treatment_agent": elapsed},
        }
