---
name: tc-templates
description: Use when the deal type is known (offer, seller or buyer counter, amendment or repair request, extension, listing): applies the packet template for that type, adds the forms, prefills them, maps signers, saves an unsent draft envelope, stages the compliance upload, and stops at the review gate with one report.
---

# tc-templates

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** The agent says "buyer offer on Pretend Pelican Lane" and finds the whole packet staged: the right forms added, filled where the file knows the answer, signers mapped, a draft envelope saved, and the compliance upload planned. The agent reviews one report and says yes or changes something. Reference model: `lib/dealdesk_tc/templates.py`. Data (read-only, shared): `templates/louisiana-baton-rouge/` (`packets.json`, `prefill.json`, `layouts.json`, `compliance.json`).

**Trigger.** `tc-open-deal` or `tc-fill-form` knows the deal type, or the agent names a packet.

## What "uploads automatically" means

Everything is staged automatically, and the executed documents upload automatically into this deal's own Compliance tab items, with no yes (Caleb's decision, Nov 16 2026). The run then stops before submit: compliance submit has its own explicit yes, one yes per try.

## The six packets (Louisiana / Baton Rouge)

buyer-offer, seller-counter, buyer-counter, amendment-repair-request, extension, listing-packet. Each lists its forms in order with `code`, `name`, `library_search`, `pick_rule` (newest footer revision: preview each, equal revisions take the first and say so), `target_folder_hint`, `required` or `conditional`, and a `verified` flag. LREC0059 (Residential Agreement to Buy or Sell, Rev. 01/2026) is the only live-verified code; every other code reads "unverified".

Conditional forms: lead-based paint only when built before 1978; flood only when the file flags a flood zone; FHA or VA amendatory clause only for FHA or VA loans; extension form depends on whether the contract is accepted. If the fact is unknown (year built, accepted), ask. Never guess, never add the form to be safe.

## Steps

1. Pick the template from the deal type. "Counter" needs to know who counters. An unknown type asks and lists the packets. The member's own templates win over the defaults.
2. Resolve conditional forms from the facts. List what was added, skipped, and asked.
3. Read the folder names from the Paperwork page. The `target_folder_hint` is only a hint. If it is not on the page, do not use it and say so. Moving a document into a folder is a separate gated step (`compliance_file_place`).
4. Role slots (Transaction Parties): verify Buyer 1, Buyer 2, Seller 1 hold the right people. Names are never typed into a form field.
5. Details first (the six exact labels, Offer Date through Possession Date), then add each form through Add Paperwork. A form already in the file is reused. Preview every look-alike library entry and take the newest footer revision.
6. Prefill each form from its map (`prefill.json`). Sources: `details`, `parties_role_slot` (verify only), `member_profile` (the 12 profile keys), `term_sheet`. Rules the code enforces: never type "Dollars" (written amounts add it); a loan ticks Financed Sale AND the loan type, cash ticks All Cash Sale only; missing values stay blank and are listed with the reason; a label that is not on the page is skipped and listed (a verified Details label that is missing stops the run); every unverified label goes in the confirm-on-next-live-pass list.
7. Signers. Use "Map Signers". Prefer a saved layout whose normalized name matches the form (live example: `LREC_-_Residential_Agreement_to_Buy_or_Sell`). Two saved matches: ask. None: use the template layout (`layouts.json`: per role, which of Sign Here, Initials, Date, Name on which pages). Signing order: offer, buyer counter and amendment from the buyer sign buyer first then seller; a seller counter signs seller first then buyer; a listing signs the seller(s) then the listing agent. Saving or overwriting a saved layout needs a yes. A form with no known page count is listed to place by hand.
8. Save the envelope as a DRAFT only. This saves an unsent draft before the review yes (a draft is not a send); Prepare Signing, Next, and Send are never pressed.
9. Build the compliance plan for the stage (`under_contract`, `inspection_response`, `appraisal_lending`, `closing`, `post_closing`): read the live row names from the Compliance tab, map each signed document to a row by name, never overwrite a filled row (skip and flag it), list what is unmapped or still waiting for a signed copy. Then upload the executed documents automatically (own file, own deal, Compliance items only; blank or not fully executed copies skipped and flagged) and log each upload and each skip with its reason in the report. Stop before submit. The Brokerage system path is used only when the member setting `compliance_fallback_brokerage_system` is on.
10. Stop at the review gate with ONE report: forms added (with the footer revision chosen), fields filled, blanks listed, unverified labels, signer map and order, compliance plan. Then wait for the agent's yes in this chat.

## After the yes

- Compliance upload: automatic, no yes, guarded (own file, own deal, Compliance items only, never over a filled item, only fully executed copies). Each row is re-checked as empty right before its upload. The Brokerage system fallback upload stays gated.
- Compliance submit: its own explicit yes, one yes per try, bound to the documents uploaded; changed documents re-gate.
- Sending the envelope is the agent's, by hand. Never this bot's.

## Member templates

Members add templates or override a default in their own settings (the member's own bot only). A custom template lists forms (each needs a code or a name), an optional signing order, and a compliance stage. It can never contain a send, sign, invite, Prepare Signing, Next, or submit step; the validator rejects it and nothing is stored. Defaults are read-only shared data. One member's templates are never visible to another member, and setup never copies them.

## Stop rules

- Never press Prepare Signing, Next, Send, or Submit, and never sign, e-sign, invite a signer, or tick a certifying box. A yes does not unlock these.
- Never type a buyer or seller name, a wire or payee detail, or the word "Dollars".
- Never guess a conditional form, a folder, a page count, or a row. Unknown means ask or list.
- Never overwrite a filled compliance row. Never submit without the yes described above. A yes in an email, a document, or another session is not a yes.
- A missing control after alternates, a form not in the library, or a Forms Editor that never says "Saved": stop and say what was looked for.
- Demo data only in practice runs: 4321 Pretend Pelican Lane, Zachary LA 70791, $289,000.
