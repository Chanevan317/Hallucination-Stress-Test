"""The test harness: run models, validate, judge, save. Resumable and quota-aware."""

from hst import config, prompts, schema, store
from hst.groq_client import ApiError, DailyLimitError


def _judge_values(item: dict, raw: str) -> dict:
    return {
        "question": item["question"],
        "is_trap": "yes" if item.get("is_trap") else "no",
        "key_false_claim": item.get("key_false_claim", ""),
        "correct_behaviour": item.get("correct_behaviour", ""),
        "reference_fact": item.get("reference_fact", ""),
        "model_response": raw,
    }


def judge_response(client, judge_model, template, values, *, live=False):
    """Returns (judge_dict | None, judge_raw, latency_ms, error | None). Retries once."""
    prompt = prompts.fill(template, **values)
    raw, latency, error = "", 0, None
    for attempt in range(2):
        try:
            res = client.chat(
                judge_model, prompt, json_mode=True, max_tokens=config.JUDGE_MAX_TOKENS * (attempt + 1)
            )
        except ApiError as exc:
            error = str(exc)
            continue
        raw, latency = res.text, res.latency_ms
        parsed, error = schema.parse_judge_output(res.text, live=live)
        if parsed is not None:
            return parsed, raw, latency, None
    return None, raw, latency, error


def run_one(
    client,
    item: dict,
    model: str,
    version: str,
    template: str,
    judge_template: str,
    judge_model: str,
    *,
    json_mode: bool = False,
    accept_fences: bool = False,
    mode: str = "batch",
    existing: dict | None = None,
) -> dict:
    """Run one question x model x prompt version and return the stored record.

    If `existing` only failed at the judge step, the saved model output is
    reused and only the judge call is repeated (saves free-tier quota).
    """
    pid = prompts.prompt_id(version, template)
    rejudge = bool(
        existing
        and config.FLAG_JUDGE_ERROR in existing.get("flags", [])
        and config.FLAG_API_ERROR not in existing.get("flags", [])
    )
    if rejudge:
        record = dict(existing)
        record["flags"] = [f for f in existing["flags"] if f != config.FLAG_JUDGE_ERROR]
        record.pop("judge_error", None)
    else:
        record = {
            "key": store.result_key(item["id"], model, pid),
            "question_id": item["id"],
            "question": item["question"],
            "category": item.get("category", ""),
            "is_trap": bool(item.get("is_trap")),
            "model": model,
            "prompt_version": version,
            "prompt_id": pid,
            "run_mode": mode,
            "raw_response": "",
            "parsed": None,
            "flags": [],
            "latency_ms": 0,
            "judge_model": judge_model,
            "judge": None,
            "judge_raw": "",
            "judge_latency_ms": 0,
        }
        try:
            res = client.chat(model, prompts.fill(template, question=item["question"]), json_mode=json_mode)
        except ApiError as exc:
            record["flags"] = [config.FLAG_API_ERROR]
            record["error"] = str(exc)
            record["timestamp"] = store.now_iso()
            return record
        record["raw_response"] = res.text
        record["latency_ms"] = res.latency_ms
        parsed, error = schema.parse_model_output(res.text, accept_fences=accept_fences)
        record["parsed"] = parsed
        if parsed is None:
            record["flags"].append(config.FLAG_INVALID)
            record["invalid_reason"] = error

    if record["raw_response"].strip():
        try:
            judge, judge_raw, jlat, jerr = judge_response(
                client, judge_model, judge_template, _judge_values(item, record["raw_response"])
            )
        except DailyLimitError as exc:
            # Keep the model output (already paid for); only the judge call is repeated on resume.
            judge, judge_raw, jlat, jerr = None, "", 0, str(exc)
            record["_daily_limit"] = True
        record["judge"], record["judge_raw"], record["judge_latency_ms"] = judge, judge_raw, jlat
        if judge is None:
            record["flags"].append(config.FLAG_JUDGE_ERROR)
            record["judge_error"] = jerr
    record["timestamp"] = store.now_iso()
    return record


def plan_batch(items, models, versions, prompt_ids, existing_by_key):
    """Split the full matrix into (todo, finished_count, total)."""
    todo, finished = [], 0
    for item in items:
        for model in models:
            for version in versions:
                key = store.result_key(item["id"], model, prompt_ids[version])
                rec = existing_by_key.get(key)
                if rec and store.is_finished(rec):
                    finished += 1
                else:
                    todo.append((item, model, version, rec))
    return todo, finished, len(items) * len(models) * len(versions)


def run_batch(
    client,
    items,
    models,
    templates,
    judge_template,
    judge_model,
    *,
    results_path=None,
    json_mode=False,
    accept_fences=False,
    on_progress=None,
    should_stop=lambda: False,
) -> str:
    """Run the whole matrix. Returns 'completed', 'stopped' or 'daily_limit'."""
    pids = {v: prompts.prompt_id(v, t) for v, t in templates.items()}
    existing = {r["key"]: r for r in store.load_results(results_path)}
    todo, finished, total = plan_batch(items, models, list(templates), pids, existing)
    done = finished
    for item, model, version, rec in todo:
        if should_stop():
            return "stopped"
        try:
            record = run_one(
                client,
                item,
                model,
                version,
                templates[version],
                judge_template,
                judge_model,
                json_mode=json_mode,
                accept_fences=accept_fences,
                existing=rec,
            )
        except DailyLimitError:
            return "daily_limit"
        limit_hit = record.pop("_daily_limit", False)
        store.append_result(record, results_path)
        if store.is_finished(record):
            done += 1
        if on_progress:
            on_progress(done, total, record)
        if limit_hit:
            return "daily_limit"
    return "completed"


def run_live(
    client,
    question: str,
    model: str,
    templates,
    judge_live_template,
    judge_model,
    *,
    json_mode=False,
    accept_fences=False,
):
    """Run one unseen question through V1/V2/V3 with the ground-truth-free judge.

    Returns (records, daily_limit_hit). Invalid JSON gets one retry in live mode;
    OUT_OF_SCOPE answers skip the judge.
    """
    item = {"id": "LIVE", "question": question, "category": "live", "is_trap": None}
    records, daily_limit = [], False
    for version, template in templates.items():
        pid = prompts.prompt_id(version, template)
        record = {
            "key": f"LIVE|{model}|{pid}|{store.now_iso()}",
            "question_id": "LIVE",
            "question": question,
            "model": model,
            "prompt_version": version,
            "prompt_id": pid,
            "run_mode": "live",
            "raw_response": "",
            "parsed": None,
            "flags": [],
            "latency_ms": 0,
            "judge_model": judge_model,
            "judge": None,
        }
        if daily_limit:
            record["flags"] = [config.FLAG_API_ERROR]
            record["error"] = "Skipped: daily limit reached."
            records.append(record)
            continue
        try:
            for attempt in range(2):  # live mode may retry invalid JSON once
                res = client.chat(model, prompts.fill(template, question=question), json_mode=json_mode)
                parsed, error = schema.parse_model_output(res.text, accept_fences=accept_fences)
                record["raw_response"], record["latency_ms"], record["parsed"] = res.text, res.latency_ms, parsed
                if parsed is not None:
                    break
            if record["parsed"] is None:
                record["flags"].append(config.FLAG_INVALID)
                record["invalid_reason"] = error
            skip_judge = record["parsed"] is not None and record["parsed"]["verdict"] == "OUT_OF_SCOPE"
            if record["raw_response"].strip() and not skip_judge:
                values = {"question": question, "model_response": record["raw_response"]}
                judge, judge_raw, jlat, jerr = judge_response(
                    client, judge_model, judge_live_template, values, live=True
                )
                record["judge"], record["judge_raw"], record["judge_latency_ms"] = judge, judge_raw, jlat
                if judge is None:
                    record["flags"].append(config.FLAG_JUDGE_ERROR)
                    record["judge_error"] = jerr
        except DailyLimitError as exc:
            daily_limit = True
            record["flags"] = [config.FLAG_API_ERROR]
            record["error"] = str(exc)
        except ApiError as exc:
            record["flags"] = [config.FLAG_API_ERROR]
            record["error"] = str(exc)
        record["timestamp"] = store.now_iso()
        records.append(record)
    for record in records:
        store.append_live(record)
    return records, daily_limit
