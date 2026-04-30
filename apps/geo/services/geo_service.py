"""
GeoService for determining country and continent from latitude/longitude.
Uses Natural Earth shapefile data for offline geographic lookups.
"""

import os
import logging
from typing import Optional, Tuple
from pathlib import Path


logger = logging.getLogger(__name__)


class GeoService:
    """
    Service for determining country and continent from geographic coordinates.

    Uses Natural Earth shapefile data (ne_110m_admin_0_countries.shp) for
    offline geographic lookups without external API calls.

    The geodata is loaded once and cached in memory for performance.
    """

    _instance = None
    _geodata = None
    _cache = {}

    def __new__(cls):
        """Singleton pattern to ensure geodata is loaded only once."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the service and load geodata if not already loaded."""
        if GeoService._geodata is None:
            self._load_geodata()

    def _load_geodata(self):
        """
        Load Natural Earth shapefile data into memory.

        Raises:
            FileNotFoundError: If shapefile is not found
            ImportError: If geopandas is not installed
        """
        logger.info("Starting GeoService geodata loading process")

        try:
            import geopandas as gpd
            logger.debug("geopandas import successful")
        except ImportError as e:
            logger.error(f"Failed to import geopandas: {e}")
            raise ImportError(
                "geopandas is required for GeoService. "
                "Install with: pip install geopandas"
            )

        # Path to shapefile relative to project root
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        shapefile_path = project_root / "geo" / "ne_110m_admin_0_countries.shp"

        logger.debug(f"Project root: {project_root}")
        logger.debug(f"Shapefile path: {shapefile_path}")

        if not shapefile_path.exists():
            logger.error(f"Shapefile not found at: {shapefile_path}")
            raise FileNotFoundError(
                f"Natural Earth shapefile not found at: {shapefile_path}"
            )

        # Load shapefile
        logger.info(f"Loading shapefile from: {shapefile_path}")
        try:
            GeoService._geodata = gpd.read_file(str(shapefile_path))
            logger.info(f"Shapefile loaded successfully. Records: {len(GeoService._geodata)}")
            logger.debug(f"Shapefile columns: {list(GeoService._geodata.columns)}")
        except Exception as e:
            logger.error(f"Failed to load shapefile: {e}", exc_info=True)
            raise

    def get_country_continent(
        self,
        lat: float,
        lon: float
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Determine country and continent from latitude/longitude coordinates.

        Args:
            lat: Latitude in decimal degrees (-90 to 90)
            lon: Longitude in decimal degrees (-180 to 180)

        Returns:
            Tuple of (country, continent) or (None, None) if no match found

        Examples:
            >>> service = GeoService()
            >>> service.get_country_continent(51.5074, -0.1278)
            ('United Kingdom', 'Europe')

            >>> service.get_country_continent(35.6762, 139.6503)
            ('Japan', 'Asia')

            >>> service.get_country_continent(0.0, 0.0)  # Ocean
            (None, None)

        Note:
            - Points in oceans or unmapped areas return (None, None)
            - Border regions return the first matching country
            - Results are cached for performance
        """
        logger.debug(f"get_country_continent called with lat={lat}, lon={lon}")

        # Check cache first
        cache_key = (lat, lon)
        if cache_key in GeoService._cache:
            result = GeoService._cache[cache_key]
            logger.debug(f"Cache HIT for ({lat}, {lon}): {result}")
            return result

        logger.debug(f"Cache MISS for ({lat}, {lon})")

        # Validate coordinates
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            logger.warning(f"Invalid coordinates: lat={lat}, lon={lon}")
            result = (None, None)
            GeoService._cache[cache_key] = result
            return result

        try:
            from shapely.geometry import Point
            logger.debug("shapely.geometry.Point import successful")
        except ImportError as e:
            logger.error(f"Failed to import shapely: {e}")
            raise ImportError(
                "shapely is required for GeoService. "
                "Install with: pip install shapely"
            )

        # Create point (IMPORTANT: lon, lat order for shapely!)
        point = Point(lon, lat)
        logger.debug(f"Created Point({lon}, {lat})")

        # Find matching country
        if GeoService._geodata is not None:
            logger.debug(f"Searching in {len(GeoService._geodata)} polygons")
            # Check which polygon contains the point
            matches = GeoService._geodata[GeoService._geodata.contains(point)]

            if not matches.empty:
                # Get first match (for border regions)
                first_match = matches.iloc[0]

                # Extract country name and continent
                # Natural Earth uses 'NAME' for country and 'CONTINENT' for continent
                country = first_match.get('NAME', first_match.get('ADMIN'))
                continent = first_match.get('CONTINENT')

                logger.info(f"Match FOUND for ({lat}, {lon}): country={country}, continent={continent}")
                result = (country, continent)
            else:
                # No match found (ocean, unmapped area)
                logger.info(f"No match for ({lat}, {lon}) - likely ocean or unmapped area")
                result = (None, None)
        else:
            # Geodata not loaded
            logger.error("Geodata is None - shapefile not loaded properly")
            result = (None, None)

        # Cache result
        GeoService._cache[cache_key] = result
        logger.debug(f"Cached result for ({lat}, {lon}): {result}")
        return result

    def clear_cache(self):
        """Clear the coordinate cache. Useful for testing or memory management."""
        GeoService._cache.clear()

    @classmethod
    def reload_geodata(cls):
        """
        Force reload of geodata from disk.
        Useful for testing or if shapefile is updated.
        """
        cls._geodata = None
        cls._cache.clear()
        if cls._instance:
            cls._instance._load_geodata()
