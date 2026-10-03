"""Reading and writing the dataset, results, cached results and histories."""

import json
from datetime import datetime, timezone

from hst import config


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# -- dataset ------------------------------------------------------------
def requires_correction(item: dict) -> bool:
    """Whether a trap's expected behaviour includes stating a correction.

    Uses an explicit 'requires_correction' field if the dataset has one,
    otherwise a keyword heuristic on correct_behaviour.
    """
    if "requires_correction" in item:
        return bool(item["requires_correction"])
    if not item.get("is_trap"):
        return False
    text = item.get("correct_behaviour", "").lower()
    return any(word in text for word in ("correct", "reject the", "explain", "identify"))


def validate_dataset(items) -> str | None:
    if not isinstance(items, list) or not items:
        return "Dataset is empty or not a list."
    seen = set()
    for i, item in enumerate(items):
        missing = [f for f in config.DATASET_FIELDS if f not in item]
        if missing:
            return f"Record {i} ({item.get('id', '?')}) is missing fields: {', '.join(missing)}."
        if item["id"] in seen:
            return f"Duplicate id {item['id']}."
        seen.add(item["id"])
    return None


def load_dataset(path=config.DATASET_FILE) -> list[dict]:
    items = json.loads(path.read_text(encoding="utf-8"))
    error = validate_dataset(items)
    if error:
        raise ValueError(error)
    return items


def load_unseen() -> list[dict]:
    return load_dataset(config.UNSEEN_FILE)


# -- results --------------------------------------------------------------
def result_key(question_id: str, model: str, prompt_id: str) -> str:
    return f"{question_id}|{model}|{prompt_id}"


def append_result(record: dict, path=None) -> None:
    path = path or config.RESULTS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()


def load_results(path=None) -> list[dict]:
    """All results, newest record winning per key (append-only file)."""
    path = path or config.RESULTS_FILE
    if not path.exists():
        return []
    latest: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue  # tolerate a half-written last line
        latest[record["key"]] = record
    return list(latest.values())


def is_finished(record: dict) -> bool:
    flags = record.get("flags", [])
    return config.FLAG_API_ERROR not in flags and config.FLAG_JUDGE_ERROR not in flags


def load_cached(path=None) -> list[dict]:
    path = path or config.CACHED_FILE
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("results", [])


def save_cached(records: list[dict], path=None) -> None:
    path = path or config.CACHED_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"saved_at": now_iso(), "count": len(records), "results": records}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")


# -- prompt history ---------------------------------------------------------
def load_prompt_history(path=None) -> list[dict]:
    path = path or config.PROMPT_HISTORY_FILE
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def append_prompt_history(entry: dict, path=None) -> dict:
    path = path or config.PROMPT_HISTORY_FILE
    history = load_prompt_history(path)
    entry = {"id": len(history) + 1, "timestamp": now_iso(), **entry}
    history.append(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, ensure_ascii=False, indent=1), encoding="utf-8")
    return entry


def next_edit_label(version: str, history: list[dict]) -> str:
    n = sum(1 for h in history if h.get("version") == version and h.get("action") == "edit")
    return f"{version}.{n + 1}"


def append_live(record: dict, path=None) -> None:
    path = path or config.LIVE_HISTORY_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_live(path=None) -> list[dict]:
    path = path or config.LIVE_HISTORY_FILE
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out
