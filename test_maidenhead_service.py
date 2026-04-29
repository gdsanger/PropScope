#!/usr/bin/env python3
"""
Standalone test script for MaidenheadService.
Does not require Django or database connection.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apps.geo.services import MaidenheadService, InvalidMaidenheadLocatorError


def test_normalization():
    """Test locator normalization."""
    service = MaidenheadService()

    print("Testing normalization...")
    assert service.normalize_locator("jn68") == "JN68"
    assert service.normalize_locator(" jn68 ") == "JN68"
    assert service.normalize_locator("JN68") == "JN68"
    print("✓ Normalization tests passed")


def test_validation():
    """Test locator validation."""
    service = MaidenheadService()

    print("\nTesting validation...")

    # Valid locators
    valid_locators = ["JN68", "JN58", "JO21", "JO90", "MN72", "AA00", "RR99"]
    for locator in valid_locators:
        assert service.is_valid_locator(locator), f"Expected {locator} to be valid"

    # Valid 6-char locators
    assert service.is_valid_locator("JN68qv")
    assert service.is_valid_locator("JN58aa")

    # Invalid locators
    invalid_locators = ["ZZ99", "JN6", "1234", "JOXX", "", "SN68", "JZ68"]
    for locator in invalid_locators:
        assert not service.is_valid_locator(locator), f"Expected {locator} to be invalid"

    print("✓ Validation tests passed")


def test_coordinate_conversion():
    """Test locator to coordinate conversion."""
    service = MaidenheadService()

    print("\nTesting coordinate conversion...")

    # Test JN68 (Austria/Vienna area)
    lat, lon = service.locator_to_latlon("JN68")
    assert isinstance(lat, float)
    assert isinstance(lon, float)
    assert abs(lat - 48.5) < 0.1, f"Expected lat ~48.5, got {lat}"
    assert abs(lon - 13.0) < 0.1, f"Expected lon ~13.0, got {lon}"

    # Test JO21 (Netherlands/Belgium)
    lat, lon = service.locator_to_latlon("JO21")
    assert abs(lat - 51.5) < 0.1, f"Expected lat ~51.5, got {lat}"
    assert abs(lon - 5.0) < 0.1, f"Expected lon ~5.0, got {lon}"

    # Test MN72
    lat, lon = service.locator_to_latlon("MN72")
    assert abs(lat - 42.5) < 0.1, f"Expected lat ~42.5, got {lat}"
    assert abs(lon - 75.0) < 0.1, f"Expected lon ~75.0, got {lon}"

    # Test boundary locator AA00
    lat, lon = service.locator_to_latlon("AA00")
    assert abs(lat - (-89.5)) < 0.1, f"Expected lat ~-89.5, got {lat}"
    assert abs(lon - (-179.0)) < 0.1, f"Expected lon ~-179.0, got {lon}"

    # Test 6-char locator
    lat, lon = service.locator_to_latlon("JN68qv")
    assert 48.0 < lat < 49.0
    assert 12.0 < lon < 14.0

    # Test normalization during conversion
    lat1, lon1 = service.locator_to_latlon("JN68")
    lat2, lon2 = service.locator_to_latlon(" jn68 ")
    assert lat1 == lat2
    assert lon1 == lon2

    print("✓ Coordinate conversion tests passed")


def test_invalid_locators_raise_exception():
    """Test that invalid locators raise exceptions."""
    service = MaidenheadService()

    print("\nTesting exception handling...")

    invalid_locators = ["ZZ99", "JN6", "1234", "JOXX", ""]
    for locator in invalid_locators:
        try:
            service.locator_to_latlon(locator)
            assert False, f"Expected exception for {locator}"
        except InvalidMaidenheadLocatorError as e:
            assert locator in str(e) or "Invalid" in str(e)

    # Test that exception is a ValueError
    assert issubclass(InvalidMaidenheadLocatorError, ValueError)

    print("✓ Exception handling tests passed")


def test_distance_calculation():
    """Test distance calculation."""
    service = MaidenheadService()

    print("\nTesting distance calculation...")

    # Distance between same point should be ~0
    distance = service.distance_km(48.5, 9.0, 48.5, 9.0)
    assert abs(distance) < 0.1, f"Expected distance ~0, got {distance}"

    # Stuttgart to Munich (~190 km)
    distance = service.distance_km(48.78, 9.18, 48.14, 11.58)
    assert abs(distance - 190) < 10, f"Expected distance ~190 km, got {distance}"

    # Distance should be symmetric
    distance1 = service.distance_km(48.5, 9.0, 51.5, 6.0)
    distance2 = service.distance_km(51.5, 6.0, 48.5, 9.0)
    assert abs(distance1 - distance2) < 0.001

    # New York to London (~5570 km)
    distance = service.distance_km(40.7, -74.0, 51.5, -0.1)
    assert abs(distance - 5570) < 50, f"Expected distance ~5570 km, got {distance}"

    print("✓ Distance calculation tests passed")


def test_distance_between_locators():
    """Test distance between locators."""
    service = MaidenheadService()

    print("\nTesting distance between locators...")

    # Distance between same locator should be ~0
    distance = service.distance_between_locators("JN68", "JN68")
    assert abs(distance) < 0.1, f"Expected distance ~0, got {distance}"

    # Distance JN58 to JO21
    distance = service.distance_between_locators("JN58", "JO21")
    assert distance > 0
    assert distance < 1000

    # Distance should be symmetric
    distance1 = service.distance_between_locators("JN68", "JO21")
    distance2 = service.distance_between_locators("JO21", "JN68")
    assert abs(distance1 - distance2) < 0.001

    # Distance between 6-char locators in same square
    distance = service.distance_between_locators("JN68qv", "JN68qw")
    assert 0 < distance < 10

    # Distance with normalization
    distance1 = service.distance_between_locators("JN68", "JO21")
    distance2 = service.distance_between_locators(" jn68 ", " jo21 ")
    assert abs(distance1 - distance2) < 0.001

    # Invalid locators should raise exception
    try:
        service.distance_between_locators("ZZ99", "JN68")
        assert False, "Expected exception"
    except InvalidMaidenheadLocatorError:
        pass

    try:
        service.distance_between_locators("JN68", "ZZ99")
        assert False, "Expected exception"
    except InvalidMaidenheadLocatorError:
        pass

    print("✓ Distance between locators tests passed")


def test_service_is_stateless():
    """Test that service is stateless and reusable."""
    service1 = MaidenheadService()
    service2 = MaidenheadService()

    print("\nTesting service statefulness...")

    result1 = service1.locator_to_latlon("JN68")
    result2 = service2.locator_to_latlon("JN68")

    assert result1 == result2

    print("✓ Service statefulness tests passed")


def test_get_grid_map_url():
    """Test grid map URL generation."""
    service = MaidenheadService()

    print("\nTesting grid map URL generation...")

    # Test valid 4-char locator
    url = service.get_grid_map_url("JN68")
    assert url == "https://k7fry.com/grid/?qth=JN68", f"Expected specific URL, got {url}"

    # Test valid 6-char locator
    url = service.get_grid_map_url("JN68qv")
    assert url == "https://k7fry.com/grid/?qth=JN68QV", f"Expected specific URL, got {url}"

    # Test normalization (lowercase)
    url = service.get_grid_map_url("jn68")
    assert url == "https://k7fry.com/grid/?qth=JN68", f"Expected normalized URL, got {url}"

    # Test whitespace stripping
    url = service.get_grid_map_url(" jn68 ")
    assert url == "https://k7fry.com/grid/?qth=JN68", f"Expected normalized URL, got {url}"

    # Test multiple locators
    test_cases = [
        ("JN68", "https://k7fry.com/grid/?qth=JN68"),
        ("JO21", "https://k7fry.com/grid/?qth=JO21"),
        ("MN72", "https://k7fry.com/grid/?qth=MN72"),
        ("AA00", "https://k7fry.com/grid/?qth=AA00"),
        ("RR99", "https://k7fry.com/grid/?qth=RR99"),
    ]
    for locator, expected_url in test_cases:
        url = service.get_grid_map_url(locator)
        assert url == expected_url, f"For {locator}, expected {expected_url}, got {url}"

    # Test invalid locators raise exception
    invalid_locators = ["ZZ99", "JN6", "1234", "", "ABCD"]
    for locator in invalid_locators:
        try:
            service.get_grid_map_url(locator)
            assert False, f"Expected exception for {locator}"
        except InvalidMaidenheadLocatorError as e:
            assert "Invalid" in str(e) or locator in str(e)

    print("✓ Grid map URL generation tests passed")


def main():
    """Run all tests."""
    print("=" * 60)
    print("MaidenheadService Test Suite")
    print("=" * 60)

    try:
        test_normalization()
        test_validation()
        test_coordinate_conversion()
        test_invalid_locators_raise_exception()
        test_distance_calculation()
        test_distance_between_locators()
        test_service_is_stateless()
        test_get_grid_map_url()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
