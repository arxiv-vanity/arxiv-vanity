from django.urls import reverse
import lxml.html
from itertools import chain
import os
import re
from ..scraper.arxiv_ids import ARXIV_URL_RE

EMAIL_RE = re.compile(
    r"[a-z0-9!#$%&'*+/=?^_`{|}~,-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|},~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
)


def process_render(fh, path_prefix, context):
    """
    Do some final processing on the rendered paper:
    * extract scripts/styles/body
    * rewrite URLs to add a prefix
    """
    html = lxml.html.parse(fh)
    head = html.find("head")

    abstract = None
    first_image = None

    # Add prefixes
    for el in html.xpath("//link[@href]"):
        el.attrib["href"] = os.path.join(path_prefix, el.attrib["href"])

    for el in html.xpath("//script[@src]"):
        el.attrib["src"] = os.path.join(path_prefix, el.attrib["src"])
        # lxml will turn it into <script /> without this, which seems to be invalid html
        el.text = ""

    for el in html.xpath("//img[@src]"):
        if not el.attrib["src"].startswith("data:"):
            el.attrib["src"] = os.path.join(path_prefix, el.attrib["src"])

    for el in html.xpath("//a[@href]"):
        # remove mailto: links
        if el.attrib["href"].startswith("mailto:"):
            el.drop_tag()
            continue

        # Turn arxiv.org links into vanity links
        match = ARXIV_URL_RE.search(el.attrib["href"])
        if match:
            arxiv_id = match.group(1)
            el.attrib["href"] = reverse("paper_detail", args=(arxiv_id,))

        # Open all links in new windows
        el.attrib["target"] = "_blank"

    # Stuff for opengraph tags
    abstract = None
    abstract_tag = html.find(".//div[@class='ltx_abstract']")
    if abstract_tag is not None:
        first_paragraph = abstract_tag.find("p")
        if first_paragraph is not None:
            abstract = first_paragraph.text_content()

    first_image = None
    for figure in html.xpath("//figure[@class='ltx_figure']"):
        img = figure.find("img")
        if img is not None:
            first_image = img.attrib["src"]
            break

    body = stringify_children(html.find("body"))

    # Remove all emails
    # Can't figure out how to do this elegantly with lxml
    body = EMAIL_RE.sub("", body)

    return {
        # FIXME: This should be str but it's bytes for some reason.
        # It's very odd - BeautifulSoup's docs insists everything is unicode,
        #  and even trying to force the input to be utf-8 doesn't help.
        "body": body,
        # just links, styles, and scripts in <head> so we can re-insert in arxiv vanity <head>
        #  stuff that's in the <body> gets included above
        "links": "".join(to_string(e) for e in head.findall("link")),
        "styles": "".join(to_string(e) for e in head.findall("style")),
        "scripts": "".join(to_string(e) for e in head.findall("script")),
        "abstract": abstract,
        "first_image": first_image,
    }


def to_string(e):
    return lxml.html.tostring(e, encoding="unicode")


# https://stackoverflow.com/questions/4624062/get-all-text-inside-a-tag-in-lxml
def stringify_children(node):
    return "".join(
        chunk
        for chunk in chain(
            (node.text,),
            chain(
                *(
                    (
                        lxml.etree.tostring(child, with_tail=False, encoding="unicode"),
                        child.tail,
                    )
                    for child in node.getchildren()
                )
            ),
            (node.tail,),
        )
        if chunk
    )

