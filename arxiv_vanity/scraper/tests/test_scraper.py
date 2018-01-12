import os
from django.test import TestCase
import vcr
from ..scraper import query_and_create_papers
from ...papers.tests.utils import create_paper

FIXTURES_PATH = os.path.join(os.path.dirname(__file__), 'fixtures')


class ScraperTest(TestCase):
    @vcr.use_cassette(os.path.join(FIXTURES_PATH, 'query.yaml'))
    def test_query_and_create_papers(self):
        # Insert paper that is at position 111 in query.yaml
        paper = create_paper(arxiv_id='1709.09354')

        # NOTE: If this raises vcr.errors.CannotOverwriteExistingCassetteException,
        # that means it is probably not stopping paginating when it has reached 1709.09354v1
        papers = list(query_and_create_papers())

        # Check it stopped at 1709.09354v1
        self.assertEqual(len(papers), 110)
