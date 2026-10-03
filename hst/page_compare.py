"""Side-by-side screen: one dataset question across V1 / V2 / V3."""

import streamlit as st

from hst import config
from hst.ui_common import active_results, get_dataset, render_card


def render() -> None:
    st.header("Side-by-Side Comparison")
    dataset, error = get_dataset()
    if error:
        st.error(f"Failed to load the dataset: {error}")
        return
    records = active_results()
    if not records:
        st.info("No result data available. Run the batch experiment or use stored results.")
        return

    by_id = {i["id"]: i for i in dataset}
    ids = [i["id"] for i in dataset if any(r["question_id"] == i["id"] for r in records)]
    qid = st.selectbox(
        "Select question",
        ids,
        format_func=lambda x: f"{x} [{'TRAP' if by_id[x]['is_trap'] else 'CONTROL'}] {by_id[x]['question'][:90]}",
    )
    models = sorted({r["model"] for r in records if r["question_id"] == qid})
    model = st.radio("Target model", models, horizontal=True)

    item = by_id[qid]
    st.markdown(f"**{item['question']}**")
    st.caption(
        f"Category: {item['category']} · {'TRAP' if item['is_trap'] else 'CONTROL'} · "
        f"Key false claim: {item['key_false_claim'] or '—'}"
    )
    st.caption(f"Expected: {item['correct_behaviour']}")

    lookup = {(r["question_id"], r["model"], r["prompt_version"]): r for r in records}
    cols = st.columns(3)
    for col, version in zip(cols, config.VERSIONS):
        with col:
            render_card(f"{version} {config.VERSION_NAMES[version]}", lookup.get((qid, model, version)))
