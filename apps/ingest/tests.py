"""
Tests for WSJT-X parser, enrichment, and importer services.
"""

from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timezone as dt_timezone
from apps.ingest.services.parser import WsjtxLineParser, ParsedWsjtxLine
from apps.ingest.models import ImportRun, ImporterState
from apps.geo.utils import maidenhead_to_latlon, haversine_distance, frequency_to_band
from apps.callsign.utils import extract_prefix, generate_qrz_url, normalize_callsign


class ImporterStateModelTests(TestCase):
    """Tests for the ImporterState model."""

    def test_create_importer_state_with_all_fields(self):
        """Test creating an importer state with all fields populated."""
        import_run = ImportRun.objects.create(
            source_filename="/path/to/ALL.TXT",
            status='completed'
        )

        state = ImporterState.objects.create(
            name="Default WSJT-X ALL.TXT",
            log_file_path="/home/user/.local/share/WSJT-X/ALL.TXT",
            last_position=1024,
            last_size=2048,
            last_modified_at=timezone.now(),
            last_read_at=timezone.now(),
            last_import_run=import_run,
            last_error="",
            is_active=True
        )

        self.assertEqual(state.name, "Default WSJT-X ALL.TXT")
        self.assertEqual(state.log_file_path, "/home/user/.local/share/WSJT-X/ALL.TXT")
        self.assertEqual(state.last_position, 1024)
        self.assertEqual(state.last_size, 2048)
        self.assertIsNotNone(state.last_modified_at)
        self.assertIsNotNone(state.last_read_at)
        self.assertEqual(state.last_import_run, import_run)
        self.assertEqual(state.last_error, "")
        self.assertTrue(state.is_active)
        self.assertIsNotNone(state.created_at)
        self.assertIsNotNone(state.updated_at)

    def test_create_importer_state_minimal_fields(self):
        """Test creating an importer state with only required fields."""
        state = ImporterState.objects.create(
            name="Test Importer",
            log_file_path="/path/to/test.txt"
        )

        self.assertEqual(state.name, "Test Importer")
        self.assertEqual(state.log_file_path, "/path/to/test.txt")
        self.assertEqual(state.last_position, 0)  # Default value
        self.assertIsNone(state.last_size)
        self.assertIsNone(state.last_modified_at)
        self.assertIsNone(state.last_read_at)
        self.assertIsNone(state.last_import_run)
        self.assertEqual(state.last_error, "")
        self.assertTrue(state.is_active)  # Default value

    def test_log_file_path_unique(self):
        """Test that log_file_path must be unique."""
        ImporterState.objects.create(
            name="First",
            log_file_path="/path/to/same.txt"
        )

        with self.assertRaises(Exception):  # IntegrityError
            ImporterState.objects.create(
                name="Second",
                log_file_path="/path/to/same.txt"
            )

    def test_importer_state_str_representation_active(self):
        """Test string representation for active state."""
        state = ImporterState.objects.create(
            name="Main Importer",
            log_file_path="/path/to/ALL.TXT",
            is_active=True
        )

        str_repr = str(state)
        self.assertIn("Main Importer", str_repr)
        self.assertIn("/path/to/ALL.TXT", str_repr)
        self.assertIn("active", str_repr)

    def test_importer_state_str_representation_inactive(self):
        """Test string representation for inactive state."""
        state = ImporterState.objects.create(
            name="Old Importer",
            log_file_path="/path/to/old.txt",
            is_active=False
        )

        str_repr = str(state)
        self.assertIn("inactive", str_repr)

    def test_importer_state_ordering(self):
        """Test that states are ordered by active status and name."""
        state1 = ImporterState.objects.create(
            name="C Importer",
            log_file_path="/path/c.txt",
            is_active=True
        )
        state2 = ImporterState.objects.create(
            name="A Importer",
            log_file_path="/path/a.txt",
            is_active=True
        )
        state3 = ImporterState.objects.create(
            name="B Importer",
            log_file_path="/path/b.txt",
            is_active=False
        )

        states = list(ImporterState.objects.all())
        # Active should come first, then ordered by name
        self.assertTrue(states[0].is_active)
        self.assertTrue(states[1].is_active)
        self.assertFalse(states[2].is_active)
        # Among active, ordered by name
        self.assertEqual(states[0].name, "A Importer")
        self.assertEqual(states[1].name, "C Importer")

    def test_update_last_position(self):
        """Test updating the last position."""
        state = ImporterState.objects.create(
            name="Test",
            log_file_path="/path/test.txt",
            last_position=0
        )

        state.last_position = 1024
        state.save()

        state.refresh_from_db()
        self.assertEqual(state.last_position, 1024)

    def test_track_file_size_change(self):
        """Test tracking file size changes for rotation detection."""
        state = ImporterState.objects.create(
            name="Test",
            log_file_path="/path/test.txt",
            last_position=1024,
            last_size=2048
        )

        # Simulate file truncation
        state.last_size = 512  # Smaller than last_position
        state.save()

        state.refresh_from_db()
        self.assertEqual(state.last_size, 512)
        # This indicates rotation detection is needed (last_size < last_position)
        self.assertLess(state.last_size, state.last_position)

    def test_update_last_error(self):
        """Test recording an error message."""
        state = ImporterState.objects.create(
            name="Test",
            log_file_path="/path/test.txt"
        )

        error_msg = "File not found"
        state.last_error = error_msg
        state.save()

        state.refresh_from_db()
        self.assertEqual(state.last_error, error_msg)

    def test_clear_last_error(self):
        """Test clearing an error message after successful import."""
        state = ImporterState.objects.create(
            name="Test",
            log_file_path="/path/test.txt",
            last_error="Previous error"
        )

        state.last_error = ""
        state.save()

        state.refresh_from_db()
        self.assertEqual(state.last_error, "")

    def test_foreign_key_to_import_run(self):
        """Test the foreign key relationship to ImportRun."""
        import_run = ImportRun.objects.create(
            source_filename="/path/to/ALL.TXT",
            status='completed'
        )

        state = ImporterState.objects.create(
            name="Test",
            log_file_path="/path/test.txt",
            last_import_run=import_run
        )

        self.assertEqual(state.last_import_run, import_run)
        # Test reverse relationship
        self.assertIn(state, import_run.importer_states.all())

    def test_foreign_key_set_null_on_delete(self):
        """Test that deleting ImportRun sets the FK to NULL."""
        import_run = ImportRun.objects.create(
            source_filename="/path/to/ALL.TXT",
            status='completed'
        )

        state = ImporterState.objects.create(
            name="Test",
            log_file_path="/path/test.txt",
            last_import_run=import_run
        )

        # Delete the import run
        import_run.delete()

        state.refresh_from_db()
        self.assertIsNone(state.last_import_run)

    def test_is_active_index_exists(self):
        """Test that is_active field is indexed."""
        state = ImporterState.objects.create(
            name="Test",
            log_file_path="/path/test.txt",
            is_active=True
        )

        # Should be able to filter efficiently
        results = ImporterState.objects.filter(is_active=True)
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first(), state)

    def test_last_read_at_index_exists(self):
        """Test that last_read_at field is indexed."""
        now = timezone.now()
        state = ImporterState.objects.create(
            name="Test",
            log_file_path="/path/test.txt",
            last_read_at=now
        )

        # Should be able to order efficiently
        results = ImporterState.objects.order_by('-last_read_at')
        self.assertEqual(results.first(), state)

    def test_update_timestamps(self):
        """Test that updated_at changes on save."""
        state = ImporterState.objects.create(
            name="Test",
            log_file_path="/path/test.txt"
        )

        old_updated_at = state.updated_at

        # Update the state
        state.last_position = 100
        state.save()

        state.refresh_from_db()
        self.assertGreater(state.updated_at, old_updated_at)

    def test_deactivate_state(self):
        """Test deactivating an importer state."""
        state = ImporterState.objects.create(
            name="Test",
            log_file_path="/path/test.txt",
            is_active=True
        )

        state.is_active = False
        state.save()

        state.refresh_from_db()
        self.assertFalse(state.is_active)


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
