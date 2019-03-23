import re

ARXIV_ID_PATTERN = r'(\d+\.\d+)(v\d+)?'
ARXIV_ID_RE = re.compile(ARXIV_ID_PATTERN)


def remove_version_from_arxiv_id(arxiv_id):
    match = ARXIV_ID_RE.match(arxiv_id)
    return match.group(1), int(match.group(2)[1:]) if match.group(2) else None


ARXIV_URL_RE = re.compile(r'v(\d+)$')


def remove_version_from_arxiv_url(url):
    return ARXIV_URL_RE.sub('', url)
