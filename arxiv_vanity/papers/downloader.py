from django.core.files.base import ContentFile
import requests


class DownloadError(Exception):
    """Error downloading a paper."""


def guess_extension_from_headers(h):
    """
    Given headers from an ArXiV e-print response, try and guess what the file
    extension should be.

    Based on: https://arxiv.org/help/mimetypes
    """
    if h.get('content-type') == 'application/pdf':
        return '.pdf'
    if h.get('content-encoding') == 'x-gzip' and h.get('content-type') == 'application/postscript':
        return '.ps.gz'
    if h.get('content-encoding') == 'x-gzip' and h.get('content-type') == 'application/x-eprint-tar':
        return '.tar.gz'
    # content-encoding is x-gzip but this appears to normally be a lie - it's
    # just plain text
    if h.get('content-type') == 'application/x-eprint':
        return '.tex'
    if h.get('content-encoding') == 'x-gzip' and h.get('content-type') == 'application/x-dvi':
        return '.dvi.gz'
    return None


def arxiv_id_to_source_url(arxiv_id):
    # This URL is normally a tarball, but sometimes something else.
    # ArXiV provides a /src/ URL which always serves up a tarball,
    # but if we used this, we'd have to untar the file to figure out
    # whether it's renderable or not. By using the /e-print/ endpoint
    # we can figure out straight away whether we should bother rendering
    # it or not.
    # https://arxiv.org/help/mimetypes has more info
    return 'https://arxiv.org/e-print/' + arxiv_id


def arxiv_id_to_source_file(arxiv_id):
    """
    Convert an arXiv ID into the filename the source file should be stored as,
    without extension.

    This is the inverse of `convert_source_file_to_arxiv_id()` in 
    `arxiv_vanity/scraper/bulk_sources.py`.
    """
    return arxiv_id.replace("/", "")


def download_source_file(arxiv_id):
    """
    Download the LaTeX source of this paper and returns as ContentFile.
    """
    source_url = arxiv_id_to_source_url(arxiv_id)
    res = requests.get(source_url)
    res.raise_for_status()
    extension = guess_extension_from_headers(res.headers)
    if not extension:
        raise DownloadError("Could not determine file extension from "
                            "headers: Content-Type: {}; "
                            "Content-Encoding: {}".format(
                                res.headers.get('content-type'),
                                res.headers.get('content-encoding')))
    file = ContentFile(res.content)
    file.name = arxiv_id_to_source_file(arxiv_id) + extension
    return file
