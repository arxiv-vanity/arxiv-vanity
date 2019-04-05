from bs4 import BeautifulSoup
import copy
from django.template.loader import render_to_string
import os
import re

from .crossref import citation_to_url


def add_citation_urls(soup):
    bibliography = soup.find("section", class_="ltx_bibliography")
    for bibitem in bibliography.find_all("li", class_="ltx_bibitem"):
        bibitem_copy = copy.copy(bibitem)
        # remove [0] etc
        bibitem_copy.find("span", class_=re.compile("ltx_tag")).extract()
        # skip if there is already a URL
        if bibitem_copy.find("a"):
            continue
        text = bibitem_copy.get_text().replace("\n", " ").strip()
        if not text:
            continue
        url = citation_to_url(text)
        if not url:
            continue
        link = soup.new_tag('a', href=url)
        link.string = str(link)
        bibitem.append(link)
    return soup


def process_render(fh, path_prefix, context):
    """
    Do some final processing on the rendered paper:
    * extract scripts/styles/body
    * rewrite URLs to add a prefix
    """
    soup = BeautifulSoup(fh, 'lxml')

    # Add prefixes
    for el in soup.find_all('link'):
        el['href'] = os.path.join(path_prefix, el['href'])
    for el in soup.find_all('script'):
        if el.get('src'):
            el['src'] = os.path.join(path_prefix, el['src'])
    for el in soup.find_all('img'):
        if not el['src'].startswith('data:'):
            el['src'] = os.path.join(path_prefix, el['src'])


    links = soup.head.find_all('link')
    styles = soup.head.find_all('style')
    scripts = soup.head.find_all('script')

    soup = add_citation_urls(soup)

    return {
        # FIXME: This should be str but it's bytes for some reason.
        # It's very odd - BeautifulSoup's docs insists everything is unicode,
        # and even trying to force the input to be utf-8 doesn't help.
        "body": soup.body.encode_contents().decode('utf-8'),
        "links": ''.join(e.prettify() for e in links),
        "styles": ''.join(e.prettify() for e in styles),
        "scripts": ''.join(e.prettify() for e in scripts),
    }
