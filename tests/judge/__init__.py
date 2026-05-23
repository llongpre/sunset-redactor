"""LLM judge: tries to re-identify redacted persons from surrounding context."""

import re
import anthropic
from dataclasses import dataclass, field


@dataclass
class PlaceholderVerdict:
    placeholder: str
    identifiable: bool
    confidence: str  # "high" | "medium" | "low"
    inferred_identity: str | None  # None when identifiable=False
    reasoning: str


@dataclass
class JudgeResult:
    source: str
    verdicts: list[PlaceholderVerdict] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Passes only when no placeholder is identifiable at any confidence level."""
        return not any(v.identifiable for v in self.verdicts)

    @property
    def flagged(self) -> list[PlaceholderVerdict]:
        return [v for v in self.verdicts if v.identifiable]


_TOOL: dict = {
    "name": "report_verdicts",
    "description": "Report whether each redacted placeholder can be re-identified from remaining context.",
    "input_schema": {
        "type": "object",
        "properties": {
            "verdicts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "placeholder": {
                            "type": "string",
                            "description": "The placeholder token, e.g. [PERSON_1]",
                        },
                        "identifiable": {
                            "type": "boolean",
                            "description": "True if you can make any reasonable guess at the real identity",
                        },
                        "confidence": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                            "description": "How certain you are about the identification",
                        },
                        "inferred_identity": {
                            "type": "string",
                            "description": "Best guess at the real name, or 'unknown'",
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "One sentence: what specific context clues led to this verdict",
                        },
                    },
                    "required": [
                        "placeholder",
                        "identifiable",
                        "confidence",
                        "inferred_identity",
                        "reasoning",
                    ],
                },
            }
        },
        "required": ["verdicts"],
    },
}

_PROMPT = """\
You are a privacy auditor red-teaming a document redaction system.

Personal names have been replaced with placeholders like [PERSON_1]. Try to identify the
real person behind each placeholder using only what remains: job title, employer, age,
specialization, relationships to others, unique skills, or any other context clues.

Set identifiable=true whenever you can make any reasonable guess — even a partial one.
A partial guess (e.g. "senior ML engineer at a fintech company, probably female based on
pronoun context") still counts as identifiable. Only set identifiable=false if the
placeholder is truly a blank — no useful context whatsoever.

Placeholders to evaluate: {placeholders}

--- DOCUMENT ---
{text}
--- END DOCUMENT ---\
"""


def judge(text: str, source: str = "") -> JudgeResult:
    """Try to re-identify each [PERSON_N] placeholder in a redacted text using Claude."""
    placeholders = sorted(set(re.findall(r"\[PERSON_\d+\]", text)))
    if not placeholders:
        return JudgeResult(source=source)

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=[_TOOL],
        tool_choice={"type": "tool", "name": "report_verdicts"},
        messages=[
            {
                "role": "user",
                "content": _PROMPT.format(
                    placeholders=", ".join(placeholders),
                    text=text,
                ),
            }
        ],
    )

    tool_use = next((b for b in response.content if b.type == "tool_use"), None)
    if not tool_use:
        return JudgeResult(source=source)

    verdicts = [
        PlaceholderVerdict(
            placeholder=v["placeholder"],
            identifiable=v["identifiable"],
            confidence=v["confidence"],
            inferred_identity=v.get("inferred_identity") if v["identifiable"] else None,
            reasoning=v["reasoning"],
        )
        for v in tool_use.input.get("verdicts", [])
    ]

    # fill in any placeholders the model skipped
    found = {v.placeholder for v in verdicts}
    for ph in placeholders:
        if ph not in found:
            verdicts.append(
                PlaceholderVerdict(
                    placeholder=ph,
                    identifiable=False,
                    confidence="low",
                    inferred_identity=None,
                    reasoning="Not evaluated by judge.",
                )
            )

    verdicts.sort(key=lambda v: v.placeholder)
    return JudgeResult(source=source, verdicts=verdicts)
