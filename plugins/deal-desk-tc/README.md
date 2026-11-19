# Deal Desk TC

From Caleb Jackson. Works in your own signed-in Transact. It opens files, fills forms, checks them, and saves signing drafts.

## What it does

- Opens a file, looking for an existing one first so you never get a duplicate.
- Fills offer, counter, addendum, amendment, and extension forms from the terms you give, then checks for blanks, conflicts, and missing disclosures.
- Preps signing: builds the envelope, adds signers and copy-only people, places fields, and saves a draft. You send it yourself.
- Watches the file after signing and tells you what changed or is due in the next three days.
- Gets signed documents into your own file's compliance tab and prepares fixes for anyone who still needs to sign.
- Applies packet templates for the Baton Rouge market.
- Drafts status updates in your voice. Drafts only.

## What it never does

It never sends, signs, or invites anyone, and never submits without your yes in chat. It does not press Next, Prepare Signing, Offer Accepted, Offer Rejected, or Delete. It never types a password; if a site asks for a sign-in or a code, it stops and asks you.

## How it fits with Deal Desk Deadline Tracker

This plugin bundles the shared core (hard rules, member setup, review gate, Louisiana market pack) inside it, so you do not install anything else first. The companion plugin, Deal Desk Deadline Tracker, bundles the same shared core and uses the same terms. You can install either one alone or both.

## What is in the folder

- `skills/`: the ten TC skills.
- `shared-core/`: the shared skills, `HARD-RULES.md`, and the shared library. The skills read `shared-core/skills/HARD-RULES.md` first.
- `lib/`: the TC library (`dealdesk_tc`).
- `templates/`: the Baton Rouge packet templates.

The Pelican practice deal is separate optional data and is not part of this plugin.
