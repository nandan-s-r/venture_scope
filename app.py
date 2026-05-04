import html
import json
import os
import re
from datetime import datetime

import streamlit as st
from groq import Groq

st.set_page_config(
    page_title="VentureScope",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ----------------------------
# STYLE
# ----------------------------
st.markdown("""
<style>
    .main {
        background: radial-gradient(circle at top, #111827 0%, #0b1020 45%, #050816 100%);
    }
    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2rem;
        max-width: 1180px;
    }
    .hero {
        padding: 22px 24px 18px 24px;
        border-radius: 24px;
        background: linear-gradient(145deg, rgba(17,24,39,0.96), rgba(15,23,42,0.96));
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 18px 50px rgba(0,0,0,0.32);
        margin-bottom: 1rem;
    }
    .title {
        font-size: 38px;
        font-weight: 800;
        color: white;
        line-height: 1.05;
        margin: 0;
    }
    .subtitle {
        font-size: 15px;
        color: #a7b0c0;
        margin-top: 6px;
    }
    .card {
        background: linear-gradient(145deg, rgba(17,24,39,0.96), rgba(15,23,42,0.96));
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        padding: 18px 18px 16px 18px;
        box-shadow: 0 10px 28px rgba(0,0,0,0.22);
        height: 100%;
    }
    .card-title {
        color: white;
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .card-body {
        color: #d7dce5;
        font-size: 15px;
        line-height: 1.7;
        white-space: pre-wrap;
    }
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 14px;
        margin: 8px 0 18px 0;
    }
    .metric-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 16px 16px 14px 16px;
    }
    .metric-label {
        color: #9ca3af;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .08em;
        margin-bottom: 8px;
    }
    .metric-value {
        color: white;
        font-size: 30px;
        font-weight: 800;
        line-height: 1.1;
    }
    .pill {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        margin-top: 12px;
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(250,204,21,0.12);
        color: #fde68a;
    }
    .section-heading {
        color: white;
        font-size: 20px;
        font-weight: 800;
        margin: 22px 0 10px 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    .stTabs [data-baseweb="tab"] {
        color: #cbd5e1;
        font-size: 14px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        color: #ff4d4d !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# API
# ----------------------------
api_key = st.secrets.get("GROQ_API_KEY", None) if hasattr(st, "secrets") else None
api_key = api_key or os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("GROQ_API_KEY not found.")
    st.stop()

client = Groq(api_key=api_key)

# ----------------------------
# HELPERS
# ----------------------------
def safe_slug(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", text.strip().lower())[:50] or "startup"

def esc(text):
    return html.escape("" if text is None else str(text))

def text_card(title, content):
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">{esc(title)}</div>
            <div class="card-body">{esc(content)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def list_card(title, items):
    items = items or []
    lis = "".join(f"<li>{esc(i)}</li>" for i in items) if items else "<li>unknown</li>"
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">{esc(title)}</div>
            <div class="card-body"><ul>{lis}</ul></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def metric_card(label, value):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{esc(label)}</div>
            <div class="metric-value">{esc(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def extract_json(text: str):
    raw = text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?", "", raw, flags=re.I).strip()
        raw = re.sub(r"```$", "", raw).strip()
    try:
        return json.loads(raw)
    except Exception:
        match = re.search(r"\{.*\}", raw, re.S)
        if match:
            return json.loads(match.group(0))
        raise ValueError("Model did not return valid JSON.")

def build_prompt(startup: str, depth: str, risk_style: str):
    return f"""
You are a senior venture capital analyst.

Rules:
- Output ONLY valid JSON.
- Do not use markdown.
- Do not invent facts, funding, customers, revenue, or numbers.
- If unsure, use "unknown".
- Be concise and specific.

Startup: {startup}
Depth: {depth}
Risk style: {risk_style}

Return this exact JSON:
{{
  "startup": "{startup}",
  "one_liner": "",
  "overview": "",
  "business_model": {{
    "customer": "",
    "revenue_streams": [],
    "pricing_model": "",
    "notes": ""
  }},
  "market": {{
    "summary": "",
    "stage": "",
    "why_now": ""
  }},
  "score": 0,
  "verdict": "Invest | Watch | Pass",
  "confidence": "low | medium | high",
  "strengths": [],
  "risks": [],
  "diligence_questions": [],
  "assumptions": []
}}
"""

# ----------------------------
# HEADER
# ----------------------------
st.markdown(
    """
    <div class="hero">
        <div class="title">🚀 VentureScope</div>
        <div class="subtitle">AI VC Decision Engine</div>
        <div class="subtitle">Turn a startup name into a clean investor memo with score, risks, assumptions, and diligence questions.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# CONTROLS
# ----------------------------
with st.sidebar:
    st.markdown("### Controls")
    depth = st.selectbox("Analysis depth", ["Basic", "Standard", "Deep"], index=1)
    risk_style = st.selectbox("Risk style", ["Balanced", "Conservative", "Aggressive"], index=0)

with st.form("analysis_form"):
    startup = st.text_input("Enter startup name", placeholder="e.g. OpenAI, Zerodha, CRED")
    submitted = st.form_submit_button("Analyze startup")

# ----------------------------
# RESULT AREA
# ----------------------------
if submitted and startup.strip():
    with st.spinner("Analyzing startup..."):
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a senior VC analyst who returns only valid JSON."},
                {"role": "user", "content": build_prompt(startup.strip(), depth, risk_style)},
            ],
            temperature=0.2,
            max_tokens=900,
        )

        raw_text = response.choices[0].message.content
        data = extract_json(raw_text)

        score = data.get("score", 0)
        verdict = data.get("verdict", "unknown")
        confidence = data.get("confidence", "unknown")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card("Score", f"{score}/10")
        with c2:
            metric_card("Verdict", verdict)
        with c3:
            metric_card("Confidence", confidence)
        with c4:
            metric_card("Startup", startup.strip())

        if score >= 8:
            st.markdown('<span class="pill">High conviction</span>', unsafe_allow_html=True)
        elif score >= 6:
            st.markdown('<span class="pill">Watchlist</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="pill">Weak case</span>', unsafe_allow_html=True)

        tabs = st.tabs(["Summary", "Business Model", "Risks", "Diligence Questions"])

        with tabs[0]:
            col1, col2 = st.columns(2)
            with col1:
                text_card("One-liner", data.get("one_liner", "unknown"))
                text_card("Overview", data.get("overview", "unknown"))
            with col2:
                market = data.get("market", {})
                text_card("Market summary", market.get("summary", "unknown"))
                text_card("Market stage", market.get("stage", "unknown"))
                text_card("Why now", market.get("why_now", "unknown"))

        with tabs[1]:
            bm = data.get("business_model", {})
            c1, c2 = st.columns(2)
            with c1:
                text_card("Customer", bm.get("customer", "unknown"))
                text_card("Pricing model", bm.get("pricing_model", "unknown"))
            with c2:
                list_card("Revenue streams", bm.get("revenue_streams", []))
                text_card("Notes", bm.get("notes", "unknown"))

        with tabs[2]:
            c1, c2 = st.columns(2)
            with c1:
                list_card("Strengths", data.get("strengths", []))
            with c2:
                list_card("Risks", data.get("risks", []))
            list_card("Assumptions", data.get("assumptions", []))

        with tabs[3]:
            list_card("Questions to ask next", data.get("diligence_questions", []))
