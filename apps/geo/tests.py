"""
Unit tests for MaidenheadService.

Tests cover:
- Locator validation
- Locator normalization
- Coordinate calculation
- Distance calculation
- Error handling
"""

from django.test import TestCase
from apps.geo.services import MaidenheadService, InvalidMaidenheadLocatorError


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
