---
name: tc-onboarding-pass
description: Use during member setup or on request to run the 1234 Demo Street practice deal through the TC plugin and confirm nothing was sent; passing marks TC ready.
---

# tc-onboarding-pass

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** Prove the TC plugin works end to end on demo data before live files. Reference scenarios: DEMO-PASS-TC, DEMO-PASS-TC-EXISTING-FILE, DEMO-PASS-TC-COLLISION.

Practice files come from the practice pack (`deal-desk-practice-<version>.zip`, folder `practice/`: README.md and files/). It is the one source of truth for the 1234 Demo Street deal. Never use a real client's papers in its place.

**Trigger.** `member-setup`, or "run the TC practice pass".

## Steps

1. Use the 1234 Demo Street deal only: 1234 Demo Street, Baton Rouge, LA 70802 (East Baton Rouge Parish), $289,000, buyer side, fake names, emails at example.com, phones 225-555-0100 to 0199.
2. Use a practice or sandbox Transact file the member controls. If none exists, run on the recorded Transact pages in the practice pack and say so.
3. Open the file (`tc-open-deal`). If it already exists, open it and stop that step.
4. Fill an offer, then a counter (`tc-fill-form`). Run the gate and wait for the agent's yes.
5. Prep a signing draft with fields mapped for every signer (`tc-signing-prep`). Show the field map and the signer check.
6. Confirm and say plainly: nothing was sent, nothing was signed, "Next" was not pressed, and the buyer signs first in a real packet.
7. Pass only if every step behaved. Record the result in the member's setup.

## Stop rules

- Demo data only. Never use a real client in the practice pass.
- A signer email collision in the practice data is a correct stop, not a failure.
- Any send, sign, or Next click means the pass fails and the plugin stays off.
