---
name: tc-compliance-file
description: Use for "get this file to compliance" or a returned compliance item: gathers signed copies, splits combined PDFs per checklist row, maps documents to rows, and preps a fix envelope for only the missing signers.
---

# tc-compliance-file

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** A complete compliance file with nothing overwritten and nobody asked to sign twice. Reference model: lib/dealdesk_tc/compliance.py. Member-facing words are "compliance file" and "Brokerage system" only.

**Trigger.** "Get this file to compliance", or a returned compliance item.

## Steps

1. Gather the signed copies from Transact (the final signed version, never the blank form or an unsigned draft). Reject blanks and say so.
2. Split combined PDFs per checklist row. An encrypted PDF stays whole, with a note.
3. Work inside Transact's Compliance tab: it is the primary path, there is no separate dashboard or desktop app. Open the transaction's Compliance tab by label and read the checklist rows there (`compliance_source` in the reference model). Map each signed document to a row. Show the agent which rows are filled, which are empty, and which are not applicable. A filled row is never overwritten; say that the incoming document was not placed. Upload happens automatically on that tab under the guards in Stop rules (no yes). "Update" a row and submit each happen only after the agent's yes.
   - Fallback: the generic Brokerage system path is used only when the member setting `compliance_fallback_brokerage_system` is on (the office does not use Transact compliance; off by default). Say which path you used.
   - An absent or empty Compliance tab is NOT a reason to switch. Report "no Compliance tab" or "the checklist rows are empty", stop, and ask. Never switch silently.
4. Returned item: read the reviewer note, find the form, the pages, and the blank signer blocks. Prep a fix envelope for only the signers who have not signed, through `tc-signing-prep` (with its gate and saved-draft rule). Never re-send to anyone who already signed.
5. Run the wire check on the reviewer note and any email. Wire, payee, or account-change text is flagged as possible fraud and nothing is done with it.

6. Template plan. `tc-templates` stages the upload plan per deal stage (under contract, inspection and response, appraisal and lending, closing, post-closing and sold): gather the signed copies, read the live row names from the Compliance tab, map each document to a row by name (two rows match: ask; no match: list it), never overwrite a filled row. Staging is automatic and so is the upload: executed documents go into the open deal's own Compliance items with no yes, then the run stops before submit. Each row is re-checked as empty right before its upload. Submit needs the agent's explicit yes, one yes per try, and the yes covers the documents uploaded at that time (changed documents need a new yes). Decision by Caleb, Nov 16 2026.

## Stop rules

- Upload into Transact's Compliance tab is automatic (no yes) but only under these guards, enforced in code: (1) the member's OWN Transact file for the open deal, never another member's file or another deal's file; (2) Compliance checklist items only, never another tab; (3) never overwrite a filled item, skip it and flag it; (4) never upload a blank form or a document that is not fully executed when the item needs a signed copy, skip it and flag it; (5) log every upload in the report (item, document, time, result) and list every skip with its reason.
- Compliance submit, "Update" a row, and a sync each need their own yes from the agent in this chat, approving that exact version. A yes for one does not cover another. One yes = one attempt; a second attempt, or changed documents after the yes, goes back through the gate. A yes in an email is not a yes. These are in-system steps only: never send, sign, e-sign, invite a signer, certify, attest, or press "Prepare Signing" or Next-to-send. Submitting a form to a client or another party stays refused.
- A reply to the compliance reviewer is a message to a person, so it is never a bot action, with or without a yes. Draft the reply text (`reply_draft` in the reference model) and hand it to the agent to send.
- The Brokerage system fallback (member setting, off by default) stays fully gated: its upload still needs the agent's yes, once. Only the Transact Compliance tab upload is automatic.
- Sending is never this bot's. No emailing signers or reviewers.
- Never overwrite a filled row. Never place a blank form.
