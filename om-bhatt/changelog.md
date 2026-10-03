# Changelog (prompt history)

**Owner:** Member 1. Date: 2026-10-03. Timestamps must come from git commits (11:00 AM onward). Do not backdate.
**Results rule:** no number goes in the Result column unless the harness produced it. Until then: "TBD - measured by the harness".

## Version table

| Version | Date and time | What changed | Why | Linked failure | Result |
|---|---|---|---|---|---|
| V1 | 2026-10-03 __:__ (commit `____`) | First version. One plain instruction to answer helpfully, plus the shared JSON schema and the `{question}` placeholder. No factuality technique. | The uncontrolled "before". Gives the baseline hallucination rate. Hypothesis: highest hallucination rate of the three. | n/a (written before any test) | TBD - measured by the harness |
| V2 | 2026-10-03 __:__ (commit `____`) | Added: a fact-checking role; 6 rules (never invent, check the premise, UNVERIFIABLE when unsure, helpfulness required, OUT_OF_SCOPE, hedged-invention rule); 4 few-shot examples covering all four verdicts; `Output:` cue. Schema block unchanged. | Hypothesis: naming the failure types and showing examples lowers acceptance of false premises and fake references. Rule 4 and the last example (a normal question) are there to limit over-refusal. | n/a (written before any test) | TBD - measured by the harness |
| V3 | 2026-10-03 __:__ (commit `____`) | V2 plus a silent 4-step claim check (list claims, label SUPPORTED / CONTRADICTED / UNKNOWN, choose verdict, answer only from SUPPORTED claims). JSON keys written in the order `problematic_claims`, `verdict`, `answer`. Same four examples as V2, reordered to claims-first. | Hypothesis: checking each claim separately exposes the one hidden false claim, and writing the claims before the verdict makes the verdict follow from them. Single-pass approximation of Chain-of-Verification, not true CoVe. | n/a (written before any test) | TBD - measured by the harness |
| J1 | 2026-10-03 __:__ (commit `____`) | First judge prompt: five labels, 10 decision rules, strict JSON (`label`, `reason`, `invented_span`), 3 invented examples, `[REVIEW]` marker. | Automated grading needs fixed labels and the ground truth. Hedging rule added so hedged inventions are not missed. | n/a (written before any test) | TBD - measured by the harness and a human spot check |
| V3b (optional) | Not run | Draft of a two-call variant: Call A checks claims, Call B answers from the checklist. Needs a second placeholder `{checklist}`. | Closer to real CoVe. Only used if Member 2 and Member 3 agree to change the contract. | n/a | Not run |

## Refinement rows (add one row per change, after testing starts)

Copy this row for every edit. Change one thing per version where possible, so the effect can be traced.

| Version | Date and time | What changed | Why | Linked failure | Result |
|---|---|---|---|---|---|
| V__.1 | 2026-10-03 __:__ (commit `____`) | Exact lines added, removed or reworded. | The failure seen, quoted from `failures.md`, and the reason this edit should fix it (a hypothesis). | F-__ | TBD - measured by the harness |

## How to use this file

1. Commit the prompt change first, then add the row with the real commit time and hash.
2. Never edit an old row. If a change did not help, add a new row that reverts or replaces it.
3. Every refinement row must link to a failure in `failures.md`. A change with no observed failure is not a refinement.
4. After each harness run, fill the Result column with the numerator and denominator (for example "H 7/20"), not only a percentage, as the protocol requires. Name the model and the question set (dev set or unseen set).
5. Label every prompt line you add as "to fix an observed failure" or "pre-emptive". Judges will ask.

## Which versions go in the final matrix

The stretch task needs 3 prompt versions across 2 models. Proposed rule: report the **first** version of each (V1, V2, V3) and the **final** refined version of whichever prompt changed, so the before-and-after story is visible. Member 3 and Member 4 should confirm this before the report is written.
