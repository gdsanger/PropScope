"""
Core service for band detection from frequency.

This service provides centralized functionality for:
- Detecting amateur radio band from frequency via database lookup

The service uses the BandDefinition database table for all lookups - no hardcoded data.
"""

from typing import Optional
from apps.cq.models import BandDefinition


class BandService:
    """
    Service for band detection from frequency.

    All band definitions are loaded from the BandDefinition database table.
    """

    def detect_band(self, frequency_mhz: float) -> Optional[BandDefinition]:
        """
        Detect amateur radio band from frequency.

        Uses BandDefinition table to find matching active band.
        Returns the first band where:
            lower_frequency_mhz <= frequency_mhz <= upper_frequency_mhz

        Args:
            frequency_mhz: Frequency in MHz

        Returns:
            BandDefinition object if found, None otherwise

        Examples:
            >>> band = service.detect_band(7.074)
            >>> band.name if band else None
            "40m"
            >>> band = service.detect_band(14.074)
            >>> band.name if band else None
            "20m"
            >>> band = service.detect_band(999.999)
            # Returns None (no matching band)
        """
        if frequency_mhz is None or frequency_mhz <= 0:
            return None

        try:
            # Query for active bands where frequency falls within range
            band = BandDefinition.objects.filter(
                is_active=True,
                lower_frequency_mhz__lte=frequency_mhz,
                upper_frequency_mhz__gte=frequency_mhz
            ).first()

            return band
        except Exception:
            # Database not available or other error
            return None

    def get_band_name(self, frequency_mhz: float) -> Optional[str]:
        """
        Get band name from frequency.

        Convenience method that returns just the band name string.

        Args:
            frequency_mhz: Frequency in MHz

        Returns:
            Band name (e.g., "40m", "20m") or None

        Examples:
            >>> service.get_band_name(7.074)
            "40m"
            >>> service.get_band_name(28.074)
            "10m"
        """
        band = self.detect_band(frequency_mhz)
        return band.name if band else None
