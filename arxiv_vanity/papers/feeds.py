from django.contrib.syndication.views import Feed
from django.urls import reverse
from .models import Paper

class LatestPapersFeed(Feed):
    title = "arXiv Vanity – Latest machine learning papers"
    link = "/papers/"
    description = "Latest machine learning papers from arXiv rendered as web pages"

    def items(self):
        qs = Paper.objects.machine_learning().has_successful_render()
        return qs.order_by('-updated')[:25]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.summary

    def item_author_name(self, item):
        try:
            return ', '.join(author['name'] for author in item.authors)
        except KeyError:
            return ''

    def item_pubdate(self, item):
        return item.updated
