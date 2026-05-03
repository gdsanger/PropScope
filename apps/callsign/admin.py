from django.contrib import admin
from django.utils.html import format_html
from .models import CallsignPrefix, GermanCallsignClassRule, KnownStation


@admin.register(CallsignPrefix)
class CallsignPrefixAdmin(admin.ModelAdmin):
    list_display = ['prefix', 'country', 'continent', 'itu_region', 'cq_zone', 'is_active']
    list_filter = ['continent', 'itu_region', 'cq_zone', 'is_active']
    search_fields = ['prefix', 'country', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['prefix']


@admin.register(GermanCallsignClassRule)
class GermanCallsignClassRuleAdmin(admin.ModelAdmin):
    list_display = ['prefix_pattern', 'license_class', 'description', 'is_active']
    list_filter = ['license_class', 'is_active']
    search_fields = ['prefix_pattern', 'description', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-prefix_pattern']  # Longer patterns first


@admin.register(KnownStation)
class KnownStationAdmin(admin.ModelAdmin):
    list_display = ['callsign', 'fixed_locator', 'country', 'continent', 'is_verified', 'is_active', 'qrz_link']
    list_filter = ['country', 'continent', 'is_verified', 'is_active', 'source']
    search_fields = ['callsign', 'country', 'continent', 'notes']
    readonly_fields = ['fixed_latitude', 'fixed_longitude', 'created_at', 'updated_at', 'qrz_link', 'grid_map_link']
    ordering = ['callsign']
    fieldsets = (
        ('Station Information', {
            'fields': ('callsign', 'qrz_link')
        }),
        ('Location', {
            'fields': ('fixed_locator', 'grid_map_link', 'fixed_latitude', 'fixed_longitude', 'country', 'continent')
        }),
        ('Metadata', {
            'fields': ('source', 'is_verified', 'is_active', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def qrz_link(self, obj):
        """Display QRZ.com link for the callsign"""
        if obj.callsign:
            from apps.callsign.services.callsign_service import CallsignService
            service = CallsignService()
            url = service.get_qrz_url(obj.callsign)
            return format_html('<a href="{}" target="_blank">{}</a>', url, url)
        return '-'
    qrz_link.short_description = 'QRZ.com Link'

    def grid_map_link(self, obj):
        """Display k7fry.com grid map link for the locator"""
        if obj.fixed_locator:
            from apps.geo.services.maidenhead_service import MaidenheadService
            service = MaidenheadService()
            url = service.get_grid_map_url(obj.fixed_locator)
            return format_html('<a href="{}" target="_blank">{}</a>', url, url)
        return '-'
    grid_map_link.short_description = 'Grid Map Link'
