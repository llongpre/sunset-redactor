# Clearpath Financial — Internal Team Handbook

## About the Company

Clearpath Financial builds automated bill payment and lending tools for community banks.
Our core products include grace-period management, real-time ACH processing, and
angel-investor reporting dashboards.

---

## Team Bios

**Will Harper**, *Product Lead*
Will joined Clearpath from Pinnacle Payments, where he led the bill payment integration
team. He is based at our New York office: 245 Park Ave, New York, NY 10167.
Contact: will.harper@clearpath.example, +1 646-555-0142.

**Grace Liu**, *ML Engineer*, age 34
Grace built the churn-prediction model that flags borrowers likely to miss a payment.
Her analysis of the grace-period cohort showed that a 7-day grace period reduces late fees
by 22%. Grace joined us from Meridian Bank's data science group.

**Mark Rivera**, *Infrastructure Engineer*
Mark owns the deployment pipeline and on-call rotation. To escalate a live incident,
mark the Jira ticket SEV1 and page Mark Rivera directly.
Mark joined from Steward Healthcare's cloud infrastructure division.

**Angel Reyes**, *Partnerships Lead*, age 29
Angel manages relationships with angel investors and regional banks. Our angel-investor
reporting dashboard was built at Angel's request; Angel Reyes is the primary contact for
all angel-round due diligence and angel-investor update emails.

**Max Schultz**, *Platform Engineer*, age 32
Max Schultz monitors system throughput and capacity. When load approaches max utilization,
the auto-scaler pages Max Schultz at max.schultz@clearpath.example or +44 20 7946 0958.
Capacity alerts fire at 80% of max throughput; Max reviews them every morning.

**Bill Nguyen**, *Payments Engineer*
Bill owns the ACH retry logic and the bill payment module. When a bill payment fails,
the system logs an event in Bill's queue. Bill Nguyen can be reached at
bill.nguyen@clearpath.example.

---

## Product Glossary

**bill payment** — the core transaction type. A bill payment initiates an ACH debit from
the customer's linked account. Note: Bill Nguyen's payments module handles all bill payment retries and reconciliations. Do not confuse "Bill" in product logs with the engineer.

**grace period** — a configurable window after a due date during which no late fee accrues.
Grace Liu's cohort research showed that shortening the grace period below 5 days increases
churn. The default grace period is 7 days and is configurable per product tier.

**angel round** — early-stage equity funding from angel investors. Angel Reyes coordinates
all angel-round communications, diligence requests, and angel-investor update reports.

**max throughput** — the peak transaction rate the platform can sustain. Alerts fire when
the platform exceeds 80% of max capacity. Do not confuse max throughput metrics with
Max Schultz's weekly capacity review reports.

---

## IT Access Policy

To request production access, open a Jira ticket tagged for Grant Lee. Grant Lee will
review the request and grant the minimum permissions required. Do not grant broad access
without documented justification; Grant Lee must approve any access beyond read-only.

To close an incident, mark the ticket resolved only after staging has been verified.
Do not mark a ticket closed while a rollback is still pending. Mark Rivera's runbook
describes the verification checklist in full.

---

## Contact Directory

| Name           | Email                             | Phone             |
|----------------|-----------------------------------|-------------------|
| Will Harper    | will.harper@clearpath.example     | +1 646-555-0142   |
| Grace Liu      | grace.liu@clearpath.example       | +1 646-555-0198   |
| Mark Rivera    | mark.rivera@clearpath.example     | +1 646-555-0231   |
| Bill Nguyen    | bill.nguyen@clearpath.example     | +1 646-555-0187   |
| Max Schultz    | max.schultz@clearpath.example     | +44 20 7946 0958  |
| HR inquiries   | hr@clearpath.example              | +1 646-555-0100   |
