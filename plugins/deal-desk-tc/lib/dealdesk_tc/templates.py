"""tc-templates: packet templates, prefill map, signer layouts, compliance mapping, auto-run.

Data lives in deal-desk-tc/templates/<market>/*.json (read-only, shared). Members add or override
templates in their own settings (validated, isolated per member). Auto-run stops at the review gate.
It never presses Prepare Signing, Next, Send, or Submit, and nothing here sends or signs.
Compliance: staged, then the executed documents upload AUTOMATICALLY into the member's own file's
Compliance tab (no yes; guards in compliance.upload_guard). Only the submit is gated (own yes).
"""
import copy
import json
import re
from pathlib import Path

from . import compliance as comp
from . import fill_form as ff
from . import navigator as nav
from . import signing_prep as sp

DATA = Path(__file__).resolve().parents[2] / "templates" / "louisiana-baton-rouge"
PICK_RULE = "newest footer revision (preview each; equal -> first and say so)"
STAGES = ("under_contract", "inspection_response", "appraisal_lending", "closing", "post_closing")
ROLES = ("buyers", "sellers", "listing_agent", "agents")
STEPS = ("add_forms", "prefill", "map_signers", "save_draft", "compliance_plan")
FACTS = ("year_built", "loan_type", "flood_zone", "accepted", "inspection_done")
ITEM_KEYS = {"code", "name", "library_search", "pick_rule", "target_folder_hint", "requirement", "when", "verified"}
TOP_KEYS = {"id", "name", "deal_types", "forms", "signing_order", "compliance_stage", "steps", "notes"}
FORBIDDEN = re.compile(r"(send|invite|prepare[ _-]?signing|submit|certif|e-?sign|\bsign\b|^next$)", re.I)
CUSTOM_KEY = "custom_templates"        # inside the member's own bot config; never shared
AMOUNT_KEYS = ("price", "deposit_amount")


def load_defaults():
    out = {}
    for k in ("packets", "prefill", "layouts", "compliance"):
        out[k] = json.loads((DATA / (k + ".json")).read_text(encoding="utf-8"))
    return copy.deepcopy(out)


def _norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def name_key(s):
    """Normalized name as a set of tokens (order, case, punctuation, plural 's' ignored)."""
    return frozenset(t[:-1] if len(t) > 3 and t.endswith("s") else t for t in _norm(s).split())


# ---------------------------------------------------------------- member templates (isolated)
def validate_custom(t):
    """A custom template may add forms and set an order. It can never contain a send or sign step."""
    problems = []
    if not isinstance(t, dict):
        return {"valid": False, "problems": ["not_an_object"]}
    for k in t:
        if k not in TOP_KEYS:
            problems.append("send_or_sign_step_not_allowed:%s" % k if FORBIDDEN.search(k)
                            else "unknown_key:%s" % k)
    for s in t.get("steps", []) or []:
        st = s.get("step") if isinstance(s, dict) else s
        if st not in STEPS:
            problems.append("send_or_sign_step_not_allowed:%s" % st if FORBIDDEN.search(str(st))
                            else "unknown_step:%s" % st)
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", str(t.get("id", ""))):
        problems.append("id_missing_or_not_kebab_case")
    if not t.get("name"):
        problems.append("name_missing")
    forms = t.get("forms")
    if not isinstance(forms, list) or not forms:
        problems.append("forms_missing")
        forms = []
    for i, f in enumerate(forms):
        if not isinstance(f, dict) or not (f.get("code") or f.get("name")):
            problems.append("form_%d_needs_code_or_name" % i)
            continue
        for k in f:
            if k not in ITEM_KEYS:
                problems.append("send_or_sign_step_not_allowed:%s" % k if FORBIDDEN.search(k)
                                else "form_%d_unknown_key:%s" % (i, k))
        if f.get("requirement", "required") not in ("required", "conditional"):
            problems.append("form_%d_bad_requirement" % i)
        if f.get("requirement") == "conditional" and not (f.get("when") or {}).get("fact") in FACTS:
            problems.append("form_%d_conditional_needs_known_fact" % i)
    for r in t.get("signing_order", []) or []:
        if r not in ROLES:
            problems.append("unknown_role:%s" % r)
    if t.get("compliance_stage") and t["compliance_stage"] not in STAGES:
        problems.append("unknown_stage")
    return {"valid": not problems, "problems": problems}


def add_member_template(bot, t):
    """Validated, stored in this member's own bot config only. Same id as a default = override."""
    v = validate_custom(t)
    if not v["valid"]:
        return {"saved": False, "problems": v["problems"]}
    with bot._lock:
        bot.config.setdefault(CUSTOM_KEY, {})[t["id"]] = copy.deepcopy(t)
    return {"saved": True, "id": t["id"]}


def member_templates(bot):
    return copy.deepcopy(bot.config.get(CUSTOM_KEY, {}))


def _fill_item(f):
    f = dict(f)
    f.setdefault("code", "unverified")
    f.setdefault("name", f["code"])
    f.setdefault("library_search", f["name"])
    f["pick_rule"] = PICK_RULE
    f.setdefault("requirement", "required")
    f.setdefault("target_folder_hint", None)
    f.setdefault("verified", False)
    return f


def catalog(custom=None):
    """Defaults (read-only copy) with the member's custom templates added or overriding by id."""
    d = load_defaults()
    cat = {k: dict(v) for k, v in d["packets"]["packets"].items()}
    for k, v in (custom or {}).items():
        base = cat.get(k, {})
        merged = dict(base)
        merged.update(copy.deepcopy(v))
        merged["custom"] = True
        cat[k] = merged
    for v in cat.values():
        v["forms"] = [_fill_item(f) for f in v["forms"]]
        v.setdefault("deal_types", [v["id"]])
        v.setdefault("signing_order", ["buyers", "sellers"])
        v.setdefault("compliance_stage", "under_contract")
    return cat


ALIASES = {"offer": "buyer-offer", "buyer offer": "buyer-offer", "listing": "listing-packet",
           "amendment": "amendment-repair-request", "repair request": "amendment-repair-request",
           "repair": "amendment-repair-request", "extension": "extension", "extend": "extension"}


def select_template(deal_type, from_party=None, custom=None):
    """Template by deal type. 'counter' needs to know who counters. Unknown type -> ask."""
    cat = catalog(custom)
    key = _norm(deal_type or "")
    if key == "counter":
        if from_party in ("seller", "buyer"):
            key = "%s counter" % from_party
        else:
            return {"ask": "who_counters", "choices": ["seller-counter", "buyer-counter"],
                    "message": "A counter: is it the seller's or the buyer's?"}
    for tid, t in cat.items():
        if t.get("custom") and (key == _norm(tid) or key in [_norm(x) for x in t["deal_types"]]):
            return {"template": t}
    for tid, t in cat.items():
        if key == _norm(tid) or key in [_norm(x) for x in t["deal_types"]]:
            return {"template": t}
    if key in ALIASES and ALIASES[key] in cat:
        return {"template": cat[ALIASES[key]]}
    return {"ask": "deal_type", "choices": sorted(cat),
            "message": "I do not know the deal type %r. Pick one of: %s." % (deal_type, ", ".join(sorted(cat)))}


# ---------------------------------------------------------------- conditional forms
def _cond(when, facts):
    v = facts.get(when["fact"])
    if "truthy" in when:
        return bool(v) == when["truthy"]
    if v is None:
        return None
    if "lt" in when:
        return v < when["lt"]
    if "in" in when:
        return v in when["in"]
    return v == when.get("eq")


def resolve_forms(template, facts):
    add, skip, ask = [], [], []
    for f in template["forms"]:
        if f["requirement"] == "required" or not f.get("when"):
            add.append(f)
            continue
        c = _cond(f["when"], facts)
        if c is None:
            ask.append({"form": f["name"], "needs": f["when"]["fact"]})
        elif c:
            add.append(f)
        else:
            skip.append({"form": f["name"], "reason": "condition_not_met", "when": f["when"]})
    return {"add": add, "skip": skip, "ask": ask}


# ---------------------------------------------------------------- prefill
def prefill_plan(form_name, terms, details, settings, defaults=None):
    """Pure plan: what goes into which label, from which source. Types nothing."""
    pre = (defaults or load_defaults())["prefill"]["forms"].get(form_name)
    if pre is None:
        return {"form": form_name, "details": [], "form_fields": [], "checkboxes": None, "slots": [],
                "profile": [], "blanks": [], "unverified": [], "no_map": True}
    left_blank = set(settings.get("left_blank", []))
    plan = {"form": form_name, "details": [], "form_fields": [], "checkboxes": None, "slots": [],
            "profile": [], "blanks": [], "unverified": [], "no_map": False}
    profile = settings.get("profile") or {}
    for e in pre["fields"]:
        src, label = e["source"], e["label"]
        if src == "parties_role_slot":
            plan["slots"].append(label)
            continue
        if src == "member_profile":
            for key, lab in ff.PROFILE_MAP:
                if str(profile.get(key) or "").strip():
                    plan["profile"].append({"key": key, "label": lab, "value": profile[key], "verified": False})
                else:
                    plan["blanks"].append({"label": lab, "source": src, "reason": "profile_value_missing"})
                plan["unverified"].append(lab)
            continue
        if e.get("kind") == "checkboxes":
            if terms.get("financing"):
                plan["checkboxes"] = terms["financing"]
            else:
                plan["blanks"].append({"label": label, "source": src, "reason": "no_value"})
            continue
        val = details.get(e["key"]) if src == "details" else terms.get(e["key"])
        if val in (None, ""):
            if label not in left_blank:
                plan["blanks"].append({"label": label, "source": src, "reason": "no_value"})
            continue
        if e["key"] in AMOUNT_KEYS or isinstance(val, str):
            val = ff.clean_amount(val)                      # never type "Dollars"
        if e["key"] == "commission":
            val = ff.format_commission(val, settings.get("commission_format"), terms.get("price", 0))
            if val is None:
                plan["blanks"].append({"label": label, "source": src, "reason": "commission_format_not_set"})
                continue
        plan["details" if e["where"] == "details" else "form_fields"].append(
            {"label": label, "value": val, "source": src, "verified": e["verified"]})
        if not e["verified"]:
            plan["unverified"].append(label)
    return plan


# ---------------------------------------------------------------- signer layouts
def pick_layout(form_name, saved_layouts):
    """Prefer a saved layout whose normalized name matches the form. Two matches ask. None -> template."""
    key = name_key(form_name)
    hits = [l["name"] if isinstance(l, dict) else l for l in saved_layouts
            if name_key(l["name"] if isinstance(l, dict) else l) == key]
    if len(hits) == 1:
        return {"source": "saved", "name": hits[0]}
    if len(hits) > 1:
        return {"source": "ask", "ask": "layout", "choices": hits}
    return {"source": "template", "name": None}


def _pages(spec, n):
    if isinstance(spec, list):
        return [p for p in spec if 1 <= p <= n]
    return {"all": list(range(1, n + 1)), "first": [1], "last": [n]}.get(spec, [])


def role_people(role, facts, settings):
    p = facts.get("parties", {})
    if role in ("buyers", "sellers"):
        return list(p.get(role, []))
    if role == "listing_agent":
        la = p.get("listing_agent") or {"name": settings.get("member_name"), "email": settings.get("member_email")}
        return [la] if la.get("name") and la.get("email") else []
    return list(facts.get("agent_signers", []))


def signer_plan(template, forms, facts, settings, saved_layouts=(), choices=None, page_counts=None,
                defaults=None):
    """Per form: saved layout or template fields per signer; plus the signing order."""
    d = defaults or load_defaults()
    order, req, seen = [], [], set()
    for role in template["signing_order"]:
        for person in role_people(role, facts, settings):
            if person["name"] not in seen:
                seen.add(person["name"])
                order.append(person["name"])
                req.append(dict(person))
    out = {"order": order, "requested": req, "docs": {}, "ask": [], "needs_page_count": [],
           "unverified": [], "roles_without_people": [r for r in template["signing_order"]
                                                       if not role_people(r, facts, settings)]}
    for f in forms:
        name = f["name"]
        pk = pick_layout(name, saved_layouts)
        if pk["source"] == "ask":
            ch = (choices or {}).get(name)
            if ch in pk["choices"]:
                pk = {"source": "saved", "name": ch}
            else:
                out["ask"].append({"doc": name, "layouts": pk["choices"]})
                continue
        if pk["source"] == "saved":
            out["docs"][name] = {"saved": pk["name"], "fields": {}, "source": "saved"}
            continue
        lay = d["layouts"]["forms"].get(name)
        if not lay:
            out["docs"][name] = {"saved": None, "fields": {}, "source": "none"}
            out["unverified"].append(name)
            continue
        n = (page_counts or {}).get(name) or lay.get("pages_hint")
        if not n:
            out["needs_page_count"].append(name)
            out["docs"][name] = {"saved": None, "fields": {}, "source": "needs_page_count"}
            continue
        if not (page_counts or {}).get(name):
            out["unverified"].append(name + " (page count)")
        fields = {}
        for role, spec in lay["roles"].items():
            people = role_people(role, facts, settings)
            if role == "agents" and not people:
                continue
            for person in people:
                fields[person["name"]] = {k: _pages(v, n) for k, v in spec["fields"].items()}
        out["docs"][name] = {"saved": None, "fields": fields, "source": "template", "pages": n}
        if not lay.get("verified"):
            out["unverified"].append(name + " (layout)")
    return out


def layout_save(gate, layout):
    """Saving or overwriting a saved layout needs the agent's yes."""
    g = gate.attempt("save_signing_layout", layout)
    return {"saved": g["allowed"], "reason": g["reason"],
            "proposal": None if g["allowed"] else gate.propose("save_signing_layout", layout)}


# ---------------------------------------------------------------- compliance
def _row_match(row, hints):
    rk = name_key(row)
    return any(name_key(h) <= rk or rk <= name_key(h) for h in hints if name_key(h))


def compliance_batch(stage, signed_docs, rows, facts, defaults=None):
    """Prepare the upload plan (doc -> row). Writes nothing."""
    stage_docs = (defaults or load_defaults())["compliance"]["stages"].get(stage)
    if stage_docs is None:
        return {"ask": "stage", "choices": list(STAGES)}
    have = {name_key(d["name"]): d for d in signed_docs}
    items, skipped, unmapped, rejected, waiting = [], [], [], [], []
    for sd in stage_docs:
        if sd.get("when") and _cond(sd["when"], facts) is not True:
            skipped.append({"doc": sd["doc"], "reason": "condition_not_met"})
            continue
        d = have.get(name_key(sd["doc"]))
        if d is None:
            waiting.append(sd["doc"])
            continue
        if d.get("blank") or not d.get("signed", False):
            rejected.append({"doc": sd["doc"], "reason": "blank_or_unsigned_form"})
            continue
        if d.get("partially_signed"):
            rejected.append({"doc": sd["doc"], "reason": "not_fully_executed"})
            continue
        cands = [r for r in rows if _row_match(r["row"], sd["row_hints"])]
        if not cands:
            unmapped.append({"doc": sd["doc"], "ask": "row", "reason": "no_row_matches_by_name"})
        elif len(cands) > 1:
            unmapped.append({"doc": sd["doc"], "ask": "row", "reason": "two_rows_match",
                             "rows": [r["row"] for r in cands]})
        elif cands[0]["status"] == "filled":
            skipped.append({"doc": sd["doc"], "row": cands[0]["row"], "reason": "row_already_filled_not_overwritten"})
        elif cands[0]["status"] == "na":
            skipped.append({"doc": sd["doc"], "row": cands[0]["row"], "reason": "row_not_applicable"})
        else:
            items.append({"doc": sd["doc"], "row": cands[0]["row"], "pages": "all", "executed": True,
                          "signed_copy_required": sd.get("signed_copy_required", True)})
    return {"stage": stage, "items": items, "skipped": skipped, "unmapped": unmapped, "rejected": rejected,
            "waiting_for_signed_copy": waiting, "writes": 0,
            "row_hints_unverified": sorted({h for sd in stage_docs for h in sd["row_hints"]})}


def batch_payload(batch, address):
    return {"stage": batch["stage"], "address": address, "batch": batch["items"]}


def _now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _plan_skips(batch):
    out = [dict(x, source="plan") for x in batch.get("skipped", [])]
    out += [dict(x, source="plan") for x in batch.get("rejected", [])]
    out += [dict(x, reason=x.get("reason", "no_row"), source="plan") for x in batch.get("unmapped", [])]
    out += [{"doc": d, "reason": "waiting_for_signed_copy", "source": "plan"}
            for d in batch.get("waiting_for_signed_copy", [])]
    return out


def upload_batch(client, gate, settings, batch, address, clock=None):
    """AUTOMATIC upload (no yes) of the executed documents into the Compliance tab of the member's OWN
    Transact file for this deal. Guards: own file only, this deal only, Compliance items only, never
    overwrite a filled item, never a blank or not-fully-executed copy. Every outcome is logged
    (item, document, time, result) and skips are listed with reasons. Submit is a separate gated step
    (submit_gate). The optional Brokerage system fallback upload stays gated."""
    plan_skips = _plan_skips(batch)
    base = {"uploaded": [], "skipped": [], "log": [], "plan_skipped": plan_skips, "writes": 0,
            "submitted": False}
    if not batch.get("items"):
        return dict(base, status="nothing_to_upload", report=_report(base))
    src = nav.compliance_source(client, settings)
    if src.get("source") == "brokerage_system":
        g = comp.action(gate, "upload", batch_payload(batch, address))
        if not g["allowed"]:
            return dict(base, status="blocked", gated=True, reason=g["reason"],
                        proposal=gate.propose(comp.ACTIONS["upload"], batch_payload(batch, address)),
                        report=["Brokerage system fallback upload still needs your yes."])
        return dict(base, status="fallback_approved", gated=True, source="brokerage_system",
                    report=["Brokerage system upload approved once; done in that system's own steps."])
    if src.get("stop"):
        return dict(base, status="stopped", source=src)
    now = clock or _now
    refusal = comp.file_guard(client, settings, address)
    if refusal:
        sk = [{"row": it["row"], "doc": it["doc"], "reason": refusal} for it in batch["items"]]
        log = [dict(x, item=x["row"], time=now(), result="refused:" + refusal) for x in sk]
        return dict(base, status="refused", reason=refusal, skipped=sk, log=log,
                    report=_report(dict(base, skipped=sk, log=log)))
    live = {r["row"]: r["status"] for r in src["rows"]}
    saved = client.current
    client.goto("compliance")
    uploaded, skipped, log = [], [], []
    try:
        for it in batch["items"]:
            why = comp.upload_guard(it, live)
            if why:
                skipped.append({"doc": it["doc"], "row": it["row"], "reason": why})
                log.append({"item": it["row"], "doc": it["doc"], "time": now(), "result": "skipped:" + why})
                continue
            client.upload_to_row(it["row"], it["doc"])
            live[it["row"]] = "filled"
            uploaded.append({"doc": it["doc"], "row": it["row"]})
            log.append({"item": it["row"], "doc": it["doc"], "time": now(), "result": "uploaded"})
    finally:
        client.goto(saved)
    out = dict(base, status="uploaded", uploaded=uploaded, skipped=skipped, log=log, writes=len(uploaded),
               source=src["source"],
               next="Submit is its own step and needs your explicit yes (one yes, one try).")
    out["report"] = _report(out)
    return out


def _report(r):
    lines = ["uploaded %s -> %s at %s" % (x["doc"], x["item"], x["time"]) for x in r["log"] if x["result"] == "uploaded"]
    lines += ["skipped %s (%s)" % (x.get("row") or x.get("doc"), x["reason"]) for x in r["skipped"]]
    lines += ["not staged %s (%s)" % (x.get("doc"), x["reason"]) for x in r["plan_skipped"]]
    return lines


def submit_gate(gate, stage, address, uploaded=()):
    """Compliance submit needs the agent's explicit yes, one yes per try. The yes is bound to the
    documents uploaded, so changed documents need a new yes."""
    pl = {"submit": stage, "address": address, "uploaded": sorted([list(u) for u in uploaded])}
    g = comp.action(gate, "submit", pl)
    return dict(g, proposal=None if g["allowed"] else gate.propose("compliance_submit", pl))


# ---------------------------------------------------------------- auto-run
def _stop(report, reason, **kw):
    report.update(status="stopped", stop=True, reason=reason, **kw)
    return report


def auto_run(client, gate, settings, deal_type, facts, terms=None, details=None, from_party=None,
             custom=None, saved_layouts=None, layout_choices=None, signed_docs=(), stage=None,
             page_counts=None):
    terms = dict(terms or {})
    defaults_used = sorted(k for k in ff.SMALL_DEFAULTS if k not in terms)
    for k in defaults_used:
        terms[k] = ff.SMALL_DEFAULTS[k]       # small defaults: picked and said, never silent
    details = dict(details or {})
    facts = dict(facts)
    sel = select_template(deal_type, from_party, custom)
    if sel.get("ask"):
        return dict(sel, status="ask", sent=0)
    tpl = sel["template"]
    d = load_defaults()
    facts.setdefault("loan_type", terms.get("financing"))
    rf = resolve_forms(tpl, facts)
    report = {"status": "running", "template": tpl["id"], "forms_to_add": [f["name"] for f in rf["add"]],
              "forms_skipped": rf["skip"], "forms_asked": rf["ask"], "forms_added": [], "forms_reused": [],
              "form_picks": {}, "not_added": [], "folders": {}, "fields_filled": [], "blanks": [],
              "labels_not_found": [], "financing_boxes": None, "role_slots": None, "written_amount_flags": [],
              "signer_map": None, "signing_order": [], "signing_draft": None, "compliance_plan": None,
              "confirm_on_next_live_pass": {"fields": [], "forms": [], "layouts": [], "compliance_rows": []},
              "sent": 0, "defaults_used": defaults_used}
    if rf["ask"]:
        report["ask"] = rf["ask"]
    unver = report["confirm_on_next_live_pass"]
    # role slots: names come from here, never typed
    if facts.get("parties"):
        slots = ff.role_slot_check(client, facts["parties"])
        if not slots["ok"]:
            fx = ff.fix_role_slots(client, facts["parties"], slots)
            if fx.get("stop"):
                return _stop(report, "role_slots", role_slots=slots, detail=fx)
            slots = dict(ff.role_slot_check(client, facts["parties"]), fixed=True)
            if not slots["ok"]:
                return _stop(report, "role_slots_wrong", role_slots=slots)
        report["role_slots"] = slots
    # folders are read from the Paperwork page, never assumed
    r = nav.click(client, "Paperwork", ())
    live_folders = nav.read_folders(client)["folders"] if r["clicked"] else []
    report["live_folders"] = live_folders
    for f in rf["add"]:
        hint = f.get("target_folder_hint")
        hit = [x for x in live_folders if hint and _norm(x) == _norm(hint)]
        report["folders"][f["name"]] = hit[0] if hit else None
        if not hit:
            report["folders"][f["name"] + " (note)"] = "hint %r is not a folder on this page; not assumed" % hint
        if not f["verified"]:
            unver["forms"].append("%s (code %s)" % (f["name"], f["code"]))
    # Details (dates + price/financing) first so the form auto-fills
    plans = {f["name"]: prefill_plan(f["name"], terms, details, settings, d) for f in rf["add"]}
    detail_vals = {}
    for p in plans.values():
        for e in p["details"]:
            detail_vals.setdefault(e["label"], e)
    if any(not p["no_map"] for p in plans.values()):
        nav.click(client, "Details", ())
        for label, e in detail_vals.items():
            fr = nav.fill(client, label, e["value"])
            if not fr["filled"]:
                if e["verified"]:
                    return _stop(report, "details_label_missing", looked_for=label)
                report["labels_not_found"].append(label)
                continue
            report["fields_filled"].append({"label": label, "where": "details", "verified": e["verified"]})
            if not e["verified"]:
                unver["fields"].append(label)
    # add the forms
    for f in rf["add"]:
        nav.click(client, "Parties", ())
        if f["name"] in client.added_forms:
            report["forms_reused"].append(f["name"])
            continue
        ap = ff.add_paperwork(client, f["name"])
        if ap.get("stop"):
            report["not_added"].append({"form": f["name"], "reason": ap.get("reason", "stopped"),
                                        "looked_for": ap.get("looked_for")})
            continue
        report["forms_added"].append(f["name"])
        if ap.get("form_pick"):
            report["form_picks"][f["name"]] = ap["form_pick"]
    # prefill on the form (the first form with fields; one form open at a time in Transact)
    expected = {}
    with_fields = [f for f in rf["add"] if plans[f["name"]]["form_fields"] or plans[f["name"]]["profile"]
                   or plans[f["name"]]["checkboxes"]]
    if with_fields:
        client.goto("forms_editor")
        if not nav.saved_status(client):
            return _stop(report, "not_saved", message="Forms Editor never showed Saved.")
        ready = nav.form_ready(client)
        if ready["stop"]:
            return _stop(report, "form_not_filled", message=ready["message"] + " Prepare Signing is not pressed.")
    for f in with_fields:
        p = plans[f["name"]]
        for e in p["form_fields"] + [dict(x, label=x["label"]) for x in p["profile"]]:
            fr = nav.fill(client, e["label"], e["value"])
            if not fr["filled"]:
                if fr.get("refused") or e.get("verified"):
                    return _stop(report, "label_problem", looked_for=e["label"], detail=fr)
                report["labels_not_found"].append(e["label"])
                unver["fields"].append(e["label"])
                continue
            expected[e["label"]] = e["value"]
            report["fields_filled"].append({"label": e["label"], "where": f["name"], "verified": e["verified"]})
            if not e["verified"]:
                unver["fields"].append(e["label"])
        if p["checkboxes"] and client.page().get("checkboxes"):
            tk = ff.tick_financing(client, p["checkboxes"])
            if tk["stop"]:
                return _stop(report, "financing_box_missing", detail=tk["stop"])
            report["financing_boxes"] = dict(ff.financing_flags(client.checked, p["checkboxes"]),
                                             ticked_now=tk["ticked"])
        report["blanks"] += p["blanks"]
    for p in plans.values():
        if p["no_map"]:
            unver["forms"].append(p["form"] + " (no prefill map)")
        elif p["form"] not in [f["name"] for f in with_fields]:
            report["blanks"] += p["blanks"]
    seen_b, kept = set(), []
    for b in report["blanks"]:
        has = b["source"] == "details" and (
            client.values.get(("details", b["label"])) or client.pages["details"].get("fields", {}).get(b["label"]))
        if b["label"] not in seen_b and not has:        # a value already on the page is not blank
            kept.append(b)
        seen_b.add(b["label"])
    report["blanks"] = kept
    if with_fields:
        report["written_amount_flags"] = ff.written_flags(client, "forms_editor")
        chk = ff.check_form(client, "forms_editor", expected, settings.get("left_blank", []),
                            {"kind": "template"}, facts)
        for lab in chk["blanks"]:
            if lab == "Financing" and report["financing_boxes"]:
                continue                      # the financing boxes carry it
            if not any(b["label"] == lab for b in report["blanks"]):
                report["blanks"].append({"label": lab, "source": "form", "reason": "still_blank"})
        report["conflicts"] = chk["conflicts"]
    # signers + draft envelope (never Prepare Signing / Next / Send)
    sp_plan = signer_plan(tpl, rf["add"], facts, settings, saved_layouts or [], layout_choices, page_counts, d)
    report["signing_order"] = sp_plan["order"]
    unver["layouts"] += sp_plan["unverified"]
    report["signer_map"] = {n: {"source": v["source"], "saved_layout": v["saved"], "fields": v["fields"]}
                            for n, v in sp_plan["docs"].items()}
    if sp_plan["ask"]:
        report["signing_draft"] = {"status": "ask", "ask": "layout", "choices": sp_plan["ask"], "draft_saved": False}
    else:
        ok = [f for f in rf["add"] if sp_plan["docs"][f["name"]]["source"] in ("template", "saved")]
        by_hand = [f["name"] for f in rf["add"] if f not in ok]
        if not ok or not sp_plan["order"]:
            report["signing_draft"] = {"status": "not_saved", "draft_saved": False, "sent": False,
                                       "reason": "no_signers" if not sp_plan["order"] else "no_layout_resolved",
                                       "needs_page_count": sp_plan["needs_page_count"], "by_hand": by_hand,
                                       "roles_without_people": sp_plan["roles_without_people"]}
        else:
            docs = [{"name": f["name"], "pages": sp_plan["docs"][f["name"]].get("pages", 1)} for f in ok]
            out = sp.prep(client, gate, settings, facts["address"], docs, sp_plan["requested"], None,
                          plan={"order": sp_plan["order"],
                                "docs": {f["name"]: sp_plan["docs"][f["name"]] for f in ok}})
            report["signing_draft"] = {k: out.get(k) for k in ("status", "draft_saved", "envelope", "cc_only",
                                                               "reason", "signer_check", "ask", "signer")
                                       if k in out}
            report["signing_draft"].update(sent=False, by_hand=by_hand, needs_page_count=sp_plan["needs_page_count"])
    # compliance plan, then the automatic upload (own file, no yes); submit stays gated
    if client.current == "signing_builder":
        nav.click(client, "Back", ())           # back to the transaction tabs; the draft stays a draft
    src = nav.compliance_source(client, settings)
    st = stage or tpl["compliance_stage"]
    if src.get("stop"):
        report["compliance_plan"] = {"status": "stopped", "source": src, "writes": 0}
    elif src.get("source") == "brokerage_system":
        report["compliance_plan"] = {"status": "fallback_brokerage_system", "writes": 0, "upload_gated": True}
    else:
        cb = compliance_batch(st, list(signed_docs), src["rows"], facts, d)
        report["compliance_plan"] = dict(cb, source=src["source"], address=facts["address"], writes=0)
        unver["compliance_rows"] = cb.get("row_hints_unverified", [])
        up = upload_batch(client, gate, settings, cb, facts["address"])
        report["compliance_upload"] = up
        report["compliance_plan"]["writes"] = up["writes"]
        if up["writes"]:
            report["compliance_submit"] = dict(
                submit_gate(gate, st, facts["address"], client.uploads),
                submitted=False)
    for k in unver:
        unver[k] = sorted(set(unver[k]))
    ready = not (report["blanks"] or report["not_added"] or report["forms_asked"] or report["labels_not_found"]
                 or report["written_amount_flags"] or report.get("conflicts")
                 or (report["financing_boxes"] or {}).get("flags")
                 or (report["signing_draft"] or {}).get("status") != "draft_saved")
    payload = {"packet": tpl["id"], "address": facts["address"], "forms": report["forms_added"] + report["forms_reused"],
               "values": expected, "order": sp_plan["order"]}
    report["proposal"] = gate.propose("form_review", payload)
    report.update(status="awaiting_yes", ready=ready, payload=payload,
                  next="Stopped at the review gate. Waiting for the agent's yes in this chat. Prepare Signing, "
                       "Next, Send and Submit are not pressed. Compliance documents upload automatically into this file's Compliance tab (logged in the report); "
                       "compliance submit needs your own yes and is not done.")
    return report
