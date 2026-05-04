import json
import os
import re
from datetime import datetime

import streamlit as st
from groq import Groq

# ----------------------------
# Page setup
# ----------------------------
st.set_page_config(
    page_title="VentureScope",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------
# Styling
# ----------------------------
st.markdown(
    """
    <style>
        .main {
            background: radial-gradient(circle at top, #111827 0%, #0b1020 45%, #050816 100%);
        }
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        .hero {
            padding: 24px 24px 18px 24px;
            border-radius: 22px;
            background: linear-gradient(145deg, rgba(17,24,39,0.92), rgba(15,23,42,0.92));
            border: 1px solid rgba(255,255,255,0.07);
            box-shadow: 0 20px 50px rgba(0,0,0,0.35);
            margin-bottom: 1rem;
        }
        .title {
            font-size: 42px;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 4px;
        }
        .subtitle {
            color: #a7b0c0;
            font-size: 16px;
        }
        .small-note {
            color: #9ca3af;
            font-size: 13px;
            margin-top: 8px;
        }
        .card {
            background: linear-gradient(145deg, rgba(17,24,39,0.96), rgba(15,23,42,0.96));
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 18px;
            margin-bottom: 14px;
            box-shadow: 0 12px 30px rgba(0,0,0,0.22);
        }
        .card h3 {
            margin: 0 0 10px 0;
            color: #ffffff;
            font-size: 18px;
        }
        .card p, .card li {
            color: #d1d5db;
            line-height: 1.55;
            font-size: 14px;
        }
        .pill {
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
            margin-right: 8px;
            margin-bottom: 8px;
            border: 1px solid rgba(255,255,255,0.08);
        }
        .pill-green { background: rgba(34,197,94,0.12); color: #86efac; }
        .pill-yellow { background: rgba(250,204,21,0.12); color: #fde68a; }
        .pill-red { background: rgba(248,113,113,0.12); color: #fca5a5; }
        .pill-blue { background: rgba(96,165,250,0.12); color: #bfdbfe; }
        .metric-box {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 16px;
        }
        .section-title {
            font-size: 20px;
            font-weight: 700;
            color: white;
            margin: 6px 0 12px 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# API key
# ----------------------------
def get_api_key():
    try:
        key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        key = None
    return key or os.getenv("GROQ_API_KEY")

api_key = get_api_key()
if not api_key:
    st.error("GROQ_API_KEY not found. Add it to Streamlit secrets or environment variables.")
    st.stop()

client = Groq(api_key=api_key)

# ----------------------------
# Helpers
# ----------------------------
def safe_slug(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", text.strip().lower())[:50] or "startup"

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
You are a sharp venture capital analyst.

Rules:
- Do NOT invent facts, numbers, customers, funding, or traction.
- If you are unsure, use "unknown" instead of guessing.
- Separate facts, assumptions, and risks clearly.
- Be concise, specific, and investor-like.
- Output ONLY valid JSON. No markdown. No extra text.

Startup: {startup}
Analysis depth: {depth}
Risk style: {risk_style}

Return this exact JSON structure:
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
  "strengths": [],
  "risks": [],
  "diligence_questions": [],
  "assumptions": [],
  "confidence": "low | medium | high"
}}

Scoring guide:
- 9-10 = strong invest case
- 6-8 = watch / promising but incomplete
- 0-5 = pass / weak or unclear

Depth rules:
- Basic: 5-7 bullets total across all arrays
- Standard: 8-12 bullets total
- Deep: 12-16 bullets total

Risk style:
- Conservative: call out uncertainty aggressively
- Balanced: practical investor framing
- Aggressive: focus more on upside
"""

def render_card(title, body_html):
    st.markdown(
        f"""
        <div class="card">
            <h3>{title}</h3>
            {body_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_list(items):
    if not items:
        return "<p>unknown</p>"
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"

# ----------------------------
# Session state
# ----------------------------
if "history" not in st.session_state:
    st.session_state.history = []

# ----------------------------
# Hero
# ----------------------------
st.markdown(
    """
    <div class="hero">
        <div class="title">🚀 VentureScope</div>
        <div class="subtitle">AI VC Decision Engine</div>
        <div class="small-note">
            Turn a startup name into a structured investor memo with score, risks, assumptions, and diligence questions.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# Sidebar controls
# ----------------------------
with st.sidebar:
    st.markdown("### Controls")
    depth = st.selectbox("Analysis depth", ["Basic", "Standard", "Deep"], index=1)
    risk_style = st.selectbox("Risk style", ["Balanced", "Conservative", "Aggressive"], index=0)
    st.markdown("---")
    st.markdown("### What this app does")
    st.caption("Uses Groq LLM + prompt engineering to generate a VC-style memo.")
    st.caption("Later upgrade: grounding with live data / RAG.")

# ----------------------------
# Input form
# ----------------------------
with st.form("analysis_form", clear_on_submit=False):
    startup = st.text_input("Enter startup name", placeholder="e.g. Zerodha, CRED, Notion, Perplexity")
    submitted = st.form_submit_button("Analyze startup")

# ----------------------------
# Main logic
# ----------------------------
if submitted and startup.strip():
    prompt = build_prompt(startup.strip(), depth, risk_style)

    with st.spinner("Analyzing startup..."):
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a senior VC analyst who returns only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=900,
            )

            raw_text = response.choices[0].message.content
            data = extract_json(raw_text)

            st.session_state.history.insert(0, {
                "startup": startup.strip(),
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "data": data,
            })
            st.session_state.history = st.session_state.history[:5]

            score = data.get("score", 0)
            verdict = data.get("verdict", "unknown")
            confidence = data.get("confidence", "unknown")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Score", f"{score}/10")
            c2.metric("Verdict", verdict)
            c3.metric("Confidence", confidence)
            c4.metric("Startup", startup.strip())

            pill_class = "pill-green" if score >= 8 else "pill-yellow" if score >= 6 else "pill-red"
            st.markdown(f'<span class="pill {pill_class}">Model output ready</span>', unsafe_allow_html=True)

            tabs = st.tabs(["Summary", "Business Model", "Risks", "Diligence Questions", "Raw JSON"])

            with tabs[0]:
                left, right = st.columns([1.2, 1])
                with left:
                    render_card("One-liner", f"<p>{data.get('one_liner', 'unknown')}</p>")
                    render_card("Overview", f"<p>{data.get('overview', 'unknown')}</p>")
                with right:
                    render_card(
                        "Market",
                        f"""
                        <p><b>Summary:</b> {data.get('market', {}).get('summary', 'unknown')}</p>
                        <p><b>Stage:</b> {data.get('market', {}).get('stage', 'unknown')}</p>
                        <p><b>Why now:</b> {data.get('market', {}).get('why_now', 'unknown')}</p>
                        """,
                    )
                    render_card(
                        "Verdict Snapshot",
                        f"""
                        <p><b>Score:</b> {score}/10</p>
                        <p><b>Verdict:</b> {verdict}</p>
                        <p><b>Confidence:</b> {confidence}</p>
                        """,
                    )

            with tabs[1]:
                bm = data.get("business_model", {})
                render_card("Customer", f"<p>{bm.get('customer', 'unknown')}</p>")
                render_card("Revenue streams", render_list(bm.get("revenue_streams", [])))
                render_card("Pricing model", f"<p>{bm.get('pricing_model', 'unknown')}</p>")
                render_card("Notes", f"<p>{bm.get('notes', 'unknown')}</p>")

            with tabs[2]:
                col1, col2 = st.columns(2)
                with col1:
                    render_card("Strengths", render_list(data.get("strengths", [])))
                with col2:
                    render_card("Risks", render_list(data.get("risks", [])))
                render_card("Assumptions", render_list(data.get("assumptions", [])))

            with tabs[3]:
                render_card("Questions to ask next", render_list(data.get("diligence_questions", [])))

            with tabs[4]:
                st.code(json.dumps(data, indent=2), language="json")
                st.download_button(
                    "Download JSON",
                    data=json.dumps(data, indent=2),
                    file_name=f"{safe_slug(startup)}_venturescope.json",
                    mime="application/json",
                )

        except Exception as e:
            st.error(f"Analysis failed: {e}")

# ----------------------------
# Recent analyses
# ----------------------------
if st.session_state.history:
    st.markdown("### Recent analyses")
    for item in st.session_state.history:
        data = item["data"]
        st.markdown(
            f"""
            <div class="card">
                <h3>{item["startup"]} <span style="color:#9ca3af;font-size:13px;">({item["time"]})</span></h3>
                <p><b>Score:</b> {data.get("score", "unknown")} / 10</p>
                <p><b>Verdict:</b> {data.get("verdict", "unknown")}</p>
                <p><b>One-liner:</b> {data.get("one_liner", "unknown")}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
