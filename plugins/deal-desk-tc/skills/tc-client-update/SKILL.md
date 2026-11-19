---
name: tc-client-update
description: Use to draft a status update to a client, lender, or the other agent in the member's voice from verified file facts; drafts only, never sent.
---

# tc-client-update

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** A short, accurate update the agent can send. Reference model: lib/dealdesk_tc/client_update.py.

**Trigger.** "Update the buyers", "tell the lender", or a due item from `tc-contract-to-close`.

## Steps

1. Collect facts from the file, the confirmed table, and mail. Use only verified facts; list any unverified ones as left out.
2. Draft in the member's voice (voice guide in settings). No voice guide: write plain text and say so.
3. Check for wire, payee, or account-change text. Flag it as possible fraud, leave it out of the draft, and take no action.
4. Put the draft in chat or the member's email drafts, addressed to the right person.

## Stop rules

- Never sent. The agent sends it.
- No wire, payee, or account details in an update. If the agent asks for them, flag it and point to the title company by phone.
- No unverified date, amount, or promise in a draft.
- Not legal advice. Clause questions go to the broker or an attorney.
