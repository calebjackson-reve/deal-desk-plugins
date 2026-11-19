"""Per-member event ledger and the review-copy rule.

The ledger records what a bot did on its own. It has no way to record a send,
sign, submit, or invite: there is no such capability, so asking for one raises.

The one outward-addressed thing is a review-copy DRAFT. It may be addressed ONLY
to the member's own review email from settings. Never a client, another agent,
a lender, or any other address, and never with cc or bcc. The bot does not send
it; the agent does. It is counted as "review-copy", separately from sends.
"""
import re
import threading

OUTBOUND = ("send", "sign", "submit", "invite")
RECORDABLE = ("review-copy", "calendar-write", "overwrite-confirmed")


class NoSendCapability(Exception):
    pass


class ReviewCopyRefused(Exception):
    pass


def _addr(value):
    return (value or "").strip().lower()


def apply_never_say(text, phrases):
    """Remove the member's never-say phrases (case-insensitive). Returns (text, removed)."""
    removed = []
    for p in phrases or []:
        rx = re.compile(re.escape(p), re.I)
        if rx.search(text or ""):
            removed.append(p)
            text = re.sub(r" {2,}", " ", rx.sub("", text)).strip()
    return text, removed


def review_subject(address, document):
    return "%s - %s - Review" % (address, document)


class Ledger:
    def __init__(self):
        self.events = []
        self._lock = threading.Lock()

    def record(self, etype, detail=None):
        if etype in OUTBOUND:
            raise NoSendCapability("the bot cannot %s" % etype)
        if etype not in RECORDABLE:
            raise ValueError("unknown ledger event " + str(etype))
        with self._lock:
            self.events.append({"type": etype, "detail": dict(detail or {})})
        return self.events[-1]

    def count(self, etype):
        return sum(1 for e in self.events if e["type"] == etype)

    def sends(self):
        return sum(self.count(t) for t in OUTBOUND)


def save_review_copy(ledger, settings, draft):
    """Validate and log a review-copy draft. Returns the saved draft (sent False).

    settings: the member's own settings (needs "review_email").
    draft: {"to": str or [str], "address", "document", "summary", optional "cc"/"bcc"}.
    """
    own = _addr(settings.get("review_email"))
    if not own:
        raise ReviewCopyRefused("no review email in settings: no review copy")
    to = draft.get("to")
    to = [to] if isinstance(to, str) else list(to or [])
    if len(to) != 1 or _addr(to[0]) != own:
        raise ReviewCopyRefused("a review copy goes only to the member's own review email")
    if draft.get("cc") or draft.get("bcc"):
        raise ReviewCopyRefused("a review copy has no cc or bcc")
    subject = review_subject(draft.get("address", ""), draft.get("document", ""))
    body, removed = apply_never_say(draft.get("summary", ""),
                                    (settings.get("voice") or {}).get("never_say"))
    saved = {"type": "draft", "sent": False, "to": [own], "subject": subject,
             "body": body, "never_say_removed": removed}
    ledger.record("review-copy", {"to": own, "subject": subject, "recipients": 1})
    return saved
