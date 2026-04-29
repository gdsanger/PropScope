from django.db import models


class StationProfile(models.Model):
    """
    Stores information about the operator's receiving station.
    Used as reference point for distance calculations and propagation analysis.
    """
    name = models.CharField(
        max_length=100,
        help_text="Descriptive name for this station profile (e.g., 'Home QTH', 'Portable Berg')"
    )
    callsign = models.CharField(
        max_length=32,
        blank=True,
        help_text="Station callsign (optional, can be empty for receive-only stations)"
    )
    locator = models.CharField(
        max_length=6,
        help_text="Maidenhead locator (4 or 6 characters, e.g., 'JN68')"
    )
    latitude = models.FloatField(
        null=True,
        blank=True,
        help_text="Station latitude (can be calculated from locator or manually set for precision)"
    )
    longitude = models.FloatField(
        null=True,
        blank=True,
        help_text="Station longitude (can be calculated from locator or manually set for precision)"
    )
    is_default = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Mark this profile as the default for distance calculations (only one should be default)"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this profile is active (inactive profiles are kept for historical reference)"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about this station (optional)"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Station Profile"
        verbose_name_plural = "Station Profiles"
        ordering = ['-is_default', '-is_active', 'name']
        indexes = [
            models.Index(fields=['is_default', 'is_active']),
            models.Index(fields=['locator']),
        ]

    def __str__(self):
        parts = [self.name]
        if self.callsign:
            parts.append(f"({self.callsign})")
        if self.locator:
            parts.append(f"- {self.locator}")
        if self.is_default:
            parts.append("[DEFAULT]")
        if not self.is_active:
            parts.append("[INACTIVE]")
        return " ".join(parts)


class PropScopeSettings(models.Model):
    """
    Stores non-sensitive configuration settings for PropScope.
    Sensitive data (like Microsoft Graph API credentials) should be stored in environment variables.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        default="default",
        help_text="Name of this settings configuration"
    )

    # Station Location Configuration
    station_locator = models.CharField(
        max_length=6,
        blank=True,
        help_text="Home station Maidenhead locator (4 or 6 characters)"
    )
    station_latitude = models.FloatField(
        null=True,
        blank=True,
        help_text="Home station latitude (for distance calculation)"
    )
    station_longitude = models.FloatField(
        null=True,
        blank=True,
        help_text="Home station longitude (for distance calculation)"
    )

    # WSJT-X Configuration
    wsjtx_all_txt_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to WSJT-X ALL.TXT file"
    )
    wsjtx_poll_interval_seconds = models.IntegerField(
        default=30,
        help_text="How often to poll the WSJT-X file (in seconds)"
    )
    wsjtx_last_position = models.BigIntegerField(
        default=0,
        help_text="Last read position in the WSJT-X file"
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this settings configuration is active"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "PropScope Settings"
        verbose_name_plural = "PropScope Settings"
        ordering = ['-is_active', '-updated_at']

    def __str__(self):
        status = "active" if self.is_active else "inactive"
        return f"{self.name} ({status})"
