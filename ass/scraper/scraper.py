from ..papers.models import Paper
from .query import query


def scrape_papers():
    """
    Download papers from Arxiv's API and insert new ones into the database.
    """
    papers = query()
    for paper in create_papers(papers):
        print("Downloading and rendering {}...".format(paper.arxiv_id))
        paper.render()


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
