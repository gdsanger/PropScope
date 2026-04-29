from django.contrib import admin
from .models import ImportRun


@admin.register(ImportRun)
class ImportRunAdmin(admin.ModelAdmin):
    list_display = ['id', 'source_filename', 'status', 'started_at', 'finished_at', 'lines_total', 'lines_imported', 'lines_skipped']
    list_filter = ['status', 'started_at']
    search_fields = ['source_filename', 'notes']
    readonly_fields = ['started_at', 'finished_at']
    ordering = ['-started_at']
