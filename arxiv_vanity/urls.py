"""URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path
from django.views.generic.base import TemplateView
from .feedback.views import submit_feedback
from .papers.views import HomeView, paper_detail, paper_convert, paper_render_state, render_update_state, stats

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('papers/<arxiv_id>/', paper_detail, name='paper_detail'),
    path('abs/<arxiv_id>/', paper_detail),
    path('format/<arxiv_id>/', paper_detail),
    re_path(r'pdf/(?P<arxiv_id>.*?)(\.pdf)?/', paper_detail),
    path('papers/<arxiv_id>/render-state/', paper_render_state, name='paper_render_state'),
    path('renders/<int:pk>/update-state/', render_update_state, name='render_update_state'),
    path('convert/', paper_convert, name='paper_convert'),
    path('submit-feedback/', submit_feedback),
    path('stats/', stats),
    path('admin/', admin.site.urls),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
]

# Serve uploaded files in development
if settings.DEBUG and settings.MEDIA_URL:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
