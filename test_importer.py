#!/usr/bin/env python
"""
Quick test script for the WSJT-X importer.
Tests parsing and enrichment without database operations.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'propscope.settings')
django.setup()

from apps.ingest.services.parser import WsjtxLineParser
from apps.ingest.services.enrichment import SignalEnricher

def main():
    print("="*60)
    print("WSJT-X Importer Test Script")
    print("="*60)

    # Test with sample file
    sample_file = os.path.join(os.path.dirname(__file__), 'sample_ALL.TXT')

    if not os.path.exists(sample_file):
        print(f"\nError: Sample file not found at {sample_file}")
        print("Please ensure sample_ALL.TXT exists in the project root.")
        sys.exit(1)

    print(f"\nReading from: {sample_file}")
    print()

    parser = WsjtxLineParser()
    enricher = SignalEnricher(
        station_lat=48.5,  # Example: JN68 area
        station_lon=13.0
    )

    with open(sample_file, 'r') as f:
        lines = f.readlines()

    print(f"Total lines in file: {len(lines)}")
    print()

    cq_count = 0
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue

        # Parse the line
        parsed = parser.parse_line(line)

        if parsed and parsed.is_cq:
            cq_count += 1
            print(f"Line {i}: CQ Call")
            print(f"  Callsign: {parsed.callsign}")
            print(f"  Locator:  {parsed.locator or 'N/A'}")
            print(f"  Band:     {parsed.mode} @ {parsed.frequency_mhz} MHz")
            print(f"  SNR:      {parsed.snr} dB")

            # Enrich the data
            signal_data = {
                'callsign': parsed.callsign,
                'locator': parsed.locator,
                'frequency_mhz': parsed.frequency_mhz,
            }
            enriched = enricher.enrich_signal_data(signal_data)

            print(f"  Band:     {enriched.get('band', 'N/A')}")
            print(f"  QRZ URL:  {enriched.get('qrz_url', 'N/A')}")

            if enriched.get('locator_lat'):
                print(f"  Location: {enriched['locator_lat']:.2f}°N, {enriched['locator_lon']:.2f}°E")

            if enriched.get('distance_km'):
                print(f"  Distance: {enriched['distance_km']:.0f} km")

            print()

    print("="*60)
    print(f"Summary: {cq_count} CQ calls found out of {len(lines)} lines")
    print("="*60)

if __name__ == '__main__':
    main()
