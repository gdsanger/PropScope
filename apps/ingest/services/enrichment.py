"""
Enrichment service for signal data.
Adds computed fields based on callsign, locator, and station configuration.
"""

from typing import Optional, Dict, Any
from apps.geo.utils import maidenhead_to_latlon, haversine_distance, frequency_to_band
from apps.callsign.utils import extract_prefix, generate_qrz_url
from apps.geo.models import MaidenheadArea
from apps.callsign.models import CallsignPrefix


class SignalEnricher:
    """
    Enriches signal data with computed fields.
    """

    def __init__(self, station_lat: Optional[float] = None, station_lon: Optional[float] = None):
        """
        Initialize enricher with optional home station coordinates.

        Args:
            station_lat: Home station latitude
            station_lon: Home station longitude
        """
        self.station_lat = station_lat
        self.station_lon = station_lon

    def enrich_signal_data(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich signal data with computed fields.

        Args:
            signal_data: Dictionary with parsed signal data

        Returns:
            Enriched signal data dictionary
        """
        enriched = signal_data.copy()

        # Generate QRZ URL
        if 'callsign' in enriched and enriched['callsign']:
            enriched['qrz_url'] = generate_qrz_url(enriched['callsign'])

        # Determine band from frequency
        if 'frequency_mhz' in enriched:
            enriched['band'] = frequency_to_band(enriched['frequency_mhz'])

        # Process locator if present
        if 'locator' in enriched and enriched['locator']:
            locator = enriched['locator']

            # Get coordinates from locator
            try:
                lat, lon = maidenhead_to_latlon(locator)
                enriched['locator_lat'] = lat
                enriched['locator_lon'] = lon

                # Calculate distance if station coordinates are available
                if self.station_lat is not None and self.station_lon is not None:
                    distance = haversine_distance(
                        self.station_lat, self.station_lon,
                        lat, lon
                    )
                    enriched['distance_km'] = distance
            except ValueError:
                # Invalid locator format
                pass

            # Look up locator in MaidenheadArea table
            locator_4char = locator[:4].upper() if len(locator) >= 4 else locator.upper()
            try:
                area = MaidenheadArea.objects.get(locator=locator_4char)
                enriched['locator_country'] = area.primary_country
                enriched['locator_alt_country'] = area.alternative_countries if area.alternative_countries else None
                enriched['locator_continent'] = area.continent
                enriched['locator_ambiguous'] = area.is_ambiguous
            except (MaidenheadArea.DoesNotExist, Exception):
                # No data for this locator or database not available
                pass

        # Look up callsign prefix
        if 'callsign' in enriched and enriched['callsign']:
            prefix = extract_prefix(enriched['callsign'])
            try:
                prefix_data = CallsignPrefix.objects.get(prefix=prefix)
                enriched['callsign_country'] = prefix_data.country
                enriched['callsign_continent'] = prefix_data.continent
            except (CallsignPrefix.DoesNotExist, Exception):
                # No data for this prefix, try shorter prefixes
                # Try progressively shorter prefixes
                for length in range(len(prefix) - 1, 0, -1):
                    short_prefix = prefix[:length]
                    try:
                        prefix_data = CallsignPrefix.objects.get(prefix=short_prefix)
                        enriched['callsign_country'] = prefix_data.country
                        enriched['callsign_continent'] = prefix_data.continent
                        break
                    except (CallsignPrefix.DoesNotExist, Exception):
                        continue

        return enriched
