"""Attach a document to the right deal. Ambiguity means ask, never auto-attach."""
import re

# USPS street suffixes (full word and common variants) -> the abbreviation used for compare.
_SUFFIX_PAIRS = {
    "ln": ("lane",), "st": ("street", "str"), "dr": ("drive", "drv"), "ave": ("avenue", "av"),
    "rd": ("road",), "blvd": ("boulevard", "boulv"), "ct": ("court",), "cir": ("circle",),
    "pl": ("place",), "pkwy": ("parkway", "pky", "parkwy"), "hwy": ("highway", "hiway"),
    "trl": ("trail",), "way": (), "ter": ("terrace", "terr"), "sq": ("square",),
    "aly": ("alley",), "cv": ("cove",), "xing": ("crossing",), "pt": ("point",),
    "rdg": ("ridge",), "bnd": ("bend",), "lk": ("lake",), "loop": (), "run": (), "path": (),
}
SUFFIX = {full: ab for ab, fulls in _SUFFIX_PAIRS.items() for full in fulls}
SUFFIXES = set(_SUFFIX_PAIRS)
DIRECTION = {"north": "n", "south": "s", "east": "e", "west": "w", "northeast": "ne",
             "northwest": "nw", "southeast": "se", "southwest": "sw"}
UNIT_RE = re.compile(r"\b(?:apt|unit|ste|suite|#)\s*\w+\b")


def normalize_address(text):
    s = (text or "").lower()
    s = s.split(",")[0] if re.search(r"\d", s.split(",")[0]) else s
    s = UNIT_RE.sub("", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    toks = [DIRECTION.get(t, SUFFIX.get(t, t)) for t in s.split()]
    number = toks[0] if toks and toks[0].isdigit() else ""
    street = " ".join(toks[1:] if number else toks)
    return {"number": number, "street": street, "key": (number + " " + street).strip()}


def _zip(text):
    m = re.search(r"\b(\d{5})\b\s*$", text or "")
    return m.group(1) if m else ""


def _edit_close(a, b):
    """House numbers one transposition or one digit apart count as similar."""
    if a == b or not a or not b:
        return False
    if sorted(a) == sorted(b) and len(a) == len(b):
        return True
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) <= 1
    return False


def _names(parties):
    return {re.sub(r"[^a-z ]", "", p.lower()).strip() for p in (parties or []) if p}


def match_document(doc, deals, threshold=0.8):
    """doc: {address, parties[], mls, transact_id}; deals: [{id, address, parties, mls, transact_id}].
    Returns {decision: match|new_deal|ask, deal_id, candidates, reason}."""
    d_addr = normalize_address(doc.get("address"))
    d_names = _names(doc.get("parties"))
    exact, similar, id_hits, party_only = [], [], [], []
    for deal in deals:
        a = normalize_address(deal.get("address"))
        same_street = d_addr["street"] and d_addr["street"] == a["street"]
        if d_addr["key"] and d_addr["key"] == a["key"]:
            exact.append(deal["id"])
        elif same_street and _edit_close(d_addr["number"], a["number"]):
            similar.append(deal["id"])
        if (doc.get("mls") and doc.get("mls") == deal.get("mls")) or \
           (doc.get("transact_id") and doc.get("transact_id") == deal.get("transact_id")):
            id_hits.append(deal["id"])
        if d_names & _names(deal.get("parties")) and deal["id"] not in exact:
            party_only.append(deal["id"])
    # An ID plus a matching address is the strongest case.
    strong = [i for i in id_hits if i in exact]
    if len(strong) == 1:
        return {"decision": "match", "deal_id": strong[0], "candidates": strong,
                "reason": "address and id agree"}
    if similar:
        return {"decision": "ask", "deal_id": None, "candidates": exact + similar,
                "reason": "similar addresses; ask the agent which deal"}
    if len(exact) == 1:
        return {"decision": "match", "deal_id": exact[0], "candidates": exact,
                "reason": "address matches"}
    if len(exact) > 1 or len(id_hits) > 1:
        return {"decision": "ask", "deal_id": None, "candidates": exact or id_hits,
                "reason": "more than one candidate"}
    if party_only or id_hits:
        return {"decision": "ask", "deal_id": None, "candidates": party_only + id_hits,
                "reason": "match on party or id alone; ask the agent"}
    return {"decision": "new_deal", "deal_id": None, "candidates": [],
            "reason": "no candidate above threshold"}
