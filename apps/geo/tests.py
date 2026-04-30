"""
Unit tests for MaidenheadService and GeoService.

Tests cover:
- Locator validation
- Locator normalization
- Coordinate calculation
- Distance calculation
- Country and continent detection
- Error handling
"""

from django.test import TestCase
from apps.geo.services import MaidenheadService, InvalidMaidenheadLocatorError, GeoService


class MaidenheadServiceTests(TestCase):
    """Test suite for MaidenheadService."""

    def setUp(self):
        """Initialize service instance for tests."""
        self.service = MaidenheadService()

    # ========== Normalization Tests ==========

    def test_normalize_locator_uppercase(self):
        """Test normalization converts to uppercase."""
        self.assertEqual(self.service.normalize_locator("jn68"), "JN68")

    def test_normalize_locator_strips_whitespace(self):
        """Test normalization strips leading and trailing whitespace."""
        self.assertEqual(self.service.normalize_locator(" jn68 "), "JN68")
        self.assertEqual(self.service.normalize_locator("\tjn68\n"), "JN68")

    def test_normalize_locator_already_normalized(self):
        """Test normalization of already normalized locator."""
        self.assertEqual(self.service.normalize_locator("JN68"), "JN68")

    # ========== Validation Tests ==========

    def test_valid_locator_4_char(self):
        """Test validation of valid 4-character locators."""
        valid_locators = [
            "JN68",
            "JN58",
            "JO21",
            "JO90",
            "MN72",
            "AA00",
            "RR99",
        ]
        for locator in valid_locators:
            with self.subTest(locator=locator):
                self.assertTrue(
                    self.service.is_valid_locator(locator),
                    f"Expected {locator} to be valid"
                )

    def test_valid_locator_6_char(self):
        """Test validation of valid 6-character locators."""
        valid_locators = [
            "JN68qv",
            "JN58aa",
            "JO21xx",
        ]
        for locator in valid_locators:
            with self.subTest(locator=locator):
                self.assertTrue(
                    self.service.is_valid_locator(locator),
                    f"Expected {locator} to be valid"
                )

    def test_invalid_locator_wrong_length(self):
        """Test validation rejects locators with wrong length."""
        invalid_locators = [
            "JN6",      # Too short
            "JN",       # Too short
            "JN68q",    # 5 chars
            "JN68qvx",  # 7 chars
            "",         # Empty
        ]
        for locator in invalid_locators:
            with self.subTest(locator=locator):
                self.assertFalse(
                    self.service.is_valid_locator(locator),
                    f"Expected {locator} to be invalid"
                )

    def test_invalid_locator_out_of_range_letters(self):
        """Test validation rejects locators with letters outside A-R range."""
        invalid_locators = [
            "ZZ99",  # Z is out of range (only A-R allowed)
            "SN68",  # S is out of range
            "JZ68",  # Z is out of range
            "JN68zz",  # Z is out of range for subsquare
        ]
        for locator in invalid_locators:
            with self.subTest(locator=locator):
                self.assertFalse(
                    self.service.is_valid_locator(locator),
                    f"Expected {locator} to be invalid"
                )

    def test_invalid_locator_wrong_format(self):
        """Test validation rejects locators with wrong format."""
        invalid_locators = [
            "1234",     # All digits
            "ABCD",     # All letters
            "JOXX",     # Letters where digits expected
            "12AB",     # Digits where letters expected
            "J123",     # Mixed format
        ]
        for locator in invalid_locators:
            with self.subTest(locator=locator):
                self.assertFalse(
                    self.service.is_valid_locator(locator),
                    f"Expected {locator} to be invalid"
                )

    def test_valid_locator_case_insensitive(self):
        """Test validation accepts lowercase locators."""
        self.assertTrue(self.service.is_valid_locator("jn68"))
        self.assertTrue(self.service.is_valid_locator("Jn68"))
        self.assertTrue(self.service.is_valid_locator("JN68"))

    # ========== Coordinate Conversion Tests ==========

    def test_locator_to_latlon_returns_tuple(self):
        """Test coordinate conversion returns tuple of floats."""
        lat, lon = self.service.locator_to_latlon("JN68")
        self.assertIsInstance(lat, float)
        self.assertIsInstance(lon, float)

    def test_locator_to_latlon_jn68(self):
        """Test coordinate conversion for JN68 (Austria/Vienna area)."""
        lat, lon = self.service.locator_to_latlon("JN68")
        # JN68 should be around 48.5°N, 13.0°E
        self.assertAlmostEqual(lat, 48.5, delta=0.1)
        self.assertAlmostEqual(lon, 13.0, delta=0.1)

    def test_locator_to_latlon_jo21(self):
        """Test coordinate conversion for JO21 (Netherlands/Belgium)."""
        lat, lon = self.service.locator_to_latlon("JO21")
        # JO21 should be around 51.5°N, 5.0°E
        self.assertAlmostEqual(lat, 51.5, delta=0.1)
        self.assertAlmostEqual(lon, 5.0, delta=0.1)

    def test_locator_to_latlon_mn72(self):
        """Test coordinate conversion for MN72."""
        lat, lon = self.service.locator_to_latlon("MN72")
        # MN72 should be around 42.5°N, 75.0°E
        self.assertAlmostEqual(lat, 42.5, delta=0.1)
        self.assertAlmostEqual(lon, 75.0, delta=0.1)

    def test_locator_to_latlon_6_char(self):
        """Test coordinate conversion for 6-character locator."""
        lat, lon = self.service.locator_to_latlon("JN68qv")
        # Should be more precise than 4-char
        self.assertIsInstance(lat, float)
        self.assertIsInstance(lon, float)
        # Should still be in JN68 area
        self.assertGreater(lat, 48.0)
        self.assertLess(lat, 49.0)

    def test_locator_to_latlon_center_point(self):
        """Test that conversion returns center of grid square."""
        # For a 4-char locator, the center should be offset by (1.0, 0.5)
        lat, lon = self.service.locator_to_latlon("AA00")
        # AA00 starts at -90°, -180° and spans 1° lat, 2° lon
        # Center should be at -89.5°, -179.0°
        self.assertAlmostEqual(lat, -89.5, places=1)
        self.assertAlmostEqual(lon, -179.0, places=1)

    def test_locator_to_latlon_invalid_raises_exception(self):
        """Test that invalid locators raise InvalidMaidenheadLocatorError."""
        invalid_locators = [
            "ZZ99",
            "JN6",
            "1234",
            "JOXX",
            "",
        ]
        for locator in invalid_locators:
            with self.subTest(locator=locator):
                with self.assertRaises(InvalidMaidenheadLocatorError):
                    self.service.locator_to_latlon(locator)

    def test_locator_to_latlon_normalizes_input(self):
        """Test that coordinate conversion normalizes input."""
        lat1, lon1 = self.service.locator_to_latlon("JN68")
        lat2, lon2 = self.service.locator_to_latlon(" jn68 ")
        self.assertEqual(lat1, lat2)
        self.assertEqual(lon1, lon2)

    # ========== Distance Calculation Tests ==========

    def test_distance_km_same_point(self):
        """Test distance between same point is zero."""
        distance = self.service.distance_km(48.5, 9.0, 48.5, 9.0)
        self.assertAlmostEqual(distance, 0.0, places=2)

    def test_distance_km_known_distance(self):
        """Test distance calculation with known coordinates."""
        # Stuttgart (48.78°N, 9.18°E) to Munich (48.14°N, 11.58°E)
        # Distance is approximately 190 km
        distance = self.service.distance_km(48.78, 9.18, 48.14, 11.58)
        self.assertAlmostEqual(distance, 190, delta=10)

    def test_distance_km_returns_positive(self):
        """Test that distance is always positive."""
        distance1 = self.service.distance_km(48.5, 9.0, 51.5, 6.0)
        distance2 = self.service.distance_km(51.5, 6.0, 48.5, 9.0)
        self.assertGreater(distance1, 0)
        self.assertEqual(distance1, distance2)

    def test_distance_km_across_globe(self):
        """Test distance calculation across large distances."""
        # New York to London (approximately 5570 km)
        distance = self.service.distance_km(40.7, -74.0, 51.5, -0.1)
        self.assertAlmostEqual(distance, 5570, delta=50)

    def test_distance_km_crossing_meridian(self):
        """Test distance calculation crossing prime meridian."""
        # Should handle longitude wraparound correctly
        distance = self.service.distance_km(0, -10, 0, 10)
        self.assertGreater(distance, 0)

    # ========== Distance Between Locators Tests ==========

    def test_distance_between_locators_same_locator(self):
        """Test distance between same locator is zero."""
        distance = self.service.distance_between_locators("JN68", "JN68")
        self.assertAlmostEqual(distance, 0.0, places=1)

    def test_distance_between_locators_jn58_to_jo21(self):
        """Test distance between JN58 and JO21."""
        distance = self.service.distance_between_locators("JN58", "JO21")
        # Should be several hundred kilometers
        self.assertGreater(distance, 0)
        self.assertLess(distance, 1000)

    def test_distance_between_locators_returns_positive(self):
        """Test that distance between locators is always positive."""
        distance = self.service.distance_between_locators("JN68", "JO21")
        self.assertGreater(distance, 0)

    def test_distance_between_locators_symmetric(self):
        """Test that distance calculation is symmetric."""
        distance1 = self.service.distance_between_locators("JN68", "JO21")
        distance2 = self.service.distance_between_locators("JO21", "JN68")
        self.assertAlmostEqual(distance1, distance2, places=5)

    def test_distance_between_locators_6_char(self):
        """Test distance between 6-character locators."""
        distance = self.service.distance_between_locators("JN68qv", "JN68qw")
        # Should be a small distance (within same 4-char square)
        self.assertGreater(distance, 0)
        self.assertLess(distance, 10)

    def test_distance_between_locators_mixed_length(self):
        """Test distance between 4-char and 6-char locators."""
        distance = self.service.distance_between_locators("JN68", "JN68qv")
        # Should be a small distance
        self.assertGreater(distance, 0)
        self.assertLess(distance, 5)

    def test_distance_between_locators_invalid_from_raises_exception(self):
        """Test that invalid from_locator raises exception."""
        with self.assertRaises(InvalidMaidenheadLocatorError):
            self.service.distance_between_locators("ZZ99", "JN68")

    def test_distance_between_locators_invalid_to_raises_exception(self):
        """Test that invalid to_locator raises exception."""
        with self.assertRaises(InvalidMaidenheadLocatorError):
            self.service.distance_between_locators("JN68", "ZZ99")

    def test_distance_between_locators_normalizes_input(self):
        """Test that distance calculation normalizes input."""
        distance1 = self.service.distance_between_locators("JN68", "JO21")
        distance2 = self.service.distance_between_locators(" jn68 ", " jo21 ")
        self.assertAlmostEqual(distance1, distance2, places=5)

    # ========== Edge Cases and Error Handling ==========

    def test_exception_is_value_error(self):
        """Test that InvalidMaidenheadLocatorError is a ValueError."""
        self.assertTrue(issubclass(InvalidMaidenheadLocatorError, ValueError))

    def test_exception_message_contains_locator(self):
        """Test that exception message contains the invalid locator."""
        try:
            self.service.locator_to_latlon("INVALID")
        except InvalidMaidenheadLocatorError as e:
            self.assertIn("INVALID", str(e))

    def test_service_is_stateless(self):
        """Test that service can be used multiple times without side effects."""
        service1 = MaidenheadService()
        service2 = MaidenheadService()

        result1 = service1.locator_to_latlon("JN68")
        result2 = service2.locator_to_latlon("JN68")

        self.assertEqual(result1, result2)

    def test_boundary_locators(self):
        """Test locators at boundaries of valid range."""
        # AA00 is minimum
        lat, lon = self.service.locator_to_latlon("AA00")
        self.assertGreater(lat, -90)
        self.assertGreater(lon, -180)

        # RR99 is maximum
        lat, lon = self.service.locator_to_latlon("RR99")
        self.assertLess(lat, 90)
        self.assertLess(lon, 180)

    # ========== Grid Map URL Tests ==========

    def test_get_grid_map_url_valid_4_char_locator(self):
        """Test grid map URL generation for valid 4-character locator."""
        url = self.service.get_grid_map_url("JN68")
        self.assertEqual(url, "https://k7fry.com/grid/?qth=JN68")

    def test_get_grid_map_url_valid_6_char_locator(self):
        """Test grid map URL generation for valid 6-character locator."""
        url = self.service.get_grid_map_url("JN68qv")
        self.assertEqual(url, "https://k7fry.com/grid/?qth=JN68QV")

    def test_get_grid_map_url_normalizes_lowercase(self):
        """Test grid map URL normalizes lowercase locator."""
        url = self.service.get_grid_map_url("jn68")
        self.assertEqual(url, "https://k7fry.com/grid/?qth=JN68")

    def test_get_grid_map_url_strips_whitespace(self):
        """Test grid map URL strips whitespace from locator."""
        url = self.service.get_grid_map_url(" jn68 ")
        self.assertEqual(url, "https://k7fry.com/grid/?qth=JN68")

    def test_get_grid_map_url_multiple_locators(self):
        """Test grid map URL generation for multiple different locators."""
        test_cases = [
            ("JN68", "https://k7fry.com/grid/?qth=JN68"),
            ("JO21", "https://k7fry.com/grid/?qth=JO21"),
            ("MN72", "https://k7fry.com/grid/?qth=MN72"),
            ("AA00", "https://k7fry.com/grid/?qth=AA00"),
            ("RR99", "https://k7fry.com/grid/?qth=RR99"),
        ]
        for locator, expected_url in test_cases:
            with self.subTest(locator=locator):
                url = self.service.get_grid_map_url(locator)
                self.assertEqual(url, expected_url)

    def test_get_grid_map_url_invalid_locator_raises_exception(self):
        """Test that invalid locators raise InvalidMaidenheadLocatorError."""
        invalid_locators = [
            "ZZ99",     # Out of range
            "JN6",      # Too short
            "1234",     # All digits
            "",         # Empty
            "ABCD",     # All letters
        ]
        for locator in invalid_locators:
            with self.subTest(locator=locator):
                with self.assertRaises(InvalidMaidenheadLocatorError):
                    self.service.get_grid_map_url(locator)

    def test_get_grid_map_url_exception_message_contains_locator(self):
        """Test that exception message contains the invalid locator."""
        try:
            self.service.get_grid_map_url("INVALID")
        except InvalidMaidenheadLocatorError as e:
            self.assertIn("INVALID", str(e))

class GeoServiceTests(TestCase):
    """Test suite for GeoService."""

    def setUp(self):
        """Initialize service instance for tests."""
        self.service = GeoService()
        # Clear cache before each test
        self.service.clear_cache()

    # ========== Country & Continent Detection Tests ==========

    def test_germany_detection(self):
        """Test detection of Germany from coordinates."""
        # Frankfurt, Germany
        lat, lon = 50.1109, 8.6821
        country, continent = self.service.get_country_continent(lat, lon)
        self.assertEqual(country, "Germany")
        self.assertEqual(continent, "Europe")

    def test_usa_detection(self):
        """Test detection of USA from coordinates."""
        # New York, USA
        lat, lon = 40.7128, -74.0060
        country, continent = self.service.get_country_continent(lat, lon)
        self.assertEqual(country, "United States of America")
        self.assertEqual(continent, "North America")

    def test_japan_detection(self):
        """Test detection of Japan from coordinates."""
        # Tokyo, Japan
        lat, lon = 35.6762, 139.6503
        country, continent = self.service.get_country_continent(lat, lon)
        self.assertEqual(country, "Japan")
        self.assertEqual(continent, "Asia")

    def test_uk_detection(self):
        """Test detection of UK from coordinates."""
        # London, UK
        lat, lon = 51.5074, -0.1278
        country, continent = self.service.get_country_continent(lat, lon)
        self.assertEqual(country, "United Kingdom")
        self.assertEqual(continent, "Europe")

    def test_australia_detection(self):
        """Test detection of Australia from coordinates."""
        # Sydney, Australia
        lat, lon = -33.8688, 151.2093
        country, continent = self.service.get_country_continent(lat, lon)
        self.assertEqual(country, "Australia")
        self.assertEqual(continent, "Oceania")

    def test_brazil_detection(self):
        """Test detection of Brazil from coordinates."""
        # Rio de Janeiro, Brazil
        lat, lon = -22.9068, -43.1729
        country, continent = self.service.get_country_continent(lat, lon)
        self.assertEqual(country, "Brazil")
        self.assertEqual(continent, "South America")

    def test_ocean_point_returns_none(self):
        """Test that points in ocean return None."""
        # Middle of Atlantic Ocean
        lat, lon = 0.0, -30.0
        country, continent = self.service.get_country_continent(lat, lon)
        self.assertIsNone(country)
        self.assertIsNone(continent)

    def test_pacific_ocean_returns_none(self):
        """Test that points in Pacific Ocean return None."""
        # Middle of Pacific Ocean
        lat, lon = 0.0, -150.0
        country, continent = self.service.get_country_continent(lat, lon)
        self.assertIsNone(country)
        self.assertIsNone(continent)

    # ========== Edge Cases ==========

    def test_invalid_latitude_high(self):
        """Test invalid latitude (too high) returns None."""
        lat, lon = 91.0, 0.0
        country, continent = self.service.get_country_continent(lat, lon)
        self.assertIsNone(country)
        self.assertIsNone(continent)

    def test_invalid_latitude_low(self):
        """Test invalid latitude (too low) returns None."""
        lat, lon = -91.0, 0.0
        country, continent = self.service.get_country_continent(lat, lon)
        self.assertIsNone(country)
        self.assertIsNone(continent)

    def test_invalid_longitude_high(self):
        """Test invalid longitude (too high) returns None."""
        lat, lon = 0.0, 181.0
        country, continent = self.service.get_country_continent(lat, lon)
        self.assertIsNone(country)
        self.assertIsNone(continent)

    def test_invalid_longitude_low(self):
        """Test invalid longitude (too low) returns None."""
        lat, lon = 0.0, -181.0
        country, continent = self.service.get_country_continent(lat, lon)
        self.assertIsNone(country)
        self.assertIsNone(continent)

    def test_north_pole(self):
        """Test detection at North Pole."""
        # North Pole - should return None as it's not in any country
        lat, lon = 90.0, 0.0
        country, continent = self.service.get_country_continent(lat, lon)
        # North Pole is not in any country
        self.assertIsNone(country)

    def test_south_pole(self):
        """Test detection at South Pole."""
        # South Pole - Antarctica
        lat, lon = -90.0, 0.0
        country, continent = self.service.get_country_continent(lat, lon)
        # South Pole may or may not be in a mapped region
        # Just check it doesn't crash
        self.assertIsInstance(country, (str, type(None)))
        self.assertIsInstance(continent, (str, type(None)))

    # ========== Caching Tests ==========

    def test_cache_stores_results(self):
        """Test that cache stores results for repeated queries."""
        lat, lon = 51.5074, -0.1278
        
        # First call
        result1 = self.service.get_country_continent(lat, lon)
        
        # Second call should use cache
        result2 = self.service.get_country_continent(lat, lon)
        
        self.assertEqual(result1, result2)
        # Verify cache contains the key
        self.assertIn((lat, lon), GeoService._cache)

    def test_clear_cache(self):
        """Test that clear_cache removes cached results."""
        lat, lon = 51.5074, -0.1278
        
        # Store in cache
        self.service.get_country_continent(lat, lon)
        self.assertGreater(len(GeoService._cache), 0)
        
        # Clear cache
        self.service.clear_cache()
        self.assertEqual(len(GeoService._cache), 0)

    # ========== Singleton Tests ==========

    def test_singleton_pattern(self):
        """Test that GeoService uses singleton pattern."""
        service1 = GeoService()
        service2 = GeoService()
        self.assertIs(service1, service2)

    def test_geodata_loaded_once(self):
        """Test that geodata is loaded only once."""
        service1 = GeoService()
        service2 = GeoService()
        self.assertIs(service1._geodata, service2._geodata)
