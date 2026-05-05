import streamlit as st
import os
import json
import re
import html
from groq import Groq

# ------------------ CONFIG ------------------
st.set_page_config(page_title="VentureScope", layout="wide")

# ------------------ STYLE ------------------
st.markdown("""
<style>
.main {
    background: radial-gradient(circle at top, #0a0f1a 0%, #050816 100%);
}
.hero {
    padding: 20px;
    border-radius: 16px;
    background: linear-gradient(135deg, #0f172a, #020617);
    border: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 16px;
}
.title {
    font-size: 34px;
    font-weight: 800;
    color: #ffffff;
}
.subtitle {
    color: #94a3b8;
    font-size: 14px;
}
.card {
    background: #020617;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 14px;
    margin-bottom: 12px;
}
.card-title {
    color: #22c55e;
    font-weight: 700;
    margin-bottom: 6px;
}
.card-body {
    color: #d1d5db;
    font-size: 14px;
    line-height: 1.6;
}
.section-title {
    color: #ffffff;
    font-weight: 700;
    margin: 12px 0 6px 0;
}
</style>
""", unsafe_allow_html=True)

# ------------------ API ------------------
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Set GROQ_API_KEY in your environment or Streamlit secrets.")
    st.stop()

client = Groq(api_key=api_key)

# ------------------ HELPERS ------------------
def esc(x):
    return html.escape(str(x)) if x is not None else "N/A"

def extract_json(text: str):
    """Robustly extract JSON from model output."""
    cleaned = re.sub(r"```json|```", "", text, flags=re.I).strip()
    match = re.search(r"\{.*\}", cleaned, re.S)
    if not match:
        raise ValueError("Model did not return valid JSON.")
    return json.loads(match.group(0))

def card(title, content):
    st.markdown(f"""
    <div class="card">
        <div class="card-title">{esc(title)}</div>
        <div class="card-body">{esc(content)}</div>
    </div>
    """, unsafe_allow_html=True)

def list_card(title, items):
    items = items or []
    lis = "".join(f"<li>{esc(i)}</li>" for i in items) if items else "<li>N/A</li>"
    st.markdown(f"""
    <div class="card">
        <div class="card-title">{esc(title)}</div>
        <ul class="card-body">{lis}</ul>
    </div>
    """, unsafe_allow_html=True)

def safe_num(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return float(default)

def safe_str(x, default="N/A"):
    return str(x) if x is not None else default

# ------------------ HEADER ------------------
st.markdown("""
<div class="hero">
  <div class="title">VentureScope</div>
  <div class="subtitle">Startup Decision Engine</div>
</div>
""", unsafe_allow_html=True)

# ------------------ INPUT ------------------
startup = st.text_input("Enter startup name")

# ------------------ MAIN ------------------
if st.button("Analyze") and startup.strip():

    prompt = f"""
You are a senior venture capital analyst.

Rules:
- Return ONLY valid JSON (no markdown, no explanations).
- Do NOT invent numbers. If unsure, use "unknown".
- Be concise and structured.

Startup: {startup.strip()}

Return this JSON:
{{
  "score": 0,
  "verdict": "Invest | Watch | Pass",
  "confidence": 0.0,

  "overview": "",
  "market_summary": "",
  "market_stage": "",
  "why_now": "",

  "market_score": 0,
  "business_score": 0,
  "moat_score": 0,
  "execution_score": 0,
  "risk_score": 0,

  "why": [],
  "risks": [],

  "signals": {{
    "market": "",
    "moat": "",
    "execution": "",
    "risk": ""
  }}
}}
"""

    try:
        with st.spinner("Analyzing..."):
            res = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a precise VC analyst who returns only JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=900
            )

        data = extract_json(res.choices[0].message.content)

        # ------------------ DECISION ------------------
        st.markdown('<div class="section-title">Decision</div>', unsafe_allow_html=True)

        score = safe_num(data.get("score"), 0)
        verdict = safe_str(data.get("verdict"), "N/A")
        confidence = safe_num(data.get("confidence"), 0)

        c1, c2, c3 = st.columns(3)
        c1.metric("Score", f"{score}/10")
        c2.metric("Verdict", verdict)
        c3.metric("Confidence", f"{int(confidence * 100)}%")

        st.progress(min(max(confidence, 0.0), 1.0))

        # ------------------ WHY + RISKS ------------------
        colA, colB = st.columns(2)
        with colA:
            list_card("Why", data.get("why"))
        with colB:
            list_card("Risks", data.get("risks"))

        # ------------------ SIGNALS ------------------
        st.markdown('<div class="section-title">Signals</div>', unsafe_allow_html=True)

        signals = data.get("signals", {}) or {}
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Market", safe_str(signals.get("market")))
        s2.metric("Moat", safe_str(signals.get("moat")))
        s3.metric("Execution", safe_str(signals.get("execution")))
        s4.metric("Risk", safe_str(signals.get("risk")))

        # ------------------ SCORE BREAKDOWN (NO EXTRA LIBS) ------------------
        st.markdown('<div class="section-title">Score Breakdown</div>', unsafe_allow_html=True)

        scores = {
            "Market": safe_num(data.get("market_score")),
            "Business": safe_num(data.get("business_score")),
            "Moat": safe_num(data.get("moat_score")),
            "Execution": safe_num(data.get("execution_score")),
            "Risk (inverse)": 10 - safe_num(data.get("risk_score"))
        }

        for k, v in scores.items():
            v_clamped = max(0.0, min(10.0, v))
            st.write(f"{k}: {v_clamped}/10")
            st.progress(v_clamped / 10.0)

        # ------------------ OVERVIEW / CONTEXT ------------------
        st.markdown("---")
        st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            card("Overview", data.get("overview", "N/A"))
            card("Market Summary", data.get("market_summary", "N/A"))

        with col2:
            card("Market Stage", data.get("market_stage", "N/A"))
            card("Why Now", data.get("why_now", "N/A"))

    except Exception as e:
        st.error(f"Error: {e}")
