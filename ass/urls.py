"""URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from .feedback.views import submit_feedback
from .papers.views import PaperListView, paper_detail, paper_wait, paper_convert

urlpatterns = [
    url(r'^$', PaperListView.as_view()),
    url(r'^papers/(?P<arxiv_id>[^/]+)/$', paper_detail, name='paper_detail'),
    url(r'^papers/(?P<arxiv_id>[^/]+)/wait-until-rendered/$', paper_wait, name='paper_wait'),
    url(r'^convert/$', paper_convert, name='paper_convert'),
    url(r'^submit-feedback/$', submit_feedback),
    url(r'^admin/', admin.site.urls),
]

# Serve uploaded files in development
if settings.DEBUG and settings.MEDIA_URL:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
