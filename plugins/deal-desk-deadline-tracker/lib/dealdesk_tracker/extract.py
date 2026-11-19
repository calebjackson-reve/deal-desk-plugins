"""tracker-extract: pull fields and periods from a classified contract.
Missing is "missing", never a guess. Unclear acceptance stops everything."""
from dealdesk_core import deadlines

FIELDS = ("address", "parish", "price", "financing")
ROLES = ("buyers", "sellers", "other_agent", "lender", "title")
UNIT = {"calendar_days": "days", "business_days": "business days", "hours": "hours",
        "event": "days (latest date)", "title_curative": "days after act of sale",
        "working_days_before_act": "working days before act of sale",
        "calendar_days_before_act": "calendar days before act of sale",
        "fixed_date": "date"}


def _blank(v):
    return v is None or v == "" or v == []


def _forms():
    return deadlines.load_pack()["forms"]


def check_form(doc, forms=None):
    forms = forms if forms is not None else _forms()
    name = doc.get("form")
    if not name:
        return ["form_not_stated"]
    known = {f["name"]: f for f in forms}
    if name not in known:
        return ["unknown_form"]
    want = known[name].get("version_date")
    have = doc.get("form_version")
    if want and have and want != have:
        return ["wrong_form_version"]
    if want and not have:
        return ["form_version_not_found_on_document"]
    return []


def _party(p):
    if _blank(p):
        return "missing"
    return {k: (p.get(k) if not _blank(p.get(k)) else "missing")
            for k in ("name", "email", "phone")}


def extract(doc, forms=None):
    out = {"stop": False, "flags": check_form(doc, forms), "fields": {}, "missing": [],
           "parties": {}, "periods": []}
    for f in FIELDS:
        v = doc.get(f)
        out["fields"][f] = "missing" if _blank(v) else v
        if _blank(v):
            out["missing"].append(f)
    parties = doc.get("parties") or {}
    for r in ROLES:
        v = parties.get(r)
        if r in ("buyers", "sellers"):
            out["parties"][r] = [_party(p) for p in v] if v else "missing"
        else:
            out["parties"][r] = _party(v)
        if out["parties"][r] == "missing":
            out["missing"].append(r)
    acc = doc.get("acceptance") or doc.get("final_signature_at")
    out["fields"]["acceptance"] = acc or "missing"
    parsed = deadlines.parse_timestamp(acc, "America/Chicago") if acc else None
    if parsed is None or not doc.get("fully_signed"):
        out["stop"] = True
        out["reason"] = "acceptance_unclear"
        out["message"] = ("Acceptance date, time, or full signatures are unclear. "
                          "Ask the agent before going further.")
        if parsed is None:
            out["missing"].append("acceptance")
        return out
    for p in doc.get("periods", []):
        missing = p.get("type") != "fixed_date" and p.get("count") is None
        out["periods"].append({
            "id": p["id"], "type": p["type"], "unit": UNIT.get(p["type"], "missing"),
            "count": "missing" if missing else p.get("count", p.get("date")),
            "counts_from": p.get("counts_from") or p.get("anchor") or "missing",
            "source": p.get("source") or "missing",
            "status": "missing" if missing else "extracted"})
    return out
