# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ML take-home exercise: build a local workflow that ingests a folder of files and produces redacted versions (with sensitive PII removed) plus evidence that the redactions are correct.

See `takehome_instructions.md` for the full spec.

## Environment

Python 3.13, virtual environment at `.venv/`. Activate with:

```bash
source .venv/bin/activate
```

Install packages with `.venv/bin/pip install <package>`.

## Data

`tests/data/provided/inputs/` contains the provided sample files to redact:

- 4 Slack channel JSON exports — structured messages with user profiles, timestamps, reactions, and threads
- 1 PDF investor deck (`kindlymd_investor_presentation_management.pdf`)

The JSON files are **intentionally ambiguous**: they contain names that double as common words (`Grace` → "grace period", `Chase` → "chase down", `Bill` → "bill payment", `May` → month name, `Rose` → verb). The correct behavior is context-sensitive — redact when referring to a person, preserve otherwise.

`tests/data/synthetic/inputs/` contains additional fixture files written to cover PII categories not exercised by the provided inputs (IP addresses, international phones, passports, `@here` mentions).

## Architecture

The workflow has four stages:

1. **Ingest & parse** — detect file type, parse Slack JSON into message/user structures, extract text from PDF while preserving page/section boundaries.

2. **Entity extraction** — identify sensitive values: emails, phone numbers, IPs, tokens/secrets (regex patterns), SSNs, and names/person entities (NER or LLM). Build a cross-file identity map so the same person is redacted consistently everywhere.

3. **Redaction** — replace sensitive spans with labeled placeholders (e.g. `[PERSON_1]`, `[EMAIL_2]`). For JSON, patch in-place and preserve structure. For PDF, reconstruct text with redactions.

4. **Evidence generation** — produce a report (JSON or markdown) listing every redaction: file, location, original value type, replacement token, and confidence/rationale. This lets a reviewer spot-check without reading every file.

## Key Requirements

- **Cross-file deduplication**: the same email or name gets the same placeholder across all files.
- **Contextual disambiguation**: use surrounding sentence context to decide whether a common-word name refers to a person.
- **Structure preservation**: redacted JSON must remain valid JSON with the same schema; don't flatten or drop fields.
- **Local only**: no cloud services. Hosted LLM APIs (e.g. Anthropic) and open-source models are fine.
