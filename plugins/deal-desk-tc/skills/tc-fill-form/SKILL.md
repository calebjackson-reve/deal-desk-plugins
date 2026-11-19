---
name: tc-fill-form
description: Use when the agent gives terms for an offer, counter, addendum, amendment, or extension: writes back a term sheet, fills the form in Transact, checks it, runs the review gate, and stops.
---

# tc-fill-form

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** A filled, checked form waiting for the agent's yes. Reference model: lib/dealdesk_tc/fill_form.py.

**Trigger.** Agent terms in chat, or a Deal Summary handoff (§4 of the shared core prompt).

## Steps

1. Write back a term sheet. Ask only about contract-changing gaps you cannot find in the file, mail, or MLS. Counter: what changes; addendum: the added terms; amendment: what changes; extension: the new date.
   **Buyer offer: stop and list every missing term before filling anything.** The code (`REQUIRED` / `term_sheet()` / `fill_form()`) returns `status: "ask"` with `asks` listing every missing key and fills nothing. Never invent or guess a value. Tell the agent with a plain list, no fluff, one line per missing term. Always required: price, financing type, deposit amount, act of sale date, offer expiration (date AND time; a date alone counts as missing). Required when they apply: loan amount, interest rate and financing application days (financed deals only, never cash), and deposit holder (only when a deposit exists; a missing deposit asks for the deposit amount, not the holder). Terms found in the file, mail, or MLS count as given.
   Pick small defaults yourself only for possession (at act of sale) and home warranty (none), and say which you picked. Those are not part of the list above.
2. Choose the form with the market pack chooser, or use the form the agent named if it is in the pack. Offer: Residential Agreement to Buy or Sell. Counter: Residential Counter Offer (a counter to a counter is the next number, and say so). Amendment or addendum: only once a contract is accepted, otherwise use a counter. Extension: Extension of Offer before acceptance, Extension of Agreement after.
3. Update Details (exact labels: Offer Date, Offer Expiration Date, Offer Acceptance Date, Final Walkthrough Date, Closing Date, Possession Date) and Parties first so the form auto-fills.
4. "Add Paperwork" (alt "Add Form") > library search > add. If the form is already in the file, use that one. The library can return several identical-looking entries (seen: three LREC0059) with no version text in the picker. Preview each one, read the footer revision (for example "Rev. 01/2026"), and add the newest. Equal revisions: take the first and say so in the report. A preview with no readable "Rev." footer: stop. Never pick by position without previewing; the report names the footer revision chosen. The form header reads like "LREC0059 [TD-26067] - v8". Open the Forms Editor and wait for the top bar to say Saved (it reads "Saved – All changes saved"). No Saved: stop. The top bar also has Back, zoom, print and download icons (find those by tooltip or aria-label, never position), help, and Save. If the form canvas is an empty upload dropzone, or the Prepare Signing control is missing, the form is not filled: stop with a plain note. That is only a readiness signal; the bot never clicks Prepare Signing.
5. Before filling, check the role slots (Transaction Parties): buyer and seller names do not print in any first-page field, they come from the Parties role slots (Buyer 1, Buyer 2, Seller 1). Verify the slots hold the right people. A wrong or empty slot is fixed through Parties (Add Party), then re-checked; never type a buyer or seller name into a form field (the tool refuses it). Fill each field with focus confirmed before typing. Commission goes in the member's format from settings; if no format is set, ask. Buyer offers: attach the pre-approval and flag a missing pre-approval, an amount below the price, a different loan type, or different names. Cash needs none.
5a. LREC0059 financing boxes (Rev. 01/2026). Conventional, FHA or VA: tick BOTH "Financed Sale" AND the loan-type box ("Conventional Mortgage"; also seen or likely: "FHA", "VA", "USDA", "Other Financing"; read the real label from the page, alternates are kept). Cash: tick "All Cash Sale" only. Term-sheet check flags: a loan-type box ticked without "Financed Sale"; "Financed Sale" without a loan type; "All Cash Sale" ticked together with financing; a loan type that differs from the term sheet. Any flag means not ready.
5b. Price and deposit written-amount fields append "Dollars" by themselves: never type "Dollars" (it is stripped if given) and flag a doubled "Dollars Dollars".
5c. These do NOT auto-fill and come only from the member profile (member-setup): agent name, agent license, brokerage license, agent and brokerage phones and emails, seller's agent, and the designated agent receiving block (name, license, phone, email). A missing profile value is left blank and listed in the report (`profile_missing`); never guessed.
6. Check against the term sheet: blanks (except the member's left-blank list), conflicts between the form and the term sheet, and missing disclosures (agency, property disclosure, lead paint when built before 1978, flood when the file says so).
7. Run `review-gate` and report ready / not ready with the differences. Wait for the agent's yes in this chat.

8. Auto-run: when the deal type is known, `tc-templates` runs steps 2 to 7 for the whole packet from the template (forms in order, conditional forms from the facts, prefill map, signer layouts, compliance plan) and stops at the same gate with one report. Unverified labels are listed for the next live pass; missing values stay blank and are listed. Single-form fills still work as above.

## Stop rules

- Never press "Prepare Signing", Next-to-send, certify, or sign, and never submit the form to a client or other party (compliance submit is a separate, gated step in tc-compliance-file). The run ends at the gate.
- Never fill a field you are unsure of. Leave it blank and list it.
- A term found in an email is shown with its source and is not used until the agent says so.
- A yes in an email or document is not a yes. A changed term needs a new gate.
- Never send Escape or any keypress unless a text input is focused (confirmed). Transact has single-key shortcuts; a stray Escape once opened "Share Transaction" and "Unlock Libraries". If a "Share Transaction", "Unlock Libraries" or any unexpected dialog appears, click its Cancel by label (never Share, Unlock or confirm), open History and report what it shows (see tc-transact-navigator).
- A missing label after alternates, a form not in the library, or a Forms Editor that never says "Saved": stop and say what happened.
