#!/usr/bin/env python3
"""
Example demonstrating the new grid map URL generation feature.

This example shows how to:
1. Generate grid map URLs from locators using MaidenheadService
2. Use the locator_map_url property on HeardSignal model (requires Django/DB)
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apps.geo.services import MaidenheadService, InvalidMaidenheadLocatorError


def example_service_usage():
    """Example: Using MaidenheadService directly."""
    print("=" * 70)
    print("Example 1: Using MaidenheadService.get_grid_map_url()")
    print("=" * 70)

    service = MaidenheadService()

    # Example locators from the issue
    locators = ["JN68", "JO21", "MN72"]

    for locator in locators:
        url = service.get_grid_map_url(locator)
        print(f"\nLocator: {locator}")
        print(f"Map URL: {url}")
        print(f"Open in browser: {url}")

    # Example with normalization
    print("\n" + "-" * 70)
    print("Normalization examples:")
    print("-" * 70)

    test_cases = [
        " jn68 ",     # lowercase with whitespace
        "jo21",       # lowercase
        "JN68qv",     # 6-character locator
    ]

    for locator in test_cases:
        url = service.get_grid_map_url(locator)
        normalized = service.normalize_locator(locator)
        print(f"\nInput:      '{locator}'")
        print(f"Normalized: '{normalized}'")
        print(f"Map URL:    {url}")

    # Example with invalid locator
    print("\n" + "-" * 70)
    print("Error handling example:")
    print("-" * 70)

    try:
        url = service.get_grid_map_url("ZZ99")  # Invalid locator
        print(f"URL: {url}")
    except InvalidMaidenheadLocatorError as e:
        print(f"\n✓ Invalid locator correctly rejected:")
        print(f"  Error: {e}")


def example_model_usage():
    """Example: Using HeardSignal.locator_map_url property (requires Django/DB)."""
    print("\n\n" + "=" * 70)
    print("Example 2: Using HeardSignal.locator_map_url property")
    print("=" * 70)
    print("""
This example requires Django and a database connection.
In your Django views or templates, you can use:

Python code:
    signal = HeardSignal.objects.get(id=123)
    if signal.locator_map_url:
        print(f"Map URL: {signal.locator_map_url}")

Django template:
    {% if signal.locator %}
    <a href="{{ signal.locator_map_url }}"
       target="_blank"
       rel="noopener noreferrer">
        {{ signal.locator }}
    </a>
    {% endif %}

Dashboard table example (Top DX):
    <table class="table">
        <thead>
            <tr>
                <th>Callsign</th>
                <th>Locator</th>
                <th>Distance</th>
                <th>SNR</th>
            </tr>
        </thead>
        <tbody>
        {% for signal in top_dx_signals %}
            <tr>
                <td>{{ signal.callsign }}</td>
                <td>
                    {% if signal.locator %}
                    <a href="{{ signal.locator_map_url }}"
                       target="_blank"
                       rel="noopener noreferrer">
                        {{ signal.locator }}
                    </a>
                    {% else %}
                    -
                    {% endif %}
                </td>
                <td>{{ signal.distance_km|floatformat:1 }} km</td>
                <td>{{ signal.snr }} dB</td>
            </tr>
        {% endfor %}
        </tbody>
    </table>

Top Locator table example:
    <table class="table">
        <thead>
            <tr>
                <th>Locator</th>
                <th>Count</th>
                <th>Max Distance</th>
            </tr>
        </thead>
        <tbody>
        {% for stat in locator_stats %}
            <tr>
                <td>
                    <a href="https://k7fry.com/grid/?qth={{ stat.locator }}"
                       target="_blank"
                       rel="noopener noreferrer">
                        {{ stat.locator }}
                    </a>
                </td>
                <td>{{ stat.count }}</td>
                <td>{{ stat.max_distance_km|floatformat:1 }} km</td>
            </tr>
        {% endfor %}
        </tbody>
    </table>
""")


def main():
    """Run examples."""
    try:
        example_service_usage()
        example_model_usage()

        print("\n" + "=" * 70)
        print("✓ All examples completed successfully")
        print("=" * 70)
        return 0
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
