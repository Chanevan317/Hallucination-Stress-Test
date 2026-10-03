# UI specification (as built)

The app is a Streamlit web app (`app.py`). Run it with `uv run streamlit run app.py`. Every element listed here exists in the finished app.

## 1. Layout

A **left sidebar** is on every screen:

| Element | Behaviour |
|---|---|
| Title "Hallucination Stress Test" | Fixed |
| Screen selector (radio) | Settings, Experiment, Side-by-Side, Live Test, Prompt Editor |
| Checkbox **Use stored results (offline)** | Dashboard and Side-by-Side read `results/cached_results.json` instead of the live run. On at start-up only if there is no live result but a stored file exists. |
| Caption `Models: <A> \| <B>` and `Judge: <judge>` | Show "—" until chosen |
| Caption `Dataset: 20 trap / 10 control loaded` | Counts come from `data/dataset.json` |

When offline mode is on, a blue banner at the top says: "Using stored results (offline mode). No API calls are being made for result views."

## 2. Colour and badge convention

Every result card shows coloured badges. Colours are fixed:

| Badge | Background | Text | Meaning |
|---|---|---|---|
| `HALLUCINATED` | #FEE2E2 | #991B1B | Accepted a false premise or invented details on a trap |
| `CORRECT_DEFENSE` | #DCFCE7 | #166534 | Rejected or did not accept the trap, invented nothing |
| `OVER_REFUSAL` | #FFEDD5 | #9A3412 | Refused a normal question |
| `CORRECT_ANSWER` | #E0E7FF | #3730A3 | Answered a normal question correctly |
| `INCORRECT_ANSWER` | #F3E8FF | #6B21A8 | Gave a wrong answer to a normal question |
| `INVENTED_DETAILS` (live) | #FEE2E2 | #991B1B | Live judge: states made-up specifics |
| `NO_INVENTED_DETAILS` (live) | #DCFCE7 | #166534 | Live judge: no unsupported specifics |
| `NEEDS_REVIEW` (live) | #FEF3C7 | #92400E | Live judge cannot tell |
| `OUT_OF_SCOPE` | #FEF3C7 | #92400E | Off-topic verdict |
| `INVALID_OUTPUT`, `API_ERROR`, `JUDGE_ERROR` | #F3F4F6 | #1F2937 | App flags, not judge labels |
| Verdict badges (`ANSWERABLE`, `FALSE_PREMISE`, `UNVERIFIABLE`) | #EFF6FF | #1E3A8A | The model's own verdict |

## 3. Screens

### 3.1 Settings

Purpose: connect to Groq and choose the models.

| Element | Exact label | Behaviour |
|---|---|---|
| Key field | **Groq API key** (masked) | Held for the browser session only. Pre-filled if the `GROQ_API_KEY` environment variable is set. |
| Button | **Test key & load models** | Success: "Key works. N chat models available." and the three defaults are pre-selected if available. Error: the Groq error message. Blank key: "Enter your Groq API key first." |
| Selectors | **Model A**, **Model B**, **Judge model** | Drop-downs of chat models after the key is tested; plain text boxes before. |
| Validation | | Error "Model A and Model B must be different models." Warning if the judge equals a tested model (self-grading bias). |
| Slider | **Minimum seconds between API calls** | 0 to 10, step 0.5, default 2.5 |
| Checkbox | **Use Groq JSON mode for the tested models** | Off by default so the Invalid Output Rate reflects the prompt itself |
| Checkbox | **Accept ```json fences as valid output** | Off by default (strict) |
| Caption | "Temperature: 0.0 (fixed). Timeout: 30 s per call." | |

### 3.2 Experiment (batch run and results dashboard on one page)

**Run panel**

| Element | Exact label | Behaviour |
|---|---|---|
| Caption | "Dataset: 20 trap / 10 control questions loaded." | |
| Checkbox | **Include control questions** | Default on |
| Metrics | **Calls finished** (`n / 180`), **Remaining**, **Estimated time left** | Recomputed from the saved results |
| Button | **Start / Resume Batch Experiment Run** | Disabled when everything is finished. Checks Settings first. |
| Button | **Stop Run** | Stops at the current item; progress is saved |
| Status line | | Shows "Rate limited, retrying in N s (attempt K)." while waiting |
| Progress bar | "Progress: n / 180 calls" | |
| Log | Last 12 lines, e.g. `Q04 · qwen/qwen3.8-27b · V2 → CORRECT_DEFENSE` | |
| Preview line | "Live hallucination rate (all models/versions): h/t (p%)" | Updates after each item |
| End states | Success "Run completed in N s. Results are below." / error "Daily limit reached, run paused. ..." | |

**Results dashboard** (below the run panel)

| Element | Exact label | Behaviour |
|---|---|---|
| Selector | **Prompt version shown in the summary cards** | V1, V2, V3 (default V3) |
| Four metric cards per model | **Hallucination rate**, **Over-refusal rate**, **Trap detection rate**, **Invalid output rate** | Each shows `numerator/denominator (percent)`. The hallucination card shows the change against V1 in percentage points (a drop is green). |
| Table | **Prompt version × model matrix** | One row per model and version: Hallucination, Over-refusal, Trap detection, Correction, Invalid output, Avg latency (ms), Errors (API/judge) |
| Table | **Category performance** with **Filter category** | Same columns per category |
| Button | **Export CSV summary** | Downloads the matrix |
| Button | **Save these results as the offline demo fallback** | Writes `results/cached_results.json` (hidden in offline mode) |
| Warning | "N results had an API or judge error and are excluded from the rates above. Resume the run to retry them." | Only if there are such results |
| Empty state | "No experiment run found. Start a batch run above, or load stored results from the sidebar." | |

All numbers are computed from the saved results. Nothing is hard-coded.

### 3.3 Side-by-Side

| Element | Behaviour |
|---|---|
| **Select question** | Every dataset question that has results, shown as `Q01 [TRAP] Why does...` or `[CONTROL]` |
| **Target model** (radio) | Switches between Model A and Model B results |
| Question block | Full question, category, TRAP/CONTROL, the key false claim, and the expected behaviour |
| Three cards | **V1 Baseline**, **V2 Guardrail**, **V3 Verification** (see 3.6) |
| Empty state | "No result data available. Run the batch experiment or use stored results." |

### 3.4 Live Test

| Element | Exact label | Behaviour |
|---|---|---|
| Text area | **Enter a question** (placeholder "Type an unseen trap question here...") | |
| Counter | `n / 500 characters` | Turns red above 500 |
| Expander | **Insert an example from the held-out set** | Buttons that fill the text area with one of the 8 held-out questions |
| Selector | **Model** | Model A or Model B |
| Button | **Run Live Stress Test** | Disabled in offline mode |
| Loading | Spinner "Querying <model> via V1 / V2 / V3..." | |
| Result | Three cards side by side (see 3.6), with live judge labels | |
| Expander | **Timestamped prompt history (live tests this app has run)** | Table of the last 50 live tests: timestamp, question, model, prompt id, verdict, judge label |
| Errors | Empty or too-long input, missing key or models, rate limit, daily limit (messages in section 4) | |

### 3.5 Prompt Editor

| Element | Exact label | Behaviour |
|---|---|---|
| Selector | **Editing target** | V1 Baseline, V2 Guardrail, V3 Verification |
| Text area | **Prompt template (use {question} where the question goes)** | The whole prompt, loaded from the default file or the last saved edit |
| Banner | "You have changes from the default V3 prompt. The default file is not modified." | Shown when the text differs from the default |
| Button | **Reset to Default** | Restores the default text and logs a reset |
| Selectors | **Test question**, **Model** | Any dataset question; Model A or B |
| Button | **Save & Re-run Question** | Needs `{question}`, a key and models. Saves the edit, runs the question once, grades it with the normal judge. |
| Result | Two cards: "Before: default V3" and "After: V3.1" | Before is the default prompt's stored result for that question and model, if there is one |
| Message | "Prompt revision saved to history log at <timestamp>. (saved as V3.1)" | |
| Expander | **Timestamped prompt history** | Table of every edit and reset: id, timestamp, version, label, action, question |

### 3.6 Result card (used in Side-by-Side, Live Test, Prompt Editor)

From top to bottom: title (for example "V3 Verification"); badges (judge label, flags, model verdict); **Problematic claims** (what the model flagged); **Answer**, with the judge's invented span highlighted in red; "Judge: <reason>"; an expander **Raw model output**; "Latency N ms · <timestamp>".

Error states on a card: `API_ERROR` shows the red API message. `INVALID_OUTPUT` shows the warning and the raw text. `JUDGE_ERROR` shows a warning and an expander **Raw judge output**. A live `OUT_OF_SCOPE` verdict shows the guardrail alert.

## 4. Exact messages

| ID | Text | Where |
|---|---|---|
| `ERR_INPUT_EMPTY` | Input cannot be empty. Please enter a valid question. | Live Test |
| `ERR_INPUT_TOO_LONG` | Input length exceeds limit (500 characters max). Current length: N. | Live Test |
| `ERR_INVALID_JSON` | Model output was not valid JSON. Raw text retained for inspection. | Result card |
| `ERR_OFF_TOPIC` | GUARDRAIL ALERT: Query flagged as OUT_OF_SCOPE. Unhandled domain query rejected safely. | Live Test card |
| `ERR_API` | API error: <detail> | Result card |
| `ERR_RATE_LIMIT` | Rate limited, retrying in N s (attempt K). | Status line |
| `ERR_DAILY_LIMIT` | Daily limit reached, run paused. Finished calls are saved; resume later or use stored results. | Experiment, Live Test, Prompt Editor |
| `ERR_JUDGE_FAILURE` | Judge model failed to evaluate this output. Raw output shown unverified. | Result card |
| `ERR_NO_KEY` | Enter your Groq API key in Settings first. | Any screen that calls the API |
| `ERR_MODELS` | Pick Model A, Model B and a judge model in Settings first. | Any screen that calls the API |
| `ERR_SAME_MODEL` | Model A and Model B must be different models. | Settings, run buttons |
| `INFO_STORED` | Using stored results (offline mode). No API calls are being made for result views. | Banner |
| `INFO_PROMPT_SAVED` | Prompt revision saved to history log at <timestamp>. | Prompt Editor |
