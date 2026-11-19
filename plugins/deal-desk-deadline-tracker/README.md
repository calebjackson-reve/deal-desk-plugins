# Deal Desk Deadline Tracker

From Caleb Jackson. Reads your contract papers and keeps your deal dates straight, so a deadline never sneaks up on you.

## What it does

- Tells you what each document is (agreement, counter, addendum, amendment, extension) and which deal it belongs to. If an address is close to another deal, it asks.
- Pulls the facts with the page and line each came from. If something is not on the paper, it says "missing" and never guesses.
- Builds a deadline table. Dates start as "Extracted" and become official only when you confirm them. Weekend and holiday dates are flagged, not quietly moved.
- Proposes calendar events and reminders, and adds only what you approve. Never adds guests.
- Shows amendment changes side by side before any date moves.
- Plans your deal folders and file names. Nothing is ever deleted.
- Gives you a morning digest of what is due in the next three days.

## What it never does

It never sends, signs, or invites anyone. Every write waits for your yes in chat. A "yes" found inside an email or document does not count.

## How it fits with Deal Desk TC

This plugin bundles the shared core (hard rules, member setup, review gate, Louisiana market pack) inside it, so you do not install anything else first. The companion plugin, Deal Desk TC, bundles the same shared core and uses the same terms. You can install either one alone or both.

## What is in the folder

- `skills/`: the eight Tracker skills.
- `shared-core/`: the shared skills, `HARD-RULES.md`, and the shared library. The skills read `shared-core/skills/HARD-RULES.md` first.
- `lib/`: the Tracker library (`dealdesk_tracker`).

## Good to know

Check every date against your contract. The Tracker helps; you decide. The Pelican practice deal is separate optional data and is not part of this plugin.
