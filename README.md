# Deal Desk

Deal Desk is two plugins for Cursor and Grok Bot, built for real estate agents by Caleb Jackson.

| Plugin | What it does |
|---|---|
| **Deal Desk Deadline Tracker** (`plugins/deal-desk-deadline-tracker`) | Reads your contract papers, builds a deadline table with sources, proposes calendar events, shows amendment changes before any date moves, and writes a morning digest. |
| **Deal Desk TC** (`plugins/deal-desk-tc`) | Transaction coordination in your own signed-in Transact: opens files, fills and checks forms, preps signing drafts, and files compliance. |

Each plugin bundles its own copy of the shared core (hard rules, member setup, review gate, Louisiana market pack). You do not install a separate core plugin. If you install both plugins you will have two identical copies of the shared core.

## Drafts only

Deal Desk never sends, signs, submits, or invites anyone. Every write waits for the agent's yes in chat. Check every deadline against your contract; the plugins help, you decide.

## Install

See [INSTALL-ON-GROK-BOT.md](INSTALL-ON-GROK-BOT.md).

## Layout

```
.cursor-plugin/marketplace.json          lists both plugins
plugins/deal-desk-deadline-tracker/      Deadline Tracker
plugins/deal-desk-tc/                    TC
```

The intended home of this repo is https://github.com/calebjackson-reve/deal-desk-plugins.

## License

All rights reserved. See [LICENSE](LICENSE).
