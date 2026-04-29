"""
Utility functions for geographic calculations and Maidenhead locator conversions.
"""

import math
from typing import Tuple, Optional


def maidenhead_to_latlon(locator: str) -> Tuple[float, float]:
    """
    Convert a Maidenhead locator to latitude/longitude coordinates.
    Returns the center point of the grid square.

    Supports 4-character (e.g., JN68) and 6-character (e.g., JN68qv) locators.

    Args:
        locator: Maidenhead locator string (4 or 6 characters)

    Returns:
        Tuple of (latitude, longitude) in degrees

    Raises:
        ValueError: If locator format is invalid
    """
    locator = locator.upper().strip()

    if len(locator) not in (4, 6):
        raise ValueError(f"Locator must be 4 or 6 characters, got: {locator}")

    # Validate format
    if not (locator[0:2].isalpha() and locator[2:4].isdigit()):
        raise ValueError(f"Invalid locator format: {locator}")

    if len(locator) == 6 and not locator[4:6].isalpha():
        raise ValueError(f"Invalid locator format: {locator}")

    # Field (first two letters): 20° longitude, 10° latitude
    lon = (ord(locator[0]) - ord('A')) * 20 - 180
    lat = (ord(locator[1]) - ord('A')) * 10 - 90

    # Square (two digits): 2° longitude, 1° latitude
    lon += int(locator[2]) * 2
    lat += int(locator[3]) * 1

    if len(locator) == 6:
        # Subsquare (two letters): 5' longitude, 2.5' latitude
        lon += (ord(locator[4]) - ord('A')) * (2/24)
        lat += (ord(locator[5]) - ord('A')) * (1/24)
        # Center of subsquare
        lon += (2/24) / 2
        lat += (1/24) / 2
    else:
        # Center of square (4-char locator)
        lon += 1
        lat += 0.5

    return (lat, lon)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth.
    Uses the Haversine formula.

    Args:
        lat1, lon1: Coordinates of first point in degrees
        lat2, lon2: Coordinates of second point in degrees

    Returns:
        Distance in kilometers
    """
    # Earth's radius in kilometers
    R = 6371.0

    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance


def calculate_distance_from_locators(locator1: str, locator2: str) -> Optional[float]:
    """
    Calculate distance between two Maidenhead locators.

    Args:
        locator1: First Maidenhead locator
        locator2: Second Maidenhead locator

    Returns:
        Distance in kilometers, or None if either locator is invalid
    """
    try:
        lat1, lon1 = maidenhead_to_latlon(locator1)
        lat2, lon2 = maidenhead_to_latlon(locator2)
        return haversine_distance(lat1, lon1, lat2, lon2)
    except (ValueError, TypeError):
        return None


def frequency_to_band(frequency_mhz: float) -> str:
    """
    Convert frequency in MHz to amateur radio band designation.

    DEPRECATED: This function now uses the BandDefinition database table.
    For new code, use BandService directly instead.

    Args:
        frequency_mhz: Frequency in MHz

    Returns:
        Band designation (e.g., "20m", "40m", "160m")
    """
    # Use BandService for database-driven band lookup
    from apps.cq.services import BandService

    service = BandService()
    band_name = service.get_band_name(frequency_mhz)

    # Return band name if found, otherwise frequency in MHz format
    if band_name:
        return band_name
    else:
        return f"{frequency_mhz:.3f}MHz"
