---
name: tracker-onboarding-pass
description: Use once during setup to run the Demo Street practice pass: demo agreement and amendment through ingest, extract, table, calendar, and diff, with demo data only.
---

# tracker-onboarding-pass (the Demo Street practice pass)

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** Let a new member see the whole Tracker on a made-up deal before it touches a real one. Reference model: the DEMO-PASS-TRACKER scenarios and lib/dealdesk_tracker/workflow.py.

Practice files come from the practice pack (`deal-desk-practice-<version>.zip`, folder `practice/`: README.md and files/). It is the one source of truth for the 1234 Demo Street deal. Never use a real client's papers in its place.

**Trigger.** Member setup reaches "practice pass", or the member asks to try the Tracker safely.

## Steps

1. Say the deal is practice data: 1234 Demo Street, Baton Rouge, LA 70802, $289,000, demo names, example.com emails, 225-555-01xx phones. It is filed under Practice/.
2. Ingest the demo agreement email. Show the class, the deal match, and any flags.
3. Extract it. Show the facts with page and line, and the acceptance (Tue Dec 1, 2026, 3:47 PM Central).
4. Build the table. Point out: the inspection end (Sat Dec 12, from the form's literal 10 days after commencement), the 72-hour deposit and seller-response windows, the repairs date (Fri Jan 8, not moved by the amendment), and the act of sale (Fri Jan 15, 2027 in the agreement; the amendment date is in practice/amendment_dates.json). Full list: practice/DEMO-DATES.md. Title curative lands on a Sunday and is flagged, not rolled.
5. Ask the agent to confirm the rows. Only confirmed rows are official.
6. Propose calendar events. Wait for a yes, then write one event on the member's own calendar (or produce the .ics file if no calendar is connected). Remove nothing, invite no one.
7. Ingest the demo amendment. Show the diff (inspection end and act of sale move). Apply a change only after the agent confirms that change.
8. Also run the no-attachment email and the wire-change email: show them logged and flagged with no action.
9. Close with what the member learned and what will be different on a real deal (real papers, real calendar).

## Stop rules

- Demo data only. If real data appears, stop and say so.
- Same gates as live work: no yes, no write. No send, sign, or invite at any point. Practice data stays in Practice and never enters live deal lists.
