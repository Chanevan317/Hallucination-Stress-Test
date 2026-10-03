"""Shared Streamlit helpers: session state, badges, response cards, data access."""

import html
import os

import streamlit as st

from hst import config, guardrails, prompts, store
from hst.groq_client import GroqClient

# label -> (background, text, border); palette from the UI spec
BADGES = {
    "HALLUCINATED": ("#FEE2E2", "#991B1B", "#FCA5A5"),
    "CORRECT_DEFENSE": ("#DCFCE7", "#166534", "#86EFAC"),
    "OVER_REFUSAL": ("#FFEDD5", "#9A3412", "#FDBA74"),
    "CORRECT_ANSWER": ("#E0E7FF", "#3730A3", "#A5B4FC"),
    "INCORRECT_ANSWER": ("#F3E8FF", "#6B21A8", "#D8B4FE"),
    "INVENTED_DETAILS": ("#FEE2E2", "#991B1B", "#FCA5A5"),
    "NO_INVENTED_DETAILS": ("#DCFCE7", "#166534", "#86EFAC"),
    "NEEDS_REVIEW": ("#FEF3C7", "#92400E", "#FDE68A"),
    "OUT_OF_SCOPE": ("#FEF3C7", "#92400E", "#FDE68A"),
    "INVALID_OUTPUT": ("#F3F4F6", "#1F2937", "#D1D5DB"),
    "API_ERROR": ("#F3F4F6", "#1F2937", "#D1D5DB"),
    "JUDGE_ERROR": ("#F3F4F6", "#1F2937", "#D1D5DB"),
}
NEUTRAL = ("#EFF6FF", "#1E3A8A", "#BFDBFE")
NAV = ["Settings", "Experiment", "Side-by-Side", "Live Test", "Prompt Editor"]


def init_state() -> None:
    ss = st.session_state
    if "initialised" in ss:
        return
    ss.initialised = True
    ss.api_key = os.environ.get("GROQ_API_KEY", "")
    ss.models = []
    ss.model_a = ""
    ss.model_b = ""
    ss.judge_model = ""
    ss.min_interval = 2.5
    ss.json_mode = False
    ss.accept_fences = False
    ss.use_cached = not store.load_results() and bool(store.load_cached())


# -- rendering --------------------------------------------------------------
def badge(label: str) -> str:
    bg, fg, border = BADGES.get(label, NEUTRAL)
    return (
        f'<span style="background:{bg};color:{fg};border:1px solid {border};'
        f'padding:2px 8px;border-radius:10px;font-size:0.8em;margin-right:4px;'
        f'font-weight:600;white-space:nowrap">{html.escape(label)}</span>'
    )


def highlight(text: str, span: str) -> str:
    """HTML-escape text, marking the judge's invented span in red if present."""
    if span and span in text:
        before, _, after = text.partition(span)
        return (
            html.escape(before)
            + f'<mark style="background:#FCA5A5">{html.escape(span)}</mark>'
            + html.escape(after)
        )
    return html.escape(text)


def render_card(title: str, rec: dict | None, *, live: bool = False) -> None:
    st.markdown(f"**{title}**")
    if rec is None:
        st.info("No result yet for this combination.")
        return
    flags = rec.get("flags", [])
    judge = rec.get("judge")
    parsed = rec.get("parsed")
    labels = ([judge["label"]] if judge else []) + list(flags)
    if parsed:
        labels.append(parsed["verdict"])
    st.markdown(" ".join(badge(x) for x in labels) or "&nbsp;", unsafe_allow_html=True)

    if config.FLAG_API_ERROR in flags:
        st.error(guardrails.message("ERR_API", detail=rec.get("error", "unknown error")))
        return

    span = (judge or {}).get("invented_claim_span", "")
    if parsed:
        if live and parsed["verdict"] == "OUT_OF_SCOPE":
            st.warning(guardrails.message("ERR_OFF_TOPIC"))
        if parsed["problematic_claims"]:
            st.caption("Problematic claims")
            st.markdown(
                "<br>".join("• " + highlight(c, span) for c in parsed["problematic_claims"]),
                unsafe_allow_html=True,
            )
        st.caption("Answer")
        st.markdown(f"<div>{highlight(parsed['answer'], span)}</div>", unsafe_allow_html=True)
    else:
        st.warning(guardrails.message("ERR_INVALID_JSON"))
        if rec.get("invalid_reason"):
            st.caption(rec["invalid_reason"])
        st.markdown(f"<div>{highlight(rec.get('raw_response', ''), span)}</div>", unsafe_allow_html=True)

    if judge:
        st.caption(f"Judge: {judge['reason']}")
        if span and (not parsed or span not in json_text(parsed)):
            st.caption(f'Invented span: "{span}"')
    if config.FLAG_JUDGE_ERROR in flags:
        st.warning(guardrails.message("ERR_JUDGE_FAILURE"))
        with st.expander("Raw judge output"):
            st.code(rec.get("judge_raw", "") or rec.get("judge_error", ""))
    if parsed:
        with st.expander("Raw model output"):
            st.code(rec.get("raw_response", ""))
    st.caption(f"Latency {rec.get('latency_ms', 0)} ms · {rec.get('timestamp', '')}")


def json_text(parsed: dict) -> str:
    return parsed["answer"] + " ".join(parsed["problematic_claims"])


# -- data access --------------------------------------------------------------
def get_dataset():
    try:
        return store.load_dataset(), None
    except (ValueError, OSError) as exc:
        return [], str(exc)


def default_prompt_ids() -> dict[str, str]:
    return {v: prompts.prompt_id(v, t) for v, t in prompts.load_all_templates().items()}


def active_results() -> list[dict]:
    """Results the dashboard and comparison view should show."""
    if st.session_state.use_cached:
        return store.load_cached()
    ids = set(default_prompt_ids().values())
    return [r for r in store.load_results() if r.get("prompt_id") in ids and r.get("run_mode") == "batch"]


def get_client(on_wait=None) -> GroqClient:
    ss = st.session_state
    return GroqClient(ss.api_key, min_interval=ss.min_interval, on_wait=on_wait)


def require_setup(need_models: bool = True) -> str | None:
    """Return an error message if Settings are incomplete."""
    ss = st.session_state
    if not ss.api_key.strip():
        return guardrails.message("ERR_NO_KEY")
    if need_models and not (ss.model_a and ss.model_b and ss.judge_model):
        return guardrails.message("ERR_MODELS")
    if need_models and ss.model_a == ss.model_b:
        return guardrails.message("ERR_SAME_MODEL")
    return None
