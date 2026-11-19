# Installing Deal Desk on Grok Bot

Deal Desk is two plugins, Deadline Tracker and TC, in the Cursor Plugin format:

```
.cursor-plugin/marketplace.json          lists both plugins
plugins/deal-desk-deadline-tracker/      the Deadline Tracker
plugins/deal-desk-tc/                    the TC plugin
```

## What you get

- **Deal Desk Deadline Tracker** reads your contract papers and keeps your deadline table, calendar proposals, and morning digest.
- **Deal Desk TC** works in your own signed-in Transact: opens files, fills and checks forms, preps signing drafts, files compliance.

Each plugin carries its own copy of the shared core (the hard rules, member setup, review gate, Louisiana market pack). You do not install a third plugin first. If you install both, you will have two identical copies of the shared core, and each plugin reads only its own copy.

## The hard rule, in one sentence

It never sends, signs, or invites anyone, and every write waits for your yes in this chat.

## How to add it

1. **This public GitHub repo:** https://github.com/calebjackson-reve/deal-desk-plugins. It has `.cursor-plugin/marketplace.json` at its root. If your app can add a plugin from a Git repository, point it at that URL.
2. **Cursor's reviewed marketplace:** Cursor lists plugins after its team reviews them. Deal Desk is not listed there yet; submitting it is a separate, later step. If it is listed later, install it from there.
3. **Cursor IDE, local copy:** if your app loads local plugins, copy a whole plugin folder (the one that contains `.cursor-plugin/`, not just `skills/`) into your local plugins location. Check Cursor's plugin documentation for the current folder.

Use whichever route your app offers.

## Practice pack (optional, separate)

The Pelican practice deal (made-up people, made-up numbers) is optional separate data and is not part of this repo or either plugin. Use it only if you want to walk through a deal with nothing at stake.

## Good to know

- Each plugin's skills first read `shared-core/skills/HARD-RULES.md` inside the same plugin.
- Check every deadline against your contract. The plugins help; you decide.
