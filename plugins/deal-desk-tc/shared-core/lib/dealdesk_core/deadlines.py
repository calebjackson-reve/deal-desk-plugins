"""Deadline math for the Louisiana market pack (pure functions, stdlib only).

compute_deadline(rule, acceptance, holidays, act_of_sale, tz) follows the
market-louisiana skill:
  * the day after acceptance is day 1 (9/30 + 13 calendar days = 10/13)
  * business days are Mon-Fri minus holidays; the act of sale day does not count
  * hours windows count to the minute in the member's time zone
  * weekend/holiday deadlines are FLAGGED, not rolled, unless the rule says
    the contract rolls them (rule["roll"])
  * title curative days count from the act of sale and may run past it
  * a period the form does not state is "unconfirmed: ask agent"
"""
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_PACK = (Path(__file__).resolve().parents[2] / "skills"
                / "market-louisiana" / "market-pack.json")
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "Saturday", "Sunday"]


def load_pack(path=None):
    with open(path or DEFAULT_PACK, encoding="utf-8") as fh:
        return json.load(fh)


def load_holidays(path=None):
    """Holiday dates (set of datetime.date) read from the market pack JSON."""
    pack = load_pack(path)
    return {date.fromisoformat(h["date"]) for h in pack["holidays"]}


def _as_date(value):
    if value is None or isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value)[:10])


def is_business_day(d, holidays):
    return d.weekday() < 5 and d not in holidays


def next_business_day(d, holidays):
    while not is_business_day(d, holidays):
        d += timedelta(days=1)
    return d


def prior_business_day(d, holidays):
    while not is_business_day(d, holidays):
        d -= timedelta(days=1)
    return d


def add_business_days(start, n, holidays):
    """Move n business days after start (start itself is not counted)."""
    d = start
    step = 1 if n >= 0 else -1
    left = abs(n)
    while left:
        d += timedelta(days=step)
        if is_business_day(d, holidays):
            left -= 1
    return d


def parse_timestamp(value, tz):
    """Parse an ISO timestamp. Returns aware datetime in tz, or None if the
    value is empty or carries no time of day."""
    if not value:
        return None
    text = str(value).strip()
    if "T" not in text and " " not in text:
        return None  # date only: no time, cannot be an acceptance clock
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    zone = ZoneInfo(tz)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=zone)
    return dt.astimezone(zone)


def controlling_acceptance(documents):
    """Counters on counters: the last fully signed document controls.
    Each document: {id, kind, fully_signed (bool), final_signature_at}.
    Returns the controlling document or None; earlier ones are history."""
    signed = [d for d in documents if d.get("fully_signed") and d.get("final_signature_at")]
    if not signed:
        return None
    return max(signed, key=lambda d: d["final_signature_at"])


def _result(d, tz_time=None):
    out = {"stop": False, "date": d.isoformat(), "weekday": WEEKDAYS[d.weekday()],
           "flags": [], "status": "extracted"}
    if tz_time is not None:
        out["time"] = tz_time.strftime("%H:%M")
        out["timestamp"] = tz_time.isoformat()
    return out


# History and Timeline times in Transact can read about 1 hour ahead of the member's Central time.
UNTRUSTED_TIME_SOURCES = {"history", "timeline", "transact history", "transact timeline"}


def compute_deadline(rule, acceptance, holidays, act_of_sale=None,
                     tz="America/Chicago", now=None, source=None):
    """Compute one deadline. Returns a dict; {"stop": True, ...} when the
    clock cannot be trusted. Never guesses a missing period. A clock read from Transact
    History or Timeline is refused (`source`): only the signed contract / Details count."""
    if source and str(source).strip().lower() in UNTRUSTED_TIME_SOURCES:
        return {"stop": True, "reason": "untrusted_time_source", "source": source,
                "message": "History and Timeline times can be offset (about 1 hour ahead). "
                           "Deadlines come only from the signed contract or Details."}
    holidays = {_as_date(h) for h in holidays}
    rtype = rule.get("type")
    act = _as_date(act_of_sale)

    # fixed dates and title curative do not need an acceptance clock for
    # their own math, everything else does.
    needs_clock = rtype in ("calendar_days", "business_days", "hours", "event")
    acc = parse_timestamp(acceptance, tz) if acceptance else None
    if needs_clock:
        if acc is None:
            reason = "acceptance_missing" if not acceptance else "acceptance_has_no_time"
            return {"stop": True, "reason": reason,
                    "message": "Acceptance date and time are required. Ask the agent."}
        if now is not None:
            now_dt = parse_timestamp(now, tz)
            if now_dt is not None and acc > now_dt:
                return {"stop": True, "reason": "acceptance_in_future",
                        "message": "Acceptance is in the future. Ask the agent."}

    if rtype != "fixed_date" and rule.get("count") is None:
        return {"stop": False, "date": None, "status": "unconfirmed",
                "flags": ["unconfirmed: ask agent"],
                "message": "The form does not state this period. Ask the agent."}

    notes = []
    time_part = None
    if rtype == "fixed_date":
        d = _as_date(rule["date"])
    elif rtype == "calendar_days":
        d = acc.date() + timedelta(days=int(rule["count"]))
    elif rtype == "business_days":
        d = add_business_days(acc.date(), int(rule["count"]), holidays)
    elif rtype == "hours":
        anchor = parse_timestamp(rule.get("anchor"), tz) or acc
        if anchor is None:
            return {"stop": True, "reason": "anchor_missing",
                    "message": "Delivery timestamp is required."}
        # add hours in local wall time so the clock minute is kept across DST
        zone = ZoneInfo(tz)
        local = anchor.astimezone(zone).replace(tzinfo=None)
        end = (local + timedelta(hours=int(rule["count"]))).replace(tzinfo=zone)
        d, time_part = end.date(), end
    elif rtype == "event":
        # Event-based: show the latest possible date, set on delivery.
        d = acc.date() + timedelta(days=int(rule["count"]))
        notes.append("set on delivery")
    elif rtype == "title_curative":
        if act is None:
            return {"stop": True, "reason": "act_of_sale_missing",
                    "message": "Act of sale date is required for title days."}
        d = act + timedelta(days=int(rule["count"]))
        notes.append("title_past_act_expected")
    elif rtype == "working_days_before_act":
        if act is None:
            return {"stop": True, "reason": "act_of_sale_missing",
                    "message": "Act of sale date is required."}
        d = add_business_days(act, -int(rule["count"]), holidays)
    elif rtype == "calendar_days_before_act":
        # calendar days counted back from the act of sale (WDI, final walk-through)
        if act is None:
            return {"stop": True, "reason": "act_of_sale_missing",
                    "message": "Act of sale date is required."}
        d = act - timedelta(days=int(rule["count"]))
    else:
        return {"stop": True, "reason": "unknown_rule_type",
                "message": "Unknown rule type: " + str(rtype)}

    res = _result(d, time_part)
    res["notes"] = notes
    if "set on delivery" in notes:
        res["set_on_delivery"] = True

    # weekend / holiday: flag, never roll silently
    if d.weekday() >= 5:
        res["flags"].append("weekend")
    if d in holidays:
        res["flags"].append("holiday")
    if res["flags"] and rule.get("roll") in ("next_business_day", "prior_business_day"):
        fn = next_business_day if rule["roll"] == "next_business_day" else prior_business_day
        rolled = fn(d, holidays)
        res["unrolled_date"] = d.isoformat()
        res["date"] = rolled.isoformat()
        res["weekday"] = WEEKDAYS[rolled.weekday()]
        res["flags"].append("rolled_per_contract")
        d = rolled
    # ends after the act (title curative runs past on purpose)
    if act is not None and d > act and rtype != "title_curative":
        res["flags"].append("ends_after_act")
    if now is not None:
        now_dt = parse_timestamp(now, tz)
        if now_dt is not None and d < now_dt.date():
            res["flags"].append("past")
    return res


def compute_from_document(doc, period_id, holidays, tz="America/Chicago", now=None):
    """Compute one named period from a structured contract stand-in."""
    for p in doc.get("periods", []):
        if p["id"] == period_id:
            rule = dict(p)
            return compute_deadline(rule, doc.get("acceptance"), holidays,
                                    doc.get("act_of_sale"), tz, now)
    return {"stop": False, "date": None, "status": "missing", "flags": ["missing"],
            "message": "Period not found in document."}
