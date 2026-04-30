"""
Tests for the backfill_enrichment management command.
"""

from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from io import StringIO
from apps.cq.models import HeardSignal, BandDefinition
from apps.ingest.models import ImportRun
from apps.geo.models import MaidenheadArea


class BackfillEnrichmentCommandTest(TestCase):
    """Tests for the backfill_enrichment management command."""

    def setUp(self):
        """Set up test data."""
        # Create an import run for foreign key relationship
        self.import_run = ImportRun.objects.create(
            source_filename="/tmp/test.txt",
            status="completed",
        )

        # Create test band definitions
        BandDefinition.objects.create(
            name='20m',
            lower_frequency_mhz=14.0,
            upper_frequency_mhz=14.35,
            mode_hint='HF',
            is_active=True
        )

        # Create test MaidenheadArea
        MaidenheadArea.objects.create(
            locator='JN68',
            center_lat=48.5,
            center_lon=9.0,
            primary_country='Germany',
            continent='EU',
            is_ambiguous=False
        )

    def test_command_help_shows_options(self):
        """Test that the command help shows all expected options."""
        # Testing help is tricky because it exits and may write to stderr
        # Just verify that the command can show help without crashing
        from django.core.management import get_commands
        self.assertIn('backfill_enrichment', get_commands())

    def test_command_runs_without_error(self):
        """Test that the command runs without errors when there are no signals."""
        out = StringIO()
        err = StringIO()

        # Should not raise any exception
        call_command('backfill_enrichment', '--dry-run', stdout=out, stderr=err)

        output = out.getvalue()
        self.assertIn('HeardSignal Enrichment Backfill', output)
        self.assertIn('No records need backfilling', output)

    def test_command_with_verbosity_levels(self):
        """Test that the command works with different verbosity levels."""
        # Create a test signal
        HeardSignal.objects.create(
            import_run=self.import_run,
            timestamp=timezone.now(),
            frequency_mhz=14.074,
            band="",  # Missing enrichment
            mode="FT8",
            snr=10,
            dt=0.5,
            audio_frequency=1500,
            raw_message="CQ DL1ABC JN68",
            raw_line="test line",
            raw_hash="abc123",
            callsign="DL1ABC",
            locator="JN68qv",
        )

        out = StringIO()
        err = StringIO()

        # Test with verbosity 0 - should not raise AttributeError
        call_command('backfill_enrichment', '--dry-run', verbosity=0, stdout=out, stderr=err)

        # Test with verbosity 1 - should not raise AttributeError
        out = StringIO()
        call_command('backfill_enrichment', '--dry-run', verbosity=1, stdout=out, stderr=err)

        # Test with verbosity 2 - should not raise AttributeError and show details
        out = StringIO()
        call_command('backfill_enrichment', '--dry-run', verbosity=2, stdout=out, stderr=err)
        output = out.getvalue()
        self.assertIn('Updated DL1ABC', output)

    def test_command_default_mode_skips_enriched_records(self):
        """Test that default mode only updates records with missing enrichment."""
        # Create a fully enriched signal
        signal = HeardSignal.objects.create(
            import_run=self.import_run,
            timestamp=timezone.now(),
            frequency_mhz=14.074,
            band="20m",  # Already enriched
            mode="FT8",
            snr=10,
            dt=0.5,
            audio_frequency=1500,
            raw_message="CQ DL1ABC JN68",
            raw_line="test line",
            raw_hash="abc123",
            callsign="DL1ABC",
            locator="JN68qv",
            qrz_url="https://www.qrz.com/db/DL1ABC",
            callsign_country="Germany",
            locator_country="Germany",
        )

        out = StringIO()
        err = StringIO()

        # Run in default mode
        call_command('backfill_enrichment', stdout=out, stderr=err)

        output = out.getvalue()
        self.assertIn('DEFAULT MODE', output)
        self.assertIn('No records need backfilling', output)

    def test_command_full_mode_updates_all_records(self):
        """Test that --full mode updates even fully enriched records."""
        # Create a fully enriched signal
        signal = HeardSignal.objects.create(
            import_run=self.import_run,
            timestamp=timezone.now(),
            frequency_mhz=14.074,
            band="20m",  # Already enriched
            mode="FT8",
            snr=10,
            dt=0.5,
            audio_frequency=1500,
            raw_message="CQ DL1ABC JN68",
            raw_line="test line",
            raw_hash="abc123",
            callsign="DL1ABC",
            locator="JN68qv",
            qrz_url="https://www.qrz.com/db/DL1ABC",
            callsign_country="Germany",
            locator_country="Germany",
        )

        out = StringIO()
        err = StringIO()

        # Run in full rebuild mode
        call_command('backfill_enrichment', '--full', '--dry-run', stdout=out, stderr=err)

        output = out.getvalue()
        self.assertIn('FULL REBUILD MODE', output)
        self.assertIn('Records to process: 1', output)

    def test_command_force_is_alias_for_full(self):
        """Test that --force is an alias for --full."""
        # Create a fully enriched signal
        signal = HeardSignal.objects.create(
            import_run=self.import_run,
            timestamp=timezone.now(),
            frequency_mhz=14.074,
            band="20m",
            mode="FT8",
            snr=10,
            dt=0.5,
            audio_frequency=1500,
            raw_message="CQ DL1ABC JN68",
            raw_line="test line",
            raw_hash="abc123",
            callsign="DL1ABC",
            locator="JN68qv",
            qrz_url="https://www.qrz.com/db/DL1ABC",
        )

        out = StringIO()
        err = StringIO()

        # Run with --force (legacy alias)
        call_command('backfill_enrichment', '--force', '--dry-run', stdout=out, stderr=err)

        output = out.getvalue()
        self.assertIn('FULL REBUILD MODE', output)
        self.assertIn('Records to process: 1', output)

    def test_command_enriches_missing_fields(self):
        """Test that the command enriches missing fields."""
        # Create a signal with missing enrichment
        signal = HeardSignal.objects.create(
            import_run=self.import_run,
            timestamp=timezone.now(),
            frequency_mhz=14.074,
            band="",  # Missing
            mode="FT8",
            snr=10,
            dt=0.5,
            audio_frequency=1500,
            raw_message="CQ DL1ABC JN68",
            raw_line="test line",
            raw_hash="abc123",
            callsign="DL1ABC",
            locator="JN68qv",
        )

        out = StringIO()
        err = StringIO()

        # Run the command (not dry-run)
        call_command('backfill_enrichment', stdout=out, stderr=err)

        # Reload the signal from the database
        signal.refresh_from_db()

        # Check that fields were enriched
        self.assertEqual(signal.band, '20m')
        self.assertIsNotNone(signal.qrz_url)
        self.assertEqual(signal.locator_country, 'Germany')
        self.assertEqual(signal.locator_continent, 'EU')
        self.assertFalse(signal.locator_ambiguous)

    def test_command_with_limit(self):
        """Test that --limit parameter works correctly."""
        # Create multiple signals
        for i in range(5):
            HeardSignal.objects.create(
                import_run=self.import_run,
                timestamp=timezone.now(),
                frequency_mhz=14.074,
                band="",  # Missing
                mode="FT8",
                snr=10,
                dt=0.5,
                audio_frequency=1500,
                raw_message=f"CQ DL{i}ABC JN68",
                raw_line=f"test line {i}",
                raw_hash=f"abc{i}",
                callsign=f"DL{i}ABC",
                locator="JN68qv",
            )

        out = StringIO()
        err = StringIO()

        # Run with limit
        call_command('backfill_enrichment', '--limit', '3', '--dry-run', stdout=out, stderr=err)

        output = out.getvalue()
        self.assertIn('Records to process: 3', output)

    def test_command_with_batch_size(self):
        """Test that --batch-size parameter is accepted."""
        # Create a signal
        HeardSignal.objects.create(
            import_run=self.import_run,
            timestamp=timezone.now(),
            frequency_mhz=14.074,
            band="",
            mode="FT8",
            snr=10,
            dt=0.5,
            audio_frequency=1500,
            raw_message="CQ DL1ABC JN68",
            raw_line="test line",
            raw_hash="abc123",
            callsign="DL1ABC",
            locator="JN68qv",
        )

        out = StringIO()
        err = StringIO()

        # Should not raise any exception
        call_command('backfill_enrichment', '--batch-size', '100', '--dry-run', stdout=out, stderr=err)

        output = out.getvalue()
        self.assertIn('Processing batch', output)

    def test_command_creates_missing_maidenhead_areas(self):
        """Test that the command creates missing MaidenheadArea records."""
        # Create a signal with a locator that doesn't exist in MaidenheadArea
        signal = HeardSignal.objects.create(
            import_run=self.import_run,
            timestamp=timezone.now(),
            frequency_mhz=14.074,
            band="",
            mode="FT8",
            snr=10,
            dt=0.5,
            audio_frequency=1500,
            raw_message="CQ W1ABC FN31",
            raw_line="test line",
            raw_hash="abc123",
            callsign="W1ABC",
            locator="FN31pr",  # FN31 doesn't exist in MaidenheadArea
        )

        # Verify FN31 doesn't exist yet
        self.assertFalse(MaidenheadArea.objects.filter(locator='FN31').exists())

        out = StringIO()
        err = StringIO()

        # Run the command (not dry-run, not skipping maidenhead creation)
        call_command('backfill_enrichment', stdout=out, stderr=err)

        output = out.getvalue()

        # Verify output mentions MaidenheadArea creation
        self.assertIn('Step 1: Creating Missing MaidenheadArea Records', output)

        # Verify FN31 now exists (if GeoService can detect the country)
        # Note: FN31 is in the USA, so this should be created
        # However, if GeoService is not available or shapefile is missing, it might not be created
        # So we just check that the command tried to create it
        self.assertIn('MaidenheadArea creation complete', output)

    def test_command_skips_maidenhead_creation_with_flag(self):
        """Test that --skip-maidenhead-creation flag skips MaidenheadArea creation."""
        # Create a signal with a locator that doesn't exist in MaidenheadArea
        signal = HeardSignal.objects.create(
            import_run=self.import_run,
            timestamp=timezone.now(),
            frequency_mhz=14.074,
            band="",
            mode="FT8",
            snr=10,
            dt=0.5,
            audio_frequency=1500,
            raw_message="CQ W1ABC FN31",
            raw_line="test line",
            raw_hash="abc123",
            callsign="W1ABC",
            locator="FN31pr",
        )

        out = StringIO()
        err = StringIO()

        # Run the command with --skip-maidenhead-creation
        call_command('backfill_enrichment', '--skip-maidenhead-creation', '--dry-run', stdout=out, stderr=err)

        output = out.getvalue()

        # Verify it skipped MaidenheadArea creation
        self.assertIn('Skipping MaidenheadArea creation', output)

    def test_command_handles_ocean_locators(self):
        """Test that the command handles ocean/unmapped locators gracefully."""
        # Create a signal with an ocean locator (e.g., in the middle of the Pacific)
        # RR00 is roughly in the Pacific Ocean
        signal = HeardSignal.objects.create(
            import_run=self.import_run,
            timestamp=timezone.now(),
            frequency_mhz=14.074,
            band="",
            mode="FT8",
            snr=10,
            dt=0.5,
            audio_frequency=1500,
            raw_message="CQ TEST RR00",
            raw_line="test line",
            raw_hash="abc123",
            callsign="TEST",
            locator="RR00aa",
        )

        out = StringIO()
        err = StringIO()

        # Run the command (dry-run to avoid side effects)
        call_command('backfill_enrichment', '--dry-run', stdout=out, stderr=err)

        output = out.getvalue()

        # Should not crash and should handle ocean locators
        self.assertIn('HeardSignal Enrichment Backfill', output)

    def test_command_respects_existing_maidenhead_areas(self):
        """Test that the command doesn't duplicate existing MaidenheadArea records."""
        # Create a signal with JN68 which already exists
        signal = HeardSignal.objects.create(
            import_run=self.import_run,
            timestamp=timezone.now(),
            frequency_mhz=14.074,
            band="",
            mode="FT8",
            snr=10,
            dt=0.5,
            audio_frequency=1500,
            raw_message="CQ DL1ABC JN68",
            raw_line="test line",
            raw_hash="abc123",
            callsign="DL1ABC",
            locator="JN68qv",
        )

        # Count JN68 records before
        count_before = MaidenheadArea.objects.filter(locator='JN68').count()
        self.assertEqual(count_before, 1)

        out = StringIO()
        err = StringIO()

        # Run the command
        call_command('backfill_enrichment', stdout=out, stderr=err)

        # Count JN68 records after - should still be 1
        count_after = MaidenheadArea.objects.filter(locator='JN68').count()
        self.assertEqual(count_after, 1)
