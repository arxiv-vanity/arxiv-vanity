from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Render


class RenderAdmin(admin.ModelAdmin):
    list_display = ['source_type', 'source_id', 'created_at', 'state']
    list_filter = ['state']
    list_per_page = 250

    readonly_fields = ['formatted_logs']

    def formatted_logs(self, obj):
        return mark_safe(f"<pre>{obj.logs}</pre>")
    formatted_logs.short_description = 'Logs'


admin.site.register(Render, RenderAdmin)
