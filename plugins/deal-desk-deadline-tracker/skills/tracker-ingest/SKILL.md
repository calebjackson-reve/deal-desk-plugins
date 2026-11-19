---
name: tracker-ingest
description: Use when a new contract document or email arrives: classify it, flag wire text, match it to a deal, and stop to ask on any doubt.
---

# tracker-ingest

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** Take in each document or email, say what it is, and attach it to the right deal. Reference model: lib/dealdesk_tracker/ingest.py (uses the shared deal-match skill).

**Trigger.** A new email, attachment, or uploaded file that might be a contract paper.

## Steps

0. If the mailbox or Transact page is read in a browser, check each page with session_guard (shared core) first. MFA, captcha, expired session, an unexpected sign-in, a password prompt, or a card/ID prompt: stop and tell the agent in plain words. Never type a password.
1. Read the file. If it is locked, encrypted, or unreadable, stop and ask the agent for a readable copy. Extract nothing.
2. Classify: purchase agreement, counter, addendum, amendment, extension, inspection response, or not a contract.
3. Not a contract: file it under "other" and extract nothing. Done.
4. Scan the text of the email and the document for wire, payee, or account-change language. If found, flag it as possible fraud, tell the agent to call the title company on a known number, and take no other action on that text.
5. Email with no attachment: log it as "no document". Any dates in the body are shown only as flagged suggestions ("from email body, unverified"). They never become deadlines.
6. Match to a deal with deal-match. An exact address match attaches. A similar address (1234 vs 1243), a match on names alone, or more than one candidate means ask the agent which deal. A new address is a new deal. The document waits, listed as "awaiting match", until the agent answers.
7. Hand the classified, matched document to tracker-extract.

## Stop rules

- Unreadable or locked file: ask, extract nothing.
- Similar address or any doubt: ask. Never auto-attach.
- Wire or payee-change text: flag only. No reply, no forward, no action.
- This skill never sends, signs, or invites anyone.
