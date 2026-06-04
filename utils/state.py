"""
ClinicalState — typed TypedDict shared across all LangGraph agents.
Keeps the full pipeline stateful and consistent.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, TypedDict, Annotated
from operator import add


def merge_dicts(a: Dict[str, int], b: Dict[str, int]) -> Dict[str, int]:
    """Merge two dicts, with b's values overwriting a's for duplicate keys."""
    return {**a, **b}


class ClinicalState(TypedDict, total=False):
    # ── Input ────────────────────────────────────────────────────────────────
    patient_input: str          # raw clinical note / symptom description
    medications: List[str]      # current medications list

    # ── Safety / Triage ──────────────────────────────────────────────────────
    triage: Dict[str, Any]      # level, reasoning, red_flags, emergency_type
    is_emergency: bool

    # ── Diagnosis ────────────────────────────────────────────────────────────
    diagnoses: List[Dict[str, Any]]   # ranked differentials with ICD-10

    # ── Treatment ────────────────────────────────────────────────────────────
    treatment: Dict[str, Any]   # evidence-graded treatment plan

    # ── Drug Interactions ────────────────────────────────────────────────────
    drug_interactions: List[Dict[str, Any]]  # DDI severity rankings

    # ── RAG / Citations ──────────────────────────────────────────────────────
    pubmed_citations: List[Dict[str, Any]]
    rag_context: str

    # ── Meta ─────────────────────────────────────────────────────────────────
    processing_time_ms: Annotated[Dict[str, int], merge_dicts]  # handles concurrent updates
    agent_logs: Annotated[List[str], add]  # handles concurrent updates
    disclaimer: str
    error: Optional[str]
