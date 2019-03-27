import unittest
from ..processor import process_render


class ProcessorTest(unittest.TestCase):
    def test_arxiv_urls_are_converted_to_vanity_urls(self):
        html = '<a href="https://arxiv.org/abs/1710.06542">Something</a>'

        output = process_render(html, "", {})
        self.assertEqual(output['body'], '<a href="/papers/1710.06542/">Something</a>')
