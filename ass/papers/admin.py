from django.contrib import admin
from .models import Paper, Render


class PaperAdmin(admin.ModelAdmin):
    actions = ['download', 'render']
    list_display = ['title', 'is_downloaded', 'is_rendered']

    def is_downloaded(self, obj):
        return bool(obj.source_file.name)
    is_downloaded.boolean = True

    def is_rendered(self, obj):
        # TODO(bfirsh): take into account render state
        return obj.renders.count() > 0
    is_rendered.boolean = True

    def download(self, request, queryset):
        for paper in queryset:
            paper.download()
    download.short_description = 'Download selected papers'

    def render(self, request, queryset):
        for paper in queryset:
            paper.render()
    render.short_description = 'Render selected papers'

admin.site.register(Paper, PaperAdmin)


class RenderAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'paper', 'state', 'container_id')


admin.site.register(Render, RenderAdmin)
