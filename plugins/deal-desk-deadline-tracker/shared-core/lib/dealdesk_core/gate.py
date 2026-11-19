"""Review-gate model.

Rules enforced here:
  * a yes counts only when it comes from the agent's own chat message
  * it approves one exact action + version hash
  * one yes = one attempt; any changed term changes the hash and needs a new yes
  * send / sign / invite / certify / attest actions are ALWAYS refused, with or without a yes
  * the compliance upload into the member's OWN Transact file's Compliance tab is not a gate step
    (Caleb, Nov 16 2026: automatic, no yes; guards live in Deal Desk TC). Compliance submit is gated.
This module performs no I/O. It only decides whether an in-system action may run.
"""
import hashlib
import json
import re

GATED_ACTIONS = {"calendar_write", "overwrite_confirmed", "compliance_file_place",
                 "save_signing_layout", "treat_dates_official", "compliance_submit"}
# Never the bot's to perform, regardless of any approval.
REFUSED_ACTIONS = {"send_email", "send_text", "send_message", "send_envelope",
                   "esign", "sign", "place_signature", "place_initials",
                   "invite_signer", "tick_certification", "submit"}
REFUSED_HINTS = ("send", "sign", "invite", "submit", "certif", "attest", "initial")
AFFIRMATIVE = re.compile(r"^\s*(yes|yep|yeah|ok|okay|approved?|go ahead|do it|confirmed?)\b", re.I)


def action_hash(kind, payload):
    blob = json.dumps({"kind": kind, "payload": payload}, sort_keys=True,
                      separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def is_refused(kind):
    k = (kind or "").lower()
    return k in REFUSED_ACTIONS or (k not in GATED_ACTIONS and
                                    any(h in k for h in REFUSED_HINTS))


class ReviewGate:
    def __init__(self):
        self._approved = {}   # hash -> remaining attempts (0 or 1)
        self.log = []

    def propose(self, kind, payload):
        h = action_hash(kind, payload)
        return {"kind": kind, "hash": h, "refused": is_refused(kind)}

    def record_message(self, source, text, target_hash):
        """Record a possible approval of target_hash. Only the agent's chat counts."""
        if source != "agent_chat":
            self.log.append(("ignored_not_agent_chat", source))
            return {"counted": False, "reason": "not_agent_chat"}
        if not AFFIRMATIVE.match(text or ""):
            return {"counted": False, "reason": "not_affirmative"}
        self._approved[target_hash] = 1
        return {"counted": True}

    def attempt(self, kind, payload):
        if is_refused(kind):
            return {"allowed": False, "reason": "refused_never_bot_action"}
        if kind not in GATED_ACTIONS:
            return {"allowed": False, "reason": "unknown_action"}
        h = action_hash(kind, payload)
        if self._approved.get(h, 0) < 1:
            return {"allowed": False, "reason": "no_approval_for_this_version"}
        self._approved[h] = 0  # one yes = one attempt
        return {"allowed": True, "reason": "approved_once"}


WIRE_PATTERNS = [
    r"\bwire (?:the |your )?(?:funds|money|deposit|payment)",
    r"\b(?:new|updated|changed|different) (?:bank|banking|account|wiring|wire|routing|payee)",
    r"\b(?:account|routing) number (?:has )?(?:changed|is now|updated)",
    r"\bchange(?:d)? (?:of )?(?:payee|account|wiring|wire) ",
    r"\bsend (?:payment|funds) to (?:a |this )?(?:new|different)",
]


def scan_wire_text(text):
    """Flag possible wire/payee/account-change fraud. Flag only; take no action."""
    hits = [p for p in WIRE_PATTERNS if re.search(p, text or "", re.I)]
    return {"flagged": bool(hits), "action": "none",
            "message": "Possible wire fraud. Do not act. Call the title company "
                       "on a known number." if hits else ""}
