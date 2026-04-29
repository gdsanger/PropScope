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
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this prefix is active and should be used for lookups"
    )
    notes = models.TextField(blank=True, help_text="Additional notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['prefix']
        verbose_name = "Callsign Prefix"
        verbose_name_plural = "Callsign Prefixes"
        indexes = [
            models.Index(fields=['prefix']),
            models.Index(fields=['country']),
            models.Index(fields=['continent']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.prefix}: {self.country}"


class GermanCallsignClassRule(models.Model):
    """
    Optional table for German callsign license class identification.
    Maps prefix patterns to BNetzA license classes.
    """
    prefix_pattern = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Prefix pattern for German callsigns (e.g., DO, DL, DA6)"
    )
    license_class = models.CharField(
        max_length=10,
        help_text="License class (e.g., A, E)"
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        help_text="Description of the license class or assignment type"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this rule is active and should be used for lookups"
    )
    notes = models.TextField(blank=True, help_text="Additional notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-prefix_pattern']  # Longer patterns first for matching
        verbose_name = "German Callsign Class Rule"
        verbose_name_plural = "German Callsign Class Rules"
        indexes = [
            models.Index(fields=['prefix_pattern']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.prefix_pattern} → Class {self.license_class}"
