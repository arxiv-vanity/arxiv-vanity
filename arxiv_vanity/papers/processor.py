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
    styles = soup.head.find_all('style')
    scripts = soup.head.find_all('script')

    # Add prefixes to images
    for img in soup.body.find_all('img'):
        img['src'] = os.path.join(path_prefix, img['src'])

    # Insert metadata into header of article
    rendered_contents = render_to_string('papers/processor/metadata.html', context)
    metadata = soup.select('.engrafo-metadata-custom')
    if metadata:
        metadata[0].append(BeautifulSoup(rendered_contents, 'lxml'))

    return {
        "body": soup.body.encode_contents(),
        "styles": ''.join(e.prettify() for e in styles),
        "scripts": ''.join(e.prettify() for e in scripts),
    }
