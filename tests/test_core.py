import json

import pytest
import requests

from hst import config, guardrails, metrics, prompts, runner, schema, store
from hst.groq_client import ApiError, ChatResult, DailyLimitError, GroqClient, parse_wait_seconds

GOOD = json.dumps({"verdict": "FALSE_PREMISE", "problematic_claims": ["x"], "answer": "No."})


# -- prompts / schema / guardrails ---------------------------------------------
def test_fill_leaves_json_braces_and_does_not_reinject():
    out = prompts.fill('{"a": 1} {question} {other}', question="{question}")
    assert out == '{"a": 1} {question} {other}'


def test_all_shipped_templates_are_valid():
    for v in config.VERSIONS:
        assert prompts.validate_template(prompts.load_template(v)) is None
    assert "{model_response}" in prompts.load_judge_template()
    assert "{model_response}" in prompts.load_judge_template(live=True)


def test_template_without_placeholder_rejected():
    assert prompts.validate_template("no placeholder") is not None
    assert prompts.validate_template("   ") is not None


def test_prompt_id_changes_with_text():
    assert prompts.prompt_id("V1", "a") != prompts.prompt_id("V1", "b")
    assert prompts.prompt_id("V1", "a").startswith("V1@")


def test_model_output_validation():
    assert schema.parse_model_output(GOOD)[0]["verdict"] == "FALSE_PREMISE"
    assert schema.parse_model_output("```json\n" + GOOD + "\n```")[0] is None  # strict
    assert schema.parse_model_output("```json\n" + GOOD + "\n```", accept_fences=True)[0] is not None
    assert schema.parse_model_output("sure! " + GOOD)[0] is None
    assert schema.parse_model_output('{"verdict": "MAYBE", "problematic_claims": [], "answer": ""}')[0] is None
    assert schema.parse_model_output('{"verdict": "ANSWERABLE", "answer": ""}')[0] is None
    assert schema.parse_model_output('{"verdict": "ANSWERABLE", "problematic_claims": [1], "answer": ""}')[0] is None
    assert schema.parse_model_output("")[0] is None


def test_judge_output_validation():
    ok = '{"label": "HALLUCINATED", "reason": "r", "invented_claim_span": null, "identifies_key_claim": false, "states_correction": false}'
    parsed, err = schema.parse_judge_output("Here: " + ok)
    assert parsed["invented_claim_span"] == "" and err is None
    assert schema.parse_judge_output('{"label": "HALLUCINATED", "reason": "r"}')[0] is None  # booleans missing
    live = '{"label": "INVENTED_DETAILS", "reason": "r", "invented_claim_span": "x"}'
    assert schema.parse_judge_output(live, live=True)[0] is not None
    assert schema.parse_judge_output(live)[0] is None  # live label invalid in batch mode


def test_input_guardrails():
    assert guardrails.check_input("   ")[1] == "ERR_INPUT_EMPTY"
    assert guardrails.check_input("x" * 501)[1] == "ERR_INPUT_TOO_LONG"
    assert guardrails.check_input("x" * 500)[0] is True


def test_requires_correction_heuristic_and_override():
    assert store.requires_correction({"is_trap": True, "correct_behaviour": "Correct the premise."})
    assert not store.requires_correction({"is_trap": True, "correct_behaviour": "Say it cannot be verified."})
    assert not store.requires_correction({"is_trap": False, "correct_behaviour": "Correct answer."})
    assert store.requires_correction({"is_trap": True, "correct_behaviour": "x", "requires_correction": True})


def test_shipped_dataset_is_valid():
    items = store.load_dataset()
    assert sum(i["is_trap"] for i in items) == 20 and len(items) == 30
    assert len(store.load_unseen()) == 8


# -- groq client ------------------------------------------------------------------
class FakeResp:
    def __init__(self, status, body=None, headers=None):
        self.status_code, self._body, self.headers = status, body or {}, headers or {}
        self.text = json.dumps(self._body)

    def json(self):
        return self._body


def ok(text):
    return FakeResp(200, {"choices": [{"message": {"content": text}}]})


class FakeSession:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), 0

    def post(self, *a, **k):
        self.calls += 1
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def make_client(responses, **kw):
    sleeps = []
    c = GroqClient("k", session=FakeSession(responses), sleep=sleeps.append, min_interval=0, **kw)
    c.sleeps = sleeps
    return c


def test_parse_wait_seconds():
    assert parse_wait_seconds("Please try again in 7.5s.") == 7.5
    assert parse_wait_seconds("Please try again in 1m23.4s") == pytest.approx(83.4)
    assert parse_wait_seconds("try again in 250ms") == pytest.approx(0.25)
    assert parse_wait_seconds("nothing") is None


def test_client_retries_short_rate_limit():
    c = make_client([FakeResp(429, {"error": {"message": "try again in 2s"}}), ok("hi")])
    assert c.chat("m", "p").text == "hi"
    assert c.sleeps == [2.5]


def test_client_daily_limit_raises():
    c = make_client([FakeResp(429, {"error": {"message": "Rate limit reached ... tokens per day (TPD)"}})])
    with pytest.raises(DailyLimitError):
        c.chat("m", "p")
    c = make_client([FakeResp(429, {"error": {"message": "x"}}, {"retry-after": "3600"})])
    with pytest.raises(DailyLimitError):
        c.chat("m", "p")


def test_client_network_error_retries_then_fails():
    c = make_client([requests.ConnectionError("boom")] * 3)
    with pytest.raises(ApiError):
        c.chat("m", "p")
    assert c.session.calls == 3  # 1 try + 2 retries


def test_client_bad_key():
    c = make_client([FakeResp(401, {"error": {"message": "bad"}})])
    with pytest.raises(ApiError, match="Invalid API key"):
        c.chat("m", "p")


# -- runner / metrics ---------------------------------------------------------------
JUDGE_TRAP_OK = json.dumps(
    {"label": "CORRECT_DEFENSE", "reason": "ok", "invented_claim_span": "", "identifies_key_claim": True, "states_correction": True}
)
JUDGE_HALLU = json.dumps(
    {"label": "HALLUCINATED", "reason": "bad", "invented_claim_span": "No.", "identifies_key_claim": False, "states_correction": False}
)


class ScriptedClient:
    """Answers model calls with GOOD and judge calls by whether the prompt is a judge prompt."""

    def __init__(self, judge_reply=JUDGE_TRAP_OK, daily_limit_after=None, model_reply=GOOD):
        self.judge_reply, self.limit, self.model_reply, self.n = judge_reply, daily_limit_after, model_reply, 0

    def chat(self, model, prompt, **kw):
        self.n += 1
        if self.limit is not None and self.n > self.limit:
            raise DailyLimitError("tokens per day")
        text = self.judge_reply if "strict evaluator" in prompt else self.model_reply
        return ChatResult(text=text, latency_ms=10, model=model)


ITEMS = [
    {"id": "T1", "question": "Why X?", "category": "false_premise", "is_trap": True,
     "key_false_claim": "X", "correct_behaviour": "Correct the premise.", "reference_fact": "f"},
    {"id": "C1", "question": "What is 1+1?", "category": "science", "is_trap": False,
     "key_false_claim": "", "correct_behaviour": "Answer 2.", "reference_fact": "f"},
]


def templates():
    return prompts.load_all_templates()


def test_batch_runs_saves_and_resumes(tmp_path):
    path = tmp_path / "r.jsonl"
    client = ScriptedClient(daily_limit_after=7)  # 12 items x 2 calls; dies partway
    outcome = runner.run_batch(client, ITEMS, ["mA", "mB"], templates(), prompts.load_judge_template(), "judge", results_path=path)
    assert outcome == "daily_limit"
    saved = store.load_results(path)
    assert 0 < len(saved) < 12
    client2 = ScriptedClient()
    outcome = runner.run_batch(client2, ITEMS, ["mA", "mB"], templates(), prompts.load_judge_template(), "judge", results_path=path)
    assert outcome == "completed"
    assert len(store.load_results(path)) == 12
    # nothing paid for is repeated: 12 items x (model + judge) = 24 calls in total.
    # client.n counts the final call that hit the limit, which did not succeed.
    assert (client.n - 1) + client2.n == 24
    # the item cut off at its judge step kept its model output and was only re-judged
    assert any(r["flags"] == [] for r in store.load_results(path))
    again = ScriptedClient()
    runner.run_batch(again, ITEMS, ["mA", "mB"], templates(), prompts.load_judge_template(), "judge", results_path=path)
    assert again.n == 0


def test_invalid_output_is_flagged_not_repaired_and_still_judged(tmp_path):
    client = ScriptedClient(model_reply="I think it is Y.", judge_reply=JUDGE_HALLU)
    rec = runner.run_one(client, ITEMS[0], "mA", "V1", templates()["V1"], prompts.load_judge_template(), "judge")
    assert config.FLAG_INVALID in rec["flags"] and rec["parsed"] is None
    assert rec["judge"]["label"] == "HALLUCINATED"
    assert client.n == 2  # one model call, one judge call, no repair attempt


def test_judge_failure_flagged_then_rejudged_without_new_model_call():
    client = ScriptedClient(judge_reply="not json")
    rec = runner.run_one(client, ITEMS[0], "mA", "V1", templates()["V1"], prompts.load_judge_template(), "judge")
    assert rec["flags"] == [config.FLAG_JUDGE_ERROR] and rec["judge"] is None
    assert client.n == 3  # model + judge + judge retry
    client2 = ScriptedClient()
    rec2 = runner.run_one(client2, ITEMS[0], "mA", "V1", templates()["V1"], prompts.load_judge_template(), "judge", existing=rec)
    assert rec2["flags"] == [] and rec2["judge"]["label"] == "CORRECT_DEFENSE"
    assert client2.n == 1  # only the judge was re-run


def test_live_run_skips_judge_for_out_of_scope(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "append_live", lambda r, path=None: None)
    oos = json.dumps({"verdict": "OUT_OF_SCOPE", "problematic_claims": [], "answer": "no"})
    client = ScriptedClient(model_reply=oos)
    recs, daily = runner.run_live(client, "write a poem", "mA", templates(), prompts.load_judge_template(live=True), "judge")
    assert len(recs) == 3 and not daily
    assert all(r["judge"] is None for r in recs) and client.n == 3


def test_live_run_retries_invalid_json_once(monkeypatch):
    monkeypatch.setattr(store, "append_live", lambda r, path=None: None)
    client = ScriptedClient(model_reply="nope", judge_reply=JUDGE_HALLU)
    recs, _ = runner.run_live(client, "q", "mA", templates(), prompts.load_judge_template(live=True), "judge")
    assert all(config.FLAG_INVALID in r["flags"] for r in recs)
    # per version: 2 model attempts + 2 judge attempts (the scripted judge answers with batch labels,
    # which are invalid in live mode, so the judge step is flagged)
    assert client.n == 12
    assert all(config.FLAG_JUDGE_ERROR in r["flags"] for r in recs)


def test_metrics_numerators_and_denominators():
    def rec(qid, trap, label, ident=False, corr=False, flags=()):
        return {"question_id": qid, "model": "m", "prompt_version": "V1", "category": "c", "is_trap": trap,
                "flags": list(flags), "latency_ms": 100,
                "judge": {"label": label, "identifies_key_claim": ident, "states_correction": corr}}
    ds = {"T1": ITEMS[0], "T2": dict(ITEMS[0], id="T2"), "T3": dict(ITEMS[0], id="T3"), "C1": ITEMS[1]}
    records = [
        rec("T1", True, "HALLUCINATED"),
        rec("T2", True, "CORRECT_DEFENSE", True, True),
        rec("T3", True, "CORRECT_DEFENSE", False, False, flags=[config.FLAG_INVALID]),
        rec("C1", False, "OVER_REFUSAL"),
        {"question_id": "T9", "model": "m", "prompt_version": "V1", "category": "c", "is_trap": True,
         "flags": [config.FLAG_API_ERROR], "judge": None},
    ]
    m = metrics.compute(records, ds)
    assert (m["hallucinated"], m["traps"]) == (1, 3)  # API error excluded from the denominator
    assert (m["detected"], m["corrected"], m["correction_required"]) == (1, 1, 3)
    assert (m["over_refusals"], m["controls"]) == (1, 1)
    assert (m["invalid"], m["model_calls"]) == (1, 4)
    assert m["api_errors"] == 1
    assert metrics.pct(1, 3) == "33.3%" and metrics.pct(0, 0) == "--"
    grouped = metrics.group(records, ds)
    assert metrics.rows(grouped)[0]["Hallucination"] == "1/3 (33.3%)"
