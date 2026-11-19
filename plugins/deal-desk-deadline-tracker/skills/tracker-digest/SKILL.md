---
name: tracker-digest
description: Use each morning or on request to give the member a private digest of deadlines due today through three days out, flags, unconfirmed rows, and documents awaiting a deal match.
---

# tracker-digest

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** A short, member-only look-ahead. Reference model: lib/dealdesk_tracker/digest.py.

**Trigger.** The member's morning check, or "what's coming up".

## Steps

1. List every deadline from today through three days out, soonest first, with deal, date, time, and status.
2. List flags (holiday or weekend dates, set-on-delivery, unconfirmed periods) on rows not Done or Waived.
3. List rows still Extracted (not confirmed) and documents awaiting a deal match.
4. Only if the Transaction Coordinator plugin is installed: add draft client heads-up notes for confirmed items. They are drafts addressed to the member to review. The bot does not send them.
5. End with one question if something needs the agent's decision.

## Stop rules

- The digest goes to the member only. Never to a client, another agent, a lender, or a title company.
- No sending of any kind. Drafts are drafts.
- Do not present unconfirmed dates as official.
