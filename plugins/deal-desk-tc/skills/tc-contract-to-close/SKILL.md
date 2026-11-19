---
name: tc-contract-to-close
description: Use after a contract is executed: tracks the file from contract to close from the confirmed table and reports only what changed or is due within 3 days, with a suggested next form.
---

# tc-contract-to-close

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** A quiet, accurate watch on the file. Reference model: lib/dealdesk_tc/contract_to_close.py.

**Trigger.** An executed contract, or the agent's routine check on a file.

## Steps

1. Source: if Tracker is installed, read its confirmed table (read-only). Otherwise accept an uploaded contract (extract it with the Tracker rules and have the agent confirm) or a confirmed table the agent pastes. No table at all: ask.
2. Track: deposit and receipt, loan application, appraisal ordered and back, inspections inside the period, inspection response sent and answered, title has the contract, curative items, repairs and receipts, walkthrough, Closing Disclosure, act of sale, recorded act, and after closing the compliance file.
3. Each check reports only what changed since last time or is due within 3 days (overdue counts). Done items are left out. Unconfirmed rows are listed as not tracked.
4. Suggest the next form when a date is at risk (for example the extension of agreement). A suggestion only.
5. Stay quiet when nothing changed and nothing is due.

## Stop rules

- Never move a date. Never write to the table. Never place calendar events; Tracker or the review gate does that.
- If a date looks wrong, do not fix it. Send Tracker a change request. It arrives as a proposed diff that goes through the gate.
- Never treat an unconfirmed date as official.
