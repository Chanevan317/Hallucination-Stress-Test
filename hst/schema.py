"""Validation of model and judge JSON output."""

import json
import re

from hst import config

_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.S | re.I)


def _strip_fences(raw: str) -> str:
    m = _FENCE.match(raw.strip())
    return m.group(1) if m else raw.strip()


def _extract_object(raw: str) -> str:
    """Lenient extraction for the judge: first '{' to last '}'."""
    text = _strip_fences(raw)
    start, end = text.find("{"), text.rfind("}")
    return text[start : end + 1] if start != -1 and end > start else text


def parse_model_output(raw: str, *, accept_fences: bool = False):
    """Strictly validate a tested model's output.

    Returns (parsed_dict | None, error_message | None). No silent repair:
    fenced or chatty output is invalid unless accept_fences is enabled.
    """
    text = _strip_fences(raw) if accept_fences else raw.strip()
    if not text:
        return None, "Empty response."
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"Not valid JSON: {exc.msg}"
    if not isinstance(data, dict):
        return None, "JSON is not an object."
    for key in ("verdict", "problematic_claims", "answer"):
        if key not in data:
            return None, f"Missing required field '{key}'."
    if data["verdict"] not in config.VERDICTS:
        return None, f"Invalid verdict {data['verdict']!r}."
    claims = data["problematic_claims"]
    if not isinstance(claims, list) or not all(isinstance(c, str) for c in claims):
        return None, "'problematic_claims' must be a list of strings."
    if not isinstance(data["answer"], str):
        return None, "'answer' must be a string."
    return data, None


def parse_judge_output(raw: str, *, live: bool = False):
    """Validate judge output (lenient about fences/chatter around the JSON)."""
    try:
        data = json.loads(_extract_object(raw))
    except json.JSONDecodeError as exc:
        return None, f"Judge output is not valid JSON: {exc.msg}"
    if not isinstance(data, dict):
        return None, "Judge JSON is not an object."
    labels = config.LIVE_LABELS if live else config.BATCH_LABELS
    if data.get("label") not in labels:
        return None, f"Invalid judge label {data.get('label')!r}."
    if not isinstance(data.get("reason"), str):
        return None, "Judge 'reason' must be a string."
    span = data.get("invented_claim_span", "")
    if span is None:
        span = ""
    if not isinstance(span, str):
        return None, "Judge 'invented_claim_span' must be a string."
    data["invented_claim_span"] = span
    if not live:
        for key in ("identifies_key_claim", "states_correction"):
            if not isinstance(data.get(key), bool):
                return None, f"Judge '{key}' must be true or false."
    return data, None
