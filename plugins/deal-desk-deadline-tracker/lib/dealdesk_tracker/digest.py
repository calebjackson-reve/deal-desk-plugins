"""tracker-digest: for the member only."""
from datetime import date, timedelta

from .table import OFFICIAL


def build_digest(deals, today, awaiting=None, tc_installed=False, days=3):
    """deals: {deal_id: [rows]}. Window is today through today + days."""
    t0 = date.fromisoformat(today)
    t1 = t0 + timedelta(days=days)
    due, flags, unconfirmed = [], [], []
    for deal_id, rows in sorted(deals.items()):
        for r in rows:
            item = {"deal": deal_id, "deadline": r["deadline"], "date": r.get("date"),
                    "time": r.get("time"), "status": r["status"]}
            if r.get("date") and t0 <= date.fromisoformat(r["date"]) <= t1 \
                    and r["status"] in OFFICIAL + ("Extracted",):
                due.append(item)
            if r.get("flags") and r["status"] not in ("Done", "Waived"):
                flags.append(dict(item, flags=r["flags"]))
            if r["status"] == "Extracted":
                unconfirmed.append(item)
    due.sort(key=lambda i: (i["date"], i["deal"]))
    drafts = []
    if tc_installed:
        drafts = [{"kind": "client_heads_up_draft", "to": "member", "deal": i["deal"],
                   "text": "Draft for you to review: %s is due %s." % (i["deadline"], i["date"])}
                  for i in due if i["status"] in OFFICIAL]
    return {"audience": "member", "recipients": ["member"], "window": [t0.isoformat(), t1.isoformat()],
            "due": due, "flags": flags, "unconfirmed": unconfirmed,
            "awaiting_match": list(awaiting or []), "client_drafts": drafts}
