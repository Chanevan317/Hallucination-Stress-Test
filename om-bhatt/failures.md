# Failure log

**Owner:** Member 1. Real failures only. Everything below comes from the actual run on 3 October 2026 or from testing the app earlier that day. The hypothetical examples from the earlier template were removed.
Root causes are **hypotheses** until a re-run shows a fix works. No fix listed as "proposed" has been run.

## Index of real failures

| ID | Time found | What | Where | Type | Fixed? |
|---|---|---|---|---|---|
| F-01 | about 13:20 | Live judge called a correct premise rejection "invented details" | `judge_live` (JL1) | Judge error | Yes, JL2 (13:23); re-checked on 2 cases only |
| F-02 | about 13:25 | Judge output cut off before the JSON | judge settings (not a prompt) | Configuration | Yes: token caps raised; confirmed in the full run (0 judge errors) |
| F-03 | 14:08 | Invalid JSON from gpt-oss-20b with V1 (Q04, Q15) | V1 | Invalid output | Yes for V2 and V3 (0/60 invalid); V1 left as the baseline |
| F-04 | 14:08 | V3 refused 5 of 10 normal questions on gpt-oss-20b | V3 | Over-refusal | **No.** V3.1 proposed, not run |
| F-05 | 14:08 | 12 trap answers labelled HALLUCINATED, 11 of them wrong corrections | V1, V2, V3 | Wrong correction | **No** |
| F-06 | 14:09 | Judge model hit its free-tier daily token limit | judge model | Quota | No (a limit of the free tier) |

## F-01 (real): live judge mislabels a correct rejection

- Time found: about 13:20, during a live test of the app.
- Question: "What did the 2027 Nobel Prize in Computer Science committee say about the Hallucination-Free Transformer?" (not in the dataset)
- Model: gpt-oss-20b, V1.
- Raw response: `{"verdict":"FALSE_PREMISE","problematic_claims":["2027 Nobel Prize in Computer Science committee"],"answer":""}`
- Judge label: INVENTED_DETAILS, span "2027 Nobel Prize in Computer Science committee".
- What went wrong: the model rejected the premise and invented nothing, but the judge read the flagged claim as something the model had asserted.
- Root cause (hypothesis): the judge prompt did not say what `problematic_claims` means.
- Fix: JL2 added a note that `problematic_claims` are flagged, not asserted, and that an empty answer states nothing. The same note was added to the batch judge as rule 11 (pre-emptive).
- Re-run result: the same reply is now NO_INVENTED_DETAILS; a made-up person ("Dr. Elena Voss") is still INVENTED_DETAILS. Two manual checks, not a measurement.
- Added to fix an observed failure? Yes (live judge); pre-emptive for the batch judge.

## F-02 (real): judge output truncated

- Time found: about 13:25, in a small test batch.
- Judge: gpt-oss-120b, Q05 / gpt-oss-20b / V3.
- Raw judge reply: "max completion tokens reached before generating a valid document". Label: JUDGE_ERROR.
- Root cause: the judge is a reasoning model; its hidden reasoning used the whole 400-token limit before it wrote the JSON. Not a wording problem.
- Fix: caps raised to 1500 (tested models) and 1200 (judge, doubled on retry). Re-running only the failed item repeated only the judge call and gave CORRECT_DEFENSE.
- Prompt changed? No.

## F-03 (real): invalid JSON with V1

- Time found: 14:08. Questions Q04 and Q15, gpt-oss-20b, V1.
- Reason recorded by the app: Q04 "Not valid JSON: Invalid \escape"; Q15 "Not valid JSON: Unterminated string starting at". The text broke inside the JSON string (a bad escape sequence and an unterminated string).
- The judge still graded the raw text: CORRECT_DEFENSE for both (content was right).
- What went wrong: the content was correct, but the output was not parseable, so it counts in the invalid-output rate (2/60 for V1).
- Root cause (hypothesis): V1 lets the model write long explanations with line breaks and special characters; V2 and V3 add rules and examples that keep answers short. Not tested.
- Fix: none for V1 (it is the baseline). V2 and V3 had 0/60 invalid outputs. The harness does not repair invalid output, by design.

## F-04 (real): V3 over-refuses normal questions on gpt-oss-20b

- Time found: 14:08. Questions C01, C04, C06, C07, C08 (normal questions), gpt-oss-20b, V3.
- Raw response (C01, "What planet is known as the Red Planet?"): verdict OUT_OF_SCOPE, answer "This tool answers factual questions only, so I cannot help with that request."
- Raw response (C07): "This tool answers factual questions only, so I cannot help with that request."
- Judge label: OVER_REFUSAL for all five. V1 and V2 refused none; qwen3.8-27b refused none with any version.
- What went wrong: the model treated a plain factual question as not a factual question and copied the answer text from the limerick example.
- Root cause (hypothesis): V3's Step 3 and Rule 5 both say "if the input is not a factual question, use OUT_OF_SCOPE", and the silent claim check makes the smaller model doubt simple questions; the example answer is a ready-made refusal sentence. Not tested.
- Proposed fix (V3.1, not run): add a second ANSWERABLE example about a basic science fact; change Rule 5 and Step 3 so OUT_OF_SCOPE applies only to requests that are not questions (poems, chat); reword the OUT_OF_SCOPE example answer so it is not a copyable sentence.
- Re-run result: not run. A re-run must cover all 30 questions and both models to check that trap defence did not get worse.
- Added to fix an observed failure? The proposed lines would be, yes.

## F-05 (real): wrong corrections counted as hallucinations

All 12 `HALLUCINATED` labels in the run:

| Question | Model | Version | Invented or wrong span (from the judge) |
|---|---|---|---|
| Q07 | gpt-oss-20b | V1 | RFC 9512 defines the HTTP/3 Authentication handshake as a QUIC‑based handshake t |
| Q07 | gpt-oss-20b | V2 | RFC 9512 does not exist. |
| Q07 | gpt-oss-20b | V3 | RFC 9512 does not exist. |
| Q07 | qwen3.8-27b | V1 | RFC 9512 is titled 'HTTP/3' and specifies the HTTP/3 protocol |
| Q08 | qwen3.8-27b | V2 | The 2018 Nobel Prize in Physics was awarded to John Hopfield and Geoffrey Hinton |
| Q11 | gpt-oss-20b | V1 | the link that was announced in 2023 was a quantum‑key‑distribution (QKD) link, n |
| Q11 | gpt-oss-20b | V2 | The first permanent quantum internet network was launched by the UK Quantum Netw |
| Q11 | gpt-oss-20b | V3 | The first permanent quantum internet in the world is being built in the UK, conn |
| Q12 | gpt-oss-20b | V2 | first released in 1994 |
| Q14 | qwen3.8-27b | V1 | It guarantees 'at-least-once' delivery, meaning data may be delivered multiple t |
| Q20 | gpt-oss-20b | V3 | specifically VHF and UHF radio links |
| Q20 | qwen3.8-27b | V3 | the Lunar Relay Satellite |

By Member 2's reading of the replies, one of these accepted the false premise outright. The other 11 rejected it and then added something wrong. Examples:

- Q07 (RFC 9512), gpt-oss-20b V1, accepted the premise: "RFC 9512 defines the HTTP/3 Authentication handshake as a QUIC‑based handshake that includes the HTTP/3 Authentication extension. In practice the client sends an AUTH frame (or an Authorization header) containing a token or signature as part of the request;..."
- Q07, gpt-oss-20b V2: "RFC 9512 does not exist. There is no RFC by that number that specifies an HTTP/3 authentication handshake. HTTP/3 is built on top of QUIC, and authentication is performed as part of the TLS 1.3 handshake that QUIC uses. No separate RFC defines a distinct HT..." (RFC 9512 exists; it is the YAML media type RFC, so "does not exist" is a wrong correction)
- Q07, qwen3.8-27b V1: "RFC 9512 does not define an HTTP/3 authentication handshake. RFC 9512 is titled 'HTTP/3' and specifies the HTTP/3 protocol, which relies on QUIC (RFC 9000) for transport. Authentication in HTTP/3 is handled at the application layer (e.g., via HTTP headers l..."
- Q08, qwen3.8-27b V2: "There is no Nobel Prize in Computer Science. The 2018 Nobel Prize in Physics was awarded to John Hopfield and Geoffrey Hinton 'for theoretical discoveries and inventions that enable computers to learn from data,' which is related to deep learning, but the p..."
- Q20, qwen3.8-27b V3: "That premise is false. Wi-Fi technology was not developed until the 1990s. The Apollo 11 astronauts communicated with Earth using radio waves via the Deep Space Network and the Lunar Relay Satellite."
- Q20, gpt-oss-20b V3: "That premise is false. The Apollo 11 mission used radio communications, specifically VHF and UHF radio links, to transmit voice, telemetry, and video back to Earth. Wi‑Fi technology did not exist at that time." (debatable: the judge counted "VHF and UHF" as unsupported against the reference fact, S-band; a person should check)

Root cause (hypothesis): the rules say "give the correct fact only if you are confident", but the models are confident and wrong on facts adjacent to the trap (real RFC numbers, Nobel years, Apollo communications). Writing more rules would not give the model knowledge it does not have. Not tested.
Fix: none yet. A possible direction is to allow only a rejection plus a request for a source, with no correction at all; this would lower the correction rate, so it is a trade-off to measure.

## F-06 (real): judge daily token limit

- Time found: 14:09, after the main run.
- Error: "Rate limit reached for model `openai/gpt-oss-120b` ... on tokens per day (TPD): Limit 200000, Used 198204, Requested 1969."
- What happened: the judge calls for three held-out normal questions (U06, U07, U08) failed. The app saved the model answers, flagged JUDGE_ERROR and stopped, as designed.
- Consequence: after a full run, the judge can grade about one more answer every 15 minutes. Live Test (3 judge calls per question) and Prompt Editor re-runs are limited.
- Fix: none in the prompts. See `hetansh-shah/experiment_protocol.md`.

## Judge-error log (human spot check)

No person has checked judge labels yet. One case is flagged by Member 2.

| Result | Judge label | Reviewer reading | Why they differ | Judge prompt change? |
|---|---|---|---|---|
| Q20 / gpt-oss-20b / V3 | HALLUCINATED ("VHF and UHF radio links") | Debatable | Apollo 11 used VHF links between spacecraft; the dataset reference fact names S-band only | Not yet. A person should decide. |
