from django.contrib.sitemaps import Sitemap
from .papers.models import Paper


class PaperSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5
    limit = 2000

    def items(self):
        return Paper.objects.only("arxiv_id", "updated").all()

    def lastmod(self, obj):
        return obj.updated


sitemaps = {"papers": PaperSitemap}
