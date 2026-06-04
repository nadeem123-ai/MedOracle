"""
MedOracle — Advanced Multi-Agent Clinical Decision Support System
Streamlit UI · Warm Slate Premium Theme
"""
import os
import streamlit as st  # type: ignore
from pipeline import run_pipeline
from utils.report_generator import generate_docx_report, generate_json_report
from dotenv import load_dotenv
load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MedOracle",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Warm Slate Premium CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global: dark stone background ── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #1c1917 !important;
    color: #e7e5e4 !important;
}
[data-testid="stHeader"] { background: #1c1917 !important; }
[data-testid="collapsedControl"], section[data-testid="stSidebar"] { display: none !important; }

/* ── Typography ── */
h1, h2, h3, h4 { color: #fafaf9 !important; font-weight: 700 !important; }
p, label, .stMarkdown { color: #d6d3d1 !important; }

/* ── Top header ── */
.mo-header {
    display: flex; align-items: center; justify-content: space-between;
    background: #292524;
    border: 0.5px solid #44403c;
    border-left: 3px solid #14b8a6;
    border-radius: 12px;
    padding: 14px 22px;
    margin-bottom: 20px;
}
.mo-orb {
    width: 38px; height: 38px; border-radius: 50%;
    background: #14b8a6;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.mo-orb-inner {
    width: 15px; height: 15px; border-radius: 50%; background: #1c1917;
}
.mo-title { font-size: 1.55em; font-weight: 800; color: #fafaf9; letter-spacing: 0.03em; }
.mo-subtitle { font-size: 0.78em; color: #78716c; margin-top: 2px; }
.mo-badges { display: flex; gap: 6px; flex-wrap: wrap; }
.mo-badge {
    background: #1c1917; border: 0.5px solid #44403c;
    border-radius: 20px; padding: 4px 10px;
    font-size: 11px; color: #a8a29e;
    display: flex; align-items: center; gap: 5px;
}
.mo-badge-dot { width: 5px; height: 5px; border-radius: 50%; background: #14b8a6; }

/* ── Section headers ── */
.mo-section {
    background: #292524;
    border: 0.5px solid #44403c;
    border-left: 3px solid #14b8a6;
    border-radius: 8px;
    padding: 7px 14px;
    font-size: 0.82em; font-weight: 700;
    color: #14b8a6;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    margin: 18px 0 10px 0;
}

/* ── Vital alert box ── */
.mo-vital-alert {
    background: #2d1515;
    border: 0.5px solid #7f1d1d;
    border-left: 3px solid #ef4444;
    border-radius: 8px;
    padding: 10px 16px;
    color: #fca5a5;
    font-size: 0.85em;
    font-weight: 600;
    margin: 10px 0;
}

/* ── Triage result banner ── */
.mo-triage-emergency {
    background: #2d1515; border: 0.5px solid #7f1d1d;
    border-left: 4px solid #ef4444;
    border-radius: 10px; padding: 14px 20px; margin: 12px 0;
    color: #fca5a5; font-weight: 700; font-size: 1.05em;
}
.mo-triage-info {
    background: #0f2520; border: 0.5px solid #134e4a;
    border-left: 4px solid #14b8a6;
    border-radius: 10px; padding: 14px 20px; margin: 12px 0;
    color: #5eead4; font-weight: 600;
}

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: #292524 !important;
    border: 0.5px solid #44403c !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
}
[data-testid="stMetricLabel"] { color: #78716c !important; font-size: 12px !important; }
[data-testid="stMetricValue"] { color: #fafaf9 !important; font-size: 22px !important; font-weight: 700 !important; }

/* ── Inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] select,
div[data-baseweb="select"] {
    background: #292524 !important;
    border: 0.5px solid #44403c !important;
    border-radius: 8px !important;
    color: #e7e5e4 !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: #14b8a6 !important;
    box-shadow: 0 0 0 1px #14b8a680 !important;
}
label { color: #a8a29e !important; font-size: 13px !important; }

/* ── Checkboxes ── */
[data-testid="stCheckbox"] label { color: #d6d3d1 !important; font-size: 13px !important; }
[data-testid="stCheckbox"] input[type="checkbox"]:checked + div {
    background: #14b8a6 !important; border-color: #14b8a6 !important;
}

/* ── Primary button ── */
[data-testid="stButton"] button[kind="primary"] {
    background: #14b8a6 !important;
    border: none !important;
    border-radius: 8px !important;
    color: #0f3e38 !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    padding: 10px 20px !important;
    transition: opacity 0.15s;
}
[data-testid="stButton"] button[kind="primary"]:hover { opacity: 0.88 !important; }

/* ── Secondary buttons ── */
[data-testid="stButton"] button[kind="secondary"] {
    background: #292524 !important;
    border: 0.5px solid #44403c !important;
    border-radius: 8px !important;
    color: #a8a29e !important;
}
[data-testid="stButton"] button[kind="secondary"]:hover {
    border-color: #14b8a6 !important; color: #14b8a6 !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #292524 !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 0.5px solid #44403c !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 8px !important;
    color: #78716c !important;
    font-weight: 600 !important;
    border: none !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: #14b8a6 !important;
    color: #0f3e38 !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    background: #292524 !important;
    border: 0.5px solid #44403c !important;
    border-radius: 10px !important;
}
[data-testid="stExpander"] summary {
    color: #d6d3d1 !important;
}
[data-testid="stExpander"] summary:hover { color: #14b8a6 !important; }

/* ── Selectbox dropdown ── */
div[data-baseweb="popover"] { background: #292524 !important; border: 0.5px solid #44403c !important; }
div[data-baseweb="option"] { background: #292524 !important; color: #d6d3d1 !important; }
div[data-baseweb="option"]:hover { background: #1c1917 !important; color: #14b8a6 !important; }

/* ── Divider ── */
hr { border-color: #44403c !important; }

/* ── Progress bar ── */
[data-testid="stProgressBar"] > div { background: #14b8a6 !important; }

/* ── Download buttons ── */
[data-testid="stDownloadButton"] button {
    background: #292524 !important;
    border: 0.5px solid #44403c !important;
    border-radius: 8px !important;
    color: #14b8a6 !important;
    font-weight: 600 !important;
}
[data-testid="stDownloadButton"] button:hover {
    border-color: #14b8a6 !important; background: #0f2520 !important;
}

/* ── Success / warning / error overrides ── */
[data-testid="stAlert"][data-baseweb="notification"] {
    background: #0f2520 !important; border-color: #134e4a !important;
}

/* ── Vitals summary card ── */
.mo-vitals-card {
    background: #292524; border: 0.5px solid #44403c;
    border-radius: 10px; padding: 16px;
}
.mo-vital-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 6px 0; border-bottom: 0.5px solid #3c3836;
    font-size: 13px;
}
.mo-vital-row:last-child { border-bottom: none; }
.mo-vital-name { color: #78716c; }
.mo-vital-value { color: #fafaf9; font-weight: 700; }
.mo-vital-ok { color: #14b8a6; font-size: 11px; }
.mo-vital-warn { color: #ef4444; font-size: 11px; }

/* ── Result cards ── */
.mo-result-card {
    background: #292524; border: 0.5px solid #44403c;
    border-radius: 10px; padding: 16px; margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = os.getenv("GROQ_API_KEY", "")
if "session_log" not in st.session_state:
    st.session_state.session_log = []
if "med_list" not in st.session_state:
    st.session_state.med_list = [""]

# ── Demo Cases ────────────────────────────────────────────────────────────────
DEMO_CASES = {
    "STEMI": {
        "age": 67, "gender": "Male", "weight": 82,
        "bp_sys": 90, "bp_dia": 60, "hr": 110, "spo2": 94,
        "temp": 37.0, "rr": 20,
        "chief_complaint": "Crushing central chest pain radiating to left arm",
        "onset": "45 minutes ago",
        "symptoms": ["Chest Pain", "Diaphoresis", "Nausea/Vomiting"],
        "additional_hx": "ECG shows ST elevation in V1-V4 with reciprocal changes.",
        "meds": ["aspirin 81mg", "metformin 1000mg", "lisinopril 10mg", "atorvastatin 40mg"],
        "pmh": ["Hypertension", "Diabetes (Type 2)"],
    },
    "Sepsis": {
        "age": 58, "gender": "Female", "weight": 65,
        "bp_sys": 88, "bp_dia": 54, "hr": 118, "spo2": 92,
        "temp": 39.8, "rr": 24,
        "chief_complaint": "Confusion, fever — nursing home resident",
        "onset": "2 days",
        "symptoms": ["Fever/Chills", "Confusion/Altered Mental Status", "Shortness of Breath"],
        "additional_hx": "WBC 18,000. Foley catheter in situ. Urinalysis: pyuria, bacteriuria. Lactate 3.2 mmol/L.",
        "meds": ["warfarin 5mg", "digoxin 0.125mg", "furosemide 40mg"],
        "pmh": ["Heart Failure", "Atrial Fibrillation"],
    },
    "HTN Crisis": {
        "age": 45, "gender": "Male", "weight": 90,
        "bp_sys": 210, "bp_dia": 130, "hr": 88, "spo2": 98,
        "temp": 37.1, "rr": 16,
        "chief_complaint": "Severe headache and blurred vision",
        "onset": "This morning",
        "symptoms": ["Headache", "Visual Disturbance"],
        "additional_hx": "No focal neuro deficits. Creatinine 2.1 (baseline 1.0). Red cell casts in urine. Fundoscopy: papilledema.",
        "meds": ["amlodipine 10mg", "hydrochlorothiazide 25mg", "NSAIDs prn"],
        "pmh": ["Hypertension", "CKD (Chronic Kidney Disease)"],
    },
}

SYMPTOM_OPTIONS = [
    "Chest Pain", "Shortness of Breath", "Palpitations",
    "Fever/Chills", "Headache", "Nausea/Vomiting",
    "Abdominal Pain", "Dizziness/Syncope", "Diaphoresis",
    "Confusion/Altered Mental Status", "Weakness/Fatigue",
    "Visual Disturbance", "Swelling/Edema", "Back Pain",
    "Cough", "Hemoptysis", "Rash", "Seizure",
]

PMH_OPTIONS = [
    "Hypertension", "Diabetes (Type 1)", "Diabetes (Type 2)",
    "Coronary Artery Disease", "Heart Failure", "Atrial Fibrillation",
    "Asthma / COPD", "CKD (Chronic Kidney Disease)", "Stroke / TIA",
    "Cancer", "HIV/AIDS", "Hypothyroidism", "Hyperlipidemia",
    "Obesity", "Depression / Anxiety", "None",
]


def build_patient_note(age, gender, weight, bp_sys, bp_dia, hr, spo2, temp, rr,
                       chief_complaint, onset, symptoms, additional_hx, pmh):
    vitals = (f"BP {bp_sys}/{bp_dia} mmHg, HR {hr} bpm, "
              f"SpO2 {spo2}%, Temp {temp:.1f}°C, RR {rr} breaths/min")
    age_gender = f"{age}{'M' if gender == 'Male' else 'F' if gender == 'Female' else ''}"
    weight_str = f", Weight {weight} kg" if weight else ""
    sym_str = ", ".join(symptoms) if symptoms else "none reported"
    pmh_str = ", ".join(pmh) if pmh and "None" not in pmh else "none significant"
    note = (f"{age_gender}{weight_str} presenting with {chief_complaint}. "
            f"Onset: {onset}. Symptoms: {sym_str}. Vitals: {vitals}. PMH: {pmh_str}. ")
    if additional_hx.strip():
        note += additional_hx.strip()
    return note


def sec(label):
    st.markdown(f'<div class="mo-section">{label}</div>', unsafe_allow_html=True)


def add_med():
    st.session_state.med_list.append("")


def remove_med(idx):
    if len(st.session_state.med_list) > 1:
        st.session_state.med_list.pop(idx)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="mo-header">
  <div style="display:flex;align-items:center;gap:12px;">
    <div class="mo-orb"><div class="mo-orb-inner"></div></div>
    <div>
      <div class="mo-title">MedOracle</div>
      <div class="mo-subtitle">Multi-Agent Clinical Decision Support</div>
    </div>
  </div>
  <div class="mo-badges">
    <div class="mo-badge"><div class="mo-badge-dot"></div>Groq Llama 3.3 70B</div>
    <div class="mo-badge"><div class="mo-badge-dot"></div>PubMed Live</div>
    <div class="mo-badge"><div class="mo-badge-dot"></div>OpenFDA</div>
    <div class="mo-badge"><div class="mo-badge-dot"></div>ICD-10 Coded</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Groq Key ──────────────────────────────────────────────────────────────────
key_col, status_col = st.columns([3, 1])
with key_col:
    groq_key = st.text_input("Groq API Key",
                             type="password",
                             placeholder="sk-... Enter your Groq API key (free at console.groq.com)",
                             label_visibility="collapsed")
    if groq_key:
        st.session_state.groq_api_key = groq_key
        os.environ["GROQ_API_KEY"] = groq_key
    elif st.session_state.groq_api_key:
        os.environ["GROQ_API_KEY"] = st.session_state.groq_api_key
with status_col:
    if st.session_state.groq_api_key:
        st.success("✅ Key loaded")
    else:
        st.warning("⚠️ Key required")

st.caption("For educational use only · Not a substitute for professional clinical judgment")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🔍  Analysis", "📊  Benchmark", "📋  Session Log"])

# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    col1, col2 = st.columns([2, 1], gap="large")

    with col1:
        # Demo loader
        demo_choice = st.selectbox("⚡ Quick Load Demo Case",
                                   ["(manual entry)"] + list(DEMO_CASES.keys()))
        demo = DEMO_CASES.get(demo_choice, {})

        # ── Patient Info ──────────────────────────────────────────────────────
        sec("👤  Patient Information")
        pi1, pi2, pi3 = st.columns(3)
        with pi1:
            age = st.number_input("Age (years)", 0, 120, demo.get("age", 45), 1)
        with pi2:
            gender = st.selectbox("Gender", ["Male", "Female", "Other / Not specified"],
                                  index=["Male","Female","Other / Not specified"]
                                  .index(demo.get("gender", "Male")))
        with pi3:
            weight = st.number_input("Weight (kg)", 0, 300, demo.get("weight", 70), 1)

        # ── Vital Signs ───────────────────────────────────────────────────────
        sec("💓  Vital Signs")
        v1, v2, v3 = st.columns(3)
        with v1:
            bp_sys = st.number_input("BP Systolic (mmHg)", 50, 300, demo.get("bp_sys", 120), 1)
            bp_dia = st.number_input("BP Diastolic (mmHg)", 20, 200, demo.get("bp_dia", 80), 1)
        with v2:
            hr = st.number_input("Heart Rate (bpm)", 20, 300, demo.get("hr", 72), 1)
            rr = st.number_input("Resp. Rate (breaths/min)", 4, 60, demo.get("rr", 16), 1)
        with v3:
            spo2 = st.number_input("SpO₂ (%)", 50, 100, demo.get("spo2", 98), 1)
            temp = st.number_input("Temperature (°C)", 30.0, 45.0,
                                   float(demo.get("temp", 37.0)), 0.1, format="%.1f")

        alerts = []
        if bp_sys < 90:   alerts.append("Hypotension (SBP < 90 mmHg)")
        if bp_sys > 180:  alerts.append("Severe Hypertension (SBP > 180 mmHg)")
        if hr > 100:      alerts.append("Tachycardia (HR > 100 bpm)")
        if hr < 50:       alerts.append("Bradycardia (HR < 50 bpm)")
        if spo2 < 94:     alerts.append("Hypoxia (SpO₂ < 94%)")
        if temp > 38.3:   alerts.append("Fever (Temp > 38.3°C)")
        if rr > 20:       alerts.append("Tachypnea (RR > 20 breaths/min)")
        if alerts:
            st.markdown(
                '<div class="mo-vital-alert">🚨 Vital Alert — ' + " · ".join(alerts) + '</div>',
                unsafe_allow_html=True
            )

        # ── Chief Complaint & Symptoms ────────────────────────────────────────
        sec("🩺  Chief Complaint & Symptoms")
        cc1, cc2 = st.columns([2, 1])
        with cc1:
            chief_complaint = st.text_input("Chief Complaint",
                                            value=demo.get("chief_complaint", ""),
                                            placeholder="e.g. Crushing chest pain radiating to left arm")
        with cc2:
            onset = st.text_input("Onset / Duration",
                                  value=demo.get("onset", ""),
                                  placeholder="e.g. 45 minutes ago")

        st.markdown('<span style="color:#78716c;font-size:13px;">Select presenting symptoms</span>',
                    unsafe_allow_html=True)
        demo_syms = demo.get("symptoms", [])
        sym_cols = st.columns(3)
        selected_symptoms = []
        for i, sym in enumerate(SYMPTOM_OPTIONS):
            with sym_cols[i % 3]:
                if st.checkbox(sym, value=(sym in demo_syms), key=f"sym_{sym}"):
                    selected_symptoms.append(sym)

        additional_hx = st.text_area("Additional History / Exam Findings",
                                     value=demo.get("additional_hx", ""),
                                     height=80,
                                     placeholder="ECG findings, lab values, exam notes...")

        # ── Past Medical History ──────────────────────────────────────────────
        sec("📋  Past Medical History")
        demo_pmh = demo.get("pmh", [])
        pmh_cols = st.columns(3)
        selected_pmh = []
        for i, cond in enumerate(PMH_OPTIONS):
            with pmh_cols[i % 3]:
                if st.checkbox(cond, value=(cond in demo_pmh), key=f"pmh_{cond}"):
                    selected_pmh.append(cond)

        # ── Medications ───────────────────────────────────────────────────────
        sec("💊  Current Medications")
        if demo_choice != "(manual entry)" and demo.get("meds"):
            st.session_state.med_list = list(demo["meds"])

        st.caption("One medication per row — include dose and frequency")
        for idx in range(len(st.session_state.med_list)):
            mc1, mc2 = st.columns([5, 1])
            with mc1:
                st.session_state.med_list[idx] = st.text_input(
                    f"med_{idx}", value=st.session_state.med_list[idx],
                    key=f"med_{idx}", placeholder="e.g. Metoprolol 50mg twice daily",
                    label_visibility="collapsed")
            with mc2:
                if len(st.session_state.med_list) > 1:
                    st.button("✕", key=f"del_{idx}", on_click=remove_med,
                              args=(idx,), help="Remove")
        st.button("＋ Add Medication", on_click=add_med)

    # ── Controls column ───────────────────────────────────────────────────────
    with col2:
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        run_btn = st.button("▶  Run Multi-Agent Analysis", type="primary",
                            use_container_width=True,
                            disabled=not st.session_state.groq_api_key)

        # Agent pipeline steps
        st.markdown("""
        <div style="background:#292524;border:0.5px solid #44403c;border-radius:10px;
                    padding:14px 16px;margin-top:14px;">
          <div style="font-size:11px;color:#78716c;text-transform:uppercase;
                      letter-spacing:0.08em;margin-bottom:10px;">Agent Pipeline</div>
          <div style="display:flex;flex-direction:column;gap:8px;">
            <div style="display:flex;align-items:center;gap:10px;">
              <div style="width:24px;height:24px;border-radius:50%;background:#14b8a6;
                          display:flex;align-items:center;justify-content:center;
                          font-size:11px;font-weight:700;color:#0f3e38;flex-shrink:0;">1</div>
              <span style="color:#d6d3d1;font-size:13px;">Safety / Triage</span>
            </div>
            <div style="display:flex;align-items:center;gap:10px;">
              <div style="width:24px;height:24px;border-radius:50%;background:#14b8a6;
                          display:flex;align-items:center;justify-content:center;
                          font-size:11px;font-weight:700;color:#0f3e38;flex-shrink:0;">2</div>
              <span style="color:#d6d3d1;font-size:13px;">Diagnosis <span style="color:#57534e;font-size:11px;">(parallel)</span></span>
            </div>
            <div style="display:flex;align-items:center;gap:10px;">
              <div style="width:24px;height:24px;border-radius:50%;background:#14b8a6;
                          display:flex;align-items:center;justify-content:center;
                          font-size:11px;font-weight:700;color:#0f3e38;flex-shrink:0;">3</div>
              <span style="color:#d6d3d1;font-size:13px;">Drug DDI <span style="color:#57534e;font-size:11px;">(parallel)</span></span>
            </div>
            <div style="display:flex;align-items:center;gap:10px;">
              <div style="width:24px;height:24px;border-radius:50%;background:#14b8a6;
                          display:flex;align-items:center;justify-content:center;
                          font-size:11px;font-weight:700;color:#0f3e38;flex-shrink:0;">4</div>
              <span style="color:#d6d3d1;font-size:13px;">PubMed RAG</span>
            </div>
            <div style="display:flex;align-items:center;gap:10px;">
              <div style="width:24px;height:24px;border-radius:50%;background:#14b8a6;
                          display:flex;align-items:center;justify-content:center;
                          font-size:11px;font-weight:700;color:#0f3e38;flex-shrink:0;">5</div>
              <span style="color:#d6d3d1;font-size:13px;">Treatment Plan</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)


        # ── Live Vitals Card ─────────────────────────────────────────────────
        st.markdown(
            '<div style="background:#292524;border:0.5px solid #44403c;border-radius:10px;'
            'padding:12px 16px;margin-top:14px;">'
            '<div style="font-size:11px;color:#78716c;text-transform:uppercase;'
            'letter-spacing:0.08em;margin-bottom:6px;">Live Vitals</div>'
            '</div>',
            unsafe_allow_html=True
        )

        vitals_data = [
            ("BP",    f"{bp_sys}/{bp_dia} mmHg", 90 <= bp_sys <= 180),
            ("HR",    f"{hr} bpm",               50 <= hr <= 100),
            ("SpO2",  f"{spo2}%",                spo2 >= 94),
            ("Temp",  f"{temp:.1f} C",           temp <= 38.3),
            ("RR",    f"{rr} br/min",            rr <= 20),
        ]
        for vname, vval, vok in vitals_data:
            vc = "#14b8a6" if vok else "#ef4444"
            vs = "Normal" if vok else "Alert"
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:5px 4px;border-bottom:0.5px solid #3c3836;font-size:13px;">'
                f'<span style="color:#78716c;">{vname}</span>'
                f'<span style="display:flex;align-items:center;gap:6px;">'
                f'<span style="color:{vc};">●</span>'
                f'<span style="color:#fafaf9;font-weight:700;">{vval}</span>'
                f'<span style="color:{vc};font-size:11px;">({vs})</span>'
                f'</span></div>',
                unsafe_allow_html=True
            )

    # ── Run pipeline ──────────────────────────────────────────────────────────
    if run_btn and chief_complaint.strip():
        patient_note = build_patient_note(
            age, gender, weight, bp_sys, bp_dia, hr, spo2, temp, rr,
            chief_complaint, onset, selected_symptoms, additional_hx, selected_pmh)
        medications = [m.strip() for m in st.session_state.med_list if m.strip()]

        with st.spinner("Running multi-agent analysis..."):
            pb = st.progress(0)
            st.empty().text("Safety Agent — triage assessment...")
            pb.progress(10)
            try:
                result = run_pipeline(patient_note, medications)
                pb.progress(100)
                st.session_state.session_log.append(result)
                st.session_state.last_result = result
            except Exception as e:
                st.error(f"Pipeline error: {e}")
                st.stop()

    elif run_btn and not chief_complaint.strip():
        st.warning("Enter a Chief Complaint before running analysis.")

    # ── Results ───────────────────────────────────────────────────────────────
    result = st.session_state.get("last_result")
    if result:
        st.divider()
        triage = result.get("triage", {})
        level  = triage.get("level", "3")
        label  = triage.get("label", "URGENT")

        if result.get("is_emergency"):
            st.markdown(
                f'<div class="mo-triage-emergency">🚨 EMERGENCY — Triage Level {level}: {label}</div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="mo-triage-info">🏥 Triage Level {level}: {label}</div>',
                unsafe_allow_html=True)

        times = result.get("processing_time_ms", {})
        total = sum(times.values())
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Time", f"{total}ms")
        m2.metric("Active Agents", len([v for v in times.values() if v > 0]))
        m3.metric("Cases This Session", len(st.session_state.session_log))
        m4.metric("Evidence Grade", result.get("treatment", {}).get("evidence_grade", "—"))

        if triage.get("red_flags"):
            with st.expander("🚩 Red Flags"):
                for f in triage["red_flags"]:
                    if f: st.markdown(f"- {f}")

        with st.expander("🔄 Agent Log"):
            for log in result.get("agent_logs", []):
                if log: st.text(log)

        t1, t2, t3, t4 = st.columns(4)
        t1.metric("Safety", f"{times.get('safety_agent',0)}ms")
        t2.metric("Diagnosis", f"{times.get('diagnosis_agent',0)}ms")
        t3.metric("Drug DDI", f"{times.get('drug_agent',0)}ms")
        t4.metric("Treatment", f"{times.get('treatment_agent',0)}ms")

        st.divider()
        col_dx, col_tx = st.columns(2, gap="large")

        with col_dx:
            sec("🔬  Differential Diagnoses")
            for dx in result.get("diagnoses", []):
                prob = dx.get("probability", "")
                icon = {"High":"🔴","Medium":"🟡","Low":"🟢"}.get(prob,"⚪")
                with st.expander(f"{icon} #{dx.get('rank','')} {dx.get('name','')} [{dx.get('icd10','')}] — {prob} ({dx.get('confidence_pct','')}%)"):
                    st.markdown(f"**ICD-10:** `{dx.get('icd10','')}` — {dx.get('icd10_description','')}")
                    st.markdown(f"**Reasoning:** {dx.get('reasoning','')}")
                    if dx.get("key_findings"):
                        st.markdown("**Key Findings:** " + " · ".join(dx["key_findings"]))
                    if dx.get("supporting_tests"):
                        st.markdown("**Tests:** " + ", ".join(dx["supporting_tests"]))

        with col_tx:
            sec("💡  Treatment Plan")
            tx = result.get("treatment", {})
            grade = tx.get("evidence_grade","?")
            gc = {"A":"🟢","B":"🟡","C":"🟠","D":"🔴"}.get(grade,"⚪")
            st.markdown(f"**Evidence Grade:** {gc} **{grade}** — {tx.get('grade_explanation','')}")
            if tx.get("immediate"):
                st.markdown("**⚡ Immediate Actions:**")
                for a in tx["immediate"]: st.markdown(f"- {a}")
            if tx.get("short_term"):
                st.markdown("**📋 Short-term:**")
                for a in tx["short_term"]: st.markdown(f"- {a}")
            if tx.get("medications_recommended"):
                st.markdown("**💊 Medications:**")
                for m in tx["medications_recommended"][:4]:
                    st.markdown(f"- **{m.get('drug','')}** {m.get('dose','')} {m.get('frequency','')} × {m.get('duration','')}")
            if tx.get("contraindications"):
                st.markdown("**🚫 Contraindications:**")
                for c in tx["contraindications"]: st.markdown(f"- ❌ {c}")

        ddis = result.get("drug_interactions", [])
        if ddis:
            sec("⚗️  Drug-Drug Interactions")
            for ddi in ddis:
                sev = ddi.get("severity","")
                se = {"CONTRAINDICATED":"🔴","MAJOR":"🟠","MODERATE":"🟡","MINOR":"🟢"}.get(sev,"⚪")
                with st.expander(f"{se} [{sev}] {ddi.get('drug_a','')} × {ddi.get('drug_b','')}"):
                    st.markdown(f"**Mechanism:** {ddi.get('mechanism','')}")
                    st.markdown(f"**Clinical Effect:** {ddi.get('clinical_effect','')}")
                    st.markdown(f"**Management:** {ddi.get('management','')}")
                    if ddi.get("alternative"): st.markdown(f"**Alternative:** {ddi['alternative']}")
                    if ddi.get("openfda_note"): st.caption(f"FDA Label: {ddi['openfda_note'][:150]}...")

        pubs = result.get("pubmed_citations", [])
        if pubs:
            sec("📚  PubMed Evidence")
            for pub in pubs:
                st.markdown(f"**{pub.get('title','')}**")
                st.caption(f"{pub.get('authors','')} · *{pub.get('journal','')}* ({pub.get('year','')}) · [PMID: {pub.get('pmid','')}]({pub.get('url','')})")

        st.divider()
        sec("📥  Export Report")
        dc, jc = st.columns(2)
        with dc:
            try:
                docx_bytes = generate_docx_report(result)
                if docx_bytes:
                    st.download_button("📄 Download Word Report", data=docx_bytes,
                                       file_name="MedOracle_report.docx",
                                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            except Exception:
                st.info("Install python-docx for Word export")
        with jc:
            st.download_button("📋 Download JSON Report",
                               data=generate_json_report(result),
                               file_name="MedOracle_report.json",
                               mime="application/json")

        st.divider()
        st.caption(result.get("disclaimer","⚠️ MedOracle is an AI decision-support tool only. Not a substitute for clinical judgment."))


# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    sec("📊  Benchmark Evaluation")
    st.markdown("Run 8 curated clinical cases and measure triage accuracy against ground truth.")

    BENCHMARK = [
        {"name":"STEMI","note":DEMO_CASES["STEMI"],"expected_level":"1","expected_emergency":True,"category":"Cardiac"},
        {"name":"Sepsis","note":DEMO_CASES["Sepsis"],"expected_level":"2","expected_emergency":True,"category":"Infectious"},
        {"name":"HTN Crisis","note":DEMO_CASES["HTN Crisis"],"expected_level":"2","expected_emergency":True,"category":"Hypertensive"},
        {"name":"Routine DM","note":{"age":52,"gender":"Female","weight":68,"bp_sys":128,"bp_dia":76,"hr":72,"spo2":99,"temp":36.8,"rr":14,"chief_complaint":"Routine diabetes follow-up, well controlled","onset":"Routine","symptoms":[],"additional_hx":"","pmh":["Diabetes (Type 2)"]},"meds":["metformin 1000mg","linagliptin 5mg"],"expected_level":"5","expected_emergency":False,"category":"Routine"},
        {"name":"Acute Stroke","note":{"age":68,"gender":"Male","weight":78,"bp_sys":160,"bp_dia":95,"hr":92,"spo2":97,"temp":37.2,"rr":16,"chief_complaint":"Sudden left-sided weakness and slurred speech","onset":"30 min ago","symptoms":["Weakness/Fatigue","Visual Disturbance"],"additional_hx":"Right gaze deviation, left facial droop, NIHSS 15.","pmh":["Hypertension"]},"meds":["metoprolol 50mg","lisinopril 10mg"],"expected_level":"1","expected_emergency":True,"category":"Neuro"},
        {"name":"Anaphylaxis","note":{"age":32,"gender":"Female","weight":58,"bp_sys":95,"bp_dia":55,"hr":125,"spo2":95,"temp":37.5,"rr":26,"chief_complaint":"Throat tightness, rash after bee sting","onset":"5 min ago","symptoms":["Shortness of Breath","Rash"],"additional_hx":"Audible wheezing.","pmh":["None"]},"meds":["none"],"expected_level":"1","expected_emergency":True,"category":"Allergic"},
        {"name":"Asthma Exac.","note":{"age":41,"gender":"Male","weight":74,"bp_sys":132,"bp_dia":82,"hr":110,"spo2":92,"temp":37.0,"rr":22,"chief_complaint":"Acute dyspnea, peak flow 60%","onset":"2 hours","symptoms":["Shortness of Breath","Cough"],"additional_hx":"Mild wheezing.","pmh":["Asthma / COPD"]},"meds":["albuterol prn","fluticasone"],"expected_level":"3","expected_emergency":False,"category":"Respiratory"},
        {"name":"Appendicitis?","note":{"age":19,"gender":"Female","weight":55,"bp_sys":118,"bp_dia":72,"hr":94,"spo2":99,"temp":38.2,"rr":16,"chief_complaint":"RLQ pain, rebound tenderness, fever","onset":"12 hours","symptoms":["Abdominal Pain","Fever/Chills","Nausea/Vomiting"],"additional_hx":"Rebound tenderness.","pmh":["None"]},"meds":["none"],"expected_level":"3","expected_emergency":False,"category":"Surgical"},
    ]

    if not os.getenv("GROQ_API_KEY"):
        st.warning("⚠️ Enter your Groq API key at the top of the page to run benchmark.")
    else:
        if st.button("▶  Run Benchmark (8 cases)", type="primary"):
            results = []
            prog = st.progress(0)
            for i, case in enumerate(BENCHMARK):
                st.write(f"Running: {case['name']}...")
                try:
                    n = case["note"]
                    note_str = build_patient_note(
                        n["age"],n["gender"],n["weight"],n["bp_sys"],n["bp_dia"],
                        n["hr"],n["spo2"],n["temp"],n["rr"],n["chief_complaint"],
                        n["onset"],n["symptoms"],n["additional_hx"],n["pmh"])
                    r = run_pipeline(note_str, case.get("meds",[]))
                    al = r.get("triage",{}).get("level","?")
                    ae = r.get("is_emergency",False)
                    results.append({
                        "case":case["name"],"category":case.get("category","Other"),
                        "expected_level":case["expected_level"],"actual_level":al,
                        "expected_emergency":case["expected_emergency"],"actual_emergency":ae,
                        "level_correct":str(al)==str(case["expected_level"]),
                        "emergency_correct":ae==case["expected_emergency"],
                    })
                except Exception as e:
                    results.append({"case":case["name"],"error":str(e)})
                prog.progress((i+1)/len(BENCHMARK))

            correct = sum(1 for r in results if r.get("level_correct") and r.get("emergency_correct"))
            acc = correct/len(BENCHMARK)*100
            st.metric("Overall Triage Accuracy", f"{acc:.0f}%")
            st.progress(acc/100)

            cats = {}
            for r in results:
                if "error" not in r:
                    cats.setdefault(r.get("category","Other"),[]).append(r)
            for cat in sorted(cats):
                st.markdown(f"**{cat}**")
                for r in cats[cat]:
                    ok = r.get("level_correct") and r.get("emergency_correct")
                    st.markdown(f"{'✅' if ok else '❌'} **{r['case']}** — Expected L{r['expected_level']} · Got L{r['actual_level']} · Emergency {r['expected_emergency']}→{r['actual_emergency']}")


# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    sec("📋  Session Case Log")
    session_log = st.session_state.get("session_log", [])
    if not session_log:
        st.info("No cases analyzed yet in this session.")
    else:
        st.metric("Cases Analyzed", len(session_log))
        case_options = [f"Case {i+1}: L{r.get('triage',{}).get('level','?')} — {r.get('patient_input','')[:50]}..." for i,r in enumerate(session_log)]

        cc1, cc2 = st.columns(2)
        with cc1:
            c1i = st.selectbox("Case 1", range(len(session_log)), format_func=lambda i: case_options[i], key="case1")
        with cc2:
            c2i = st.selectbox("Case 2", range(len(session_log)), format_func=lambda i: case_options[i], key="case2", index=min(1,len(session_log)-1)) if len(session_log)>1 else None

        if c2i is not None and c1i != c2i:
            st.divider()
            st.markdown("**Case Comparison**")
            cp1, cp2 = st.columns(2)
            r1, r2 = session_log[c1i], session_log[c2i]
            with cp1:
                st.markdown(f"**Case 1 — Level {r1.get('triage',{}).get('level','?')}**")
                dxs1 = r1.get("diagnoses",[])
                if dxs1: st.markdown(f"Top Dx: {dxs1[0].get('name','')} ({dxs1[0].get('confidence_pct','')}%)")
                tx1 = r1.get("treatment",{})
                if tx1: st.markdown(f"Evidence Grade: {tx1.get('evidence_grade','?')}")
            with cp2:
                st.markdown(f"**Case 2 — Level {r2.get('triage',{}).get('level','?')}**")
                dxs2 = r2.get("diagnoses",[])
                if dxs2: st.markdown(f"Top Dx: {dxs2[0].get('name','')} ({dxs2[0].get('confidence_pct','')}%)")
                tx2 = r2.get("treatment",{})
                if tx2: st.markdown(f"Evidence Grade: {tx2.get('evidence_grade','?')}")

        st.divider()
        for i, r in enumerate(session_log):
            triage = r.get("triage",{})
            with st.expander(f"Case {i+1} — L{triage.get('level','?')}: {triage.get('label','?')} · Emergency: {r.get('is_emergency',False)}"):
                d1, d2 = st.columns([2,1])
                with d1:
                    st.markdown(f"**Input:** {r.get('patient_input','')}")
                    st.markdown(f"**Medications:** {', '.join(r.get('medications',[])) or 'None'}")
                    dxs = r.get("diagnoses",[])
                    if dxs:
                        st.markdown("**Top Diagnoses:**")
                        for dx in dxs[:3]:
                            st.markdown(f"- {dx.get('rank','?')}. {dx.get('name','')} [{dx.get('icd10','')}] ({dx.get('confidence_pct','')}%)")
                with d2:
                    times = r.get("processing_time_ms",{})
                    st.metric("Safety", f"{times.get('safety_agent',0)}ms")
                    st.metric("Diagnosis", f"{times.get('diagnosis_agent',0)}ms")
                    st.metric("Drug DDI", f"{times.get('drug_agent',0)}ms")
                    st.metric("Treatment", f"{times.get('treatment_agent',0)}ms")