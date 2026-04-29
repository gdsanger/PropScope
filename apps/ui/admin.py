from django.contrib import admin
from .models import PropScopeSettings


@admin.register(PropScopeSettings)
class PropScopeSettingsAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'wsjtx_all_txt_path', 'wsjtx_poll_interval_seconds', 'updated_at']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['name', 'wsjtx_all_txt_path']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        ('General', {
            'fields': ['name', 'is_active']
        }),
        ('WSJT-X Configuration', {
            'fields': ['wsjtx_all_txt_path', 'wsjtx_poll_interval_seconds', 'wsjtx_last_position'],
            'description': 'Configuration for WSJT-X file monitoring'
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
