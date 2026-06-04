# MedOracle

> **Advanced Multi-Agent Clinical Decision Support System**
> Production-grade LangGraph framework with 4 specialized agents, evidence-based treatment recommendations, and live PubMed literature integration.

`License: MIT` · `Python 3.10+` · `Status: Production Ready` · `Framework: LangGraph` · `LLM: Llama 3.3 70B`

---

## Table of Contents

- [Overview](#overview)
- [Key Capabilities](#key-capabilities)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Deployment](#deployment)
- [Performance](#performance)
- [Limitations & Safety](#limitations--safety)

---

## Overview

MedOracle is an enterprise-grade clinical decision support system (CDSS) built on LangGraph. It orchestrates four specialized AI agents — triage, differential diagnosis, drug interaction analysis, and evidence-based treatment — into a unified, production-hardened pipeline.

The system integrates real-time medical literature via NCBI PubMed, FDA drug safety data, and standardized evidence-grading protocols to augment clinical workflows. It is designed with strict data privacy constraints, graceful API degradation, and full audit traceability.

> **Intended for use as a clinician-facing decision support tool. Not a substitute for professional medical judgment.**

---

## Key Capabilities

| Capability | Details |
|---|---|
| **ICD-10 Clinical Coding** | LLM-generated ICD-10-CM codes with clinical reasoning |
| **Severity Triage** | 5-level severity stratification (ESI-aligned, L1–L5) |
| **DDI Analysis** | CONTRAINDICATED / MAJOR / MODERATE / MINOR classification with mechanism detail |
| **Evidence Grading** | Level A (RCTs) through D (Expert Opinion), GRADE-aligned |
| **PubMed RAG** | Real-time literature retrieval via NCBI Entrez API |
| **Multi-Format Export** | Structured DOCX reports and machine-readable JSON |
| **Audit Trail** | Full decision provenance with per-agent reasoning |
| **Benchmark Suite** | 4 validated clinical test cases with ground-truth labels |

---

## System Architecture

```
┌──────────────────────────────────────────────┐
│           Streamlit User Interface            │
└───────────────────┬──────────────────────────┘
                    │
┌───────────────────▼──────────────────────────┐
│          LangGraph Orchestrator               │
│      (parallel agent execution graph)         │
└──────┬────────────────────────────┬───────────┘
       │                            │
┌──────▼──────┐              ┌──────▼──────┐
│ Safety      │              │ Diagnosis   │
│ Agent       │              │ Agent       │
│ (L1–L5)     │              │ (ICD-10-CM) │
└──────┬──────┘              └──────┬──────┘
       │                            │
┌──────▼──────┐              ┌──────▼──────┐
│ Drug DDI    │              │ Treatment   │
│ Agent       │              │ Agent       │
│ (OpenFDA)   │              │ (Evidence)  │
└──────┬──────┘              └──────┬──────┘
       │                            │
       └──────────┬─────────────────┘
                  │
       ┌──────────▼──────────┐
       │   PubMed RAG Layer  │
       │ (NCBI Entrez + FAISS│
       │  live citation sync) │
       └─────────────────────┘
```

### Agent Responsibilities

| Agent | Role | Output |
|---|---|---|
| **Safety Agent** | Initial severity stratification | Triage level L1–L5 |
| **Diagnosis Agent** | Differential generation with ICD-10 codes | Ranked conditions + confidence scores |
| **Drug Agent** | Polypharmacy and DDI analysis | Severity-classified interaction warnings |
| **Treatment Agent** | Evidence-based recommendation synthesis | Graded recommendations with citations |

---

## Technology Stack

### Core — 100% Open Source / Free Tier

| Layer | Technology | Cost |
|---|---|---|
| **LLM** | Groq Llama 3.3 70B | Free tier |
| **Orchestration** | LangGraph + LangChain | Open source |
| **Literature** | NCBI Entrez / PubMed API | Free |
| **Drug Safety** | OpenFDA API | Free |
| **Vector Store** | FAISS (local) | Open source |
| **UI** | Streamlit | Open source |
| **Runtime** | Python 3.10+ | Open source |

### Upgrade Paths

| Current | Production Upgrade |
|---|---|
| Groq free tier | Groq paid / OpenAI GPT-4o |
| NCBI PubMed | Semantic Scholar + full-text PDF extraction |
| OpenFDA | DrugBank Enterprise |
| FAISS local | Pinecone / Weaviate / Milvus |

---

## Installation

### Prerequisites

- Python 3.10+
- `pip` or `conda`
- Git

### Local Setup

```bash
# 1. Clone and enter the project
git clone https://github.com/yourusername/MedOracle.git
cd MedOracle

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# → Edit .env with your API credentials
```

### Docker

```bash
docker-compose up --build
```

The application will be available at `http://localhost:8501`.

---

## Configuration

Create a `.env` file in the project root using `.env.example` as a template:

```env
# ── LLM Provider ──────────────────────────────────────────
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=optional_fallback_key

# ── Literature & Drug APIs ────────────────────────────────
PUBMED_EMAIL=your_email@example.com
PUBMED_TOOL=MedOracle

# ── Application ───────────────────────────────────────────
LOG_LEVEL=INFO
CACHE_TYPE=redis          # options: redis | local
CACHE_TTL=3600

# ── Rate Limiting ─────────────────────────────────────────
RATE_LIMIT_CALLS=100
RATE_LIMIT_WINDOW=3600

# ── Storage ───────────────────────────────────────────────
DATABASE_URL=sqlite:///MedOracle.db
```

Additional configuration surfaces:

| File | Purpose |
|---|---|
| `config.yaml` | Application-level settings |
| `logging.conf` | Log format and handler config |
| `docker-compose.yml` | Container orchestration |

---

## Usage

### Streamlit UI

```bash
streamlit run app.py
```

### Python API

```python
from pipeline import MedOraclePipeline

pipeline = MedOraclePipeline()

response = pipeline.process({
    "symptoms": "Chest pain, shortness of breath, diaphoresis",
    "medications": ["Lisinopril 10mg", "Atorvastatin 20mg"],
    "conditions": ["Hypertension", "Hyperlipidemia"],
    "age": 58,
    "gender": "male"
})

print(response.triage_level)            # → 2
print(response.differential_diagnosis) # → [{ condition, icd10, confidence, ... }]
print(response.recommendations)        # → [{ treatment, evidence_grade, citations }]
```

### Docker

```bash
# Start in detached mode
docker-compose up -d

# Stream application logs
docker-compose logs -f app

# Tear down
docker-compose down
```

---

## API Reference

### `MedOraclePipeline.process(input_dict) → MedOracleResponse`

Runs a full clinical case through the multi-agent pipeline.

**Input Parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `symptoms` | `str` | ✅ | Free-text symptom description |
| `medications` | `list[str]` | ✅ | Current medication list |
| `conditions` | `list[str]` | ✅ | Known comorbidities |
| `age` | `int` | ○ | Patient age |
| `gender` | `str` | ○ | Patient gender |

**Response Schema**

```json
{
  "triage_level": 2,
  "differential_diagnosis": [
    {
      "condition": "Acute Coronary Syndrome",
      "icd10": "I24.9",
      "confidence": 0.92,
      "reasoning": "Typical anginal chest pain with diaphoresis in high-risk patient."
    }
  ],
  "ddi_warnings": [
    {
      "drugs": ["Lisinopril", "Potassium Chloride"],
      "severity": "MAJOR",
      "mechanism": "Additive hyperkalemia risk via RAAS suppression."
    }
  ],
  "recommendations": [
    {
      "treatment": "Initiate dual antiplatelet therapy (aspirin + P2Y12 inhibitor)",
      "evidence_grade": "A",
      "citations": [
        {
          "pmid": "19329000",
          "title": "...",
          "journal": "NEJM",
          "year": 2009
        }
      ]
    }
  ],
  "citations": []
}
```

## Performance

### Baseline Benchmarks (single-node, Groq free tier)

| Operation | Avg Latency | Notes |
|---|---|---|
| Single case — full pipeline | 6–10 s | End-to-end, all agents |
| Parallel agent execution | 3–5 s | Triage + diagnosis in parallel |
| PubMed literature query | 1–2 s | Cached on repeat queries |
| DOCX report generation | 2–3 s | Full structured export |

### Optimization Notes

- Enable Redis caching for high-frequency condition queries
- Batch API calls when processing multiple cases concurrently
- Use a load balancer (e.g., Nginx) for >5 concurrent users
- Upgrade to Groq paid tier or OpenAI for significantly lower latency at scale

---

## Limitations & Safety

> ⚠️ **IMPORTANT DISCLAIMER**
> MedOracle is a clinical decision *support* tool. All AI-generated output requires review and validation by a licensed clinician before any clinical action is taken.

### Safety Requirements

- **Always verify** ICD-10 codes against the official WHO / CMS database before coding
- **Never rely solely** on DDI output; cross-reference with primary DDI references (e.g., Lexicomp, Micromedex)
- **Emergency protocol**: Acute emergencies (chest pain, stroke, respiratory failure) require immediate emergency services — call 911 (US) or 112 (EU) without delay
- **No PHI retention**: Patient data is not persisted beyond the active API request lifecycle

### Known Limitations

| Area | Limitation |
|---|---|
| Rare diseases | Coverage depends on LLM training corpus; rare conditions may have lower recall |
| Pediatrics | Reduced accuracy for pediatric-specific dosing and presentations |
| Drug coverage | DDI analysis bounded by OpenFDA database; may not cover all agents |
| Language | English only in current release |
| ICD-10 validation | Codes are LLM-proposed, not validated against authoritative WHO/CMS source |

---

## 👤 Author

**Muhammad Nadeem** — AI · ML · Agentic Engineer