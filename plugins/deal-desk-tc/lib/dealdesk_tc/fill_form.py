"""tc-fill-form: term sheet, form choice, fill, check, then the review gate and STOP.

Never Prepare Signing, submit, certify, or sign. The last thing this does is
propose the review gate.
"""
import json
import re
from pathlib import Path

from . import navigator as nav

_PACK_REL = Path("shared-core") / "skills" / "market-louisiana" / "market-pack.json"
# Source layout: dealdesk/shared-core next to dealdesk/deal-desk-tc.
# Plugin layout: shared-core is bundled inside the plugin root, next to lib/.
PACK_PATH = Path(__file__).resolve().parents[3] / _PACK_REL
if not PACK_PATH.exists():
    PACK_PATH = Path(__file__).resolve().parents[2] / _PACK_REL

REQUIRED = {"offer": ["price", "financing", "deposit_amount", "act_of_sale"],
            "counter": ["changes"], "addendum": ["added_terms"],
            "amendment": ["changes"], "extension": ["new_date"]}
# Offer terms asked only when they apply (see offer_asks). Order is the order of the plain list.
OFFER_CONDITIONAL = ["loan_amount", "interest_rate", "financing_application_days",
                     "deposit_holder", "offer_expiration"]
SMALL_DEFAULTS = {"possession": "At act of sale", "home_warranty": "None"}
FIELD_MAP = [("price", "Purchase Price"), ("deposit_amount", "Deposit"),
             ("act_of_sale", "Act of Sale Date"), ("financing", "Financing"),
             ("possession", "Possession"), ("commission", "Commission"),
             ("new_date", "New Date"), ("offer_expiration", "Offer Expires")]
# LREC0059 (Residential Agreement to Buy or Sell, Rev. 01/2026) financing boxes. Labels are read
# from the page; the first name is the one seen, the rest are likely alternates.
FINANCED = ("Financed Sale", "Financed")
ALL_CASH = ("All Cash Sale", "Cash Sale")
LOAN_BOXES = {"Conventional": ("Conventional Mortgage", "Conventional", "Conventional Loan"),
              "FHA": ("FHA", "FHA Mortgage", "FHA Loan"),
              "VA": ("VA", "VA Mortgage", "VA Loan"),
              "USDA": ("USDA", "USDA Rural Development", "USDA Loan"),
              "Other": ("Other Financing", "Other")}
# Member-profile keys (member-setup) -> form labels. None of these auto-fill.
PROFILE_MAP = [("agent_name", "Agent Name"), ("agent_license", "Agent License"),
               ("brokerage_license", "Brokerage License"), ("agent_phone", "Agent Phone"),
               ("agent_email", "Agent Email"), ("brokerage_phone", "Brokerage Phone"),
               ("brokerage_email", "Brokerage Email"), ("sellers_agent", "Seller's Agent"),
               ("designated_agent_name", "Designated Agent Name"),
               ("designated_agent_license", "Designated Agent License"),
               ("designated_agent_phone", "Designated Agent Phone"),
               ("designated_agent_email", "Designated Agent Email")]
WRITTEN = {"Purchase Price": "Purchase Price (written)", "Deposit": "Deposit (written)"}
DISCLOSURES = {"agency": "Agency Disclosure Informational Pamphlet (LREC)",
               "property": "Property Disclosure Document + buyer receipt",
               "lead": "Lead-Based Paint Disclosure (pre-1978)",
               "flood": "Flood disclosure"}


ASK_LABELS = {"price": "Purchase price", "financing": "Financing type",
              "deposit_amount": "Deposit amount", "act_of_sale": "Act of sale date",
              "loan_amount": "Loan amount", "interest_rate": "Interest rate",
              "financing_application_days": "Financing application days",
              "deposit_holder": "Deposit holder",
              "offer_expiration": "Offer expiration date and time"}


def load_pack():
    return json.loads(PACK_PATH.read_text(encoding="utf-8"))


def _blank(v):
    return v is None or v == [] or (isinstance(v, str) and not v.strip())


_TIME_OF_DAY = re.compile(r"\b\d{1,2}:\d{2}\b|\b\d{1,2}\s*(?:a\.?m\.?|p\.?m\.?)(?![a-z])|"
                          r"\b(?:noon|midnight)\b", re.I)


def has_time_of_day(v):
    """An offer expiration needs a date AND a time. A bare date is not enough."""
    if hasattr(v, "hour"):                       # a datetime object carries a time
        return True
    return bool(_TIME_OF_DAY.search(str(v)))


def _has_deposit(v):
    if _blank(v):
        return False
    try:
        return float(re.sub(r"[^0-9.]", "", str(v)) or 0) > 0
    except ValueError:
        return True


def offer_asks(merged):
    """Every missing offer term, in one list. Base fields always; the rest only when they apply."""
    asks = [k for k in REQUIRED["offer"] if _blank(merged.get(k))]
    fin = merged.get("financing")
    financed = not _blank(fin) and str(fin).strip().lower() != "cash"
    if financed:
        asks += [k for k in ("loan_amount", "interest_rate", "financing_application_days")
                 if _blank(merged.get(k))]
    if _has_deposit(merged.get("deposit_amount")) and _blank(merged.get("deposit_holder")):
        asks.append("deposit_holder")
    exp = merged.get("offer_expiration")
    if _blank(exp) or not has_time_of_day(exp):
        asks.append("offer_expiration")
    return asks


def term_sheet(kind, terms, found=None):
    """Merge what the agent said with what is in the file, mail, or MLS.

    Ask only about contract-changing gaps; pick and state small defaults.
    """
    merged = dict(found or {})
    merged.update(terms)
    if kind == "offer":
        asks = offer_asks(merged)
    else:
        asks = [k for k in REQUIRED[kind] if merged.get(k) in (None, "", [])]
    defaults = {k: v for k, v in SMALL_DEFAULTS.items() if k not in merged}
    full = dict(defaults)
    full.update(merged)
    return {"kind": kind, "terms": full, "asks": asks, "defaults_used": sorted(defaults)}


def choose_form(kind, pack, context=None, named=None):
    ctx = context or {}
    names = {f["name"] for f in pack["forms"]}
    if named:
        if named in names:
            return {"form": named, "why": "named by the agent"}
        return {"ask": "form", "message": "%s is not in the market pack form list." % named}
    ch = pack["form_chooser"]
    accepted = ctx.get("accepted", False)
    if kind == "offer":
        return {"form": ch["offer"]}
    if kind == "counter":
        n = ctx.get("counter_number", 0) + 1
        return {"form": ch["counter"], "counter_number": n,
                "counter_on_counter": n > 1}
    if kind in ("amendment", "addendum"):
        if not accepted:
            return {"stop": True, "reason": "not_accepted",
                    "message": "Nothing is accepted yet. A %s changes an accepted "
                               "contract. Use a counter instead." % kind}
        return {"form": ch["change_after_acceptance" if kind == "amendment" else "add_a_term"]}
    if kind == "extension":
        return {"form": ch["more_time_on_contract_date" if accepted
                           else "more_time_before_acceptance"]}
    return {"ask": "form", "message": "Unknown form kind %s" % kind}


def format_commission(value, fmt, price):
    """Member format: percent ('3%') or dollar ('$8,670.00')."""
    if fmt == "percent":
        pct = value["pct"] if isinstance(value, dict) else float(value)
        return ("%g%%" % pct)
    if fmt == "dollar":
        if isinstance(value, dict):
            amt = price * value["pct"] / 100.0 if "pct" in value else value["amount"]
        else:
            amt = float(value)
        return "${:,.2f}".format(amt)
    return None


def _rev(footer):
    m = re.search(r"Rev\.?\s*(\d{1,2})\s*/\s*(\d{4})", footer or "", re.I)
    return (int(m.group(2)), int(m.group(1))) if m else None


def pick_library_entry(client, entries):
    """Look-alike library entries carry no version text. Preview each, read the footer revision,
    take the newest; equal revisions: take the first and say so. Never pick by position unseen."""
    seen = []
    for e in entries:
        pv = client.preview(e["id"])
        seen.append({"id": e["id"], "footer": pv["footer"], "rev": _rev(pv["footer"])})
    if any(x["rev"] is None for x in seen):
        return {"stop": True, "reason": "no_footer_revision", "previews": seen,
                "message": "A library entry preview has no readable 'Rev. MM/YYYY' footer. "
                           "Not choosing by position."}
    top = max(x["rev"] for x in seen)
    best = [x for x in seen if x["rev"] == top]
    note = ("Newest footer revision: %s." % best[0]["footer"] if len(best) == 1 else
            "%d entries share the newest revision (%s); took the first." % (len(best), best[0]["footer"]))
    return {"stop": False, "id": best[0]["id"], "footer": best[0]["footer"], "tie": len(best) > 1,
            "previews": seen, "note": note}


def add_paperwork(client, name):
    r = nav.click(client, "Add Paperwork", ("Add Form",))
    if not r["clicked"]:
        return dict(r, stop=True)
    entries = client.library_entries(name)
    if entries:
        if len(entries) > 1:
            pick = pick_library_entry(client, entries)
            if pick["stop"]:
                return dict(pick, form_not_added=True)
        else:
            pv = client.preview(entries[0]["id"])
            pick = {"id": entries[0]["id"], "footer": pv["footer"], "tie": False,
                    "previews": [{"id": entries[0]["id"], "footer": pv["footer"]}],
                    "note": "Only one library entry."}
        client.add_form_entry(pick["id"])
        return {"added": name, "form_pick": {k: pick[k] for k in
                                             ("id", "footer", "tie", "previews", "note")}}
    hits = client.library_search(name)
    if name not in hits:
        return {"stop": True, "reason": "form_not_in_library", "looked_for": name}
    client.add_form(name)
    return {"added": name}


def pre_approval_flags(terms):
    pa = terms.get("pre_approval")
    flags = []
    if terms.get("financing") == "Cash":
        return flags
    if not pa:
        return ["pre_approval_missing"]
    if pa.get("amount") is not None and terms.get("price") and pa["amount"] < terms["price"]:
        flags.append("pre_approval_amount_below_price")
    if pa.get("loan_type") and terms.get("financing") and pa["loan_type"] != terms["financing"]:
        flags.append("pre_approval_loan_type_mismatch")
    if pa.get("borrowers") and terms.get("buyers") and \
            sorted(pa["borrowers"]) != sorted(terms["buyers"]):
        flags.append("pre_approval_name_mismatch")
    return flags


def financing_flags(ticked, financing=None):
    """Term-sheet check on the financing boxes. `ticked` = labels ticked on the form."""
    t = {x.lower() for x in ticked}
    financed = any(x.lower() in t for x in FINANCED)
    cash = any(x.lower() in t for x in ALL_CASH)
    loans = [k for k, names in LOAN_BOXES.items() if any(n.lower() in t for n in names)]
    flags = []
    if loans and not financed:
        flags.append("loan_type_without_financed_sale")
    if financed and not loans:
        flags.append("financed_sale_without_loan_type")
    if cash and (financed or loans):
        flags.append("all_cash_with_financing")
    if financing == "Cash" and not cash and not (financed or loans):
        flags.append("cash_term_but_all_cash_not_ticked")
    if financing and financing != "Cash" and loans and financing not in loans:
        flags.append("loan_type_differs_from_term_sheet")
    return {"flags": flags, "financed": financed, "all_cash": cash, "loan_types": loans}


def tick_financing(client, financing):
    """Cash -> All Cash Sale only. Any loan -> Financed Sale AND the loan-type box."""
    want = [ALL_CASH] if financing == "Cash" else \
        [FINANCED, LOAN_BOXES.get(financing, LOAN_BOXES["Other"])]
    ticked = []
    for alts in want:
        if any(a in client.checked for a in alts):
            continue
        r = nav.click(client, alts[0], alts[1:])
        if not r["clicked"]:
            return {"ticked": ticked, "stop": r}
        ticked.append(r["label"])
    return {"ticked": ticked, "stop": None}


def clean_amount(v):
    """The written-amount fields append "Dollars" themselves; never type it."""
    return re.sub(r"\s*dollars\b", "", v, flags=re.I).strip() if isinstance(v, str) else v


def written_flags(client, page_key):
    pg = client.pages[page_key]
    out = []
    for lab in WRITTEN.values():
        val = client.values.get((page_key, lab), pg.get("fields", {}).get(lab))
        if val and re.search(r"\bdollars\s+dollars\b", val, re.I):
            out.append({"field": lab, "value": val, "problem": "dollars_doubled"})
    return out


def _slots(parties):
    from .open_deal import party_slots
    return party_slots({k: parties[k] for k in ("buyers", "sellers") if k in parties})


def role_slot_check(client, parties):
    """Names come from Parties role slots. Returns slots that are empty or hold someone else."""
    wrong, empty = [], []
    for slot, person in _slots(parties):
        have = client.parties.get(slot)
        if not have:
            empty.append(slot)
        elif have["name"].lower() != person["name"].lower():
            wrong.append({"slot": slot, "has": have["name"], "wanted": person["name"]})
    return {"ok": not (wrong or empty), "wrong": wrong, "empty": empty}


def fix_role_slots(client, parties, check, allow=()):
    """Fix a wrong or empty slot through Parties (Add Party); the caller re-checks."""
    from .open_deal import add_party_slot
    nav.click(client, "Parties", ())
    todo = set(check["empty"]) | {w["slot"] for w in check["wrong"]}
    for slot, person in _slots(parties):
        if slot in todo:
            r = add_party_slot(client, slot, person, allow)
            if r.get("stop"):
                return r
    return {"stop": False}


def check_form(client, form_key, expected, left_blank, terms, facts):
    page = client.pages[form_key]
    blanks = []
    for label, initial in page.get("fields", {}).items():
        val = client.values.get((form_key, label), initial)
        if val in (None, "") and label not in left_blank:
            blanks.append(label)
    conflicts = []
    for label, want in expected.items():
        have = client.values.get((form_key, label))
        if have is not None and str(have) != str(want):
            conflicts.append({"field": label, "form": have, "term_sheet": want})
    have_forms = set(client.added_forms)
    missing = []
    if facts.get("side", "buyer") == "buyer" and terms.get("kind") == "offer":
        need = ["agency", "property"]
        if facts.get("year_built") and facts["year_built"] < 1978:
            need.append("lead")
        if facts.get("flood_zone"):
            need.append("flood")
        missing = [DISCLOSURES[k] for k in need if DISCLOSURES[k] not in have_forms]
    return {"blanks": blanks, "conflicts": conflicts, "missing_disclosures": missing}


def fill_form(client, gate, settings, kind, terms, context=None, found=None,
              facts=None, named=None, pack=None):
    pack = pack or load_pack()
    facts = facts or {}
    sheet = term_sheet(kind, terms, found)
    if sheet["asks"]:
        # Nothing is filled. The agent gets a plain list of what is still needed; never guess a value.
        return {"status": "ask", "asks": sheet["asks"], "filled": {},
                "message": "Still needed before I fill anything:\n" +
                           "\n".join("- " + ASK_LABELS.get(k, k) for k in sheet["asks"]),
                "term_sheet": sheet}
    choice = choose_form(kind, pack, context, named)
    if choice.get("ask") or choice.get("stop"):
        return dict(choice, status="stopped", term_sheet=sheet)
    form = choice["form"]
    t = dict(sheet["terms"], kind=kind)
    commission = None
    if "commission" in t:
        commission = format_commission(t["commission"], settings.get("commission_format"),
                                       t.get("price", 0))
        if commission is None:
            return {"status": "ask", "asks": ["commission_format"], "term_sheet": sheet}
        t["commission"] = commission
    slots = None
    if facts.get("parties"):
        slots = role_slot_check(client, facts["parties"])
        if not slots["ok"]:
            fixed = sorted(set(slots["empty"]) | {w["slot"] for w in slots["wrong"]})
            fx = fix_role_slots(client, facts["parties"], slots)
            if fx.get("stop"):
                return dict(fx, status="stopped", role_slots=slots, term_sheet=sheet)
            again = role_slot_check(client, facts["parties"])
            slots = dict(again, fixed=fixed)
            if not again["ok"]:
                return {"status": "stopped", "stop": True, "reason": "role_slots_wrong",
                        "role_slots": slots, "term_sheet": sheet}
    # Details and Parties first so the form auto-fills.
    details = {}
    for key, label in (("price", "List Price"), ("financing", "Financing")):
        if key in t:
            nav.click(client, "Details", ())
            r = nav.fill(client, label, t[key])
            if not r["filled"]:
                return dict(r, status="stopped", term_sheet=sheet)
            details[label] = t[key]
    nav.click(client, "Parties", ())
    ap = add_paperwork(client, form)
    if ap.get("stop"):
        return dict(ap, status="stopped", term_sheet=sheet)
    client.goto("forms_editor")
    page = client.page()
    if not nav.saved_status(client):
        return {"status": "stopped", "stop": True, "reason": "not_saved",
                "message": "Forms Editor never showed Saved."}
    ready = nav.form_ready(client)
    if ready["stop"]:
        return {"status": "stopped", "stop": True, "reason": "form_not_filled",
                "message": ready["message"] + " Prepare Signing is not pressed.",
                "term_sheet": sheet}
    expected = {}
    for key, label in FIELD_MAP:
        if key not in t or t[key] in (None, ""):
            continue
        val = clean_amount(t[key]) if key in ("price", "deposit_amount") else t[key]
        r = nav.fill(client, label, val)
        if not r["filled"]:
            return dict(r, status="stopped", filled=expected, term_sheet=sheet)
        expected[label] = val
    fin_boxes = None
    if t.get("financing") and client.page().get("checkboxes"):
        tk = tick_financing(client, t["financing"])
        if tk["stop"]:
            return dict(tk["stop"], status="stopped", filled=expected, term_sheet=sheet)
        fin_boxes = dict(financing_flags(client.checked, t["financing"]), ticked_now=tk["ticked"])
    profile = settings.get("profile") or {}
    profile_missing = []
    for key, label in PROFILE_MAP:
        if not str(profile.get(key) or "").strip():
            profile_missing.append({"key": key, "field": label})
            continue
        r = nav.fill(client, label, profile[key])
        if not r["filled"]:
            return dict(r, status="stopped", filled=expected, term_sheet=sheet)
        expected[label] = profile[key]
    wflags = written_flags(client, "forms_editor")
    flags = []
    if kind == "offer" and facts.get("side", "buyer") == "buyer":
        pa = t.get("pre_approval")
        if pa:
            client.attach(pa["file"])
        flags = pre_approval_flags(t)
    check = check_form(client, "forms_editor", expected, settings.get("left_blank", []),
                       t, facts)
    fflags = (fin_boxes or {}).get("flags", [])
    ready = not (check["blanks"] or check["conflicts"] or check["missing_disclosures"] or flags
                 or fflags or wflags or profile_missing)
    payload = {"form": form, "address": facts.get("address"), "values": expected,
               "counter_number": choice.get("counter_number")}
    proposal = gate.propose("form_review", payload)
    return {"status": "awaiting_yes", "ready": ready, "form": form,
            "counter_number": choice.get("counter_number"),
            "counter_on_counter": choice.get("counter_on_counter", False),
            "filled": expected, "details_updated": details, "commission": commission,
            "pre_approval_flags": flags, "check": check, "financing_boxes": fin_boxes,
            "profile_missing": profile_missing, "written_amount_flags": wflags,
            "role_slots": slots, "form_pick": ap.get("form_pick"), "defaults_used": sheet["defaults_used"],
            "proposal": proposal, "payload": payload,
            "next": "Waiting for the agent's yes in this chat. Prepare Signing is not pressed."}
