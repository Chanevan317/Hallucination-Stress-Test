# Hallucination Stress Test: problem analysis

## Problem and users

Language models can answer a question built on a false premise fluently instead of challenging it. The risk is highest for fabricated papers, people, standards, dates and technical claims. This project tests whether factuality-focused prompting reduces invented claims **without** making the model refuse ordinary questions.

Target users are hackathon judges, developers evaluating an LLM, and researchers who want a small, inspectable reliability test.

Member 3 owns the research question, the labelled data, the held-out data, the evaluation definitions and the experiment protocol. The app is built by Member 2, the prompts are written by Member 1, and the workflow and UI documents are written by Member 4.

## Requirements (as built)

| Requirement | How the finished app meets it |
|---|---|
| At least 20 trap questions | 20 traps in `dataset.json`, four in each of five categories |
| Control questions to catch over-refusal | 10 legitimate questions (`C01`..`C10`) |
| 3 prompt versions, 2 models | V1 Baseline, V2 Guardrail, V3 Verification on two Groq models |
| Automated evaluation | A third model grades every reply against the ground truth |
| Hallucination, over-refusal, trap-detection, correction, invalid-output rates | Computed by the app and shown as `numerator/denominator` |
| Unseen input | Live Test screen, plus 8 held-out questions in `unseen_set.json` |
| Guardrails: invalid output, off-topic input, refusals | Strict JSON check, `OUT_OF_SCOPE` verdict, judge labels for refusals |

The full matrix is 30 questions x 3 prompt versions x 2 models = **180 model calls and 180 judge calls**.

## Hypothesis

Explicit trap checks and claim-verification instructions lower the hallucination rate on traps while keeping correct answers on controls. This is an empirical hypothesis. The measured outcome is in `results.md`, and it is reported whether or not it supports the hypothesis.

## Operational definition

A **hallucination** is a reply that accepts or elaborates a false, nonexistent, contradicted or unsupported claim in a trap question as though it were factual. A reply that rejects the key false claim and invents nothing is a **correct defense**. On a control question, a refusal is an **over-refusal** and a materially wrong answer is an **incorrect answer** (not a hallucination).

## The data

| Set | Size | Use |
|---|---|---|
| `dataset.json` | 20 traps + 10 controls | The measured experiment. Every record has `key_false_claim`, `correct_behaviour`, `reference_fact` and `requires_correction`. |
| `unseen_set.json` | 5 traps + 3 controls | Held-out questions for the live demo. Never shown to the prompt writer, and not used in the measured results. |

Trap categories: false premise, fake reference, nonexistent entity, false technical claim, impossible or contradictory claim. Three trap records (Q05, Q06, Q11) and two held-out records (U02, U03) rest on "no reliable source was located" and are marked NEEDS HUMAN VERIFICATION. See `verification_checklist.md`.

## Research background

- **HaluEval** (Li et al., 2023, arXiv:2305.11747) motivates a labelled, adversarial test set. Ours is much smaller and is not a reproduction.
- **SelfCheckGPT** (Manakul, Liusie and Gales, 2023, arXiv:2303.08896) uses agreement between sampled replies as a signal. Not implemented: we run each cell once.
- **Chain-of-Verification** (Dhuliawala et al., 2023, arXiv:2309.11495) drafts verification questions, answers them independently and revises. **V3 is only a single-pass approximation**, because everything happens in one generation.
- **FActScore** (Min et al., 2023, EMNLP) breaks answers into atomic claims and checks support. The judge's `invented_claim_span` and the model's `problematic_claims` borrow this claim-level view.

The paper titles and identifiers above should be checked against the organisers' preferred bibliography before formal publication.

## Mapping research to implementation

| Idea | Where it appears |
|---|---|
| Adversarial benchmark (HaluEval) | `dataset.json` |
| Claim-level checking (FActScore) | V3 steps, `problematic_claims`, judge span |
| Verify before answering (CoVe) | V3 (single-pass approximation) |
| Consistency across samples (SelfCheckGPT) | Not implemented |
