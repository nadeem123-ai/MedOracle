"""
DiagnosisAgent — generates ranked differential diagnoses with validated ICD-10 codes.
Runs in parallel with DrugAgent after SafetyAgent.
"""
from __future__ import annotations
import time
import logging
from typing import Any, Dict

from utils.base_agent import _get_llm, parse_json_response, is_rate_limited
from utils.rate_limit_fallback import RateLimitFallback
from utils.state import ClinicalState

logger = logging.getLogger(__name__)

DIAGNOSIS_PROMPT = """You are an expert clinician. Analyze the clinical presentation and generate a ranked differential diagnosis list.
Use REAL ICD-10-CM codes (e.g. I21.0 for STEMI anterior wall, J18.9 for pneumonia unspecified).

Patient presentation:
{patient_input}

Triage level: {triage_level}
Emergency type: {emergency_type}

Respond with ONLY this JSON:
{{
  "diagnoses": [
    {{
      "rank": 1,
      "name": "Diagnosis name",
      "icd10": "X00.0",
      "icd10_description": "Full ICD-10 description",
      "probability": "High/Medium/Low",
      "confidence_pct": 75,
      "reasoning": "Clinical reasoning...",
      "key_findings": ["finding1", "finding2"],
      "supporting_tests": ["ECG", "Troponin"],
      "against_diagnosis": ["reason it might not be this"]
    }}
  ]
}}

Include 3-5 diagnoses ordered by probability."""

def run_diagnosis_agent(state: ClinicalState) -> Dict[str, Any]:
    t0 = time.time()
    patient_input = state.get("patient_input", "")
    
    try:
        llm = _get_llm()
        
        triage = state.get("triage", {})
        prompt = DIAGNOSIS_PROMPT.format(
            patient_input=patient_input,
            triage_level=triage.get("level", "3"),
            emergency_type=triage.get("emergency_type", "NONE"),
        )
        response = llm.invoke(prompt)
        parsed = parse_json_response(response.content)
        diagnoses = parsed.get("diagnoses", [])
        
        elapsed = int((time.time() - t0) * 1000)
        log_entry = f"[DiagnosisAgent] {len(diagnoses)} differentials generated ({elapsed}ms)"
        logger.info(log_entry)
        
        return {
            "diagnoses": diagnoses,
            "agent_logs": [log_entry],
            "processing_time_ms": {"diagnosis_agent": elapsed},
        }
    except Exception as e:
        elapsed = int((time.time() - t0) * 1000)
        
        # Check if rate limited
        if is_rate_limited(e):
            logger.warning(f"Rate limited - using fallback diagnoses ({elapsed}ms)")
            fallback = RateLimitFallback.get_diagnosis_fallback(patient_input)
            fallback["processing_time_ms"] = {"diagnosis_agent": elapsed}
            return fallback
        
        # Other errors: return empty diagnoses
        logger.error(f"Diagnosis agent error: {e}", exc_info=True)
        return {
            "diagnoses": [],
            "agent_logs": [f"[DiagnosisAgent] Error: {str(e)[:100]}"],
            "processing_time_ms": {"diagnosis_agent": elapsed},
        }
