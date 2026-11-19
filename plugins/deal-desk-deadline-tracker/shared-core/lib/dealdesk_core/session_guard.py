"""session_guard: look at a recorded page/connector state and say whether to stop.

State = {url, title, labels: [visible labels], text: visible text, fields: {...}}.
Returns {"stop": False} or {"stop": True, "reason", "message"}.
Pure inspection: it never types, fills, clicks, or stores anything, and it
never fills a password.
"""
import re

# order matters: the first match wins
CHECKS = [
    ("expired_session", re.compile(
        r"session (?:has )?(?:expired|timed out)|you(?:'ve| have) been signed out|"
        r"signed out due to inactivity|please sign in again", re.I),
     "The session has expired. Ask the member to sign in again in their own "
     "browser, then wait. Do not try to sign in for them."),
    ("mfa", re.compile(
        r"verification code|two-factor|2-step|multi-factor|\bmfa\b|"
        r"authenticator app|enter the code we (?:sent|texted)|one-time (?:code|passcode)",
        re.I),
     "The site is asking for a verification code. Stop and ask the member to "
     "complete it themselves."),
    ("captcha", re.compile(
        r"captcha|i'm not a robot|i am not a robot|verify you are human|"
        r"select all (?:images|squares)", re.I),
     "The site is showing a human check. Stop and ask the member to complete it "
     "themselves."),
    ("card_or_id_prompt", re.compile(
        r"card number|credit card|\bcvv\b|security code|social security|\bssn\b|"
        r"driver'?s licen[sc]e|government id|date of birth", re.I),
     "The page is asking for a card or ID number. Stop. Never enter these; tell "
     "the member."),
    ("password_prompt", re.compile(r"\bpassword\b|\bpasscode\b", re.I),
     "The page is asking for a password. Stop. Never type a password; ask the "
     "member to sign in themselves."),
    ("unexpected_sign_in", re.compile(
        r"\bsign in\b|\blog in\b|\blogin\b|\bsign-in\b", re.I),
     "An unexpected sign-in page appeared. Stop and tell the member."),
]


def inspect(state):
    blob = " ".join([str(state.get("url", "")), str(state.get("title", "")),
                     " ".join(str(x) for x in state.get("labels", [])),
                     str(state.get("text", ""))])
    for reason, rx, message in CHECKS:
        if rx.search(blob):
            return {"stop": True, "reason": reason, "message": message}
    return {"stop": False}


def read_fields(fields, wanted):
    """Return each wanted field as seen, or "missing". Never guess or borrow."""
    out = {}
    for name in wanted:
        v = (fields or {}).get(name)
        out[name] = "missing" if v is None or v == "" else v
    return out
