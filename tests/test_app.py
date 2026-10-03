"""Headless smoke tests: every screen renders, with and without stored results."""

import pytest
from streamlit.testing.v1 import AppTest

from hst import config, prompts, runner, store
from test_core import ITEMS, ScriptedClient

NAV = ["Settings", "Experiment", "Side-by-Side", "Live Test", "Prompt Editor"]


def open_app(page):
    at = AppTest.from_file(str(config.ROOT / "app.py"), default_timeout=30)
    at.run()
    assert not at.exception
    at.sidebar.radio[0].set_value(page).run()
    return at


@pytest.fixture
def stored(tmp_path, monkeypatch):
    """Fake batch results for the real dataset, saved as the offline cache."""
    items = store.load_dataset()
    results = tmp_path / "r.jsonl"
    runner.run_batch(
        ScriptedClient(), items, ["modelA", "modelB"], prompts.load_all_templates(),
        prompts.load_judge_template(), "judge", results_path=results,
    )
    cache = tmp_path / "cache.json"
    store.save_cached(store.load_results(results), cache)
    monkeypatch.setattr(config, "CACHED_FILE", cache)
    monkeypatch.setattr(config, "RESULTS_FILE", tmp_path / "none.jsonl")
    monkeypatch.setattr(config, "PROMPT_HISTORY_FILE", tmp_path / "hist.json")
    monkeypatch.setattr(config, "LIVE_HISTORY_FILE", tmp_path / "live.jsonl")
    return cache


@pytest.mark.parametrize("page", NAV)
def test_every_screen_renders_empty(page, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CACHED_FILE", tmp_path / "missing.json")
    monkeypatch.setattr(config, "RESULTS_FILE", tmp_path / "none.jsonl")
    monkeypatch.setattr(config, "PROMPT_HISTORY_FILE", tmp_path / "hist.json")
    monkeypatch.setattr(config, "LIVE_HISTORY_FILE", tmp_path / "live.jsonl")
    at = open_app(page)
    assert not at.exception


def test_dashboard_and_compare_with_stored_results(stored):
    at = open_app("Experiment")
    assert not at.exception
    assert any("Hallucination rate" in m.label for m in at.metric)
    assert at.dataframe  # benchmark matrix
    at = open_app("Side-by-Side")
    assert not at.exception
    assert at.selectbox  # question picker rendered


def test_live_test_blocks_empty_and_oversized_input():
    at = open_app("Live Test")
    at.button[-1].click().run()
    assert any("cannot be empty" in e.value for e in at.error)
    at.text_area[0].set_value("x" * 501).run()
    at.button[-1].click().run()
    assert any("exceeds limit" in e.value for e in at.error)


def test_live_test_requires_key():
    at = open_app("Live Test")
    at.text_area[0].set_value("Who won the 2031 Nobel Prize in Computer Science?").run()
    at.button[-1].click().run()
    assert any("API key" in e.value for e in at.error)


def test_editor_rejects_template_without_placeholder(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "PROMPT_HISTORY_FILE", tmp_path / "hist.json")
    at = open_app("Prompt Editor")
    at.text_area[0].set_value("no placeholder here").run()
    at.button[-1].click().run()
    assert any("{question}" in e.value for e in at.error)
    assert not (tmp_path / "hist.json").exists()  # invalid edits are not saved
