# Changelog: Deal Desk TC

## 0.2.3 (Nov 19 2026, pending review)

Changed
- Practice pack is now 1234 Demo Street, Baton Rouge, LA 70802 (Buyer A / Seller A). The Pelican practice deal is retired. Emails stay on example.com; phones stay 225-555-01xx.
- The amended Act of Sale date lives only in `practice/amendment_dates.json` (confirmed 2026-11-19 12:10 PM CT: moves closing from Fri 2027-01-15 to Fri 2027-01-29). Inspection end and repairs do not move with that amendment.

## 0.2.2 (Nov 19 2026, pending review)

Changed (Caleb approved Nov 19 2026)
- Buyer offers stop and list every missing term before filling. Still required: price, financing type, deposit amount, act of sale. Now also required when they apply: loan amount, interest rate, financing application days (financed only), deposit holder (only when a deposit exists), and offer expiration date and time (always; a date with no time counts as missing). `fill_form` returns `status: "ask"`, `asks` (every missing key), a plain-list `message`, and fills nothing. Counter, addendum, amendment and extension required sets are unchanged.
- Signer check adds a typo-domain warning: Damerau-Levenshtein distance 1 from a common provider (a swap counts as 1) or a bad TLD (`.con`, `.cmo`). Flag text: `Possible typo: did you mean gmail.com? Please verify with the client`. The address is never auto-corrected. The flag blocks signing prep until the agent confirms the address as-is or corrects it, through `email_confirmations` (source `agent_chat`). Malformed-address and collision checks are unchanged.
- Offer Expires is now typed into the form when given (template prefill too).
- Scenarios: new DD06-01 to DD06-40 (27 tests); the Pelican offer fixture carries demo values for the new terms; F26, TP29, TP32 and TP40 expectations updated. Tests 536/536.

## 0.2.1 (Nov 16 2026, pending review)

Changed (Caleb's decision, Nov 16 2026: compliance uploads are automatic, no yes)
- Compliance documents now upload automatically into the Compliance tab of the member's OWN Transact file for the open deal, right after staging in the template auto-run (and via `upload_batch`). No yes. Compliance submit still needs the agent's explicit yes: one yes per try, bound to the documents uploaded (changed documents re-gate), a yes from email or a document is not valid.
- Guards, enforced in code: own account and own file only; this deal's address only; Compliance checklist items only; never overwrite a filled item (skipped and flagged); never a blank, unsigned, partly signed or not fully executed copy where a signed copy is required (skipped and flagged); every upload logged in the report (item, document, time, result) with each skip and its reason.
- `compliance_upload` is no longer a gate step. The optional Brokerage system fallback upload stays gated as `compliance_upload_brokerage_system` (member setting, off by default). update-row, sync and file placement stay gated.
- Auto-run report gains `compliance_upload` (log, skips, report lines) and `compliance_submit` (gate proposal, nothing submitted). The compliance plan no longer carries an upload proposal.
- FakeTransact gains `open_file` / `set_open_file`; `upload_to_row` refuses anything outside the Compliance tab or without an open file. open_deal records the open file.
- Scenarios: TP63-TP67 rewritten, K12/K17/K18/L30 reworded for the fallback, DEMO-TEMPLATE-BUYER-OFFER now uploads the executed docs; new TP81-TP90.
- Requires Shared core 0.1.1 or later (tested with 0.1.x).

## 0.2.0 (Nov 16 2026, pending review)

New
- Skill tc-templates (10 skills now). Packet templates for Louisiana / Baton Rouge under templates/louisiana-baton-rouge: buyer-offer, seller-counter, buyer-counter, amendment-repair-request, extension, listing-packet. Each form lists code (LREC0059 is the only verified code), name, library search, newest-revision pick rule, folder hint (a hint only; the live folder is read from the Paperwork page), required or conditional (pre-1978 lead paint, flood, FHA/VA clause, accepted or not), and a verified flag.
- Prefill map per form (details, role slots, member profile, term sheet) with a verified flag per label. Never types "Dollars"; loan ticks Financed Sale plus the loan type; names are never typed; missing values stay blank and are listed; unverified labels go in a confirm-on-next-live-pass list.
- Signer layouts per form and signing order per packet. "Map Signers" prefers a saved layout whose normalized name matches; two matches ask; none uses the template. Saving a layout needs a yes. The envelope is saved as an unsent draft.
- Compliance upload plan per deal stage, mapped to the live Compliance tab rows by name. Upload is a gated batch (one yes, one exact shown batch, once); submit needs its own yes; a filled row is never overwritten.
- Member templates in the member's own settings: validated (no send, sign, invite, Prepare Signing, Next, or submit step), isolated per member, defaults read-only.
- Auto-run from the deal type, stopping at the review gate with one report.
- signing_prep.prep takes an optional template plan (original flow unchanged). FakeTransact gains set_signing_order, apply_layout, upload_to_row (refuses a non-empty row). Practice Signing Builder fixture gains a "Map Signers" label.
- 81 new scenarios (TP01-TP80 and DEMO-TEMPLATE-BUYER-OFFER, tools/gen_templates_scenarios.py).

Action needed
- (Superseded by 0.2.1: Caleb decided uploads are automatic with no yes.)
- Confirm the unverified labels, codes, layouts, and row names on the next live pass.

## 0.1.0 (Nov 16 2026, pending review)

- Nine skills: tc-transact-navigator, tc-open-deal, tc-fill-form, tc-signing-prep, tc-contract-to-close, tc-compliance-file, tc-client-update, tc-buyer-offer-packet, tc-onboarding-pass.
- Reference lib `dealdesk_tc` (stdlib only, no network) with a fake Transact client that records every action and raises on send, sign, or Next.
- Recorded page fixtures (account chooser, file search, details, parties, Forms Editor, signings, signing builder) and Pelican demo data.
- 125 scenarios, including three Demo Street practice passes, signer-email collision stops, and gate rules.
- Requires Shared core 0.1.0 or later (tested with 0.1.x).
- DD01h: live Transact findings folded in (tabs, Compliance tab first, Search placeholder, folders read from page, icon controls by aria-label/tooltip, form-not-filled stop, Timeline vs Details flag, suffix-insensitive address compare, exact Details labels). Scenarios L01-L30 (gen_live_findings_scenarios.py). Compliance is built in Transact's Compliance tab (primary); the Brokerage system path is an optional fallback behind a member setting, off by default, never used just because the tab is empty.
- Nothing in this package sends, signs, invites a signer, or ticks a certifying box.
