from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Paper, Render


class HasSuccessfulRenderListFilter(admin.SimpleListFilter):
    title = 'has successful render'
    parameter_name = 'has_successful_render'

    def lookups(self, request, model_admin):
        return (
            ('1', 'Yes'),
            ('0', 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.has_successful_render()
        if self.value() == '0':
            return queryset.has_no_successful_render()


class PaperAdmin(admin.ModelAdmin):
    actions = ['render']
    list_display = ['id', 'has_successful_render', 'latest_render']
    list_filter = [HasSuccessfulRenderListFilter]
    list_per_page = 250
    search_fields = ['id']

    def has_source_file(self, obj):
        return bool(obj.source_file)
    has_source_file.boolean = True

    def is_renderable(self, obj):
        return obj.is_renderable()
    is_renderable.boolean = True

    def has_successful_render(self, obj):
        return obj.renders.succeeded().exists()
    has_successful_render.boolean = True

    def latest_render(self, obj):
        try:
            render = obj.renders.latest()
        except Render.DoesNotExist:
            return ""
        return format_html('<a href="../render/{}/">{}</a>', render.id, render.state)

    def render(self, request, queryset):
        rendered = 0
        for paper in queryset:
            paper.render()
            rendered += 1
        self.message_user(request, f"{rendered} successfully rendered.")
    render.short_description = 'Render selected papers'


admin.site.register(Paper, PaperAdmin)


class RenderAdmin(admin.ModelAdmin):
    list_display = ['paper', 'created_at', 'state']
    list_filter = ['state']
    list_per_page = 250
    list_select_related = ['paper']

    readonly_fields = ['formatted_logs']

    def formatted_logs(self, obj):
        return mark_safe(f"<pre>{obj.logs}</pre>")
    formatted_logs.short_description = 'Logs'


admin.site.register(Render, RenderAdmin)
