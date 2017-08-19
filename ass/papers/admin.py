from django.contrib import admin
from django.utils.safestring import mark_safe
import json
from .models import Paper, Render


class PaperAdmin(admin.ModelAdmin):
    actions = ['download', 'render']
    list_display = ['title', 'is_downloaded', 'render_state']

    def is_downloaded(self, obj):
        return bool(obj.source_file.name)
    is_downloaded.boolean = True

    def render_state(self, obj):
        try:
            render = obj.renders.latest()
        except Render.DoesNotExist:
            return ""
        return '<a href="../render/{}/">{}</a>'.format(render.id, render.state)
    render_state.allow_tags = True

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
    # The fields except the ones we're formatting
    RENDER_FIELDS = [
        f.name for f in Render._meta.get_fields()
        if f.name not in ['container_logs', 'container_inspect']
    ] + ['formatted_container_logs', 'formatted_container_inspect']
    fields = RENDER_FIELDS
    readonly_fields = RENDER_FIELDS

    def formatted_container_logs(self, obj):
        return mark_safe("<pre>{}</pre>".format(obj.container_logs))
    formatted_container_logs.short_description = 'Container logs'

    def formatted_container_inspect(self, obj):
        formatted = json.dumps(obj.container_inspect, indent=2)
        return mark_safe("<pre>{}</pre>".format(formatted))
    formatted_container_inspect.short_description = 'Container inspect'


admin.site.register(Render, RenderAdmin)
