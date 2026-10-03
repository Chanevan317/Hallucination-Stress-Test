"""Hallucination Stress Test: run with `uv run streamlit run app.py`."""

import streamlit as st

from hst import guardrails, page_compare, page_editor, page_experiment, page_live, page_settings
from hst.ui_common import NAV, get_dataset, init_state

st.set_page_config(page_title="Hallucination Stress Test", layout="wide")
init_state()

PAGES = {
    "Settings": page_settings.render,
    "Experiment": page_experiment.render,
    "Side-by-Side": page_compare.render,
    "Live Test": page_live.render,
    "Prompt Editor": page_editor.render,
}

ss = st.session_state
with st.sidebar:
    st.title("Hallucination Stress Test")
    page = st.radio("Screen", NAV, label_visibility="collapsed")
    st.divider()
    ss.use_cached = st.checkbox(
        "Use stored results (offline)",
        value=ss.use_cached,
        help="Reads results/cached_results.json instead of the live run. Use as the demo fallback.",
    )
    st.caption(f"Models: {ss.model_a or '—'} | {ss.model_b or '—'}")
    st.caption(f"Judge: {ss.judge_model or '—'}")
    dataset, error = get_dataset()
    if not error:
        traps = sum(1 for i in dataset if i["is_trap"])
        st.caption(f"Dataset: {traps} trap / {len(dataset) - traps} control loaded")

if ss.use_cached:
    st.info(guardrails.message("INFO_STORED"))
PAGES[page]()
