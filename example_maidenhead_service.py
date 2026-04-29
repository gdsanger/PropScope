#!/usr/bin/env python3
"""
Example usage of MaidenheadService.

This demonstrates how to use the service for:
- Validating Maidenhead locators
- Converting locators to coordinates
- Calculating distances
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apps.geo.services import MaidenheadService, InvalidMaidenheadLocatorError


def main():
    # Create service instance
    service = MaidenheadService()

    print("=" * 60)
    print("MaidenheadService Usage Examples")
    print("=" * 60)

    # Example 1: Normalize and validate locators
    print("\n1. Normalization and Validation:")
    test_locators = ["jn68", "JO21", "MN72", "ZZ99", "INVALID"]
    for locator in test_locators:
        normalized = service.normalize_locator(locator)
        is_valid = service.is_valid_locator(normalized)
        print(f"   {locator:10s} → {normalized:10s} (valid: {is_valid})")

    # Example 2: Convert locators to coordinates
    print("\n2. Locator to Coordinates:")
    valid_locators = ["JN68", "JO21", "JN58"]
    for locator in valid_locators:
        lat, lon = service.locator_to_latlon(locator)
        print(f"   {locator}: {lat:6.2f}°N, {lon:6.2f}°E")

    # Example 3: Calculate distance between coordinates
    print("\n3. Distance Between Coordinates:")
    # Stuttgart to Munich
    distance = service.distance_km(48.78, 9.18, 48.14, 11.58)
    print(f"   Stuttgart to Munich: {distance:.1f} km")

    # Example 4: Calculate distance between locators
    print("\n4. Distance Between Locators:")
    pairs = [
        ("JN68", "JO21"),
        ("JN58", "JO21"),
        ("JN68", "JN68"),
    ]
    for loc1, loc2 in pairs:
        distance = service.distance_between_locators(loc1, loc2)
        print(f"   {loc1} ↔ {loc2}: {distance:.1f} km")

    # Example 5: Error handling
    print("\n5. Error Handling:")
    try:
        service.locator_to_latlon("ZZ99")
        print("   ERROR: Should have raised exception")
    except InvalidMaidenheadLocatorError as e:
        print(f"   ✓ Caught exception: {e}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
