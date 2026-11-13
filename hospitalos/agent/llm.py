"""
agent/llm.py — Calls any OpenAI-compatible chat API (Gemini free tier, Groq, ...).

We send a plain HTTP POST to {LLM_BASE_URL}/chat/completions with httpx, so no
vendor SDK is needed and switching provider means changing only the 3 .env values.

Failures become an LLMError with a friendly `user_message`:
  - 429 rate limit / 503 overloaded -> retried up to 3 times with waiting in between
  - 401/403 bad key, 404 wrong model or URL, timeouts, no internet
"""

import asyncio

import httpx

from agent.settings import llm_config_problem, llm_settings

MAX_RETRIES = 3
REQUEST_TIMEOUT_SECONDS = 60


class LLMError(Exception):
    """An LLM problem with a message that is safe and helpful to show the user."""

    def __init__(self, user_message: str):
        super().__init__(user_message)
        self.user_message = user_message


def _retry_wait_seconds(response: httpx.Response, attempt: int) -> float:
    """Use the provider's Retry-After header if present, else 2s, 4s, 8s (max 20s)."""
    try:
        return min(float(response.headers.get("retry-after", "")), 20.0)
    except ValueError:
        return min(2.0 * (2 ** attempt), 20.0)


async def chat_completion(messages: list[dict], tools: list[dict] | None = None) -> dict:
    """
    Send the conversation (and available tools) to the LLM.
    Returns the assistant message dict: {"role": "assistant", "content": ..., "tool_calls": [...]}.
    """
    problem = llm_config_problem()
    if problem:
        raise LLMError(problem)
    s = llm_settings()
    url = s["base_url"].rstrip("/") + "/chat/completions"
    payload = {"model": s["model"], "messages": messages, "temperature": 0.2}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    headers = {"Authorization": f"Bearer {s['api_key']}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await client.post(url, json=payload, headers=headers)
            except httpx.TimeoutException:
                raise LLMError("The AI model took too long to answer. Please try again.")
            except httpx.HTTPError:
                raise LLMError("Could not reach the AI model. Check your internet connection and LLM_BASE_URL.")

            if response.status_code in (429, 500, 502, 503) and attempt < MAX_RETRIES:
                await asyncio.sleep(_retry_wait_seconds(response, attempt))
                continue
            if response.status_code == 429:
                raise LLMError("The AI model's free-tier rate limit was reached. Please wait a minute and try again.")
            if response.status_code in (401, 403):
                raise LLMError("The AI model rejected the API key. Check LLM_API_KEY in your .env file.")
            if response.status_code == 404:
                raise LLMError(f"Model '{s['model']}' or the URL was not found. Check LLM_MODEL and LLM_BASE_URL.")
            if response.status_code >= 400:
                detail = response.text[:300]
                raise LLMError(f"The AI model returned an error (HTTP {response.status_code}): {detail}")

            try:
                return response.json()["choices"][0]["message"]
            except (ValueError, KeyError, IndexError):
                raise LLMError("The AI model sent back a response we could not read.")
    raise LLMError("The AI model is busy right now. Please try again shortly.")
