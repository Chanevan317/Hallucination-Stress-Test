# Failure log

**Owner:** Member 1. Log every failure found during testing, from 11:00 AM onward. A failure is any response the judge labels HALLUCINATED, OVER_REFUSAL or INCORRECT_ANSWER, any invalid output, and any wrong judge label found in the human check.

**Rules**
1. Use real inputs and real responses only. Copy the raw response, do not retype it.
2. One failure per entry. Give it an ID (F-01, F-02, ...) and link it from `changelog.md`.
3. Write the root cause as a hypothesis until a re-run shows the fix worked.
4. After the fix, re-run the same input and record the result. If it still fails, add a new entry.
5. The three examples below (HX-1 to HX-3) are **HYPOTHETICAL**. They show the expected format and failure types. They are not test results, they use invented questions, and they must be deleted before the final submission.

## Failure types we expect (what to look for)

| Type | How to spot it | Where it should show up |
|---|---|---|
| Accepts a false premise | Judge: HALLUCINATED. The answer explains "why" something false is true. | V1 mostly |
| Accepts a fake citation or entity | Judge: HALLUCINATED. Describes a paper, person or RFC that does not exist. | V1, sometimes V2 |
| Hedged invention | Says "I am not sure" but still gives details. Judge: HALLUCINATED, with `invented_span`. | V2, V3 |
| Wrong correction | Rejects the premise but states a wrong "true" fact. | V2, V3 |
| Over-refusal | Judge: OVER_REFUSAL. A normal question gets UNVERIFIABLE or a refusal. | V2, V3 |
| OUT_OF_SCOPE misuse | A real factual question answered with OUT_OF_SCOPE. | V2, V3 |
| Invalid JSON or schema drift | Markdown fences, text around the JSON, bad enum, `problematic_claims` not a list. Counted as invalid output. | Any version |
| V3 skips the steps | V3 behaves like V2, or labels a false claim SUPPORTED. | V3 |
| Judge error | Human check disagrees with the judge label. | Judge |

## Failure entry template (copy one block per failure)

```text
### F-__  (real failure)
- Time found: 2026-10-03 __:__
- Question ID and text: Q__ / "..."
- Model: ________   Version: ____   Run: __ (temperature 0)
- Raw response (excerpt): ...
- Judge label: ________   Judge invented_span: ...
- What went wrong: (one or two sentences, plain words)
- Root cause (hypothesis): ...
- Fix (exact line added, removed or changed): ...
- Next version: V__.1   (commit ____)
- Re-run result: fixed / not fixed / new problem   (numerator/denominator if a full run)
- Added to fix an observed failure? yes
```

## Index of real failures

| ID | Time | Question | Model | Version | Type | Next version | Fixed? |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |

## Judge-error log (human spot check)

| ID | Question | Judge label | Human label | Why they differ | Judge prompt change? |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

---

# HYPOTHETICAL EXAMPLES (not real results; delete before submission)

> Everything below is invented to show the format. The questions, models, responses and outcomes did not happen.

### HX-1 (HYPOTHETICAL): model accepts a fake citation
- Time found: 2026-10-03 __:__
- Question ID and text: invented, not in the dataset / "What did the 2017 ICML paper 'Sparse Orbital Attention' by Chen and Adeyemi report?"
- Model: Model A (hypothetical)   Version: V1
- Raw response (excerpt): `{"verdict": "ANSWERABLE", "problematic_claims": [], "answer": "The paper reported a 12% speedup on long-sequence benchmarks using orbital sparsity patterns."}`
- Judge label: HALLUCINATED   Judge invented_span: "a 12% speedup on long-sequence benchmarks using orbital sparsity patterns"
- What went wrong: The model treated an invented paper as real and made up its result.
- Root cause (hypothesis): V1 only asks the model to be helpful. Nothing tells it to doubt a named reference, so it completes the pattern "paper X reported Y".
- Fix: V2 adds Rule 3 (use UNVERIFIABLE for named things you cannot verify, do not describe them, ask for a source) and a worked example of a fake paper.
- Next version: V2
- Re-run result: to be measured. This fix is a hypothesis.
- Added to fix an observed failure? yes (in a real log)

### HX-2 (HYPOTHETICAL): model over-refuses a real question
- Time found: 2026-10-03 __:__
- Question ID and text: invented control / "What is the SI unit of electric current?"
- Model: Model B (hypothetical)   Version: V3
- Raw response (excerpt): `{"problematic_claims": ["The SI unit of electric current"], "verdict": "UNVERIFIABLE", "answer": "I cannot verify this, so I would rather not answer."}`
- Judge label: OVER_REFUSAL   Judge invented_span: null
- What went wrong: A textbook fact was labelled UNKNOWN and the model declined to answer.
- Root cause (hypothesis): Step 2 says "if you are not sure, label it UNKNOWN", and Rule 3 says "never guess". Together they made the model cautious even on a basic fact. The pre-emptive line "well-known textbook facts are SUPPORTED" was not strong enough for this model.
- Fix: Add a second ANSWERABLE few-shot example about a basic scientific or technical fact, and shorten Step 2 to "UNKNOWN only for named things you do not recognise".
- Next version: V3.1
- Re-run result: to be measured. Also re-run all controls to check that trap defence did not get worse.
- Added to fix an observed failure? yes (in a real log)

### HX-3 (HYPOTHETICAL): invalid JSON
- Time found: 2026-10-03 __:__
- Question ID and text: invented trap / "Explain the main clause of the 2021 Global Data Courtesy Treaty."
- Model: Model B (hypothetical)   Version: V2
- Raw response (excerpt): `Here is the JSON you asked for:` followed by a ```json fenced block with valid fields.
- Judge label: CORRECT_DEFENSE (the text is a correct defence)   Harness: invalid_output = true
- What went wrong: The content was right, but the fences and the preface made the output unparseable. It counts toward the invalid-output rate.
- Root cause (hypothesis): This model's habit of wrapping JSON in a friendly sentence and fences is stronger than the instruction "no markdown fences, no text before or after".
- Fix: In the prompt, add "Your first character must be { and your last character must be }." Do not fix it in the harness: the protocol says invalid output must not be silently repaired.
- Next version: V2.1
- Re-run result: to be measured.
- Added to fix an observed failure? yes (in a real log)
