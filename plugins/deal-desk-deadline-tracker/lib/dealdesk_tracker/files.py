"""tracker-files: folder plan and filenames. There is deliberately no remove
function in this module. A name clash gets a numbered copy, never an overwrite."""
import re

DEAL_FOLDERS = ("Contract", "Addenda-Amendments", "Inspection", "Appraisal-Lending",
                "Title", "Other")
FOLDER_FOR = {"purchase_agreement": "Contract", "counter": "Contract",
              "addendum": "Addenda-Amendments", "amendment": "Addenda-Amendments",
              "extension": "Addenda-Amendments", "inspection_response": "Inspection",
              "appraisal": "Appraisal-Lending", "loan": "Appraisal-Lending",
              "title": "Title", "other": "Other"}
SUFFIXES = {"lane", "ln", "street", "st", "road", "rd", "drive", "dr", "avenue", "ave",
            "court", "ct", "circle", "cir", "place", "pl", "boulevard", "blvd"}


def address_short(address):
    """'4321 Pretend Pelican Lane, Zachary LA 70791' -> '4321 Pelican'."""
    first = (address or "").split(",")[0].split()
    if not first:
        return "unknown"
    num = first[0] if first[0].isdigit() else ""
    words = [w for w in first[1:] if w.lower() not in SUFFIXES] or first[1:]
    name = words[-1] if words else first[0]
    return ("%s %s" % (num, name)).strip()


def _slug(text):
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-")


def filename(date_iso, doc_class, address):
    return "%s_%s_%s.pdf" % (date_iso, _slug(doc_class.replace("_", " ")),
                             _slug(address_short(address)))


def plan(date_iso, doc_class, address, practice=False):
    folder = FOLDER_FOR.get(doc_class, "Other")
    deal = _slug(address_short(address))
    root = ("Practice/" if practice else "") + deal
    return {"folder": "%s/%s" % (root, folder), "filename": filename(date_iso, doc_class, address),
            "path": "%s/%s/%s" % (root, folder, filename(date_iso, doc_class, address)),
            "practice": practice}


class FileStore:
    """In-memory stand-in for member storage. Add only."""

    def __init__(self):
        self.paths = []

    def file(self, plan_):
        path = plan_["path"]
        n = 2
        while path in self.paths:
            path = plan_["path"][:-4] + "-%d.pdf" % n
            n += 1
        self.paths.append(path)
        return {"stored": path, "renamed": path != plan_["path"]}
