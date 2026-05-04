import streamlit as st
import os
import json
import re
from groq import Groq
import plotly.graph_objects as go

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
    border: 1px solid rgba(255,255,255,0.05);
}

.title {
    font-size: 36px;
    font-weight: 800;
    color: white;
}
.subtitle {
    color: #94a3b8;
}

.card {
    background: #020617;
    border: 1px solid rgba(255,255,255,0.05);
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
</style>
""", unsafe_allow_html=True)

# ------------------ API ------------------
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Set GROQ_API_KEY")
    st.stop()

client = Groq(api_key=api_key)

# ------------------ HELPERS ------------------
def extract_json(text):
    text = re.sub(r"```json|```", "", text)
    match = re.search(r"\{.*\}", text, re.S)
    return json.loads(match.group())

def card(title, content):
    st.markdown(f"""
    <div class="card">
        <div class="card-title">{title}</div>
        <div class="card-body">{content}</div>
    </div>
    """, unsafe_allow_html=True)

def list_card(title, items):
    items = items or []
    li = "".join(f"<li>{i}</li>" for i in items)
    st.markdown(f"""
    <div class="card">
        <div class="card-title">{title}</div>
        <ul class="card-body">{li}</ul>
    </div>
    """, unsafe_allow_html=True)

# ------------------ HEADER ------------------
st.markdown("""
<div class="hero">
<div class="title">🚀 VentureScope</div>
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
"score": 0,
"verdict": "",
"confidence": 0.0,

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

    with st.spinner("Analyzing..."):
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

    data = extract_json(res.choices[0].message.content)

    # ------------------ DECISION ------------------
    st.subheader("🔥 Decision")

    c1, c2, c3 = st.columns(3)
    c1.metric("Score", f"{data['score']}/10")
    c2.metric("Verdict", data["verdict"])
    c3.metric("Confidence", f"{int(data['confidence']*100)}%")

    st.progress(data["confidence"])

    # ------------------ WHY ------------------
    list_card("💡 Why", data["why"])

    # ------------------ RISKS ------------------
    list_card("⚠️ Risks", data["risks"])

    # ------------------ SIGNALS ------------------
    st.subheader("📊 Signals")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Market", data["signals"]["market"])
    s2.metric("Moat", data["signals"]["moat"])
    s3.metric("Execution", data["signals"]["execution"])
    s4.metric("Risk", data["signals"]["risk"])

    # ------------------ SCORE CHART ------------------
    st.subheader("📈 Score Breakdown")

    labels = ["Market", "Business", "Moat", "Execution", "Risk"]
    values = [
        data["market_score"],
        data["business_score"],
        data["moat_score"],
        data["execution_score"],
        10 - data["risk_score"]
    ]

    fig = go.Figure(data=[
        go.Bar(x=labels, y=values)
    ])

    fig.update_layout(
        paper_bgcolor="#050816",
        plot_bgcolor="#050816",
        font_color="white",
        yaxis=dict(range=[0, 10])
    )

    st.plotly_chart(fig, use_container_width=True)
