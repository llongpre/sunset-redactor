"""Judge: identifies over-redaction — non-PII content incorrectly removed."""

import anthropic
from dataclasses import dataclass, field


@dataclass
class OverRedactionIssue:
    location: str  # quote or description of where in the document
    concern: str   # what non-PII content was removed and why it matters


@dataclass
class OverRedactionResult:
    source: str
    issues: list[OverRedactionIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.issues


_TOOL: dict = {
    "name": "report_issues",
    "description": "Report places where non-PII content was incorrectly redacted.",
    "input_schema": {
        "type": "object",
        "properties": {
            "issues": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Quote or describe where in the document the issue appears",
                        },
                        "concern": {
                            "type": "string",
                            "description": "What non-PII content was incorrectly removed and why it matters",
                        },
                    },
                    "required": ["location", "concern"],
                },
            }
        },
        "required": ["issues"],
    },
}

_PROMPT = """\
You are reviewing a redacted document for usability. The original \
contained real company data. The redacted version should preserve \
structure, domain vocabulary, and relationships while removing identity.

Flag any redactions that appear to have removed non-PII content, broken \
a sentence's meaning, or made the document unusable for training purposes.

Original:
{original_text}

Redacted:
{redacted_text}\
"""


def judge_over_redaction(
    original_text: str,
    redacted_text: str,
    source: str = "",
) -> OverRedactionResult:
    """Find places where the redaction incorrectly removed non-PII content."""
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=[_TOOL],
        tool_choice={"type": "tool", "name": "report_issues"},
        messages=[
            {
                "role": "user",
                "content": _PROMPT.format(
                    original_text=original_text,
                    redacted_text=redacted_text,
                ),
            }
        ],
    )

    tool_use = next((b for b in response.content if b.type == "tool_use"), None)
    if not tool_use:
        return OverRedactionResult(source=source)

    issues = [
        OverRedactionIssue(location=i["location"], concern=i["concern"])
        for i in tool_use.input.get("issues", [])
    ]
    return OverRedactionResult(source=source, issues=issues)
