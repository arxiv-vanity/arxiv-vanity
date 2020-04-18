"""URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps import views as sitemap_views
from django.urls import path, re_path
from django.views.generic.base import TemplateView, RedirectView
from .feedback.views import submit_feedback
from .papers.feeds import LatestPapersFeed
from .papers.views import (
    HomeView,
    PaperListView,
    paper_detail,
    paper_convert,
    paper_render_state,
    render_update_state,
    stats,
)
from .scraper.arxiv_ids import ARXIV_ID_PATTERN
from .sitemaps import sitemaps

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("papers/", PaperListView.as_view(), name="paper_list"),
    path("papers/feed/", LatestPapersFeed(), name="paper_feed"),
    re_path(
        fr"papers/(?P<arxiv_id>{ARXIV_ID_PATTERN})/$", paper_detail, name="paper_detail"
    ),
    re_path(
        fr"abs/(?P<arxiv_id>{ARXIV_ID_PATTERN})/",
        RedirectView.as_view(pattern_name="paper_detail"),
    ),
    re_path(
        fr"format/(?P<arxiv_id>{ARXIV_ID_PATTERN})/",
        RedirectView.as_view(pattern_name="paper_detail"),
    ),
    re_path(
        fr"pdf/(?P<arxiv_id>{ARXIV_ID_PATTERN})(\.pdf)?/",
        RedirectView.as_view(pattern_name="paper_detail"),
    ),
    re_path(
        fr"papers/(?P<arxiv_id>{ARXIV_ID_PATTERN})/render-state/",
        paper_render_state,
        name="paper_render_state",
    ),
    path(
        "renders/<int:pk>/update-state/",
        render_update_state,
        name="render_update_state",
    ),
    re_path(
        fr"papers/(?P<arxiv_id>{ARXIV_ID_PATTERN})/update-version/",
        paper_render_state,
        name="paper_render_state",
    ),
    path("convert/", paper_convert, name="paper_convert"),
    path("submit-feedback/", submit_feedback),
    path("stats/", stats),
    path("admin/", admin.site.urls),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path("sitemap.xml", sitemap_views.index, {"sitemaps": sitemaps}),
    path(
        "sitemap-<section>.xml",
        sitemap_views.sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
]

# Serve uploaded files in development
if settings.DEBUG and settings.MEDIA_URL:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
