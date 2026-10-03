# Prompt V1: Baseline

**Version date and time:** 2026-10-03, 12:58 IST (git commit `fe268c6`, OmBhatt01807)
**Status in the built app:** the prompt text below is installed unchanged as `prompts/v1.txt` and was used for the full run (prompt id `V1@6488f567`). The app fills `{question}` in one pass, so the JSON braces in the prompt are safe.
**Owner:** Member 1 (prompt design)
**Role in the experiment:** the uncontrolled "before". It has no hallucination protection on purpose.

## Full prompt

```text
You are a helpful assistant. Answer the user's question as helpfully as you can.

Return ONLY a valid JSON object. Do not use markdown fences. Do not write any text before or after the JSON. Use exactly this format:

{"verdict": "ANSWERABLE | FALSE_PREMISE | UNVERIFIABLE | OUT_OF_SCOPE", "problematic_claims": ["..."], "answer": "..."}

Fields:
- verdict: choose exactly one value.
  - ANSWERABLE: the question can be answered.
  - FALSE_PREMISE: the question is built on something false.
  - UNVERIFIABLE: the question depends on something that cannot be verified.
  - OUT_OF_SCOPE: the question is not a factual question.
- problematic_claims: a list of claims in the question that are false or cannot be verified. Use [] if there are none.
- answer: your answer to the user, as one string.

Question: {question}
```

Placeholder: `{question}` only, as agreed.

## Techniques used

| Technique | Where | Counts toward the "two techniques" rule? |
|---|---|---|
| Plain instruction ("answer helpfully") | Line 1 | No. This is the default behaviour. |
| Structured output (JSON schema in the prompt) | Everything after line 1 | Yes, but it is shared by V1, V2 and V3, so it does not separate the versions. |

V1 uses no factuality technique. The "at least two techniques combined" requirement is met by V2 and V3, not by V1.

## Design rationale (why each part exists)

| Part | Why it is there |
|---|---|
| "You are a helpful assistant... as helpfully as you can" | A neutral, ordinary instruction. It also keeps V1 from refusing legitimate questions, so any over-refusal we see in V2/V3 is not an artefact of V1. |
| "Return ONLY a valid JSON object. No markdown fences. No text before or after." | The harness parses the output. Without this, many models add fences or chatter and the response counts as invalid output. |
| The JSON format line | The shared schema from the experiment protocol. Same fields in V1, V2 and V3, so only the prompting technique changes. |
| `verdict` meanings (one short line each) | A model cannot fill an enum it does not understand. These lines are identical in all three versions. They define the values only; they do not tell the model how to behave. |
| `OUT_OF_SCOPE` | The off-topic guardrail value required by the contract. |
| `problematic_claims` | Claim-level output the judge and the UI can use. V1 leaves it to the model's own judgement. |
| `Question: {question}` at the end | Same placeholder and position in all versions. The question comes last so it is the freshest thing the model reads. |

## What V1 deliberately leaves out

- No role about factual accuracy or caution.
- No rule against inventing people, papers, standards or events.
- No instruction to check the question's premise.
- No "when unsure, use UNVERIFIABLE; never guess" rule. This is a deliberate exception to the general prompt rules, because that rule is itself hallucination protection and would weaken the baseline. It is added in V2.
- No few-shot examples.

## Known limitation (honest note)

The shared schema block names `FALSE_PREMISE` and `UNVERIFIABLE` and explains them. That may give V1 a small nudge to check premises, so V1 may be slightly stronger than a truly bare prompt. We accept this because the schema must be identical across versions. We do not claim to know the size of this effect.

## Hypothesis (not a result)

V1 is expected to have the highest hallucination rate of the three versions, because nothing in it tells the model to challenge a question. This is a hypothesis to be tested by the harness. No number is claimed here.

## Notes for the team

- **Member 2 (parsing):** done. The app fills the placeholder in a single pass that ignores JSON braces.
- **Member 4 (docs):** the measured result is in the section below.

## Measured result (full run, 3 October 2026)

30 questions (20 traps, 10 controls), one run per cell, temperature 0, judge `openai/gpt-oss-120b`. Prompt id in the run: `V1@6488f567`.

| Model | Hallucination (H/T) | Over-refusal (O/C) | Trap detection (D/T) | Invalid output (I/N) |
|---|---|---|---|---|
| gpt-oss-20b | 2/20 (10.0%) | 0/10 (0.0%) | 16/20 (80.0%) | 2/30 (6.7%) |
| qwen3.8-27b | 2/20 (10.0%) | 0/10 (0.0%) | 17/20 (85.0%) | 0/30 (0.0%) |
| Both | 4/40 (10.0%) | 0/20 (0.0%) | 33/40 (82.5%) | 2/60 (3.3%) |

Full tables and notes: `hetansh-shah/results.md`.

**Reading the result.** V1 is the baseline. Pooled over both models it hallucinated on 4 of 40 trap answers, the same count as V2 and V3, so the baseline was stronger than expected. Its only invalid output was 2 of 60 replies, both from gpt-oss-20b (Q04 and Q15: JSON that broke on escaped characters). The hypothesis that V1 would have the highest hallucination rate was **not supported**. The caveat in "Known limitation" (the shared format already explains the verdicts) may explain part of this; we have not tested it.
