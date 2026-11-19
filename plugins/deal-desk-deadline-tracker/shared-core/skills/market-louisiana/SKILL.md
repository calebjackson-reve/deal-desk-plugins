---
name: market-louisiana
description: Use for Louisiana / Baton Rouge deadline math, the forms list, holidays, and the form chooser; every number is read from the signed form.
---

# market-louisiana

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** Deadline math, the form list, and local defaults. These are observed GBRAR / LREC practice, not law. Data lives in market-pack.json next to this file; math lives in lib/dealdesk_core/deadlines.py (compute_deadline).

**Trigger.** Any deadline computation, form selection, or holiday/weekend check. Swappable per market.

## Steps

1. Clock: acceptance = the final signature on the last counter (date + time). If missing, in the future, or without a time: stop and ask.
2. Counting: calendar days unless the form says business/working days. The day after acceptance is day 1 (9/30 + 13 days = 10/13). Business days are Mon-Fri minus holidays; the act of sale day does not count.
3. Hours count to the minute in the member's time zone (inspection response windows are commonly 72h each way from the delivery timestamp: Fri 4:15 PM + 72h = Mon 4:15 PM).
4. Event-based periods (appraisal delivered, response received) show the latest possible date, marked "set on delivery".
5. Title curative days count from the act of sale; running past the act is normal. Repairs and receipts are commonly due 5 working days before the act. "On or before" dates are outer limits.
6. Weekend or holiday deadlines are flagged, not rolled, unless the contract says to roll them.
7. A period the form does not state is "unconfirmed: ask agent", never filled from defaults.
8. Deadline types: deposit/earnest money; loan application and proof; lender intent to proceed; proof of funds (cash); inspection / due diligence end and response windows; WDIR; appraisal; financing/loan approval; sale-of-buyer's-home contingency; repairs complete + receipts; title exam / curative; insurance binder; final walkthrough; act of sale / closing; possession.
9. Flags: weekend/holiday; already past; ends after the act (except title); loan application after inspection ends; walkthrough before repairs are due; email date differs from agreement (show both; the agreement wins until the agent decides); missing other-agent, lender, or title contact; FHA/VA without its amendatory clause.
10. Form chooser: offer -> Agreement to Buy or Sell; counter -> Counter Offer; change after acceptance -> Amendment; add a term -> Addendum; more time before acceptance -> Extension of Offer; more time on a contract date -> Extension of Agreement; inspection reply -> DD/Inspection Response; buyer's sale -> Contingency Addendum; cancel -> Cancellation. If two versions match, use the newest dated one and say which.

## Form-specific field rules: LREC0059 (Residential Agreement to Buy or Sell, header "LREC0059 [TD-26067] - v8", footer "Rev. 01/2026")

Observed in a live practice fill (demo file). Re-check when the footer revision changes.

- Financing boxes: conventional, FHA or VA tick BOTH "Financed Sale" AND the loan-type box ("Conventional Mortgage"; also seen or likely "FHA", "VA", "USDA", "Other Financing"). Cash ticks "All Cash Sale" only. Term-sheet check flags a loan-type box without "Financed Sale", "Financed Sale" without a loan type, and "All Cash Sale" ticked with financing.
- Price and deposit written-amount fields append "Dollars" themselves. Do not type it; flag "Dollars Dollars".
- Not auto-filled, filled from the member profile only (blank and listed if missing): agent name and license, brokerage license, phones, emails, seller's agent, designated agent receiving block.
- Buyer and seller names print in no first-page field; they come from the Parties role slots. Verify the slots, fix through Parties, never type names into the form.
- The form library can show several identical-looking LREC0059 entries with no version text: preview each, read the footer revision, take the newest (equal: first, and say so).
- Transact History and Timeline times can read about 1 hour ahead of Central time. Never compute a deadline from them (compute_deadline refuses source "history" / "timeline"); only the signed contract or Details. This likely explains the Timeline-vs-Details off-by-one.

## Stop rules

- Holidays are data (2026-2027 in market-pack.json, including Mardi Gras and Good Friday marked verify). Confirm office and title closures with the broker.
- Not legal advice. Clause meaning goes to the broker or an attorney.
- Never guess or quietly move a date. The signed contract controls; unreadable means missing.
