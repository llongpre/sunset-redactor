# Redaction Pipeline — Design Decisions & Known Limitations

## How to run

**Requirements**
- Python 3.13
- An Anthropic API key (used for contextual name disambiguation)

**Setup**
```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key-here
```

**Run on the provided sample files**
```bash
python run.py
```

**Run on a custom folder**
```bash
python run.py path/to/folder/ path/to/outputs/
```

**Run tests**
```bash
pytest tests/
```

The e2e tests (`test_provided.py`, `test_synthetic.py`) run the full pipeline once per session before asserting on the outputs. Each run hits the LLM API (~30–60s). To skip re-running and assert against already-generated outputs:
```bash
pytest tests/ --use-existing
```

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
- System/incident identifiers (e.g. `INC-2024-1107`, `BILL_PAY_042`, `risk-8842`, `exp_2024_0612`) — not personal information

## PDF handling
- Output is plain text, not a reconstructed PDF
- Text inside images is not extracted (no OCR)

## What I'd do next
- **Coreference resolution** — after redacting a name, also replace co-referential pronouns (`he`, `she`, `his`) with the same placeholder
- **First-name-only cross-file matching** — improve deduplication when a person is referenced by first name only in one file and full name in another
- **Address detection** — integrate `pyap` or libpostal for reliable structured address detection in prose
- **OCR** — extract text from image-embedded PDF pages (currently skipped)
- **More file formats** — DOCX, CSV, HTML Slack exports
- **Batch LLM calls** — send multiple messages in one API call to reduce latency and cost
- **Confidence scores** — per-detection confidence score so a reviewer can prioritize spot-checks
- **Precision/recall eval** — annotate a small held-out set and measure detection quality per category instead of relying only on the scenario tests
- **NER as a pre-filter** — run a local NER model (spaCy, GLiNER) cheaply to find candidate person names, then pass only messages containing candidates to the LLM for disambiguation. This gives a real cost saving at scale: instead of sending every message to the LLM, only send the ones where a potential name was found. Off-the-shelf NER alone would fail on the ambiguous cases (it would flag "grace period" and "Chase Bank"), but as a cheap gating layer it's the natural next architecture
- **International ID formats** — SSN/tax ID equivalents for non-US documents

## Synthetic test fixtures

The test suite includes four synthetic fixture files in `tests/data/synthetic/` that extend coverage beyond the provided sample inputs.

**JSON fixtures** (`security-incidents_2024-09-05.json`, `hr-onboarding_2025-01-20.json`) fill gaps left by the provided Slack exports: IP addresses in bot alert messages alongside system identifiers that must survive (e.g. `INC-2024-0905`), UK and US phone numbers together in a single message, passport numbers in an HR/onboarding context, and a three-way disambiguation — Hope Kaplan (person) / "I hope" (sentiment) / Summer (season) — all appearing in one message.

**Markdown fixtures** (`team-handbook.md`, `incident-postmortem.md`) test redaction in document-shaped prose rather than chat messages.

- `team-handbook.md` is a fictional fintech company handbook. Its bio section embeds person names alongside employer names that must also be redacted (e.g. "Meridian Bank" and "Steward Healthcare" appearing in personal bios). The product glossary is deliberately adversarial: "Bill Nguyen's payments module handles all bill payment retries" puts a person name and the product term "bill payment" in the same sentence, as does "Max Schultz monitors throughput … when load reaches max utilization" and "Angel Reyes manages … angel-investor reporting." The last two introduce two new disambiguation pairs not covered anywhere in the provided data: **Angel** (person) vs. "angel investor" (finance term), and **Max** (person) vs. "max throughput / max utilization" (infrastructure term).

- `incident-postmortem.md` is a security incident write-up. It tests that a Stripe token in a narrative paragraph is redacted while the incident ID beside it is preserved, and that IPs in a technical-details section are redacted while a firewall rule ID (`FW-RULE-8842`) survives. The most demanding test is the action items block, which contains all four of Chase/Grant/Mark/Faith paired with a verb or phrase using the same word in the same numbered list — asserting that all four people are redacted while "chase all third-party", "grant the minimum viable scope", "mark the secrets-scanning CI step", and "grace period" are all preserved in a single `redact_text` call.

## Detector merge strategy
- Both regex and LLM run on every piece of text
- Results are merged and sorted by position; overlapping spans keep the longer match
- Deduplication happens via the entity registry: same value (case-insensitive) → same placeholder, regardless of which detector found it or in which file

## Known limitations
- **Pronouns not resolved** — after redacting a name, co-referential pronouns (`he`, `she`, `his`) are left in place
- **Contextual name/word ambiguity** — names that double as common words (Grace/grace period, Bill/billable, May/month, Chase/verb, Rose/verb, Hope/sentiment, Grant/grant-funded) will have some false positives/negatives
- **Credential strings** — names with credentials attached (`Amy Powell, MD, FACP`) leave credentials in place, which could narrow identity in small professional communities
- **Cross-file deduplication** — same person gets one placeholder across all files, but first-name-only references may get a different placeholder than the full name
