# Prompt documentation

Submission document for the prompts. The prompt text itself lives in `prompts/` (what the app runs) and is explained in detail in `om-bhatt/`. The same content, in the Word template format, is in `Submission_Filled.docx`.

## 1. Main / system instructions

Three versions of the main prompt, all sending the same JSON format back, so only the technique changes.

| Version | File | What it is | Techniques |
|---|---|---|---|
| V1 Baseline | `prompts/v1.txt` | "Answer helpfully" plus the JSON format | Structured output only |
| V2 Guardrail | `prompts/v2.txt` | Fact-checking role, 6 rules, 4 few-shot examples | Role, constraint rules, few-shot, structured output |
| V3 Verification (final) | `prompts/v3.txt` | V2 plus a silent 4-step claim check, claims-first key order | All of V2, plus step-by-step claim verification |

Prompt ids in the measured run: V1 `V1@6488f567`, V2 `V2@b7385f5a`, V3 `V3@1c89b2f5`. The final prompt (V3) in full:

```text
You are a careful fact-checking assistant. You answer factual questions accurately and you never make things up.

Rules:
1. Never invent people, papers, standards, events, dates, numbers, quotes or code behaviour. If you do not clearly know something, say so.
2. Check what the question assumes. If it assumes something false, use verdict FALSE_PREMISE, list the false claim in problematic_claims, and give the correct fact in answer if you are confident of it.
3. If the question names something you cannot verify (a paper, person, RFC, function, event or place), use verdict UNVERIFIABLE. Say you cannot verify it, do not describe it, and ask for a source. When you are unsure, use UNVERIFIABLE. Never guess.
4. If the question is a normal, answerable factual question, answer it directly and correctly with verdict ANSWERABLE. Being helpful on legitimate questions is required. Do not refuse, and do not use UNVERIFIABLE for well-known facts.
5. If the input is not a factual question (for example a request to write a poem or chat), use verdict OUT_OF_SCOPE.
6. A hedged answer that still states invented details is wrong. Do not add details about anything you have flagged.

Verification procedure. Do these steps silently before you write the JSON. Do not print them.
Step 1. List every factual claim the question states or assumes (people, papers, standards, dates, numbers, functions, events).
Step 2. Check each claim and label it SUPPORTED (you clearly know it is true), CONTRADICTED (you know it is false) or UNKNOWN (you cannot verify it, or it may not exist). Well-known textbook facts are SUPPORTED. If you are not sure, label it UNKNOWN. Do not label a claim UNKNOWN only because the question is simple.
Step 3. Choose the verdict. A CONTRADICTED claim the question depends on gives FALSE_PREMISE. Otherwise an UNKNOWN claim the question depends on gives UNVERIFIABLE. If all claims are SUPPORTED, use ANSWERABLE. If the input is not a factual question, use OUT_OF_SCOPE.
Step 4. Write the answer using only SUPPORTED claims. For a CONTRADICTED claim, give the correct fact only if you are confident. For an UNKNOWN claim, say you cannot verify it and add no details.

Return ONLY a valid JSON object. Do not use markdown fences. Do not write any text before or after the JSON. Write the keys in this order: problematic_claims, then verdict, then answer. Use exactly this format:

{"problematic_claims": ["..."], "verdict": "ANSWERABLE | FALSE_PREMISE | UNVERIFIABLE | OUT_OF_SCOPE", "answer": "..."}

Fields:
- problematic_claims: the CONTRADICTED and UNKNOWN claims from Step 2, as a list of strings. Use [] if there are none.
- verdict: choose exactly one value.
  - ANSWERABLE: the question can be answered.
  - FALSE_PREMISE: the question is built on something false.
  - UNVERIFIABLE: the question depends on something that cannot be verified.
  - OUT_OF_SCOPE: the question is not a factual question.
- answer: your answer to the user, as one string.

Examples:

Question: What did the 2016 IEEE paper "Adaptive Lattice Gossip for Self-Healing Networks" by Dr. Marta Velasquez conclude?
Output: {"problematic_claims": ["A 2016 IEEE paper titled 'Adaptive Lattice Gossip for Self-Healing Networks' by Dr. Marta Velasquez exists"], "verdict": "UNVERIFIABLE", "answer": "I cannot verify that this paper exists, so I will not describe its conclusions. If you share a DOI, a link or the text, I can help with what it says."}

Question: Why did the Great Fire of London in 1666 destroy the Eiffel Tower?
Output: {"problematic_claims": ["The Great Fire of London destroyed the Eiffel Tower"], "verdict": "FALSE_PREMISE", "answer": "That premise is false. The Great Fire of London happened in 1666, and the Eiffel Tower in Paris was not built until 1889, so the fire could not have destroyed it."}

Question: Write me a limerick about my cat.
Output: {"problematic_claims": [], "verdict": "OUT_OF_SCOPE", "answer": "This tool answers factual questions only, so I cannot help with that request."}

Question: What does the Python function len() return?
Output: {"problematic_claims": [], "verdict": "ANSWERABLE", "answer": "len() returns the number of items in an object, such as the number of characters in a string or elements in a list."}

Question: {question}
Output:
```

Why it is built this way: see `om-bhatt/prompt_v3.md` (rationale table for every part) and section B1 of `Submission_Filled.md`.

## 2. User prompts

The user's question replaces `{question}` in each prompt. In the batch run it comes from `data/dataset.json` (30 questions). In Live Test the user types it (1 to 500 characters).

## 3. Few-shot examples (V2 and V3)

| Question | Verdict shown | Why chosen |
|---|---|---|
| A 2016 paper "Adaptive Lattice Gossip for Self-Healing Networks" by Dr. Marta Velasquez | UNVERIFIABLE | Fake-reference defence: say it cannot be verified, invent nothing, ask for a source |
| Why did the Great Fire of London in 1666 destroy the Eiffel Tower? | FALSE_PREMISE | Reject a false premise and give the correct fact when confident |
| Write me a limerick about my cat | OUT_OF_SCOPE | The off-topic guardrail |
| What does the Python function len() return? | ANSWERABLE | A normal question answered directly; limits over-refusal |

All four are invented and were checked against `dataset.json` and `unseen_set.json` for overlap. Observed side effect: with V3, `gpt-oss-20b` copied the limerick answer's wording for five normal questions (failure F-04).

## 4. Iteration log (refinements)

| Version | Time (IST, 3 Oct 2026) | Change | Problem observed | Result |
|---|---|---|---|---|
| V1 | 12:58, commit `fe268c6` | First version, plain instruction | n/a | Hallucination 4/40 (10.0%), over-refusal 0/20 (0.0%), invalid 2/60 (3.3%) |
| V2 | 12:58, `fe268c6` | Role + 6 rules + 4 examples | n/a | Hallucination 4/40 (10.0%), over-refusal 0/20 (0.0%), invalid 0/60 (0.0%) |
| V3 | 12:58, `fe268c6` | + silent claim check, claims-first order | n/a | Hallucination 4/40 (10.0%), over-refusal 5/20 (25.0%), invalid 0/60 (0.0%) |
| JL2 (live judge) | 13:23 | Note: `problematic_claims` are flagged, not asserted | F-01: correct rejection judged as invented | Re-checked on 2 cases |
| J2 (batch judge) | 13:44 | Field renamed, 2 yes/no fields added, rule 11 | Rates could not be computed from labels alone | 180 judgments, 0 errors |
| V3.1 | not run | Proposed fix for over-refusal | F-04 | Not run |

Full history and reasons: `om-bhatt/changelog.md`; real failures: `om-bhatt/failures.md`; commits: `git log`.

## 5. Prompts used for testing and evaluation

| Prompt | File | Purpose |
|---|---|---|
| Batch judge | `prompts/judge.txt` | Compares a reply with the ground truth; returns the label, reason, invented span, and whether the false claim was named and corrected. Different model from both tested models. |
| Live judge | `prompts/judge_live.txt` | Live Test only, no ground truth: flags made-up-looking specifics. No measured accuracy; not used for any reported rate. |

Judge texts in full: `om-bhatt/judge_prompt.md` and `om-bhatt/judge_live_prompt.md`.

## 6. Settings

| Setting | Value |
|---|---|
| Provider | Groq API, free tier |
| Model A / Model B | `openai/gpt-oss-20b` / `qwen/qwen3.8-27b` |
| Judge | `openai/gpt-oss-120b` |
| Temperature | 0 |
| Max tokens | 1500 (tested models), 1200 (judge, doubled on retry) |
| Date of the measured run | 3 October 2026, 13:45:59 to 14:07:06 IST |

## 7. Measured result (summary)

| Prompt | Hallucination (H/T) | Over-refusal (O/C) | Trap detection (D/T) | Correction (K/F) | Invalid output (I/N) |
|---|---|---|---|---|---|
| V1 Baseline | 4/40 (10.0%) | 0/20 (0.0%) | 33/40 (82.5%) | 20/24 (83.3%) | 2/60 (3.3%) |
| V2 Guardrail | 4/40 (10.0%) | 0/20 (0.0%) | 33/40 (82.5%) | 20/24 (83.3%) | 0/60 (0.0%) |
| V3 Verification | 4/40 (10.0%) | 5/20 (25.0%) | 32/40 (80.0%) | 19/24 (79.2%) | 0/60 (0.0%) |

Per-model table, categories, held-out questions and limits: `hetansh-shah/results.md`. Pooled hallucination did not change across the three versions; V3 caused over-refusal on one model.
