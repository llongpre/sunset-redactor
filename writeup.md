# Redaction Pipeline — Design Decisions & Known Limitations

## Setup

**Requirements:** Python 3.13, Anthropic API key

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key-here
```

---

## Running the pipeline

**Provided sample files**
```bash
python run.py
# inputs:  tests/data/provided/inputs/
# outputs: tests/data/provided/outputs/
```

**New inputs**
```bash
python run.py path/to/inputs/ path/to/outputs/
```
Supports `.json` (Slack exports), `.pdf`, and `.md`. Outputs are prefixed with `redacted_`, plus `evidence_by_file.json` and `evidence_by_placeholder.json`.

---

## Running tests

```bash
# Full run — re-runs the pipeline (~2 min, hits LLM API)
pytest tests/

# Fast run — assert against already-generated outputs
pytest tests/ --use-existing

# Single test
pytest tests/test_unit.py::test_stripe_key_is_redacted
```

`test_unit.py` — inline fixture tests, one behavior per test, no LLM calls  
`test_provided.py` — loads from provided sample files, asserts nuanced disambiguation  
`test_synthetic.py` — loads from synthetic fixtures, covers PII categories not in provided data

---

## Running the LLM judge

```bash
python -m tests.judge.run                               # both output dirs
python -m tests.judge.run tests/data/provided/outputs/
python -m tests.judge.run tests/data/synthetic/outputs/
```

Three complementary probes, each making a Claude API call with structured output:

- **Re-identification** — adversarial probe. Given a redacted document, can Claude name the real person behind each `[PERSON_N]` using only what remains (job title, employer, age, relationships)? Any identification attempt is flagged as a failure.
- **Missed PII** — completeness check. Does anything in the redacted output still identify a real person — self-disclosures, credential combinations, or attribute clusters? This caught a real gap: "Rose is my name" survived redaction after "Rose Patel" was removed.
- **Over-redaction** — usability check. Was any non-PII content incorrectly removed? Requires the sibling `inputs/` directory; files with no recoverable original are skipped.

Results are written to `judge_report.json` in each output directory.

---

## What we redact
- Personal names
- All email addresses (including org emails like `investors@kindlymd.com`)
- Phone numbers
- Physical addresses
- Ages (all formats: `age 46`, `Jared Barrera, MBA, 43`)
- SSNs, tax IDs, credit card numbers, bank account/routing numbers, passport numbers
- API tokens and secrets
- IP addresses
- Slack user IDs and avatar hashes
- Employer names when inside a personal bio paragraph

## What we don't redact
- Financial figures (revenue, expenses) — they're the substance of the document
- Org names in general business prose (e.g. "Chase Bank", "Justice Grown")
- Public URLs
- System/incident identifiers (e.g. `INC-2024-1107`, `BILL_PAY_042`, `risk-8842`) — not personal information

---

## Architecture

### Detection

Two detectors run on every piece of text and their results are merged:

**Regex detector** (`redactor/detectors/regex_detector.py`) — handles well-structured PII where format alone is sufficient: emails, phones, SSNs, tax IDs, credit cards, bank account/routing numbers, API tokens (Slack `xox*`, Stripe `sk_live/test_`), IPs, ages (`age N`), Slack user IDs, and avatar hashes. Patterns are ordered most-specific first. Patterns with a capture group (passport, bank account, routing number) use a keyword anchor — e.g. `\baccount\s+(\d{6,12})` — to avoid false positives on product codes; `m.group(1)` extracts just the value, not the anchor. After collecting all matches, overlapping spans are removed by sorting by `(start, -length)` and keeping the longest match at each position.

**LLM detector** (`redactor/detectors/llm_detector.py`) — handles contextual PII that regex cannot: person names, addresses, and bare ages after credentials (e.g. `"Jared Barrera, MBA, 43"`). Also acts as a safety net for any structured PII in formats regex may miss. Uses the Claude API with `tool_choice: {type: "tool"}` (forced tool use) to guarantee structured JSON output with an enum-constrained `kind` field — no parsing fragility. The enum is restricted to kinds where LLM adds value; EMAIL, SSN, API_TOKEN, CREDIT_CARD, SLACK_USER_ID, AVATAR_HASH are excluded since regex is more reliable and the LLM adds hallucination risk. The LLM's findings are deduplicated by `(value, kind)` before being located in the text via `re.finditer(re.escape(value), text)`.

**Merge** — both detectors' matches are combined, sorted by `(start, -length)`, and overlaps removed. This means a longer regex match always beats a shorter LLM match at the same position, and vice versa.

### Entity registry

`EntityRegistry` (`redactor/entity_registry.py`) provides cross-file deduplication. Keys are `value.lower().strip()`; each key maps to an `Entity(value, kind, placeholder)`. Per-kind counters give independent placeholder sequences: `[PERSON_1]`, `[PERSON_2]`, `[EMAIL_1]`, etc. The `alias(value, entity)` method registers an alternate key pointing to an existing entity without creating a new placeholder.

### Slack profile pre-registration

Before processing any message text, `run()` does a first pass over all JSON files and calls `_register_profile` on every user profile. This anchors `real_name` as the canonical PERSON entity and aliases `display_name`, `first_name`, and `username` to it. As a result, `will.harper` encountered in file B's message text maps to the same `[PERSON_1]` as `Will Harper` from file C's profile, regardless of processing order.

Profile fields are then redacted structurally — no LLM call needed. `real_name`, `display_name`, `first_name`, and `username` are replaced directly via the registry. `title` is free text and still runs through the full detection pipeline. `avatar_hash` is registered and replaced as `AVATAR_HASH`.

### Parsers

**Slack JSON** — messages and user profiles are parsed into typed structs (`Message`, `UserProfile`). Bot messages (identified by `bot_id`) are included; their text is scanned but they have no user profile.

**PDF** — PyMuPDF extracts text per page. A normalization step fixes extraction artifacts before detection: hyphenated line breaks (`word-\nword` → `word-word`) and single newlines (PDF layout wrapping) are collapsed to spaces.

**Markdown** — split into sections by heading using a regex on `^#{1,6} `. Each section is redacted independently and the document is reassembled with the same structure.

### Evidence

Two output files are written after every run:
- `evidence_by_file.json` — flat list of every redaction: file, field, kind, original value, placeholder, and a ±40-character context snippet
- `evidence_by_placeholder.json` — grouped by placeholder, showing the canonical value and every location it was found; useful for verifying that all occurrences of a placeholder really refer to the same person

---

## Synthetic test fixtures

Four files in `tests/data/synthetic/inputs/` extend coverage beyond the provided samples.

**JSON fixtures** (`security-incidents_2024-09-05.json`, `hr-onboarding_2025-01-20.json`) cover: IP addresses alongside system IDs that must survive (`INC-2024-0905`), UK + US phones in the same message, passport numbers in HR context, and a three-way disambiguation — Hope Kaplan (person) / "I hope" (sentiment) / Summer (season) — in one message.

**Markdown fixtures** (`team-handbook.md`, `incident-postmortem.md`) cover:
- Bios with employer names that must be redacted (Meridian Bank, Steward Healthcare)
- Adversarial glossary: "Bill Nguyen's payments module handles all bill payment retries", "Max Schultz monitors throughput … when load reaches max utilization", "Angel Reyes manages … angel-investor reporting" — two new disambiguation pairs: **Angel** vs. "angel investor" and **Max** vs. "max throughput"
- Stripe token redacted alongside preserved incident ID
- Action items block with Chase/Grant/Mark/Faith each paired with a same-word verb in the same numbered list

---

## Known limitations
- **Pronouns not resolved** — co-referential pronouns (`he`, `she`, `his`) are left in place after a name is redacted
- **First-name-only references** — two failure modes in opposite directions: (1) a standalone first name like `"Jared"` gets a separate placeholder from `"Jared Barrera"` because the registry has no way to link them without seeing the full name nearby; (2) if two people share a first name (e.g. two people named Dana), a standalone `"Dana"` could be incorrectly merged with the wrong full name, producing a false link rather than a missed one
- **Credential strings** — `Amy Powell, MD, FACP` leaves credentials in place, which could narrow identity in small professional communities
- **Attribute re-identification** — span-based redaction removes explicit identifiers but has no concept of quasi-identifiers; a combination of age + title + employer + specialty can still uniquely identify someone even with the name removed. The LLM re-identification judge probes for this but doesn't guarantee detection
- **Username aliasing requires a profile** — if a username (e.g. `will.harper`) appears in a file where no matching user profile exists in the input directory, it won't be linked to the full name
- **No OCR** — text inside PDF images is not extracted

## What I'd do next
- **Coreference resolution** — replace co-referential pronouns with the same placeholder as the redacted name
- **First-name resolution** — better handling of standalone first names: link them to the right full-name entity when context is clear, avoid linking when there's ambiguity (e.g. two people named Dana)
- **Quasi-identifier analysis** — after redaction, check whether remaining attribute clusters (age + role + employer + specialty) are uniquely identifying even without the name; flag documents that fail a k-anonymity threshold
- **Address detection** — integrate `pyap` or libpostal for reliable structured address detection
- **NER as a pre-filter** — run a local NER model (spaCy, GLiNER) cheaply to gate which messages go to the LLM, reducing API cost at scale
- **Batch LLM calls** — send multiple messages per API call to reduce latency and cost
- **Confidence scores** — per-detection confidence so a reviewer can prioritize spot-checks
- **More file formats** — DOCX, CSV, HTML Slack exports
- **International ID formats** — SSN/tax ID equivalents for non-US documents
