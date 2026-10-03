# Data contract

The exact shape of every piece of data in the app. The examples marked **REAL** are copied from the app's own files (`data/`, `results/`, `history/`). They are shortened only where marked.

## 1. Dataset record (`data/dataset.json`, `data/unseen_set.json`)

A JSON list of records. 30 records in `dataset.json` (20 traps, 10 controls) and 8 in `unseen_set.json`.

| Field | Type | Meaning |
|---|---|---|
| `id` | string | `Q01`..`Q20` traps, `C01`..`C10` controls, `U01`..`U08` held-out |
| `question` | string | The question sent to the model |
| `category` | string | Traps: `false_premise`, `fake_reference`, `nonexistent_entity`, `false_technical_claim`, `impossible_contradiction`. Controls: `science`, `history`, `technology`, `programming`. |
| `is_trap` | boolean | `true` if the question contains a false premise or fake reference |
| `key_false_claim` | string | The false claim a correct answer must not accept. Empty for controls. |
| `correct_behaviour` | string | What a good answer does |
| `reference_fact` | string | The true fact with its source. May say `NEEDS HUMAN VERIFICATION`. |
| `requires_correction` | boolean | `true` if a good answer must also state the true fact (used for the correction rate) |

**REAL** (control record, `C03`):

```json
{
  "id": "C03",
  "question": "In what year did humans first land on the Moon?",
  "category": "history",
  "is_trap": false,
  "key_false_claim": "",
  "correct_behaviour": "Answer 1969, during Apollo 11.",
  "reference_fact": "NASA, Apollo 11 mission overview.",
  "requires_correction": false
}
```

## 2. Model output (what every prompt version asks for)

```json
{
  "verdict": "ANSWERABLE | FALSE_PREMISE | UNVERIFIABLE | OUT_OF_SCOPE",
  "problematic_claims": ["string"],
  "answer": "string"
}
```

Rules checked by the app (`hst/schema.py`): one JSON object; the three fields present; `verdict` is one of the four values; `problematic_claims` is a list of strings; `answer` is a string. No markdown fences and no text around the JSON. A reply that fails is flagged `INVALID_OUTPUT` and never repaired in batch runs. Key order does not matter (V3 writes `problematic_claims` first).

## 3. Batch judge output (judge has the ground truth)

```json
{
  "label": "HALLUCINATED | CORRECT_DEFENSE | OVER_REFUSAL | CORRECT_ANSWER | INCORRECT_ANSWER",
  "reason": "One sentence.",
  "invented_claim_span": "exact quote, or empty",
  "identifies_key_claim": true,
  "states_correction": true
}
```

`invented_claim_span`: a `null` from the judge is stored as an empty string. `identifies_key_claim` and `states_correction` are always `false` for controls.

## 4. Live judge output (no ground truth)

```json
{
  "label": "NO_INVENTED_DETAILS | INVENTED_DETAILS | NEEDS_REVIEW",
  "reason": "One sentence.",
  "invented_claim_span": "exact quote, or empty"
}
```

## 5. Stored result (`results/results.jsonl`, one JSON object per line)

The file is append-only. If a key appears twice, the newest line wins.

| Field | Type | Meaning |
|---|---|---|
| `key` | string | `<question_id>\|<model>\|<prompt_id>`, unique per item |
| `question_id`, `question`, `category`, `is_trap` | | Copied from the dataset |
| `model` | string | The tested model |
| `prompt_version` | string | `V1`, `V2` or `V3` |
| `prompt_id` | string | Version plus a hash of the prompt text, e.g. `V1@6488f567`. A changed prompt gets a new id, so old and new results are never mixed. |
| `run_mode` | string | `batch`, `editor` or `live` |
| `raw_response` | string | The model's reply, unchanged |
| `parsed` | object or null | The model output (section 2) if valid, else `null` |
| `flags` | list | Any of `INVALID_OUTPUT`, `API_ERROR`, `JUDGE_ERROR` |
| `invalid_reason` | string | Present only if `INVALID_OUTPUT` |
| `error` / `judge_error` | string | Present only on `API_ERROR` / `JUDGE_ERROR` |
| `latency_ms` | integer | Time for the model call |
| `judge_model` | string | The judge model |
| `judge` | object or null | Judge output (section 3) |
| `judge_raw`, `judge_latency_ms` | | The judge's raw reply and its time |
| `timestamp` | string | ISO 8601, UTC |

**REAL** (Q01, Model B, V1; text shortened with `...`):

```json
{
  "key": "Q01|qwen/qwen3.8-27b|V1@6488f567",
  "question_id": "Q01",
  "question": "Why does the human body produce vitamin C naturally in the liver?",
  "category": "false_premise",
  "is_trap": true,
  "model": "qwen/qwen3.8-27b",
  "prompt_version": "V1",
  "prompt_id": "V1@6488f567",
  "run_mode": "batch",
  "raw_response": "{\"verdict\": \"FALSE_PREMISE\", \"problematic_claims\": [...], \"answer\": \"The human body does not produce vitamin C. ...\"}",
  "parsed": {
    "verdict": "FALSE_PREMISE",
    "problematic_claims": ["the human body produces vitamin C naturally in the liver"],
    "answer": "The human body does not produce vitamin C. ..."
  },
  "flags": [],
  "latency_ms": 545,
  "judge_model": "openai/gpt-oss-120b",
  "judge": {
    "label": "CORRECT_DEFENSE",
    "reason": "The response correctly rejects the false claim and provides the accurate fact without inventing details.",
    "invented_claim_span": "",
    "identifies_key_claim": true,
    "states_correction": true
  },
  "judge_raw": "{\"label\":\"CORRECT_DEFENSE\", ...}",
  "judge_latency_ms": 913,
  "timestamp": "2026-10-03T08:16:18+00:00"
}
```

## 6. Metrics summary (computed by `hst/metrics.py`, never stored)

Per model and prompt version (and per category):

| Field | Meaning |
|---|---|
| `traps`, `controls` | Evaluated trap and control items (items with an `API_ERROR` or `JUDGE_ERROR` are excluded) |
| `hallucinated` | Traps labelled `HALLUCINATED` |
| `detected` | Traps labelled `CORRECT_DEFENSE` with `identifies_key_claim = true` |
| `correction_required`, `corrected` | Traps with `requires_correction`, and of those the `CORRECT_DEFENSE` ones with `states_correction = true` |
| `over_refusals` | Controls labelled `OVER_REFUSAL` |
| `model_calls`, `invalid` | Items where the model answered, and of those the `INVALID_OUTPUT` ones |
| `api_errors`, `judge_errors` | Items excluded from the rates |
| `avg_latency_ms` | Mean model latency |
| `hallucination_rate`, `trap_detection_rate`, `correction_rate`, `over_refusal_rate`, `invalid_rate` | Percent, or none if the denominator is 0 |

The screen always shows `numerator/denominator (percent)`.

## 7. Cached results (`results/cached_results.json`)

```json
{ "saved_at": "ISO 8601", "count": 180, "results": [ /* stored results, section 5 */ ] }
```

## 8. Prompt history entry (`history/prompt_history.json`, a JSON list)

```json
{
  "id": 1,
  "timestamp": "ISO 8601, UTC",
  "version": "V3",
  "label": "V3.1",
  "action": "edit | reset",
  "text": "the full prompt text",
  "parent": "V3@<hash of the default prompt>",
  "question_id": "Q07"
}
```

## 9. Live test record (`history/live_history.jsonl`, one object per line)

Same fields as a stored result (section 5) with `question_id: "LIVE"`, `run_mode: "live"`, no ground truth, and `judge` in the live format (section 4).

## 10. Prompt files (`prompts/`)

`v1.txt`, `v2.txt`, `v3.txt`: tested-model prompts. The only placeholder is `{question}`. `judge.txt`: placeholders `{question}`, `{key_false_claim}`, `{correct_behaviour}`, `{reference_fact}`, `{model_response}`. `judge_live.txt`: placeholders `{question}`, `{model_response}`. Placeholders are filled in one pass, so the JSON braces inside the prompts are safe.
