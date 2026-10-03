# Prompts

These files are the prompts the app runs. `{question}` is the only placeholder in V1-V3.

> **Status: placeholders.** Member 2 drafted these so the app runs end to end. Om Bhatt's
> prompts (see `om-bhatt/`) replace them: copy each final prompt into the file with the same
> name. No code change is needed. Each change gives the prompt a new id (a hash), so old
> results are never mixed with results from the new text.

| File | Used for |
|---|---|
| `v1.txt` | V1 Baseline |
| `v2.txt` | V2 Guardrail (role + constraints + few-shot) |
| `v3.txt` | V3 Verification (V2 + claim extraction and verification steps) |
| `judge.txt` | Batch judge, has ground truth. Placeholders: `{question}` `{is_trap}` `{key_false_claim}` `{correct_behaviour}` `{reference_fact}` `{model_response}` |
| `judge_live.txt` | Live Test judge, no ground truth. Placeholders: `{question}` `{model_response}` |

Few-shot examples must not duplicate any question in `data/dataset.json` or `data/unseen_set.json`.
