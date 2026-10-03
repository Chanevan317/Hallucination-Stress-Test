"""Prompt Editor screen: edit a prompt template and re-run one question."""

import pandas as pd
import streamlit as st

from hst import config, guardrails, prompts, runner, store
from hst.ui_common import get_client, get_dataset, render_card, require_setup


def _reset(version: str, key: str, default: str) -> None:
    st.session_state[key] = default
    store.append_prompt_history(
        {"version": version, "label": version, "action": "reset", "text": default, "parent": prompts.prompt_id(version, default)}
    )


def render() -> None:
    ss = st.session_state
    st.header("Prompt Editor")
    st.caption(
        "Edit a prompt, then re-run one question to see the effect. Edits are saved to the prompt history as a "
        "new version and never overwrite the default prompt files or earlier results."
    )
    dataset, error = get_dataset()
    if error:
        st.error(f"Failed to load the dataset: {error}")
        return

    version = st.selectbox(
        "Editing target", config.VERSIONS, index=2, format_func=lambda v: f"{v} {config.VERSION_NAMES[v]} Prompt"
    )
    default = prompts.load_template(version)
    history = store.load_prompt_history()
    edits = [h for h in history if h["version"] == version and h["action"] == "edit"]
    key = f"editor_text_{version}"
    if key not in ss:
        ss[key] = edits[-1]["text"] if edits else default
    text = st.text_area("Prompt template (use {question} where the question goes)", key=key, height=380)
    if text != default:
        st.warning(f"You have changes from the default {version} prompt. The default file is not modified.")
    st.button("Reset to Default", on_click=_reset, args=(version, key, default))

    by_id = {i["id"]: i for i in dataset}
    qid = st.selectbox(
        "Test question",
        list(by_id),
        format_func=lambda x: f"{x} [{'TRAP' if by_id[x]['is_trap'] else 'CONTROL'}] {by_id[x]['question'][:80]}",
    )
    options = [m for m in (ss.model_a, ss.model_b) if m]
    model = st.selectbox("Model", options) if options else None

    if st.button("Save & Re-run Question", type="primary", disabled=ss.use_cached):
        problem = prompts.validate_template(text) or require_setup()
        if problem:
            st.error(problem)
        elif model is None:
            st.error(guardrails.message("ERR_MODELS"))
        else:
            label = store.next_edit_label(version, history)
            entry = store.append_prompt_history(
                {
                    "version": version,
                    "label": label,
                    "action": "edit",
                    "text": text,
                    "parent": prompts.prompt_id(version, default),
                    "question_id": qid,
                }
            )
            st.success(guardrails.message("INFO_PROMPT_SAVED", timestamp=entry["timestamp"]) + f" (saved as {label})")
            wait_box = st.empty()
            client = get_client(
                on_wait=lambda s, a, r: wait_box.warning(guardrails.message("ERR_RATE_LIMIT", seconds=s, attempt=a))
            )
            item = by_id[qid]
            default_key = store.result_key(qid, model, prompts.prompt_id(version, default))
            before = next((r for r in store.load_results() if r["key"] == default_key), None)
            try:
                with st.spinner("Re-evaluating..."):
                    after = runner.run_one(
                        client, item, model, version, text, prompts.load_judge_template(), ss.judge_model,
                        json_mode=ss.json_mode, accept_fences=ss.accept_fences, mode="editor",
                    )
                if after.pop("_daily_limit", False):
                    st.error(guardrails.message("ERR_DAILY_LIMIT"))
                store.append_result(after)
                wait_box.empty()
                left, right = st.columns(2)
                with left:
                    render_card(f"Before: default {version}", before)
                with right:
                    render_card(f"After: {label}", after)
            except Exception as exc:  # DailyLimitError and anything unexpected
                wait_box.empty()
                st.error(guardrails.message("ERR_DAILY_LIMIT") if "limit" in str(exc).lower() else guardrails.message("ERR_API", detail=str(exc)))

    with st.expander("Timestamped prompt history"):
        if history:
            st.dataframe(
                pd.DataFrame(history)[["id", "timestamp", "version", "label", "action", "question_id"]].fillna(""),
                hide_index=True, use_container_width=True,
            )
        else:
            st.caption("No edits yet.")
