"""
Enrichment service for signal data.
Adds computed fields based on callsign, locator, and station configuration.
"""

from typing import Optional, Dict, Any
from apps.geo.utils import maidenhead_to_latlon, haversine_distance
from apps.geo.models import MaidenheadArea
from apps.callsign.services import CallsignService
from apps.cq.services import BandService
from apps.geo.services import GeoService


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
        self.callsign_service = CallsignService()
        self.band_service = BandService()
        self.geo_service = None  # Lazy-loaded to avoid startup overhead

    def _get_geo_service(self) -> GeoService:
        """Lazy-load GeoService to avoid loading geodata on every enricher init."""
        if self.geo_service is None:
            self.geo_service = GeoService()
        return self.geo_service

    def enrich_signal_data(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich signal data with computed fields.

        Args:
            signal_data: Dictionary with parsed signal data

        Returns:
            Enriched signal data dictionary
        """
        enriched = signal_data.copy()

        # Generate QRZ URL using CallsignService
        if 'callsign' in enriched and enriched['callsign']:
            enriched['qrz_url'] = self.callsign_service.get_qrz_url(enriched['callsign'])

        # Determine band from frequency using BandService
        if 'frequency_mhz' in enriched:
            band_name = self.band_service.get_band_name(enriched['frequency_mhz'])
            enriched['band'] = band_name if band_name else f"{enriched['frequency_mhz']:.3f}MHz"

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

                # Try GeoService for auto-detection first
                try:
                    geo_service = self._get_geo_service()
                    country_auto, continent_auto = geo_service.get_country_continent(lat, lon)
                    if country_auto:
                        enriched['locator_country_auto'] = country_auto
                    if continent_auto:
                        enriched['locator_continent_auto'] = continent_auto
                except Exception:
                    # GeoService failed, continue without auto-detection
                    pass

            except ValueError:
                # Invalid locator format
                pass

            # Look up locator in MaidenheadArea table (manual override)
            # Manual values take precedence over auto-detected values
            locator_4char = locator[:4].upper() if len(locator) >= 4 else locator.upper()
            try:
                area = MaidenheadArea.objects.get(locator=locator_4char)
                enriched['locator_country'] = area.primary_country
                enriched['locator_alt_country'] = area.alternative_countries if area.alternative_countries else None
                enriched['locator_continent'] = area.continent
                enriched['locator_ambiguous'] = area.is_ambiguous
            except (MaidenheadArea.DoesNotExist, Exception):
                # No manual data for this locator, use auto-detected values if available
                if 'locator_country_auto' in enriched and 'locator_country' not in enriched:
                    enriched['locator_country'] = enriched['locator_country_auto']
                if 'locator_continent_auto' in enriched and 'locator_continent' not in enriched:
                    enriched['locator_continent'] = enriched['locator_continent_auto']

        # Look up callsign prefix using CallsignService
        if 'callsign' in enriched and enriched['callsign']:
            country_info = self.callsign_service.detect_country(enriched['callsign'])
            if country_info:
                enriched['callsign_country'] = country_info.get('country')
                enriched['callsign_continent'] = country_info.get('continent')

        return enriched
