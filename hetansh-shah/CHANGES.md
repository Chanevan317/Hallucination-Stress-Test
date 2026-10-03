# Changes in this revision

| # | Change | Why |
|---|---|---|
| 1 | `dataset.json` and `unseen_set.json` now have an explicit `requires_correction` field (true for 12 of 20 traps, and for U04) | The correction rate needs to know which traps require a stated correction. Before, the app guessed from keywords in `correct_behaviour`. |
| 2 | Metric definitions updated: trap detection and correction use two judge fields (`identifies_key_claim`, `states_correction`); items with an API or judge error are left out of the denominators and reported separately | The five labels alone cannot show whether a refusal named the specific false claim |
| 3 | Judge definitions rewritten (`judge_prompt.md`): special cases for `OUT_OF_SCOPE`, invalid JSON and `problematic_claims`; live judge added | The app now has two judges (with and without ground truth) |
| 4 | Experiment protocol updated to the built app: 180 model calls plus 180 judge calls, Groq free-tier budget, strict validation with no repair | Matches what was run |
| 5 | `results.md` added with the measured results of the full run | First real results |
| 6 | `verification_checklist.md` added | Lists every fact that still needs a person to check it |
| 7 | The long planning document `Research, problem analysis, testing.md` removed | It described a different design (Next.js, 120 evaluations) that was not built |
| 8 | `problem_analysis.md` rewritten for the built project | Same reason |

Not changed: the 30 questions and their ground truth, and the 8 held-out questions.
Not done: a human check of the judge's labels, and verification of the five facts marked NEEDS HUMAN VERIFICATION.
