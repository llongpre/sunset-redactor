# Post-Mortem: INC-2024-1209 — Stripe Token Exposure


**Severity:** SEV1
**Date:** 2024-12-09
**Incident commander:** [PERSON_4]
**Status:** Resolved

---

## Summary


A live Stripe secret key (`[API_TOKEN_1]`) was committed to the public repository
`clearpath/payments-sdk` and remained exposed for approximately 4 hours before detection.
[PERSON_4] led the response. The key was revoked, downstream callers were audited, and git
history was purged. Incident ID: INC-2024-1209.

---

## Timeline


| Time (UTC) | Actor        | Action                                                              |
|------------|--------------|---------------------------------------------------------------------|
| 08:14      | scanner      | Detected `[API_TOKEN_1]` in commit abc1234                 |
| 08:19      | PagerDuty    | Alert routed to [PERSON_4]                                           |
| 08:22      | [PERSON_4]    | Confirmed exposure; began to chase all downstream API callers       |
| 08:35      | [PERSON_6]  | Revoked key in Stripe; marked the Stripe webhook as disabled        |
| 08:41      | [PERSON_3]    | Granted emergency repo access to purge git history                 |
| 08:55      | [PERSON_5] | Logged SSN [SSN_1] found in a support ticket CC'd to the webhook|
| 09:03      | [PERSON_7]    | Confirmed no ML pipelines had ingested the exposed key             |
| 10:18      | [PERSON_4]    | Closed INC-2024-1209 after all remediations verified               |

---

## Technical Details


Scanner traffic originated from [IP_ADDRESS_1] and [IP_ADDRESS_2]. Both IPs are external and
do not match any Clearpath-owned range. Four authenticated API calls were made from
[IP_ADDRESS_1] using the exposed key between 08:14 and 08:35. Both IPs have been blocked at
the perimeter; see firewall rule FW-RULE-8842. Incident tracking ID: INC-2024-1209.

---

## Responder Contact Log


| Name          | Role                  | Contact                               |
|---------------|-----------------------|---------------------------------------|
| [PERSON_4]     | Incident commander    | [PHONE_1]                       |
| [PERSON_6]   | Token rotation        | [EMAIL_2]         |
| [PERSON_3]     | Repo access           | [EMAIL_3]           |
| [PERSON_5]  | Compliance lead       | [EMAIL_4]        |
| [PERSON_7]     | ML pipeline audit     | [EMAIL_5]           |

---

## Action Items


1. **[PERSON_4]** — chase all third-party vendors for confirmation of no secondary exposure.
2. **[PERSON_3]** — grant the security team read-only access to all public repos via policy update; do not grant write permissions without a second approval; grant the minimum viable scope only.
3. **[PERSON_6]** — mark the secrets-scanning CI step as required on all repos; mark this item complete once branch-protection rules are enforced in GitHub.
4. **[PERSON_5]** — verify the grace period for mandatory breach notification (72 hours under GDPR) has been satisfied; the 72-hour grace period clock started at first detection (08:14 UTC).

---

## What Went Well


- Automated scanner detected the exposure without human intervention.
- On-call rotation reached [PERSON_4] within 5 minutes of the alert.
- The grace period for affected merchant accounts was extended during remediation to
  prevent false late-fee accruals while the vault credentials were rotated.