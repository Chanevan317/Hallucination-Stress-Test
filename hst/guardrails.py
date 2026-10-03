"""Input guardrails and the exact user-facing messages."""

from hst import config

MESSAGES = {
    "ERR_INPUT_EMPTY": "Input cannot be empty. Please enter a valid question.",
    "ERR_INPUT_TOO_LONG": "Input length exceeds limit ({max} characters max). Current length: {n}.",
    "ERR_INVALID_JSON": "Model output was not valid JSON. Raw text retained for inspection.",
    "ERR_OFF_TOPIC": "GUARDRAIL ALERT: Query flagged as OUT_OF_SCOPE. Unhandled domain query rejected safely.",
    "ERR_API": "API error: {detail}",
    "ERR_RATE_LIMIT": "Rate limited, retrying in {seconds:.0f} s (attempt {attempt}).",
    "ERR_DAILY_LIMIT": "Daily limit reached, run paused. Finished calls are saved; resume later or use stored results.",
    "ERR_JUDGE_FAILURE": "Judge model failed to evaluate this output. Raw output shown unverified.",
    "ERR_NO_KEY": "Enter your Groq API key in Settings first.",
    "ERR_MODELS": "Pick Model A, Model B and a judge model in Settings first.",
    "ERR_SAME_MODEL": "Model A and Model B must be different models.",
    "INFO_STORED": "Using stored results (offline mode). No API calls are being made for result views.",
    "INFO_PROMPT_SAVED": "Prompt revision saved to history log at {timestamp}.",
}


def message(code: str, **kwargs) -> str:
    return MESSAGES[code].format(**kwargs)


def check_input(text: str):
    """Validate a live question. Returns (ok, error_code | None, message | None)."""
    stripped = (text or "").strip()
    if not stripped:
        return False, "ERR_INPUT_EMPTY", message("ERR_INPUT_EMPTY")
    if len(stripped) > config.MAX_INPUT_CHARS:
        return (
            False,
            "ERR_INPUT_TOO_LONG",
            message("ERR_INPUT_TOO_LONG", max=config.MAX_INPUT_CHARS, n=len(stripped)),
        )
    return True, None, None
