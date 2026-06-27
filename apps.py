import os
import streamlit as st
import pandas as pd
import ast
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    try:
        GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    except Exception:
        GROQ_API_KEY = None
# Now import your engines (they will see the env var)
from analyzer.static_rules import StaticRuleEngine
from analyzer.complexity_analyzer import ComplexityAnalyzer
from evaluator.code_scoring import CodeScoringSystem
from fixer.auto_fixer import AutoFixer

st.set_page_config(page_title="CodeOptima", page_icon="🚀", layout="wide")
st.title("🚀 CodeOptima: Intelligent Python Analysis System")

# Initialize engines
@st.cache_resource
def load_engines():
    return StaticRuleEngine(), ComplexityAnalyzer(), CodeScoringSystem(), AutoFixer()

rule_engine, complexity_analyzer, scoring_system, auto_fixer = load_engines()

# --- rest of your code (user input, analysis, etc.) ---
# (keep everything else exactly as you had)

# --- 3. User Input ---
st.subheader("📥 Code Input")
input_method = st.radio("Choose input method:", ["Paste Code", "Upload .py File"], horizontal=True)

user_code = ""
if input_method == "Paste Code":
    user_code = st.text_area("Paste Python/ML code (Max 500 lines):", height=250)
else:
    uploaded_file = st.file_uploader("Upload a Python file", type=["py"])
    if uploaded_file is not None:
        user_code = uploaded_file.read().decode("utf-8")
        st.success(f"✅ File loaded: {uploaded_file.name}")

if st.button("Run Full Analysis Pipeline", type="primary"):
    # Line limit check
    lines = user_code.split('\n')
    if len(lines) > 500:
        st.error("❌ Limit Exceeded: CodeOptima is optimized for scripts under 300 lines.")
        st.stop()

    # PHASE 1: SYNTAX PARSING (The Gatekeeper)
    try:
        ast.parse(user_code)
        st.success("✅ Phase 1 Complete: Syntax is valid.")
    except SyntaxError as e:
        st.error(f"❌ Phase 1 Failed: Syntax Error Detected")
        st.info(f"Location: Line {e.lineno} | Error: {e.msg}")
        st.stop()  # No API call

    # PHASE 2 & 3: STATIC RULE ENGINE & ISSUE CLASSIFICATION
    with st.spinner("Executing Static Rule Engine..."):
        issues = rule_engine.analyze(user_code)
        metrics = complexity_analyzer.analyze(user_code)
        level = complexity_analyzer.get_complexity_level(metrics)
        score_data = scoring_system.calculate_score(issues, metrics, level)

        # Quality Scorecard
        st.subheader("📊 Code Quality Scorecard")
        cols = st.columns(4)
        cols[0].metric("Grade", score_data.grade)
        cols[1].metric("Score", f"{score_data.overall_score}/100")
        cols[2].metric("Complexity", level.value)
        cols[3].metric("Issues", len(issues))

        # Issue Classification Table (Phase 3)
        st.subheader("🚩 Phase 3: Issue Classification Table")
        if issues:
            df_issues = pd.DataFrame([
                {
                    "Line": i.line,
                    "Category": i.category.value,
                    "Severity": i.severity.value,
                    "Description": i.title,
                    "Recommended Fix": i.suggestion
                } for i in issues
            ])
            # Color-code severity
            st.dataframe(
                df_issues.style.map(
                    lambda x: 'background-color: #ffcccc' if x == 'CRITICAL' else
                              'background-color: #ffe0b3' if x == 'HIGH' else
                              'background-color: #fff3cd' if x == 'MEDIUM' else '',
                    subset=['Severity']
                ),
                width="stretch",
                hide_index=True
            )
        else:
            st.success("No structural issues identified by the Static Engine.")

    # PHASE 4: AI SUGGESTION ENGINE (Groq Llama 3)
    @st.fragment
    def optimization_fragment():
        choice = st.radio(
        "What would you like to do?",
        ["Rule-Based Fixes Only","AI Optimization"]
        )
        if choice == "AI Optimization" :
            with st.spinner("Engaging Groq AI for Deep Logic Optimization..."):
                fixed_code, applied_fixes, ai_details = auto_fixer.fix_code_with_ai(user_code, issues, provider="Groq")
                st.badge(f"AI DEBUG: Success using {ai_details.get('provider')}") 

                if ai_details.get("error"):
                    st.warning(f"⚠️ AI optimization skipped: {ai_details['error']}. Using rule‑based fixes only.")
        elif choice == "Rule-Based Fixes Only":
            with st.spinner("Applying rule-based fixes only..."):
                fixed_code, applied_fixes, ai_details = auto_fixer.apply_rule_based_fixes(user_code, issues)

        # PHASE 5: FINAL OUTPUT (Side-by-Side Comparison)
        st.subheader("✨Phase 5: Optimization Output")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Original Input**")
            st.code(user_code, language="python")
        with col2:
            output_title = "**Optimized Output (CodeOptima AI)**" if choice == "AI Optimization" else "**Optimized Output (CodeOptima Rule-Based)**"
            st.markdown(output_title)
            clean_code = fixed_code.replace("```python", "").replace("```", "").strip()
            st.code(clean_code, language="python")
            
            # Add download button for improved code
            st.download_button(
                label="📥 Download as improved.py",
                data=clean_code,
                file_name="improved.py",
                mime="text/plain"
            )

        # AI Explanation
        with st.expander("📝 View AI Refactoring Details"):
            if ai_details.get("explanation"):
                st.write(ai_details["explanation"])
            else:
                st.write("AI did not provide a detailed explanation.")
            if ai_details.get("pros"):
                st.markdown("**Improvements Made:**")
                for pro in ai_details["pros"]:
                    st.markdown(f"- {pro}")
            if ai_details.get("cons_of_old"):
                st.markdown("**Issues in original code:**")
                for con in ai_details["cons_of_old"]:
                    st.markdown(f"- {con}")

    optimization_fragment()
