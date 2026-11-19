---
name: connectors
description: Use when connecting or reconnecting email, calendar, Transact, Flexmls, or the optional Brokerage system; defines the connector interface and failure handling.
---

# connectors

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** Connector notes and the common interface every service sits behind.

**Trigger.** Onboarding, a connector failure, or any skill that needs a service.

## Steps

1. Email: official Gmail / Outlook connectors with read scopes. Tracker never uses send scopes.
2. Calendar: official Google / Outlook connectors. Events go on the member's own calendar with no attendees. ICS file as the fallback.
3. Transact / Flexmls: a public third-party Transact API was not confirmed, and Flexmls's API platform needs MLS approval and a data license. Verify both. Until granted, use only the member's own signed-in browser with the bot working visibly, user-initiated official exports or PDF downloads uploaded to the bot, or emails forwarded to a mailbox the member controls.
4. Put each connector behind one interface: authorize, pull, fetchDocument, disconnect, so official API access drops in later. Placeholders until supplied: <TRANSACT_CLIENT_ID>, <FLEXMLS_CLIENT_ID>.
5. Brokerage system (optional, off by default): used for the compliance file only when the member setting `compliance_fallback_brokerage_system` is on (its upload stays gated: it needs the agent's yes, unlike the automatic Transact Compliance tab upload) (office does not use Transact compliance); the primary compliance path is Transact's Compliance tab, with no separate dashboard or desktop app. Official API if confirmed. Otherwise the contact CSV export through crm-csv-import.
6. Before each pull or fetch on a signed-in page, check the page state with lib/dealdesk_core/session_guard.py. A stop result (mfa, captcha, expired_session, unexpected_sign_in, password_prompt, card_or_id_prompt) ends the step cleanly with its note to the agent; the member completes the sign-in step themselves.
7. Failures: expired session -> "Reconnect" (the member signs in; wait). MFA or captcha -> stop. Permission denied -> name the missing scope. Timeouts -> retry with backoff (max 3). Partial sync -> show counts.

## Stop rules

- Official APIs/OAuth or host connectors plus the member's own vault logins only. Never credential scraping, stored passwords driving headless logins, session-cookie replay, or ToS-violating automation.
- Logs record the error class only, never client data.
