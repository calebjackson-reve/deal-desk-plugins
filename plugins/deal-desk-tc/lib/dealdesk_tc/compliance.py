"""tc-compliance-file: signed copies only, split per row, map to rows, fix envelope.

Everything here is in-system. The upload into the member's own Transact file's Compliance tab is
automatic (no yes) under the guards in upload_guard; submit / update row / sync (and the optional
Brokerage system upload) each need their own yes through the gate. A reply to the compliance reviewer is a
message to a person, so it is never a bot action: reply_draft() writes the text
and the agent sends it. Member-facing words: "compliance file" and "Brokerage
system".
"""
from dealdesk_core import gate as core_gate

# "upload" here is the optional Brokerage system fallback upload only, which stays gated. The Transact
# Compliance tab upload is automatic and never goes through the gate (see upload_guard).
ACTIONS = {"upload": "compliance_upload_brokerage_system", "submit": "compliance_submit",
           "update_row": "compliance_update_row", "sync": "compliance_sync"}


def reply_draft(reviewer, address, answers, voice=None):
    """Draft text answering the reviewer. Never sent by the bot."""
    first = (reviewer.get("name") or "there").split()[0]
    v = voice or {}
    body = "%s %s,\n\nRe: %s\n%s\n\n%s\n%s" % (
        v.get("greeting", "Hi"), first, address.split(",")[0],
        "\n".join("- " + a for a in answers), v.get("signoff", "Thanks,"), v.get("name", ""))
    return {"type": "draft", "sent": False, "to": reviewer.get("email"),
            "body": body.rstrip(), "bot_action": False,
            "note": "Draft for the agent to review and send."}


def file_guard(client, settings, address):
    """The upload may only go into the member's OWN Transact file for THIS deal. Returns a reason
    string when it may not, else None."""
    from dealdesk_core import deal_match
    f = getattr(client, "open_file", None)
    if not f:
        return "no_open_file"
    if (f.get("account") != settings.get("transact_account")
            or (f.get("owner") or "").lower() != (settings.get("member_email") or "").lower()):
        return "not_members_own_file"
    if deal_match.normalize_address(f.get("address") or "")["key"] != deal_match.normalize_address(address)["key"]:
        return "not_this_deals_file"
    return None


def upload_guard(item, live_rows):
    """Per-item guards. Returns a skip reason, else None. Never overwrite, Compliance tab items only,
    fully executed copies only (never a blank form) where the item needs a signed copy."""
    if item.get("tab", "compliance") != "compliance" or item["row"] not in live_rows:
        return "outside_compliance_tab"
    if live_rows[item["row"]] != "empty":
        return "row_not_empty_now"
    if item.get("blank"):
        return "blank_form"
    if item.get("signed_copy_required", True) and item.get("executed") is not True:
        return "not_fully_executed"
    return None


def plan(docs, checklist):
    """docs: [{name, signed, blank, encrypted, pages:[{page,row}]}]. checklist: [{row,status}]."""
    rows = {c["row"]: dict(c, incoming=[]) for c in checklist}
    rejected, notes, parts = [], [], []
    for d in docs:
        if d.get("blank") or not d.get("signed", False):
            rejected.append({"doc": d["name"], "reason": "blank_or_unsigned_form"})
            continue
        if d.get("encrypted"):
            notes.append({"doc": d["name"], "note": "Encrypted PDF stays whole; not split."})
            segs = [{"doc": d["name"], "row": d.get("row"), "pages": "all"}]
        else:
            by_row = {}
            for p in d.get("pages", []):
                by_row.setdefault(p["row"], []).append(p["page"])
            segs = [{"doc": d["name"], "row": r, "pages": pg} for r, pg in by_row.items()]
        for s in segs:
            parts.append(s)
            r = rows.get(s["row"])
            if r is None:
                notes.append({"doc": s["doc"], "note": "No checklist row %s" % s["row"]})
            elif r["status"] == "filled":
                notes.append({"doc": s["doc"], "row": s["row"],
                              "note": "Row already filled; not overwritten."})
            elif r["status"] == "na":
                notes.append({"doc": s["doc"], "row": s["row"], "note": "Row is not applicable."})
            else:
                r["incoming"].append(s)
    summary = {"filled": [], "empty": [], "na": []}
    for k, r in rows.items():
        if r["status"] == "filled":
            summary["filled"].append(k)
        elif r["status"] == "na":
            summary["na"].append(k)
        else:
            summary["empty" if not r["incoming"] else "empty"].append(k)
    mapped = [k for k, r in rows.items() if r["status"] != "filled" and r["incoming"]]
    still_empty = [k for k in summary["empty"] if k not in mapped]
    return {"rows": rows, "parts": parts, "rejected": rejected, "notes": notes,
            "summary": summary, "mapped": mapped, "still_empty": still_empty,
            "writes": 0}


def fix_plan(returned):
    """returned: {note, form, pages, signer_blocks:[{signer,email,pages,signed}]}."""
    missing = [b for b in returned["signer_blocks"] if not b.get("signed")]
    done = [b["signer"] for b in returned["signer_blocks"] if b.get("signed")]
    scan = core_gate.scan_wire_text(returned.get("note", ""))
    return {"form": returned["form"], "pages": returned.get("pages"),
            "signers_needed": [b["signer"] for b in missing],
            "skip_already_signed": done, "wire_flag": scan}


def action(gate, name, payload):
    """Each in-system step needs its own yes. The bot never sends anything."""
    kind = ACTIONS.get(name)
    if kind is None:
        return {"allowed": False, "reason": "refused_never_bot_action"}
    return gate.attempt(kind, payload)
