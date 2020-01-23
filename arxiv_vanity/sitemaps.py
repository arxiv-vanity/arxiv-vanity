from django.contrib.sitemaps import Sitemap
from .papers.models import Paper


class PaperSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5
    limit = 5000

    def items(self):
        return Paper.objects.all()

    def lastmod(self, obj):
        return obj.updated
