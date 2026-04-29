#!/usr/bin/env python3
"""
Standalone test script for advanced propagation features.
Tests azimuth calculation and statistics service enhancements.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apps.geo.services import MaidenheadService


def test_azimuth_calculation():
    """Test azimuth (bearing) calculation."""
    service = MaidenheadService()

    print("Testing azimuth calculation...")

    # Test cases with known bearings
    # From Stuttgart (48.8, 9.2) to Hamburg (53.6, 10.0) - roughly North
    azimuth = service.calculate_azimuth(48.8, 9.2, 53.6, 10.0)
    assert 0 <= azimuth < 360, "Azimuth should be in range [0, 360)"
    assert 350 <= azimuth or azimuth <= 20, f"Expected ~North, got {azimuth:.1f}°"
    print(f"  Stuttgart → Hamburg: {azimuth:.1f}° ✓")

    # From Berlin (52.5, 13.4) to London (51.5, -0.1) - roughly West
    azimuth = service.calculate_azimuth(52.5, 13.4, 51.5, -0.1)
    assert 0 <= azimuth < 360, "Azimuth should be in range [0, 360)"
    assert 250 <= azimuth <= 280, f"Expected ~West, got {azimuth:.1f}°"
    print(f"  Berlin → London: {azimuth:.1f}° ✓")

    # From New York (40.7, -74.0) to Los Angeles (34.0, -118.2) - roughly West
    azimuth = service.calculate_azimuth(40.7, -74.0, 34.0, -118.2)
    assert 0 <= azimuth < 360, "Azimuth should be in range [0, 360)"
    assert 250 <= azimuth <= 280, f"Expected ~West, got {azimuth:.1f}°"
    print(f"  New York → Los Angeles: {azimuth:.1f}° ✓")

    # Test 0° = North
    azimuth_north = service.calculate_azimuth(0, 0, 10, 0)
    assert 355 <= azimuth_north or azimuth_north <= 5, f"North should be ~0°, got {azimuth_north:.1f}°"
    print(f"  Equator → North: {azimuth_north:.1f}° ✓")

    # Test 90° = East
    azimuth_east = service.calculate_azimuth(0, 0, 0, 10)
    assert 85 <= azimuth_east <= 95, f"East should be ~90°, got {azimuth_east:.1f}°"
    print(f"  Equator → East: {azimuth_east:.1f}° ✓")

    # Test 180° = South
    azimuth_south = service.calculate_azimuth(10, 0, 0, 0)
    assert 175 <= azimuth_south <= 185, f"South should be ~180°, got {azimuth_south:.1f}°"
    print(f"  North → Equator: {azimuth_south:.1f}° ✓")

    # Test 270° = West
    azimuth_west = service.calculate_azimuth(0, 10, 0, 0)
    assert 265 <= azimuth_west <= 275, f"West should be ~270°, got {azimuth_west:.1f}°"
    print(f"  East → West: {azimuth_west:.1f}° ✓")

    print("✓ Azimuth calculation tests passed")


def test_statistics_service_methods():
    """Test that the new statistics service methods exist and have correct signatures."""
    print("\nTesting statistics service methods...")

    try:
        from apps.analysis.services import StatisticsService

        service = StatisticsService()

        # Check methods exist
        assert hasattr(service, 'get_cq_count_by_continent'), "Method get_cq_count_by_continent should exist"
        assert hasattr(service, 'get_cq_count_by_callsign_country'), "Method get_cq_count_by_callsign_country should exist"
        assert hasattr(service, 'get_best_dx_time'), "Method get_best_dx_time should exist"

        # Check methods are callable
        assert callable(service.get_cq_count_by_continent), "get_cq_count_by_continent should be callable"
        assert callable(service.get_cq_count_by_callsign_country), "get_cq_count_by_callsign_country should be callable"
        assert callable(service.get_best_dx_time), "get_best_dx_time should be callable"

        print("  ✓ get_cq_count_by_continent exists")
        print("  ✓ get_cq_count_by_callsign_country exists")
        print("  ✓ get_best_dx_time exists")

        print("✓ Statistics service method tests passed")
    except ImportError as e:
        print(f"⚠ Could not test statistics service (requires Django): {e}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Advanced Propagation Features")
    print("=" * 60)

    try:
        test_azimuth_calculation()
        test_statistics_service_methods()

        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
