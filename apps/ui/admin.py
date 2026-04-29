from django.contrib import admin
from .models import PropScopeSettings, StationProfile


@admin.register(StationProfile)
class StationProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'callsign', 'locator', 'is_default', 'is_active', 'updated_at']
    list_filter = ['is_default', 'is_active', 'created_at', 'updated_at']
    search_fields = ['name', 'callsign', 'locator']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        ('General', {
            'fields': ['name', 'callsign', 'is_default', 'is_active']
        }),
        ('Location', {
            'fields': ['locator', 'latitude', 'longitude'],
            'description': 'Maidenhead locator and coordinates (lat/lon can be calculated from locator or set manually for precision)'
        }),
        ('Notes', {
            'fields': ['notes'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


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
