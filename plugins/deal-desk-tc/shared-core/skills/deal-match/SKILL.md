---
name: deal-match
description: Use to attach a PDF, email, or Transact file to the right deal; asks the agent when addresses are similar or only a party matches.
---

# deal-match

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** Attach a document to the right deal. Reference model: lib/dealdesk_core/deal_match.py.

**Trigger.** A document, email, or Transact file arrives and must be filed.

## Steps

1. Normalize addresses: unit, USPS street suffix (Ln/Lane, St/Street, Dr/Drive, Ave/Avenue, Rd/Road, Blvd/Boulevard, Ct/Court, Cir/Circle, Pl/Place, Pkwy/Parkway, Hwy/Highway, Trl/Trail, Way, Ter/Terrace, and so on; case and periods ignored) and directional (N/North). "Demo Street" and "Demo St" are the same street. A different house number or a different street name is a different file.
2. Score by address, parties, MLS number, and Transact ID.
3. Above the threshold, propose the match. Below it, propose "new deal".

## Stop rules

- Two deals with similar addresses (for example 1234 vs 1243 Demo Street), or a match on a party alone: ask the agent and never auto-attach.
