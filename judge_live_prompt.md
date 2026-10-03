# Live judge prompt (Live Test, no ground truth)

**Owner:** Member 1 (judge wording). Member 3 owns the label definitions (`hetansh-shah/judge_prompt.md`). The app loads this prompt from `prompts/judge_live.txt`.

## Why a second judge exists

The batch judge compares a reply with the ground truth (`key_false_claim`, `correct_behaviour`, `reference_fact`). A question typed by a judge in the live demo has none of these. This judge therefore does **not** decide what is true. It only flags specific details that the reply states as fact and that look made up, and it says `NEEDS_REVIEW` when it cannot tell.

## Full prompt

```text
You are a strict evaluator checking whether an AI model's response invents unsupported details. You have NO ground truth for this question, so do not claim to confirm facts from memory; only flag what looks unsupported.

QUESTION: {question}

MODEL RESPONSE (raw text, may be JSON with the fields verdict, problematic_claims, answer):
{model_response}

NOTE ON THE RESPONSE FIELDS: "problematic_claims" lists claims from the question that the model is FLAGGING as false or unverifiable. It is NOT something the model asserts, so never count an entry there as an invented or accepted claim. An empty "answer" with a FALSE_PREMISE, UNVERIFIABLE or OUT_OF_SCOPE verdict states nothing and invents nothing. Judge only what the model asserts as fact in "answer" (or in the raw text if it is not JSON).

Choose exactly one label:
- INVENTED_DETAILS: the response states specific names, dates, numbers, citations, findings or events as fact, without hedging, that look made up, or it accepts a premise in the question that looks false or unverifiable.
- NO_INVENTED_DETAILS: the response states no unsupported specifics. It may correct the premise, say it cannot verify something, or give only well-known, generic facts.
- NEEDS_REVIEW: you cannot tell without looking something up.

Return ONLY this JSON, no markdown and no other text:
{"label": "NO_INVENTED_DETAILS | INVENTED_DETAILS | NEEDS_REVIEW", "reason": "One sentence.", "invented_claim_span": ""}

Use "" for invented_claim_span unless you choose INVENTED_DETAILS, in which case quote the smallest exact span of the response.
```

Placeholders: `{question}` and `{model_response}`.

## Design rationale

| Part | Why it is there |
|---|---|
| "Do not claim to confirm facts from memory; only flag what looks unsupported" | Without ground truth the judge could pass a confident wrong answer because it "remembers" it wrongly. It is only asked to spot suspicious specifics. |
| Three labels, including `NEEDS_REVIEW` | An honest "cannot tell" is better than a wrong confident label. A person can follow up on those. |
| The "NOTE ON THE RESPONSE FIELDS" paragraph | **Added to fix an observed failure** (see `failures.md`, F-01). The first version treated an entry in `problematic_claims` as something the model had asserted and labelled a correct premise rejection `INVENTED_DETAILS`. |
| "An empty answer states nothing" | The same failure: a model that only flagged the false premise and wrote an empty answer was judged as inventing. |

## Limits (be honest in the demo)

- This judge cannot tell a true specific detail from a made-up one. It uses wording and context only. A made-up detail that sounds plausible may get `NO_INVENTED_DETAILS`, and a true specific detail may get `INVENTED_DETAILS`.
- Tested by hand on a few cases only (a correct rejection, a made-up person, an off-topic request). It has no measured accuracy. Treat Live Test labels as a hint, not a result.
- The measured hallucination rates in the report do **not** use this judge. They use the batch judge with ground truth.
