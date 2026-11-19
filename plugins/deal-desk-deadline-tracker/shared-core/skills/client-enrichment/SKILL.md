---
name: client-enrichment
description: Use after an import or connector pull, or 'fill in my clients': proposes missing client fields with a source, and saves only what the agent accepts.
---

# client-enrichment

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** Fill gaps in client records with reviewed suggestions. Reference model: lib/dealdesk_core/enrichment.py.

**Trigger.** After an import or connector pull, or "fill in my clients".

## Steps

1. Propose missing fields (property facts from Flexmls or public tax records, a link to an open deal, contact cleanup).
2. Show each suggestion with field, current value, proposed value, source ("Flexmls listing", "Public tax record", "Transact file", "CSV import", "Brokerage system"), and confidence.
3. The agent accepts or rejects each one (bulk accept per source allowed).

## Stop rules

- No saved record changes without review.
- A rejected suggestion is remembered and not re-proposed unless the source value changes.
- Agent-confirmed values win over later syncs, extractions, and suggestions unless the agent accepts the new value.
