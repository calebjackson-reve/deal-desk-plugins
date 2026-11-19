"""tracker-calendar: proposed events, gated writes on the member's own calendar,
ICS fallback. Events never carry guests. The client here is injected, so tests
use a fake and count writes."""
import hashlib
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from dealdesk_core import deadlines

from .table import OFFICIAL


def reminder_dates(deadline, holidays, lead_days=(2, 1), today=None):
    out = []
    d0 = date.fromisoformat(deadline)
    for n in lead_days:
        r = deadlines.prior_business_day(d0 - timedelta(days=n), holidays)
        if today and r < date.fromisoformat(today):
            continue
        if r.isoformat() not in out:
            out.append(r.isoformat())
    return out


def build_events(rows, short, holidays, lead_days=(2, 1), today=None):
    """Events for confirmed rows only."""
    events = []
    for r in rows:
        if r["status"] not in OFFICIAL or not r.get("date"):
            continue
        events.append({"row": r["id"], "title": "%s – %s" % (short, r["deadline"]),
                       "date": r["date"], "time": r.get("time"), "calendar": "own",
                       "guests": [],
                       "reminders": reminder_dates(r["date"], holidays, lead_days, today)})
    return events


class FakeCalendarClient:
    """Stand-in for a calendar connector. Records every write."""

    def __init__(self):
        self.writes = []
        self.events = {}

    def create(self, event):
        eid = "evt-%d" % (len(self.events) + 1)
        self.events[eid] = dict(event)
        self.writes.append(("create", eid))
        return eid

    def update(self, eid, event):
        self.events[eid] = dict(event)
        self.writes.append(("update", eid))

    def remove(self, eid):
        self.events.pop(eid, None)
        self.writes.append(("remove", eid))


class CalendarWriter:
    def __init__(self, gate, client):
        self.gate, self.client = gate, client
        self.first_done = set()
        self.auto = set()
        self.placed = {}   # (deal, row) -> event id

    def set_auto_place(self, deal_id):
        if deal_id not in self.first_done:
            return {"ok": False, "reason": "needs_a_first_gated_write_on_this_deal"}
        self.auto.add(deal_id)
        return {"ok": True}

    def write_events(self, deal_id, events):
        results = []
        for ev in events:
            if ev.get("guests"):
                results.append({"row": ev["row"], "written": False, "reason": "guests_never"})
                continue
            if deal_id in self.auto and deal_id in self.first_done:
                via = "auto_place"
            else:
                g = self.gate.attempt("calendar_write", ev)
                if not g["allowed"]:
                    results.append({"row": ev["row"], "written": False, "reason": g["reason"]})
                    continue
                via = "gate"
            eid = self.client.create(ev)
            self.placed[(deal_id, ev["row"])] = eid
            if via == "gate":
                self.first_done.add(deal_id)
            results.append({"row": ev["row"], "written": True, "via": via, "event_id": eid})
        return results

    def update_payload(self, deal_id, row_id, event):
        return {"op": "update", "deal": deal_id, "row": row_id, "event": event}

    def update_event(self, deal_id, row_id, event):
        eid = self.placed.get((deal_id, row_id))
        if eid is None:
            return {"written": False, "reason": "no_such_event"}
        g = self.gate.attempt("calendar_write", self.update_payload(deal_id, row_id, event))
        if not g["allowed"]:
            return {"written": False, "reason": g["reason"]}
        self.client.update(eid, event)
        return {"written": True, "event_id": eid}

    def remove_payload(self, deal_id, row_id):
        return {"op": "remove", "deal": deal_id, "row": row_id}

    def remove_event(self, deal_id, row_id):
        eid = self.placed.get((deal_id, row_id))
        if eid is None:
            return {"written": False, "reason": "no_such_event"}
        g = self.gate.attempt("calendar_write", self.remove_payload(deal_id, row_id))
        if not g["allowed"]:
            return {"written": False, "reason": g["reason"]}
        self.client.remove(eid)
        del self.placed[(deal_id, row_id)]
        return {"written": True}


def _esc(text):
    return str(text).replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")


def to_ics(events, tz="America/Chicago", stamp="20260101T000000Z"):
    """Valid iCalendar text. No organizer, no guests, no network."""
    zone = ZoneInfo(tz)
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Deal Desk//Tracker//EN",
             "CALSCALE:GREGORIAN"]
    for ev in events:
        uid = hashlib.sha1((ev["title"] + ev["date"]).encode()).hexdigest()[:16]
        lines += ["BEGIN:VEVENT", "UID:dd-%s" % uid, "DTSTAMP:%s" % stamp]
        d = date.fromisoformat(ev["date"])
        if ev.get("time"):
            hh, mm = ev["time"].split(":")
            start = datetime(d.year, d.month, d.day, int(hh), int(mm))
            end = start + timedelta(minutes=30)
            lines.append("DTSTART;TZID=%s:%s" % (tz, start.strftime("%Y%m%dT%H%M%S")))
            lines.append("DTEND;TZID=%s:%s" % (tz, end.strftime("%Y%m%dT%H%M%S")))
        else:
            lines.append("DTSTART;VALUE=DATE:%s" % d.strftime("%Y%m%d"))
            lines.append("DTEND;VALUE=DATE:%s" % (d + timedelta(days=1)).strftime("%Y%m%d"))
        lines.append("SUMMARY:%s" % _esc(ev["title"]))
        for r in ev.get("reminders", []):
            rd = date.fromisoformat(r)
            at = datetime(rd.year, rd.month, rd.day, 9, 0, tzinfo=zone).astimezone(
                ZoneInfo("UTC"))
            lines += ["BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:%s" % _esc(ev["title"]),
                      "TRIGGER;VALUE=DATE-TIME:%s" % at.strftime("%Y%m%dT%H%M%SZ"),
                      "END:VALARM"]
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
