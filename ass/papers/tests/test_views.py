from django.test import TestCase
from .utils import create_paper

class PaperListViewTest(TestCase):
    def test_view(self):
        paper = create_paper(title="Foobar 1")
        res = self.client.get('/')
        self.assertIn('Foobar 1', str(res.content))
