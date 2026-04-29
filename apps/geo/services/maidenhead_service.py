"""
Core service for Maidenhead locator processing and distance calculations.

This service provides centralized functionality for:
- Validating Maidenhead locators
- Converting locators to coordinates
- Calculating distances between coordinates
- Calculating distances between locators
- Generating external map URLs for locators

The service is independent of database, UI, and import functionality.
"""

import re
import math
from typing import Tuple


class InvalidMaidenheadLocatorError(ValueError):
    """Raised when a Maidenhead locator is invalid or malformed."""
    pass


class MaidenheadService:
    """
    Service for Maidenhead locator processing and geographic calculations.

    Supports 4-character Maidenhead locators (e.g., JN68, JO21, MN72).
    Optional support for 6-character locators is included.
    """

    # Pattern for 4-character locator: [A-R][A-R][0-9][0-9]
    LOCATOR_4_PATTERN = re.compile(r'^[A-R]{2}[0-9]{2}$', re.IGNORECASE)

    # Pattern for 6-character locator: [A-R][A-R][0-9][0-9][A-X][A-X]
    LOCATOR_6_PATTERN = re.compile(r'^[A-R]{2}[0-9]{2}[A-X]{2}$', re.IGNORECASE)

    # Earth's radius in kilometers
    EARTH_RADIUS_KM = 6371.0

    def normalize_locator(self, locator: str) -> str:
        """
        Normalize a Maidenhead locator by stripping whitespace and converting to uppercase.

        Args:
            locator: Raw locator string

        Returns:
            Normalized locator string (uppercase, no whitespace)

        Example:
            >>> service.normalize_locator(" jn68 ")
            "JN68"
        """
        return locator.strip().upper()

    def is_valid_locator(self, locator: str) -> bool:
        """
        Check if a Maidenhead locator is valid.

        Validates 4-character and 6-character locators.

        Args:
            locator: Locator string to validate

        Returns:
            True if valid, False otherwise

        Examples:
            >>> service.is_valid_locator("JN68")
            True
            >>> service.is_valid_locator("ZZ99")
            False
            >>> service.is_valid_locator("JN6")
            False
        """
        normalized = self.normalize_locator(locator)

        # Check length
        if len(normalized) not in (4, 6):
            return False

        # Check format
        if len(normalized) == 4:
            return self.LOCATOR_4_PATTERN.match(normalized) is not None
        else:
            return self.LOCATOR_6_PATTERN.match(normalized) is not None

    def locator_to_latlon(self, locator: str) -> Tuple[float, float]:
        """
        Convert a Maidenhead locator to latitude/longitude coordinates.

        Returns the center point of the grid square.
        Supports 4-character (e.g., JN68) and 6-character (e.g., JN68qv) locators.

        Args:
            locator: Maidenhead locator string (4 or 6 characters)

        Returns:
            Tuple of (latitude, longitude) in degrees

        Raises:
            InvalidMaidenheadLocatorError: If locator format is invalid

        Examples:
            >>> lat, lon = service.locator_to_latlon("JN68")
            >>> isinstance(lat, float) and isinstance(lon, float)
            True
        """
        normalized = self.normalize_locator(locator)

        if not self.is_valid_locator(normalized):
            raise InvalidMaidenheadLocatorError(
                f"Invalid Maidenhead locator format: {locator}"
            )

        # Field (first two letters): 20° longitude, 10° latitude
        lon = (ord(normalized[0]) - ord('A')) * 20 - 180
        lat = (ord(normalized[1]) - ord('A')) * 10 - 90

        # Square (two digits): 2° longitude, 1° latitude
        lon += int(normalized[2]) * 2
        lat += int(normalized[3]) * 1

        if len(normalized) == 6:
            # Subsquare (two letters): 5' longitude, 2.5' latitude
            lon += (ord(normalized[4]) - ord('A')) * (2/24)
            lat += (ord(normalized[5]) - ord('A')) * (1/24)
            # Center of subsquare
            lon += (2/24) / 2
            lat += (1/24) / 2
        else:
            # Center of square (4-char locator)
            lon += 1.0
            lat += 0.5

        return (lat, lon)

    def distance_km(
        self,
        from_lat: float,
        from_lon: float,
        to_lat: float,
        to_lon: float,
    ) -> float:
        """
        Calculate the great circle distance between two points on Earth.

        Uses the Haversine formula for accurate distance calculation.

        Args:
            from_lat: Latitude of first point in degrees
            from_lon: Longitude of first point in degrees
            to_lat: Latitude of second point in degrees
            to_lon: Longitude of second point in degrees

        Returns:
            Distance in kilometers

        Example:
            >>> distance = service.distance_km(48.5, 9.0, 51.5, 6.0)
            >>> distance > 0
            True
        """
        # Convert to radians
        lat1_rad = math.radians(from_lat)
        lon1_rad = math.radians(from_lon)
        lat2_rad = math.radians(to_lat)
        lon2_rad = math.radians(to_lon)

        # Differences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        # Haversine formula
        a = (
            math.sin(dlat / 2)**2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = self.EARTH_RADIUS_KM * c
        return distance

    def distance_between_locators(
        self,
        from_locator: str,
        to_locator: str,
    ) -> float:
        """
        Calculate distance between two Maidenhead locators.

        Args:
            from_locator: First Maidenhead locator
            to_locator: Second Maidenhead locator

        Returns:
            Distance in kilometers

        Raises:
            InvalidMaidenheadLocatorError: If either locator is invalid

        Example:
            >>> distance = service.distance_between_locators("JN58", "JO21")
            >>> distance > 0
            True
        """
        from_lat, from_lon = self.locator_to_latlon(from_locator)
        to_lat, to_lon = self.locator_to_latlon(to_locator)

        return self.distance_km(from_lat, from_lon, to_lat, to_lon)

    def get_grid_map_url(self, locator: str) -> str:
        """
        Generate a k7fry.com grid map URL for a Maidenhead locator.

        The locator is normalized and validated before generating the URL.
        The URL can be used to display the locator on an interactive map.

        Args:
            locator: Maidenhead locator string (4 or 6 characters)

        Returns:
            URL string for k7fry.com grid map

        Raises:
            InvalidMaidenheadLocatorError: If locator format is invalid

        Examples:
            >>> url = service.get_grid_map_url("jn68")
            >>> url
            "https://k7fry.com/grid/?qth=JN68"

            >>> url = service.get_grid_map_url(" JO21 ")
            >>> url
            "https://k7fry.com/grid/?qth=JO21"
        """
        normalized = self.normalize_locator(locator)

        if not self.is_valid_locator(normalized):
            raise InvalidMaidenheadLocatorError(
                f"Invalid Maidenhead locator format: {locator}"
            )

        return f"https://k7fry.com/grid/?qth={normalized}"
