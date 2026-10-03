"""Minimal Groq chat client (OpenAI-compatible endpoint) tuned for the free tier.

Handles throttling, 429 back-off, and tells a short rate limit (wait and retry)
apart from a daily limit (stop and let the caller pause the run).
"""

import re
import time
from dataclasses import dataclass

import requests

from hst import config


class GroqError(Exception):
    pass


class ApiError(GroqError):
    """The call failed after retries (bad key, bad model, timeout, 5xx...)."""


class DailyLimitError(GroqError):
    """Free-tier daily quota (or a very long wait) reached; stop the run."""


@dataclass
class ChatResult:
    text: str
    latency_ms: int
    model: str
    total_tokens: int = 0


_DURATION = re.compile(r"try again in\s+((?:\d+h)?(?:\d+m(?!s))?(?:[\d.]+s)?(?:[\d.]+ms)?)", re.I)


def parse_wait_seconds(message: str) -> float | None:
    """Parse Groq's 'Please try again in 1m23.4s' style hint."""
    m = _DURATION.search(message or "")
    if not m or not m.group(1):
        return None
    total = 0.0
    for value, unit in re.findall(r"([\d.]+)(ms|h|m|s)", m.group(1)):
        v = float(value)
        total += {"h": 3600, "m": 60, "s": 1, "ms": 0.001}[unit] * v
    return total


class GroqClient:
    def __init__(
        self,
        api_key: str,
        *,
        min_interval: float = 2.5,
        max_retries: int = 2,
        max_rate_limit_retries: int = 5,
        timeout: float = config.REQUEST_TIMEOUT_S,
        session=None,
        sleep=time.sleep,
        clock=time.monotonic,
        on_wait=None,
    ):
        self.api_key = api_key
        self.min_interval = min_interval
        self.max_retries = max_retries
        self.max_rate_limit_retries = max_rate_limit_retries
        self.timeout = timeout
        self.session = session or requests.Session()
        self._sleep = sleep
        self._clock = clock
        self.on_wait = on_wait  # callable(seconds: float, attempt: int, reason: str)
        self._last_call = None
        self.calls_made = 0
        self.total_tokens = 0  # tokens used by successful calls (includes hidden reasoning)

    # -- helpers ---------------------------------------------------------
    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _throttle(self):
        if self._last_call is not None:
            wait = self.min_interval - (self._clock() - self._last_call)
            if wait > 0:
                self._sleep(wait)
        self._last_call = self._clock()

    def _wait(self, seconds: float, attempt: int, reason: str):
        if self.on_wait:
            self.on_wait(seconds, attempt, reason)
        self._sleep(seconds)

    @staticmethod
    def _error_message(resp) -> str:
        try:
            return resp.json().get("error", {}).get("message", "") or resp.text[:300]
        except ValueError:
            return resp.text[:300]

    # -- public API ------------------------------------------------------
    def list_models(self) -> list[str]:
        try:
            resp = self.session.get(
                f"{config.GROQ_BASE_URL}/models", headers=self._headers(), timeout=self.timeout
            )
        except requests.RequestException as exc:
            raise ApiError(f"Could not reach Groq: {exc}") from exc
        if resp.status_code == 401:
            raise ApiError("Invalid API key (401).")
        if resp.status_code >= 400:
            raise ApiError(f"Groq error {resp.status_code}: {self._error_message(resp)}")
        return sorted(m["id"] for m in resp.json().get("data", []))

    def chat(
        self,
        model: str,
        prompt: str,
        *,
        temperature: float = config.TEMPERATURE,
        json_mode: bool = False,
        max_tokens: int = config.MODEL_MAX_TOKENS,
    ) -> ChatResult:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        transient_failures = 0
        rate_limit_hits = 0
        while True:
            self._throttle()
            start = self._clock()
            try:
                resp = self.session.post(
                    f"{config.GROQ_BASE_URL}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                transient_failures += 1
                if transient_failures > self.max_retries:
                    raise ApiError(f"Network error/timeout after {self.max_retries} retries: {exc}") from exc
                self._wait(2**transient_failures, transient_failures, "network")
                continue
            latency_ms = int((self._clock() - start) * 1000)
            self.calls_made += 1

            if resp.status_code == 200:
                body = resp.json()
                text = body["choices"][0]["message"].get("content") or ""
                tokens = (body.get("usage") or {}).get("total_tokens", 0)
                self.total_tokens += tokens
                return ChatResult(text=text, latency_ms=latency_ms, model=model, total_tokens=tokens)

            message = self._error_message(resp)
            if resp.status_code == 429:
                wait = None
                if resp.headers.get("retry-after"):
                    try:
                        wait = float(resp.headers["retry-after"])
                    except ValueError:
                        pass
                if wait is None:
                    wait = parse_wait_seconds(message)
                if (
                    "per day" in message.lower()
                    or (wait is not None and wait > config.MAX_RATE_LIMIT_WAIT_S)
                ):
                    raise DailyLimitError(message or "Daily limit reached.")
                rate_limit_hits += 1
                if rate_limit_hits > self.max_rate_limit_retries:
                    raise DailyLimitError(f"Still rate limited after {self.max_rate_limit_retries} retries: {message}")
                self._wait((wait if wait is not None else 5 * rate_limit_hits) + 0.5, rate_limit_hits, "rate_limit")
                continue
            if resp.status_code >= 500:
                transient_failures += 1
                if transient_failures > self.max_retries:
                    raise ApiError(f"Groq server error {resp.status_code} after retries: {message}")
                self._wait(2**transient_failures, transient_failures, "server")
                continue
            if resp.status_code == 401:
                raise ApiError("Invalid API key (401).")
            if resp.status_code == 400 and json_mode:
                # JSON mode rejected the generation; keep the raw text for validation.
                try:
                    failed = resp.json().get("error", {}).get("failed_generation")
                except ValueError:
                    failed = None
                if failed is not None:
                    return ChatResult(text=failed, latency_ms=latency_ms, model=model)
            raise ApiError(f"Groq error {resp.status_code}: {message}")
