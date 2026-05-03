"""
Service for calculating the greyline (day/night terminator) on Earth.

The greyline represents the boundary between day and night on Earth's surface,
which is crucial for understanding radio propagation conditions, especially
for DX (long-distance) communications.
"""

import math
from datetime import datetime
from typing import List, Tuple


class GreylineService:
    """
    Service for calculating the day/night terminator (greyline) coordinates.

    The greyline is the line on Earth's surface where the sun is at the horizon,
    marking the boundary between day and night. Radio propagation is often
    enhanced along this line due to D-layer absorption characteristics.
    """

    EARTH_RADIUS_KM = 6371.0

    @staticmethod
    def calculate_solar_declination(day_of_year: int) -> float:
        """
        Calculate the solar declination for a given day of the year.

        Args:
            day_of_year: Day of year (1-366)

        Returns:
            Solar declination in degrees
        """
        # Simplified formula for solar declination
        # Maximum tilt is approximately 23.44 degrees
        angle = 2 * math.pi * (day_of_year - 81) / 365
        declination = 23.44 * math.sin(angle)
        return declination

    @staticmethod
    def calculate_solar_hour_angle(longitude: float, utc_time: datetime) -> float:
        """
        Calculate the solar hour angle for a given longitude and UTC time.

        Args:
            longitude: Longitude in degrees
            utc_time: UTC datetime

        Returns:
            Solar hour angle in degrees
        """
        # Calculate the fraction of the day
        hours = utc_time.hour + utc_time.minute / 60.0 + utc_time.second / 3600.0

        # Solar noon is at 12:00 UTC at 0° longitude
        # The sun moves 360° in 24 hours = 15° per hour
        solar_longitude = (hours - 12) * 15

        # Hour angle is the difference between the solar longitude and the point's longitude
        hour_angle = solar_longitude - longitude

        return hour_angle

    def calculate_greyline(self, timestamp: datetime = None, resolution: int = 360) -> List[Tuple[float, float]]:
        """
        Calculate the greyline (day/night terminator) coordinates.

        Args:
            timestamp: UTC datetime for calculation (default: current time)
            resolution: Number of points to calculate (default: 360)

        Returns:
            List of (latitude, longitude) tuples representing the greyline
        """
        if timestamp is None:
            from datetime import timezone
            timestamp = datetime.now(timezone.utc)

        # Calculate day of year
        day_of_year = timestamp.timetuple().tm_yday

        # Calculate solar declination
        declination = self.calculate_solar_declination(day_of_year)
        declination_rad = math.radians(declination)

        # Calculate hour offset from midnight UTC
        hours = timestamp.hour + timestamp.minute / 60.0 + timestamp.second / 3600.0

        # Calculate the subsolar point (where sun is directly overhead)
        # The sun moves 15 degrees per hour (360°/24h)
        subsolar_longitude = (hours - 12) * 15

        # Generate points along the terminator
        coordinates = []

        for i in range(resolution + 1):
            # Longitude ranges from -180 to 180
            lon = -180 + (360 * i / resolution)

            # Calculate the latitude where the sun is at the horizon
            # This is based on the solar declination and the longitude difference
            # from the subsolar point

            lon_diff = lon - subsolar_longitude
            # Normalize to -180 to 180
            while lon_diff > 180:
                lon_diff -= 360
            while lon_diff < -180:
                lon_diff += 360

            lon_diff_rad = math.radians(lon_diff)

            # At the terminator, the solar zenith angle is 90°
            # This gives us the equation: sin(lat) = -tan(declination) * cos(lon_diff)
            # However, this only works when |tan(decl) * cos(lon_diff)| <= 1

            tan_dec = math.tan(declination_rad)
            cos_lon_diff = math.cos(lon_diff_rad)
            sin_lat = -tan_dec * cos_lon_diff

            # Check if the calculation is valid
            if abs(sin_lat) <= 1.0:
                lat = math.degrees(math.asin(sin_lat))
                coordinates.append((lat, lon))
            else:
                # During polar day/night, there's no terminator at some longitudes
                # In these cases, we skip this point or use the pole
                if sin_lat > 1.0:
                    coordinates.append((90.0, lon))
                else:
                    coordinates.append((-90.0, lon))

        return coordinates

    def calculate_greyline_with_twilight(
        self,
        timestamp: datetime = None,
        resolution: int = 360,
        twilight_angle: float = 6.0
    ) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
        """
        Calculate both the greyline and civil twilight boundary.

        Civil twilight occurs when the sun is between 0° and 6° below the horizon.

        Args:
            timestamp: UTC datetime for calculation (default: current time)
            resolution: Number of points to calculate (default: 360)
            twilight_angle: Degrees below horizon for twilight (default: 6.0 for civil twilight)

        Returns:
            Tuple of (greyline_coords, twilight_coords)
        """
        greyline = self.calculate_greyline(timestamp, resolution)

        # For simplicity, we'll return the same greyline for now
        # A more sophisticated implementation could calculate the actual twilight zone
        return (greyline, greyline)
