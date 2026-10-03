"""Metrics, following hetansh-shah/experiment_protocol.md.

Always reported as numerator / denominator. Records whose model call or judge
call failed (API_ERROR / JUDGE_ERROR) are not "evaluated" and are excluded from
the rates, but counted separately so nothing is hidden.
"""

from hst import config, store


def pct(num: int, den: int) -> str:
    return f"{100 * num / den:.1f}%" if den else "--"


def ratio(num: int, den: int) -> float | None:
    return 100 * num / den if den else None


def _evaluated(record: dict) -> bool:
    flags = record.get("flags", [])
    return config.FLAG_API_ERROR not in flags and config.FLAG_JUDGE_ERROR not in flags


def compute(records: list[dict], dataset_by_id: dict[str, dict]) -> dict:
    """Metrics for one group of records (one model + prompt version, or one category)."""
    answered = [r for r in records if config.FLAG_API_ERROR not in r.get("flags", [])]
    evaluated = [r for r in records if _evaluated(r)]
    traps = [r for r in evaluated if r.get("is_trap")]
    controls = [r for r in evaluated if not r.get("is_trap")]

    def label(r):
        return (r.get("judge") or {}).get("label")

    def flag(r, name):
        return bool((r.get("judge") or {}).get(name))

    need_fix = [r for r in traps if store.requires_correction(dataset_by_id.get(r["question_id"], r))]
    out = {
        "traps": len(traps),
        "hallucinated": sum(label(r) == "HALLUCINATED" for r in traps),
        "detected": sum(label(r) == "CORRECT_DEFENSE" and flag(r, "identifies_key_claim") for r in traps),
        "correction_required": len(need_fix),
        "corrected": sum(label(r) == "CORRECT_DEFENSE" and flag(r, "states_correction") for r in need_fix),
        "controls": len(controls),
        "over_refusals": sum(label(r) == "OVER_REFUSAL" for r in controls),
        "control_correct": sum(label(r) == "CORRECT_ANSWER" for r in controls),
        "model_calls": len(answered),
        "invalid": sum(config.FLAG_INVALID in r.get("flags", []) for r in answered),
        "api_errors": sum(config.FLAG_API_ERROR in r.get("flags", []) for r in records),
        "judge_errors": sum(config.FLAG_JUDGE_ERROR in r.get("flags", []) for r in records),
    }
    latencies = [r["latency_ms"] for r in answered if r.get("latency_ms")]
    out["avg_latency_ms"] = round(sum(latencies) / len(latencies)) if latencies else None
    out["hallucination_rate"] = ratio(out["hallucinated"], out["traps"])
    out["over_refusal_rate"] = ratio(out["over_refusals"], out["controls"])
    out["trap_detection_rate"] = ratio(out["detected"], out["traps"])
    out["correction_rate"] = ratio(out["corrected"], out["correction_required"])
    out["invalid_rate"] = ratio(out["invalid"], out["model_calls"])
    return out


def group(records: list[dict], dataset_by_id: dict[str, dict], by_category: bool = False) -> dict:
    """{(model, version): metrics} or {(model, version, category): metrics}."""
    buckets: dict[tuple, list] = {}
    for r in records:
        key = (r["model"], r["prompt_version"])
        if by_category:
            key += (r.get("category", ""),)
        buckets.setdefault(key, []).append(r)
    return {k: compute(v, dataset_by_id) for k, v in sorted(buckets.items())}


def rows(grouped: dict, by_category: bool = False) -> list[dict]:
    """Flatten grouped metrics into table rows with 'n/d (pct)' strings."""
    out = []
    for key, m in grouped.items():
        row = {"Model": key[0], "Prompt": key[1]}
        if by_category:
            row["Category"] = key[2]
        row.update(
            {
                "Hallucination": f"{m['hallucinated']}/{m['traps']} ({pct(m['hallucinated'], m['traps'])})",
                "Over-refusal": f"{m['over_refusals']}/{m['controls']} ({pct(m['over_refusals'], m['controls'])})",
                "Trap detection": f"{m['detected']}/{m['traps']} ({pct(m['detected'], m['traps'])})",
                "Correction": f"{m['corrected']}/{m['correction_required']} ({pct(m['corrected'], m['correction_required'])})",
                "Invalid output": f"{m['invalid']}/{m['model_calls']} ({pct(m['invalid'], m['model_calls'])})",
                "Avg latency (ms)": m["avg_latency_ms"] if m["avg_latency_ms"] is not None else "--",
                "Errors (API/judge)": f"{m['api_errors']}/{m['judge_errors']}",
            }
        )
        out.append(row)
    return out
