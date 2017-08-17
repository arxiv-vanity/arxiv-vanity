import os
from django.test import TestCase
from ..query import parse
from ..scraper import create_papers
from ...papers.models import Paper

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'test-data.xml')


class ScraperTest(TestCase):
    def test_create_papers(self):
        papers = parse(open(TEST_DATA_PATH).read())
        self.assertEqual(len(list(create_papers(papers))), 10)
        self.assertEqual(Paper.objects.count(), 10)
        # Duplicates should be ignored
        self.assertEqual(len(list(create_papers(papers))), 0)
        self.assertEqual(Paper.objects.count(), 10)

        latest = Paper.objects.latest()
        self.assertEqual(
            latest.title, "Radical-level Ideograph Encoder for RNN-based Sentiment Analysis of Chinese and Japanese")
