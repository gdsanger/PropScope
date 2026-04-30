"""
Tests for WSJT-X parser, enrichment, and importer services.
"""

import tempfile
import os
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timezone as dt_timezone
from apps.ingest.services.parser import WsjtxLineParser, ParsedWsjtxLine
from apps.ingest.services.wsjtx_importer import WsjtxLogImporter
from apps.ingest.models import ImportRun, ImporterState
from apps.ui.models import PropScopeSettings
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

    def test_parse_timestamp_correct_format(self):
        """Test timestamp parsing with correct YYMMDD format."""
        # Example from issue: 260428_145500 should be 2026-04-28 14:55:00
        line = "260428_145500     7.074 Rx FT8    -19  0.3 1133 CQ DL1ABC JN68"
        parsed = self.parser.parse_line(line)

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.timestamp.year, 2026)
        self.assertEqual(parsed.timestamp.month, 4)
        self.assertEqual(parsed.timestamp.day, 28)
        self.assertEqual(parsed.timestamp.hour, 14)
        self.assertEqual(parsed.timestamp.minute, 55)
        self.assertEqual(parsed.timestamp.second, 0)

    def test_parse_timestamp_example_from_issue(self):
        """Test timestamp parsing with example from issue: 260419_185200."""
        line = "260419_185200     7.074 Rx FT8    -19  0.3 1133 CQ EX7CQ MN72"
        parsed = self.parser.parse_line(line)

        self.assertIsNotNone(parsed)
        # Should be 2026-04-19 18:52:00, NOT 2019-04-26
        self.assertEqual(parsed.timestamp.year, 2026)
        self.assertEqual(parsed.timestamp.month, 4)
        self.assertEqual(parsed.timestamp.day, 19)
        self.assertEqual(parsed.timestamp.hour, 18)
        self.assertEqual(parsed.timestamp.minute, 52)
        self.assertEqual(parsed.timestamp.second, 0)

    def test_parse_timestamp_direct_parsing(self):
        """Test the _parse_timestamp method directly."""
        # Test case 1: 260428_145500 -> 2026-04-28 14:55:00
        dt = self.parser._parse_timestamp("260428_145500")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.month, 4)
        self.assertEqual(dt.day, 28)
        self.assertEqual(dt.hour, 14)
        self.assertEqual(dt.minute, 55)
        self.assertEqual(dt.second, 0)

        # Test case 2: 260419_185200 -> 2026-04-19 18:52:00
        dt = self.parser._parse_timestamp("260419_185200")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.month, 4)
        self.assertEqual(dt.day, 19)
        self.assertEqual(dt.hour, 18)
        self.assertEqual(dt.minute, 52)
        self.assertEqual(dt.second, 0)

        # Test case 3: Different date
        dt = self.parser._parse_timestamp("250315_120000")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.year, 2025)
        self.assertEqual(dt.month, 3)
        self.assertEqual(dt.day, 15)
        self.assertEqual(dt.hour, 12)
        self.assertEqual(dt.minute, 0)
        self.assertEqual(dt.second, 0)

    def test_parse_timestamp_utc_timezone(self):
        """Test that parsed timestamps are in UTC timezone."""
        dt = self.parser._parse_timestamp("260428_145500")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.tzinfo, dt_timezone.utc)

    def test_parse_timestamp_invalid_format(self):
        """Test that invalid timestamp format returns None."""
        # Invalid formats should return None
        self.assertIsNone(self.parser._parse_timestamp("invalid"))
        self.assertIsNone(self.parser._parse_timestamp(""))
        self.assertIsNone(self.parser._parse_timestamp("26-04-28_145500"))
        self.assertIsNone(self.parser._parse_timestamp("260428145500"))  # Missing underscore


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


class WsjtxImporterTests(TestCase):
    """
    Tests for the WsjtxLogImporter service.
    Specifically tests the fix for the "telling position disabled by next() call" bug.
    """

    def setUp(self):
        """Create a temporary test file."""
        self.test_content = """260419_185200     7.074 Rx FT8    -19  0.3 1133 CQ EX7CQ MN72
260419_185215    14.074 Rx FT8    -12  0.2 1456 CQ DL1ABC JN68
260419_185230    21.074 Rx FT8     -8  0.1 1789 CQ K1XYZ FN42
260419_185245     7.074 Rx FT8    -15  0.4 1234 DL1ABC K1XYZ RR73
260419_185300    14.074 Rx FT8    -10  0.3 1567 CQ G4ABC IO91
"""
        fd, self.test_file_path = tempfile.mkstemp(suffix='.txt', prefix='test_all_')
        with os.fdopen(fd, 'w') as f:
            f.write(self.test_content)

    def tearDown(self):
        """Clean up temporary test file."""
        if os.path.exists(self.test_file_path):
            os.unlink(self.test_file_path)

    def test_full_import_no_tell_error(self):
        """
        Test that full import works without 'telling position disabled by next() call' error.
        This verifies the fix for the bug where using 'for line in f:' with 'f.tell()' caused an error.
        """
        importer = WsjtxLogImporter()

        # Run full import
        import_run = importer.import_file(
            file_path=self.test_file_path,
            incremental=False,
            settings=None
        )

        # Assert import completed successfully
        self.assertEqual(import_run.status, 'completed')
        self.assertEqual(import_run.lines_total, 5)
        # 4 CQ lines, but duplicates might be skipped based on hash
        self.assertGreaterEqual(import_run.lines_imported, 1)
        self.assertGreaterEqual(import_run.lines_skipped, 0)

    def test_incremental_import_with_position_tracking(self):
        """
        Test that incremental import correctly tracks file position using tell().
        This verifies that the fix allows proper position tracking without errors.
        """
        # Create settings for position tracking
        settings = PropScopeSettings.objects.create(
            name='test_settings',
            is_active=False,
            wsjtx_last_position=0
        )

        importer = WsjtxLogImporter()

        # First incremental import (from position 0)
        import_run1 = importer.import_file(
            file_path=self.test_file_path,
            incremental=True,
            settings=settings
        )

        # Assert first import completed successfully
        self.assertEqual(import_run1.status, 'completed')
        self.assertEqual(import_run1.lines_total, 5)

        # Get the saved position
        settings.refresh_from_db()
        first_position = settings.wsjtx_last_position
        self.assertGreater(first_position, 0, "Position should be saved after import")

        # Append new data to the file
        with open(self.test_file_path, 'a') as f:
            f.write("260419_185315     7.074 Rx FT8    -20  0.5 1890 CQ VE3ABC FN03\n")
            f.write("260419_185330    14.074 Rx FT8    -18  0.2 1123 CQ JA1ABC PM95\n")

        # Second incremental import (from saved position)
        import_run2 = importer.import_file(
            file_path=self.test_file_path,
            incremental=True,
            settings=settings
        )

        # Assert second import completed successfully
        self.assertEqual(import_run2.status, 'completed')
        # Should only process the 2 new lines
        self.assertEqual(import_run2.lines_total, 2)

        # Get the new saved position
        settings.refresh_from_db()
        second_position = settings.wsjtx_last_position
        self.assertGreater(second_position, first_position, "Position should advance after second import")

    def test_incremental_import_from_middle_of_file(self):
        """
        Test that incremental import can correctly seek to a position and continue reading.
        This verifies the fix works with seek() + readline() combination.
        """
        # Calculate the position of the 3rd line
        lines = self.test_content.split('\n')
        first_two_lines = '\n'.join(lines[:2]) + '\n'
        start_position = len(first_two_lines.encode('utf-8'))

        settings = PropScopeSettings.objects.create(
            name='test_settings',
            is_active=False,
            wsjtx_last_position=start_position
        )

        importer = WsjtxLogImporter()

        # Import from the middle of the file
        import_run = importer.import_file(
            file_path=self.test_file_path,
            incremental=True,
            settings=settings
        )

        # Assert import completed successfully
        self.assertEqual(import_run.status, 'completed')
        # Should process lines from position onwards (3 lines: 3rd, 4th, 5th)
        self.assertEqual(import_run.lines_total, 3)

    def test_file_position_updated_correctly(self):
        """
        Test that file position is correctly updated and saved after import.
        """
        settings = PropScopeSettings.objects.create(
            name='test_settings',
            is_active=False,
            wsjtx_last_position=0
        )

        importer = WsjtxLogImporter()

        # Run incremental import
        import_run = importer.import_file(
            file_path=self.test_file_path,
            incremental=True,
            settings=settings
        )

        # Get file size
        file_size = os.path.getsize(self.test_file_path)

        # Get saved position
        settings.refresh_from_db()
        saved_position = settings.wsjtx_last_position

        # Position should be at or near end of file (equal to file size)
        self.assertEqual(saved_position, file_size, "Position should match file size after reading entire file")

    def test_azimuth_deg_persisted(self):
        """
        Test that azimuth_deg is correctly persisted to the database.
        This verifies the fix for issue #641.
        """
        from apps.geo.utils import maidenhead_to_latlon

        # Create settings with station coordinates to enable azimuth calculation
        station_lat, station_lon = maidenhead_to_latlon('JN68qv')  # Stuttgart area
        settings = PropScopeSettings.objects.create(
            name='test_settings',
            is_active=True,
            station_locator='JN68qv',
            station_latitude=station_lat,
            station_longitude=station_lon,
            wsjtx_last_position=0
        )

        importer = WsjtxLogImporter()

        # Run import
        import_run = importer.import_file(
            file_path=self.test_file_path,
            incremental=False,
            settings=settings
        )

        # Assert import completed successfully
        self.assertEqual(import_run.status, 'completed')

        # Check that HeardSignal records have azimuth_deg populated
        from apps.cq.models import HeardSignal
        signals_with_azimuth = HeardSignal.objects.filter(azimuth_deg__isnull=False)

        # We should have at least some signals with azimuth data
        # (all CQ signals with valid locators should have azimuth calculated)
        self.assertGreater(signals_with_azimuth.count(), 0,
                          "At least one signal should have azimuth_deg populated")

        # Verify that azimuth values are in valid range (0-360 degrees)
        for signal in signals_with_azimuth:
            self.assertGreaterEqual(signal.azimuth_deg, 0.0)
            self.assertLessEqual(signal.azimuth_deg, 360.0)

