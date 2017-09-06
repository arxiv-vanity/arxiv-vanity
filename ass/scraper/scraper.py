from ..papers.models import Paper, PaperIsNotRenderableError
from .query import category_search_query

CATEGORIES = [
    "cs.CV",
    "cs.AI",
    "cs.LG",
    "cs.CL",
    "cs.NE",
    "stat.ML"
]


def scrape_papers():
    """
    Download papers from Arxiv's API and insert new ones into the database.
    """
    papers = category_search_query(CATEGORIES)
    for paper in create_papers(papers):
        print("Downloading and rendering {}... ".format(paper.arxiv_id), end="")
        try:
            paper.render()
        except PaperIsNotRenderableError:
            print("not renderable")
        else:
            print("success")


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
