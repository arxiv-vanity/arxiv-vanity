from ..bulk_sources import convert_source_file_to_arxiv_id
from django.test import TestCase


class BulkSourcesTest(TestCase):
    def test_convert_source_file_to_arxiv_id(self):
        self.assertEqual(
            convert_source_file_to_arxiv_id("source-files/1805.12181.gz"), "1805.12181"
        )
        self.assertEqual(
            convert_source_file_to_arxiv_id("source-files/1805.12181.pdf"), "1805.12181"
        )
        self.assertEqual(
            convert_source_file_to_arxiv_id("source-files/astro-ph0001055.gz"),
            "astro-ph/0001055",
        )
