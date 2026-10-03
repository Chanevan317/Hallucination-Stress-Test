"""Prompt templates: loading, filling, validation and ids.

Templates use single-pass {placeholder} substitution (not str.format) so the
JSON braces inside prompts are left alone and model text can never inject a
placeholder.
"""

import hashlib
import re

from hst import config

_PLACEHOLDER = re.compile(r"\{(\w+)\}")


def load_template(version: str) -> str:
    return (config.PROMPTS_DIR / config.PROMPT_FILES[version]).read_text(encoding="utf-8")


def load_judge_template(live: bool = False) -> str:
    name = config.JUDGE_LIVE_FILE if live else config.JUDGE_FILE
    return (config.PROMPTS_DIR / name).read_text(encoding="utf-8")


def load_all_templates() -> dict[str, str]:
    return {v: load_template(v) for v in config.VERSIONS}


def fill(template: str, **values: str) -> str:
    return _PLACEHOLDER.sub(lambda m: str(values.get(m.group(1), m.group(0))), template)


def validate_template(text: str) -> str | None:
    """Return an error message, or None if the template is usable."""
    if not text.strip():
        return "Prompt template is empty."
    if "{question}" not in text:
        return "Prompt template must contain the {question} placeholder."
    return None


def prompt_id(version: str, text: str) -> str:
    return f"{version}@{hashlib.sha1(text.encode('utf-8')).hexdigest()[:8]}"
