from django.test import TestCase
from ..arxiv_ids import remove_version_from_arxiv_id


class ArxivIdsTest(TestCase):
    def test_remove_version_from_arxiv_id(self):
        id, version = remove_version_from_arxiv_id("1709.09354v1")
        self.assertEqual((id, version), ("1709.09354", 1))

        id, version = remove_version_from_arxiv_id("1709.09354")
        self.assertEqual((id, version), ("1709.09354", None))

        id, version = remove_version_from_arxiv_id("astro-ph/0601001")
        self.assertEqual((id, version), ("astro-ph/0601001", None))

        id, version = remove_version_from_arxiv_id("astro-ph/0601001v402")
        self.assertEqual((id, version), ("astro-ph/0601001", 402))
