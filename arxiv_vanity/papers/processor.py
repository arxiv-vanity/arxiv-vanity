from bs4 import BeautifulSoup
from django.urls import reverse
import os
from ..scraper.arxiv_ids import ARXIV_URL_RE


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
    
    # Turn arxiv.org links into vanity links
    for el in soup.find_all('a'):
        if el.get('href'):
            match = ARXIV_URL_RE.search(el['href'])
            if match:
                arxiv_id = match.group(1)
                el['href'] = reverse('paper_detail', args=(arxiv_id,))

            # Open all links in new windows
            el['target'] = '_blank'

    # Stuff for opengraph tags
    abstract = None
    abstract_tag = soup.find("div", class_="ltx_abstract")
    if abstract_tag:
        first_paragraph = abstract_tag.find("p")
        if first_paragraph:
            abstract = first_paragraph.get_text()

    first_image = None
    for figure in soup.find_all("figure", class_="ltx_figure"):
        img = figure.find('img')
        if img:
            first_image = img['src']
            break

    return {
        # FIXME: This should be str but it's bytes for some reason.
        # It's very odd - BeautifulSoup's docs insists everything is unicode,
        # and even trying to force the input to be utf-8 doesn't help.
        "body": soup.body.encode_contents().decode('utf-8'),
        # just links, styles, and scripts in <head> so we can re-insert in arxiv vanity <head>
        # stuff that's in the <body> gets included above
        "links": ''.join(e.prettify() for e in soup.head.find_all('link')),
        "styles": ''.join(e.prettify() for e in soup.head.find_all('style')),
        "scripts": ''.join(e.prettify() for e in soup.head.find_all('scripts')),
        "abstract": abstract,
        "first_image": first_image,
    }
