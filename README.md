# Hallucination Stress Test

Does an LLM go along with a question built on a lie? This app measures it.

It feeds language models **trap questions** (false premises, fake papers, nonexistent people and technologies, impossible claims) and **legitimate control questions**, runs them through three prompt strategies on two models, has a third model judge every answer, and reports the **hallucination rate** before and after better prompting.

> Hackathon project for *Prompt Engineering for Generative AI* (Theme D: Reliability, Hallucination and Safety). The problem statement is in [`problem_17.md`](problem_17.md).

## Team

| Member | Responsibilities (Contribution) | Name | Folder |
| :--- | :--- | :--- | :--- |
| Member 1 | Prompt design, testing, refinement | Om Bhatt | [`om-bhatt/`](om-bhatt) |
| Member 2 | Prototype development/integration | Chan Evan | `app.py`, `hst/`, `tests/`, `data/`, `prompts/` |
| Member 3 | Research, problem analysis, testing | Hetansh Shah | [`hetansh-shah/`](hetansh-shah) |
| Member 4 | UI, workflow, documentation/demo | Hitarthi Pansuriya | [`hitarthi-pansuriya/`](hitarthi-pansuriya) |

## Quick start

You need [`uv`](https://docs.astral.sh/uv/) and a free [Groq API key](https://console.groq.com/keys). `uv` installs the right Python (3.12) by itself.

```bash
git clone https://github.com/Chanevan317/Hallucination-Stress-Test.git
cd Hallucination-Stress-Test

uv sync                        # first time only; downloads ~300 MB of packages, can be slow
uv run streamlit run app.py    # opens http://localhost:8501
```

Then, in the app:

1. **Settings**: paste your Groq API key and click **Test key & load models**. The three models below are preselected.
2. **Experiment**: click **Start / Resume Batch Experiment Run**. The full run is 180 model calls plus 180 judge calls and takes roughly 20 minutes on the free tier. Watch the progress bar and live log; the results dashboard fills in below.
3. When it finishes, click **Save these results as the offline demo fallback**.

To run the tests (no API key needed): `uv run pytest`

## The screens

| Screen | What it does |
|---|---|
| **Settings** | API key, model choice (A, B, judge), call pacing, JSON-mode and strictness toggles. |
| **Experiment** | Runs the 30-question batch, then shows the dashboard: hallucination, over-refusal, trap-detection, correction and invalid-output rates per model and prompt version (always as `numerator/denominator`), plus a per-category breakdown and a CSV export. |
| **Side-by-Side** | Pick any dataset question and see V1, V2 and V3 answers next to each other, with the judge's label, reason and the invented span highlighted in red. |
| **Live Test** | Type a new, unseen question. It runs through V1, V2 and V3 on the chosen model and is judged without ground truth. This is the "unseen input" demo. |
| **Prompt Editor** | Edit any prompt, then **Save & Re-run Question** to see before vs after for one question. Every edit is saved with a timestamp. |

The sidebar has **Use stored results (offline)**: if Groq fails during the demo, the dashboard and Side-by-Side screens read `results/cached_results.json` instead.

## How it works

```
dataset (20 traps + 10 controls)
        │  for each question × model (A, B) × prompt (V1, V2, V3)
        ▼
  tested model ──► strict JSON check ──► judge model (has ground truth) ──► label ──► metrics
   (temp 0)        INVALID_OUTPUT        HALLUCINATED / CORRECT_DEFENSE /
                   (no silent repair)    OVER_REFUSAL / CORRECT_ANSWER / INCORRECT_ANSWER
```

**Prompt versions** (one shared JSON output format, so only the technique changes):

| Version | Technique |
|---|---|
| **V1 Baseline** | Plain "answer helpfully" instruction. No hallucination protection; this is the "before". |
| **V2 Guardrail** | Factuality-first role + explicit constraints (never invent, say what can't be verified, still answer real questions) + few-shot examples. |
| **V3 Verification** | V2 + claim extraction and per-claim checking (SUPPORTED / CONTRADICTED / UNKNOWN) before answering. A single-pass approximation of Chain-of-Verification. |

**Model output:** `{"verdict": "ANSWERABLE | FALSE_PREMISE | UNVERIFIABLE | OUT_OF_SCOPE", "problematic_claims": [...], "answer": "..."}`

**Metrics** (full definitions in [`hetansh-shah/experiment_protocol.md`](hetansh-shah/experiment_protocol.md)):

- **Hallucination rate** (primary) = hallucinated trap answers / trap questions evaluated.
- **Over-refusal rate** = real questions wrongly refused / control questions. This stops "refuse everything" from looking good.
- **Trap detection**, **correction rate**, **invalid-output rate**, average latency.

## Guardrails

| Situation | What the app does |
|---|---|
| Model returns invalid or non-JSON output | Flags `INVALID_OUTPUT`, keeps the raw text, still judges it, counts it in the rates. Not repaired in batch runs (Live Test retries once). |
| Empty or over-500-character input (Live Test) | Blocked before any API call, with an inline error. |
| Off-topic question | The prompts return `OUT_OF_SCOPE`. In Live Test the app shows a guardrail alert and skips the judge. In batch runs the answer is still judged by content, so a dataset question answered with `OUT_OF_SCOPE` is never counted as a success by default. |
| Refusal | Judged by content: refusing a trap is a correct defense, refusing a real question is an over-refusal. |
| Groq rate limit (429) | Waits as instructed and retries, with a visible "Rate limited, retrying" message. |
| Daily limit reached | The run pauses cleanly. Finished calls are already saved, so **Start / Resume** continues without repeating them. |
| Judge fails to return valid output | Retried with a larger token budget, then flagged `JUDGE_ERROR`; on resume only the judge call is repeated. |
| Prompt edit without `{question}` | Rejected, not saved. |

## Models (free Groq tier)

| Role | Model | Why |
|---|---|---|
| Model A | `openai/gpt-oss-20b` | Small model from one family. |
| Model B | `qwen/qwen3.8-27b` | Different family; fewest tokens and fastest (~570 tokens, ~370 ms per call). |
| Judge | `openai/gpt-oss-120b` | A third, larger model so no model grades itself. On 18 sample records `qwen` as judge agreed with it 18/18. |

Measured on a few dozen calls, so treat the numbers as rough. The free tier showed **1000 requests/day and 8000 tokens/minute per model**; a full run (~270k tokens) is limited by tokens per minute, not by the daily cap. Models can be changed in Settings.

## Project layout

```
app.py              Streamlit entry point
hst/                App code: Groq client, runner, schema checks, metrics, storage, screens
prompts/            The prompts the app runs: v1.txt, v2.txt, v3.txt, judge.txt, judge_live.txt
data/               dataset.json (20 traps + 10 controls), unseen_set.json (8 held-out demo questions)
results/            results.jsonl (append-only run log), cached_results.json (offline fallback)
history/            Timestamped prompt edits (prompt_history.json) and live tests (live_history.jsonl)
tests/              29 tests: logic and headless rendering of every screen
om-bhatt/           Member 1: prompt versions, changelog, failure log
hetansh-shah/       Member 3: problem analysis, dataset, judge prompt, experiment protocol
hitarthi-pansuriya/ Member 4: workflow, UI spec, documentation, demo script
problem_17.md       The original problem statement
```

> **Status:** the prompts in `prompts/` are working placeholders written so the app runs end to end. Final prompts from `om-bhatt/` replace them by copying each into the file of the same name; no code change is needed. Every prompt has an id derived from its text, so results from different prompt texts are never mixed.

## Prompt history

Prompt changes are tracked two ways: **Git commits** (one commit per prompt change gives the timestamped history), and the app's **Prompt Editor**, which logs every live edit to `history/prompt_history.json`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `uv sync` is very slow | It is downloading `pyarrow`, `numpy` and `pandas` (~100 MB). Check your network and let it finish; later runs are instant. |
| "Enter your Groq API key in Settings first." | Paste the key in Settings. It is kept only in the browser session, so re-enter it after a restart. You can also set the `GROQ_API_KEY` environment variable before starting. |
| "Pick Model A, Model B and a judge model" | Click **Test key & load models** in Settings. |
| Many "Rate limited, retrying" messages | Normal on the free tier. Raise *Minimum seconds between API calls* in Settings if it persists. |
| "Daily limit reached, run paused" | Wait for the quota to reset, or switch on **Use stored results (offline)** and demo from saved results. |
| Run stopped halfway | Click **Start / Resume**; finished calls are not repeated. |
| Results look stale after changing a prompt | Expected: a changed prompt gets a new id, so the dashboard shows only results for the current prompt files. Re-run the experiment. |

## Security

The Groq API key is never written to disk, results, history or exports. Do not commit keys; `.env` is git-ignored.
