---
name: tc-open-deal
description: Use when the agent says "open a file for [address/MLS#]": finds an existing file first, otherwise creates it with Details from Flexmls, parties by role, and the starting paperwork.
---

# tc-open-deal

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** A correct Transact file with no duplicates. Reference model: lib/dealdesk_tc/open_deal.py.

**Trigger.** "Open a file for [address or MLS#]", or a signed document that has no file yet.

## Steps

1. Load `tc-transact-navigator`. Search for an existing file by address, then MLS#, in every account context. An existing file spelled "Ln" is the same file as "Lane". If one exists: open it, list any duplicates, and stop. Do not create a second.
2. No file: create it. If the member's Brokerage system is set as the starting point and can create the file there, start there so the compliance file links. Otherwise start in Transact ("New Transaction", alt "Create Transaction").
3. Fill Details from Flexmls facts (flexmls-read): address, city, state, zip, the parish (Transact's label for it is "County"), price, financing, dates (exact Details labels: Offer Date, Offer Expiration Date, Offer Acceptance Date, Final Walkthrough Date, Closing Date, Possession Date). A missing label stops the step and names what was looked for.
4. On the Parties tab (heading "Transaction Parties"), use "Add Party" for each person. Fill Parties by role slot (Buyer 1, Buyer 2, Seller 1, Other Agent, Lender, Title). For each person: search contacts by email, then name, before "Create New". Never add the same person twice. If a contact has the same name but a different email, stop and ask. After each add, read the email back; a mismatch stops the run.
4a. Buyer and seller names do not print in any first-page form field; the forms read them from these role slots. Verify the slots (Buyer 1, Buyer 2, Seller 1) hold the right people before any form is filled. A wrong or empty slot is fixed through Parties ("Add Party") and re-checked. Never type names into first-page fields.
5. Add the starting paperwork for the side from the market pack (buyer: agency disclosure pamphlet and buyer representation agreement; seller: listing agreement, agency disclosure, property disclosure). Use the brokerage name from settings.
6. Report what was created, what was reused, and what is left.

7. If the deal type is known (offer, counter, amendment or repair request, extension, listing), hand off to `tc-templates`: it applies the packet template (add forms with the newest-revision pick, prefill, map signers, save an unsent draft envelope, stage the compliance plan) and stops at the review gate with one report. Unknown type: ask. Nothing in that run presses Prepare Signing, Next, Send, or Submit.

## Stop rules

- Existing file: open it, flag duplicates, stop.
- Never click "Offer Accepted", "Offer Rejected", "Delete", or any sync button unless the agent asked for that exact step. Allowing one does not allow the others.
- A contact whose email differs, or an email that reads back wrong: stop.
- A look-alike address (4312 vs 4321) is a different file. Leave it alone and mention it.
- Wrong user, MFA, captcha, expired session: stop (see the navigator).
