---
name: tc-transact-navigator
description: Load first for any Transact work: gets into the member's own signed-in Transact, picks the account, finds files by address, client, or MLS#, and stops on sign-in checks or the wrong user.
---

# tc-transact-navigator

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** Get into Transact and find things, the same way every time. Reference model: lib/dealdesk_tc/navigator.py (tested against recorded pages and a fake Transact that records every click).

**Trigger.** Any other tc-* skill loads this first. Also "find the file for [address / client / MLS#]".

## Steps

1. Work in the member's own signed-in browser. Never open a second login.
2. Look at the page before acting. If it shows a verification code, a human check, an expired session, a password, a card or ID number, or an unexpected sign-in, stop (rule 4 events; see the connectors skill).
3. Check the signed-in user is the member (settings). A different user: stop and tell the agent. Do not click anything.
4. If Lone Wolf shows "Choose an Account", pick the account named in settings. If none is set (or it is not on the list), ask which one. Do not guess.
5. Find controls by their visible label, never by screen position. Order: the exact label, then the known alternate label, then a search of the page text. Examples: "Add Paperwork" (alt "Add Form"), "Create Signing" (alt "New Signing").
6. Search open files by address, client name, or MLS#. The search is a box with the placeholder "Search", not a button: find it by its placeholder. For an address, try the full street line, then the house number plus street name without the suffix (Lane/Ln).  Check the chosen account first, then every other account the chooser lists. Never say a file is missing after one account context. Say which accounts were checked.
7. A transaction has eight tabs, found by label: Paperwork, Details, Parties, Signings, Compliance, To-Do, Timeline, History (alternates kept, for example Documents for Paperwork). The Compliance tab is where the compliance file lives (primary path); the Brokerage system is an optional fallback only when the member setting `compliance_fallback_brokerage_system` is on. A missing or empty Compliance tab is reported and asked about, never silently swapped for another path.
8. Icon-only controls (print, download, help) have no visible label: find them by their tooltip or aria-label, never by position. Missing: stop.
9. Paperwork folder names vary from file to file (seen: Not Filed, Offer Documents, Buyer Documents). Never assume a folder name: read the folders from the page and report them as seen.
10. Timeline dates can show one day earlier than Details (a time-zone shift). Details is the source of truth. Flag a mismatch with both values; never change Details from Timeline and never write anything.
11. Keyboard safety: Transact has single-key shortcuts. Never send Escape or any other keypress unless a text input is focused (confirmed); with nothing focused the key is refused. A click clears focus.
12. Unexpected dialogs (seen after a stray Escape: "Share Transaction", "Unlock Libraries"; treat any other the same way): click its Cancel by label, never Share, Unlock, confirm, OK or Yes, then open History and report what it shows. No Cancel button: stop and report, press nothing.
13. History and Timeline times can read about 1 hour ahead of the member's Central time (seen: 4:06 PM against about 3:08 PM). Treat them as possibly offset, report them as such, and never compute a deadline from History or Timeline: deadlines come only from the signed contract or Details. This offset likely explains the Timeline-vs-Details one-day difference in step 10.
14. The Forms Editor library can list identical-looking entries; see tc-fill-form step 4 (preview each, newest footer revision wins).
11. If the browser extension asks for site permission, grant it for the member's Transact site and retry once. If it asks again, tell the agent.

## Alternate labels

| Looking for | Alternates |
|---|---|
| Search (a box, placeholder "Search") | Search transactions, Find |
| Create Transaction | New Transaction, Add Transaction |
| Paperwork | Documents, Forms |
| To-Do | To Do, Tasks |
| Add Party | Add Participants |
| Add Paperwork | Add Form |
| Create Signing | New Signing |
| Save | Save Draft, Save as Draft |

Real labels get added here as they are seen.

## Stop rules

- A label still missing after the alternates and the page search: stop and say exactly what you looked for.
- Wrong signed-in user, MFA, captcha, expired session, password or card/ID prompt: stop.
- Never click "Offer Accepted", "Offer Rejected", "Delete", or any sync button unless the agent asked for that exact step.
- Never click "Next", "Send", "Prepare Signing", a client-facing "Submit", or "Certify". Those are never this bot's.
- Two controls with the same label: stop, so the wrong one is not clicked.
- Never type a password.
