import time
from django.conf import settings
from ..papers.models import Paper, PaperIsNotRenderableError
from .query import category_search_query


def scrape_and_render_papers():
    """
    Render new papers from Arxiv's API.
    """
    for paper in query_and_create_papers():
        print(f"Downloading and rendering {paper.arxiv_id}... ", end="", flush=True)
        try:
            paper.render()
        except PaperIsNotRenderableError:
            print("not renderable")
        else:
            print("success")

        # Be nice.
        # This limits both API requests and source downloads because we're using iterators.
        time.sleep(5.0)


def query_and_create_papers():
    """
    Download papers from Arxiv's API and insert new ones into the database.
    Returns an iterator of new papers.
    """
    papers = category_search_query(settings.PAPERS_MACHINE_LEARNING_CATEGORIES)
    for paper in papers:
        obj, created = Paper.objects.update_or_create_from_api(paper)
        if created:
            yield obj
        else:
            print(f"Paper {obj.arxiv_id} already exists. Assuming we have scraped all new papers, so stopping.")
            break
