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
    margin: 14px 0 8px 0;
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
    cleaned = re.sub(r"```json|```", "", text, flags=re.I).strip()
    match = re.search(r"\{.*\}", cleaned, re.S)
    if not match:
        raise ValueError("Model did not return valid JSON.")
    return json.loads(match.group(0))

def safe_num(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return float(default)

def is_placeholder_text(x):
    if x is None:
        return True
    s = str(x).strip().lower()
    return (
        s in {
            "",
            "n/a",
            "na",
            "unknown",
            "invest | watch | pass",
            "invest / watch / pass",
        }
        or "|" in s and "invest" in s and "watch" in s and "pass" in s
    )

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

def compute_final_score(market, business, moat, execution, risk):
    # risk is inverse-weighted
    final = (
        market * 0.25 +
        business * 0.20 +
        moat * 0.20 +
        execution * 0.20 +
        (10 - risk) * 0.15
    )
    return round(max(0, min(10, final)), 1)

def verdict_from_score(score):
    if score >= 8:
        return "Invest"
    elif score >= 6:
        return "Watch"
    return "Pass"

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
- Return ONLY valid JSON.
- Do NOT use placeholders like "Invest | Watch | Pass".
- Do NOT invent specific facts, numbers, revenue, or funding if you are not sure.
- If something is uncertain, use "unknown".
- Keep it concise and decision-oriented.

Startup: {startup.strip()}

Return this JSON with real values filled in:
{{
  "overview": "",
  "market_summary": "",
  "market_stage": "",
  "why_now": "",

  "market_score": 0,
  "business_score": 0,
  "moat_score": 0,
  "execution_score": 0,
  "risk_score": 0,

  "score": 0,
  "verdict": "",
  "confidence": 0.0,

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

        # ---- Fallbacks if model returns bad placeholders ----
        market_score = safe_num(data.get("market_score"), 0)
        business_score = safe_num(data.get("business_score"), 0)
        moat_score = safe_num(data.get("moat_score"), 0)
        execution_score = safe_num(data.get("execution_score"), 0)
        risk_score = safe_num(data.get("risk_score"), 0)

        computed_score = compute_final_score(
            market_score, business_score, moat_score, execution_score, risk_score
        )

        raw_score = safe_num(data.get("score"), 0)
        score = computed_score if raw_score <= 0 or raw_score > 10 else round(raw_score, 1)

        verdict = data.get("verdict", "")
        if is_placeholder_text(verdict):
            verdict = verdict_from_score(score)

        confidence = safe_num(data.get("confidence"), 0)
        if confidence > 1:
            confidence = confidence / 100.0
        confidence = max(0.0, min(1.0, confidence))

        signals = data.get("signals", {}) or {}

        # ------------------ OVERVIEW FIRST ------------------
        st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            card("Overview", data.get("overview", "N/A"))
            card("Market Summary", data.get("market_summary", "N/A"))
        with col2:
            card("Market Stage", data.get("market_stage", "N/A"))
            card("Why Now", data.get("why_now", "N/A"))

        # ------------------ DECISION ------------------
        st.markdown('<div class="section-title">Decision</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Score", f"{score}/10")
        c2.metric("Verdict", verdict)
        c3.metric("Confidence", f"{int(confidence * 100)}%")

        st.progress(confidence)

        # ------------------ SIGNALS ------------------
        st.markdown('<div class="section-title">Signals</div>', unsafe_allow_html=True)
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Market", signals.get("market", "N/A"))
        s2.metric("Moat", signals.get("moat", "N/A"))
        s3.metric("Execution", signals.get("execution", "N/A"))
        s4.metric("Risk", signals.get("risk", "N/A"))

        # ------------------ SCORE BREAKDOWN ------------------
        st.markdown('<div class="section-title">Score Breakdown</div>', unsafe_allow_html=True)

        score_items = [
            ("Market", market_score),
            ("Business", business_score),
            ("Moat", moat_score),
            ("Execution", execution_score),
            ("Risk", 10 - risk_score),
        ]

        for label, value in score_items:
            value = max(0.0, min(10.0, value))
            st.write(f"{label}: {value}/10")
            st.progress(value / 10.0)

        # ------------------ WHY / RISKS ------------------
        colA, colB = st.columns(2)
        with colA:
            list_card("Why", data.get("why"))
        with colB:
            list_card("Risks", data.get("risks"))

    except Exception as e:
        st.error(f"Error: {e}")
