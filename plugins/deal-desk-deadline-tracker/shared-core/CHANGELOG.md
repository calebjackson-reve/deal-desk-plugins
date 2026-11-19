# Shared core changelog

## 0.1.1 (Nov 16 2026, pending review)

Changed (Caleb's decision, Nov 16 2026: compliance uploads are automatic)
- HARD-RULES rule 1 and "How a yes works": compliance documents upload into the member's own Transact file's Compliance tab with no yes, under guards (own file, own deal, Compliance items only, never over a filled item, only fully executed copies, every upload logged). Compliance submit still needs the agent's explicit yes, one yes per try.
- gate.py: "attest" added to the always-refused hints (certify and attest are never the bot's). No other gate behaviour changed; the upload guards live in Deal Desk TC.
- member-setup and connectors wording: the optional Brokerage system fallback upload stays gated.

## 0.1.0 (unreleased)

New
- Skills: member-setup, review-gate, market-louisiana, crm-csv-import, client-enrichment, flexmls-read, deal-match, connectors.
- Deterministic helpers in lib/dealdesk_core (deadlines, csv_import, deal_match, gate, enrichment). Python 3 standard library only.
- Louisiana market pack data: holidays 2026-2027, forms list, form chooser.
- Pelican practice fixtures and scenario test bank.
- member_store: custom_templates counts as member data, so a setup template can never carry another member's templates.

Action needed
- None yet. Not released.
