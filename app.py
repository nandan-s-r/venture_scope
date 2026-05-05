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
    color: white;
}

.subtitle {
    color: #94a3b8;
}

/* BIG OVERVIEW */
.overview-hero {
    border: 1px solid rgba(34,197,94,0.2);
    border-radius: 18px;
    padding: 24px;
    margin-bottom: 20px;
}

.overview-title {
    font-size: 18px;
    font-weight: 700;
    color: #22c55e;
    margin-bottom: 10px;
}

.overview-text {
    font-size: 18px;
    line-height: 1.7;
    color: #e2e8f0;
}

/* CARDS */
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
}

.card-body {
    color: #d1d5db;
}

/* SECTION */
.section-title {
    color: white;
    font-weight: 700;
    margin: 14px 0 8px 0;
}
</style>
""", unsafe_allow_html=True)

# ------------------ API ------------------
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Set GROQ_API_KEY")
    st.stop()

client = Groq(api_key=api_key)

# ------------------ HELPERS ------------------
def esc(x):
    return html.escape(str(x)) if x else "N/A"

def extract_json(text):
    text = re.sub(r"```json|```", "", text)
    match = re.search(r"\{.*\}", text, re.S)
    return json.loads(match.group())

def safe_num(x, default=0):
    try:
        return float(x)
    except:
        return default

def compute_score(m, b, mo, e, r):
    return round(
        m*0.25 + b*0.2 + mo*0.2 + e*0.2 + (10-r)*0.15, 1
    )

def verdict_from_score(score):
    if score >= 8:
        return "Invest"
    elif score >= 6:
        return "Watch"
    return "Pass"

def list_card(title, items):
    items = items or []
    li = "".join(f"<li>{esc(i)}</li>" for i in items)
    st.markdown(f"""
    <div class="card">
        <div class="card-title">{title}</div>
        <ul class="card-body">{li}</ul>
    </div>
    """, unsafe_allow_html=True)

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
if st.button("Analyze") and startup:

    prompt = f"""
You are a VC analyst.

Return ONLY JSON.

Startup: {startup}

{{
"overview": "",
"market_summary": "",
"why_now": "",

"market_score": 0,
"business_score": 0,
"moat_score": 0,
"execution_score": 0,
"risk_score": 0,

"confidence": 0.0,

"why": [],
"risks": []
}}
"""

    with st.spinner("Analyzing..."):
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

    data = extract_json(res.choices[0].message.content)

    # ---- Compute Score ----
    m = safe_num(data.get("market_score"))
    b = safe_num(data.get("business_score"))
    mo = safe_num(data.get("moat_score"))
    e = safe_num(data.get("execution_score"))
    r = safe_num(data.get("risk_score"))

    score = compute_score(m, b, mo, e, r)
    verdict = verdict_from_score(score)
    confidence = safe_num(data.get("confidence"), 0.7)

    # ------------------ OVERVIEW ------------------
    st.markdown(f"""
    <div class="overview-hero">
        <div class="overview-title">Overview</div>
        <div class="overview-text">
            {esc(data.get("overview", "N/A"))}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ------------------ DECISION ------------------
    st.markdown('<div class="section-title">Decision</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Score", f"{score}/10")
    c2.metric("Verdict", verdict)
    c3.metric("Confidence", f"{int(confidence*100)}%")

    st.progress(confidence)

    # ------------------ WHY / RISKS ------------------
    c1, c2 = st.columns(2)
    with c1:
        list_card("Why", data.get("why"))
    with c2:
        list_card("Risks", data.get("risks"))

    # ------------------ SCORE BREAKDOWN ------------------
    st.markdown('<div class="section-title">Score Breakdown</div>', unsafe_allow_html=True)

    scores = {
        "Market": m,
        "Business": b,
        "Moat": mo,
        "Execution": e,
        "Risk": 10 - r
    }

    for k, v in scores.items():
        st.write(f"{k}: {v}/10")
        st.progress(v/10)

    # ------------------ CONTEXT ------------------
    st.markdown('<div class="section-title">Context</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.write("Market Summary")
        st.write(data.get("market_summary", "N/A"))

    with col2:
        st.write("Why Now")
        st.write(data.get("why_now", "N/A"))
