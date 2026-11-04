"""Request authentication and input checks for the worker."""

import hmac
import os
import re
import zipfile
from xml.etree import ElementTree

STORAGE_ROOT = os.path.realpath("/storage")

# The API sends this token in "Authorization: Bearer <token>". The worker does not start without it.
WORKER_TOKEN = os.getenv("WORKER_TOKEN", "").strip()
if not WORKER_TOKEN:
    raise RuntimeError("Set WORKER_TOKEN. The worker refuses requests without a shared token.")


class InvalidRequest(Exception):
    """The request payload is not acceptable."""


def is_authorized(scope) -> bool:
    for name, value in scope.get("headers", []):
        if name.lower() == b"authorization":
            expected = f"Bearer {WORKER_TOKEN}".encode()
            return hmac.compare_digest(value, expected)
    return False


def storage_path(relative_path: str) -> str:
    """Return the absolute path of a file in /storage. Refuse a path that goes out of /storage."""
    if not isinstance(relative_path, str) or not relative_path:
        raise InvalidRequest("A storage path is required.")
    path = os.path.realpath(os.path.join(STORAGE_ROOT, relative_path.lstrip("/")))
    if os.path.commonpath([path, STORAGE_ROOT]) != STORAGE_ROOT or path == STORAGE_ROOT:
        raise InvalidRequest("The path is outside the storage folder.")
    return path



# Checks on ODF templates.

ODF_NS = {
    "draw": "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0",
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "script": "urn:oasis:names:tc:opendocument:xmlns:script:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "xlink": "http://www.w3.org/1999/xlink",
}


def _tag(prefix, name):
    return "{%s}%s" % (ODF_NS[prefix], name)


# Elements that make LibreOffice load content from outside the template, or run scripts.
FORBIDDEN_ELEMENTS = {
    _tag("text", "section-source"),
    _tag("table", "table-source"),
    _tag("table", "cell-range-source"),
    _tag("table", "dde-link"),
    _tag("office", "dde-source"),
    _tag("text", "dde-connection-decl"),
    _tag("script", "event-listener"),
    _tag("text", "script"),
}
# LibreOffice does not open hyperlinks when it converts a document.
HYPERLINK_ELEMENTS = {_tag("text", "a"), _tag("draw", "a")}
XLINK_HREF = _tag("xlink", "href")
TABLE_FORMULA = _tag("table", "formula")
# A URI scheme ("file:", "http:"), an absolute path, or a Windows path.
EXTERNAL_HREF = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|/|\\)")
# Formulas that fetch URLs, use DDE, or refer to another file ('file:///x.ods'#Sheet1.A1).
FORBIDDEN_FORMULA = re.compile(r"WEBSERVICE\s*\(|DDE\s*\(|'[a-zA-Z][a-zA-Z0-9+.-]*:", re.IGNORECASE)
MACRO_FOLDERS = ("Basic/", "Scripts/")


def check_template(path: str) -> None:
    """Refuse an ODF template that can read files or URLs, or that contains macros."""
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        raise InvalidRequest("The template is not an ODF file.")
    with archive:
        names = archive.namelist()
        if any(name.startswith(MACRO_FOLDERS) for name in names):
            raise InvalidRequest("The template contains macros.")
        for name in ("content.xml", "styles.xml"):
            if name not in names:
                continue
            with archive.open(name) as xml_file:
                for _, element in ElementTree.iterparse(xml_file):
                    _check_element(element)
                    element.clear()


def _check_element(element) -> None:
    if element.tag in FORBIDDEN_ELEMENTS:
        raise InvalidRequest("The template links to external content or contains scripts.")
    href = element.get(XLINK_HREF)
    if href and element.tag not in HYPERLINK_ELEMENTS:
        if EXTERNAL_HREF.match(href) or ".." in href.replace("\\", "/").split("/"):
            raise InvalidRequest("The template links to a file or URL outside the template.")
    formula = element.get(TABLE_FORMULA)
    if formula and FORBIDDEN_FORMULA.search(formula):
        raise InvalidRequest("The template contains a formula that reads external data.")
