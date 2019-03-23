from urllib.parse import urlencode
from xml.etree import ElementTree
import dateutil.parser
import requests

from .arxiv_ids import remove_version_from_arxiv_id, remove_version_from_arxiv_url, ARXIV_ID_RE

ROOT_URL = 'http://export.arxiv.org/api/'
NS = {
    'atom': 'http://www.w3.org/2005/Atom',
    'arxiv': 'http://arxiv.org/schemas/atom',
}


class PaperNotFoundError(Exception):
    """A query was made for a particular paper and it was not found."""


def category_search_query(categories):
    """
    Download papers from ArXiV from a given list of categories.
    """
    search_query = ' OR '.join('cat:' + cat for cat in categories)
    return query(search_query=search_query)


def query_single_paper(paper_id):
    """
    Download and parse a single paper from arxiv.
    """
    try:
        result = list(query_page(id_list=[paper_id], max_results=1))
    except requests.HTTPError as e:
        # This seems to mean the ID was badly formatted
        if e.response.status_code == 400:
            raise PaperNotFoundError()
        raise
    if not result:
        raise PaperNotFoundError()
    return result[0]


def query(search_query=None, id_list=None, results_per_iteration=100,
          wait_time=5.0, max_index=10000):
    """
    Returns an iterator of parsed results from arXiv's API.
    """
    for i in range(0, max_index, results_per_iteration):
        print(f"Downloading page starting from {i}...", flush=True)
        for result in query_page(search_query=search_query, id_list=id_list,
                                 start=i, max_results=results_per_iteration):
            yield result


def query_page(search_query=None, id_list=None, start=0, max_results=100):
    """
    Download a single page of results from arXiv's API and returns an iterator
    of parsed results.
    """
    url_args = {"start": start,
                "max_results": max_results,
                "sortBy": "lastUpdatedDate"}
    if search_query is not None:
        url_args["search_query"] = search_query
    if id_list is not None:
        url_args["id_list"] = ','.join(id_list)
    response = requests.get(ROOT_URL + 'query?' + urlencode(url_args))
    response.raise_for_status()
    return parse(response.text)


def parse(s):
    """
    Returns an iterator of parsed results given an API response from arXiv.
    """
    # We're not using Feedparser here because it eats a lot of the extra
    # data that arXiv adds. By manually reading the XML, we can be sure we've
    # got everything.
    root = ElementTree.fromstring(s)
    for entry in root.findall("atom:entry", NS):
        # If there are no results, arxiv sometimes just a blank entry
        if entry.find("atom:id", NS) is None:
            continue
        yield convert_entry_to_paper(entry)


def convert_entry_to_paper(entry):
    """
    Convert an ElementTree <entry> into a dictionary to initialize a paper
    with.
    """
    d = {}
    d['arxiv_id'] = ARXIV_ID_RE.search(entry.find("atom:id", NS).text).group()
    d['title'] = entry.find("atom:title", NS).text
    d['title'] = d['title'].replace('\n', '').replace('  ', ' ')
    d['published'] = dateutil.parser.parse(
        entry.find('atom:published', NS).text)
    d['updated'] = dateutil.parser.parse(entry.find('atom:updated', NS).text)
    d['summary'] = entry.find('atom:summary', NS).text
    d['authors'] = []
    for author in entry.findall('atom:author', NS):
        d['authors'].append({
            'name': author.find('atom:name', NS).text,
            'affiliation': [e.text for e in author.findall('arxiv:affiliation', NS)],
        })
    d['arxiv_url'] = entry.find(
        "./atom:link[@type='text/html']", NS).attrib['href']
    d['pdf_url'] = entry.find(
        "./atom:link[@type='application/pdf']", NS).attrib['href']
    d['primary_category'] = entry.find(
        'arxiv:primary_category', NS).attrib['term']
    d['categories'] = [e.attrib['term']
                       for e in entry.findall('atom:category', NS)]
    # Optional
    d['comment'] = getattr(entry.find('arxiv:comment', NS), 'text', None)
    d['doi'] = getattr(entry.find('arxiv:doi', NS), 'text', None)
    d['journal_ref'] = getattr(entry.find(
        'arxiv:journal_ref', NS), 'text', None)

    # Remove version from everything
    d['arxiv_id'], d['arxiv_version'] = remove_version_from_arxiv_id(d['arxiv_id'])
    d['arxiv_url'] = remove_version_from_arxiv_url(d['arxiv_url'])
    d['pdf_url'] = remove_version_from_arxiv_url(d['pdf_url'])

    return d
