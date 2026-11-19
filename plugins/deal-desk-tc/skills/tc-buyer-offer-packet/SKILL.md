---
name: tc-buyer-offer-packet
description: Use to run a buyer offer from first terms to a draft email for the listing agent: build the offer, gate it, save a signing draft for the buyer, then draft the email once the buyer has signed.
---

# tc-buyer-offer-packet

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** One orderly path for a buyer offer. Reference models: fill_form.py, signing_prep.py, client_update.py (listing_agent_email).

**Trigger.** "Write an offer for [buyer] on [address]".

## Steps

1. Build the offer with `tc-fill-form`, including the pre-approval and the disclosure check.
2. Run the review gate. Wait for the agent's yes.
3. Save a signing draft for the buyer with `tc-signing-prep`. The agent sends it.
4. Watch for the buyer's completed signing. Until the buyer has signed, do nothing further.
5. After the buyer signs, draft the email to the listing agent with the fully signed offer, the pre-approval, and the agency disclosure. Flag any missing attachment.

## Stop rules

- The buyer signs first. No email draft before then.
- If the pre-approval or the agency disclosure is missing, ask. Do not hand over a short packet.
- Every outbound send is done by the agent, never the bot.
- All stop rules of `tc-fill-form` and `tc-signing-prep` apply.
