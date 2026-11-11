"""
Input sanitization, PII redaction, and prompt-injection protection for AI clinical agents.
"""
import re
from dataclasses import dataclass
from typing import Optional

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_MULTI_SPACE_RE = re.compile(r"[ \t]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3,4}\)?[\s.-]?){2}\d{3,4}(?!\d)")

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+|any\s+)?(?:previous|prior|above)\s+instructions?", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+|any\s+)?(?:previous|prior|above)\s+instructions?", re.IGNORECASE),
    re.compile(r"forget\s+(?:everything|all\s+previous|your\s+instructions)", re.IGNORECASE),
    re.compile(r"(?:reveal|show|print|leak|dump)\s+(?:your\s+|the\s+)?(?:system\s+prompt|hidden\s+instructions|api\s*key|secret)", re.IGNORECASE),
    re.compile(r"<\s*\|\s*(?:im_start|im_end|system|assistant|user)\s*\|\s*>", re.IGNORECASE),
    re.compile(r"(?:^|\n)\s*###\s*(?:system|instruction|override)\b", re.IGNORECASE),
    re.compile(r"\b(?:jailbreak|developer\s+mode|dan\s+mode|override\s+safety)\b", re.IGNORECASE),
]

_PLACEHOLDER_VALUES = {
    "",
    "none",
    "n/a",
    "na",
    "nil",
    "null",
    "nkda",
    "no known allergies",
    "no known drug allergies",
    "nothing",
    "-",
    "--",
}


class PromptInjectionError(ValueError):
    """Raised when user input contains prompt-injection or instruction-override patterns."""


@dataclass
class SanitizationResult:
    text: str
    was_truncated: bool
    injection_detected: bool


def is_non_clinical_placeholder(value: Optional[str]) -> bool:
    """Returns True if the string represents an empty or 'none/N/A' clinical field."""
    if value is None:
        return True
    cleaned = str(value).strip().lower()
    return cleaned in _PLACEHOLDER_VALUES


def redact_pii(text: str) -> str:
    """Redacts emails and phone numbers before sending text to external LLM providers."""
    if not text:
        return ""
    redacted = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    redacted = _PHONE_RE.sub("[REDACTED_PHONE]", redacted)
    return redacted


def sanitize_clinical_text(
    text: Optional[str],
    *,
    max_length: int = 2000,
    reject_injection: bool = True,
) -> SanitizationResult:
    """
    Cleans clinical text input: strips control characters/HTML, checks prompt-injection
    patterns, and enforces maximum character length.
    """
    if text is None:
        return SanitizationResult(text="", was_truncated=False, injection_detected=False)

    cleaned = str(text)
    cleaned = _CONTROL_CHARS_RE.sub("", cleaned)

    injection_detected = any(pattern.search(cleaned) for pattern in _INJECTION_PATTERNS)
    if injection_detected and reject_injection:
        raise PromptInjectionError(
            "Input contains disallowed instruction-override patterns."
        )

    cleaned = _HTML_TAG_RE.sub(" ", cleaned)
    cleaned = _MULTI_SPACE_RE.sub(" ", cleaned)
    cleaned = _MULTI_NEWLINE_RE.sub("\n\n", cleaned).strip()

    was_truncated = False
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip()
        was_truncated = True

    return SanitizationResult(
        text=cleaned,
        was_truncated=was_truncated,
        injection_detected=injection_detected,
    )
