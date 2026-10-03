"""Settings screen: API key, models, request pacing."""

import streamlit as st

from hst import config
from hst.groq_client import GroqClient, GroqError

_NON_CHAT = ("whisper", "tts", "guard", "playai", "orpheus", "embed")


def _model_input(label: str, key: str, help_text: str = "") -> None:
    ss = st.session_state
    if ss.models:
        options = ss.models
        index = options.index(ss[key]) if ss[key] in options else None
        ss[key] = st.selectbox(label, options, index=index, placeholder="Choose a model", help=help_text) or ""
    else:
        ss[key] = st.text_input(label, value=ss[key], help=help_text + " Test your key to load the list.")


def render() -> None:
    ss = st.session_state
    st.header("Settings")
    st.caption(
        "Free Groq tier: requests per minute and per day are limited. Each question costs one call per "
        "model and prompt version plus one judge call; the app paces calls, waits on rate limits, and "
        "pauses cleanly if the daily limit is reached."
    )
    ss.api_key = st.text_input(
        "Groq API key",
        type="password",
        value=ss.api_key,
        help="Held in this browser session only. Never written to results, history or export files.",
    )
    if st.button("Test key & load models"):
        if not ss.api_key.strip():
            st.error("Enter your Groq API key first.")
        else:
            try:
                models = GroqClient(ss.api_key).list_models()
                ss.models = [m for m in models if not any(t in m.lower() for t in _NON_CHAT)]
                for field, default in (("model_a", config.DEFAULT_MODEL_A), ("model_b", config.DEFAULT_MODEL_B),
                                       ("judge_model", config.DEFAULT_JUDGE)):
                    if not ss[field] and default in ss.models:
                        ss[field] = default
                st.success(f"Key works. {len(ss.models)} chat models available.")
            except GroqError as exc:
                st.error(str(exc))

    st.subheader("Models")
    _model_input("Model A", "model_a")
    _model_input("Model B", "model_b", "Use a clearly different model from Model A so the comparison means something.")
    _model_input("Judge model", "judge_model", "A third model, different from A and B, to limit self-grading bias.")
    if ss.model_a and ss.model_a == ss.model_b:
        st.error("Model A and Model B must be different models.")
    if ss.judge_model and ss.judge_model in (ss.model_a, ss.model_b):
        st.warning("The judge is the same as a tested model, which risks self-grading bias. Prefer a third model.")

    st.subheader("Request settings")
    ss.min_interval = st.slider(
        "Minimum seconds between API calls", 0.0, 10.0, float(ss.min_interval), 0.5,
        help="Raise this if you keep hitting rate limits.",
    )
    ss.json_mode = st.checkbox(
        "Use Groq JSON mode for the tested models",
        value=ss.json_mode,
        help="Off by default so the Invalid Output Rate shows whether the prompt itself produces valid JSON.",
    )
    ss.accept_fences = st.checkbox(
        "Accept ```json fences as valid output", value=ss.accept_fences,
        help="Off = strict. Markdown fences count as INVALID_OUTPUT.",
    )
    st.caption(f"Temperature: {config.TEMPERATURE} (fixed). Timeout: {config.REQUEST_TIMEOUT_S} s per call.")
