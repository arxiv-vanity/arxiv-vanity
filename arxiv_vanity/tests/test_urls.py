from django.urls import resolve
from django.test import TestCase


class UrlsTest(TestCase):

    def test_urls(self):
        resolver = resolve('/papers/1703.07815/')
        self.assertEquals(resolver.view_name, 'paper_detail')

        resolver = resolve('/pdf/1703.07815/')
        self.assertEquals(resolver.view_name, 'django.views.generic.base.RedirectView')

        resolver = resolve('/papers/1703.07815/render-state/')
        self.assertEquals(resolver.view_name, 'paper_render_state')

        resolver = resolve('/papers/astro-ph/0601001/')
        self.assertEquals(resolver.view_name, 'paper_detail')

        resolver = resolve('/papers/astro-ph/0601001/render-state/')
        self.assertEquals(resolver.view_name, 'paper_render_state')
