import streamlit as st
import os
import json
import re
import html
from groq import Groq
import matplotlib.pyplot as plt

# ------------------ CONFIG ------------------
st.set_page_config(page_title="VentureScope", layout="wide")

# ------------------ STYLE ------------------
st.markdown("""
<style>
.main {
    background: radial-gradient(circle at top, #0a0f1a 0%, #050816 100%);
}

.hero {
    padding: 24px;
    border-radius: 20px;
    background: linear-gradient(135deg, #0f172a, #020617);
    border: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 20px;
}

.title {
    font-size: 38px;
    font-weight: 800;
    color: white;
}
.subtitle {
    color: #94a3b8;
}

/* cards */
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
}
.card-body {
    color: #d1d5db;
}

/* metric */
.metric {
    background: #020617;
    border: 1px solid rgba(34,197,94,0.2);
    padding: 14px;
    border-radius: 14px;
    text-align: center;
}
.metric-value {
    font-size: 28px;
    font-weight: 800;
    color: white;
}
.metric-label {
    font-size: 12px;
    color: #94a3b8;
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
    text = re.sub(r"```json|```", "", text)
    match = re.search(r"\{.*\}", text, re.S)
    return json.loads(match.group())

def card(title, content):
    st.markdown(f"""
    <div class="card">
    <div class="card-title">{title}</div>
    <div class="card-body">{esc(content)}</div>
    </div>
    """, unsafe_allow_html=True)

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

    scores = {
        "Market": data["market_score"],
        "Business": data["business_score"],
        "Moat": data["moat_score"],
        "Execution": data["execution_score"],
        "Risk": 10 - data["risk_score"]
    }

    labels = list(scores.keys())
    values = list(scores.values())

    fig, ax = plt.subplots()
    ax.bar(labels, values)
    ax.set_ylim(0, 10)
    ax.set_title("Score Breakdown")

    st.pyplot(fig)
