import streamlit as st
st.set_page_config(page_title="VentureScope", layout="wide")

import os
import requests
from groq import Groq

# ------------------ UI THEME ------------------
st.markdown("""
<style>
body {
    background-color: #0b0f14;
}
.block-container {
    padding: 2rem;
}
.section {
    background: linear-gradient(145deg, #111827, #0f172a);
    padding: 20px;
    border-radius: 14px;
    margin-bottom: 18px;
    border: 1px solid rgba(255,255,255,0.05);
}
.title {
    font-size: 42px;
    font-weight: 700;
}
.subtitle {
    color: #9ca3af;
}
.score {
    font-size: 32px;
    font-weight: bold;
    color: #22c55e;
}
</style>
""", unsafe_allow_html=True)

# ------------------ API ------------------
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("API key not found. Set GROQ_API_KEY in Secrets.")
    st.stop()

client = Groq(api_key=api_key)

# ------------------ UI ------------------
st.markdown("<div class='title'>🚀 VentureScope</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>AI VC Decision Engine</div>", unsafe_allow_html=True)
st.caption("AI-powered startup analysis for investors")

startup = st.text_input("Enter Startup Name:")

# ------------------ DISPLAY FUNCTION ------------------
def display_section(title, content):
    st.markdown(f"""
    <div class='section'>
        <h3>{title}</h3>
        <p>{content}</p>
    </div>
    """, unsafe_allow_html=True)

# ------------------ MAIN LOGIC ------------------
if startup:

    # ---- LOG SEARCH (Google Sheets) ----
    try:
        requests.post(
            "https://script.google.com/macros/s/AKfycbyWpP3JJwQgk62qbeQzXMBYsk8srKDemoYss7wlGuHIVae4xPSMZcWKcfhfiyQoa0UodQ/exec",
            json={"startup": startup},
            timeout=5
        )
    except:
        pass

    # ---- PROMPT ----
    prompt = f"""
Act as a venture capital analyst.

Startup: {startup}

Output strictly:

Overview: (max 2 lines)

Business Model:
- (3 bullets max, include revenue source)

Market: (max 2 lines)

Investment:
Score: X/10
Verdict: (1 sharp line)

Strengths:
- (2 bullets)

Risks:
- (2 bullets)

Rules:
- No fluff
- No generic words like "strong potential"
- No made-up numbers
- Max 100 words
"""

    try:
        with st.spinner("Analyzing startup..."):
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.3,
                max_tokens=180
            )

        output = response.choices[0].message.content

        # ------------------ PARSE OUTPUT ------------------
        sections = {
            "Overview": "",
            "Business Model": "",
            "Market": "",
            "Verdict": "",
            "Score": "",
            "Strengths": "",
            "Risks": ""
        }

        current_section = None

        for line in output.split("\n"):
            line = line.strip()

            if "Overview:" in line:
                current_section = "Overview"
                continue
            elif "Business Model:" in line:
                current_section = "Business Model"
                continue
            elif "Market:" in line:
                current_section = "Market"
                continue
            elif "Investment:" in line:
                current_section = None
                continue
            elif "Score:" in line:
                sections["Score"] = line.replace("Score:", "").strip()
                continue
            elif "Verdict:" in line:
                sections["Verdict"] = line.replace("Verdict:", "").strip()
                continue
            elif "Strengths:" in line:
                current_section = "Strengths"
                continue
            elif "Risks:" in line:
                current_section = "Risks"
                continue

            if current_section and line:
                sections[current_section] += line + " "

        # ------------------ DISPLAY ------------------
        display_section("Overview", sections["Overview"])
        display_section("Business Model", sections["Business Model"])
        display_section("Market", sections["Market"])

        st.markdown(f"""
        <div class='section'>
            <h3>Verdict</h3>
            <p>{sections['Verdict']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class='section'>
            <h3>Score</h3>
            <div class='score'>{sections['Score']}</div>
        </div>
        """, unsafe_allow_html=True)

        display_section("Strengths", sections["Strengths"])
        display_section("Risks", sections["Risks"])

    except Exception as e:
        st.error(f"Error: {e}")
