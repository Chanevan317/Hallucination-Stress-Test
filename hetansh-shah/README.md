# Hetansh Shah (Member 3): Research, Problem Analysis, Testing

Put your files in this folder. Commit often.

## What goes here
- `problem_analysis.md`: the problem, target users, requirements, and how we define "hallucination".
- `trap_questions.csv`: the labelled test set (20+ questions). Suggested columns: `id, question, trap_type, why_its_a_trap, correct_behaviour`.
  - Trap types: false premise, fake reference, nonexistent fact.
  - Include some real (non-trap) questions as controls to catch over-refusal.
- `unseen_inputs.md`: extra questions kept aside for the live demo.
- `results.md`: hallucination rate per prompt version and per model.

## Rules
- Every question needs a clear, verifiable correct behaviour.
- Do not share the `unseen_inputs.md` questions with the prompt writer.
