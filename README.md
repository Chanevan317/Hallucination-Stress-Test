# Om Bhatt (Member 1): Prompt Design, Testing, Refinement

These are the prompts the app runs, with their design rationale and history.

| File | What it is |
|---|---|
| `prompt_v1.md` | V1 Baseline: the "before" |
| `prompt_v2.md` | V2 Guardrail: role, rules and few-shot examples |
| `prompt_v3.md` | V3 Verification: V2 plus a silent claim-checking procedure |
| `judge_prompt.md` | The batch judge (has ground truth) |
| `judge_live_prompt.md` | The live judge (Live Test, no ground truth) |
| `changelog.md` | Timestamped prompt history: what changed, why, and the measured result |
| `failures.md` | Failures found in the real run, root cause and what was done |
| `live_edit_guide.md` | How to change a prompt live in the demo, and a 30-second explanation of each prompt |

The prompt text in these files is identical to `prompts/v1.txt`, `v2.txt`, `v3.txt`, `judge.txt` and `judge_live.txt` in the repository. If you change a prompt, change both and commit.

Remove the old files in this folder before pushing; these files replace them. Never overwrite an old version silently: add a row to `changelog.md` for every change.
