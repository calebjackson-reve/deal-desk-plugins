"""tc-contract-to-close: read a confirmed table, report changes and items due in 3 days.

Read-only. Never moves a date, never writes the table, never places calendar events.
"""
import copy
from datetime import date

ITEMS = ["deposit_receipt", "loan_application", "appraisal_ordered", "appraisal",
         "inspection_end", "inspection_response_seller", "inspection_response_buyer",
         "title_has_contract", "title_curative", "repairs_receipts", "walkthrough",
         "closing_disclosure", "act_of_sale", "recorded_act", "compliance_file"]
AT_RISK_FORM = {"loan_application": "Extension of Agreement to Buy or Sell",
                "appraisal": "Extension of Agreement to Buy or Sell",
                "title_curative": "Extension of Agreement to Buy or Sell",
                "repairs_receipts": "Extension of Agreement to Buy or Sell",
                "act_of_sale": "Extension of Agreement to Buy or Sell",
                "inspection_end": "Due Diligence and Inspection Response (GBRAR)",
                "inspection_response_seller": "Due Diligence and Inspection Response (GBRAR)",
                "inspection_response_buyer": "Due Diligence and Inspection Response (GBRAR)"}
OFFICIAL = ("Confirmed", "Done")


def pick_source(tracker_installed, tracker_table, uploaded_table):
    """Tracker's confirmed table first (read-only copy); else an uploaded/pasted one."""
    if tracker_installed and tracker_table:
        return {"source": "tracker", "rows": copy.deepcopy(tracker_table)}
    if uploaded_table:
        return {"source": "uploaded", "rows": copy.deepcopy(uploaded_table)}
    return None


def check(today, tracker_installed=False, tracker_table=None, uploaded_table=None,
          done=None, previous=None, window_days=3):
    src = pick_source(tracker_installed, tracker_table, uploaded_table)
    if not src:
        return {"status": "ask", "ask": "confirmed_table",
                "message": "No confirmed table. Install Tracker, upload the contract, "
                           "or paste a confirmed table."}
    done = done or {}
    previous = previous or {}
    t = date.fromisoformat(today)
    due, changes, unconfirmed = [], [], []
    for row in src["rows"]:
        if row.get("status") not in OFFICIAL:
            unconfirmed.append(row["id"])
            continue
        if row.get("date") is None:
            continue
        days = (date.fromisoformat(row["date"]) - t).days
        was = previous.get(row["id"])
        if was is not None and was != row["date"]:
            changes.append({"id": row["id"], "was": was, "now": row["date"]})
        if not done.get(row["id"]) and days <= window_days and row.get("status") != "Done":
            due.append({"id": row["id"], "date": row["date"], "days_left": days,
                        "overdue": days < 0})
    due.sort(key=lambda x: x["date"])
    suggest = None
    for d in due:
        if d["days_left"] <= 1 and d["id"] in AT_RISK_FORM:
            suggest = {"form": AT_RISK_FORM[d["id"]], "because": d["id"],
                       "note": "Suggestion only. The agent decides; no date is moved."}
            break
    return {"status": "ok", "source": src["source"], "changes": changes, "due_within_window": due,
            "unconfirmed_not_tracked": unconfirmed, "next_form": suggest,
            "quiet": not (changes or due), "calendar_writes": 0, "dates_moved": 0}
