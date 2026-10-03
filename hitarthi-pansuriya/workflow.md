# Workflow and guardrails

How the finished app works, step by step. Everything here matches the code in `hst/` (see `hst/runner.py`, `hst/groq_client.py`, `hst/guardrails.py`).

## Shared setup (all modes)

- All models run through the free **Groq API**. The user pastes the API key on the **Settings** screen. The key lives only in the browser session and is never written to results, history or exports.
- Three models: **Model A** (default `openai/gpt-oss-20b`), **Model B** (default `qwen/qwen3.8-27b`), and a **judge** (default `openai/gpt-oss-120b`). The judge must be a different model so no model grades itself.
- Temperature is always 0. Calls are paced (default 2.5 s between calls) to respect the free-tier limits.

## Mode A: Batch experiment

Trigger: **Start / Resume Batch Experiment Run** on the Experiment screen.

```
[Load data/dataset.json] --invalid--> [Stop: "Failed to load the dataset: ..."]
        |
        v
[Plan: 30 questions x 2 models x 3 prompt versions = 180 items; skip items already finished]
        |
        v   (question by question, so each question gets all 6 results before the next)
[Call tested model with the prompt for this version]
        |-- network / server error --> retry up to 2 times (waits 2 s, 4 s) --> still failing: save API_ERROR, go on
        |-- 429 rate limit ----------> wait as Groq instructs, retry (up to 5 times), show "Rate limited, retrying in N s"
        |-- daily limit -------------> PAUSE the run (finished items are already saved)
        v
[Check the reply is valid JSON in the agreed format]
        |-- invalid --> flag INVALID_OUTPUT, keep the raw text, NO repair (counts in the rates)
        v
[Judge model grades the reply against the ground truth]  (also grades invalid replies, using the raw text)
        |-- judge reply invalid --> retry once with a bigger token budget --> still invalid: flag JUDGE_ERROR
        |-- daily limit during the judge call --> save the model reply anyway, flag JUDGE_ERROR, PAUSE
        v
[Append the result to results/results.jsonl immediately]
        v
[Update progress bar, log and the live hallucination rate; next item]
        v
[All 180 finished] --> compute metrics --> results dashboard
```

Step list:

1. **Validate the dataset.** Every record needs `id, question, category, is_trap, key_false_claim, correct_behaviour, reference_fact`. Otherwise the run does not start.
2. **Plan the run.** Items already finished are skipped, so a stopped run resumes where it left off. An item that only failed at the judge step is re-judged without asking the model again (saves quota).
3. **Call the model** with the prompt for that version, with `{question}` filled in.
4. **Validate the output strictly.** It must be one JSON object with `verdict` (one of four values), `problematic_claims` (list of strings) and `answer` (string). Markdown fences or extra text make it invalid, unless the Settings option *Accept json fences* is on.
5. **Judge.** The judge gets the question, the ground truth (`key_false_claim`, `correct_behaviour`, `reference_fact`) and the model's raw reply, and returns a label.
6. **Save and show progress.** Each result is written to disk before the next call starts.
7. **Stop.** Press **Stop Run** (or click anywhere else). Nothing is lost; click Start / Resume to continue.

## Mode B: Live Test (one new question)

Trigger: **Run Live Stress Test** on the Live Test screen.

1. **Input check.** Empty or longer than 500 characters: blocked with an inline error, no API call.
2. **Settings check.** No API key or no models chosen: blocked with an error.
3. **Run V1, V2 and V3** on the chosen model (3 model calls). Invalid JSON gets **one retry** in live mode.
4. **Off-topic.** If a version answers `OUT_OF_SCOPE`, the card shows the guardrail alert and the judge is skipped.
5. **Judge without ground truth.** The live judge only checks whether the answer states specific details (names, dates, numbers, citations) as fact that look made up. Labels: `NO_INVENTED_DETAILS`, `INVENTED_DETAILS`, `NEEDS_REVIEW`.
6. **Show three cards side by side** with verdict, flagged claims, answer, judge label, latency and timestamp.
7. **Log** every card to `history/live_history.jsonl` (shown in the "Timestamped prompt history" drawer).

A live question uses up to 6 calls of the free quota.

## Mode C: Prompt Editor re-run

1. Pick a version (V1, V2 or V3), edit the template, pick a dataset question and a model.
2. **Save & Re-run Question.** The edit must still contain `{question}`; otherwise it is rejected and not saved.
3. The edit is saved to `history/prompt_history.json` with a timestamp and a label (for example `V3.1`). The default prompt files are not changed.
4. The question runs once with the edited prompt and is graded by the normal judge (it has ground truth).
5. The screen shows **Before** (the default prompt's stored result, if any) next to **After**.

## Offline fallback

If Groq is down or the quota is gone during the demo: tick **Use stored results (offline)** in the sidebar. The Experiment dashboard and Side-by-Side screens then read `results/cached_results.json`. To create that file, finish a run and click **Save these results as the offline demo fallback**.

## Guardrail matrix

| ID | Situation | How it is detected | What the system does | What the user sees |
|---|---|---|---|---|
| `INVALID_OUTPUT` | Model reply is not valid JSON in the agreed format | JSON parse fails, a field is missing, or the verdict is not one of the four values | Batch: flag, keep raw text, still judge it, count it. Live: retry once, then flag. Never repaired silently. | Grey `INVALID_OUTPUT` badge, the raw text, and: "Model output was not valid JSON. Raw text retained for inspection." |
| `ERR_INPUT_EMPTY` | Empty live question | Length is 0 after trimming | Blocks the call | "Input cannot be empty. Please enter a valid question." |
| `ERR_INPUT_TOO_LONG` | Live question over 500 characters | Length check | Blocks the call | "Input length exceeds limit (500 characters max). Current length: N." |
| `OUT_OF_SCOPE` | Off-topic input | The model's verdict is `OUT_OF_SCOPE` | Live: show alert, skip the judge. Batch: judged by content like any other answer; never counted as a success by default. | Yellow `OUT_OF_SCOPE` badge and "GUARDRAIL ALERT: Query flagged as OUT_OF_SCOPE. Unhandled domain query rejected safely." |
| Refusal on a trap | Trap question, model says `FALSE_PREMISE` or `UNVERIFIABLE` and invents nothing | Judge label `CORRECT_DEFENSE` | Counts as a successful defense | Green `CORRECT_DEFENSE` badge |
| Refusal on a normal question | Control question, model refuses | Judge label `OVER_REFUSAL` | Counts toward the over-refusal rate | Amber `OVER_REFUSAL` badge |
| `ERR_RATE_LIMIT` | Groq 429 | HTTP 429 | Waits as instructed and retries | "Rate limited, retrying in N s (attempt K)." |
| `ERR_DAILY_LIMIT` | Daily quota reached | Groq message mentions a daily limit, or the wait is over 120 s | Pauses; finished items are saved | "Daily limit reached, run paused. Finished calls are saved; resume later or use stored results." |
| `API_ERROR` | Network error, server error, bad key, bad model | Request fails after 2 retries | Saves an `API_ERROR` record; the item is retried on the next resume | Red message "API error: ..." on the card |
| `JUDGE_ERROR` | Judge reply invalid | Judge JSON fails the check twice | Saves the model reply with `JUDGE_ERROR`; only the judge is repeated on resume | Grey `JUDGE_ERROR` badge and "Judge model failed to evaluate this output. Raw output shown unverified." |
| `ERR_NO_KEY` | No API key | Empty key field | Blocks the call | "Enter your Groq API key in Settings first." |
| `ERR_MODELS` | Models not chosen | Empty model fields | Blocks the call | "Pick Model A, Model B and a judge model in Settings first." |
| `ERR_SAME_MODEL` | Model A equals Model B | Name comparison | Blocks the call | "Model A and Model B must be different models." |
| Template check | Prompt edit lacks `{question}` | Placeholder check | Rejects, does not save | "Prompt template must contain the {question} placeholder." |
