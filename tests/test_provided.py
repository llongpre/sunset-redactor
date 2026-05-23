"""
End-to-end tests against the provided sample files.
The pipeline runs once per session (see conftest.py); tests load from pre-generated outputs.
"""
import json
from pathlib import Path

from tests.helpers import msg_out, page_out

_INPUT = Path("tests/data/provided/inputs")
_OUTPUT = Path("tests/data/provided/outputs")
_PDF_STEM = "kindlymd_investor_presentation_management"


def _msg_out(json_file: str, contains: str) -> str:
    return msg_out(_INPUT, _OUTPUT, json_file, contains)

def _page_out(page_num: int) -> str:
    return page_out(_OUTPUT, _PDF_STEM, page_num)


# ---------------------------------------------------------------------------
# Grace: person name vs. "grace period" vs. "say grace"
# ---------------------------------------------------------------------------

def test_grace_and_grace_period_in_same_message(pipeline_outputs):
    out = _msg_out("data-science_2024-06-12.json", "grace period cohort")
    assert "Grace Liu" not in out
    assert "grace period" in out

def test_grace_as_blessing_in_same_message(pipeline_outputs):
    out = _msg_out("people-launch_2026-04-10.json", "say grace before")
    assert "Grace Liu" not in out
    assert "say grace" in out

def test_grace_and_grace_period_section_with_multiple_people(pipeline_outputs):
    out = _msg_out("architecture_2023-01-10.json", "grace period section")
    assert "Grace Liu" not in out
    assert "Mark Rivera" not in out
    assert "grace period" in out


# ---------------------------------------------------------------------------
# May: person name vs. month vs. modal verb
# ---------------------------------------------------------------------------

def test_may_person_month_and_modal_in_same_message(pipeline_outputs):
    out = _msg_out("architecture_2023-01-10.json", "launch milestone from May")
    assert "May Chen" not in out
    assert "from May to June" in out

def test_may_person_and_may_modal_verb(pipeline_outputs):
    out = _msg_out("people-launch_2026-04-10.json", "may invite Renee")
    assert "May Chen" not in out
    assert "rcho@bioverse.example" not in out


# ---------------------------------------------------------------------------
# Chase: person name vs. verb vs. "Chase Bank"
# ---------------------------------------------------------------------------

def test_chase_person_verb_and_org_in_same_message(pipeline_outputs):
    out = _msg_out("banking-bots_2024-11-07.json", "chase the vendor")
    assert "Chase Kim" not in out
    assert "chase the vendor" in out
    assert "Chase Bank" in out

def test_chase_person_and_verb_in_architecture(pipeline_outputs):
    out = _msg_out("architecture_2023-01-10.json", "chase the webhook owner")
    assert "Chase Kim" not in out
    assert "chase the webhook owner" in out

def test_grace_and_chase_bank_in_same_message(pipeline_outputs):
    out = _msg_out("banking-bots_2024-11-07.json", "Chase Bank bill pay")
    assert "Grace Liu" not in out
    assert "grace period" in out
    assert "Chase Bank" in out


# ---------------------------------------------------------------------------
# Bill: person name vs. "bill payment"
# ---------------------------------------------------------------------------

def test_bill_person_and_bill_payment_with_financial_identifiers(pipeline_outputs):
    out = _msg_out("banking-bots_2024-11-07.json", "Bill payment retries should use account")
    assert "Bill Nguyen" not in out
    assert "Bill payment" in out
    assert "987654321" not in out
    assert "021000021" not in out

def test_bill_payment_in_bot_message_not_redacted(pipeline_outputs):
    out = _msg_out("banking-bots_2024-11-07.json", "Bill payment registration error - bill payment failed")
    assert "Bill payment" in out
    assert "bill payment" in out

def test_bill_person_and_bill_payment_explicit(pipeline_outputs):
    out = _msg_out("architecture_2023-01-10.json", "Bill is a person in my name")
    assert "Bill Nguyen" not in out
    assert "bill payment" in out


# ---------------------------------------------------------------------------
# Rose: person name vs. past tense of "rise"
# ---------------------------------------------------------------------------

def test_rose_person_and_rose_verb_in_same_message(pipeline_outputs):
    out = _msg_out("data-science_2024-06-12.json", "metric rose because")
    assert "Rose Patel" not in out
    assert "metric rose" in out

def test_rose_person_and_signups_rose(pipeline_outputs):
    out = _msg_out("people-launch_2026-04-10.json", "signups rose after")
    assert "Rose Patel" not in out
    assert "Sam Lee" not in out
    assert "signups rose" in out

def test_conversion_rose_in_may_message(pipeline_outputs):
    out = _msg_out("data-science_2024-06-12.json", "Conversion rose 4.2%")
    assert "rose" in out
    assert "May Chen" not in out


# ---------------------------------------------------------------------------
# Grant: person name vs. "grant permission"
# ---------------------------------------------------------------------------

def test_grant_person_and_grant_verb_same_sentence(pipeline_outputs):
    out = _msg_out("people-launch_2026-04-10.json", "will grant permission")
    assert "Grant Lee" not in out
    assert "grant permission" in out

def test_grant_person_and_grant_funded(pipeline_outputs):
    out = _msg_out("data-science_2024-06-12.json", "grant-funded users should stay")
    assert "Grant Lee" not in out
    assert "grant-funded" in out


# ---------------------------------------------------------------------------
# Hope: person name vs. sentiment
# ---------------------------------------------------------------------------

def test_hope_person_and_hope_sentiment_same_message(pipeline_outputs):
    out = _msg_out("data-science_2024-06-12.json", "turn hope into a person placeholder")
    assert "Hope Kaplan" not in out
    assert "I hope" in out

def test_hope_person_and_quoted_hope(pipeline_outputs):
    out = _msg_out("people-launch_2026-04-10.json", "hope this helps")
    assert "Hope Kaplan" not in out
    assert "hope this helps" in out


# ---------------------------------------------------------------------------
# Faith: person name vs. idiom
# ---------------------------------------------------------------------------

def test_faith_person_and_keep_faith_idiom(pipeline_outputs):
    out = _msg_out("architecture_2023-01-10.json", "Keep faith with the rollback")
    assert "Faith Morgan" not in out
    assert "Keep faith" in out


# ---------------------------------------------------------------------------
# Mark: person name vs. verb
# ---------------------------------------------------------------------------

def test_mark_person_and_mark_verb_same_message(pipeline_outputs):
    out = _msg_out("architecture_2023-01-10.json", "mark the migration task as blocked")
    assert "Mark Rivera" not in out
    assert "mark the migration" in out


# ---------------------------------------------------------------------------
# Summer: looks like a name but is a season
# ---------------------------------------------------------------------------

def test_summer_as_season_not_redacted(pipeline_outputs):
    out = _msg_out("architecture_2023-01-10.json", "Summer is not a teammate")
    assert "Summer" in out


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def test_may_as_month_in_pdf_title(pipeline_outputs):
    out = _page_out(1)
    assert "May 21, 2024" in out

def test_executive_bio_page_names_and_ages_redacted(pipeline_outputs):
    out = _page_out(18)
    assert "Adam Cox" not in out
    assert "Christian Robinson" not in out
    assert "Amy Powell" not in out
    assert "Jared Barrera" not in out
    assert "age 55" not in out
    assert "age 50" not in out
    assert ", 47," not in out
    assert ", 43," not in out


# ---------------------------------------------------------------------------
# Cross-file consistency: same person → same placeholder across files
# ---------------------------------------------------------------------------

def test_will_harper_same_placeholder_across_files(pipeline_outputs):
    by_ph = json.loads((_OUTPUT / "evidence_by_placeholder.json").read_text())
    will_entry = next(
        (v for v in by_ph.values() if v["original_value"].lower() == "will harper"),
        None,
    )
    assert will_entry is not None, "Will Harper not found in evidence"
    files = {r["file"] for r in will_entry["redactions"]}
    assert len(files) > 1, f"Will Harper only appeared in one file: {files}"
