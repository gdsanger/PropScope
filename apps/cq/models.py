from django.db import models


class BandDefinition(models.Model):
    """
    Defines amateur radio band frequency ranges.
    Used to map frequencies to band designations (e.g., 40m, 20m).
    """
    name = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Band name (e.g., 40m, 20m, 10m)"
    )
    lower_frequency_mhz = models.FloatField(
        db_index=True,
        help_text="Lower frequency bound in MHz"
    )
    upper_frequency_mhz = models.FloatField(
        db_index=True,
        help_text="Upper frequency bound in MHz"
    )
    mode_hint = models.CharField(
        max_length=20,
        blank=True,
        help_text="Mode hint (e.g., HF, VHF, UHF)"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this band definition is active and should be used for lookups"
    )
    notes = models.TextField(blank=True, help_text="Additional notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['lower_frequency_mhz']
        verbose_name = "Band Definition"
        verbose_name_plural = "Band Definitions"
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['lower_frequency_mhz', 'upper_frequency_mhz']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.lower_frequency_mhz}-{self.upper_frequency_mhz} MHz)"


class HeardSignal(models.Model):
    """
    Stores a received CQ call from WSJT-X ALL.TXT.
    """
    # Reference to import run
    import_run = models.ForeignKey(
        'ingest.ImportRun',
        on_delete=models.CASCADE,
        related_name='heard_signals',
        help_text="The import run this signal belongs to"
    )

    # Basic signal data
    timestamp = models.DateTimeField(db_index=True, help_text="When the signal was received")
    frequency_mhz = models.FloatField(help_text="Frequency in MHz")
    band = models.CharField(max_length=10, db_index=True, help_text="Band (e.g., 20m, 40m)")
    mode = models.CharField(max_length=20, help_text="Mode (e.g., FT8, FT4)")
    snr = models.IntegerField(help_text="Signal-to-noise ratio in dB")
    dt = models.FloatField(help_text="Time offset in seconds")
    audio_frequency = models.IntegerField(help_text="Audio frequency in Hz")
    raw_message = models.CharField(max_length=100, help_text="Raw decoded message")
    raw_line = models.TextField(help_text="Complete raw line from ALL.TXT")
    raw_hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="SHA256 hash of raw_line for deduplication"
    )

    # Callsign information
    callsign = models.CharField(max_length=32, db_index=True, help_text="Callsign")
    callsign_country = models.CharField(max_length=100, null=True, blank=True, help_text="Country from callsign prefix")
    callsign_continent = models.CharField(max_length=50, null=True, blank=True, help_text="Continent from callsign prefix")
    qrz_url = models.URLField(null=True, blank=True, help_text="QRZ.com URL for the callsign")

    # CQ target (e.g., DX, NA, EU, AS, RU, JA, CA)
    cq_target = models.CharField(max_length=10, null=True, blank=True, db_index=True, help_text="CQ target prefix (e.g., DX, NA, EU)")

    # Locator information
    locator = models.CharField(max_length=10, db_index=True, null=True, blank=True, help_text="Maidenhead locator (4 or 6 char)")
    locator_lat = models.FloatField(null=True, blank=True, help_text="Latitude from locator")
    locator_lon = models.FloatField(null=True, blank=True, help_text="Longitude from locator")
    locator_country = models.CharField(max_length=100, null=True, blank=True, help_text="Country from locator")
    locator_alt_country = models.CharField(max_length=100, null=True, blank=True, help_text="Alternative country from locator (for border areas)")
    locator_continent = models.CharField(max_length=50, null=True, blank=True, help_text="Continent from locator")
    locator_ambiguous = models.BooleanField(default=False, help_text="True if locator spans multiple countries")

    # Distance
    distance_km = models.FloatField(null=True, blank=True, db_index=True, help_text="Distance in kilometers")

    # Direction (azimuth)
    azimuth_deg = models.FloatField(null=True, blank=True, help_text="Azimuth/bearing from station to signal source in degrees (0-360)")

    # Meta fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['callsign']),
            models.Index(fields=['locator']),
            models.Index(fields=['band']),
            models.Index(fields=['distance_km']),
            models.Index(fields=['timestamp', 'band']),
            models.Index(fields=['timestamp', 'callsign']),
        ]

    def __str__(self):
        locator_str = f" {self.locator}" if self.locator else ""
        return f"{self.callsign}{locator_str} @ {self.timestamp} ({self.band}, {self.snr}dB)"

    @property
    def locator_map_url(self):
        """
        Generate a k7fry.com grid map URL for this signal's Maidenhead locator.

        Returns:
            URL string for k7fry.com grid map, or None if no locator is present

        Example:
            >>> signal = HeardSignal(locator="JN68")
            >>> signal.locator_map_url
            "https://k7fry.com/grid/?qth=JN68"

            >>> signal = HeardSignal(locator=None)
            >>> signal.locator_map_url
            None
        """
        if not self.locator:
            return None

        from apps.geo.services import MaidenheadService
        service = MaidenheadService()
        return service.get_grid_map_url(self.locator)
