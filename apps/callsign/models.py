from django.db import models


class CallsignPrefix(models.Model):
    """
    Manually maintained table for callsign prefixes.
    Maps prefixes to countries, continents, and zones.
    """
    prefix = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        help_text="Callsign prefix (e.g., DL, G, K)"
    )
    country = models.CharField(max_length=100, help_text="Country name")
    continent = models.CharField(max_length=50, help_text="Continent code (e.g., EU, NA, AS)")
    itu_region = models.IntegerField(
        help_text="ITU region (1, 2, or 3)",
        null=True,
        blank=True
    )
    cq_zone = models.IntegerField(
        help_text="CQ zone number",
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True, help_text="Additional notes")

    class Meta:
        ordering = ['prefix']
        verbose_name = "Callsign Prefix"
        verbose_name_plural = "Callsign Prefixes"
        indexes = [
            models.Index(fields=['prefix']),
            models.Index(fields=['country']),
            models.Index(fields=['continent']),
        ]

    def __str__(self):
        return f"{self.prefix}: {self.country}"
