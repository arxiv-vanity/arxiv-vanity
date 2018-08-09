from django.test import TestCase
from ..models import Render


class RenderTest(TestCase):
    def test_set_state(self):
        render = Render.objects.create(id_type="arxiv", paper_id="1234.5678v2")
        self.assertEqual(render.state, Render.STATE_UNSTARTED)
        render.set_state(Render.STATE_RUNNING)
        # updated locally
        self.assertEqual(render.state, Render.STATE_RUNNING)
        # and in the database
        self.assertEqual(Render.objects.get(id=render.id).state, Render.STATE_RUNNING)
