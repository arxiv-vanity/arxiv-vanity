from bs4 import BeautifulSoup
import os


def process_render(fh, path_prefix):
    """
    Do some final processing on the rendered paper:
    * extract scripts/styles/body
    * rewrite URLs to add a prefix
    """
    soup = BeautifulSoup(fh, 'lxml')
    styles = soup.head.find_all('style')
    scripts = soup.head.find_all('script')

    for img in soup.body.find_all('img'):
        img['src'] = os.path.join(path_prefix, img['src'])

    return {
        "body": soup.body.encode_contents(),
        "styles": ''.join(e.prettify() for e in styles),
        "scripts": ''.join(e.prettify() for e in scripts),
    }
