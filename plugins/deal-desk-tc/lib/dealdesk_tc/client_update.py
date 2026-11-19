"""tc-client-update and the buyer-offer packet email: drafts only, verified facts only."""
from dealdesk_core import gate as core_gate
from dealdesk_core.ledger import apply_never_say


def draft(audience, to, address, facts, voice=None, subject=None):
    """facts: [{text, verified}]. Unverified facts are left out and listed."""
    use = [f["text"] for f in facts if f.get("verified")]
    left_out = [f["text"] for f in facts if not f.get("verified")]
    wire = [f["text"] for f in facts if core_gate.scan_wire_text(f["text"])["flagged"]]
    use = [t for t in use if t not in wire]
    removed = []
    cleaned = []
    for t in use:
        t, r = apply_never_say(t, (voice or {}).get("never_say"))
        cleaned.append(t)
        removed += r
    use = [t for t in cleaned if t]
    first = (to.get("name") or "there").split()[0]
    greet = (voice or {}).get("greeting", "Hi")
    sign = (voice or {}).get("signoff", "Thanks,")
    name = (voice or {}).get("name", "")
    body = "%s %s,\n\nQuick update on %s:\n%s\n\n%s\n%s" % (
        greet, first, address.split(",")[0], "\n".join("- " + t for t in use), sign, name)
    return {"type": "draft", "sent": False, "audience": audience, "to": to.get("email"),
            "subject": subject or "%s - update" % address.split(",")[0],
            "body": body.rstrip(), "voice": "guide" if voice else "plain_text",
            "note": None if voice else "No voice guide on file, so this is plain text.",
            "left_out_unverified": left_out, "never_say_removed": removed,
            "wire_flag": {"flagged": bool(wire), "action": "none", "texts": wire}}


def listing_agent_email(listing_agent, address, buyer_signed, attachments):
    """Draft for the agent to send after the buyer signs. Never before."""
    if not buyer_signed:
        return {"type": "none", "status": "waiting_for_buyer", "sent": False}
    need = ["signed offer", "pre-approval", "agency disclosure"]
    missing = [n for n in need if n not in attachments]
    return {"type": "draft", "sent": False, "to": listing_agent["email"],
            "subject": "%s - offer" % address.split(",")[0], "attachments": list(attachments),
            "missing_attachments": missing,
            "body": "Hi %s,\n\nAttached is our offer on %s with the pre-approval and the "
                    "agency disclosure." % (listing_agent["name"].split()[0], address.split(",")[0])}
