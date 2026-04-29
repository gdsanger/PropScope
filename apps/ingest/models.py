from django.db import models


class ImportRun(models.Model):
    """
    Tracks an import process for WSJT-X ALL.TXT files.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    source_filename = models.CharField(max_length=500, help_text="Path to the imported file")
    started_at = models.DateTimeField(auto_now_add=True, help_text="When the import started")
    finished_at = models.DateTimeField(null=True, blank=True, help_text="When the import finished")
    lines_total = models.IntegerField(default=0, help_text="Total lines in the file")
    lines_imported = models.IntegerField(default=0, help_text="Successfully imported lines")
    lines_skipped = models.IntegerField(default=0, help_text="Skipped lines")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    notes = models.TextField(blank=True, help_text="Additional notes or error messages")

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['-started_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Import {self.id}: {self.source_filename} ({self.status})"
