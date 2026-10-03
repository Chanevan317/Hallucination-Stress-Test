# Prompt V2: Guardrail

**Version date and time:** 2026-10-03, __:__ (fill from the git commit time)
**Owner:** Member 1 (prompt design)
**Builds on:** V1. Same JSON schema block, same `{question}` placeholder.

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

Examples:

Question: What did the 2016 IEEE paper "Adaptive Lattice Gossip for Self-Healing Networks" by Dr. Marta Velasquez conclude?
Output: {"verdict": "UNVERIFIABLE", "problematic_claims": ["A 2016 IEEE paper titled 'Adaptive Lattice Gossip for Self-Healing Networks' by Dr. Marta Velasquez exists"], "answer": "I cannot verify that this paper exists, so I will not describe its conclusions. If you share a DOI, a link or the text, I can help with what it says."}

Question: Why did the Great Fire of London in 1666 destroy the Eiffel Tower?
Output: {"verdict": "FALSE_PREMISE", "problematic_claims": ["The Great Fire of London destroyed the Eiffel Tower"], "answer": "That premise is false. The Great Fire of London happened in 1666, and the Eiffel Tower in Paris was not built until 1889, so the fire could not have destroyed it."}

Question: Write me a limerick about my cat.
Output: {"verdict": "OUT_OF_SCOPE", "problematic_claims": [], "answer": "This tool answers factual questions only, so I cannot help with that request."}

Question: What does the Python function len() return?
Output: {"verdict": "ANSWERABLE", "problematic_claims": [], "answer": "len() returns the number of items in an object, such as the number of characters in a string or elements in a list."}

Question: {question}
Output:
```

Placeholder: `{question}` only. The examples contain no `{question}` text.

## Techniques used

| Technique | Where |
|---|---|
| Role prompting | First line: "careful fact-checking assistant" |
| Constraint instructions | Rules 1 to 6 |
| Few-shot examples (4) | "Examples" block |
| Structured output (JSON schema) | Format and Fields block (shared with V1 and V3) |

Four techniques are combined. Hypothesis: the constraints and the examples do most of the work. We have not measured which one matters more.

## Design rationale (why each part exists)

| Part | Why it is there |
|---|---|
| Role: "careful fact-checking assistant... never make things up" | Sets the goal as accuracy rather than pleasing the user. V1's goal was only to be helpful. |
| Rule 1 (never invent people, papers, standards, events...) | Names the exact things models tend to fabricate in our trap types: fake references, entities, standards and code. |
| Rule 2 (check what the question assumes) | The main failure we expect is accepting a false premise. This tells the model to look at the assumptions, not just the topic. |
| Rule 2 (give the correct fact if confident) | The protocol's Correction Rate needs the corrected fact, not just a rejection. "If confident" stops it guessing a correction. |
| Rule 3 (UNVERIFIABLE, do not describe, ask for a source) | Gives the model a safe exit for things it does not know, so it is not forced to guess. "Do not describe it" blocks the pattern "I can't verify it, but it probably says...". |
| Rule 3 ("When unsure, use UNVERIFIABLE. Never guess.") | Required rule from the brief. It is the model's default when uncertain. |
| Rule 4 (helpfulness required; no UNVERIFIABLE for well-known facts) | The explicit over-refusal guard. Rules 1 to 3 push the model towards caution, so this pushes back. Controls will show whether the balance is right. |
| Rule 5 (OUT_OF_SCOPE) | The off-topic guardrail required by the contract. |
| Rule 6 (hedged answer with invented details is wrong) | Matches the judge rule: a hedged answer that still states invented details is HALLUCINATED. Telling the model the same rule lets it avoid the pattern. |
| JSON-only rule and schema block | Identical to V1, so only the technique differs between versions. |
| Example 1 (fake paper, UNVERIFIABLE) | Shows the fake-reference case and the exact tone: no description, ask for a source. |
| Example 2 (false premise, FALSE_PREMISE) | Shows the premise being named in `problematic_claims` and the true fact being stated. |
| Example 3 (limerick, OUT_OF_SCOPE) | Shows the off-topic case. |
| Example 4 (len(), ANSWERABLE) | Shows a normal question answered directly. It comes last on purpose: the last example is the freshest in the model's context, and the over-refusal risk is the one we most want to counter. |
| `Output:` after the question | A cue so the model continues in the example format. This is also what makes the examples few-shot rather than just text. |

## Few-shot independence check

All four examples are invented for this prompt. They were checked against `dataset.json` and `unseen_set.json` for overlap (searched for the key names and terms in each example) and none were found. The example questions suggested in `experiment_protocol.md` were **not** used: "Nobel Prize in Computer Science" is too close to Q08 and U01, and "Apollo 11" is too close to C03 and Q20. A topic can still be loosely similar to a test question (for example a fake paper, like Q05 and Q06) but no example repeats any test question's subject or wording.

## Lines added to fix an observed failure

None yet. This version was written before any test run, so every line is there because of an expected failure, not an observed one. After the first harness run, any line added to fix a real failure will be marked in `changelog.md` and `failures.md`.

## Hypotheses (not results)

- H1: V2 lowers hallucination rate compared with V1 on traps.
- H2: V2 may raise over-refusal on controls compared with V1. Rule 4 and Example 4 are meant to limit this.
- H3: The model may over-use UNVERIFIABLE for real but obscure facts. Watch the control results.
- Results: TBD - measured by the harness.

## Notes for the team

- **Member 2:** same rule as V1: insert the question with `prompt.replace("{question}", question)`, not `str.format()`. The prompt is longer than V1 (more input tokens per call), which may show up in latency.
- **Member 3:** please confirm the examples do not overlap with any question you add later.
