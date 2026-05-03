import streamlit as st
import os
from groq import Groq

# ------------------ UI THEME ------------------
st.markdown("""
<style>
body {
    background-color: #0e1117;
    color: #ffffff;
}
.block-container {
    padding: 2rem;
}
.section {
    background-color: #161b22;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 15px;
}
.score {
    font-size: 28px;
    font-weight: bold;
    color: #00ff9f;
}
</style>
""", unsafe_allow_html=True)

# ------------------ API ------------------
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("API key not found. Set GROQ_API_KEY in terminal.")
    st.stop()

client = Groq(api_key=api_key)

# ------------------ UI ------------------
st.title("🚀 VentureScope")
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

    prompt = f"""
You are a venture capital analyst.

Startup: {startup}

Provide a realistic VC-style analysis using general knowledge.

Return EXACT format:

Overview:
(max 2 lines)

Business Model:
- (max 3 bullets, include revenue source)

Market:
(max 2 lines)

Investment:
Score: X/10
Verdict: (1 short sentence)

Strengths:
- (2 bullets)

Risks:
- (2 bullets)

Rules:
- Be practical and realistic
- Do NOT say "unknown" unless absolutely necessary
- Do NOT give exact numbers unless confident
- Keep total under 120 words
"""

    try:
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