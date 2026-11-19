"""One member session wiring the tracker pieces together (used by the tests and
the onboarding pass). Every change to confirmed data or the calendar goes
through the review gate."""
from dealdesk_core import deadlines
from dealdesk_core.gate import ReviewGate, action_hash

from . import calendar as cal
from . import diff as diffmod
from . import digest, extract, files, ingest, table


class Session:
    def __init__(self, deals=None, today="2026-10-01", tz="America/Chicago",
                 tc_installed=False, practice=False):
        self.holidays = deadlines.load_holidays()
        self.deals = list(deals or [])
        self.today, self.tz, self.tc, self.practice = today, tz, tc_installed, practice
        self.gate = ReviewGate()
        self.client = cal.FakeCalendarClient()
        self.writer = cal.CalendarWriter(self.gate, self.client)
        self.tables, self.awaiting, self.pending = {}, [], []
        self.store = files.FileStore()
        self.docs = {}

    # --- steps -------------------------------------------------------
    def ingest(self, doc=None, email=None, create_deal=False):
        if email is not None:
            r = ingest.ingest_email(email, self.deals)
            for d in r["documents"]:
                if d["decision"] == "ask":
                    self.awaiting.append(d.get("filename") or "document")
            return r
        r = ingest.ingest_document(doc, self.deals)
        if r["decision"] == "ask":
            self.awaiting.append(doc.get("filename") or doc.get("address") or "document")
        if r["decision"] == "new_deal" and create_deal:
            did = "deal-" + files.address_short(doc["address"]).replace(" ", "-").lower()
            self.deals.append({"id": did, "address": doc["address"], "parties": [
                p["name"] for p in doc["parties"].get("buyers", [])], "mls": "",
                "transact_id": ""})
            r["deal_id"] = did
        return r

    def extract(self, doc, forms=None):
        return extract.extract(doc, forms)

    def make_table(self, deal_id, doc):
        t = table.DeadlineTable(deal_id)
        t.load(table.build_rows(doc, self.holidays, self.tz, self.today))
        self.tables[deal_id] = t
        return {"rows": list(t.rows.values())}

    def confirm(self, deal_id, ids):
        return {i: self.tables[deal_id].confirm(i) for i in ids}

    def _pend(self, kind, payload):
        h = action_hash(kind, payload)
        self.pending.append({"kind": kind, "payload": payload, "hash": h})
        return len(self.pending) - 1

    def say(self, source, text, target=-1):
        return self.gate.record_message(source, text, self.pending[target]["hash"])

    def propose_events(self, deal_id, lead_days=(2, 1)):
        short = files.address_short(self._address(deal_id))
        evs = cal.build_events(list(self.tables[deal_id].rows.values()), short,
                               self.holidays, lead_days, self.today)
        idx = [self._pend("calendar_write", e) for e in evs]
        return {"events": evs, "pending_index": idx}

    def _address(self, deal_id):
        for d in self.deals:
            if d["id"] == deal_id:
                return d["address"]
        return deal_id

    def propose_overwrite(self, deal_id, row_id, date, time=None):
        return {"pending_index": self._pend("overwrite_confirmed",
                                            table.overwrite_payload(deal_id, row_id, date, time))}

    def write_events(self, deal_id, only=None):
        evs = cal.build_events(list(self.tables[deal_id].rows.values()),
                               files.address_short(self._address(deal_id)),
                               self.holidays, (2, 1), self.today)
        if only:
            evs = [e for e in evs if e["row"] in only]
        return {"results": self.writer.write_events(deal_id, evs)}

    def ics(self, deal_id):
        evs = cal.build_events(list(self.tables[deal_id].rows.values()),
                               files.address_short(self._address(deal_id)),
                               self.holidays, (2, 1), self.today)
        return {"ics": cal.to_ics(evs, self.tz)}

    def diff(self, deal_id, doc):
        t = self.tables[deal_id]
        placed = {row: eid for (d, row), eid in self.writer.placed.items() if d == deal_id}
        self._diff = diffmod.make_diff(t, doc, self.holidays, self.tz, self.today, placed)
        for c in self._diff["changes"]:
            c["pending_index"] = self._pend("overwrite_confirmed",
                                            diffmod.change_payload(t, c))
        return self._diff

    def apply_change(self, deal_id, row_id):
        c = next(c for c in self._diff["changes"] if c["id"] == row_id)
        return diffmod.apply_change(self.tables[deal_id], c, self.gate)

    def propose_event_update(self, deal_id, row_id):
        row = self.tables[deal_id].rows[row_id]
        ev = cal.build_events([row], files.address_short(self._address(deal_id)),
                              self.holidays, (2, 1), self.today)
        if not ev:
            return {"event": None}
        idx = self._pend("calendar_write", self.writer.update_payload(deal_id, row_id, ev[0]))
        return {"event": ev[0], "pending_index": idx}

    def update_event(self, deal_id, row_id):
        row = self.tables[deal_id].rows[row_id]
        ev = cal.build_events([row], files.address_short(self._address(deal_id)),
                              self.holidays, (2, 1), self.today)[0]
        return self.writer.update_event(deal_id, row_id, ev)

    def file_doc(self, doc_class, date_iso, address):
        return self.store.file(files.plan(date_iso, doc_class, address, self.practice))

    def digest(self, today=None):
        return digest.build_digest({k: list(t.rows.values()) for k, t in self.tables.items()},
                                   today or self.today, self.awaiting, self.tc)
