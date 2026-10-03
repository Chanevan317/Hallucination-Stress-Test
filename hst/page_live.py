"""Live Test screen: a brand-new question through V1 / V2 / V3 side by side."""

import pandas as pd
import streamlit as st

from hst import config, guardrails, prompts, runner, store
from hst.ui_common import get_client, render_card, require_setup

_KEY = "live_question"


def _load_example(text: str) -> None:
    st.session_state[_KEY] = text


def render() -> None:
    ss = st.session_state
    st.header("Live Test")
    st.caption(
        "Type a question the system has never seen. It runs through all three prompt versions on the chosen "
        "model (3 model calls + up to 3 judge calls of the free quota). The judge has no ground truth here, "
        "so it only flags unsupported details."
    )
    if ss.use_cached:
        st.caption("Live Test needs the API, so turn offline mode off in the sidebar.")

    question = st.text_area(
        "Enter a question",
        key=_KEY,
        placeholder="Type an unseen trap question here...",
        height=100,
    )
    n = len(question.strip())
    st.markdown(
        f":red[{n} / {config.MAX_INPUT_CHARS} characters]" if n > config.MAX_INPUT_CHARS else f"{n} / {config.MAX_INPUT_CHARS} characters"
    )

    with st.expander("Insert an example from the held-out set"):
        try:
            for item in store.load_unseen():
                st.button(
                    f"{item['id']}: {item['question'][:80]}", key=f"ex_{item['id']}",
                    on_click=_load_example, args=(item["question"],),
                )
        except (ValueError, OSError) as exc:
            st.caption(f"Held-out set unavailable: {exc}")

    options = [m for m in (ss.model_a, ss.model_b) if m]
    model = st.selectbox("Model", options) if options else None
    clicked = st.button("Run Live Stress Test", type="primary", disabled=ss.use_cached)

    if clicked:
        ok, code, msg = guardrails.check_input(question)
        if not ok:
            st.error(msg)
        elif (err := require_setup()) or model is None:
            st.error(err or guardrails.message("ERR_MODELS"))
        else:
            wait_box = st.empty()
            client = get_client(
                on_wait=lambda s, a, r: wait_box.warning(guardrails.message("ERR_RATE_LIMIT", seconds=s, attempt=a))
            )
            with st.spinner(f"Querying {model} via V1 / V2 / V3..."):
                records, daily = runner.run_live(
                    client,
                    question.strip(),
                    model,
                    prompts.load_all_templates(),
                    prompts.load_judge_template(live=True),
                    ss.judge_model,
                    json_mode=ss.json_mode,
                    accept_fences=ss.accept_fences,
                )
            wait_box.empty()
            if daily:
                st.error(guardrails.message("ERR_DAILY_LIMIT"))
            for col, rec in zip(st.columns(3), records):
                with col:
                    render_card(f"{rec['prompt_version']} {config.VERSION_NAMES[rec['prompt_version']]}", rec, live=True)
    else:
        st.caption("Enter a question above and click 'Run Live Stress Test' to compare prompt defences.")

    with st.expander("Timestamped prompt history (live tests this app has run)"):
        rows = [
            {
                "Timestamp": r.get("timestamp", ""),
                "Question": r["question"][:80],
                "Model": r["model"],
                "Prompt": r["prompt_id"],
                "Verdict": (r.get("parsed") or {}).get("verdict", ",".join(r.get("flags", []))),
                "Judge": (r.get("judge") or {}).get("label", "--"),
            }
            for r in reversed(store.load_live())
        ]
        if rows:
            st.dataframe(pd.DataFrame(rows[:50]), hide_index=True, use_container_width=True)
        else:
            st.caption("Nothing yet.")
