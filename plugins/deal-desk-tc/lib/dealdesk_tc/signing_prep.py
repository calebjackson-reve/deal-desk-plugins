"""tc-signing-prep: envelope, signers, CC-only, layouts, field map, signer check, DRAFT only.

Never clicks Next, never sends, never signs. Stops at the saved draft.
"""
import re

from . import navigator as nav

FIELD_KINDS = ("Initials", "Sign Here", "Date", "Name")


def _email(s):
    return (s or "").strip().lower()


def _digits(s):
    return re.sub(r"\D", "", s or "")


def signer_check(signers, member):
    """Stop on two different signers sharing an email or phone, a signer email
    equal to the member's own when they are not that signer, or a bad email."""
    problems = []
    by_email, by_phone = {}, {}
    for s in signers:
        e = _email(s.get("email"))
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", e):
            problems.append({"type": "bad_email", "signer": s["name"], "email": s.get("email")})
            continue
        by_email.setdefault(e, set()).add(s["name"])
        if _digits(s.get("phone")):
            by_phone.setdefault(_digits(s["phone"]), set()).add(s["name"])
    for e, names in by_email.items():
        if len(names) > 1:
            problems.append({"type": "SIGNER-EMAIL COLLISION", "email": e,
                             "signers": sorted(names)})
        if e == _email(member.get("email")):
            others = [n for n in names if n != member.get("name")]
            if others:
                problems.append({"type": "SIGNER-EMAIL COLLISION", "email": e,
                                 "signers": sorted(others), "matches": "member's own email"})
    for ph, names in by_phone.items():
        if len(names) > 1:
            problems.append({"type": "SIGNER-PHONE COLLISION", "phone": ph,
                             "signers": sorted(names)})
    return {"stop": bool(problems), "problems": problems,
            "signers": [{"name": s["name"], "email": s.get("email")} for s in signers]}


def _same_envelope(a, b):
    """Same doc part and the same address after suffix / directional normalizing (Lane = Ln)."""
    from dealdesk_core import deal_match
    sep = " \u2013 "
    pa, pb = a.split(sep, 1), b.split(sep, 1)
    if len(pa) != 2 or len(pb) != 2:
        return a == b
    return pa[1] == pb[1] and deal_match.normalize_address(pa[0])["key"] == \
        deal_match.normalize_address(pb[0])["key"]


def resolve_signers(client, requested):
    out = []
    for r in requested:
        name = r["name"] if isinstance(r, dict) else r
        person = None
        for src, pool in (("transaction", list(client.parties.values())),
                          ("contacts", client.data.get("contacts", []))):
            hit = [p for p in pool if p["name"].lower() == name.lower()]
            if hit:
                person = dict(hit[0], source=src)
                break
        if not person:
            if isinstance(r, dict) and r.get("email"):
                person = dict(r, source="new")
            else:
                return None, {"ask": "signer_email", "signer": name}
        if isinstance(r, dict) and r.get("email") and person["source"] != "new":
            person["email"] = r["email"]      # an email the agent gave wins; the check will see it
        out.append(person)
    return out, None


def pick_layouts(docs, settings, choices):
    picked, ask = {}, []
    for d in docs:
        cands = [l["name"] for l in settings.get("layouts", []) if l.get("doc") == d["name"]]
        if d["name"] in choices and choices[d["name"]] in cands:
            picked[d["name"]] = choices[d["name"]]
        elif len(cands) == 1:
            picked[d["name"]] = cands[0]
        elif len(cands) > 1:
            ask.append({"doc": d["name"], "layouts": cands})
        else:
            picked[d["name"]] = None          # none fits: place by hand
    return picked, ask


def prep(client, gate, settings, address, docs, requested_signers, review_payload,
         layout_choices=None, edit_layout=None, plan=None):
    """plan = a template signing plan (tc-templates auto-run). It saves the UNSENT draft before the
    review yes (a draft is not a send); every other gate still applies. No plan = the original flow."""
    member = {"name": settings.get("member_name"), "email": settings.get("member_email")}
    signers, ask = resolve_signers(client, requested_signers)
    if ask:
        return dict(ask, status="ask")
    check = signer_check(signers, member)
    if check["stop"]:
        return {"status": "stopped", "stop": True, "reason": "signer_check",
                "signer_check": check, "draft_saved": False}
    if plan is None:
        picked, ask = pick_layouts(docs, settings, layout_choices or {})
        if ask:
            return {"status": "ask", "ask": "layout", "choices": ask, "draft_saved": False}
        g = gate.attempt("form_review", review_payload)
        if not g["allowed"]:
            return {"status": "blocked", "reason": g["reason"], "draft_saved": False}
    else:
        picked = {n: (v["saved"] or None) for n, v in plan["docs"].items()}
    envelope = "%s – %s" % (address.split(",")[0], docs[0]["name"]
                                  if len(docs) == 1 else "Packet")  # docs is emptied below for a plan
    if any(_same_envelope(envelope, e) for e in client.data.get("signings", [])):
        return {"status": "existing_draft", "stop": True, "envelope": envelope,
                "draft_saved": False}
    layout_edit, layout_proposal = None, None
    if edit_layout:
        eg = gate.attempt("save_signing_layout", edit_layout)
        layout_edit = "applied" if eg["allowed"] else "needs_yes"
        if not eg["allowed"]:
            layout_proposal = gate.propose("save_signing_layout", edit_layout)
    nav.click(client, "Signings", ())
    r = nav.click(client, "Create Signing", ("New Signing",))
    if not r["clicked"]:
        return dict(r, status="stopped", draft_saved=False)
    nav.fill(client, "Envelope Name", envelope)
    cc = [{"name": member["name"], "email": member["email"], "role": "CC only"}]
    for e in settings.get("cc_only", []):
        if _email(e) not in {_email(c["email"]) for c in cc}:
            cc.append({"email": e, "role": "CC only"})
    field_map = {}
    if plan is not None:
        mp = nav.click(client, "Map Signers", ())
        if not mp["clicked"]:
            return dict(mp, status="stopped", draft_saved=False)
        client.set_signing_order(plan["order"])
        for d in docs:
            dp = plan["docs"][d["name"]]
            if dp["saved"]:
                client.apply_layout(dp["saved"], d["name"])
                field_map[d["name"]] = {"saved_layout": dp["saved"]}
                continue
            fm = field_map.setdefault(d["name"], {})
            for who, kinds in dp["fields"].items():
                for kind, pages in kinds.items():
                    for pg in pages:
                        client.place_field(who, kind, d["name"], pg)
                    fm.setdefault(who, {})[kind] = list(pages)
        docs = []
    for d in docs:
        names = d.get("signers") or [s["name"] for s in signers]
        for s in signers:
            if s["name"] not in names:
                continue
            m = field_map.setdefault(s["name"], {})
            for p in range(1, d.get("pages", 1) + 1):
                client.place_field(s["name"], "Initials", d["name"], p)
                m.setdefault("Initials", []).append(p)
            last = d.get("pages", 1)
            for kind in ("Sign Here", "Date", "Name"):
                client.place_field(s["name"], kind, d["name"], last)
                m.setdefault(kind, []).append(last)
    sv = nav.click(client, "Save", ())
    if not sv["clicked"]:
        return dict(sv, status="stopped", draft_saved=False)
    return {"status": "draft_saved", "draft_saved": client.draft_saved, "sent": False,
            "envelope": envelope, "signing_order": (plan or {}).get("order"), "signers": check["signers"], "cc_only": cc,
            "layouts": picked, "field_map": field_map, "layout_edit": layout_edit,
            "layout_proposal": layout_proposal,
            "signer_check": check,
            "next": "Saved as a draft. The agent decides whether to send it. Next is not pressed."}
