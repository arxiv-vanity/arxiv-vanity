import re

# These patterns need to be implemented case insensitive (e.g. [vV])
# because Django doesn't let us add re.I to re_path() in URLs
ARXIV_ID_PATTERN = r"([a-zA-Z\-]+(?:\.[a-zA-Z]{2})?/\d{7}|\d+\.\d+)([vV]\d+)?"
ARXIV_ID_RE = re.compile(ARXIV_ID_PATTERN)
ARXIV_URL_RE = re.compile(fr"arxiv.org/[^\/]+/({ARXIV_ID_PATTERN})(\.pdf)?", re.I)
ARXIV_DOI_RE = re.compile(fr"^(?:arxiv:)?({ARXIV_ID_PATTERN})$", re.I)
ARXIV_VANITY_RE = re.compile(
    fr"(?:localhost\:\d+|arxiv-vanity\.com)/[^\/]+/({ARXIV_ID_PATTERN})\/?", re.I
)


def remove_version_from_arxiv_id(arxiv_id):
    match = ARXIV_ID_RE.match(arxiv_id)
    return match.group(1), int(match.group(2)[1:]) if match.group(2) else None


ARXIV_VERSION_RE = re.compile(r"v(\d+)$")


def remove_version_from_arxiv_url(url):
    return ARXIV_VERSION_RE.sub("", url)
