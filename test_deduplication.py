#!/usr/bin/env python3
"""
Test Top DX deduplication logic without database.
"""


def test_deduplication_logic():
    """Test the deduplication logic used in get_top_dx."""
    print("Testing Top DX deduplication logic...")

    # Simulate database results (sorted by distance descending)
    mock_signals = [
        {"callsign": "UA0SU", "distance_km": 9387, "timestamp": "2026-04-28 20:00:00"},
        {"callsign": "DF1ABC", "distance_km": 8500, "timestamp": "2026-04-28 18:00:00"},
        {"callsign": "UA0SU", "distance_km": 8200, "timestamp": "2026-04-28 14:00:00"},  # Duplicate
        {"callsign": "W1XYZ", "distance_km": 7800, "timestamp": "2026-04-28 12:00:00"},
        {"callsign": "DF1ABC", "distance_km": 7500, "timestamp": "2026-04-28 10:00:00"},  # Duplicate
        {"callsign": "JA1ABC", "distance_km": 7200, "timestamp": "2026-04-28 08:00:00"},
        {"callsign": "UA0SU", "distance_km": 7000, "timestamp": "2026-04-28 06:00:00"},  # Duplicate
        {"callsign": "VK2XYZ", "distance_km": 6800, "timestamp": "2026-04-28 04:00:00"},
    ]

    # Apply deduplication logic (same as in StatisticsService.get_top_dx)
    limit = 20
    seen_callsigns = set()
    result = []

    for signal in mock_signals:
        if signal["callsign"] not in seen_callsigns:
            result.append(signal)
            seen_callsigns.add(signal["callsign"])

        if len(result) >= limit:
            break

    # Verify results
    print(f"  Original signals: {len(mock_signals)}")
    print(f"  Deduplicated signals: {len(result)}")

    # Check that each callsign appears only once
    callsigns_in_result = [s["callsign"] for s in result]
    unique_callsigns = set(callsigns_in_result)

    assert len(callsigns_in_result) == len(unique_callsigns), "Each callsign should appear only once"
    print(f"  Unique callsigns: {len(unique_callsigns)}")

    # Check that UA0SU has the highest distance (9387)
    ua0su = next((s for s in result if s["callsign"] == "UA0SU"), None)
    assert ua0su is not None, "UA0SU should be in results"
    assert ua0su["distance_km"] == 9387, f"UA0SU should have max distance 9387, got {ua0su['distance_km']}"
    print(f"  ✓ UA0SU has max distance: {ua0su['distance_km']} km")

    # Check that DF1ABC has the highest distance (8500, not 7500)
    df1abc = next((s for s in result if s["callsign"] == "DF1ABC"), None)
    assert df1abc is not None, "DF1ABC should be in results"
    assert df1abc["distance_km"] == 8500, f"DF1ABC should have max distance 8500, got {df1abc['distance_km']}"
    print(f"  ✓ DF1ABC has max distance: {df1abc['distance_km']} km")

    # Check that results are in order of distance
    distances = [s["distance_km"] for s in result]
    assert distances == sorted(distances, reverse=True), "Results should be ordered by distance descending"
    print(f"  ✓ Results ordered by distance: {distances}")

    print("✓ Top DX deduplication tests passed")


if __name__ == "__main__":
    try:
        test_deduplication_logic()
        print("\nAll deduplication tests passed! ✓")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import sys
        sys.exit(1)
