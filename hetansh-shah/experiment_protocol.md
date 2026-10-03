# Experiment protocol

## Shared model-output schema

V1, V2, and V3 must require exactly this schema; only prompting technique changes:

```json
{
  "verdict": "ANSWERABLE | FALSE_PREMISE | UNVERIFIABLE | OUT_OF_SCOPE",
  "problematic_claims": ["string"],
  "answer": "string"
}
```

`OUT_OF_SCOPE` is needed for the app's off-topic guardrail. It is not a factuality verdict and must not be counted as a trap defense or a control refusal unless the question is genuinely legitimate and the model used it improperly.

## Prompting techniques

- **V1 baseline:** direct answer instruction; no special factuality technique.
- **V2:** factuality-first role, explicit constraints against accepting false premises, and 3–4 few-shot examples.
- **V3:** V2 plus claim extraction and a verify-before-answer checklist. This is a single-pass approximation of Chain-of-Verification, not true CoVe; true CoVe requires a separate verification call.

Few-shot examples for V2/V3 must come from a separate prompt-authoring file and must not be any question in `dataset.json` or `unseen_set.json`. Suggested examples: “Who was the 1840 winner of the Nobel Prize in Computer Science?” (no such category), “What is the capital of France?” (Paris), “What does the fictional JavaScript method `Array.prototype.teleport()` return?” (not standard), and “What year did Apollo 11 land on the Moon?” (1969).

## Labels and validation

The judge labels are defined in `judge_prompt.md`. Validate the model response against the shared schema before judging. `invalid_output=true` if JSON cannot be parsed, a required field is missing, an enum is invalid, `problematic_claims` is not a list of strings, or `answer` is not a string. Do not silently repair invalid output.

## Metrics

Compute separately for each model and prompt version, then optionally aggregate.

- **Hallucination Rate (primary):** `H / T`, where `H` is trap cases labelled `HALLUCINATED` and `T` is the number of trap questions evaluated. The denominator is all trap questions, including failed/invalid responses.
- **Over-Refusal Rate:** `O / C`, where `O` is controls labelled `OVER_REFUSAL` and `C` is the number of controls evaluated.
- **Trap Detection Rate:** `D / T`, where `D` is trap responses labelled `CORRECT_DEFENSE` **and** the response identifies the specific `key_false_claim` (or an unmistakable equivalent). This is not defined as `1 - Hallucination Rate`; vague refusals do not count.
- **Correction Rate:** `K / F`, where `K` is trap responses that both have `CORRECT_DEFENSE` and state the relevant corrected fact when `correct_behaviour` requires one, and `F` is traps whose `correct_behaviour` requires correction. Report `N/A` if `F=0`.
- **Invalid Output Rate:** `I / N`, where `I` is invalid model outputs and `N` is all model evaluations. Report separately from judge labels.

Percentages are `100 × numerator / denominator`; report numerator and denominator as well as the percentage. Do not count a control's incorrect answer as a hallucination.

## Settings and run plan

Use temperature `0`, record model name/version, prompt version/hash, timestamp, raw response, validation result, judge JSON, and latency. Run each question once for the hackathon. If time permits, run three times per cell and use a predeclared majority label; also report disagreement. Temperature zero is not a guarantee of determinism because providers can change backend versions and serving details.

The minimum matrix is `30 questions × 3 prompt versions × 2 models = 180 model evaluations`. The primary comparison is within the same question set, model, and prompt version.

## Empty results template

| Model | Prompt | Trap H/T | Hallucination rate | Control O/C | Over-refusal rate | Trap D/T | Detection rate | Correction K/F | Correction rate | Invalid I/N | Invalid rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|  | V1 |  |  |  |  |  |  |  |  |  |  |
|  | V2 |  |  |  |  |  |  |  |  |  |  |
|  | V3 |  |  |  |  |  |  |  |  |  |  |
