import re

ARXIV_ID_RE = re.compile(r'^(.+?)v(\d+)$')


def remove_version_from_arxiv_id(arxiv_id):
    match = ARXIV_ID_RE.match(arxiv_id)
    if not match:
        return arxiv_id, None
    return match.group(1), int(match.group(2))


ARXIV_URL_RE = re.compile(r'v(\d+)$')


def remove_version_from_arxiv_url(url):
    return ARXIV_URL_RE.sub('', url)
