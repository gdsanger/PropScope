from django.db import models


class ImporterState(models.Model):
    """
    Tracks the runtime state of periodic WSJT-X log file import.
    Enables incremental imports by tracking file position and detecting file changes.
    """
    name = models.CharField(
        max_length=200,
        help_text="Descriptive name for this importer state (e.g., 'Default WSJT-X ALL.TXT', 'FT-710 Shack')"
    )
    log_file_path = models.CharField(
        max_length=500,
        unique=True,
        help_text="Path to the monitored WSJT-X ALL.TXT file"
    )
    last_position = models.BigIntegerField(
        default=0,
        help_text="Byte position in the file where last read ended"
    )
    last_size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="File size at last read (used to detect truncation or rotation)"
    )
    last_modified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last known modification timestamp of the log file"
    )
    last_read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the file was last successfully read"
    )
    last_import_run = models.ForeignKey(
        'ImportRun',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='importer_states',
        help_text="Reference to the most recent ImportRun (optional)"
    )
    last_error = models.TextField(
        blank=True,
        help_text="Last error message if import failed (empty if successful)"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this importer state is active (inactive states are kept for historical reference)"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Importer State"
        verbose_name_plural = "Importer States"
        ordering = ['-is_active', 'name']
        indexes = [
            models.Index(fields=['log_file_path']),
            models.Index(fields=['is_active']),
            models.Index(fields=['-last_read_at']),
        ]

    def __str__(self):
        status = "active" if self.is_active else "inactive"
        return f"{self.name} - {self.log_file_path} ({status})"


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
