"""
Example usage of GeoService for country and continent detection.

This example demonstrates how to use the GeoService to detect country
and continent from latitude/longitude coordinates using Natural Earth
shapefile data.
"""

from apps.geo.services import GeoService


def main():
    # Initialize GeoService (singleton pattern - geodata loaded once)
    geo_service = GeoService()

    # Example coordinates
    test_locations = [
        (51.5074, -0.1278, "London, UK"),
        (40.7128, -74.0060, "New York, USA"),
        (35.6762, 139.6503, "Tokyo, Japan"),
        (50.1109, 8.6821, "Frankfurt, Germany"),
        (-33.8688, 151.2093, "Sydney, Australia"),
        (0.0, -30.0, "Atlantic Ocean"),
    ]

    print("GeoService Example - Country & Continent Detection")
    print("=" * 60)

    for lat, lon, description in test_locations:
        country, continent = geo_service.get_country_continent(lat, lon)

        print(f"\n{description}")
        print(f"  Coordinates: {lat}, {lon}")
        print(f"  Country: {country or 'Not found (ocean/unmapped)'}")
        print(f"  Continent: {continent or 'Not found (ocean/unmapped)'}")

    # Performance example: caching
    print("\n" + "=" * 60)
    print("Performance Test - Repeated Lookups (cached)")
    print("=" * 60)

    import time
    lat, lon = 51.5074, -0.1278

    # First lookup (loads data and caches result)
    start = time.time()
    result1 = geo_service.get_country_continent(lat, lon)
    time1 = time.time() - start

    # Second lookup (uses cache)
    start = time.time()
    result2 = geo_service.get_country_continent(lat, lon)
    time2 = time.time() - start

    print(f"\nFirst lookup: {time1*1000:.2f}ms - Result: {result1}")
    print(f"Second lookup (cached): {time2*1000:.2f}ms - Result: {result2}")
    print(f"Speedup: {time1/time2:.1f}x faster")


if __name__ == '__main__':
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'propscope.settings')
    django.setup()

    main()
