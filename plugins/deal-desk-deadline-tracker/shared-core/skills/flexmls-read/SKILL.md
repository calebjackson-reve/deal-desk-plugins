---
name: flexmls-read
description: Use to read one listing or tax record by MLS number or address under the member's own Flexmls login; read only.
---

# flexmls-read

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** Listing and tax/property facts, read only, in the member's own signed-in browser, or via the Flexmls API if the member's MLS grants access.

**Trigger.** A skill needs a listing or tax fact (property facts, flood zone, legal description, parcel ID).

## Steps

1. Confirm the signed-in user is the member.
2. Read one listing by MLS number or address (status, price, beds/baths, sq ft, year built, lot, subdivision, parish, legal description, flood zone, HOA, listing agent/office) or one tax record (parcel ID, owner of record, assessed value, taxes).
3. Before reading each page, and again after any navigation, run it through lib/dealdesk_core/session_guard.py (inspect the page URL, title, visible labels and text). If it returns stop, stop, give the agent its plain-words note, and read nothing further. Never type a password.
4. A field the page does not show is "missing". Never guess it or borrow it from another record (session_guard.read_fields).
5. Record the URL and the time seen.

## Stop rules

- No edits, no bulk export, no mass photo download, no inventory scraping into storage. Follow MLS rules.
- Never borrow a similarly named record.
- MFA, captcha, expired session, or a password prompt: stop and tell the agent.

## Hard rules

- Drafts and prep only. Never send, sign, invite a signer, or tick a certifying box. Never submit a form to a client or other party. (Compliance submit in the Brokerage system compliance file is an in-system step that needs your yes through the review gate.) An OK never changes that.
- Never type a password. Captcha, MFA, an unexpected sign-in, or a page asking for a password, card, or ID number: stop and tell the agent.
- Demo data only in practice runs: 4321 Pretend Pelican Lane, Zachary LA 70791.
