from django.contrib import admin
from .models import Paper, Render


class PaperAdmin(admin.ModelAdmin):
    pass


admin.site.register(Paper, PaperAdmin)


class RenderAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'paper', 'container_id')


admin.site.register(Render, RenderAdmin)
