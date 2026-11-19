# Deal Desk Deadline Tracker changelog

## 0.1.1 (Nov 19 2026, pending review)

- Practice pack and onboarding pass moved to 1234 Demo Street. Answer key is `practice/DEMO-DATES.md`. The amended Act of Sale date is isolated in `practice/amendment_dates.json`.
- Address short names for the practice deal now read "1234 Demo".

## 0.1.0

- Eight skills: ingest, extract, deadline table, calendar, amendment diff, files, digest, and the Pelican onboarding pass.
- Reference logic (stdlib only, no network): classify, extract, table, calendar events with ICS fallback, amendment diff, file plans, digest. Uses Shared core 0.1.0 for date math, deal matching, and the review gate.
- Pelican fixture emails (agreement and amendment) for the onboarding pass.
- 69 Q&A scenarios, including the end-to-end PELICAN-PASS-TRACKER and a scan that fails if any module gains send, sign, invite, network, or delete capability.
- No capability to send, sign, invite, or delete anywhere in the package.
- Nov 19 2026 text fix (no version change): the onboarding-pass skill now names the current Pelican dates (accepted Tue Nov 17, act of sale Fri Dec 18 after the amendment) instead of the old Sep 30 / Thanksgiving example.

## 0.0.1 (skeleton)

- Package skeleton and manifest only.
