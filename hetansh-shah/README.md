# Hetansh Shah (Member 3): Research, Problem Analysis, Testing

| File | What it is |
|---|---|
| `problem_analysis.md` | The problem, users, requirements, hypothesis, definition of hallucination and research background |
| `dataset.json` | The measured test set: 20 traps and 10 controls, with ground truth and `requires_correction` |
| `unseen_set.json` | 8 held-out questions for the live demo (not part of the measured results) |
| `experiment_protocol.md` | The model output format, metric formulas, settings and the free-tier run budget |
| `judge_prompt.md` | What the judge labels mean and how special cases are counted |
| `verification_checklist.md` | Facts a person must check by hand |
| `results.md` | The measured results of the full run |
| `CHANGES.md` | What changed in this revision |

`dataset.json` and `unseen_set.json` are the same files the app loads from `data/`. If you change a question, change both copies and re-run the affected questions.

