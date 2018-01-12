import datetime
from django.test import TestCase
from django.utils import timezone
from ..models import guess_extension_from_headers, Render, Paper, SourceFile
from .utils import create_paper, create_render, create_source_file_bulk_tarball


class PaperTest(TestCase):
    def test_get_source_url(self):
        paper = create_paper(arxiv_id='1708.03313')
        self.assertEqual(paper.get_source_url(), 'https://arxiv.org/e-print/1708.03313')

    def test_get_https_arxiv_url(self):
        paper = create_paper(arxiv_url='http://arxiv.org/abs/1708.03313')
        self.assertEqual(paper.get_https_arxiv_url(), 'https://arxiv.org/abs/1708.03313')

    def test_get_https_pdf_url(self):
        paper = create_paper(pdf_url='http://arxiv.org/pdf/1708.03313')
        self.assertEqual(paper.get_https_pdf_url(), 'https://arxiv.org/pdf/1708.03313')

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

    def test_is_deleted(self):
        paper = create_paper(arxiv_id='1708.03313')
        self.assertEqual(Paper.objects.count(), 1)
        self.assertEqual(Paper.objects.deleted().count(), 0)
        paper.is_deleted = True
        paper.save()
        self.assertEqual(Paper.objects.count(), 0)
        self.assertEqual(Paper.objects.deleted().count(), 1)



class RenderTest(TestCase):
    def test_get_webhook_url(self):
        paper = create_paper()
        render = create_render(paper=paper)
        self.assertEqual(render.get_webhook_url(), f"http://web:8000/renders/{render.pk}/update-state/")

    def test_not_expired(self):
        paper = create_paper()
        render1 = create_render(paper=paper)
        render1.created_at = datetime.datetime(1900, 1, 1).replace(tzinfo=timezone.utc)
        render1.save()
        render2 = create_render(paper=paper)

        # haven't updated expired status yet
        qs = Render.objects.not_expired()
        self.assertIn(render1, qs)
        self.assertIn(render2, qs)

        # batch job which updates the expired flag
        Render.objects.update_is_expired()

        # render1 should have expired now
        qs = Render.objects.not_expired()
        self.assertNotIn(render1, qs)
        self.assertIn(render2, qs)


class SourceFileBulkTarballTest(TestCase):
    def test_has_correct_number_of_items(self):
        tarball = create_source_file_bulk_tarball(num_items=2)
        SourceFile.objects.create(file="1.gz", bulk_tarball=tarball)
        self.assertFalse(tarball.has_correct_number_of_files())
        SourceFile.objects.create(file="2.gz", bulk_tarball=tarball)
        self.assertTrue(tarball.has_correct_number_of_files())
