"""
DrugAgent — DDI severity ranking (CONTRAINDICATED → MAJOR → MODERATE → MINOR).
Enriches with OpenFDA label data where available. Runs parallel to DiagnosisAgent.
"""
from __future__ import annotations
import time
import logging
import requests
from typing import Any, Dict, List

from utils.base_agent import _get_llm, parse_json_response, is_rate_limited
from utils.rate_limit_fallback import RateLimitFallback
from utils.state import ClinicalState

logger = logging.getLogger(__name__)

DDI_PROMPT = """You are a clinical pharmacist expert. Analyze drug-drug interactions for the given medication list.

Medications: {medications}
Top diagnosis: {top_diagnosis}

For each significant interaction, provide ONLY this JSON:
{{
  "interactions": [
    {{
      "drug_a": "Drug name",
      "drug_b": "Drug name",
      "severity": "CONTRAINDICATED" | "MAJOR" | "MODERATE" | "MINOR",
      "mechanism": "Pharmacokinetic/pharmacodynamic mechanism...",
      "clinical_effect": "What happens clinically...",
      "management": "How to manage this interaction...",
      "monitoring_parameters": ["parameter1", "parameter2"],
      "alternative": "Safer alternative if available"
    }}
  ],
  "high_risk_drugs": ["drugs needing extra caution"],
  "renal_dosing_needed": true | false,
  "hepatic_dosing_needed": true | false
}}

If no significant interactions, return {{"interactions": [], "high_risk_drugs": [], "renal_dosing_needed": false, "hepatic_dosing_needed": false}}"""


def _fetch_openfda_label(drug_name: str) -> str:
    """Fetch drug warnings from OpenFDA (free API)."""
    try:
        url = f"https://api.fda.gov/drug/label.json?search=openfda.generic_name:{drug_name}&limit=1"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if results:
                warnings = results[0].get("warnings", [""])[0]
                return warnings[:300] if warnings else ""
    except Exception:
        pass
    return ""


def run_drug_agent(state: ClinicalState) -> Dict[str, Any]:
    t0 = time.time()
    medications = state.get("medications", [])
    
    if not medications:
        elapsed = int((time.time() - t0) * 1000)
        log_entry = f"[DrugAgent] No medications provided, skipping DDI check ({elapsed}ms)"
        logger.info(log_entry)
        return {
            "drug_interactions": [],
            "agent_logs": [log_entry],
            "processing_time_ms": {"drug_agent": elapsed},
        }
    
    try:
        llm = _get_llm()
        
        diagnoses = state.get("diagnoses", [])
        top_dx = diagnoses[0].get("name", "Unknown") if diagnoses else "Unknown"
        
        prompt = DDI_PROMPT.format(
            medications=", ".join(medications),
            top_diagnosis=top_dx,
        )
        response = llm.invoke(prompt)
        parsed = parse_json_response(response.content)
        interactions = parsed.get("interactions", [])
        
        # Enrich with OpenFDA where possible (best effort)
        for interaction in interactions[:3]:  # limit API calls
            drug_a = interaction.get("drug_a", "").lower().split()[0]
            note = _fetch_openfda_label(drug_a)
            if note:
                interaction["openfda_note"] = note[:200]
        
        elapsed = int((time.time() - t0) * 1000)
        log_entry = f"[DrugAgent] {len(interactions)} DDIs identified ({elapsed}ms)"
        logger.info(log_entry)
        
        return {
            "drug_interactions": interactions,
            "agent_logs": [log_entry],
            "processing_time_ms": {"drug_agent": elapsed},
        }
    except Exception as e:
        elapsed = int((time.time() - t0) * 1000)
        
        # Check if rate limited
        if is_rate_limited(e):
            logger.warning(f"Rate limited - checking common DDIs ({elapsed}ms)")
            fallback = RateLimitFallback.get_drug_fallback(medications)
            fallback["processing_time_ms"] = {"drug_agent": elapsed}
            return fallback
        
        # Other errors: return empty interactions
        logger.error(f"Drug agent error: {e}", exc_info=True)
        return {
            "drug_interactions": [],
            "agent_logs": [f"[DrugAgent] Error: {str(e)[:100]}"],
            "processing_time_ms": {"drug_agent": elapsed},
        }
