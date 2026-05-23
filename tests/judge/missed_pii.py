"""Judge: identifies residual PII or identifying information that survived redaction."""

import anthropic
from dataclasses import dataclass, field


@dataclass
class PIIFinding:
    text: str        # the specific text snippet that is identifying
    reason: str      # why it could still identify a real person
    confidence: str  # "high" | "medium" | "low"


@dataclass
class MissedPIIResult:
    source: str
    findings: list[PIIFinding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.findings


_TOOL: dict = {
    "name": "report_findings",
    "description": "Report residual PII or identifying information found in the redacted text.",
    "input_schema": {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The specific text snippet that is still identifying",
                        },
                        "reason": {
                            "type": "string",
                            "description": "Why this could still identify a real person",
                        },
                        "confidence": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                        },
                    },
                    "required": ["text", "reason", "confidence"],
                },
            }
        },
        "required": ["findings"],
    },
}

_PROMPT = """\
You are a privacy auditor. The following text has been through a PII \
redaction pipeline. Identify anything that could still identify a real \
person — including names, ages, employers, dates tied to career events, \
credentials, or combinations of attributes that together are identifying.

Be conservative. Flag uncertain cases rather than ignoring them.

Redacted text:
{redacted_text}\
"""


def judge_missed_pii(text: str, source: str = "") -> MissedPIIResult:
    """Identify residual identifying information that survived redaction."""
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=[_TOOL],
        tool_choice={"type": "tool", "name": "report_findings"},
        messages=[{"role": "user", "content": _PROMPT.format(redacted_text=text)}],
    )

    tool_use = next((b for b in response.content if b.type == "tool_use"), None)
    if not tool_use:
        return MissedPIIResult(source=source)

    findings = [
        PIIFinding(
            text=f["text"],
            reason=f["reason"],
            confidence=f["confidence"],
        )
        for f in tool_use.input.get("findings", [])
    ]
    return MissedPIIResult(source=source, findings=findings)
