from django.contrib import admin
from django.template.defaultfilters import truncatechars
from django.utils.html import format_html
import json
from .models import (
    Paper,
    Render,
    PaperIsNotRenderableError,
    SourceFile,
    SourceFileBulkTarball,
)


class HasSuccessfulRenderListFilter(admin.SimpleListFilter):
    title = "has successful render"
    parameter_name = "has_successful_render"

    def lookups(self, request, model_admin):
        return (("1", "Yes"), ("0", "No"))

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.has_successful_render()
        if self.value() == "0":
            return queryset.has_no_successful_render()


class PaperAdmin(admin.ModelAdmin):
    actions = ["render"]
    list_display = [
        "arxiv_id",
        "title",
        "has_source_file",
        "is_renderable",
        "has_successful_render",
        "latest_render",
    ]
    list_filter = [HasSuccessfulRenderListFilter]
    list_per_page = 250
    search_fields = ["arxiv_id", "title"]
    raw_id_fields = ("source_file",)
    ordering = ["-updated"]

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
        return format_html(
            '<a href="../render/{}/change/">{}</a>', render.id, render.state
        )

    def render(self, request, queryset):
        rendered = 0
        not_renderable = 0
        for paper in queryset:
            try:
                paper.render()
            except PaperIsNotRenderableError:
                not_renderable += 1
            else:
                rendered += 1
        s = f"{rendered} successfully rendered."
        if not_renderable > 0:
            s += f" {not_renderable} not renderable."
        self.message_user(request, s)

    render.short_description = "Render selected papers"


admin.site.register(Paper, PaperAdmin)


def mark_as_deleted(modeladmin, request, queryset):
    for render in queryset:
        render.mark_as_deleted()


mark_as_deleted.short_description = "Mark selected renders as deleted"


class RenderAdmin(admin.ModelAdmin):
    list_display = [
        "created_at",
        "short_paper_title",
        "state",
        "short_container_id",
        "is_deleted",
    ]
    list_filter = ["state", "is_deleted"]
    list_per_page = 250
    list_select_related = ["paper"]
    actions = [mark_as_deleted]

    # The fields except the ones we're formatting
    RENDER_FIELDS = [
        f.name
        for f in Render._meta.get_fields()
        if f.name not in ["container_logs", "container_inspect"]
    ] + ["formatted_container_logs", "formatted_container_inspect"]
    fields = RENDER_FIELDS
    readonly_fields = RENDER_FIELDS

    def formatted_container_logs(self, obj):
        return format_html("<pre>{}</pre>", obj.container_logs)

    formatted_container_logs.short_description = "Container logs"

    def formatted_container_inspect(self, obj):
        formatted = json.dumps(obj.container_inspect, indent=2)
        return format_html("<pre>{}</pre>", formatted)

    formatted_container_inspect.short_description = "Container inspect"

    def short_paper_title(self, obj):
        return truncatechars(obj.paper.title, 70)

    short_paper_title.short_description = "Paper"


admin.site.register(Render, RenderAdmin)


class SourceFileBulkTarballAdmin(admin.ModelAdmin):
    pass


admin.site.register(SourceFileBulkTarball, SourceFileBulkTarballAdmin)


class IsFromBulkTarballFilter(admin.SimpleListFilter):
    title = "is from bulk tarball"
    parameter_name = "is_from_bulk_tarball"

    def lookups(self, request, model_admin):
        return (("1", "Yes"), ("0", "No"))

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(bulk_tarball__isnull=False)
        if self.value() == "0":
            return queryset.filter(bulk_tarball__isnull=True)


class SourceFileAdmin(admin.ModelAdmin):
    list_display = ["file", "arxiv_id", "bulk_tarball"]
    list_filter = [IsFromBulkTarballFilter]
    search_fields = ["arxiv_id"]


admin.site.register(SourceFile, SourceFileAdmin)
