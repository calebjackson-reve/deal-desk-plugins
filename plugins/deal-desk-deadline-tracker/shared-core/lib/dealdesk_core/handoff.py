"""Tracker <-> TC handoff (spec section 4).

Tracker owns the deadline table. TC gets a read-only view and never writes it.
A TC change request becomes a proposal for Tracker through the gate; it changes
nothing by itself. Connections are made once per member and reused.
"""
import copy

OFFICIAL = ("Confirmed", "Done")
# table row id -> Deal Summary key date name
KEY_DATES = {"deposit_receipt": "deposit", "inspection_end": "inspection_dd_end",
             "appraisal": "appraisal", "loan_application": "financing",
             "act_of_sale": "act_of_sale", "walkthrough": "walkthrough",
             "title_curative": "title_extension"}


class ConnectionRegistry:
    """One member's connections. A second plugin reuses what is already connected."""

    def __init__(self):
        self.connected = {}
        self.connect_count = {}
        self.reused_by = {}

    def ensure(self, service, plugin):
        if service in self.connected:
            self.reused_by.setdefault(service, []).append(plugin)
            return {"service": service, "reused": True, "asked_member": False}
        self.connected[service] = plugin
        self.connect_count[service] = self.connect_count.get(service, 0) + 1
        return {"service": service, "reused": False, "asked_member": True}


class TableView:
    """Read-only copy of Tracker's table for TC. Has no write methods."""

    def __init__(self, rows):
        self._rows = tuple(copy.deepcopy(r) for r in rows)

    def rows(self):
        return copy.deepcopy(list(self._rows))

    def confirmed(self):
        return [r for r in self.rows() if r.get("status") in OFFICIAL and r.get("date")]

    def request_change(self, gate, deal_id, row_id, date, time=None):
        """TC change request -> proposed diff for Tracker, through the gate."""
        payload = {"deal": deal_id, "row": row_id, "date": date, "time": time}
        p = gate.propose("overwrite_confirmed", payload)
        return {"type": "proposed_diff", "to": "tracker", "applied": False,
                "proposal": p, "payload": payload}


def deal_summary(deal, view, acceptance, next_form=None, why="", notes=""):
    """Build the Deal Summary. Key dates come from confirmed rows only."""
    keys, skipped = {}, []
    for r in view.rows():
        name = KEY_DATES.get(r["id"])
        if not name:
            continue
        if r.get("status") in OFFICIAL and r.get("date"):
            keys[name] = {"date": r["date"], "time": r.get("time")}
        else:
            skipped.append(r["id"])
    return {"address": deal["address"], "parish": deal.get("parish"), "side": deal.get("side"),
            "price": deal.get("price"), "financing": deal.get("financing"),
            "parties": copy.deepcopy(deal.get("parties", {})),
            "acceptance": acceptance, "key_dates": keys, "unconfirmed_left_out": skipped,
            "next_form": next_form, "why": why, "notes": notes}


def summary_to_facts(summary):
    """What tc-open-deal / tc-fill-form read from the Deal Summary."""
    return {k: copy.deepcopy(summary[k]) for k in
            ("address", "parish", "side", "price", "financing", "parties")
            if summary.get(k) is not None}


def dates_changed(before_rows, after_rows, deal_id):
    """Tracker -> TC: a suggestion and a draft line only. Nothing is sent or moved."""
    was = {r["id"]: r.get("date") for r in before_rows}
    moved = [{"id": r["id"], "was": was.get(r["id"]), "now": r.get("date")}
             for r in after_rows if r["id"] in was and was[r["id"]] != r.get("date")]
    if not moved:
        return {"suggestion": None, "sent": False}
    return {"suggestion": "Dates changed on %s; an extension or amendment may be needed." % deal_id,
            "moved": moved, "draft_only": True, "sent": False}
