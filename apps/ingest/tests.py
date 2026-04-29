"""
Tests for WSJT-X parser, enrichment, and importer services.
"""

from django.test import TestCase
from datetime import datetime, timezone
from apps.ingest.services.parser import WsjtxLineParser, ParsedWsjtxLine
from apps.geo.utils import maidenhead_to_latlon, haversine_distance, frequency_to_band
from apps.callsign.utils import extract_prefix, generate_qrz_url, normalize_callsign


class WsjtxLineParserTests(TestCase):
    """Tests for WSJT-X ALL.TXT line parser."""

    def setUp(self):
        self.parser = WsjtxLineParser()

    def test_parse_cq_line_with_locator(self):
        """Test parsing a CQ line with locator."""
        line = "260419_185200     7.074 Rx FT8    -19  0.3 1133 CQ EX7CQ MN72"
        parsed = self.parser.parse_line(line)

        self.assertIsNotNone(parsed)
        self.assertTrue(parsed.is_cq)
        self.assertEqual(parsed.callsign, "EX7CQ")
        self.assertEqual(parsed.locator, "MN72")
        self.assertEqual(parsed.frequency_mhz, 7.074)
        self.assertEqual(parsed.mode, "FT8")
        self.assertEqual(parsed.snr, -19)
        self.assertEqual(parsed.dt, 0.3)
        self.assertEqual(parsed.audio_frequency, 1133)

    def test_parse_cq_line_without_locator(self):
        """Test parsing a CQ line without locator."""
        line = "260419_185200     7.074 Rx FT8    -19  0.3 1133 CQ DL1ABC"
        parsed = self.parser.parse_line(line)

        self.assertIsNotNone(parsed)
        self.assertTrue(parsed.is_cq)
        self.assertEqual(parsed.callsign, "DL1ABC")
        self.assertIsNone(parsed.locator)

    def test_parse_non_cq_line(self):
        """Test parsing a non-CQ line."""
        line = "260419_185200     7.074 Rx FT8    -19  0.3 1133 DL1ABC K1XYZ RR73"
        parsed = self.parser.parse_line(line)

        self.assertIsNotNone(parsed)
        self.assertFalse(parsed.is_cq)

    def test_parse_tx_line_returns_none(self):
        """Test that TX lines are skipped."""
        line = "260419_185200     7.074 Tx FT8    -19  0.3 1133 CQ DL1ABC JN68"
        parsed = self.parser.parse_line(line)

        self.assertIsNone(parsed)

    def test_parse_invalid_line(self):
        """Test parsing an invalid line."""
        line = "invalid line format"
        parsed = self.parser.parse_line(line)

        self.assertIsNone(parsed)

    def test_parse_empty_line(self):
        """Test parsing an empty line."""
        line = ""
        parsed = self.parser.parse_line(line)

        self.assertIsNone(parsed)

    def test_is_cq_line(self):
        """Test quick CQ detection."""
        self.assertTrue(self.parser.is_cq_line("CQ DL1ABC JN68"))
        self.assertTrue(self.parser.is_cq_line("CQ"))
        self.assertFalse(self.parser.is_cq_line("DL1ABC K1XYZ RR73"))


class MaidenheadUtilsTests(TestCase):
    """Tests for Maidenhead locator utilities."""

    def test_maidenhead_to_latlon_4char(self):
        """Test conversion of 4-character locator."""
        lat, lon = maidenhead_to_latlon("JN68")
        # JN68 center should be around 48.5N, 8.0E
        self.assertAlmostEqual(lat, 48.5, delta=0.1)
        self.assertAlmostEqual(lon, 8.0, delta=0.1)

    def test_maidenhead_to_latlon_6char(self):
        """Test conversion of 6-character locator."""
        lat, lon = maidenhead_to_latlon("JN68qv")
        # More precise location
        self.assertGreater(lat, 48.0)
        self.assertLess(lat, 49.0)
        self.assertGreater(lon, 8.0)
        self.assertLess(lon, 9.0)

    def test_maidenhead_invalid_length(self):
        """Test that invalid length raises ValueError."""
        with self.assertRaises(ValueError):
            maidenhead_to_latlon("JN")

    def test_maidenhead_invalid_format(self):
        """Test that invalid format raises ValueError."""
        with self.assertRaises(ValueError):
            maidenhead_to_latlon("1234")

    def test_haversine_distance(self):
        """Test distance calculation between two points."""
        # JN68 to JO62 (Stuttgart to Berlin area, ~500km)
        lat1, lon1 = maidenhead_to_latlon("JN68")
        lat2, lon2 = maidenhead_to_latlon("JO62")
        distance = haversine_distance(lat1, lon1, lat2, lon2)

        # Should be around 500km
        self.assertGreater(distance, 400)
        self.assertLess(distance, 600)

    def test_haversine_same_point(self):
        """Test distance to same point is zero."""
        distance = haversine_distance(50.0, 10.0, 50.0, 10.0)
        self.assertAlmostEqual(distance, 0.0, delta=0.1)


class FrequencyBandTests(TestCase):
    """Tests for frequency to band conversion."""

    def test_frequency_to_band_20m(self):
        """Test 20m band detection."""
        self.assertEqual(frequency_to_band(14.074), "20m")

    def test_frequency_to_band_40m(self):
        """Test 40m band detection."""
        self.assertEqual(frequency_to_band(7.074), "40m")

    def test_frequency_to_band_80m(self):
        """Test 80m band detection."""
        self.assertEqual(frequency_to_band(3.573), "80m")

    def test_frequency_to_band_15m(self):
        """Test 15m band detection."""
        self.assertEqual(frequency_to_band(21.074), "15m")

    def test_frequency_to_band_unknown(self):
        """Test unknown frequency returns MHz format."""
        result = frequency_to_band(99.999)
        self.assertIn("99.999", result)
        self.assertIn("MHz", result)


class CallsignUtilsTests(TestCase):
    """Tests for callsign utilities."""

    def test_normalize_callsign(self):
        """Test callsign normalization."""
        self.assertEqual(normalize_callsign("DL1ABC/P"), "DL1ABC")
        self.assertEqual(normalize_callsign("K1XYZ/M"), "K1XYZ")
        self.assertEqual(normalize_callsign("DL1ABC"), "DL1ABC")

    def test_normalize_callsign_with_prefix(self):
        """Test callsign with prefix indicator."""
        self.assertEqual(normalize_callsign("DL/K1ABC"), "K1ABC")

    def test_extract_prefix(self):
        """Test prefix extraction."""
        self.assertEqual(extract_prefix("DL1ABC"), "DL")
        self.assertEqual(extract_prefix("K1XYZ"), "K")
        self.assertEqual(extract_prefix("VE3ABC"), "VE")
        self.assertEqual(extract_prefix("G4ABC"), "G")

    def test_generate_qrz_url(self):
        """Test QRZ URL generation."""
        url = generate_qrz_url("DL1ABC")
        self.assertEqual(url, "https://www.qrz.com/db/DL1ABC")

    def test_generate_qrz_url_with_suffix(self):
        """Test QRZ URL generation with suffix."""
        url = generate_qrz_url("DL1ABC/P")
        self.assertEqual(url, "https://www.qrz.com/db/DL1ABC")
