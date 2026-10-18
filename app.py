"""Streamlit UI for the Autonomous Code Review Agent.

Run with:
    streamlit run app.py

Paste a code snippet or upload a .py/.diff file, then click "Review code".
The same read-only LangGraph workflow used by the CLI runs in the background
and the Markdown report is rendered in the page.
"""

from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

from code_review_agent import MissingAPIKeyError, get_llm, review_diff


def _strip_report_title(report: str) -> str:
    """Drop the report's own '# Code Review Report' H1 for a cleaner UI.

    The page already shows a 'Review report' heading, so repeating the title
    would just add an oversized, redundant line. The downloaded file keeps the
    full report including its title.
    """
    lines = report.splitlines()
    if lines and lines[0].strip().startswith("# Code Review Report"):
        return "\n".join(lines[1:]).lstrip("\n")
    return report


st.set_page_config(
    page_title="Autonomous Code Review Agent",
    page_icon="🔍",
    layout="wide",
)

load_dotenv()

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

/* Apply the UI font WITHOUT touching Streamlit's icon font. A selector like
   [class*="st-"] also matches icon elements and breaks the Material Symbols
   ligatures (icons then render as text such as "uploadupload"). */
html, body, .stApp {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

/* Belt-and-suspenders: keep Material icons using their own font. */
[data-testid="stIconMaterial"],
span[class*="material-symbols"],
.material-symbols-rounded {
    font-family: 'Material Symbols Rounded' !important;
}

.hero-title {
    font-family: 'Space Grotesk', 'Inter', sans-serif;
    font-size: 2.2rem;
    font-weight: 700;
    line-height: 1.2;
    letter-spacing: -0.02em;
    margin: 0;
    background: linear-gradient(90deg, #4f8cff 0%, #a855f7 55%, #ec4899 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-sub {
    color: #9aa0a6;
    font-size: 0.95rem;
    margin-top: 0.4rem;
    max-width: 58rem;
}

.hero-sub code {
    color: #c7d2fe;
}

/* Keep markdown headings inside the report reasonably sized */
.stMarkdown h1 { font-size: 1.7rem; font-weight: 650; margin-top: 0.4rem; }
.stMarkdown h2 { font-size: 1.3rem; font-weight: 650; margin-top: 1rem; }
.stMarkdown h3 { font-size: 1.05rem; font-weight: 600; margin-top: 0.9rem; }
.stMarkdown p, .stMarkdown li { font-size: 0.96rem; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown(
    '<div class="hero-title">Autonomous Code Review Agent</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="hero-sub">Paste a code snippet or upload a <code>.py</code> / '
    '<code>.diff</code> file. Findings are AI-generated suggestions that require '
    'human verification — no code is executed or modified.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Settings")
    model_override = st.text_input(
        "Model (optional)",
        value="",
        help="Leave blank to use LLM_MODEL from your .env file.",
    )

tab_paste, tab_upload = st.tabs(["Paste snippet", "Upload file"])

with tab_paste:
    pasted_text = st.text_area(
        "Paste code or a Git diff",
        height=320,
        placeholder="def add(a, b):\n    return a + b\n",
    )

with tab_upload:
    uploaded_file = st.file_uploader(
        "Upload a source file",
        type=["py", "diff", "patch", "txt"],
    )

review_clicked = st.button("Review code", type="primary")

if review_clicked:
    code_text = ""
    if pasted_text.strip():
        code_text = pasted_text
    elif uploaded_file is not None:
        code_text = uploaded_file.read().decode("utf-8", errors="replace")

    if not code_text.strip():
        st.warning("Please paste some code or upload a file first.")
    else:
        with st.spinner("Reviewing your code..."):
            try:
                llm = get_llm(model=model_override or None)
                st.session_state["report"] = review_diff(code_text, llm=llm)
                st.session_state["reviewed"] = True
            except MissingAPIKeyError as exc:
                st.session_state.pop("report", None)
                st.error(f"Configuration error: {exc}")
            except Exception as exc:  # noqa: BLE001 - surface API/network errors
                st.session_state.pop("report", None)
                st.error(f"Review failed: {exc}")

if st.session_state.get("report"):
    st.divider()
    header_col, action_col = st.columns([4, 1], vertical_alignment="center")
    header_col.subheader("Review report")
    with action_col:
        st.download_button(
            "Download review.md",
            data=st.session_state["report"],
            file_name="review.md",
            mime="text/markdown",
            use_container_width=True,
        )
    st.markdown(_strip_report_title(st.session_state["report"]))
