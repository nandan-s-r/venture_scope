import streamlit as st
import os
import json
import re
import html
from groq import Groq

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="VentureScope", layout="wide")

# ------------------ STYLE ------------------
st.markdown("""
<style>

/* BACKGROUND */
.main {
    background: radial-gradient(circle at top, #0a0f1a 0%, #050816 100%);
}

/* HERO */
.hero {
    padding: 24px;
    border-radius: 20px;
    background: linear-gradient(135deg, #0f172a, #020617);
    border: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 20px;
}

/* TITLE */
.title {
    font-size: 38px;
    font-weight: 800;
    color: white;
}
.subtitle {
    color: #94a3b8;
}

/* METRICS */
.metric-card {
    background: #020617;
    border: 1px solid rgba(34,197,94,0.2);
    border-radius: 16px;
    padding: 14px;
    transition: 0.2s;
}
.metric-card:hover {
    border: 1px solid #22c55e;
    box-shadow: 0 0 12px rgba(34,197,94,0.3);
}
.metric-label {
    font-size: 12px;
    color: #94a3b8;
}
.metric-value {
    font-size: 28px;
    font-weight: 800;
    color: white;
}

/* CARDS */
.card {
    background: #020617;
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 14px;
}
.card-title {
    font-weight: 700;
    color: #22c55e;
    margin-bottom: 6px;
}
.card-body {
    color: #d1d5db;
    font-size: 14px;
}

/* TABS */
.stTabs [aria-selected="true"] {
    color: #22c55e !important;
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
    return html.escape(str(x)) if x else "unknown"

def extract_json(text):
    text = text.strip()
    text = re.sub(r"```json|```", "", text)
    match = re.search(r"\{.*\}", text, re.S)
    return json.loads(match.group())

def card(title, content):
    st.markdown(f"""
    <div class="card">
        <div class="card-title">{esc(title)}</div>
        <div class="card-body">{esc(content)}</div>
    </div>
    """, unsafe_allow_html=True)

def list_card(title, items):
    items = items or []
    li = "".join(f"<li>{esc(i)}</li>" for i in items)
    st.markdown(f"""
    <div class="card">
        <div class="card-title">{esc(title)}</div>
        <ul class="card-body">{li}</ul>
    </div>
    """, unsafe_allow_html=True)

def metric(label, value):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# ------------------ HEADER ------------------
st.markdown("""
<div class="hero">
<div class="title">🚀 VentureScope</div>
<div class="subtitle">AI VC Decision Engine</div>
<div class="subtitle">Clean investor-style startup analysis</div>
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
"one_liner": "",
"overview": "",
"market_summary": "",
"market_stage": "",
"why_now": "",
"score": 0,
"verdict": "",
"confidence": "",
"strengths": [],
"risks": [],
"diligence_questions": []
}}
"""

    with st.spinner("Analyzing..."):
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

    data = extract_json(res.choices[0].message.content)

    # ------------------ METRICS ------------------
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric("Score", f"{data['score']}/10")
    with c2:
        metric("Verdict", data["verdict"])
    with c3:
        metric("Confidence", data["confidence"])
    with c4:
        metric("Startup", startup)

    # ------------------ TABS ------------------
    tabs = st.tabs(["Summary", "Business", "Risks", "Questions"])

    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            card("🚀 One-liner", data["one_liner"])
            card("📘 Overview", data["overview"])
        with col2:
            card("📊 Market", data["market_summary"])
            card("📍 Stage", data["market_stage"])
            card("⚡ Why now", data["why_now"])

    with tabs[1]:
        list_card("💰 Strengths", data["strengths"])

    with tabs[2]:
        list_card("⚠️ Risks", data["risks"])

    with tabs[3]:
        list_card("❓ Diligence Questions", data["diligence_questions"])
