# Demo script (about 5 minutes)

No slides. Demonstrate the running app. Open it before the judges arrive: `uv run streamlit run app.py`, paste the Groq key in **Settings**, click **Test key & load models**, and check that **Use stored results (offline)** is unticked (or ticked, if the network is bad).

Speakers: **Hitarthi** introduces and closes, **Hetansh** explains the data and metrics, **Om** explains the prompts, **Chan** drives the app and answers technical questions. Everyone must be able to explain every part.

## Timed flow

| Time | Who | Screen | What to say and do |
|---|---|---|---|
| 0:00 | Hitarthi | Experiment | "Language models can answer a question built on a lie as if it were true, for example describing a research paper that does not exist. We built a test bench that measures this and checks whether better prompts reduce it." |
| 0:30 | Hetansh | Side-by-Side, pick a trap | Show the question and the expected behaviour. "We wrote 20 trick questions in five categories, plus 10 normal questions. The normal ones catch a prompt that just refuses everything." |
| 1:00 | Om | Side-by-Side | Show V1, V2 and V3 for one trap. "V1 is the plain prompt. V2 adds a fact-checking role, rules and examples. V3 adds a silent claim-by-claim check. All three use the same JSON format, so only the technique changes." Point at the judge badge and the highlighted invented text, if there is any. |
| 2:00 | Hetansh | Experiment, dashboard | Show the version x model table. "Same questions, three prompts, two models, graded by a third model. This is the hallucination rate, with numerator and denominator." Compare V1 with V3. Say plainly what the numbers show, including anything that did not improve. |
| 3:00 | Chan | Live Test | Ask a judge to type any new trick question. Click **Run Live Stress Test**. "It has never seen this question. The three prompts run side by side; a live judge flags invented specifics." |
| 3:45 | Chan | Live Test | Type an off-topic request ("Write me a poem about my cat"). Show the guardrail alert (`OUT_OF_SCOPE`). Try an empty box to show the input error. |
| 4:15 | Om | Prompt Editor | Let a judge name a change (or use "delete Rule 3 from V3"). Click **Save & Re-run Question** on a fake-reference trap. Show Before vs After and the timestamped history. "Our edits never overwrite the default prompts." |
| 4:45 | Hitarthi | Experiment | Close: what worked, what did not, and the limits (small test set, one run, LLM judge). |

## Unseen input ideas

Use the held-out set (Live Test, **Insert an example from the held-out set**) or make up your own: a fake paper, a person who never won an award, an impossible date, a function that does not exist.

## Likely judge questions and short answers

**Hitarthi (UI, workflow, documentation)**
- *What happens if the model returns bad JSON?* The reply is flagged `INVALID_OUTPUT`, kept as raw text, still judged, and counted in the invalid-output rate. We never repair it silently. Live Test retries once.
- *How do you handle off-topic input?* The prompts return `OUT_OF_SCOPE`. In Live Test the app shows a guardrail alert and skips the judge.
- *What if the network fails during the demo?* Tick **Use stored results (offline)**; the dashboard and Side-by-Side read the saved run.
- *How do you handle the free-tier limits?* Calls are paced, a 429 waits and retries, and a daily limit pauses the run. Finished items are saved, so it resumes without repeating.

**Hetansh (data, metrics, research)**
- *Why 30 questions?* 20 traps in five categories (four each) and 10 normal questions. It is a small set, so we report numerators and denominators, not just percentages.
- *What is the hallucination rate?* Trap replies the judge labelled `HALLUCINATED`, divided by trap questions evaluated.
- *Why normal questions?* To measure over-refusal. A prompt that refuses everything would otherwise look perfect.
- *How reliable is the judge?* It is a language model and can be wrong. It uses the ground truth we wrote, is a different model from the two tested, and we have not measured its accuracy against people yet (see the verification checklist).
- *Is V3 Chain-of-Verification?* No. It is a single-pass approximation; real CoVe checks claims in a separate step.

**Om (prompts)**
- *Which techniques did you combine?* Role prompting, constraint rules, few-shot examples, structured JSON output, and (V3) step-by-step claim verification with a claims-first output order.
- *Why the same JSON in all versions?* So the only thing that changes is the technique.
- *Which line fixes which failure?* See `changelog.md` and `failures.md`. Lines added after a failure are marked as such; the rest are pre-emptive.
- *Why is the baseline fair?* It has no rule about premises or verification. It does explain the four verdict values, because the format must be the same.

**Chan (prototype)**
- *Which models and why?* Two Groq models from different families, and a third as judge. We measured tokens and latency for each before choosing.
- *What did testing find?* A judge token cap that was too low for a reasoning model, a judge that mistook flagged claims for invented ones, and wasted quota when the daily limit hit mid-item. All fixed and covered by tests.
- *Does it run on an unseen input?* Yes: Live Test, no dataset needed.

## If something breaks

| Problem | Fix |
|---|---|
| "Rate limited, retrying" | Wait; the app retries. Raise the seconds between calls in Settings if it repeats. |
| "Daily limit reached" | Tick **Use stored results (offline)** and continue with the stored run. |
| Wrong key / models | Settings: re-paste the key, **Test key & load models**. |
| App not loading | `uv run streamlit run app.py` again; the results on disk are safe. |
