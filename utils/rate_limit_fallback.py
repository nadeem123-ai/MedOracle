"""
Rate Limit Fallback - Graceful degradation when API rate limited.
Returns reasonable defaults based on input patterns.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class RateLimitFallback:
    """Provide safe default responses when rate limited."""
    
    @staticmethod
    def get_safety_fallback(patient_input: str) -> Dict[str, Any]:
        """
        Return safe default triage based on keywords.
        
        Use when Safety Agent rate limited.
        """
        logger.warning("Safety Agent rate limited - using keyword-based triage")
        
        lower_input = patient_input.lower()
        
        # L1 emergency indicators
        l1_keywords = ["unresponsive", "cardiac arrest", "severe", "unconscious", 
                       "not breathing", "choking", "anaphylaxis"]
        if any(kw in lower_input for kw in l1_keywords):
            return {
                "triage": {
                    "level": 1,
                    "label": "IMMEDIATE",
                    "red_flags": ["High-risk emergency detected"]
                },
                "is_emergency": True,
                "emergency_type": "ESI_L1",
                "agent_logs": ["[FALLBACK] Rate limited - keyword triage L1"]
            }
        
        # L2 emergency indicators
        l2_keywords = ["chest pain", "difficulty breathing", "SOB", "dyspnea",
                       "stroke", "TIA", "severe bleeding", "severe pain",
                       "altered mental", "confusion", "sepsis", "fever 103"]
        if any(kw in lower_input for kw in l2_keywords):
            return {
                "triage": {
                    "level": 2,
                    "label": "EMERGENT",
                    "red_flags": ["Potential emergency presentation"]
                },
                "is_emergency": True,
                "emergency_type": "ESI_L2",
                "agent_logs": ["[FALLBACK] Rate limited - keyword triage L2"]
            }
        
        # L3 urgent
        l3_keywords = ["fever", "cough", "shortness", "pain", "nausea", "vomiting"]
        if any(kw in lower_input for kw in l3_keywords):
            return {
                "triage": {
                    "level": 3,
                    "label": "URGENT",
                    "red_flags": []
                },
                "is_emergency": False,
                "emergency_type": "NONE",
                "agent_logs": ["[FALLBACK] Rate limited - keyword triage L3"]
            }
        
        # Default L4
        return {
            "triage": {
                "level": 4,
                "label": "SEMI-URGENT",
                "red_flags": []
            },
            "is_emergency": False,
            "emergency_type": "NONE",
            "agent_logs": ["[FALLBACK] Rate limited - default triage L4"]
        }
    
    @staticmethod
    def get_diagnosis_fallback(patient_input: str) -> Dict[str, Any]:
        """Return reasonable differential diagnoses based on keywords."""
        logger.warning("Diagnosis Agent rate limited - using keyword-based diagnosis")
        
        lower_input = patient_input.lower()
        
        # Map keywords to common diagnoses
        diagnosis_map = {
            "chest pain": [
                {"name": "Acute Coronary Syndrome", "icd10": "I24.9", "confidence": 0.7},
                {"name": "Musculoskeletal chest pain", "icd10": "M79.1", "confidence": 0.5},
                {"name": "Anxiety", "icd10": "F41.1", "confidence": 0.4}
            ],
            "fever": [
                {"name": "Upper Respiratory Infection", "icd10": "J06.9", "confidence": 0.6},
                {"name": "Influenza", "icd10": "J09.X3", "confidence": 0.5},
                {"name": "Bacterial infection (undetermined site)", "icd10": "A49.9", "confidence": 0.4}
            ],
            "cough": [
                {"name": "Cough (unspecified)", "icd10": "R05.9", "confidence": 0.7},
                {"name": "Acute bronchitis", "icd10": "J20.9", "confidence": 0.6},
                {"name": "Pneumonia", "icd10": "J18.9", "confidence": 0.4}
            ],
            "shortness of breath": [
                {"name": "Dyspnea (unspecified)", "icd10": "R06.02", "confidence": 0.7},
                {"name": "Asthma", "icd10": "J45.9", "confidence": 0.5},
                {"name": "Pneumonia", "icd10": "J18.9", "confidence": 0.4}
            ],
            "abdominal pain": [
                {"name": "Abdominal pain (generalized)", "icd10": "R10.9", "confidence": 0.6},
                {"name": "Gastroenteritis", "icd10": "A09", "confidence": 0.5},
                {"name": "Appendicitis", "icd10": "K35.80", "confidence": 0.3}
            ]
        }
        
        # Find matching diagnoses
        for keyword, diagnoses in diagnosis_map.items():
            if keyword in lower_input:
                return {
                    "diagnoses": diagnoses,
                    "agent_logs": [f"[FALLBACK] Rate limited - {keyword} fallback diagnoses"]
                }
        
        # Default fallback
        return {
            "diagnoses": [
                {"name": "Undetermined presentation", "icd10": "R69", "confidence": 0.5},
                {"name": "Acute illness unspecified", "icd10": "A09", "confidence": 0.3}
            ],
            "agent_logs": ["[FALLBACK] Rate limited - default diagnoses"]
        }
    
    @staticmethod
    def get_drug_fallback(medications: list) -> Dict[str, Any]:
        """Return common drug interactions or safe default (no interactions)."""
        logger.warning("Drug Agent rate limited - checking for common interactions")
        
        # Common contraindicated combinations
        contraindicated = [
            (["warfarin", "aspirin"], "Increased bleeding risk"),
            (["methotrexate", "NSAIDs"], "Renal toxicity"),
            (["ACE inhibitor", "potassium"], "Hyperkalemia"),
        ]
        
        med_lower = [m.lower() for m in medications]
        
        for drug_combo, risk in contraindicated:
            if all(any(drug in med for med in med_lower) for drug in drug_combo):
                return {
                    "drug_interactions": [
                        {
                            "drug_a": drug_combo[0],
                            "drug_b": drug_combo[1],
                            "severity": "MAJOR",
                            "mechanism": risk
                        }
                    ],
                    "agent_logs": ["[FALLBACK] Rate limited - common DDI check"]
                }
        
        # Safe: no major interactions detected
        return {
            "drug_interactions": [],
            "agent_logs": ["[FALLBACK] Rate limited - no interactions detected"]
        }
    
    @staticmethod
    def get_treatment_fallback(triage_level: int, diagnosis: str) -> Dict[str, Any]:
        """Return evidence-graded treatment plan based on level/diagnosis."""
        logger.warning("Treatment Agent rate limited - using guideline-based treatment")
        
        # Basic treatment templates by triage level
        templates = {
            1: {
                "plan": "IMMEDIATE specialist consultation required. Activate emergency protocols.",
                "evidence_grade": "A",
                "medications": ["Contact specialist"],
                "key_actions": ["Continuous monitoring", "Prepare for ICU admission"]
            },
            2: {
                "plan": "Urgent evaluation and stabilization. Specialist consultation.",
                "evidence_grade": "A",
                "medications": ["Consult with attending"],
                "key_actions": ["ECG/Labs ordered", "IV access established"]
            },
            3: {
                "plan": "Standard diagnostic workup. Consider specialist referral.",
                "evidence_grade": "B",
                "medications": ["Based on working diagnosis"],
                "key_actions": ["Labs ordered", "Follow-up arranged"]
            },
            4: {
                "plan": "Outpatient management. Primary care follow-up.",
                "evidence_grade": "B",
                "medications": ["Symptomatic relief"],
                "key_actions": ["PCP referral", "Return precautions provided"]
            }
        }
        
        template = templates.get(triage_level, templates[4])
        
        return {
            "treatment": {
                "plan": template["plan"],
                "evidence_grade": template["evidence_grade"],
                "medications": template["medications"],
                "key_actions": template["key_actions"]
            },
            "agent_logs": [f"[FALLBACK] Rate limited - L{triage_level} template treatment"]
        }
