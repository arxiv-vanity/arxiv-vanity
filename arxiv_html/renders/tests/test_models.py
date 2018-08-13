from unittest.mock import patch
from django.test import TestCase, override_settings
from .. import tasks
from ..models import Render


class RenderTest(TestCase):
    def test_get_source_url(self):
        render = Render.objects.create(source_type="arxiv", source_id="1234.5678v2")
        self.assertEqual(render.get_source_url(), "https://arxiv.org/src/1234.5678v2")

        render = Render.objects.create(source_type="submission", source_id="1234")
        self.assertEqual(render.get_source_url(), "http://fm-service-endpoint/upload/1234/content")
