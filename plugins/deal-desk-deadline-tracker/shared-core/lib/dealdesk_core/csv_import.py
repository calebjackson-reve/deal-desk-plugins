"""CRM CSV import: column guess, normalize, dedupe, preview plan.

plan_import() never writes. apply_plan() writes to the member's own client
list only when confirm=True, and only the rows the agent approved.
Dedupe order: email, then phone, then name + address.
"""
import csv
import io
import re

FIELD_ALIASES = {
    "name": ["name", "full name", "contact name", "client"],
    "first_name": ["first name", "first", "firstname", "given name"],
    "last_name": ["last name", "last", "lastname", "surname", "family name"],
    "email": ["email", "e-mail", "email address", "e-mail address"],
    "phone": ["phone", "mobile", "cell", "phone number", "mobile phone", "cell phone"],
    "address": ["address", "street", "street address", "address line 1"],
    "city": ["city"],
    "state": ["state", "st"],
    "zip": ["zip", "zip code", "postal code", "postcode"],
    "tags": ["tags", "tag", "labels"],
    "notes": ["notes", "note", "comments"],
}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def guess_mapping(headers):
    """Auto-guess header -> field. The agent can correct it."""
    mapping = {}
    for h in headers:
        key = h.strip().lower()
        for field, names in FIELD_ALIASES.items():
            if key in names and field not in mapping.values():
                mapping[h] = field
                break
    return mapping


def normalize_phone(value):
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 10:
        return "+1" + digits
    if len(digits) == 11 and digits.startswith("1"):
        return "+" + digits
    return ""


def normalize_email(value):
    return (value or "").strip().lower()


def _norm_text(value):
    return re.sub(r"[^a-z0-9 ]", "", (value or "").lower()).strip()


def normalize_row(raw, mapping):
    rec = {}
    for header, field in mapping.items():
        rec[field] = (raw.get(header) or "").strip()
    if not rec.get("name"):
        rec["name"] = " ".join(x for x in (rec.get("first_name"), rec.get("last_name")) if x)
    rec["email"] = normalize_email(rec.get("email"))
    rec["phone"] = normalize_phone(rec.get("phone"))
    return rec


def _name_addr_key(rec):
    n, a = _norm_text(rec.get("name")), _norm_text(rec.get("address"))
    return (n, a) if n and a else None


def _find_match(rec, clients):
    """email -> phone -> name+address. Returns (client, matched_by) or (None, None)."""
    if rec.get("email"):
        for c in clients:
            if c.get("email") == rec["email"]:
                return c, "email"
    if rec.get("phone"):
        for c in clients:
            if c.get("phone") == rec["phone"]:
                return c, "phone"
    key = _name_addr_key(rec)
    if key:
        for c in clients:
            if _name_addr_key(c) == key:
                return c, "name_address"
    return None, None


def plan_import(csv_text, existing_clients, mapping=None):
    """Return a preview plan. Pure: existing_clients is not modified."""
    reader = csv.DictReader(io.StringIO(csv_text))
    headers = reader.fieldnames or []
    mapping = mapping or guess_mapping(headers)
    working = [dict(c) for c in existing_clients]  # includes earlier CSV rows
    rows = []
    for i, raw in enumerate(reader, start=1):
        rec = normalize_row(raw, mapping)
        item = {"row": i, "record": rec, "matched_by": None, "existing_id": None}
        if not (rec.get("email") or rec.get("phone") or rec.get("name")):
            item.update(status="error", reason="no name, email, or phone")
        elif rec.get("email") and not EMAIL_RE.match(rec["email"]):
            item.update(status="error", reason="invalid email")
        else:
            match, by = _find_match(rec, working)
            if match is None:
                item["status"] = "new"
                working.append(dict(rec, id="csv-row-%d" % i))
            else:
                item["matched_by"] = by
                item["existing_id"] = match.get("id")
                in_file = str(match.get("id", "")).startswith("csv-row")
                item["status"] = "update" if by == "email" and not in_file else "possible_duplicate"
                item["choices"] = ["merge", "skip"]
        rows.append(item)
    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return {"mapping": mapping, "rows": rows, "counts": counts,
            "written": 0, "needs_confirm": True}


def apply_plan(plan, store, confirm=False, decisions=None):
    """Write approved rows into store (a list of client dicts).
    Without confirm=True nothing is written. Duplicates default to skip.
    Error rows are never written. Returns the import job record."""
    job = {"written": 0, "added": 0, "merged": 0, "skipped": 0, "confirmed": bool(confirm)}
    if confirm is not True:
        return job
    decisions = decisions or {}
    for item in plan["rows"]:
        st = item["status"]
        if st == "error":
            job["skipped"] += 1
        elif st == "new":
            store.append(dict(item["record"], id="c%d" % (len(store) + 1)))
            job["added"] += 1
        elif decisions.get(item["row"]) == "merge":
            for c in store:
                if c.get("id") == item["existing_id"]:
                    for k, v in item["record"].items():
                        if v and not c.get(k):
                            c[k] = v  # fill blanks only; never overwrite
                    job["merged"] += 1
                    break
        else:
            job["skipped"] += 1
    job["written"] = job["added"] + job["merged"]
    return job
