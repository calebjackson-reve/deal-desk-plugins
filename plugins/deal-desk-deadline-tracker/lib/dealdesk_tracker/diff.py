"""tracker-amendment-diff: recompute, show differences, apply nothing."""
from .table import build_rows, overwrite_payload, OFFICIAL


def make_diff(table, new_doc, holidays, tz="America/Chicago", now=None, placed=None):
    """table: DeadlineTable with current rows. placed: {row_id: event_id} for
    calendar impact. Nothing is applied here."""
    placed = placed or {}
    changes, unchanged = [], []
    for r in build_rows(new_doc, holidays, tz, now):
        cur = table.rows.get(r["id"])
        cur_val = cur["date"] if cur else None
        cur_time = cur["time"] if cur else None
        if cur and cur["status"] in OFFICIAL and (cur_val, cur_time) == (r["date"], r["time"]):
            unchanged.append(r["id"])
            continue
        if cur and not cur["status"] in OFFICIAL and (cur_val, cur_time) == (r["date"], r["time"]):
            unchanged.append(r["id"])
            continue
        changes.append({"id": r["id"], "deadline": r["deadline"],
                        "current": cur_val if cur else "none", "current_status":
                        cur["status"] if cur else "none", "proposed": r["date"] or "unconfirmed",
                        "proposed_time": r["time"], "source": r["source"],
                        "weekday": r["weekday"], "flag": r["flag"], "row": r,
                        "calendar_event_affected": r["id"] in placed})
    return {"applied": False, "changes": changes, "unchanged": unchanged,
            "affected_events": [c["id"] for c in changes if c["calendar_event_affected"]]}


def change_payload(table, change):
    return overwrite_payload(table.deal_id, change["id"], change["row"]["date"],
                             change["row"]["time"])


def apply_change(table, change, gate):
    """Apply exactly one change. Needs the gate when the row is already official."""
    r = change["row"]
    if r["date"] is None:
        return {"ok": False, "reason": "proposed_has_no_date"}
    if change["id"] not in table.rows:
        # a new row: it enters as Extracted; the agent confirms it separately
        table.rows[change["id"]] = dict(r)
        return {"ok": True, "added": True}
    cur = table.rows[change["id"]]
    was_official = cur["status"] in OFFICIAL
    res = table.overwrite(change["id"], {"date": r["date"], "time": r["time"],
                                         "weekday": r["weekday"], "flags": r["flags"],
                                         "flag": r["flag"]}, gate)
    if res["ok"] and was_official:
        cur["status"] = "Confirmed"
    return res
