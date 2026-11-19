---
name: crm-csv-import
description: Use when the member uploads a contact CSV from any CRM or Brokerage system export: maps columns, dedupes by email then phone then name+address, previews, and writes only after confirm.
---

# crm-csv-import

Hard rules apply. Read `shared-core/skills/HARD-RULES.md` first.

**Purpose.** Bring contacts in safely. Reference model: lib/dealdesk_core/csv_import.py.

**Trigger.** The member uploads a contact CSV.

## Steps

1. Auto-guess mappings for common headers (Name, First/Last, Email, Phone/Mobile, Address/City/State/Zip, Tags, Notes). The agent corrects them.
2. Normalize: trim, lowercase emails, E.164 phones.
3. Dedupe against existing clients by email, then phone, then name + address.
4. Preview each row as New / Update / Possible duplicate / Error, with merge or skip per duplicate.
5. Record the import job and its counts. Offer enrichment.

## Stop rules

- Nothing is written before the agent confirms the preview.
- Duplicates default to skip. Merge fills blanks only and never overwrites.
- Error rows are never written.
