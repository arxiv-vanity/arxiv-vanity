import datetime
from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.utils import timezone
from .papers.models import Paper


class PaperSitemap(Sitemap):
    priority = 0.5
    limit = 2000
    protocol = 'https' if settings.ENABLE_SSL else 'http'

    def items(self):
        return Paper.objects.only("arxiv_id", "updated").all()

    def lastmod(self, obj):
        return obj.updated

    def changefreq(self, obj):
        #  greater than 5 years ago, assume it ain't gonna change
        if obj.updated < timezone.now() - datetime.timedelta(days=5 * 365):
            return "yearly"
        return "monthly"


sitemaps = {"papers": PaperSitemap}
