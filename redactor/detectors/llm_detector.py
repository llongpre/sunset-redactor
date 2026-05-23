"""Detects PII using Claude API with structured output. Acts as both primary detector
for contextual PII (names, addresses, ages) and safety net for anything regex missed."""
import re
import anthropic
from redactor.models import Match, PIIKind

_CLIENT = anthropic.Anthropic()

# Kinds handled by the LLM. High-confidence regex kinds (EMAIL, API_TOKEN, SSN,
# CREDIT_CARD, SLACK_USER_ID, AVATAR_HASH) are excluded — regex is more reliable
# for those and the LLM adds hallucination risk without benefit.
_LLM_KINDS = [
    PIIKind.PERSON,
    PIIKind.ADDRESS,
    PIIKind.AGE,
    PIIKind.PHONE,
    PIIKind.TAX_ID,
    PIIKind.BANK_ACCOUNT,
    PIIKind.ROUTING_NUMBER,
    PIIKind.PASSPORT,
    PIIKind.IP_ADDRESS,
]

_TOOL = {
    "name": "report_pii",
    "description": "Report all PII found in the text.",
    "input_schema": {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "value": {
                            "type": "string",
                            "description": "Exact string from the text to redact.",
                        },
                        "kind": {
                            "type": "string",
                            "enum": [k.value for k in _LLM_KINDS],
                        },
                    },
                    "required": ["value", "kind"],
                },
            }
        },
        "required": ["findings"],
    },
}

_SYSTEM = """\
You are a PII detection system. Identify all personally identifiable information in the text.

A regex layer already runs alongside you and reliably catches well-formatted structured PII \
(emails, SSNs, credit cards, API tokens, IPs, phone numbers, passports). Flag those too if \
you see them — you act as a safety net for formats regex may miss — but your primary value \
is catching what regex cannot: person names, addresses, and bare ages.

Rules for PERSON:
- Redact full names of real individuals. Use context to distinguish names from common words:
    - "Grace Liu" → PERSON, but "grace period" → not a person
    - "Bill Nguyen" → PERSON, but "bill payment" / "billable" → not a person
    - "Chase Kim" → PERSON, but "chase" as a verb or "Chase Bank" → not a person
    - "May Chen" → PERSON, but "May" as a month or modal verb → not a person
    - "Rose Patel" → PERSON, but "rose" as past tense of rise → not a person
    - "Hope Kaplan" → PERSON, but "I hope" / "hope this helps" → not a person
    - "Grant Lee" → PERSON, but "grant permission" / "grant-funded" → not a person
    - "Faith Morgan" → PERSON, but "keep faith" → not a person
    - "Mark Rivera" → PERSON, but "mark the task" as a verb → not a person
- Organisation names in general business prose → not a person (e.g. "Chase Bank requires a webhook", "Justice Grown expanded").
- Exception: redact an employer name when it appears in a personal bio paragraph — i.e. alongside a named individual's role, credentials, or age. It narrows the person's identity even though it is an org name.
    - "Adam Cox stood out as Steward Healthcare's go-to expert" → redact "Steward Healthcare" (bio context)
    - "Grace Liu joined Meridian Bank as a risk analyst" → redact "Meridian Bank" (bio context)
    - "Chase Bank requires a new webhook" → preserve (general prose, no named individual)

Rules for ADDRESS:
- Full street addresses only (number + street + city/state/zip).

Rules for AGE:
- A person's age as a bare number after credentials: "Jared Barrera, MBA, 43,"
- Do NOT flag ages already in "age N" format — those are caught by regex.\
"""


def detect(text: str) -> list[Match]:
    response = _CLIENT.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        system=_SYSTEM,
        tools=[_TOOL],
        tool_choice={"type": "tool", "name": "report_pii"},
        messages=[{"role": "user", "content": text}],
    )

    tool_use = next(b for b in response.content if b.type == "tool_use")
    findings = tool_use.input.get("findings", [])
    return _to_matches(text, findings)


def _to_matches(text: str, findings: list[dict]) -> list[Match]:
    seen: set[tuple[str, str]] = set()  # deduplicate (value, kind) pairs from LLM
    matches = []
    for item in findings:
        value = item.get("value", "")
        kind_str = item.get("kind", "")
        key = (value.lower(), kind_str)
        if key in seen:
            continue
        seen.add(key)
        kind = PIIKind[kind_str]
        for m in re.finditer(re.escape(value), text):
            matches.append(Match(start=m.start(), end=m.end(), kind=kind, value=value))
    return matches
