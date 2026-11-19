---
name: member-setup
description: Use on first install, 'set up Deal Desk', when a plugin is added, or when any skill hits a missing setting: collects per-member settings, connects services, runs the Pelican practice pass.
---

# member-setup

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** Per-member settings, connectors, vault check, and the practice-deal pass test.

**Trigger.** First install, "set up Deal Desk", a new plugin added, or a missing setting hit by any skill.

## Steps

1. Detect installed plugins and show only the connectors they need.
2. Walk through connecting each one (see the connectors skill). The member saves logins in their own vault. Check that the vault entry exists, never what is in it.
3. Collect settings: name, brokerage, office, team, license block, signature block, review email (their own), time zone (default America/Chicago), voice (short style guide plus a never-say list, captured from 3 sample emails the member pastes), forms list (name, code, version date, editable), market pack (default Louisiana / Baton Rouge), never-use names list, commission display format, fields left blank for the agent, reminder lead times (default 2 days and 1 day before), and the form profile (`profile`): agent_name, agent_license, brokerage_license, agent_phone, agent_email, brokerage_phone, brokerage_email, sellers_agent, designated_agent_name, designated_agent_license, designated_agent_phone, designated_agent_email. Transact does not auto-fill these on the Agreement to Buy or Sell, so TC fills them from here. Add any that are absent; a value the member does not give stays empty and is listed in the form report, never guessed.
3a. Templates (Deal Desk TC): the default packet templates are read-only shared data. The member may add a template or override a default in their own settings (forms need a code or a name; no send, sign, invite, Prepare Signing, Next, or submit step is ever allowed; the validator rejects it). Custom templates are stored in this member's bot only, are never visible to another member, and setup never copies them.
4. Run the Pelican practice deal for each installed plugin, using the practice pack (`deal-desk-practice-<version>.zip`, folder `practice/`). Tell the member it is made-up data kept apart from live deals.
5. Mark the member onboarded only on a pass.

## Stop rules

- Live (non-practice) work stays blocked until required connectors and the pass test are done.
- Never copy settings from another member or from a template holding real data.
- Required connectors: Tracker needs email (Gmail and/or Outlook), calendar (Google or Outlook, ICS file fallback), and Flexmls. Transact is optional for Tracker. TC needs Transact and Flexmls. Brokerage system is optional for both. Compliance is handled inside Transact's Compliance tab; the member setting `compliance_fallback_brokerage_system` (off by default) sends compliance work to the Brokerage system path instead, only for offices that do not use Transact compliance. Ask once during setup; leave it off unless the member says their office does not use Transact compliance. With both plugins installed, each service is connected once and reused.

## Hard rules

- Drafts and prep only. Never send, sign, invite a signer, or tick a certifying box. Never submit a form to a client or other party. (Compliance submit in the Transact Compliance tab (or the optional Brokerage system fallback) is an in-system step that needs your yes through the review gate. Compliance uploads into your own Transact file's Compliance tab run automatically with no yes, under guards; the optional Brokerage system fallback upload still needs your yes.) An OK never changes that.
- Never type a password. Captcha, MFA, an unexpected sign-in, or a page asking for a password, card, or ID number: stop and tell the agent.
- Demo data only in practice runs: 4321 Pretend Pelican Lane, Zachary LA 70791.
