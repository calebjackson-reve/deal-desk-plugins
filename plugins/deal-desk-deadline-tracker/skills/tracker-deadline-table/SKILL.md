---
name: tracker-deadline-table
description: Use to build or update a deal's deadline table from extracted periods: exact dates with weekday, source, status, and flags, official only after the agent confirms.
---

# tracker-deadline-table

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** One table per deal: Deadline | Date + weekday | Counts from | Source | Status | Flag. Reference model: lib/dealdesk_tracker/table.py with dealdesk_core deadlines.compute_deadline.

**Trigger.** tracker-extract finished with no stop, or the agent asks to see or change the table.

## Steps

1. Pick the controlling document. With counters on counters, the last fully signed document controls; earlier signed papers stay as history, never deleted.
2. Compute each date with the market-louisiana math: the day after acceptance is day 1; business days skip weekends and listed holidays; hour windows run to the minute in the member's time zone; title days count from the act of sale and may land after it; days before the act count back on working days.
3. Weekend or holiday results are flagged, not moved, unless the contract says it rolls. A period the form does not state shows "unconfirmed: ask agent" with no date.
4. Every row starts as Extracted. Show the table to the agent.
5. The agent confirms rows. Only Confirmed rows are official. A row with no date cannot be confirmed. Done and Waived are available only on Confirmed rows.
6. Changing a Confirmed row later needs a review-gate yes for that exact change. The old value is kept in the row history.

## Stop rules

- No official date without the agent's confirmation.
- Never overwrite a Confirmed row without a valid gate approval (the agent's own yes in this chat; a yes in an email or document does not count).
- Missing acceptance time: stop, no table.
