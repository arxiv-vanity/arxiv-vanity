from django.contrib import admin
from .models import Paper


class PaperAdmin(admin.ModelAdmin):
    pass
admin.site.register(Paper, PaperAdmin)
