# Changelog (prompt history)

**Owner:** Member 1. Timestamps are real: git commit times (IST, 3 October 2026) or file times noted in the row. The git history is the authoritative record (`git log -- prompts om-bhatt`).
**Results rule:** every number comes from the full run on 3 October 2026 (13:45:59 to 14:07:06). Format: numerator/denominator. Question set: the 30 dev questions. Models: gpt-oss-20b and qwen3.8-27b, judge gpt-oss-120b.

## Version table

| Version | Date and time | What changed | Why | Linked failure | Result |
|---|---|---|---|---|---|
| V1 | 12:58, commit `fe268c6` | First version. One plain instruction to answer helpfully, plus the shared JSON format and `{question}`. No factuality technique. | The uncontrolled "before". | n/a (written before any test) | Hallucination 4/40 pooled (A 2/20, B 2/20). Over-refusal 0/20. Invalid output 2/60. |
| V2 | 12:58, commit `fe268c6` | Added a fact-checking role, 6 rules (never invent, check the premise, UNVERIFIABLE when unsure, helpfulness required, OUT_OF_SCOPE, hedged-invention rule) and 4 few-shot examples covering all four verdicts. | Hypothesis: naming the failure types and showing examples lowers acceptance of false premises. Rule 4 and the normal-question example limit over-refusal. | n/a (written before any test) | Hallucination 4/40 pooled (A 3/20, B 1/20). Over-refusal 0/20. Invalid output 0/60. |
| V3 | 12:58, commit `fe268c6` | V2 plus a silent 4-step claim check (list claims, label SUPPORTED/CONTRADICTED/UNKNOWN, choose verdict, answer only from SUPPORTED claims) and claims-first key order. | Hypothesis: checking each claim exposes the hidden false claim. A single-pass approximation of Chain-of-Verification, not the real thing. | n/a (written before any test) | Hallucination 4/40 pooled (A 3/20, B 1/20). **Over-refusal 5/20** (all on gpt-oss-20b: 5/10). Invalid output 0/60. |
| J1 | 12:58, commit `fe268c6` | First batch judge: five labels, ten decision rules, three examples, `[REVIEW]` marker, output with `invented_span`. | Automated grading needs fixed labels and the ground truth. | n/a | Superseded by J2 before the full run. |
| JL1 | about 12:55 (written during the app build; first committed in `26b82b0`, 13:38) | First live judge (for questions with no ground truth), written by Member 2 as a placeholder: three labels INVENTED_DETAILS / NO_INVENTED_DETAILS / NEEDS_REVIEW. | Live Test needs a judge that works without ground truth. | n/a | A live test labelled a correct premise rejection as INVENTED_DETAILS (F-01). |
| JL2 | 13:23 (file time) | Added the "NOTE ON THE RESPONSE FIELDS" paragraph: `problematic_claims` are flagged, not asserted; an empty answer states nothing. | Fix for F-01, an observed failure. | F-01 | Re-checked on the same case: now NO_INVENTED_DETAILS; a made-up person is still INVENTED_DETAILS (2 manual checks, not a measurement). |
| J2 | 13:44 (file time) | Batch judge adapted to the built app: `invented_span` renamed `invented_claim_span`; added `identifies_key_claim` and `states_correction` with field rules; added rule 11 (same note as JL2). Prompt text otherwise unchanged. | The app computes Trap Detection and Correction from the two new fields (gap 1 in J1's notes). Rule 11 is **pre-emptive**, copied from the JL2 fix. | gap 1; F-01 (pre-emptive) | Used for all 180 judgments in the full run: 0 judge errors. |
| V3.1 (proposed) | not run | Proposed: add one more ANSWERABLE example about a basic science fact, and change Rule 5 and Step 3 to say OUT_OF_SCOPE only for requests that are not questions (poems, chat), never for a question that asks for a fact. | Fix proposed for F-04 (V3 refused 5 of 10 normal questions on gpt-oss-20b by copying the off-topic example). **Hypothesis only.** | F-04 | **Not run.** Needs a re-run of V3 on all 30 questions and both models to check that trap defence did not get worse. |
| V3b (optional) | not run | Draft of a two-call variant (Call A checks claims, Call B answers from the checklist). In `prompt_v3.md`. | Closer to real CoVe. Needs a second placeholder, so it does not fit the agreed contract. | n/a | Not run. |

## Summary of the measured result

| Prompt | Hallucination (H/T) | Over-refusal (O/C) | Trap detection (D/T) | Correction (K/F) | Invalid output (I/N) |
|---|---|---|---|---|---|
| V1 Baseline | 4/40 (10.0%) | 0/20 (0.0%) | 33/40 (82.5%) | 20/24 (83.3%) | 2/60 (3.3%) |
| V2 Guardrail | 4/40 (10.0%) | 0/20 (0.0%) | 33/40 (82.5%) | 20/24 (83.3%) | 0/60 (0.0%) |
| V3 Verification | 4/40 (10.0%) | 5/20 (25.0%) | 32/40 (80.0%) | 19/24 (79.2%) | 0/60 (0.0%) |

Pooled over both models, V1, V2 and V3 hallucinated on the same number of trap answers (4 of 40). The hypothesis that V2 and V3 lower hallucination was **not supported**. The clear effects were: V2 and V3 removed invalid output (2/60 to 0/60), and V3 caused over-refusal on one model (0/10 to 5/10).

## How to use this file

1. Commit the prompt change first, then add the row with the real commit time and hash.
2. Never edit an old row. If a change did not help, add a new row that reverts or replaces it.
3. Every refinement row must link to a failure in `failures.md`. A change with no observed failure is a pre-emptive change and must be marked as such.
4. After each harness run, fill the Result column with numerators and denominators, and name the model and question set.

## Which versions go in the final matrix

V1, V2 and V3 (the first versions) are in the full run. No refined version has been run yet; if V3.1 is run, report it as a fourth row, not as a replacement.
