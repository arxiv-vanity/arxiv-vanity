import datetime
from django.test import TestCase
from django.utils import timezone
from ..models import Render, Paper, SourceFile
from .utils import create_paper, create_render, create_source_file_bulk_tarball, create_source_file


class PaperTest(TestCase):
    def test_get_https_arxiv_url(self):
        paper = create_paper(arxiv_url='http://arxiv.org/abs/1708.03313')
        self.assertEqual(paper.get_https_arxiv_url(), 'https://arxiv.org/abs/1708.03313')

    def test_get_https_pdf_url(self):
        paper = create_paper(pdf_url='http://arxiv.org/pdf/1708.03313')
        self.assertEqual(paper.get_https_pdf_url(), 'https://arxiv.org/pdf/1708.03313')

    def test_is_renderable(self):
        paper = create_paper(source_file=None)
        self.assertFalse(paper.is_renderable())

        source_file = create_source_file(file='foo.tar.gz')
        paper = create_paper(source_file=source_file)
        self.assertTrue(paper.is_renderable())

    def test_is_deleted(self):
        paper = create_paper(arxiv_id='1708.03313')
        self.assertEqual(Paper.objects.count(), 1)
        self.assertEqual(Paper.objects.deleted().count(), 0)
        paper.is_deleted = True
        paper.save()
        self.assertEqual(Paper.objects.count(), 0)
        self.assertEqual(Paper.objects.deleted().count(), 1)


class RenderTest(TestCase):
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
        SourceFile.objects.create(arxiv_id="1", file="1.gz", bulk_tarball=tarball)
        self.assertFalse(tarball.has_correct_number_of_files())
        SourceFile.objects.create(arxiv_id="2", file="2.gz", bulk_tarball=tarball)
        self.assertTrue(tarball.has_correct_number_of_files())


class SourceFileTest(TestCase):
    def test_is_pdf(self):
        sf = create_source_file(arxiv_id='1234.5678', file='source-files/1234.5678.pdf')
        self.assertTrue(sf.is_pdf())
        sf = create_source_file(arxiv_id='1234.5679', file='source-files/1234.5679.gz')
        self.assertFalse(sf.is_pdf())

    def test_is_renderable(self):
        sf = create_source_file(file="foo.pdf")
        self.assertFalse(sf.is_renderable())

        sf = create_source_file(file="foo.ps.gz")
        self.assertFalse(sf.is_renderable())

        sf = create_source_file(file="foo.tar.gz")
        self.assertTrue(sf.is_renderable())

        sf = create_source_file(file="foo.gz")
        self.assertTrue(sf.is_renderable())
