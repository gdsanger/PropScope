from django.test import TestCase
from apps.cq.models import BandDefinition, HeardSignal
from apps.cq.services import BandService
from apps.ingest.models import ImportRun
from django.utils import timezone


class HeardSignalModelTest(TestCase):
    """Tests for HeardSignal model"""

    def setUp(self):
        """Set up test data"""
        # Create an import run for foreign key relationship
        self.import_run = ImportRun.objects.create(
            file_path="/tmp/test.txt",
            status="completed",
        )

    def test_locator_map_url_with_valid_locator(self):
        """Test locator_map_url property with valid 4-character locator."""
        signal = HeardSignal(
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
            locator="JN68",
        )
        self.assertEqual(signal.locator_map_url, "https://k7fry.com/grid/?qth=JN68")

    def test_locator_map_url_with_6_char_locator(self):
        """Test locator_map_url property with valid 6-character locator."""
        signal = HeardSignal(
            import_run=self.import_run,
            timestamp=timezone.now(),
            frequency_mhz=14.074,
            band="20m",
            mode="FT8",
            snr=10,
            dt=0.5,
            audio_frequency=1500,
            raw_message="CQ DL1ABC JN68qv",
            raw_line="test line",
            raw_hash="abc456",
            callsign="DL1ABC",
            locator="JN68qv",
        )
        self.assertEqual(signal.locator_map_url, "https://k7fry.com/grid/?qth=JN68QV")

    def test_locator_map_url_with_no_locator(self):
        """Test locator_map_url property returns None when locator is None."""
        signal = HeardSignal(
            import_run=self.import_run,
            timestamp=timezone.now(),
            frequency_mhz=14.074,
            band="20m",
            mode="FT8",
            snr=10,
            dt=0.5,
            audio_frequency=1500,
            raw_message="CQ DL1ABC",
            raw_line="test line",
            raw_hash="abc789",
            callsign="DL1ABC",
            locator=None,
        )
        self.assertIsNone(signal.locator_map_url)

    def test_locator_map_url_with_empty_locator(self):
        """Test locator_map_url property returns None when locator is empty."""
        signal = HeardSignal(
            import_run=self.import_run,
            timestamp=timezone.now(),
            frequency_mhz=14.074,
            band="20m",
            mode="FT8",
            snr=10,
            dt=0.5,
            audio_frequency=1500,
            raw_message="CQ DL1ABC",
            raw_line="test line",
            raw_hash="abc101112",
            callsign="DL1ABC",
            locator="",
        )
        self.assertIsNone(signal.locator_map_url)


class BandServiceTest(TestCase):
    """Tests for BandService"""

    def setUp(self):
        """Set up test data"""
        self.service = BandService()

        # Create test band definitions
        BandDefinition.objects.create(
            name='40m',
            lower_frequency_mhz=7.0,
            upper_frequency_mhz=7.3,
            mode_hint='HF',
            is_active=True
        )
        BandDefinition.objects.create(
            name='20m',
            lower_frequency_mhz=14.0,
            upper_frequency_mhz=14.35,
            mode_hint='HF',
            is_active=True
        )
        BandDefinition.objects.create(
            name='10m',
            lower_frequency_mhz=28.0,
            upper_frequency_mhz=29.7,
            mode_hint='HF',
            is_active=True
        )
        BandDefinition.objects.create(
            name='2m',
            lower_frequency_mhz=144.0,
            upper_frequency_mhz=148.0,
            mode_hint='VHF',
            is_active=True
        )
        # Inactive band should not be used
        BandDefinition.objects.create(
            name='TEST',
            lower_frequency_mhz=1.0,
            upper_frequency_mhz=2.0,
            mode_hint='TEST',
            is_active=False
        )

    def test_detect_band_40m(self):
        """Test 40m band detection"""
        band = self.service.detect_band(7.074)
        self.assertIsNotNone(band)
        self.assertEqual(band.name, '40m')
        self.assertEqual(band.mode_hint, 'HF')

    def test_detect_band_20m(self):
        """Test 20m band detection"""
        band = self.service.detect_band(14.074)
        self.assertIsNotNone(band)
        self.assertEqual(band.name, '20m')

    def test_detect_band_10m(self):
        """Test 10m band detection"""
        band = self.service.detect_band(28.074)
        self.assertIsNotNone(band)
        self.assertEqual(band.name, '10m')

    def test_detect_band_2m(self):
        """Test 2m band detection"""
        band = self.service.detect_band(144.174)
        self.assertIsNotNone(band)
        self.assertEqual(band.name, '2m')
        self.assertEqual(band.mode_hint, 'VHF')

    def test_detect_band_outside_all_bands(self):
        """Test frequency outside all bands returns None"""
        band = self.service.detect_band(999.999)
        self.assertIsNone(band)

    def test_detect_band_lower_boundary(self):
        """Test lower frequency boundary"""
        # Exact lower boundary should match
        band = self.service.detect_band(7.0)
        self.assertIsNotNone(band)
        self.assertEqual(band.name, '40m')

    def test_detect_band_upper_boundary(self):
        """Test upper frequency boundary"""
        # Exact upper boundary should match
        band = self.service.detect_band(7.3)
        self.assertIsNotNone(band)
        self.assertEqual(band.name, '40m')

    def test_detect_band_just_below_lower_boundary(self):
        """Test frequency just below lower boundary"""
        band = self.service.detect_band(6.999)
        self.assertIsNone(band)

    def test_detect_band_just_above_upper_boundary(self):
        """Test frequency just above upper boundary"""
        band = self.service.detect_band(7.301)
        self.assertIsNone(band)

    def test_detect_band_inactive_ignored(self):
        """Test that inactive band definitions are ignored"""
        band = self.service.detect_band(1.5)
        self.assertIsNone(band)

    def test_detect_band_invalid_frequency_none(self):
        """Test None frequency returns None"""
        band = self.service.detect_band(None)
        self.assertIsNone(band)

    def test_detect_band_invalid_frequency_zero(self):
        """Test zero frequency returns None"""
        band = self.service.detect_band(0)
        self.assertIsNone(band)

    def test_detect_band_invalid_frequency_negative(self):
        """Test negative frequency returns None"""
        band = self.service.detect_band(-10.5)
        self.assertIsNone(band)

    def test_get_band_name(self):
        """Test get_band_name convenience method"""
        self.assertEqual(self.service.get_band_name(7.074), '40m')
        self.assertEqual(self.service.get_band_name(14.074), '20m')
        self.assertEqual(self.service.get_band_name(28.074), '10m')

    def test_get_band_name_unknown(self):
        """Test get_band_name returns None for unknown frequency"""
        self.assertIsNone(self.service.get_band_name(999.999))

