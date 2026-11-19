---
name: tracker-files
description: Use to file a matched document into the deal's folder plan with a consistent name, adding only and never deleting.
---

# tracker-files

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** Keep every deal's papers in the same place with the same names. Reference model: lib/dealdesk_tracker/files.py.

**Trigger.** A document was matched to a deal (or filed as "other").

## Steps

1. Folders per deal: Contract/, Addenda-Amendments/, Inspection/, Appraisal-Lending/, Title/, Other/. Practice deals go under Practice/ first.
2. Name the file YYYY-MM-DD_[doc type]_[address short].pdf, for example 2026-10-02_amendment_4321-Pelican.pdf.
3. Place the copy in the matching folder. If the name already exists, save a numbered copy (-2, -3). Never overwrite.
4. Tell the agent where it went, in one line.

## Stop rules

- Never delete, move out, or overwrite a file. This skill has no delete step.
- Unmatched or unreadable documents wait for the agent (tracker-ingest) and are not filed into a deal.
- Never share a folder or file with anyone.
