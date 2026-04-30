"""
GeoService for determining country and continent from latitude/longitude.
Uses Natural Earth shapefile data for offline geographic lookups.
"""

import os
from typing import Optional, Tuple
from pathlib import Path


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
        try:
            import geopandas as gpd
        except ImportError:
            raise ImportError(
                "geopandas is required for GeoService. "
                "Install with: pip install geopandas"
            )

        # Path to shapefile relative to project root
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        shapefile_path = project_root / "geo" / "ne_110m_admin_0_countries.shp"

        if not shapefile_path.exists():
            raise FileNotFoundError(
                f"Natural Earth shapefile not found at: {shapefile_path}"
            )

        # Load shapefile
        GeoService._geodata = gpd.read_file(str(shapefile_path))

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
        # Check cache first
        cache_key = (lat, lon)
        if cache_key in GeoService._cache:
            return GeoService._cache[cache_key]

        # Validate coordinates
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            result = (None, None)
            GeoService._cache[cache_key] = result
            return result

        try:
            from shapely.geometry import Point
        except ImportError:
            raise ImportError(
                "shapely is required for GeoService. "
                "Install with: pip install shapely"
            )

        # Create point (IMPORTANT: lon, lat order for shapely!)
        point = Point(lon, lat)

        # Find matching country
        if GeoService._geodata is not None:
            # Check which polygon contains the point
            matches = GeoService._geodata[GeoService._geodata.contains(point)]

            if not matches.empty:
                # Get first match (for border regions)
                first_match = matches.iloc[0]

                # Extract country name and continent
                # Natural Earth uses 'NAME' for country and 'CONTINENT' for continent
                country = first_match.get('NAME', first_match.get('ADMIN'))
                continent = first_match.get('CONTINENT')

                result = (country, continent)
            else:
                # No match found (ocean, unmapped area)
                result = (None, None)
        else:
            # Geodata not loaded
            result = (None, None)

        # Cache result
        GeoService._cache[cache_key] = result
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
