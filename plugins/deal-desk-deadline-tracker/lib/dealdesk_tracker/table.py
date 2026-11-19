"""tracker-deadline-table: rows, confirmation, counters on counters."""
from dealdesk_core import deadlines

OFFICIAL = ("Confirmed", "Done")
STATUSES = ("Extracted", "Confirmed", "Done", "Waived")
COUNTS_FROM = {"calendar_days": "acceptance", "business_days": "acceptance",
               "event": "acceptance (set on delivery)", "title_curative": "act of sale",
               "working_days_before_act": "act of sale", "calendar_days_before_act": "act of sale",
               "fixed_date": "fixed date"}


def label(period_id):
    return period_id.replace("_", " ").capitalize()


def build_rows(doc, holidays, tz="America/Chicago", now=None):
    rows = []
    for p in doc.get("periods", []):
        res = deadlines.compute_from_document(doc, p["id"], holidays, tz, now)
        flags = list(res.get("flags", []))
        if res.get("stop"):
            flags.append("stop: " + res.get("reason", "unknown"))
        if res.get("set_on_delivery"):
            flags.append("set on delivery")
        counts = p.get("counts_from") or (
            "delivery time %s" % p["anchor"] if p.get("anchor") else
            COUNTS_FROM.get(p["type"], "missing"))
        rows.append({"id": p["id"], "deadline": label(p["id"]), "date": res.get("date"),
                     "time": res.get("time"), "weekday": res.get("weekday"),
                     "counts_from": counts, "source": p.get("source") or "missing",
                     "status": "Extracted", "flags": flags, "flag": "; ".join(flags),
                     "history": []})
    return rows


def controlling(documents):
    """Last fully signed document controls; earlier signed ones are history."""
    doc = deadlines.controlling_acceptance(documents)
    if doc is None:
        return {"controlling_id": None, "history": []}
    hist = sorted((d for d in documents if d.get("fully_signed") and d is not doc),
                  key=lambda d: d["final_signature_at"])
    return {"controlling_id": doc["id"], "history": [d["id"] for d in hist],
            "acceptance": doc["final_signature_at"]}


def overwrite_payload(deal_id, row_id, date, time=None):
    return {"deal": deal_id, "row": row_id, "date": date, "time": time}


class DeadlineTable:
    def __init__(self, deal_id):
        self.deal_id = deal_id
        self.rows = {}

    def load(self, rows):
        for r in rows:
            self.rows[r["id"]] = dict(r)

    def row(self, row_id):
        return self.rows[row_id]

    def confirm(self, row_id):
        r = self.rows[row_id]
        if not r["date"]:
            return {"ok": False, "reason": "no_date_cannot_confirm"}
        r["status"] = "Confirmed"
        return {"ok": True}

    def set_status(self, row_id, status):
        r = self.rows[row_id]
        if status not in ("Done", "Waived") or r["status"] not in ("Confirmed", "Done"):
            return {"ok": False, "reason": "only_confirmed_rows_can_be_done_or_waived"}
        r["status"] = status
        return {"ok": True}

    def official(self):
        return [r for r in self.rows.values() if r["status"] in OFFICIAL]

    def overwrite(self, row_id, new, gate):
        """Replace date/time. A confirmed row needs a valid gate approval."""
        r = self.rows[row_id]
        if r["status"] in OFFICIAL + ("Waived",):
            g = gate.attempt("overwrite_confirmed", overwrite_payload(
                self.deal_id, row_id, new["date"], new.get("time")))
            if not g["allowed"]:
                return {"ok": False, "reason": g["reason"]}
        r["history"].append({"date": r["date"], "time": r["time"]})
        for k in ("date", "time", "weekday", "flags", "flag"):
            if k in new:
                r[k] = new[k]
        return {"ok": True}
