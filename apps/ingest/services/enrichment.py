"""
Enrichment service for signal data.
Adds computed fields based on callsign, locator, and station configuration.
"""

import logging
from typing import Optional, Dict, Any
from apps.geo.utils import maidenhead_to_latlon, haversine_distance
from apps.geo.models import MaidenheadArea
from apps.callsign.services import CallsignService
from apps.cq.services import BandService
from apps.geo.services import GeoService


logger = logging.getLogger(__name__)


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
            logger.debug("Initializing GeoService (lazy load)")
            try:
                self.geo_service = GeoService()
                logger.info("GeoService initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize GeoService: {e}", exc_info=True)
                raise
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
            logger.debug(f"Processing locator: {locator}")

            # Get coordinates from locator
            try:
                lat, lon = maidenhead_to_latlon(locator)
                enriched['locator_lat'] = lat
                enriched['locator_lon'] = lon
                logger.debug(f"Locator {locator} converted to lat={lat}, lon={lon}")

                # Calculate distance if station coordinates are available
                if self.station_lat is not None and self.station_lon is not None:
                    distance = haversine_distance(
                        self.station_lat, self.station_lon,
                        lat, lon
                    )
                    enriched['distance_km'] = distance
                    logger.debug(f"Distance calculated: {distance:.2f} km")

                    # Calculate azimuth (bearing) from station to signal
                    try:
                        from apps.geo.services import MaidenheadService
                        maidenhead_service = MaidenheadService()
                        azimuth = maidenhead_service.calculate_azimuth(
                            self.station_lat, self.station_lon,
                            lat, lon
                        )
                        enriched['azimuth_deg'] = azimuth
                        logger.debug(f"Azimuth calculated: {azimuth:.1f}°")
                    except Exception as e:
                        logger.warning(f"Failed to calculate azimuth: {e}")

                # Try GeoService for auto-detection first
                try:
                    logger.debug(f"Calling GeoService for locator {locator} (lat={lat}, lon={lon})")
                    geo_service = self._get_geo_service()
                    country_auto, continent_auto = geo_service.get_country_continent(lat, lon)

                    if country_auto:
                        enriched['locator_country_auto'] = country_auto
                        logger.info(f"GeoService detected country: {country_auto} for locator {locator}")
                    else:
                        logger.info(f"GeoService returned None for country (locator {locator})")

                    if continent_auto:
                        enriched['locator_continent_auto'] = continent_auto
                        logger.info(f"GeoService detected continent: {continent_auto} for locator {locator}")
                    else:
                        logger.info(f"GeoService returned None for continent (locator {locator})")

                except Exception as e:
                    # GeoService failed, continue without auto-detection
                    logger.error(f"GeoService failed for locator {locator}: {e}", exc_info=True)
                    pass

            except ValueError as e:
                # Invalid locator format
                logger.warning(f"Invalid locator format: {locator} - {e}")
                pass

            # Look up locator in MaidenheadArea table (manual override)
            # Manual values take precedence over auto-detected values
            locator_4char = locator[:4].upper() if len(locator) >= 4 else locator.upper()
            try:
                logger.debug(f"Looking up MaidenheadArea for {locator_4char}")
                area = MaidenheadArea.objects.get(locator=locator_4char)
                enriched['locator_country'] = area.primary_country
                enriched['locator_alt_country'] = area.alternative_countries if area.alternative_countries else None
                enriched['locator_continent'] = area.continent
                enriched['locator_ambiguous'] = area.is_ambiguous
                logger.info(f"MaidenheadArea found for {locator_4char}: country={area.primary_country}, continent={area.continent}")
            except (MaidenheadArea.DoesNotExist, Exception) as e:
                # No manual data for this locator, use auto-detected values if available
                if isinstance(e, MaidenheadArea.DoesNotExist):
                    logger.debug(f"No MaidenheadArea entry for {locator_4char}, using auto-detected values")
                else:
                    logger.error(f"Error looking up MaidenheadArea for {locator_4char}: {e}")

                if 'locator_country_auto' in enriched and 'locator_country' not in enriched:
                    enriched['locator_country'] = enriched['locator_country_auto']
                    logger.debug(f"Using auto-detected country: {enriched['locator_country_auto']}")
                if 'locator_continent_auto' in enriched and 'locator_continent' not in enriched:
                    enriched['locator_continent'] = enriched['locator_continent_auto']
                    logger.debug(f"Using auto-detected continent: {enriched['locator_continent_auto']}")

        # If no locator in the message, check KnownStation table
        elif 'callsign' in enriched and enriched['callsign']:
            callsign = enriched['callsign']
            logger.debug(f"No locator in message for {callsign}, checking KnownStation table")

            try:
                from apps.callsign.models import KnownStation
                # Look up normalized callsign
                normalized_callsign = self.callsign_service.normalize_callsign(callsign)
                known_station = KnownStation.objects.get(
                    callsign=normalized_callsign,
                    is_active=True
                )

                logger.info(f"Found KnownStation for {callsign}: {known_station.fixed_locator}")

                # Use fixed locator from KnownStation
                enriched['locator'] = known_station.fixed_locator
                enriched['locator_lat'] = known_station.fixed_latitude
                enriched['locator_lon'] = known_station.fixed_longitude

                if known_station.country:
                    enriched['locator_country'] = known_station.country
                if known_station.continent:
                    enriched['locator_continent'] = known_station.continent

                # Calculate distance if station coordinates are available
                if (self.station_lat is not None and self.station_lon is not None and
                    known_station.fixed_latitude is not None and known_station.fixed_longitude is not None):
                    distance = haversine_distance(
                        self.station_lat, self.station_lon,
                        known_station.fixed_latitude, known_station.fixed_longitude
                    )
                    enriched['distance_km'] = distance
                    logger.debug(f"Distance calculated from KnownStation: {distance:.2f} km")

                    # Calculate azimuth
                    try:
                        from apps.geo.services import MaidenheadService
                        maidenhead_service = MaidenheadService()
                        azimuth = maidenhead_service.calculate_azimuth(
                            self.station_lat, self.station_lon,
                            known_station.fixed_latitude, known_station.fixed_longitude
                        )
                        enriched['azimuth_deg'] = azimuth
                        logger.debug(f"Azimuth calculated from KnownStation: {azimuth:.1f}°")
                    except Exception as e:
                        logger.warning(f"Failed to calculate azimuth from KnownStation: {e}")

            except Exception as e:
                # KnownStation not found or error - not a problem
                if hasattr(e, '__class__') and e.__class__.__name__ == 'DoesNotExist':
                    logger.debug(f"No active KnownStation entry for {callsign}")
                else:
                    logger.debug(f"Error looking up KnownStation for {callsign}: {e}")

        # Look up callsign prefix using CallsignService
        if 'callsign' in enriched and enriched['callsign']:
            country_info = self.callsign_service.detect_country(enriched['callsign'])
            if country_info:
                enriched['callsign_country'] = country_info.get('country')
                enriched['callsign_continent'] = country_info.get('continent')

        return enriched
