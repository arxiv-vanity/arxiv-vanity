import importlib
from django.test import TestCase

from ..models import Paper, Render
from .utils import create_paper, create_render


# Python can't import modules starting with a number
remove_version_from_arxiv_ids = importlib.import_module(
    "arxiv_vanity.papers.migrations.0014_remove_version_from_arxiv_ids"
).remove_version_from_arxiv_ids


class RemoveVersionsFromArxivIDsTest(TestCase):
    def test_remove_version_from_arxiv_ids(self):
        paper = create_paper(
            arxiv_id="1708.03311v1",
            arxiv_version=0,
            arxiv_url="https://arxiv.org/abs/1708.03311v1",
            pdf_url="https://arxiv.org/pdf/1708.03311v1",
        )
        create_render(paper=paper, state=Render.STATE_SUCCESS)
        paper = create_paper(arxiv_id="1708.03313v3", arxiv_version=0)
        create_render(paper=paper, state=Render.STATE_SUCCESS)
        paper = create_paper(arxiv_id="1708.03313v2", arxiv_version=0)
        create_render(paper=paper, state=Render.STATE_SUCCESS)
        # a paper without version that already exists for some reason
        paper_without_render = create_paper(arxiv_id="1708.03314", arxiv_version=2)
        create_render(paper=paper, state=Render.STATE_SUCCESS)
        paper = create_paper(arxiv_id="1708.03314v2", arxiv_version=0)
        create_render(paper=paper, state=Render.STATE_SUCCESS)

        self.assertEqual(Paper.objects.count(), 5)
        self.assertEqual(Paper.objects.deleted().count(), 0)
        self.assertEqual(Render.objects.count(), 5)

        remove_version_from_arxiv_ids(Paper)

        self.assertEqual(Paper.objects.count(), 3)
        self.assertEqual(Paper.objects.deleted().count(), 2)
        self.assertEqual(Render.objects.count(), 5)

        paper = Paper.objects.get(arxiv_id="1708.03311")
        self.assertEqual(paper.arxiv_version, 1)
        self.assertEqual(paper.arxiv_url, "https://arxiv.org/abs/1708.03311")
        self.assertEqual(paper.pdf_url, "https://arxiv.org/pdf/1708.03311")

        # ensure most recent version is kept
        paper = Paper.objects.get(arxiv_id="1708.03313")
        self.assertEqual(paper.arxiv_version, 3)
        self.assertTrue(
            Paper.objects.deleted().filter(arxiv_id="1708.03313v2").exists()
        )

        # ensure paper without version already existing is handled correctly
        self.assertEqual(
            Paper.objects.get(arxiv_id="1708.03314").pk, paper_without_render.pk
        )
        self.assertTrue(
            Paper.objects.deleted().filter(arxiv_id="1708.03314v2").exists()
        )
