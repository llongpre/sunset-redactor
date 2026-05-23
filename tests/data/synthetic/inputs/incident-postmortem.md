# Post-Mortem: INC-2024-1209 — Stripe Token Exposure

**Severity:** SEV1
**Date:** 2024-12-09
**Incident commander:** Chase Kim
**Status:** Resolved

---

## Summary

A live Stripe secret key (`sk_live_51H8demoToken`) was committed to the public repository
`clearpath/payments-sdk` and remained exposed for approximately 4 hours before detection.
Chase Kim led the response. The key was revoked, downstream callers were audited, and git
history was purged. Incident ID: INC-2024-1209.

---

## Timeline

| Time (UTC) | Actor        | Action                                                              |
|------------|--------------|---------------------------------------------------------------------|
| 08:14      | scanner      | Detected `sk_live_51H8demoToken` in commit abc1234                 |
| 08:19      | PagerDuty    | Alert routed to Chase Kim                                           |
| 08:22      | Chase Kim    | Confirmed exposure; began to chase all downstream API callers       |
| 08:35      | Mark Rivera  | Revoked key in Stripe; marked the Stripe webhook as disabled        |
| 08:41      | Grant Lee    | Granted emergency repo access to purge git history                 |
| 08:55      | Faith Morgan | Logged SSN 123-45-6789 found in a support ticket CC'd to the webhook|
| 09:03      | Grace Liu    | Confirmed no ML pipelines had ingested the exposed key             |
| 10:18      | Chase Kim    | Closed INC-2024-1209 after all remediations verified               |

---

## Technical Details

Scanner traffic originated from 10.24.18.77 and 192.168.4.12. Both IPs are external and
do not match any Clearpath-owned range. Four authenticated API calls were made from
10.24.18.77 using the exposed key between 08:14 and 08:35. Both IPs have been blocked at
the perimeter; see firewall rule FW-RULE-8842. Incident tracking ID: INC-2024-1209.

---

## Responder Contact Log

| Name          | Role                  | Contact                               |
|---------------|-----------------------|---------------------------------------|
| Chase Kim     | Incident commander    | +1 646-555-0142                       |
| Mark Rivera   | Token rotation        | mark.rivera@clearpath.example         |
| Grant Lee     | Repo access           | grant.lee@clearpath.example           |
| Faith Morgan  | Compliance lead       | faith.morgan@clearpath.example        |
| Grace Liu     | ML pipeline audit     | grace.liu@clearpath.example           |

---

## Action Items

1. **Chase Kim** — chase all third-party vendors for confirmation of no secondary exposure.
2. **Grant Lee** — grant the security team read-only access to all public repos via policy update; do not grant write permissions without a second approval; grant the minimum viable scope only.
3. **Mark Rivera** — mark the secrets-scanning CI step as required on all repos; mark this item complete once branch-protection rules are enforced in GitHub.
4. **Faith Morgan** — verify the grace period for mandatory breach notification (72 hours under GDPR) has been satisfied; the 72-hour grace period clock started at first detection (08:14 UTC).

---

## What Went Well

- Automated scanner detected the exposure without human intervention.
- On-call rotation reached Chase Kim within 5 minutes of the alert.
- The grace period for affected merchant accounts was extended during remediation to
  prevent false late-fee accruals while the vault credentials were rotated.
