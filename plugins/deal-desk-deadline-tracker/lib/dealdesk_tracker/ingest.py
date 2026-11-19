"""tracker-ingest: classify, flag, match. Never extracts from non-contracts."""
import re

from dealdesk_core import deal_match, gate

CLASSES = ("purchase_agreement", "counter", "addendum", "amendment", "extension",
           "inspection_response", "other")
KEYWORDS = [
    ("inspection_response", ("inspection response", "due diligence")),
    ("counter", ("counter",)),
    ("amendment", ("amendment",)),
    ("extension", ("extension",)),
    ("addendum", ("addendum",)),
    ("purchase_agreement", ("agreement to buy", "purchase agreement", "agreement")),
]
MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec"
DATE_HINTS = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b(?:%s)[a-z]*\.? \d{1,2}(?:st|nd|rd|th)?\b" % MONTHS, re.I),
    re.compile(r"\bthe \d{1,2}(?:st|nd|rd|th)\b", re.I),
]


def classify(doc):
    """Return {"class", "readable"}. Unreadable or encrypted: ask the agent."""
    if doc.get("encrypted") or doc.get("readable") is False:
        return {"class": "unreadable", "readable": False, "action": "ask_agent",
                "message": "This file is locked or unreadable. Ask the agent for a "
                           "readable copy."}
    kind = doc.get("type")
    if kind not in CLASSES:
        text = " ".join(str(doc.get(k, "")) for k in
                        ("filename", "title", "form", "text")).lower()
        kind = "other"
        for name, words in KEYWORDS:
            if any(w in text for w in words):
                kind = name
                break
    return {"class": kind, "readable": True}


def match_input(doc):
    parties = doc.get("parties") or {}
    names = []
    if isinstance(parties, dict):
        for role in ("buyers", "sellers"):
            names += [p.get("name") for p in parties.get(role, []) if p.get("name")]
    else:
        names = list(parties)
    return {"address": doc.get("address"), "parties": names,
            "mls": doc.get("mls", ""), "transact_id": doc.get("transact_id", "")}


def ingest_document(doc, deals):
    c = classify(doc)
    if c["class"] == "unreadable":
        return {"class": "unreadable", "filed_as": None, "extracted": False,
                "action": "ask_agent", "decision": None, "message": c["message"]}
    wire = gate.scan_wire_text(str(doc.get("text", "")))
    if c["class"] == "other":
        return {"class": "other", "filed_as": "other", "extracted": False,
                "decision": None, "wire_flag": wire["flagged"]}
    m = deal_match.match_document(match_input(doc), deals)
    return {"class": c["class"], "filed_as": c["class"], "extracted": False,
            "decision": m["decision"], "deal_id": m["deal_id"],
            "candidates": m["candidates"], "reason": m["reason"],
            "wire_flag": wire["flagged"]}


def date_suggestions(body):
    out = []
    for rx in DATE_HINTS:
        for m in rx.finditer(body or ""):
            out.append({"text": m.group(0), "status": "suggestion",
                        "flag": "from email body, unverified, not a contract date"})
    return out


def ingest_email(email, deals):
    wire = gate.scan_wire_text("%s %s" % (email.get("subject", ""), email.get("body", "")))
    base = {"wire_flag": wire["flagged"], "action": "none" if wire["flagged"] else None}
    atts = email.get("attachments") or []
    if not atts:
        return dict(base, logged="no document", documents=[],
                    suggestions=date_suggestions(email.get("body")), extracted=False)
    docs = []
    for a in atts:
        r = ingest_document(a.get("document") or {"filename": a.get("filename", "")}, deals)
        r["filename"] = a.get("filename")
        docs.append(r)
    return dict(base, logged="documents", documents=docs, suggestions=[], extracted=False)
