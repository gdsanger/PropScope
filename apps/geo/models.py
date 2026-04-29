from django.db import models


class MaidenheadArea(models.Model):
    """
    Manually maintained table for 4-character Maidenhead locator grid squares.
    Maps locators to countries and continents.
    """
    locator = models.CharField(
        max_length=4,
        unique=True,
        db_index=True,
        help_text="4-character Maidenhead locator (e.g., JN68)"
    )
    center_lat = models.FloatField(help_text="Center latitude of the grid square")
    center_lon = models.FloatField(help_text="Center longitude of the grid square")
    primary_country = models.CharField(max_length=100, help_text="Primary country in this grid square")
    alternative_countries = models.TextField(
        blank=True,
        help_text="Comma-separated list of alternative countries (for border areas)"
    )
    continent = models.CharField(max_length=50, help_text="Continent code (e.g., EU, NA, AS)")
    is_ambiguous = models.BooleanField(
        default=False,
        help_text="True if this locator spans multiple countries"
    )
    notes = models.TextField(blank=True, help_text="Additional notes")

    class Meta:
        ordering = ['locator']
        verbose_name = "Maidenhead Area"
        verbose_name_plural = "Maidenhead Areas"
        indexes = [
            models.Index(fields=['locator']),
            models.Index(fields=['primary_country']),
            models.Index(fields=['continent']),
        ]

    def __str__(self):
        ambiguous_marker = " (ambiguous)" if self.is_ambiguous else ""
        return f"{self.locator}: {self.primary_country}{ambiguous_marker}"
