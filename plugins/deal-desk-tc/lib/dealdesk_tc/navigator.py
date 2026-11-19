"""tc-transact-navigator: label-first control finding, account chooser, stops."""
import re

from dealdesk_core import session_guard

FORBIDDEN_UNLESS_ASKED = ("offer accepted", "offer rejected", "delete")

# Live transaction tabs (demo file, Nov 16 2026). Alternates kept for older wording.
TABS = ["Paperwork", "Details", "Parties", "Signings", "Compliance", "To-Do", "Timeline", "History"]
TAB_ALTERNATES = {"Paperwork": ("Documents",), "To-Do": ("To Do", "Todo", "Tasks")}


def _norm(s):
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def find_control(client, label, alternates=()):
    """Exact label, then alternates, then a page search. Never coordinates."""
    tried = [label] + list(alternates)
    labels = client.page().get("labels", [])
    by_norm = {_norm(x): x for x in labels}
    for i, t in enumerate(tried):
        if _norm(t) in by_norm:
            return {"found": True, "label": by_norm[_norm(t)],
                    "via": "label" if i == 0 else "alternate"}
    for t in tried:
        hit = [x for x in labels if _norm(t) in _norm(x)]
        if hit:
            return {"found": True, "label": hit[0], "via": "page_search"}
    return {"found": False, "stop": True, "reason": "missing_label", "looked_for": tried,
            "message": "Could not find %s (looked for: %s) after alternates and page search."
                       % (label, ", ".join(tried))}


def forbidden(label, allow=()):
    n = _norm(label)
    if n in [_norm(a) for a in allow]:
        return False
    return n in FORBIDDEN_UNLESS_ASKED or "sync" in n


def click(client, label, alternates=(), allow=()):
    for t in [label] + list(alternates):
        if forbidden(t, allow):
            return {"clicked": False, "refused": True, "reason": "forbidden_button", "label": t}
    f = find_control(client, label, alternates)
    if not f["found"]:
        return dict(f, clicked=False)
    if forbidden(f["label"], allow):
        return {"clicked": False, "refused": True, "reason": "forbidden_button", "label": f["label"]}
    client.click(f["label"])
    return {"clicked": True, "label": f["label"], "via": f["via"]}


# First-page fields that never print names: buyer and seller names come from the Parties role slots.
NAME_FIELDS = {"buyer", "buyer name", "buyers", "buyer names", "seller", "seller name",
               "sellers", "seller names", "buyer 1", "buyer 2", "seller 1", "seller 2"}


def fill(client, label, value, alternates=()):
    if _norm(label) in NAME_FIELDS:
        return {"filled": False, "refused": True, "reason": "names_come_from_role_slots",
                "label": label, "message": "Buyer and seller names come from the Parties role "
                "slots (Transaction Parties), never typed into a form field."}
    f = find_control(client, label, alternates)
    if not f["found"]:
        return dict(f, filled=False)
    client.focus(f["label"])          # focus confirmed before typing
    client.fill(f["label"], value)
    return {"filled": True, "label": f["label"]}


def open_transact(client, settings):
    """Guard the page, confirm the signed-in user, pick the account."""
    g = session_guard.inspect(client.page())
    if g["stop"]:
        return {"stop": True, "reason": g["reason"], "message": g["message"]}
    user = client.page().get("user")
    if user and user != settings.get("expected_user"):
        return {"stop": True, "reason": "wrong_user",
                "message": "Signed in as %s, not the member. Stop." % user}
    if "choose an account" in _norm(client.page().get("title", "")):
        acct = settings.get("transact_account")
        options = client.data.get("accounts", [])
        if not acct or acct not in options:
            return {"stop": True, "ask": "transact_account", "options": options,
                    "message": "Which account should I use? It is not set (or not on the chooser)."}
        client.select_account(acct)
    return {"stop": False, "account": client.account}


def search_file(client, query):
    """Chosen account first, then every other account context.

    "missing" is only concluded after every account has been checked.
    """
    accounts = client.data.get("accounts", [])
    order = ([client.account] if client.account else []) + \
        [a for a in accounts if a != client.account]
    checked, home = [], client.account
    for a in order:
        if a != client.account:
            client.select_account(a)
        checked.append(a)
        hits = client.search_files(query)
        if not hits and query[:1].isdigit():
            for alt in address_queries(query)[1:]:
                hits = client.search_files(alt)
                if hits:
                    break
        if hits:
            return {"status": "found", "contexts_checked": checked,
                    "matches": [dict(h, account=a) for h in hits]}
    if home and client.account != home:
        client.select_account(home)        # go back to the member's own account
    if len(checked) < max(len(accounts), 1):
        return {"status": "unknown", "contexts_checked": checked}
    return {"status": "missing", "contexts_checked": checked}


def open_tab(client, tab, allow=()):
    """Click a transaction tab by label (alternates kept)."""
    return click(client, tab, TAB_ALTERNATES.get(tab, ()), allow)


def find_icon_control(client, name):
    """Icon-only controls (print, download, help): aria-label or tooltip, never position."""
    n = _norm(name)
    for c in client.page().get("icon_controls", []):
        if _norm(c.get("aria_label", "")) == n:
            return {"found": True, "via": "aria_label", "name": c["aria_label"]}
        if _norm(c.get("tooltip", "")) == n:
            return {"found": True, "via": "tooltip", "name": c["tooltip"]}
    return {"found": False, "stop": True, "reason": "missing_icon_control", "looked_for": name,
            "message": "No control with aria-label or tooltip %r. Not guessing by position." % name}


def find_search_box(client):
    """The Paperwork / file search is a box with the placeholder 'Search', not a button."""
    box = client.page().get("search_box")
    if box and _norm(box.get("placeholder", "")) == "search":
        return {"found": True, "via": "placeholder", "placeholder": box["placeholder"]}
    return {"found": False, "stop": True, "reason": "missing_search_box",
            "message": "No search box with the placeholder 'Search' on this page."}


def read_folders(client):
    """Folder names are read from the page and reported; none are assumed."""
    folders = list(client.page().get("folders", []))
    return {"folders": folders, "assumed": [], "count": len(folders)}


def saved_status(client):
    """True when the Forms Editor top bar says Saved (e.g. 'Saved – All changes saved')."""
    pg = client.page()
    status = _norm((pg.get("top_bar") or {}).get("status") or pg.get("status") or "")
    return status.startswith("saved") or "Saved" in pg.get("labels", [])


def form_ready(client):
    """Readiness signal only. A missing Prepare Signing control or an empty upload dropzone
    means the form is not filled. The bot never clicks Prepare Signing."""
    pg = client.page()
    if pg.get("canvas") == "empty_dropzone":
        return {"ready": False, "stop": True, "reason": "form_not_filled",
                "message": "The form canvas is an empty upload dropzone, so the form is not filled yet."}
    if "prepare signing" not in {_norm(x) for x in pg.get("labels", [])}:
        return {"ready": False, "stop": True, "reason": "form_not_filled",
                "message": "Prepare Signing is not on the page, so the form is not filled yet."}
    return {"ready": True, "stop": False}


FALLBACK_SETTING = "compliance_fallback_brokerage_system"   # member setting, off by default


def compliance_source(client, settings=None):
    """Transact's Compliance tab is the PRIMARY path. The generic Brokerage system path is an
    optional fallback used only when the member setting is on (office does not use Transact
    compliance). An absent or empty tab never switches path by itself: report it and ask."""
    if (settings or {}).get(FALLBACK_SETTING):
        return {"source": "brokerage_system", "fallback": True, "reason": "member_setting"}
    labels = {_norm(x) for x in client.page().get("labels", [])}
    if "compliance" not in labels:
        return {"source": "compliance_tab", "fallback": False, "stop": True, "ask": True,
                "reason": "tab_absent", "rows": [],
                "message": "I do not see a Compliance tab on this file. Does your office use it? "
                           "I will not switch to another path unless your setting says so."}
    saved = client.current
    client.goto("compliance")
    rows = client.page().get("rows", [])
    client.goto(saved)
    if not rows:
        return {"source": "compliance_tab", "fallback": False, "stop": True, "ask": True,
                "reason": "tab_empty", "rows": [],
                "message": "The Compliance tab has no checklist rows. Tell me what to do; "
                           "I will not switch to another path on my own."}
    return {"source": "compliance_tab", "fallback": False, "rows": rows}


def _day_diff(a, b):
    from datetime import date
    try:
        return (date.fromisoformat(a) - date.fromisoformat(b)).days
    except ValueError:
        return None


def dates_check(client, labels=None):
    """Details is the source of truth. Timeline can show a date one day earlier (time-zone shift).
    Reads only; flags with both values; never writes."""
    det = client.pages["details"].get("fields", {})
    tl = client.pages["timeline"].get("fields", {})
    flags = []
    for label in (labels or [k for k in det if k in tl]):
        if det.get(label) and tl.get(label) and det[label] != tl[label]:
            one = _day_diff(det[label], tl[label]) == 1
            flags.append({"label": label, "details": det[label], "timeline": tl[label],
                          "kind": "timeline_one_day_earlier" if one else "timeline_differs",
                          "likely": "time-zone shift" if one else None})
    return {"source_of_truth": "Details", "flags": flags, "writes": 0, "details_unchanged": True}


def address_queries(address):
    """Full street line, then number + street name without the suffix. Suffix-insensitive search."""
    from dealdesk_core import deal_match
    line = address.split(",")[0].strip()
    n = deal_match.normalize_address(line)
    out = [line]
    toks = n["street"].split()
    if n["number"] and toks:
        bare = toks[:-1] if toks[-1] in deal_match.SUFFIXES and len(toks) > 1 else toks
        q = (n["number"] + " " + " ".join(bare)).strip()
        if q.lower() != line.lower():
            out.append(q)
    return out


def press_key(client, key):
    """Transact has single-key shortcuts (a stray Escape opened Share Transaction and Unlock
    Libraries). Never send Escape or any keypress unless a text input is focused (confirmed)."""
    if not getattr(client, "focused", None):
        return {"pressed": False, "refused": True, "reason": "no_focused_input", "key": key,
                "message": "No text input is focused, so %r is not sent." % key}
    client.keypress(key)
    return {"pressed": True, "key": key}


UNEXPECTED_DIALOGS = ("share transaction", "unlock libraries")


def handle_dialog(client):
    """Any unexpected dialog (Share Transaction, Unlock Libraries, anything else): click Cancel by
    label, never Share / Unlock / confirm, then open History and report what it shows."""
    d = getattr(client, "dialog", None)
    if not d:
        return {"dialog": None, "handled": False}
    if "Cancel" not in d["labels"]:
        return {"dialog": d["title"], "handled": False, "stop": True, "reason": "no_cancel_button",
                "message": "Dialog %r has no Cancel button. Stopping; nothing was pressed." % d["title"]}
    client.click_dialog("Cancel")
    t = open_tab(client, "History")
    hist = read_history(client) if t.get("clicked") else {"entries": [], "stop": True}
    return {"dialog": d["title"], "handled": True, "cancelled": True, "confirmed": False,
            "history_checked": bool(t.get("clicked")), "history": hist.get("entries", []),
            "message": "A %r dialog opened by itself. I cancelled it (nothing shared or unlocked) "
                       "and checked History. Entries are listed; times may be offset." % d["title"]}


TIME_NOTE = ("History and Timeline times can read about 1 hour ahead of the member's Central time "
             "(seen: 4:06 PM vs about 3:08 PM). Never compute a deadline from them.")


def read_history(client):
    """Read-only. Times are flagged as possibly offset and are never used for deadlines."""
    entries = list(client.page().get("entries", []))
    return {"entries": entries, "time_offset_possible": True, "note": TIME_NOTE,
            "usable_for_deadlines": False, "writes": 0}

