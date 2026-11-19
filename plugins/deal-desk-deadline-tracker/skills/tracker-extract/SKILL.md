---
name: tracker-extract
description: Use after a contract document is matched to a deal: pull parties, address, price, financing, acceptance, and every period with its page and line, marking anything absent as missing.
---

# tracker-extract

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** Turn a matched contract into plain facts with their source. Reference model: lib/dealdesk_tracker/extract.py.

**Trigger.** A document that tracker-ingest classified as a contract and matched (or the agent matched by hand).

## Steps

1. Check the form against the member's form list (market-louisiana). If the form is not on the list, or its version date differs from the member's current version, flag it and tell the agent. Keep going only if the agent says so.
2. Pull: buyers, sellers, other agent, lender, title company (name, email, phone), property address, parish, price, financing type, side, act of sale date.
3. Pull acceptance: the date and time the last required signature landed, and whether the document is fully signed. If acceptance is unclear (no time, not fully signed, signatures out of order), stop and ask. Do not compute anything.
4. Pull each period: what it is, how many, what unit (calendar days, business days, hours, event, title days, days before act), what it counts from, and the page and line it came from.
5. Anything not on the paper is written "missing". Never guess, never fill from memory or from a similar deal.
6. Pass the result to tracker-deadline-table.

## Stop rules

- Unclear acceptance: stop. No deadlines until the agent settles it.
- A period with no stated count is "missing", not an assumed default.
- Unknown or wrong form version: flag, ask, do not silently continue.
- Counters on counters: the last fully signed document controls (see tracker-deadline-table).
