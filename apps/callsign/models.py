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


class KnownStation(models.Model):
    """
    Manually maintained table for known stations with fixed locators.
    Used to enrich signals that don't include a locator in the CQ message.
    """
    callsign = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        help_text="Normalized callsign (uppercase, no whitespace)"
    )
    fixed_locator = models.CharField(
        max_length=6,
        help_text="Fixed Maidenhead locator for this station (e.g., JN58, PM95)"
    )
    fixed_latitude = models.FloatField(
        null=True,
        blank=True,
        help_text="Latitude calculated from fixed_locator"
    )
    fixed_longitude = models.FloatField(
        null=True,
        blank=True,
        help_text="Longitude calculated from fixed_locator"
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        help_text="Country name (optional, can be auto-populated)"
    )
    continent = models.CharField(
        max_length=50,
        blank=True,
        help_text="Continent code (e.g., EU, NA, AS)"
    )
    source = models.CharField(
        max_length=50,
        default='manual',
        help_text="Source of information (e.g., manual, qrz, operator_page, log_observation)"
    )
    is_verified = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this assignment has been verified"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this station should be used for enrichment"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about this station"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['callsign']
        verbose_name = "Known Station"
        verbose_name_plural = "Known Stations"
        indexes = [
            models.Index(fields=['callsign']),
            models.Index(fields=['country']),
            models.Index(fields=['continent']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_verified']),
        ]

    def __str__(self):
        return f"{self.callsign} @ {self.fixed_locator}"

    def save(self, *args, **kwargs):
        """
        Override save to normalize callsign and calculate lat/lon from locator.
        """
        # Normalize callsign
        from apps.callsign.services.callsign_service import CallsignService
        callsign_service = CallsignService()
        self.callsign = callsign_service.normalize_callsign(self.callsign)

        # Calculate lat/lon from locator
        if self.fixed_locator:
            from apps.geo.services.maidenhead_service import MaidenheadService
            maidenhead_service = MaidenheadService()
            normalized_locator = maidenhead_service.normalize_locator(self.fixed_locator)

            if maidenhead_service.is_valid_locator(normalized_locator):
                self.fixed_locator = normalized_locator
                lat, lon = maidenhead_service.locator_to_latlon(self.fixed_locator)
                self.fixed_latitude = lat
                self.fixed_longitude = lon

        super().save(*args, **kwargs)
