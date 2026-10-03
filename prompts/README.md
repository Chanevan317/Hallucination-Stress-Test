# Prompts

These files are the prompts the app runs. `{question}` is the only placeholder in V1-V3.

> **Source:** V1, V2, V3 and `judge.txt` are Om Bhatt's prompts (`om-bhatt/`), adapted only for the
> app's contract (the judge returns `invented_claim_span`, `identifies_key_claim` and
> `states_correction`, and has a rule that `problematic_claims` are flagged claims, not assertions).
> `judge_live.txt` is the judge used by Live Test, where there is no ground truth.
> To change a prompt, edit the file here. Each change gives the prompt a new id (a hash), so old
> results are never mixed with results from the new text.

| File | Used for |
|---|---|
| `v1.txt` | V1 Baseline |
| `v2.txt` | V2 Guardrail (role + constraints + few-shot) |
| `v3.txt` | V3 Verification (V2 + claim extraction and verification steps) |
| `judge.txt` | Batch judge, has ground truth. Placeholders: `{question}` `{key_false_claim}` `{correct_behaviour}` `{reference_fact}` `{model_response}` |
| `judge_live.txt` | Live Test judge, no ground truth. Placeholders: `{question}` `{model_response}` |

Few-shot examples must not duplicate any question in `data/dataset.json` or `data/unseen_set.json`.
