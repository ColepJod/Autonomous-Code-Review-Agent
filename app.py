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

st.set_page_config(
    page_title="Autonomous Code Review Agent",
    page_icon="🔍",
    layout="wide",
)

load_dotenv()

st.title("🔍 Autonomous Code Review Agent")
st.caption(
    "Paste a code snippet or upload a `.py` / `.diff` file. "
    "Findings are AI-generated suggestions that require human verification — "
    "no code is executed or modified."
)

with st.sidebar:
    st.header("Settings")
    model_override = st.text_input(
        "Model (optional)",
        value="",
        help="Leave blank to use LLM_MODEL from your .env file.",
    )
    st.markdown(
        "Configure the provider in your **`.env`** file:\n\n"
        "```\nLLM_API_KEY=...\nLLM_BASE_URL=...\nLLM_MODEL=...\n```"
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
    st.subheader("Review report")
    st.markdown(st.session_state["report"])
    st.download_button(
        "Download report (review.md)",
        data=st.session_state["report"],
        file_name="review.md",
        mime="text/markdown",
    )
