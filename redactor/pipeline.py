"""Orchestrates the full redaction pipeline: load → detect → redact → write output."""
import json
import re
from pathlib import Path

from redactor.detectors import regex_detector, llm_detector
from redactor.entity_registry import EntityRegistry
from redactor.models import Match, PIIKind
from redactor.parsers import slack_json, pdf, markdown


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def redact_text(text: str, registry: EntityRegistry | None = None) -> str:
    """Detect and redact all PII in a string. Creates a throwaway registry if none given."""
    if registry is None:
        registry = EntityRegistry()
    matches = _detect_all(text)
    return _apply(text, matches, registry)


def run(input_dir: str, output_dir: str) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    registry = EntityRegistry()
    evidence: list[dict] = []

    # Pre-register all Slack profiles across all files before processing any text
    # so aliases are available regardless of file processing order.
    for path in sorted(Path(input_dir).iterdir()):
        if path.suffix == ".json":
            for msg in slack_json.parse(str(path)).messages:
                if msg.user_profile:
                    _register_profile(msg.user_profile, registry)

    for path in sorted(Path(input_dir).iterdir()):
        if path.suffix == ".json":
            _process_slack(path, out, registry, evidence)
        elif path.suffix == ".pdf":
            _process_pdf(path, out, registry, evidence)
        elif path.suffix == ".md":
            _process_markdown(path, out, registry, evidence)

    (out / "evidence_by_file.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )
    (out / "evidence_by_placeholder.json").write_text(
        json.dumps(_group_by_placeholder(evidence), indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def _detect_all(text: str) -> list[Match]:
    matches = regex_detector.detect(text) + llm_detector.detect(text)
    return _remove_overlaps(sorted(matches, key=lambda m: (m.start, -(m.end - m.start))))


def _remove_overlaps(matches: list[Match]) -> list[Match]:
    result: list[Match] = []
    last_end = -1
    for m in matches:
        if m.start >= last_end:
            result.append(m)
            last_end = m.end
    return result


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------

def _apply(text: str, matches: list[Match], registry: EntityRegistry) -> str:
    parts = []
    cursor = 0
    for m in matches:
        parts.append(text[cursor:m.start])
        parts.append(registry.placeholder_for(m.value, m.kind))
        cursor = m.end
    parts.append(text[cursor:])
    return "".join(parts)


# ---------------------------------------------------------------------------
# Slack JSON processing
# ---------------------------------------------------------------------------

def _process_slack(
    path: Path, out: Path, registry: EntityRegistry, evidence: list[dict]
) -> None:
    export = slack_json.parse(str(path))

    redacted_messages = []
    for msg in export.messages:
        redacted = dict(ts=msg.ts, user_id=msg.user_id, bot_id=msg.bot_id)

        # redact message text
        text_matches = _detect_all(msg.text)
        redacted["text"] = _apply(msg.text, text_matches, registry)
        _record(evidence, path.name, "text", msg.text, text_matches, registry)

        # redact user profile fields
        if msg.user_profile:
            redacted["user_profile"] = _redact_profile(
                msg.user_profile, registry, evidence, path.name
            )

        if msg.user_id:
            redacted["user_id"] = registry.placeholder_for(msg.user_id, PIIKind.SLACK_USER_ID)

        redacted_messages.append(redacted)

    output = {"channel": export.channel_name, "messages": redacted_messages}
    (out / f"redacted_{path.name}").write_text(json.dumps(output, indent=2), encoding="utf-8")


def _register_profile(profile, registry: EntityRegistry) -> None:
    """Register all name representations for a user as aliases of the same entity."""
    if not profile.real_name:
        return
    entity = registry.get_or_create(profile.real_name, PIIKind.PERSON)
    for val in (profile.display_name, profile.first_name, profile.username):
        if val:
            registry.alias(val, entity)
    if profile.avatar_hash:
        registry.get_or_create(profile.avatar_hash, PIIKind.AVATAR_HASH)


def _redact_profile(profile, registry: EntityRegistry, evidence: list[dict], filename: str) -> dict:
    result = {}

    # Anchor on real_name as the canonical identity, alias all other name
    # representations to the same entity so they get the same placeholder.
    entity = None
    if profile.real_name:
        entity = registry.get_or_create(profile.real_name, PIIKind.PERSON)
        result["real_name"] = entity.placeholder
        _record_field(evidence, filename, "user_profile.real_name", profile.real_name, entity)

    for field in ("display_name", "first_name", "username"):
        val = getattr(profile, field)
        if val and entity:
            registry.alias(val, entity)
            result[field] = entity.placeholder
            _record_field(evidence, filename, f"user_profile.{field}", val, entity)
        elif val:
            result[field] = val  # no real_name anchor — leave as-is

    # title is free text, not necessarily just a name
    if profile.title:
        matches = _detect_all(profile.title)
        result["title"] = _apply(profile.title, matches, registry)
        _record(evidence, filename, "user_profile.title", profile.title, matches, registry)

    if profile.avatar_hash:
        result["avatar_hash"] = registry.placeholder_for(profile.avatar_hash, PIIKind.AVATAR_HASH)

    return result


def _record_field(evidence: list[dict], filename: str, field: str, value: str, entity) -> None:
    evidence.append({
        "file": filename,
        "field": field,
        "kind": PIIKind.PERSON,
        "original_value": value,
        "placeholder": entity.placeholder,
        "context": value,
    })


# ---------------------------------------------------------------------------
# PDF processing
# ---------------------------------------------------------------------------

def _process_pdf(
    path: Path, out: Path, registry: EntityRegistry, evidence: list[dict]
) -> None:
    doc = pdf.extract(str(path))
    redacted_pages = []

    for page in doc.pages:
        matches = _detect_all(page.text)
        redacted_text = _apply(page.text, matches, registry)
        _record(evidence, path.name, f"page_{page.page_num}", page.text, matches, registry)
        redacted_pages.append(f"--- Page {page.page_num} ---\n{redacted_text}")

    out_path = out / f"redacted_{path.stem}.txt"
    out_path.write_text("\n\n".join(redacted_pages), encoding="utf-8")


# ---------------------------------------------------------------------------
# Markdown processing
# ---------------------------------------------------------------------------

def _process_markdown(
    path: Path, out: Path, registry: EntityRegistry, evidence: list[dict]
) -> None:
    doc = markdown.parse(str(path))
    redacted_sections = []
    for section in doc.sections:
        matches = _detect_all(section.text)
        redacted_text = _apply(section.text, matches, registry)
        _record(evidence, path.name, section.heading or "<preamble>", section.text, matches, registry)
        redacted_sections.append(redacted_text)
    out_path = out / f"redacted_{path.name}"
    out_path.write_text("\n\n".join(redacted_sections), encoding="utf-8")


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

def _group_by_placeholder(evidence: list[dict]) -> dict:
    grouped: dict[str, dict] = {}
    for entry in evidence:
        ph = entry["placeholder"]
        if ph not in grouped:
            grouped[ph] = {
                "kind": entry["kind"],
                "original_value": entry["original_value"],
                "redactions": [],
            }
        grouped[ph]["redactions"].append({
            "file": entry["file"],
            "field": entry["field"],
            "context": entry["context"],
        })
    return dict(sorted(grouped.items()))


def _record(
    evidence: list[dict],
    filename: str,
    field: str,
    original: str,
    matches: list[Match],
    registry: EntityRegistry,
) -> None:
    for m in matches:
        evidence.append({
            "file": filename,
            "field": field,
            "kind": m.kind.value,
            "original_value": m.value,
            "placeholder": registry.placeholder_for(m.value, m.kind),
            "context": _snippet(original, m.start, m.end),
        })


def _snippet(text: str, start: int, end: int, window: int = 40) -> str:
    lo = max(0, start - window)
    hi = min(len(text), end + window)
    return f"...{text[lo:hi]}..."
