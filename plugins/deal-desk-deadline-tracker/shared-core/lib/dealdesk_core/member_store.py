"""Per-member stores. One bot per member; nothing is shared between bots.

Model of hard rule 3: vault entry NAMES only (never contents), files, clients,
deals, config, and an error log that records the error class only. A Platform
only simulates many members installing at once; it holds no member data itself.
"""
import copy
import threading

from . import gate as _gate
from . import ledger as _ledger

DEFAULT_CONFIG = {"lead_days": [2, 1], "commission_format": "percent",
                  "left_blank": ["New Date", "Offer Expires", "Commission"]}
PERSONAL_KEYS = {"member_name", "member_email", "name", "email", "voice", "brokerage",
                 "signature", "signature_block", "cc_only", "vault", "files", "clients",
                 "deals", "practice_deals", "expected_user", "review_email",
                 "custom_templates"}


class CrossMemberAccess(Exception):
    pass


class TemplateHasMemberData(Exception):
    pass


class SecretValueRefused(Exception):
    pass


class MemberBot:
    def __init__(self, member_id, profile, template=None):
        self.member_id = member_id
        self._lock = threading.Lock()
        self.config = copy.deepcopy(DEFAULT_CONFIG)
        if template is not None:
            if template.get("kind") != "blank_defaults" or PERSONAL_KEYS & set(template):
                raise TemplateHasMemberData("template carries member data")
            self.config.update({k: v for k, v in template.items() if k != "kind"})
        # Setup takes the member's own answers only.
        self.config.update(copy.deepcopy(profile))
        self.vault_names = set()
        self.files = {}
        self.clients = []
        self.deals = []
        self.practice_deals = []
        self.error_log = []
        self.ledger = _ledger.Ledger()
        self.gate = _gate.ReviewGate()
        self.plugins = set()
        self._file_owner = {}

    # ---- writes (this bot only) ----
    def add_vault_name(self, name, value=None):
        if value is not None:
            raise SecretValueRefused("vault contents are never stored; names only")
        with self._lock:
            self.vault_names.add(name)

    def add_file(self, path, text):
        with self._lock:
            self.files[path] = text
            self._file_owner[path] = self.member_id

    def read_file(self, path):
        """Own files only, even if another member's file object was handed in."""
        if path not in self.files:
            return None
        if self._file_owner.get(path) != self.member_id:
            raise CrossMemberAccess("file belongs to another member")
        return self.files[path]

    def add_client(self, client):
        with self._lock:
            self.clients.append(copy.deepcopy(client))

    def add_deal(self, deal, practice=False):
        with self._lock:
            (self.practice_deals if practice else self.deals).append(copy.deepcopy(deal))

    def save_review_copy(self, draft):
        """Review-copy draft to this member's own review email only (see ledger)."""
        return _ledger.save_review_copy(self.ledger, self.config, draft)

    def log_error(self, exc):
        """Error class only. Never the message, never client data."""
        with self._lock:
            self.error_log.append(type(exc).__name__)

    # ---- reads ----
    def live_deals(self):
        return copy.deepcopy(self.deals)

    def everything(self):
        """All stored content as one text blob (used by the isolation checks)."""
        return repr((self.config, sorted(self.vault_names), self.files, self.clients,
                     self.deals, self.practice_deals, self.error_log, self.ledger.events))


class Platform:
    """Holds one bot per member and refuses any caller that is not the owner."""

    def __init__(self):
        self._bots = {}
        self._lock = threading.Lock()

    def install(self, member_id, profile, template=None):
        bot = MemberBot(member_id, profile, template)
        with self._lock:
            if member_id in self._bots:
                raise ValueError("already installed")
            self._bots[member_id] = bot
        return bot

    def bot(self, member_id, caller):
        if caller != member_id:
            raise CrossMemberAccess("caller may only open its own bot")
        return self._bots[member_id]

    def add_plugin(self, member_id, plugin):
        """A second plugin joins the same bot; settings and data are kept."""
        bot = self._bots[member_id]
        with bot._lock:
            bot.plugins.add(plugin)
        return bot

    def member_ids(self):
        return sorted(self._bots)
