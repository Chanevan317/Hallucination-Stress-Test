# Prompt V3: Verification

**Version date and time:** 2026-10-03, __:__ (fill from the git commit time)
**Owner:** Member 1 (prompt design)
**Builds on:** V2. All six V2 rules, the role and the same four examples are kept. V3 adds a claim-checking procedure and a claims-first output order.

## Full prompt

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

Placeholder: `{question}` only.

## Techniques used

| Technique | Where | New in V3? |
|---|---|---|
| Role prompting | First line | No (from V2) |
| Constraint instructions | Rules 1 to 6 | No (from V2) |
| Few-shot examples (4) | Examples block | No (same examples as V2, reordered to claims-first) |
| Structured output (JSON) | Format block | No (shared) |
| Step-by-step claim verification | Verification procedure, Steps 1 to 4 | **Yes** |
| Claims-first output order | "Write the keys in this order" | **Yes** |

Six techniques are combined. The brief requires at least two across the final version.

## Design rationale (why each part exists)

| Part | Why it is there |
|---|---|
| Rules 1 to 6 and the role | Kept from V2 so V3 differs from V2 only by the verification step. If V3 beats V2, the cause should be the step, not other wording. |
| Step 1: list the claims | A trap usually hides in one claim ("RFC 9512 defines X", "TCP guarantees exactly-once"). Listing claims separately makes the hidden one visible instead of being absorbed into the question's topic. This idea comes from claim-level checking (FActScore). |
| Step 2: SUPPORTED / CONTRADICTED / UNKNOWN | Three labels, not two. UNKNOWN is the safe state for fake references: the model does not have to say "true" or "false", only "I cannot confirm". This is the main route to UNVERIFIABLE. |
| Step 2: "Well-known textbook facts are SUPPORTED... not UNKNOWN only because the question is simple" | Over-refusal guard inside the new step. A checking procedure can make a model doubt everything. This line pushes back. It is a prediction, not a fix for an observed failure. |
| Step 2: "If you are not sure, label it UNKNOWN" | Same rule as V2's "never guess", applied per claim. |
| Step 3: verdict from the labels | Makes the verdict follow from the checking rather than from a first impression. CONTRADICTED beats UNKNOWN because a known-false claim can be corrected. |
| Step 4: "answer using only SUPPORTED claims" | The core requirement. Details about CONTRADICTED or UNKNOWN claims are where invented content appears. |
| "Do these steps silently... Do not print them" | The contract says the output is the shared JSON only, and an extra text block would count as invalid output. So the steps cannot be shown. |
| Keys in order: `problematic_claims`, `verdict`, `answer` | A model writes left to right. If `problematic_claims` comes first, the model commits to which claims are bad before it chooses a verdict and writes the answer. This gives some visible, in-output checking that does not break the JSON-only rule. Key order is ignored by JSON parsers, so the schema is unchanged. |
| `problematic_claims` = CONTRADICTED and UNKNOWN claims | Links the output field to the procedure. Judges can see which claims the model flagged. |
| Same four examples as V2 | The examples cannot show silent steps, so they stay as in V2 (only key order changed). Keeping them equal keeps the comparison fair. They were checked for overlap with the test sets (see `prompt_v2.md`). |

## Honest limits: this is not true Chain-of-Verification

Chain-of-Verification (CoVe) drafts an answer, writes verification questions, answers those questions **separately**, and then revises. The separate step is what makes it work: the verification is not influenced by the draft.

V3 is a **single-pass approximation**. Everything happens in one generation, and the model checks claims while it is already reading the question and writing the answer. That means:

- The checking is silent, so we cannot audit it. We only see the result in `problematic_claims`, `verdict` and `answer`.
- A model that is not good at reasoning silently may skip the steps. The prompt cannot enforce them.
- The model may "check" a false claim with the same belief that caused the error, so it may still label it SUPPORTED.

We must not call V3 "CoVe" in the demo. Say: "V3 is a single-pass approximation of the verification idea."

## Hypotheses (not results)

- H1: V3 lowers hallucination rate compared with V2, mainly on fake references and technical traps.
- H2: V3 may raise over-refusal on controls, because UNKNOWN labels make the model more cautious. Watch C01 to C10.
- H3: Claims-first key order may improve verdict quality. We have not tested it separately.
- H4: Gains from V3 over V2 may be smaller than gains from V2 over V1.
- Results: TBD - measured by the harness.

## Lines added to fix an observed failure

None yet. This version was written before any test run.

## Optional V3b: separate-call variant (draft, untested)

V3b is closer to real CoVe because verification happens in its own call, before the answer is written. It is **not** part of the main 3-version matrix, because it needs two calls and a second placeholder, and the contract says each prompt takes `{question}` and nothing else. Use it only if Member 2 and Member 3 agree to change the contract, and treat it as an extra experiment.

**Call A: verify (input `{question}`)**

```text
You are a strict fact-checker. You do not answer the question. You only check its claims.

List every factual claim the question states or assumes. Label each one SUPPORTED (you clearly know it is true), CONTRADICTED (you know it is false) or UNKNOWN (you cannot verify it, or it may not exist). Well-known textbook facts are SUPPORTED. If you are not sure, use UNKNOWN. Never guess.

Return ONLY a valid JSON object with no markdown fences and no other text:

{"claims": [{"claim": "...", "label": "SUPPORTED | CONTRADICTED | UNKNOWN", "note": "one short reason or the correct fact if you are confident"}]}

Question: {question}
```

**Call B: answer (inputs `{question}` and `{checklist}`, where `{checklist}` is Call A's JSON)**

```text
You are a careful fact-checking assistant. A fact-checker has already labelled the claims in the question. Answer using only the claims labelled SUPPORTED. Do not describe claims labelled UNKNOWN: say you cannot verify them and ask for a source. Correct claims labelled CONTRADICTED using the checker's note, if there is one. If every claim is SUPPORTED, answer the question directly and helpfully. Never refuse a legitimate question. If the input is not a factual question, use OUT_OF_SCOPE.

Return ONLY a valid JSON object with no markdown fences and no other text, in exactly this format:

{"verdict": "ANSWERABLE | FALSE_PREMISE | UNVERIFIABLE | OUT_OF_SCOPE", "problematic_claims": ["..."], "answer": "..."}

Where problematic_claims lists the CONTRADICTED and UNKNOWN claims (or [] if none).

Question: {question}
Checklist: {checklist}
```

Open risks for V3b: Call B trusts Call A, so a wrong label in A is copied into B. Call B has no few-shot examples, so a comparison with V3 would also change that technique. Latency roughly doubles. If the team uses V3b, add examples to Call B and record it as a new version in `changelog.md`.

## Notes for the team

- **Member 2:** V3's JSON key order is `problematic_claims`, `verdict`, `answer`. Validate by key name, not by position. Insert the question with `.replace("{question}", question)`.
- **Member 2:** V3 is the longest prompt. Expect more input tokens and slightly higher latency than V2.
- **Member 4:** in the UI and the docs, call V3 "verification (single-pass)", not "CoVe".
