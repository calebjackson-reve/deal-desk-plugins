"""Gate for TC: the shared ReviewGate plus the TC in-system kinds.

Send / sign / invite / certify stay refused with or without a yes.

Decision (Caleb, Nov 16 2026): the compliance upload into the member's OWN Transact file's Compliance
tab is automatic and is NOT a gate step (no yes). Its guards live in compliance.upload_guard and
templates.upload_batch. Compliance submit is gated: one explicit yes, one attempt. The optional
Brokerage system fallback upload stays gated ("compliance_upload_brokerage_system").
"""
from dealdesk_core import gate as core_gate

TC_GATED = {"form_review", "save_signing_layout", "compliance_upload_brokerage_system", "compliance_submit",
            "compliance_update_row", "compliance_sync",
            "compliance_file_place"}

# Messages to people are never bot actions, even inside the compliance flow.
TC_REFUSED = {"compliance_reply"}


def refused(kind):
    return kind in TC_REFUSED or (kind not in TC_GATED and core_gate.is_refused(kind))


class TcGate(core_gate.ReviewGate):
    def propose(self, kind, payload):
        return {"kind": kind, "hash": core_gate.action_hash(kind, payload),
                "refused": refused(kind)}

    def attempt(self, kind, payload):
        if refused(kind):
            return {"allowed": False, "reason": "refused_never_bot_action"}
        if kind not in TC_GATED:
            return {"allowed": False, "reason": "unknown_action"}
        h = core_gate.action_hash(kind, payload)
        if self._approved.get(h, 0) < 1:
            return {"allowed": False, "reason": "no_approval_for_this_version"}
        self._approved[h] = 0  # one yes = one attempt
        return {"allowed": True, "reason": "approved_once"}
