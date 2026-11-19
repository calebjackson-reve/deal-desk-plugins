"""Client enrichment: suggestions with a source, agent accept/reject.

  * nothing changes on a client record without an explicit accept
  * a rejected value is remembered and not re-proposed unless the source
    value (version) changes
  * agent-confirmed values win over later syncs
"""


class EnrichmentStore:
    def __init__(self):
        self.clients = {}      # id -> {field: value}
        self.confirmed = {}    # (id, field) -> value
        self.rejected = {}     # (id, field, proposed) -> source_version
        self.suggestions = {}  # sid -> suggestion
        self._n = 0

    def add_client(self, cid, **fields):
        self.clients[cid] = dict(fields)

    def propose(self, cid, field, proposed, source, confidence="medium",
                source_version=None):
        cur = self.clients.get(cid, {}).get(field)
        if cur == proposed:
            return None
        rej = self.rejected.get((cid, field, proposed), "__none__")
        if rej != "__none__" and rej == source_version:
            return None  # rejected before and the source value has not changed
        self._n += 1
        sid = "s%d" % self._n
        s = {"id": sid, "client": cid, "field": field, "current": cur,
             "proposed": proposed, "source": source, "confidence": confidence,
             "source_version": source_version,
             "replaces_confirmed": (cid, field) in self.confirmed}
        self.suggestions[sid] = s
        return s

    def accept(self, sid):
        s = self.suggestions.pop(sid)
        self.clients[s["client"]][s["field"]] = s["proposed"]
        self.confirmed[(s["client"], s["field"])] = s["proposed"]
        return s

    def reject(self, sid):
        s = self.suggestions.pop(sid)
        self.rejected[(s["client"], s["field"], s["proposed"])] = s["source_version"]
        return s

    def sync(self, cid, field, value):
        """A background sync/extraction. Confirmed values always win."""
        if (cid, field) in self.confirmed:
            return {"applied": False, "reason": "confirmed_wins"}
        self.clients.setdefault(cid, {})[field] = value
        return {"applied": True}
