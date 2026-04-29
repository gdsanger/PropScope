from django.contrib import admin
from .models import HeardSignal, BandDefinition


@admin.register(BandDefinition)
class BandDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'lower_frequency_mhz', 'upper_frequency_mhz', 'mode_hint', 'is_active']
    list_filter = ['mode_hint', 'is_active']
    search_fields = ['name', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['lower_frequency_mhz']


@admin.register(HeardSignal)
class HeardSignalAdmin(admin.ModelAdmin):
    list_display = ['id', 'timestamp', 'callsign', 'locator', 'band', 'snr', 'distance_km', 'mode']
    list_filter = ['band', 'mode', 'timestamp', 'locator_ambiguous']
    search_fields = ['callsign', 'locator', 'raw_message']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Basic Signal Data', {
            'fields': ('import_run', 'timestamp', 'frequency_mhz', 'band', 'mode', 'snr', 'dt', 'audio_frequency')
        }),
        ('Raw Data', {
            'fields': ('raw_message', 'raw_line'),
            'classes': ('collapse',)
        }),
        ('Callsign Information', {
            'fields': ('callsign', 'callsign_country', 'callsign_continent', 'qrz_url')
        }),
        ('Locator Information', {
            'fields': ('locator', 'locator_lat', 'locator_lon', 'locator_country', 'locator_alt_country', 'locator_continent', 'locator_ambiguous')
        }),
        ('Distance', {
            'fields': ('distance_km',)
        }),
        ('Meta', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
