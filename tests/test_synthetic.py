"""
End-to-end scenario tests using synthetic fixture files.
The pipeline runs once per session (see conftest.py); tests load from pre-generated outputs.

JSON fixtures cover:
- IP address in a bot alert alongside a system incident ID that must survive
- UK + US phone numbers in the same message
- @here mention preserved alongside real PII
- Passport number in an HR/onboarding context
- SSN + passport + email together in a bot message
- Hope Kaplan (person) / "I hope" (verb) / Summer (season) all in one message
- Grant Lee (person) / "grant them access" (verb) in an onboarding message

Markdown fixtures cover:
- Bios with names, credentials, ages, and employer names in prose
- Glossary entries where the same word is a product term and a person name
- New disambiguation pairs: Angel/angel-investor, Max/max-throughput
- Contact tables with personal and org email addresses
- Incident post-mortem with tokens, IPs, firewall rule IDs, and action items that
  mix person names with verbs in the same numbered list
"""
from pathlib import Path

from tests.helpers import msg_out, md_block_out

_INPUT = Path("tests/data/synthetic/inputs")
_OUTPUT = Path("tests/data/synthetic/outputs")


def _msg_out(json_file: str, contains: str) -> str:
    return msg_out(_INPUT, _OUTPUT, json_file, contains)

def _md_block_out(md_file: str, contains: str) -> str:
    return md_block_out(_OUTPUT, md_file, contains)


# ---------------------------------------------------------------------------
# Security incidents fixture
# ---------------------------------------------------------------------------

def test_ip_in_incident_alert_redacted_system_id_preserved(synthetic_pipeline_outputs):
    out = _msg_out("security-incidents_2024-09-05.json", "INC-2024-0905")
    assert "10.24.18.77" not in out
    assert "INC-2024-0905" in out

def test_chase_person_and_verb_and_token_in_security_channel(synthetic_pipeline_outputs):
    out = _msg_out("security-incidents_2024-09-05.json", "chase the IP owner")
    assert "Chase Kim" not in out
    assert "chase the IP owner" in out
    assert "xoxb-1122-demo-token" not in out

def test_uk_and_us_phones_both_redacted_in_same_message(synthetic_pipeline_outputs):
    out = _msg_out("security-incidents_2024-09-05.json", "+44 20 7946 0958")
    assert "Faith Morgan" not in out
    assert "+44 20 7946 0958" not in out
    assert "+1 646-555-0142" not in out

def test_mark_verb_person_and_at_here_in_incident_message(synthetic_pipeline_outputs):
    out = _msg_out("security-incidents_2024-09-05.json", "mark the incident as SEV1")
    assert "Mark Rivera" not in out
    assert "Chase Kim" not in out
    assert "mark the incident" in out
    assert "@here" in out

def test_grace_period_policy_preserved_and_grace_person_redacted(synthetic_pipeline_outputs):
    out = _msg_out("security-incidents_2024-09-05.json", "grace period for expired tokens")
    assert "Grace Liu" not in out
    assert "grace period" in out


# ---------------------------------------------------------------------------
# HR onboarding fixture
# ---------------------------------------------------------------------------

def test_ssn_passport_and_email_in_hr_bot_message_all_redacted(synthetic_pipeline_outputs):
    out = _msg_out("hr-onboarding_2025-01-20.json", "I-9 verification complete")
    assert "123-45-6789" not in out
    assert "P9876543" not in out
    assert "hr@acmecorp.example" not in out

def test_passport_redacted_and_signups_rose_preserved(synthetic_pipeline_outputs):
    out = _msg_out("hr-onboarding_2025-01-20.json", "signups rose by four")
    assert "Rose Patel" not in out
    assert "P4319927" not in out
    assert "signups rose" in out

def test_hope_person_redacted_hope_verb_and_summer_season_both_preserved(synthetic_pipeline_outputs):
    out = _msg_out("hr-onboarding_2025-01-20.json", "summer intern paperwork")
    assert "Hope Kaplan" not in out
    assert "I hope" in out
    assert "Summer" in out

def test_grant_person_redacted_grant_access_preserved(synthetic_pipeline_outputs):
    out = _msg_out("hr-onboarding_2025-01-20.json", "grant them system access")
    assert "Grant Lee" not in out
    assert "grant them system access" in out


# ---------------------------------------------------------------------------
# team-handbook.md
# ---------------------------------------------------------------------------

def test_angel_person_redacted_angel_investor_preserved(synthetic_pipeline_outputs):
    out = _md_block_out("team-handbook.md", "angel-investor reporting dashboard")
    assert "Angel Reyes" not in out
    assert "angel-investor" in out

def test_max_person_redacted_max_utilization_preserved(synthetic_pipeline_outputs):
    out = _md_block_out("team-handbook.md", "max utilization")
    assert "Max Schultz" not in out
    assert "max utilization" in out

def test_grace_bio_person_redacted_grace_period_and_employer_redacted(synthetic_pipeline_outputs):
    out = _md_block_out("team-handbook.md", "grace-period cohort")
    assert "Grace Liu" not in out
    assert "Meridian Bank" not in out
    assert "grace period" in out

def test_employer_in_mark_bio_is_redacted(synthetic_pipeline_outputs):
    out = _md_block_out("team-handbook.md", "cloud infrastructure division")
    assert "Steward Healthcare" not in out
    assert "Mark Rivera" not in out

def test_bill_payment_glossary_person_and_term_distinguished(synthetic_pipeline_outputs):
    out = _md_block_out("team-handbook.md", "bill payment retries")
    assert "Bill Nguyen" not in out
    assert "bill payment" in out

def test_grant_policy_person_and_verb_in_handbook(synthetic_pipeline_outputs):
    out = _md_block_out("team-handbook.md", "grant the minimum permissions")
    assert "Grant Lee" not in out
    assert "grant the minimum permissions" in out

def test_mark_policy_person_and_verb_in_handbook(synthetic_pipeline_outputs):
    out = _md_block_out("team-handbook.md", "mark the ticket resolved")
    assert "Mark Rivera" not in out
    assert "mark the ticket resolved" in out

def test_contact_table_all_emails_and_phones_redacted(synthetic_pipeline_outputs):
    out = _md_block_out("team-handbook.md", "Contact Directory")
    assert "will.harper@clearpath.example" not in out
    assert "grace.liu@clearpath.example" not in out
    assert "hr@clearpath.example" not in out
    assert "+1 646-555-0142" not in out
    assert "+44 20 7946 0958" not in out


# ---------------------------------------------------------------------------
# incident-postmortem.md
# ---------------------------------------------------------------------------

def test_token_redacted_incident_id_preserved_in_postmortem(synthetic_pipeline_outputs):
    out = _md_block_out("incident-postmortem.md", "INC-2024-1209")
    assert "sk_live_51H8demoToken" not in out
    assert "INC-2024-1209" in out

def test_ips_redacted_firewall_rule_id_preserved(synthetic_pipeline_outputs):
    out = _md_block_out("incident-postmortem.md", "FW-RULE-8842")
    assert "10.24.18.77" not in out
    assert "192.168.4.12" not in out
    assert "FW-RULE-8842" in out
    assert "INC-2024-1209" in out

def test_ssn_in_timeline_redacted(synthetic_pipeline_outputs):
    out = _md_block_out("incident-postmortem.md", "Logged SSN")
    assert "123-45-6789" not in out

def test_chase_timeline_person_and_verb(synthetic_pipeline_outputs):
    out = _md_block_out("incident-postmortem.md", "chase all downstream")
    assert "Chase Kim" not in out
    assert "chase all downstream" in out

def test_action_items_all_persons_redacted_all_verbs_preserved(synthetic_pipeline_outputs):
    out = _md_block_out("incident-postmortem.md", "grant the minimum viable scope")
    assert "Chase Kim" not in out
    assert "Grant Lee" not in out
    assert "Mark Rivera" not in out
    assert "Faith Morgan" not in out
    assert "chase all third-party" in out
    assert "grant the minimum viable scope" in out
    assert "mark the secrets-scanning" in out
    assert "grace period" in out
