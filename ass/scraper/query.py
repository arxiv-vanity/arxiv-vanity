import dateutil.parser
import re
import requests
from urllib.parse import urlencode
from xml.etree import ElementTree
from ..papers.models import Paper

ROOT_URL = 'http://export.arxiv.org/api/'
NS = {
    'atom': 'http://www.w3.org/2005/Atom',
    'arxiv': 'http://arxiv.org/schemas/atom',
}


def scrape_papers():
    """
    Download papers from Arxiv's API and insert new ones into the database.
    """
    papers = query()
    for paper in create_papers(papers):
        print("Downloading and rendering {}...".format(paper.get_short_arxiv_id()))
        paper.render()


def query():
    """
    Download and parse papers from Arxiv's API.
    """
    search_query = "cat:cs.CV OR cat:cs.AI OR cat:cs.LG OR cat:cs.CL OR cat:cs.NE OR cat:stat.ML"
    start = 0
    max_results = 100
    url_args = urlencode({"search_query": search_query,
                          "start": start,
                          "max_results": max_results,
                          "sortBy": "lastUpdatedDate"})
    response = requests.get(ROOT_URL + 'query?' + url_args)
    response.raise_for_status()
    return parse(response.text)


def parse(s):
    """
    Parse an API response from Arxiv.
    """
    # We're not using Feedparser here because it eats a lot of the extra
    # data that Arxiv adds. By manually reading the XML, we can be sure we've
    # got everything.
    root = ElementTree.fromstring(s)
    for entry in root.findall("atom:entry", NS):
        yield convert_entry_to_paper(entry)


def convert_entry_to_paper(entry):
    """
    Convert an ElementTree <entry> into a dictionary to initialize a paper
    with.
    """
    d = {}
    d['arxiv_id'] = entry.find("atom:id", NS).text
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

    return d


def create_papers(papers):
    """
    Create papers that don't already exist. Returns an iterator of papers
    that have been created.
    """
    for paper in papers:
        obj, created = Paper.objects.get_or_create(arxiv_id=paper['arxiv_id'],
                                                    defaults=paper)
        if created:
            yield obj
