"""
Pipeline — LangGraph StateGraph that wires all agents.

Flow:
  safety_agent
       │
  ┌────┴────┐  (parallel)
  diagnosis  drug
  └────┬────┘
   pubmed_fetch
       │
  treatment_agent
"""
from __future__ import annotations
import time
from typing import Dict, Any

from langgraph.graph import StateGraph, END

from utils.state import ClinicalState
from agents.safety_agent import run_safety_agent
from agents.diagnosis_agent import run_diagnosis_agent
from agents.drug_agent import run_drug_agent
from agents.treatment_agent import run_treatment_agent
from rag.pubmed_retriever import search_pubmed, build_rag_query


def pubmed_node(state: ClinicalState) -> Dict[str, Any]:
    """Fetch PubMed citations based on top diagnosis."""
    t0 = time.time()
    query = build_rag_query(state.get("diagnoses", []), state.get("patient_input", ""))
    citations = search_pubmed(query, max_results=5)
    # Build RAG context string from abstracts/titles
    rag_context = "\n".join(
        f"{c['title']} ({c['journal']}, {c['year']})" for c in citations
    )
    elapsed = int((time.time() - t0) * 1000)
    log_entry = f"[PubMedNode] {len(citations)} citations fetched ({elapsed}ms)"
    
    return {
        "pubmed_citations": citations,
        "rag_context": rag_context,
        "agent_logs": [log_entry],
        "processing_time_ms": {"pubmed_fetch": elapsed},
    }


def add_disclaimer(state: ClinicalState) -> Dict[str, Any]:
    return {
        "disclaimer": (
            "⚠️ MedOracle  is an AI decision-support tool only. "
            "It does NOT replace clinical judgment, licensed clinician review, or established medical protocols. "
            "Always verify AI-generated suggestions with qualified healthcare professionals before acting. "
            "In emergencies call emergency services immediately."
        )
    }


def build_pipeline() -> StateGraph:
    g = StateGraph(ClinicalState)

    g.add_node("safety",    run_safety_agent)
    g.add_node("diagnosis", run_diagnosis_agent)
    g.add_node("drug",      run_drug_agent)
    g.add_node("pubmed",    pubmed_node)
    g.add_node("treatment", run_treatment_agent)
    g.add_node("finalize",  add_disclaimer)

    g.set_entry_point("safety")
    g.add_edge("safety", "diagnosis")
    g.add_edge("safety", "drug")
    g.add_edge("diagnosis", "pubmed")
    g.add_edge("drug", "pubmed")
    g.add_edge("pubmed", "treatment")
    g.add_edge("treatment", "finalize")
    g.add_edge("finalize", END)

    return g.compile()


# Singleton compiled pipeline
_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = build_pipeline()
    return _pipeline


def run_pipeline(patient_input: str, medications: list) -> Dict[str, Any]:
    """Entry point for Streamlit UI."""
    pipeline = get_pipeline()
    initial_state: ClinicalState = {
        "patient_input": patient_input,
        "medications": medications,
        "agent_logs": [],
        "processing_time_ms": {},
    }
    return pipeline.invoke(initial_state)
