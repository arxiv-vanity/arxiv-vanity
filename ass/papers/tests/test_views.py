from django.test import TestCase
from ..models import Render
from .utils import create_paper, create_render

class PaperListViewTest(TestCase):
    def test_view(self):
        paper1 = create_paper(title="Paper no render")
        paper2 = create_paper(title="Paper unstarted render")
        create_render(paper=paper2, state=Render.STATE_UNSTARTED)
        paper3 = create_paper(title="Paper failed render")
        create_render(paper=paper3, state=Render.STATE_FAILURE)
        paper4 = create_paper(title="Paper success render")
        create_render(paper=paper4, state=Render.STATE_SUCCESS)
        res = self.client.get('/')
        self.assertNotIn('Paper no render', str(res.content))
        self.assertNotIn('Paper unstarted render', str(res.content))
        self.assertNotIn('Paper failed render', str(res.content))
        self.assertIn('Paper success render', str(res.content))
