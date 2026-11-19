"""Session: one member's Transact run over the fake client. Drives the scenario ops."""
import copy
import json
from pathlib import Path

from . import (client_update, compliance, contract_to_close, fill_form, navigator,
               open_deal, signing_prep, templates)
from .fake_client import HARD_NEVER, FakeTransact, TransactActionError
from .gate_tc import TcGate

DEFAULT_SETTINGS = {
    "member_name": "Taylor Member", "member_email": "taylor.member@example.com",
    "expected_user": "taylor.member@example.com", "transact_account": "Example Realty North",
    "commission_format": "percent", "left_blank": ["New Date", "Offer Expires", "Commission"],
    "cc_only": ["tc.copy@example.com"],
    # Member profile (member-setup). Demo values only; license numbers are clearly fake.
    "profile": {"agent_name": "Taylor Member", "agent_license": "DEMO-LIC-0001",
                "brokerage_license": "DEMO-BRK-0001", "agent_phone": "225-555-0110",
                "agent_email": "taylor.member@example.com", "brokerage_phone": "225-555-0111",
                "brokerage_email": "office@example.com", "sellers_agent": "Casey Example",
                "designated_agent_name": "Taylor Member", "designated_agent_license": "DEMO-LIC-0001",
                "designated_agent_phone": "225-555-0110",
                "designated_agent_email": "taylor.member@example.com"},
    "layouts": [{"name": "Offer buyer side", "doc": "Residential Agreement to Buy or Sell (LREC)"},
                {"name": "Counter standard", "doc": "Residential Counter Offer"}],
}


def load_site(fixtures_dir, page_patches=None, data_patch=None):
    pages = {}
    for p in sorted(Path(fixtures_dir).glob("transact_page_*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        pages[d["key"]] = d
    for key, patch in (page_patches or {}).items():
        pg = pages[key]
        patch = dict(patch)
        rm = patch.pop("labels_remove", [])
        add = patch.pop("labels_add", [])
        pg.update(patch)
        pg["labels"] = [x for x in pg["labels"] if x not in rm] + add
    data = json.loads((Path(fixtures_dir) / "transact_data.json").read_text(encoding="utf-8"))
    data.update(data_patch or {})
    return pages, data


class Session:
    def __init__(self, pages, data, settings=None, unset=()):
        self.settings = copy.deepcopy(DEFAULT_SETTINGS)
        self.settings.update(settings or {})
        for k in unset:
            self.settings.pop(k, None)
        self.pack = fill_form.load_pack()
        data.setdefault("library", [f["name"] for f in self.pack["forms"]])
        self.client = FakeTransact(pages, data)
        self.gate = TcGate()
        self.last_hash = None
        self.last_payload = None
        self.facts = {}
        self.platform = None
        self.last_batch = None

    # ---- helpers ----
    def _bot(self, member, caller=None, profile=None, template=None):
        from dealdesk_core.member_store import Platform
        if self.platform is None:
            self.platform = Platform()
        if member not in self.platform.member_ids():
            self.platform.install(member, profile or {}, template)
        return self.platform.bot(member, caller or member)

    def _custom(self, a):
        return templates.member_templates(self._bot(a["member"])) if a.get("member") else None

    def _track(self, out):
        prop = out.get("proposal") if isinstance(out, dict) else None
        if prop:
            self.last_hash = prop["hash"]

    def run(self, op):
        a = {k: v for k, v in op.items() if k not in ("op", "as")}
        name = op["op"]
        c = self.client
        if name == "goto":
            c.goto(a["page"])
            return {"page": a["page"]}
        if name == "open_transact":
            return navigator.open_transact(c, self.settings)
        if name == "search_file":
            r = navigator.open_transact(c, self.settings)
            return r if r["stop"] else navigator.search_file(c, a["query"])
        if name == "find_control":
            return navigator.find_control(c, a["label"], a.get("alternates", ()))
        if name == "open_tab":
            return navigator.open_tab(c, a["tab"], a.get("allow", ()))
        if name == "icon_control":
            return navigator.find_icon_control(c, a["name"])
        if name == "search_box":
            return navigator.find_search_box(c)
        if name == "read_folders":
            return navigator.read_folders(c)
        if name == "saved_status":
            return {"saved": navigator.saved_status(c)}
        if name == "form_ready":
            return navigator.form_ready(c)
        if name == "compliance_source":
            return navigator.compliance_source(c, self.settings)
        if name == "dates_check":
            return navigator.dates_check(c, a.get("labels"))
        if name == "press_key":
            return navigator.press_key(c, a["key"])
        if name == "raw_keypress":              # straight at the client: it must refuse too
            try:
                c.keypress(a["key"])
                return {"raised": False}
            except TransactActionError:
                return {"raised": True}
        if name == "focus":
            c.focus(a["label"])
            return {"focused": a["label"]}
        if name == "stray_dialog":
            c.open_dialog(a["title"], a.get("labels", ["Cancel"]))
            return {"dialog": a["title"]}
        if name == "handle_dialog":
            return navigator.handle_dialog(c)
        if name == "dialog_confirm":            # attempt to confirm: the client must refuse
            try:
                c.click_dialog(a["label"])
                return {"raised": False}
            except TransactActionError:
                return {"raised": True}
        if name == "read_history":
            return navigator.read_history(c)
        if name == "fill_field":
            return navigator.fill(c, a["label"], a["value"])
        if name == "role_slots":
            return fill_form.role_slot_check(c, a["parties"])
        if name == "library_pick":
            c.goto("parties")
            return fill_form.add_paperwork(c, a["name"])
        if name == "financing_flags":
            return fill_form.financing_flags(a["ticked"], a.get("financing"))
        if name == "raw_add_entry":
            try:
                c.add_form_entry(a["entry"])
                return {"raised": False}
            except TransactActionError:
                return {"raised": True}
        if name == "set_slot":
            c.parties[a["slot"]] = dict(a["person"])
            return {"slot": a["slot"]}
        if name == "clear_slot":
            c.parties.pop(a["slot"], None)
            return {"slot": a["slot"]}
        if name == "page_text":
            return {"header": c.page().get("header"), "footer": c.page().get("footer")}
        if name == "same_address":
            from dealdesk_core import deal_match
            x, y = (deal_match.normalize_address(a[k]) for k in ("a", "b"))
            return {"same": x["key"] == y["key"], "a": x["key"], "b": y["key"]}
        if name == "click":
            return navigator.click(c, a["label"], a.get("alternates", ()), a.get("allow", ()))
        if name == "open_deal":
            facts = a["facts"]
            self.facts = facts
            return open_deal.open_deal(c, self.settings, facts, facts.get("parties", {}),
                                       a.get("allow", ()))
        if name == "fill_form":
            facts = dict(self.facts, **a.get("facts", {}))
            out = fill_form.fill_form(c, self.gate, self.settings, a["kind"], a.get("terms", {}),
                                      a.get("context"), a.get("found"), facts, a.get("named"),
                                      self.pack)
            self._track(out)
            if out.get("payload"):
                self.last_payload = out["payload"]
            return out
        if name == "add_paperwork":
            c.goto("parties")
            return fill_form.add_paperwork(c, a["name"])
        if name == "raw_set_row":               # test hook: someone filled a row meanwhile
            for r in c.pages["compliance"]["rows"]:
                if r["row"] == a["row"]:
                    r["status"] = a["status"]
            return {"row": a["row"], "status": a["status"]}
        if name == "tpl_select":
            return templates.select_template(a.get("deal_type"), a.get("from_party"), self._custom(a))
        if name == "tpl_validate":
            tpl = a.get("template") or templates.catalog()[a["default_id"]]
            return templates.validate_custom(tpl)
        if name == "tpl_member_add":
            return templates.add_member_template(self._bot(a["member"]), a["template"])
        if name == "tpl_member_list":
            from dealdesk_core.member_store import CrossMemberAccess
            try:
                return {"ids": sorted(templates.member_templates(self._bot(a["member"], a.get("caller"))))}
            except CrossMemberAccess:
                return {"refused": True, "reason": "cross_member_access"}
        if name == "tpl_member_install":
            from dealdesk_core.member_store import TemplateHasMemberData
            try:
                self._bot(a["member"], profile=a.get("profile", {}), template=a.get("template"))
                return {"installed": True}
            except TemplateHasMemberData:
                return {"installed": False, "refused": "template_has_member_data"}
        if name == "tpl_resolve":
            tpl = templates.select_template(a["deal_type"], a.get("from_party"), self._custom(a))["template"]
            facts = dict(a.get("facts", {}))
            facts.setdefault("loan_type", a.get("terms", {}).get("financing"))
            r = templates.resolve_forms(tpl, facts)
            return {"add": [f["name"] for f in r["add"]], "skip": [x["form"] for x in r["skip"]],
                    "ask": r["ask"], "template": tpl["id"]}
        if name == "tpl_prefill":
            return templates.prefill_plan(a["form"], a.get("terms", {}), a.get("details", {}), self.settings)
        if name == "tpl_pick_layout":
            return templates.pick_layout(a["form"], a.get("saved", []))
        if name == "tpl_signer_plan":
            tpl = templates.select_template(a["deal_type"], a.get("from_party"), self._custom(a))["template"]
            facts = dict(self.facts, **a.get("facts", {}))
            forms = [f for f in templates.resolve_forms(tpl, facts)["add"]]
            return templates.signer_plan(tpl, forms, facts, self.settings, a.get("saved", []),
                                         a.get("choices"), a.get("page_counts"))
        if name == "tpl_layout_save":
            r = templates.layout_save(self.gate, a["layout"])
            if r.get("proposal"):
                self.last_hash = r["proposal"]["hash"]
            return r
        if name == "tpl_compliance_plan":
            c.goto("compliance")
            src = navigator.compliance_source(c, self.settings)
            rows = src.get("rows", a.get("rows", []))
            b = templates.compliance_batch(a["stage"], a.get("signed", []), rows,
                                           dict(self.facts, **a.get("facts", {})))
            self.last_batch = b
            return dict(b, source=src.get("source"))
        if name == "tpl_compliance_upload":
            b = a.get("batch") or self.last_batch
            out = templates.upload_batch(c, self.gate, self.settings, b,
                                         a.get("address", "4321 Pretend Pelican Lane"),
                                         (lambda: a["now"]) if a.get("now") else None)
            self._track(out)
            return out
        if name == "tpl_submit":
            r = templates.submit_gate(self.gate, a["stage"], a.get("address", "4321 Pretend Pelican Lane"),
                                      c.uploads)
            if r.get("proposal"):
                self.last_hash = r["proposal"]["hash"]
            return r
        if name == "set_open_file":             # test hook: which Transact file is open
            c.account = a.get("account", c.account)
            c.open_file = {"account": a.get("account", c.account), "address": a["address"],
                           "owner": a.get("owner", c.page().get("user"))}
            return c.open_file
        if name == "tpl_auto_run":
            facts = dict(self.facts, **a.get("facts", {}))
            out = templates.auto_run(c, self.gate, self.settings, a.get("deal_type"), facts, a.get("terms"),
                                     a.get("details"), a.get("from_party"), self._custom(a), a.get("saved"),
                                     a.get("choices"), a.get("signed", []), a.get("stage"),
                                     a.get("page_counts"))
            self._track(out)
            if out.get("payload"):
                self.last_payload = out["payload"]
            if out.get("compliance_plan") and out["compliance_plan"].get("items") is not None:
                self.last_batch = out["compliance_plan"]
            return out
        if name == "say":
            return self.gate.record_message(a["source"], a["text"], self.last_hash)
        if name == "signing_prep":
            out = signing_prep.prep(c, self.gate, self.settings, a["address"], a["docs"],
                                    a["signers"], a.get("payload", self.last_payload),
                                    a.get("layout_choices"), a.get("edit_layout"),
                                    email_confirmations=a.get("email_confirmations"))
            if out.get("reason") == "no_approval_for_this_version":
                out["proposal"] = self.gate.propose("form_review", a.get("payload", self.last_payload))
            if out.get("layout_proposal"):
                self.last_hash = out["layout_proposal"]["hash"]
            self._track(out)
            return out
        if name == "signing_try_send":
            res = []
            for fn in (c.send, c.sign, c.next_to_send):
                try:
                    fn()
                    res.append("allowed")
                except TransactActionError:
                    res.append("raised")
            return {"results": res}
        if name == "contract_to_close":
            return contract_to_close.check(**a)
        if name == "compliance_plan":
            p = compliance.plan(a["docs"], a["checklist"])
            return {k: p[k] for k in p if k != "rows"} | {
                "row_status": {k: v["status"] for k, v in p["rows"].items()},
                "row_incoming": {k: len(v["incoming"]) for k, v in p["rows"].items()}}
        if name == "compliance_fix":
            plan = compliance.fix_plan(a["returned"])
            if plan["wire_flag"]["flagged"]:
                return {"status": "flagged", "wire_flag": plan["wire_flag"], "action": "none",
                        "fix": plan}
            if not plan["signers_needed"]:
                return {"status": "nothing_to_send", "fix": plan, "draft_saved": False}
            out = signing_prep.prep(c, self.gate, self.settings, a["address"],
                                    [{"name": plan["form"], "pages": a["returned"].get("page_count", 1)}],
                                    [{"name": b["signer"], "email": b["email"]}
                                     for b in a["returned"]["signer_blocks"]
                                     if b["signer"] in plan["signers_needed"]], plan)
            if out.get("reason") == "no_approval_for_this_version":
                out["proposal"] = self.gate.propose("form_review", plan)
                self.last_payload = plan
            self._track(out)
            return dict(out, fix=plan)
        if name == "compliance_reply_draft":
            return compliance.reply_draft(a["reviewer"], a["address"], a["answers"], a.get("voice"))
        if name == "compliance_action":
            return compliance.action(self.gate, a["action"], a.get("payload", {}))
        if name == "propose":
            p = self.gate.propose(a["kind"], a.get("payload", {}))
            self.last_hash = p["hash"]
            return {"proposal": p}
        if name == "attempt":
            return self.gate.attempt(a["kind"], a.get("payload", {}))
        if name == "client_update":
            return client_update.draft(a["audience"], a["to"], a["address"], a["facts"],
                                       a.get("voice"), a.get("subject"))
        if name == "listing_email":
            return client_update.listing_agent_email(a["listing_agent"], a["address"],
                                                     a["buyer_signed"], a["attachments"])
        if name == "term_sheet":
            return fill_form.term_sheet(a["kind"], a.get("terms", {}), a.get("found"))
        if name == "choose_form":
            return fill_form.choose_form(a["kind"], self.pack, a.get("context"), a.get("named"))
        raise ValueError("unknown op " + name)

    def summary(self):
        c = self.client
        acts = c.actions
        return {"clicked": c.labels_clicked,
                "fills": dict((x[1], x[2]) for x in acts if x[0] == "fill"),
                "forbidden_clicked": [x for x in c.labels_clicked if x.lower() in HARD_NEVER or x.lower() in ("offer accepted", "offer rejected", "delete") or "sync" in x.lower()],
                "focus_before_fill": all(acts[i - 1][0] == "focus" and acts[i - 1][1] == a[1]
                                         for i, a in enumerate(acts) if a[0] == "fill"),
                "created_contacts": [x[1] for x in acts if x[0] == "create_contact"],
                "added_forms": list(c.added_forms), "parties": {k: v["name"] for k, v in c.parties.items()},
                "placed": len(c.placed), "draft_saved": c.draft_saved,
                "sent": len([x for x in c.labels_clicked if x.lower() in HARD_NEVER]),
                "page": c.current, "account": c.account,
                "fill_count": len([x for x in acts if x[0] == "fill"]), "title": c.page().get("title"),
                "keypresses": list(c.keypresses), "checked": sorted(c.checked), "dialog_open": bool(c.dialog),
                "previewed": sorted(c.previewed), "uploads": [list(u) for u in c.uploads],
                "signing_order": list(c.signing_order), "applied_layouts": [list(u) for u in c.applied_layouts],
                "prepare_signing_clicks": len([x for x in c.labels_clicked if x.lower() == "prepare signing"]),
                "next_clicks": len([x for x in c.labels_clicked if x.lower() == "next"]),
                "add_party_clicks": len([x for x in c.labels_clicked if x == "Add Party"]),
                "selected_accounts": [x[1] for x in acts if x[0] == "select_account"]}
