"""FakeTransact: a recorded-page stand-in for the member's Transact browser.

Pages come from JSON fixtures {key, url, title, user, labels, fields, text, navigates}.
Every action is recorded so tests can assert what was and was not clicked.
send / sign / next_to_send do not exist as capabilities: calling them raises.
"""
import copy


class TransactActionError(Exception):
    """Raised when anything tries to send, sign, or go Next toward sending."""


# Buttons on a stray dialog that are never pressed (Share Transaction, Unlock Libraries, any confirm).
DIALOG_NEVER = {"share", "share transaction", "unlock", "unlock libraries", "confirm", "ok",
                "yes", "continue", "send", "invite"}
HARD_NEVER = {"next", "send", "send now", "prepare signing", "submit", "certify",
              "sign", "finish and send", "send for signature"}


class FakeTransact:
    def __init__(self, pages, data):
        self.pages = copy.deepcopy(pages)
        self.data = copy.deepcopy(data)
        self.current = data.get("start", "account_chooser")
        self.account = None
        self.actions = []          # (op, label, value)
        self.values = {}           # (page, label) -> value
        self.parties = {}          # role -> person
        self.added_forms = []
        self.placed = []           # field placements (not signatures)
        self.draft_saved = False
        self.contacts_created = []
        self.focused = None        # label of the confirmed focused text input, else None
        self.checked = set()       # ticked checkbox labels on the form
        self.dialog = None         # {"title", "labels"} while a dialog is open
        self.previewed = set()     # library entry ids previewed this session
        self.keypresses = []
        self.uploads = []          # (row, doc) placed on the Compliance tab
        self.open_file = None      # {"account", "address", "owner"} of the deal file now open
        self.signing_order = []
        self.applied_layouts = []  # (layout name, doc) chosen through Map Signers

    def page(self):
        return self.pages[self.current]

    def goto(self, key):
        self.current = key

    @property
    def labels_clicked(self):
        return [a[1] for a in self.actions if a[0] == "click"]

    def click(self, label):
        self.actions.append(("click", label, None))
        self.focused = None
        if self.dialog and label.strip().lower() in DIALOG_NEVER:
            raise TransactActionError("never confirm a dialog with %r" % label)
        if label in self.page().get("checkboxes", []):
            self.checked ^= {label}
        if label.strip().lower() in HARD_NEVER:
            raise TransactActionError("never click %r" % label)
        if label == "Save" and self.current == "signing_builder":
            self.draft_saved = True
        nav = self.page().get("navigates", {}).get(label)
        if nav:
            self.current = nav
        return {"clicked": label}

    def focus(self, label):
        self.actions.append(("focus", label, None))
        self.focused = label

    def fill(self, label, value):
        self.actions.append(("fill", label, value))
        self.values[(self.current, label)] = value
        # Written-amount fields auto-append "Dollars" on their own (never typed by the bot).
        written = self.page().get("auto_words", {}).get(label)
        if written:
            words = self.data.get("written_amounts", {}).get(str(value))
            if words:
                self.values[(self.current, written)] = words + " Dollars"

    def keypress(self, key):
        """Single-key shortcuts exist in Transact (a stray Escape opened dialogs). Refused unless
        a text input is focused."""
        self.actions.append(("keypress", key, self.focused))
        if not self.focused:
            raise TransactActionError("keypress %r with no focused text input" % key)
        self.keypresses.append(key)

    def open_dialog(self, title, labels):
        """Test hook: Transact opened a dialog by itself."""
        self.dialog = {"title": title, "labels": list(labels)}

    def click_dialog(self, label):
        self.actions.append(("click_dialog", label, None))
        if label.strip().lower() in DIALOG_NEVER:
            raise TransactActionError("never confirm a dialog with %r" % label)
        if self.dialog and label in self.dialog["labels"]:
            self.dialog = None
            return {"clicked": label}
        raise TransactActionError("no dialog button %r" % label)

    def select_account(self, name):
        self.actions.append(("select_account", name, None))
        self.account = name
        self.current = "file_search"

    def search_files(self, query):
        self.actions.append(("search_files", query, self.account))
        q = query.lower()
        return [f for f in self.data.get("files", {}).get(self.account, [])
                if q in f["address"].lower() or q == str(f.get("mls", "")).lower()
                or q in f.get("client", "").lower()]

    def search_contacts(self, query):
        self.actions.append(("search_contacts", query, None))
        q = query.lower()
        return [c for c in self.data.get("contacts", []) + self.contacts_created
                if q in c["email"].lower() or q in c["name"].lower()]

    def create_contact(self, person):
        self.actions.append(("create_contact", person["name"], person["email"]))
        self.contacts_created.append(dict(person))

    def add_party(self, role, person, how):
        self.actions.append(("add_party", role, how))
        self.parties[role] = dict(person)

    def read_email(self, role):
        p = self.parties.get(role)
        if not p:
            return None
        return self.data.get("readback_override", {}).get(p["email"], p["email"])

    def library_entries(self, text):
        """Picker rows: id and name only, no version text (look-alike entries are common)."""
        self.actions.append(("library_entries", text, None))
        return [{"id": e["id"], "name": e["name"]} for e in self.data.get("library_entries", [])
                if text.lower() in e["name"].lower() and e["name"] in self.data.get("library", [])]

    def preview(self, entry_id):
        self.actions.append(("preview", entry_id, None))
        self.previewed.add(entry_id)
        for e in self.data.get("library_entries", []):
            if e["id"] == entry_id:
                return {"id": entry_id, "footer": e.get("footer", "")}
        return {"id": entry_id, "footer": ""}

    def add_form_entry(self, entry_id):
        """Adding a library entry that was never previewed is refused (no picking by position)."""
        if entry_id not in self.previewed:
            raise TransactActionError("library entry %s was not previewed" % entry_id)
        for e in self.data.get("library_entries", []):
            if e["id"] == entry_id:
                self.actions.append(("add_form", e["name"], entry_id))
                self.added_forms.append(e["name"])
                return
        raise TransactActionError("unknown library entry")

    def add_form(self, name):
        self.actions.append(("add_form", name, None))
        self.added_forms.append(name)

    def library_search(self, text):
        self.actions.append(("library_search", text, None))
        return [f for f in self.data.get("library", []) if text.lower() in f.lower()]

    def attach(self, filename):
        self.actions.append(("attach", filename, None))

    def place_field(self, signer, kind, doc, page_no):
        assert kind in ("Initials", "Sign Here", "Date", "Name")
        self.actions.append(("place_field", signer, kind))
        self.placed.append({"signer": signer, "field": kind, "doc": doc, "page": page_no})

    def set_signing_order(self, names):
        self.actions.append(("set_signing_order", list(names), None))
        self.signing_order = list(names)

    def apply_layout(self, name, doc):
        self.actions.append(("apply_layout", name, doc))
        self.applied_layouts.append((name, doc))

    def set_open_file(self, address):
        """Record which Transact file is open (the member's own account, this deal's address)."""
        self.open_file = {"account": self.account, "address": address, "owner": self.page().get("user")}

    def upload_to_row(self, row, doc):
        """Compliance tab upload. Only on the Compliance tab, only into an open file, and a row that
        is not empty is never overwritten."""
        if self.current != "compliance":
            raise TransactActionError("uploads go only into the Compliance tab")
        if not self.open_file:
            raise TransactActionError("no open file to upload into")
        for r in self.pages["compliance"].get("rows", []):
            if r["row"] == row:
                if r["status"] != "empty":
                    raise TransactActionError("row %r is not empty; never overwrite" % row)
                r["status"] = "filled"
                self.actions.append(("upload", row, doc))
                self.uploads.append((row, doc))
                return
        raise TransactActionError("no Compliance row %r" % row)

    def save_draft(self):
        self.actions.append(("click", "Save", None))
        self.draft_saved = True

    # never available
    def send(self, *a, **k):
        raise TransactActionError("send is not available")

    def sign(self, *a, **k):
        raise TransactActionError("sign is not available")

    def next_to_send(self, *a, **k):
        raise TransactActionError("next toward sending is not available")
