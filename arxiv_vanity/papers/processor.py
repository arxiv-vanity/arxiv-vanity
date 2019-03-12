from bs4 import BeautifulSoup
from django.template.loader import render_to_string
import os


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

    return {
        # FIXME: This should be str but it's bytes for some reason.
        # It's very odd - BeautifulSoup's docs insists everything is unicode,
        # and even trying to force the input to be utf-8 doesn't help.
        "body": soup.body.encode_contents().decode('utf-8'),
        "links": ''.join(e.prettify() for e in links),
        "styles": ''.join(e.prettify() for e in styles),
        "scripts": ''.join(e.prettify() for e in scripts),
    }
