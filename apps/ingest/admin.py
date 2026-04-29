from django.contrib import admin
from .models import ImportRun, ImporterState


@admin.register(ImporterState)
class ImporterStateAdmin(admin.ModelAdmin):
    list_display = ['name', 'log_file_path', 'last_position', 'last_read_at', 'is_active', 'updated_at']
    list_filter = ['is_active', 'last_read_at', 'created_at']
    search_fields = ['name', 'log_file_path', 'last_error']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        ('General', {
            'fields': ['name', 'log_file_path', 'is_active']
        }),
        ('File Tracking', {
            'fields': ['last_position', 'last_size', 'last_modified_at', 'last_read_at'],
            'description': 'State information for incremental import'
        }),
        ('Import History', {
            'fields': ['last_import_run', 'last_error'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


@admin.register(ImportRun)
class ImportRunAdmin(admin.ModelAdmin):
    list_display = ['id', 'source_filename', 'status', 'started_at', 'finished_at', 'lines_total', 'lines_imported', 'lines_skipped']
    list_filter = ['status', 'started_at']
    search_fields = ['source_filename', 'notes']
    readonly_fields = ['started_at', 'finished_at']
    ordering = ['-started_at']
