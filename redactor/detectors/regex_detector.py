"""Detects structured PII using regex: emails, phones, SSNs, tokens, IPs, etc."""
import re
from redactor.models import Match, PIIKind


# Each entry is (compiled_pattern, kind).
# Order matters for overlapping matches — more specific patterns first.
_PATTERNS: list[tuple[re.Pattern, PIIKind]] = [
    # API tokens — before general patterns to avoid partial matches
    (re.compile(r"\bxox[bpars]-[A-Za-z0-9\-]+"), PIIKind.API_TOKEN),
    (re.compile(r"\bsk_(?:live|test)_[A-Za-z0-9]+"), PIIKind.API_TOKEN),

    # Financial identifiers
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), PIIKind.SSN),
    (re.compile(r"\b\d{2}-\d{7}\b"), PIIKind.TAX_ID),
    (re.compile(r"\b(?:\d{4}[\s\-]){3}\d{4}\b"), PIIKind.CREDIT_CARD),
    (re.compile(r"(?i)\baccount\s+(\d{6,12})\b"), PIIKind.BANK_ACCOUNT),
    (re.compile(r"(?i)\brouting\s+(\d{9})\b"), PIIKind.ROUTING_NUMBER),

    # Contact
    (re.compile(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}"), PIIKind.EMAIL),
    (re.compile(r"\+\d{1,3}[\s.\-]?(?:\(?\d+\)?[\s.\-]?){2,5}\d{2,}"), PIIKind.PHONE),
    (re.compile(r"\b\d{3}[\s.\-]\d{3}[\s.\-]\d{4}\b"), PIIKind.PHONE),

    # Government IDs — keyword-anchored to avoid false positives on product codes etc.
    (re.compile(r"(?i)passport\s+([A-Z]\d{7})\b"), PIIKind.PASSPORT),

    # Network
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), PIIKind.IP_ADDRESS),

    # Ages
    (re.compile(r"\bage \d{1,3}\b"), PIIKind.AGE),

    # Slack structural identifiers
    (re.compile(r"\bU[A-Z0-9]{4,10}\b"), PIIKind.SLACK_USER_ID),
    (re.compile(r"\bh_u\w+\b"), PIIKind.AVATAR_HASH),
]


def detect(text: str) -> list[Match]:
    """Return all PII matches found in text, sorted by position, non-overlapping.

    For patterns with a capture group, the match span and value refer to the
    captured group only (e.g. just the number, not the keyword anchor).
    """
    matches: list[Match] = []
    for pattern, kind in _PATTERNS:
        for m in pattern.finditer(text):
            if m.lastindex:  # pattern has a capture group — use it
                start, end = m.span(1)
                value = m.group(1)
            else:
                start, end = m.start(), m.end()
                value = m.group(0)
            matches.append(Match(start=start, end=end, kind=kind, value=value))

    return _remove_overlaps(sorted(matches, key=lambda m: (m.start, -(m.end - m.start))))


def _remove_overlaps(matches: list[Match]) -> list[Match]:
    """Keep the first (longest at each position) match, drop anything that overlaps it."""
    result: list[Match] = []
    last_end = -1
    for m in matches:
        if m.start >= last_end:
            result.append(m)
            last_end = m.end
    return result
