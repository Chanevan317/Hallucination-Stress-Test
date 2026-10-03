"""Constants and file locations shared by the whole app."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PROMPTS_DIR = ROOT / "prompts"
RESULTS_DIR = ROOT / "results"
HISTORY_DIR = ROOT / "history"

DATASET_FILE = DATA_DIR / "dataset.json"
UNSEEN_FILE = DATA_DIR / "unseen_set.json"
RESULTS_FILE = RESULTS_DIR / "results.jsonl"
CACHED_FILE = RESULTS_DIR / "cached_results.json"
PROMPT_HISTORY_FILE = HISTORY_DIR / "prompt_history.json"
LIVE_HISTORY_FILE = HISTORY_DIR / "live_history.jsonl"

VERSIONS = ["V1", "V2", "V3"]
VERSION_NAMES = {"V1": "Baseline", "V2": "Guardrail", "V3": "Verification"}
PROMPT_FILES = {"V1": "v1.txt", "V2": "v2.txt", "V3": "v3.txt"}
JUDGE_FILE = "judge.txt"
JUDGE_LIVE_FILE = "judge_live.txt"

# Preselected in Settings when the key is tested (chosen from measurements, see README).
DEFAULT_MODEL_A = "openai/gpt-oss-20b"
DEFAULT_MODEL_B = "qwen/qwen3.8-27b"
DEFAULT_JUDGE = "openai/gpt-oss-120b"

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MAX_INPUT_CHARS = 500
TEMPERATURE = 0.0
REQUEST_TIMEOUT_S = 30
# Reasoning models (gpt-oss, qwen3) spend completion tokens on hidden reasoning before
# the JSON, so these caps must be generous. The judge's retry doubles its cap.
MODEL_MAX_TOKENS = 1500
JUDGE_MAX_TOKENS = 1200
# A 429 that asks us to wait longer than this is treated as a daily limit.
MAX_RATE_LIMIT_WAIT_S = 120

VERDICTS = ("ANSWERABLE", "FALSE_PREMISE", "UNVERIFIABLE", "OUT_OF_SCOPE")
BATCH_LABELS = (
    "HALLUCINATED",
    "CORRECT_DEFENSE",
    "OVER_REFUSAL",
    "CORRECT_ANSWER",
    "INCORRECT_ANSWER",
)
LIVE_LABELS = ("NO_INVENTED_DETAILS", "INVENTED_DETAILS", "NEEDS_REVIEW")

FLAG_INVALID = "INVALID_OUTPUT"
FLAG_API_ERROR = "API_ERROR"
FLAG_JUDGE_ERROR = "JUDGE_ERROR"

DATASET_FIELDS = (
    "id",
    "question",
    "category",
    "is_trap",
    "key_false_claim",
    "correct_behaviour",
    "reference_fact",
)
