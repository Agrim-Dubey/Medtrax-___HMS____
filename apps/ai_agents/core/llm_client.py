"""
Hybrid LLM client supporting Google Gemini and OpenAI with strict timeouts,
PII redaction, JSON validation, and automatic deterministic fallback.
"""
import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

import requests
from django.conf import settings

from .sanitizer import redact_pii

logger = logging.getLogger(__name__)

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


@dataclass
class LLMResult:
    success: bool
    data: Optional[Dict[str, Any]]
    provider: str
    model: str
    fallback_reason: Optional[str] = None


def _redact_payload(obj: Any) -> Any:
    if isinstance(obj, str):
        return redact_pii(obj)
    if isinstance(obj, list):
        return [_redact_payload(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _redact_payload(v) for k, v in obj.items()}
    return obj


def _parse_json_object(raw_text: str) -> Dict[str, Any]:
    cleaned = _JSON_FENCE_RE.sub("", raw_text.strip()).strip()
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("LLM response JSON is not an object.")
    return parsed


class HybridLLMClient:
    """
    Dependency-light clinical LLM gateway. Never raises on external provider failures;
    returns LLMResult(success=False, ...) so agents always fall back deterministically.
    """

    def __init__(self) -> None:
        self.provider = str(getattr(settings, "AI_LLM_PROVIDER", "none") or "none").lower().strip()
        self.api_key = str(getattr(settings, "AI_LLM_API_KEY", "") or "").strip()
        default_model = "gemini-2.0-flash" if self.provider == "gemini" else "gpt-4o-mini"
        self.model = str(getattr(settings, "AI_LLM_MODEL", "") or default_model).strip()
        self.timeout_seconds = max(1, int(getattr(settings, "AI_LLM_TIMEOUT_SECONDS", 8)))
        self.max_tokens = max(64, int(getattr(settings, "AI_LLM_MAX_TOKENS", 600)))

    def is_configured(self) -> bool:
        return self.provider in {"gemini", "openai"} and bool(self.api_key)

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_payload: Dict[str, Any],
        required_keys: Iterable[str] = (),
    ) -> LLMResult:
        if not self.is_configured():
            reason = "llm_disabled" if self.provider in {"", "none"} else "missing_api_key"
            return LLMResult(
                success=False,
                data=None,
                provider=self.provider or "none",
                model=self.model,
                fallback_reason=reason,
            )

        safe_payload = _redact_payload(user_payload)
        serialized_payload = json.dumps(safe_payload, ensure_ascii=False)

        try:
            if self.provider == "gemini":
                raw_text = self._call_gemini(system_prompt, serialized_payload)
            elif self.provider == "openai":
                raw_text = self._call_openai(system_prompt, serialized_payload)
            else:
                return LLMResult(
                    success=False,
                    data=None,
                    provider=self.provider,
                    model=self.model,
                    fallback_reason="unsupported_provider",
                )

            parsed = _parse_json_object(raw_text)
            missing = [k for k in required_keys if k not in parsed]
            if missing:
                return LLMResult(
                    success=False,
                    data=None,
                    provider=self.provider,
                    model=self.model,
                    fallback_reason=f"missing_keys:{','.join(missing)}",
                )

            return LLMResult(
                success=True,
                data=parsed,
                provider=self.provider,
                model=self.model,
            )
        except requests.Timeout:
            logger.warning("AI LLM request timed out (provider=%s)", self.provider)
            return LLMResult(
                success=False,
                data=None,
                provider=self.provider,
                model=self.model,
                fallback_reason="timeout",
            )
        except requests.RequestException as exc:
            logger.warning("AI LLM HTTP error (provider=%s): %s", self.provider, type(exc).__name__)
            return LLMResult(
                success=False,
                data=None,
                provider=self.provider,
                model=self.model,
                fallback_reason="upstream_http_error",
            )
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            logger.warning("AI LLM response parse error (provider=%s): %s", self.provider, exc)
            return LLMResult(
                success=False,
                data=None,
                provider=self.provider,
                model=self.model,
                fallback_reason="invalid_json_response",
            )

    def _call_gemini(self, system_prompt: str, user_text: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }
        body = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_text}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": self.max_tokens,
                "responseMimeType": "application/json",
            },
        }
        resp = requests.post(url, headers=headers, json=body, timeout=self.timeout_seconds)
        resp.raise_for_status()
        payload = resp.json()
        candidates = payload.get("candidates") or []
        parts = candidates[0]["content"]["parts"]
        return parts[0]["text"]

    def _call_openai(self, system_prompt: str, user_text: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        body = {
            "model": self.model,
            "temperature": 0.2,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
        }
        resp = requests.post(url, headers=headers, json=body, timeout=self.timeout_seconds)
        resp.raise_for_status()
        payload = resp.json()
        return payload["choices"][0]["message"]["content"]
