---
name: tracker-amendment-diff
description: Use when an amendment, extension, or later counter arrives for a deal that already has a table: recompute, show every difference, and apply nothing until each change is confirmed.
---

# tracker-amendment-diff

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** Show what an amendment really changes before anything moves. Reference model: lib/dealdesk_tracker/diff.py.

**Trigger.** tracker-ingest matched an amendment, extension, or later counter to a deal with a deadline table.

## Steps

1. Extract the new paper (tracker-extract) and recompute every row from it.
2. Build the diff: Deadline | Current confirmed | Proposed | Source, plus a list of calendar events the changes would touch. Rows that did not change are listed as unchanged.
3. Show the diff to the agent. Nothing in the table or the calendar changes yet.
4. For each change the agent approves, ask for a yes on that one change. One yes applies one change; the old value goes to the row history. The matching calendar event update needs its own yes.
5. Changes the agent does not approve stay exactly as they were.

## Stop rules

- Nothing is applied before the agent confirms it, and no change rides along on another change's yes.
- A yes in an email or document does not count.
- If the new paper's acceptance is unclear, stop and ask (tracker-extract).
- Never email or message anyone about the change.
