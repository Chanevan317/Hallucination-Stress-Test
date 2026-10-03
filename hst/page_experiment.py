"""Experiment screen: batch run (Mode A) plus the results dashboard."""

import time

import pandas as pd
import streamlit as st

from hst import config, guardrails, metrics, prompts, runner, store
from hst.ui_common import active_results, get_client, get_dataset, require_setup


def _estimate(remaining: int) -> str:
    # each item costs one model call and (usually) one judge call
    seconds = remaining * 2 * max(st.session_state.min_interval, 1.0)
    return f"~{seconds / 60:.0f} min" if seconds >= 90 else f"~{seconds:.0f} s"


def _run_panel(items) -> None:
    ss = st.session_state
    templates = prompts.load_all_templates()
    judge_template = prompts.load_judge_template()
    models = [ss.model_a, ss.model_b]
    pids = {v: prompts.prompt_id(v, t) for v, t in templates.items()}
    existing = {r["key"]: r for r in store.load_results()}
    todo, finished, total = runner.plan_batch(items, models, config.VERSIONS, pids, existing)

    st.subheader("Experiment configuration")
    c1, c2, c3 = st.columns(3)
    c1.metric("Calls finished", f"{finished} / {total}")
    c2.metric("Remaining", len(todo))
    c3.metric("Estimated time left", _estimate(len(todo)) if todo else "--")
    st.caption(
        f"{len(items)} questions × {len(config.VERSIONS)} prompt versions × 2 models = {total} model calls, "
        "plus a judge call each. Finished calls are saved immediately, so a stopped run resumes where it left off."
    )

    start, stop = st.columns([1, 1])
    start_clicked = start.button("Start / Resume Batch Experiment Run", type="primary", disabled=not todo)
    stop.button("Stop Run", help="Stops the run at the current item. Progress is saved.")

    if not todo:
        st.success("All combinations are finished. Results are below.")
        return
    if not start_clicked:
        return

    error = require_setup()
    if error:
        st.error(error)
        return

    status = st.empty()
    bar = st.progress(finished / total if total else 0.0, text=f"Progress: {finished} / {total} calls")
    log_box, preview = st.empty(), st.empty()
    log: list[str] = []
    started = time.time()

    client = get_client(
        on_wait=lambda s, a, r: status.warning(guardrails.message("ERR_RATE_LIMIT", seconds=s, attempt=a))
    )

    def on_progress(done, total_calls, record):
        status.empty()
        bar.progress(done / total_calls, text=f"Progress: {done} / {total_calls} calls")
        label = (record.get("judge") or {}).get("label") or ",".join(record["flags"]) or "?"
        log.append(f"{record['question_id']} · {record['model']} · {record['prompt_version']} → {label}")
        log_box.code("\n".join(log[-12:]), language="text")
        recs = [r for r in store.load_results() if r.get("prompt_id") in pids.values()]
        by_id = {i["id"]: i for i in items}
        m = metrics.compute(recs, by_id)
        preview.caption(
            f"Live hallucination rate (all models/versions): {m['hallucinated']}/{m['traps']} "
            f"({metrics.pct(m['hallucinated'], m['traps'])})"
        )

    outcome = runner.run_batch(
        client,
        items,
        models,
        templates,
        judge_template,
        ss.judge_model,
        json_mode=ss.json_mode,
        accept_fences=ss.accept_fences,
        on_progress=on_progress,
    )
    elapsed = time.time() - started
    if outcome == "daily_limit":
        st.error(guardrails.message("ERR_DAILY_LIMIT"))
    elif outcome == "completed":
        st.success(f"Run completed in {elapsed:.0f} s. Results are below.")
        st.rerun()


def _dashboard(dataset: list[dict]) -> None:
    records = active_results()
    st.divider()
    st.subheader("Results dashboard")
    if not records:
        st.info("No experiment run found. Start a batch run above, or load stored results from the sidebar.")
        return
    by_id = {i["id"]: i for i in dataset}
    grouped = metrics.group(records, by_id)
    models_present = sorted({k[0] for k in grouped})

    version = st.selectbox(
        "Prompt version shown in the summary cards",
        config.VERSIONS,
        index=len(config.VERSIONS) - 1,
        format_func=lambda v: f"{v} {config.VERSION_NAMES[v]}",
    )
    for model in models_present:
        st.markdown(f"**{model}**")
        m, base = grouped.get((model, version)), grouped.get((model, "V1"))
        if not m:
            st.caption(f"No {version} results for this model yet.")
            continue
        cols = st.columns(4)
        delta = None
        if base and version != "V1" and m["hallucination_rate"] is not None and base["hallucination_rate"] is not None:
            delta = f"{m['hallucination_rate'] - base['hallucination_rate']:+.1f} pp vs V1"
        cols[0].metric(
            "Hallucination rate",
            f"{m['hallucinated']}/{m['traps']} ({metrics.pct(m['hallucinated'], m['traps'])})",
            delta=delta,
            delta_color="inverse",
        )
        cols[1].metric("Over-refusal rate", f"{m['over_refusals']}/{m['controls']} ({metrics.pct(m['over_refusals'], m['controls'])})")
        cols[2].metric("Trap detection rate", f"{m['detected']}/{m['traps']} ({metrics.pct(m['detected'], m['traps'])})")
        cols[3].metric("Invalid output rate", f"{m['invalid']}/{m['model_calls']} ({metrics.pct(m['invalid'], m['model_calls'])})")

    st.markdown("**Prompt version × model matrix**")
    table = pd.DataFrame(metrics.rows(grouped))
    st.dataframe(table, hide_index=True, use_container_width=True)

    st.markdown("**Category performance**")
    cat_group = metrics.group(records, by_id, by_category=True)
    cat_table = pd.DataFrame(metrics.rows(cat_group, by_category=True))
    cats = ["All"] + sorted(cat_table["Category"].unique())
    choice = st.selectbox("Filter category", cats)
    if choice != "All":
        cat_table = cat_table[cat_table["Category"] == choice]
    st.dataframe(cat_table, hide_index=True, use_container_width=True)

    c1, c2 = st.columns(2)
    c1.download_button("Export CSV summary", table.to_csv(index=False), "summary.csv", "text/csv")
    if not st.session_state.use_cached and c2.button("Save these results as the offline demo fallback"):
        store.save_cached(records)
        st.success(f"Saved {len(records)} results to results/cached_results.json.")
    pending = [r for r in records if not store.is_finished(r)]
    if pending:
        st.warning(
            f"{len(pending)} results had an API or judge error and are excluded from the rates above. "
            "Resume the run to retry them."
        )


def render() -> None:
    st.header("Experiment")
    dataset, error = get_dataset()
    if error:
        st.error(f"Failed to load the dataset: {error}")
        return
    traps = sum(1 for i in dataset if i["is_trap"])
    st.caption(f"Dataset: {traps} trap / {len(dataset) - traps} control questions loaded.")

    if st.session_state.use_cached:
        st.caption("Offline mode is on. Turn it off in the sidebar to run new experiments.")
    else:
        include_controls = st.checkbox("Include control questions", value=True)
        items = dataset if include_controls else [i for i in dataset if i["is_trap"]]
        _run_panel(items)
    _dashboard(dataset)
