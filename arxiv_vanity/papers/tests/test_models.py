from django.test import TestCase
from ..models import guess_extension_from_headers
from .utils import create_paper, create_render


class PaperTest(TestCase):
    def test_get_source_url(self):
        paper = create_paper(arxiv_id='1708.03312v1')
        self.assertEqual(paper.get_source_url(), 'https://arxiv.org/e-print/1708.03312v1')

    def test_get_https_arxiv_url(self):
        paper = create_paper(arxiv_id='http://arxiv.org/abs/1708.03312v1')
        self.assertEqual(paper.get_https_arxiv_url(), 'https://arxiv.org/abs/1708.03312v1')

    def test_get_https_pdf_url(self):
        paper = create_paper(pdf_url='http://arxiv.org/pdf/1708.03312v1')
        self.assertEqual(paper.get_https_pdf_url(), 'https://arxiv.org/pdf/1708.03312v1')

    def test_is_renderable(self):
        paper = create_paper(source_file=None)
        self.assertFalse(paper.is_renderable())

        paper = create_paper(source_file="foo.pdf")
        self.assertFalse(paper.is_renderable())

        paper = create_paper(source_file="foo.tar.gz")
        self.assertTrue(paper.is_renderable())

    def test_guess_extension_from_headers(self):
        self.assertEqual(guess_extension_from_headers({
            'content-type': 'application/pdf',
        }), '.pdf')
        self.assertEqual(guess_extension_from_headers({
            'content-encoding': 'x-gzip',
            'content-type': 'application/postscript',
        }), '.ps.gz')
        self.assertEqual(guess_extension_from_headers({
            'content-encoding': 'x-gzip',
            'content-type': 'application/x-eprint-tar',
        }), '.tar.gz')
        self.assertEqual(guess_extension_from_headers({
            'content-encoding': 'x-gzip',
            'content-type': 'application/x-eprint',
        }), '.tex')
        self.assertEqual(guess_extension_from_headers({
            'content-encoding': 'x-gzip',
            'content-type': 'application/x-dvi',
        }), '.dvi.gz')


class RenderTest(TestCase):
    def test_get_webhook_url(self):
        paper = create_paper()
        render = create_render(paper=paper)
        self.assertEqual(render.get_webhook_url(), f"http://web:8000/renders/{render.pk}/update-state/")
