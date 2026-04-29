from django.db import models


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

    # Callsign information
    callsign = models.CharField(max_length=32, db_index=True, help_text="Callsign")
    callsign_country = models.CharField(max_length=100, null=True, blank=True, help_text="Country from callsign prefix")
    callsign_continent = models.CharField(max_length=50, null=True, blank=True, help_text="Continent from callsign prefix")
    qrz_url = models.URLField(null=True, blank=True, help_text="QRZ.com URL for the callsign")

    # Locator information
    locator = models.CharField(max_length=6, db_index=True, null=True, blank=True, help_text="Maidenhead locator (4 or 6 char)")
    locator_lat = models.FloatField(null=True, blank=True, help_text="Latitude from locator")
    locator_lon = models.FloatField(null=True, blank=True, help_text="Longitude from locator")
    locator_country = models.CharField(max_length=100, null=True, blank=True, help_text="Country from locator")
    locator_alt_country = models.CharField(max_length=100, null=True, blank=True, help_text="Alternative country from locator (for border areas)")
    locator_continent = models.CharField(max_length=50, null=True, blank=True, help_text="Continent from locator")
    locator_ambiguous = models.BooleanField(default=False, help_text="True if locator spans multiple countries")

    # Distance
    distance_km = models.FloatField(null=True, blank=True, db_index=True, help_text="Distance in kilometers")

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
