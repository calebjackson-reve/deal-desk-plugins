"""tc-open-deal: existing file first, create, Details, Parties, starting paperwork."""
from . import navigator as nav
from .fill_form import add_paperwork

SIDE_PAPERWORK = {
    "buyer": ["Agency Disclosure Informational Pamphlet (LREC)",
              "Buyer representation agreement (Louisiana REALTORS)"],
    "seller": ["Listing agreement", "Agency Disclosure Informational Pamphlet (LREC)",
               "Property Disclosure Document + buyer receipt"],
}
DETAIL_FIELDS = [("address", "Address"), ("city", "City"), ("state", "State"), ("zip", "Zip"),
                 ("parish", "County"),          # Transact calls the parish "County"
                 ("price", "List Price"), ("financing", "Financing"),
                 ("closing_date", "Closing Date")]


def party_slots(parties):
    out = []
    for key, base in (("buyers", "Buyer"), ("sellers", "Seller")):
        for i, p in enumerate(parties.get(key, []), 1):
            out.append(("%s %d" % (base, i), p))
    for key, label in (("other_agent", "Other Agent"), ("lender", "Lender"), ("title", "Title")):
        if parties.get(key):
            out.append((label, parties[key]))
    return out


def add_party_slot(client, slot, person, allow=()):
    """One role slot: contact search (email, then name), Add Party, read the email back."""
    email = person["email"].lower()
    hits = client.search_contacts(person["email"]) or client.search_contacts(person["name"])
    hits = [h for h in hits if h["name"].lower() == person["name"].lower()
            or h["email"].lower() == email]
    if hits and hits[0]["email"].lower() != email:
        return {"status": "stopped", "stop": True, "reason": "contact_email_differs",
                "slot": slot, "contact": hits[0]["email"], "wanted": person["email"]}
    ap = nav.click(client, "Add Party", ("Add Participants",), allow)
    if not ap["clicked"]:
        return dict(ap, status="stopped", stop=True)
    if hits:
        how = "contact"
        nav.click(client, "Add from Contacts", (), allow)
    else:
        how = "created"
        nav.click(client, "Create New", (), allow)
        client.create_contact(person)
    client.add_party(slot, person, how)
    back = client.read_email(slot)
    if (back or "").lower() != email:
        return {"status": "stopped", "stop": True, "reason": "email_readback_mismatch",
                "slot": slot, "expected": person["email"], "read": back}
    return {"stop": False, "email": back, "how": how}


def open_deal(client, settings, facts, parties, allow=()):
    t = nav.open_transact(client, settings)
    if t["stop"]:
        return dict(t, status="stopped")
    found = nav.search_file(client, facts["address"].split(",")[0])
    if found["status"] == "missing" and facts.get("mls"):
        found = nav.search_file(client, facts["mls"])
    if found["status"] == "found":
        client.goto("details")
        client.set_open_file(facts["address"])
        return {"status": "existing_opened", "stop": True, "created": False,
                "duplicates": found["matches"][1:], "matches": len(found["matches"]),
                "contexts_checked": found["contexts_checked"]}
    if found["status"] != "missing":
        return {"status": "stopped", "stop": True, "reason": "contexts_not_all_checked"}
    started = "Brokerage system" if (settings.get("brokerage_system_start")
                                     and settings.get("brokerage_system_can_create")) else "Transact"
    r = nav.click(client, "New Transaction", ("Create Transaction",), allow)
    if not r["clicked"]:
        return dict(r, status="stopped")
    filled = {}
    for key, label in DETAIL_FIELDS:
        if facts.get(key) in (None, ""):
            continue
        f = nav.fill(client, label, facts[key])
        if not f["filled"]:
            return dict(f, status="stopped", filled=filled)
        filled[label] = facts[key]
    r = nav.click(client, "Parties", (), allow)
    if not r["clicked"]:
        return dict(r, status="stopped", filled=filled)
    added, seen = [], set()
    for slot, person in party_slots(parties):
        email = person["email"].lower()
        if email in seen:
            continue                      # never the same person twice
        seen.add(email)
        r = add_party_slot(client, slot, person, allow)
        if r.get("stop"):
            return dict(r, added=added)
        back = r["email"]
        added.append({"slot": slot, "name": person["name"], "email": back, "how": r["how"]})
    docs = []
    for name in SIDE_PAPERWORK.get(facts.get("side", "buyer"), []):
        a = add_paperwork(client, name)
        if a.get("stop"):
            return dict(a, status="stopped", parties=added)
        docs.append(name)
    client.set_open_file(facts["address"])
    return {"status": "created", "created": True, "started_in": started, "details": filled,
            "parties": added, "paperwork": docs, "stop": False}
