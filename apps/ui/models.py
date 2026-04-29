from django.db import models


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
