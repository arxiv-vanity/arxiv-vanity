from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField


class Paper(models.Model):
    arxiv_id = models.CharField(max_length=200, unique=True)
    title = models.TextField()
    published = models.DateTimeField()
    updated = models.DateTimeField()
    summary = models.TextField()
    authors = JSONField()
    arxiv_url = models.URLField()
    pdf_url = models.URLField()
    primary_category = models.CharField(max_length=50)
    categories = ArrayField(models.CharField(max_length=50))
    comment = models.TextField(null=True, blank=True)
    doi = models.CharField(null=True, blank=True, max_length=100)
    journal_ref = models.TextField(null=True, blank=True, max_length=100)

    class Meta:
        get_latest_by = 'updated'

    def __str__(self):
        return self.title
