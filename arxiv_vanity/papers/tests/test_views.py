import datetime
import os
import shutil
import unittest
from unittest import mock
from django.conf import settings
from django.test import TestCase, override_settings
from ..models import Render, Paper
from ..views import convert_query_to_arxiv_id
from .utils import (
    create_paper,
    create_render,
    create_render_with_html,
    create_source_file,
    patch_update_or_create_from_arxiv_id,
    patch_render_run,
)


class PaperListViewTest(TestCase):
    def test_view(self):
        paper1 = create_paper(title="Paper no render", arxiv_id="1111.1111")
        paper2 = create_paper(title="Paper unstarted render", arxiv_id="1111.1112")
        create_render(paper=paper2, state=Render.STATE_UNSTARTED)
        paper3 = create_paper(title="Paper failed render", arxiv_id="1111.1113")
        create_render(paper=paper3, state=Render.STATE_FAILURE)
        paper4 = create_paper(title="Paper success render", arxiv_id="1234.5678")
        create_render(paper=paper4, state=Render.STATE_SUCCESS)
        paper5 = create_paper(
            title="Paper not ML", categories=["astro-ph"], arxiv_id="1111.1114"
        )
        create_render(paper=paper5, state=Render.STATE_SUCCESS)
        res = self.client.get("/papers/")
        self.assertEqual(res["Cache-Control"], f"public, max-age=86400")
        # FIXME: has_success_render() is too slow
        # self.assertNotIn("Paper no render", str(res.content))
        # self.assertNotIn("Paper unstarted render", str(res.content))
        # self.assertNotIn("Paper failed render", str(res.content))
        self.assertIn("Paper success render", str(res.content))
        self.assertIn("/papers/1234.5678/", str(res.content))
        self.assertNotIn("Paper not ML", str(res.content))


TEST_MEDIA_ROOT = os.path.join(settings.MEDIA_ROOT, "test")


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class PaperDetailViewTest(TestCase):
    def tearDown(self):
        try:
            shutil.rmtree(TEST_MEDIA_ROOT)
        except FileNotFoundError:
            pass

    @patch_render_run()
    def test_it_outputs_rendered_papers(self, mock_run):
        source_file = create_source_file(arxiv_id="1234.5678", file="foo.tar.gz")
        paper = create_paper(
            arxiv_id="1234.5678", title="Some paper", source_file=source_file,
        )
        render = create_render_with_html(paper=paper)
        res = self.client.get("/papers/1234.5678/")
        self.assertEqual(res.status_code, 200)
        content = res.content.decode("utf-8")
        self.assertEqual(
            res["Cache-Control"], f"public, max-age={settings.PAPER_CACHE_SECONDS}"
        )
        # using .count() because multiple copies of script were inserted at one point
        self.assertEqual(
            content.count("Some paper"), 3
        )  # title, opengraph, citation tags
        self.assertEqual(content.count("script was inserted"), 1)
        self.assertEqual(content.count("style-was-inserted"), 1)
        self.assertEqual(content.count("body was inserted"), 1)

        # literal new line, caused by django naively converting bytes to str
        self.assertNotIn("\\n", content)

        # ensure we haven't spun off a new render job
        mock_run.assert_not_called()

    @patch_render_run()
    def test_expired_render_gets_displayed_and_rerendered(self, mock_run):
        source_file = create_source_file(arxiv_id="1234.5678", file="foo.tar.gz")
        paper = create_paper(
            arxiv_id="1234.5678",
            title="Some paper",
            source_file=source_file,
            updated=datetime.datetime(
                2017, 8, 5, 17, 46, 28, tzinfo=datetime.timezone.utc
            ),
        )
        render = create_render_with_html(paper=paper, is_expired=True)

        res = self.client.get("/papers/1234.5678/")
        content = res.content.decode("utf-8")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Some paper", content)

        mock_run.assert_called_once()

        self.assertEqual(paper.renders.count(), 2)
        render = paper.renders.latest()
        self.assertEqual(render.state, Render.STATE_RUNNING)

    def test_it_shows_an_error_if_a_paper_is_not_renderable(self):
        source_file = create_source_file(arxiv_id="1234.5678", file="foo.pdf")
        paper = create_paper(
            arxiv_id="1234.5678",
            pdf_url="http://arxiv.org/pdf/1234.5678",
            source_file=source_file,
        )
        res = self.client.get("/papers/1234.5678/")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(
            res["Cache-Control"], f"public, max-age={settings.PAPER_CACHE_SECONDS}"
        )
        # FIXME: quotes aren't working in this, so just check this substr
        self.assertIn("have LaTeX source code", str(res.content))
        self.assertIn("https://arxiv.org/pdf/1234.5678", str(res.content))

    @patch_update_or_create_from_arxiv_id()
    @patch_render_run()
    def test_it_creates_new_papers_if_they_dont_exist(self, mock_create, mock_run):
        res = self.client.get("/papers/1234.5678/")
        self.assertEqual(res.status_code, 503)
        self.assertIn("This paper is rendering!", str(res.content))
        self.assertEqual(
            res["Cache-Control"], "max-age=0, no-cache, no-store, must-revalidate"
        )

        mock_create.assert_called_once()
        mock_run.assert_called_once()

        render = Render.objects.latest()
        self.assertEqual(render.paper.arxiv_id, "1234.5678")
        self.assertEqual(render.state, Render.STATE_RUNNING)

    def test_it_shows_a_message_if_the_paper_is_being_rendered(self):
        source_file = create_source_file(arxiv_id="1234.5678", file="foo.tar.gz")
        paper = create_paper(arxiv_id="1234.5678", source_file=source_file)
        render = create_render(paper=paper, state=Render.STATE_RUNNING)
        res = self.client.get("/papers/1234.5678/")
        self.assertEqual(res.status_code, 503)
        self.assertEqual(
            res["Cache-Control"], "max-age=0, no-cache, no-store, must-revalidate"
        )
        self.assertIn("This paper is rendering", str(res.content))

    def test_it_shows_an_error_if_the_paper_has_failed_to_render(self):
        source_file = create_source_file(arxiv_id="1234.5678", file="foo.tar.gz")
        paper = create_paper(
            arxiv_id="1234.5678", source_file=source_file, title="Theory of everything"
        )
        render = create_render(paper=paper, state=Render.STATE_FAILURE)
        res = self.client.get("/papers/1234.5678/")
        self.assertEqual(res.status_code, 500)
        self.assertEqual(
            res["Cache-Control"], f"public, max-age={settings.PAPER_CACHE_SECONDS}"
        )
        self.assertIn(
            'The paper "Theory of everything" failed to render', str(res.content)
        )

    @patch_render_run()
    def test_it_shows_an_error_and_rerenders_if_there_is_failed_expired_render(
        self, mock_run
    ):
        source_file = create_source_file(arxiv_id="1234.5678", file="foo.tar.gz")
        paper = create_paper(
            arxiv_id="1234.5678", source_file=source_file, title="Theory of everything"
        )
        render = create_render(paper=paper, state=Render.STATE_FAILURE, is_expired=True)
        res = self.client.get("/papers/1234.5678/")
        self.assertEqual(res.status_code, 503)
        self.assertIn("This paper is rendering", str(res.content))
        mock_run.assert_called_once()

    def test_it_redirects_different_versions_to_a_canonical_one(self):
        source_file = create_source_file(arxiv_id="1234.5678", file="foo.tar.gz")
        paper = create_paper(
            arxiv_id="1234.5678", title="Some paper", source_file=source_file
        )
        render = create_render_with_html(paper=paper)
        res = self.client.get("/papers/1234.5678v1/")
        self.assertRedirects(res, "/papers/1234.5678/")

    def test_arxiv_style_paths(self):

        source_file = create_source_file(arxiv_id="1234.5678", file="foo.tar.gz")
        title = "Decoupling Virtual Machines from Semaphores in Model Checking"
        create_paper(arxiv_id="1234.5678", source_file=source_file, title=title)

        responses = map(
            lambda x: self.client.get(x),
            [
                "/abs/1234.5678/",
                "/format/1234.5678/",
                "/pdf/1234.5678/",
                "/pdf/1234.5678.pdf/",
            ],
        )

        for res in responses:
            self.assertRedirects(
                res, "/papers/1234.5678/", fetch_redirect_response=False
            )


class TestPaperConvert(TestCase):
    def test_convert_query_to_arxiv_id(self):
        # arxiv URLs
        self.assertEqual(
            convert_query_to_arxiv_id("http://arxiv.org/abs/1709.04466v1"),
            "1709.04466v1",
        )
        self.assertEqual(
            convert_query_to_arxiv_id("http://arxiv.org/abs/astro-ph/0601001"),
            "astro-ph/0601001",
        )
        self.assertEqual(
            convert_query_to_arxiv_id("http://arXiv.org/abs/1709.04466v1"),
            "1709.04466v1",
        )
        self.assertEqual(
            convert_query_to_arxiv_id("https://arxiv.org/abs/1709.04466v1"),
            "1709.04466v1",
        )
        self.assertEqual(
            convert_query_to_arxiv_id("http://arxiv.org/pdf/1709.04466v1"),
            "1709.04466v1",
        )
        self.assertEqual(
            convert_query_to_arxiv_id("https://arxiv.org/pdf/1709.04466v1"),
            "1709.04466v1",
        )
        self.assertEqual(
            convert_query_to_arxiv_id("https://arxiv.org/pdf/1709.04466v1.pdf"),
            "1709.04466v1",
        )
        self.assertEqual(
            convert_query_to_arxiv_id("arxiv.org/pdf/1709.04466v1"), "1709.04466v1"
        )
        self.assertEqual(
            convert_query_to_arxiv_id(
                "https://arxiv.org/pdf/1511.08861.pdf#page=10&zoom=100,0,732"
            ),
            "1511.08861",
        )
        self.assertEqual(
            convert_query_to_arxiv_id("https://arxiv.org/abs/1711.01768#"), "1711.01768"
        )

        # arxiv IDs
        self.assertEqual(convert_query_to_arxiv_id("1709.04466"), "1709.04466")
        self.assertEqual(convert_query_to_arxiv_id("1709.04466v1"), "1709.04466v1")
        self.assertEqual(
            convert_query_to_arxiv_id("astro-ph/0601001v1"), "astro-ph/0601001v1"
        )
        self.assertEqual(convert_query_to_arxiv_id("arxiv:1709.04466"), "1709.04466")
        self.assertEqual(convert_query_to_arxiv_id("arXiv:1709.04466"), "1709.04466")

        # arxiv vanity URLs
        self.assertEqual(
            convert_query_to_arxiv_id(
                "https://www.arxiv-vanity.com/papers/1707.08901v1/"
            ),
            "1707.08901v1",
        )
        self.assertEqual(
            convert_query_to_arxiv_id(
                "https://www.arxiv-vanity.com/papers/1707.08901v1/?foo=bar"
            ),
            "1707.08901v1",
        )
        self.assertEqual(
            convert_query_to_arxiv_id("http://localhost:8010/html/1707.08901v1/"),
            "1707.08901v1",
        )
        self.assertEqual(
            convert_query_to_arxiv_id("http://localhost:8000/papers/1707.08901v1/"),
            "1707.08901v1",
        )

        # non-matching
        self.assertEqual(
            convert_query_to_arxiv_id("https://example.com/abs/1709.04466v1"), None
        )
        self.assertEqual(
            convert_query_to_arxiv_id("https://example.com/pdf/1709.04466v1"), None
        )
        self.assertEqual(
            convert_query_to_arxiv_id("http://arxiv.org/1709.04466v1"), None
        )
        self.assertEqual(convert_query_to_arxiv_id("4789432"), None)
        self.assertEqual(convert_query_to_arxiv_id("foobar"), None)


class TestPaperRenderState(TestCase):
    def test_render_state(self):
        source_file = create_source_file(arxiv_id="1234.5678", file="foo.tar.gz")
        paper = create_paper(arxiv_id="1234.5678", source_file=source_file)
        render = create_render(paper=paper, state=Render.STATE_RUNNING)
        res = self.client.get("/papers/1234.5678/render-state/")
        self.assertEqual(res.json()["state"], "running")
        render.state = Render.STATE_SUCCESS
        render.save()
        res = self.client.get("/papers/1234.5678/render-state/")
        self.assertEqual(res.json()["state"], "success")


class TestRenderUpdateState(TestCase):
    def test_render_update_state(self):
        source_file = create_source_file(arxiv_id="1234.5678", file="foo.tar.gz")
        paper = create_paper(arxiv_id="1234.5678", source_file=source_file)
        render = create_render(paper=paper, state=Render.STATE_RUNNING)
        with mock.patch("arxiv_vanity.papers.models.Render.update_state") as m:
            res = self.client.post(
                f"/renders/{render.pk}/update-state/", {"exit_code": "1"}
            )
            self.assertEqual(res.status_code, 200)
            m.assert_called_once_with(exit_code="1")
