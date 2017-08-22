import os
import shutil
from django.conf import settings
from django.test import TestCase, override_settings
from ..models import Render
from .utils import create_paper, create_render, create_render_with_html

class PaperListViewTest(TestCase):
    def test_view(self):
        paper1 = create_paper(title="Paper no render")
        paper2 = create_paper(title="Paper unstarted render")
        create_render(paper=paper2, state=Render.STATE_UNSTARTED)
        paper3 = create_paper(title="Paper failed render")
        create_render(paper=paper3, state=Render.STATE_FAILURE)
        paper4 = create_paper(title="Paper success render", arxiv_id="1234.5678")
        create_render(paper=paper4, state=Render.STATE_SUCCESS)
        res = self.client.get('/')
        self.assertNotIn('Paper no render', str(res.content))
        self.assertNotIn('Paper unstarted render', str(res.content))
        self.assertNotIn('Paper failed render', str(res.content))
        self.assertIn('Paper success render', str(res.content))
        self.assertIn('/papers/1234.5678/', str(res.content))


TEST_MEDIA_ROOT = os.path.join(settings.MEDIA_ROOT, 'test')


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class PaperDetailViewTest(TestCase):
    def tearDown(self):
        shutil.rmtree(TEST_MEDIA_ROOT)

    def test_view(self):
        paper = create_paper(arxiv_id="1234.5678", title="Some paper")
        render = create_render_with_html(paper=paper)
        res = self.client.get('/papers/1234.5678/')
        self.assertIn('Some paper', str(res.content))
        self.assertIn('script was inserted', str(res.content))
        self.assertIn('style-was-inserted', str(res.content))
        self.assertIn('body was inserted', str(res.content))
