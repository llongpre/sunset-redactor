"""
Unit-style scenario tests. Each test defines its own input text and asserts
a single, specific redaction behavior. Exhaustive coverage of every PII
category and disambiguation case we intend to handle.
"""
from redactor.pipeline import redact_text


# ---------------------------------------------------------------------------
# Emails
# ---------------------------------------------------------------------------

def test_personal_email_is_redacted():
    assert "ari.mendoza@bioverse.example" not in redact_text("contact ari.mendoza@bioverse.example for access")

def test_org_email_is_redacted():
    assert "investors@kindlymd.com" not in redact_text("email investors@kindlymd.com for questions")

def test_org_email_with_subdomain_is_redacted():
    assert "info@wallachbeth.com" not in redact_text("reach the syndicate at info@wallachbeth.com")

def test_email_with_plus_addressing_is_redacted():
    assert "user+tag@example.com" not in redact_text("forwarded to user+tag@example.com")

def test_multiple_emails_in_one_string_all_redacted():
    out = redact_text("cc ari.mendoza@bioverse.example and rcho@bioverse.example on this")
    assert "ari.mendoza@bioverse.example" not in out
    assert "rcho@bioverse.example" not in out

def test_email_at_end_of_sentence_is_redacted():
    assert "user@domain.com" not in redact_text("send it to user@domain.com.")

def test_non_email_at_symbol_not_redacted():
    assert "@here" in redact_text("ping @here for a response")


# ---------------------------------------------------------------------------
# Phone numbers
# ---------------------------------------------------------------------------

def test_us_phone_is_redacted():
    assert "+1 646-555-0142" not in redact_text("call +1 646-555-0142 to confirm")

def test_uk_phone_is_redacted():
    assert "+44 20 7946 0958" not in redact_text("reach her at +44 20 7946 0958")


# ---------------------------------------------------------------------------
# Financial identifiers
# ---------------------------------------------------------------------------

def test_ssn_is_redacted():
    assert "123-45-6789" not in redact_text("SSN 123-45-6789 was found in the payload")

def test_tax_id_is_redacted():
    assert "12-3456789" not in redact_text("tax id 12-3456789 on file")

def test_credit_card_is_redacted():
    assert "4242 4242 4242 4242" not in redact_text("card 4242 4242 4242 4242 pasted in ticket")

def test_bank_account_is_redacted():
    assert "987654321" not in redact_text("use account 987654321 for retries")

def test_routing_number_is_redacted():
    assert "021000021" not in redact_text("routing number is 021000021")


# ---------------------------------------------------------------------------
# Secrets and tokens
# ---------------------------------------------------------------------------

def test_slack_token_is_redacted():
    assert "xoxb-1122-demo-token" not in redact_text("token xoxb-1122-demo-token was exposed")

def test_stripe_key_is_redacted():
    assert "sk_live_51H8demoToken" not in redact_text("rotate sk_live_51H8demoToken immediately")


# ---------------------------------------------------------------------------
# Network identifiers
# ---------------------------------------------------------------------------

def test_ip_address_is_redacted():
    assert "10.24.18.77" not in redact_text("node IP 10.24.18.77 is in the notes")


# ---------------------------------------------------------------------------
# Government identifiers
# ---------------------------------------------------------------------------

def test_passport_is_redacted():
    assert "P4319927" not in redact_text("passport P4319927 found in screenshot")


# ---------------------------------------------------------------------------
# Ages
# ---------------------------------------------------------------------------

def test_age_with_label_is_redacted():
    assert "age 46" not in redact_text("Tim Pickett, MPAS-C, age 46, is the founder")

def test_age_bare_after_credentials_is_redacted():
    assert ", 43," not in redact_text("Jared Barrera, MBA, 43, became CFO")


# ---------------------------------------------------------------------------
# Physical addresses
# ---------------------------------------------------------------------------

def test_physical_address_is_redacted():
    assert "245 Park Ave" not in redact_text("meet at 245 Park Ave, New York, NY 10167 on Friday")


# ---------------------------------------------------------------------------
# Slack structural fields
# ---------------------------------------------------------------------------

def test_slack_user_id_is_redacted():
    assert "U05BILL" not in redact_text("user U05BILL sent the message")

def test_avatar_hash_is_redacted():
    assert "h_u05bill" not in redact_text("avatar_hash is h_u05bill")


# ---------------------------------------------------------------------------
# Contextual name disambiguation
# ---------------------------------------------------------------------------

def test_grace_as_person_is_redacted():
    assert "Grace Liu" not in redact_text("Grace Liu reviewed the numbers.")

def test_grace_period_is_preserved():
    assert "grace period" in redact_text("the grace period should stay at 7 days")

def test_bill_as_person_is_redacted():
    assert "Bill Nguyen" not in redact_text("Bill Nguyen reproduced the issue.")

def test_bill_payment_is_preserved():
    assert "bill payment" in redact_text("bill payment retries failed for 128 users")

def test_may_as_person_is_redacted():
    assert "May Chen" not in redact_text("May Chen posted the analysis.")

def test_may_as_month_is_preserved():
    assert "May" in redact_text("the milestone moved from May to June")

def test_chase_as_person_is_redacted():
    assert "Chase Kim" not in redact_text("Chase Kim will own the webhook migration.")

def test_chase_as_verb_is_preserved():
    assert "chase the owner" in redact_text("someone should chase the owner for a response")

def test_chase_bank_as_org_is_preserved():
    assert "Chase Bank" in redact_text("Chase Bank referral traffic was up 12%")

def test_rose_as_person_is_redacted():
    assert "Rose Patel" not in redact_text("Rose Patel checked the dashboard.")

def test_rose_as_verb_is_preserved():
    assert "rose" in redact_text("error volume rose 18% after the deploy")

def test_hope_as_person_is_redacted():
    assert "Hope Kaplan" not in redact_text("Hope Kaplan mocked up the page.")

def test_hope_as_sentiment_is_preserved():
    assert "hope" in redact_text("I hope the labels stay readable")

def test_grant_as_person_is_redacted():
    assert "Grant Lee" not in redact_text("Grant Lee approved the plan.")

def test_grant_as_verb_is_preserved():
    assert "grant permission" in redact_text("grant permission to the service account")

def test_grant_funded_is_preserved():
    assert "grant-funded" in redact_text("grant-funded users should stay a segment label")

def test_faith_as_person_is_redacted():
    assert "Faith Morgan" not in redact_text("Faith Morgan signed off on the wording.")

def test_faith_as_idiom_is_preserved():
    assert "Keep faith" in redact_text("Keep faith with the rollback plan.")

def test_mark_as_person_is_redacted():
    assert "Mark Rivera" not in redact_text("Mark Rivera owns the migration.")

def test_mark_as_verb_is_preserved():
    assert "mark the task" in redact_text("I will mark the task as blocked")

def test_summer_as_non_person_is_preserved():
    assert "Summer" in redact_text("Summer traffic is higher due to seasonality.")


# ---------------------------------------------------------------------------
# PDF-specific
# ---------------------------------------------------------------------------

def test_name_with_credentials_is_redacted():
    assert "Amy Powell" not in redact_text("Amy Powell, MD, FACP, FAMSSM, age 50, is a Professor")

def test_name_that_is_also_adjective_is_redacted():
    assert "Christian Robinson" not in redact_text("Christian Robinson, CPA, age 55, is the Corporate Controller")


# ---------------------------------------------------------------------------
# Employer names in bios
# ---------------------------------------------------------------------------

def test_employer_in_bio_is_redacted():
    assert "Steward Healthcare" not in redact_text(
        "Adam Cox, 47, stood out as Steward Healthcare's go-to expert for critical operations."
    )

def test_employer_in_general_prose_is_preserved():
    assert "Steward Healthcare" in redact_text(
        "Steward Healthcare is one of the largest private hospital operators in the US."
    )


# ---------------------------------------------------------------------------
# Known limitations — explicitly documented failures
# ---------------------------------------------------------------------------

def test_pronouns_after_redacted_name_are_not_resolved():
    out = redact_text("Adam Cox, 47, is a seasoned leader. He stood out as a go-to expert.")
    assert "Adam Cox" not in out
    assert "He" in out  # known gap: coreference resolution is out of scope
