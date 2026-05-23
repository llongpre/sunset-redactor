# Clearpath Financial — Internal Team Handbook

## About the Company


Clearpath Financial builds automated bill payment and lending tools for community banks.
Our core products include grace-period management, real-time ACH processing, and
angel-investor reporting dashboards.

---

## Team Bios


**[PERSON_8]**, *Product Lead*
Will joined Clearpath from [PERSON_9], where he led the bill payment integration
team. He is based at our New York office: [ADDRESS_1].
Contact: [EMAIL_6], [PHONE_1].

**[PERSON_7]**, *ML Engineer*, [AGE_1]
Grace built the churn-prediction model that flags borrowers likely to miss a payment.
Her analysis of the grace-period cohort showed that a 7-day grace period reduces late fees
by 22%. Grace joined us from [PERSON_10]'s data science group.

**[PERSON_6]**, *Infrastructure Engineer*
Mark owns the deployment pipeline and on-call rotation. To escalate a live incident,
mark the Jira ticket SEV1 and page [PERSON_6] directly.
Mark joined from [PERSON_11]'s cloud infrastructure division.

**[PERSON_12]**, *Partnerships Lead*, [AGE_2]
Angel manages relationships with angel investors and regional banks. Our angel-investor
reporting dashboard was built at Angel's request; [PERSON_12] is the primary contact for
all angel-round due diligence and angel-investor update emails.

**[PERSON_13]**, *Platform Engineer*, [AGE_3]
[PERSON_13] monitors system throughput and capacity. When load approaches max utilization,
the auto-scaler pages [PERSON_13] at [EMAIL_7] or [PHONE_2].
Capacity alerts fire at 80% of max throughput; Max reviews them every morning.

**[PERSON_14]**, *Payments Engineer*
Bill owns the ACH retry logic and the bill payment module. When a bill payment fails,
the system logs an event in Bill's queue. [PERSON_14] can be reached at
[EMAIL_8].

---

## Product Glossary


**bill payment** — the core transaction type. A bill payment initiates an ACH debit from
the customer's linked account. Note: [PERSON_14]'s payments module handles all bill payment retries and reconciliations. Do not confuse "Bill" in product logs with the engineer.

**grace period** — a configurable window after a due date during which no late fee accrues.
[PERSON_7]'s cohort research showed that shortening the grace period below 5 days increases
churn. The default grace period is 7 days and is configurable per product tier.

**angel round** — early-stage equity funding from angel investors. [PERSON_12] coordinates
all angel-round communications, diligence requests, and angel-investor update reports.

**max throughput** — the peak transaction rate the platform can sustain. Alerts fire when
the platform exceeds 80% of max capacity. Do not confuse max throughput metrics with
[PERSON_13]'s weekly capacity review reports.

---

## IT Access Policy


To request production access, open a Jira ticket tagged for [PERSON_3]. [PERSON_3] will
review the request and grant the minimum permissions required. Do not grant broad access
without documented justification; [PERSON_3] must approve any access beyond read-only.

To close an incident, mark the ticket resolved only after staging has been verified.
Do not mark a ticket closed while a rollback is still pending. [PERSON_6]'s runbook
describes the verification checklist in full.

---

## Contact Directory


| Name           | Email                             | Phone             |
|----------------|-----------------------------------|-------------------|
| [PERSON_8]    | [EMAIL_6]     | [PHONE_1]   |
| [PERSON_7]      | [EMAIL_5]       | [PHONE_3]   |
| [PERSON_6]    | [EMAIL_2]     | [PHONE_4]   |
| [PERSON_14]    | [EMAIL_8]     | [PHONE_5]   |
| [PERSON_13]    | [EMAIL_7]     | [PHONE_2]  |
| HR inquiries   | [EMAIL_9]              | [PHONE_6]   |