from django.test import TestCase
from apps.callsign.models import CallsignPrefix, GermanCallsignClassRule
from apps.callsign.services import CallsignService


class CallsignServiceTest(TestCase):
    """Tests for CallsignService"""

    def setUp(self):
        """Set up test data"""
        self.service = CallsignService()

        # Create test prefixes
        CallsignPrefix.objects.create(
            prefix='DL',
            country='Germany',
            continent='EU',
            itu_region=1,
            cq_zone=14,
            is_active=True
        )
        CallsignPrefix.objects.create(
            prefix='OE',
            country='Austria',
            continent='EU',
            itu_region=1,
            cq_zone=15,
            is_active=True
        )
        CallsignPrefix.objects.create(
            prefix='EA8',
            country='Canary Islands',
            continent='AF',
            itu_region=1,
            cq_zone=33,
            is_active=True
        )
        CallsignPrefix.objects.create(
            prefix='EA',
            country='Spain',
            continent='EU',
            itu_region=1,
            cq_zone=14,
            is_active=True
        )
        CallsignPrefix.objects.create(
            prefix='K',
            country='United States',
            continent='NA',
            itu_region=2,
            cq_zone=5,
            is_active=True
        )
        # Inactive prefix should not be used
        CallsignPrefix.objects.create(
            prefix='TEST',
            country='Test Country',
            continent='XX',
            itu_region=1,
            cq_zone=1,
            is_active=False
        )

        # Create German callsign class rules
        GermanCallsignClassRule.objects.create(
            prefix_pattern='DL',
            license_class='A',
            description='Class A',
            is_active=True
        )
        GermanCallsignClassRule.objects.create(
            prefix_pattern='DO',
            license_class='E',
            description='Class E',
            is_active=True
        )

    def test_normalize_callsign_basic(self):
        """Test basic callsign normalization"""
        self.assertEqual(self.service.normalize_callsign(' dl3tx '), 'DL3TX')
        self.assertEqual(self.service.normalize_callsign('dl3tx'), 'DL3TX')
        self.assertEqual(self.service.normalize_callsign('DL3TX'), 'DL3TX')

    def test_normalize_callsign_angle_brackets(self):
        """Test removing angle brackets"""
        self.assertEqual(self.service.normalize_callsign('<R065N>'), 'R065N')
        self.assertEqual(self.service.normalize_callsign('<DL3TX>'), 'DL3TX')

    def test_normalize_callsign_portable(self):
        """Test portable callsign normalization"""
        self.assertEqual(self.service.normalize_callsign('dl/ad2lx'), 'DL/AD2LX')
        self.assertEqual(self.service.normalize_callsign('EA8/DL1ABC'), 'EA8/DL1ABC')

    def test_normalize_callsign_empty(self):
        """Test empty callsign"""
        self.assertEqual(self.service.normalize_callsign(''), '')
        self.assertEqual(self.service.normalize_callsign('  '), '')

    def test_get_qrz_url(self):
        """Test QRZ URL generation"""
        self.assertEqual(
            self.service.get_qrz_url('DL3TX'),
            'https://www.qrz.com/db/DL3TX'
        )
        self.assertEqual(
            self.service.get_qrz_url(' dl3tx '),
            'https://www.qrz.com/db/DL3TX'
        )

    def test_detect_prefix_simple(self):
        """Test simple prefix detection"""
        prefix = self.service.detect_prefix('DL3TX')
        self.assertIsNotNone(prefix)
        self.assertEqual(prefix.prefix, 'DL')
        self.assertEqual(prefix.country, 'Germany')
        self.assertEqual(prefix.continent, 'EU')

    def test_detect_prefix_longest_match_wins(self):
        """Test that longest prefix wins"""
        # EA8 is longer than EA and should match first
        prefix = self.service.detect_prefix('EA8XYZ')
        self.assertIsNotNone(prefix)
        self.assertEqual(prefix.prefix, 'EA8')
        self.assertEqual(prefix.country, 'Canary Islands')

        # EA1 should fall back to EA
        prefix = self.service.detect_prefix('EA1ABC')
        self.assertIsNotNone(prefix)
        self.assertEqual(prefix.prefix, 'EA')
        self.assertEqual(prefix.country, 'Spain')

    def test_detect_prefix_unknown_callsign(self):
        """Test unknown callsign returns None"""
        prefix = self.service.detect_prefix('ZZZ999')
        self.assertIsNone(prefix)

    def test_detect_prefix_inactive_not_used(self):
        """Test that inactive prefixes are not used"""
        prefix = self.service.detect_prefix('TEST123')
        self.assertIsNone(prefix)

    def test_detect_prefix_portable_before_slash(self):
        """Test portable callsign with prefix before slash"""
        # DL/AD2LX should detect DL
        prefix = self.service.detect_prefix('DL/AD2LX')
        self.assertIsNotNone(prefix)
        self.assertEqual(prefix.prefix, 'DL')
        self.assertEqual(prefix.country, 'Germany')

    def test_detect_prefix_portable_after_slash(self):
        """Test portable callsign with callsign after slash"""
        # EA8/DL1ABC should detect EA8 first (before slash)
        prefix = self.service.detect_prefix('EA8/DL1ABC')
        self.assertIsNotNone(prefix)
        self.assertEqual(prefix.prefix, 'EA8')
        self.assertEqual(prefix.country, 'Canary Islands')

    def test_detect_country(self):
        """Test country detection"""
        result = self.service.detect_country('DL3TX')
        self.assertEqual(result['country'], 'Germany')
        self.assertEqual(result['continent'], 'EU')
        self.assertEqual(result['itu_region'], 1)
        self.assertEqual(result['cq_zone'], 14)
        self.assertEqual(result['prefix'], 'DL')

    def test_detect_country_unknown(self):
        """Test unknown callsign returns empty dict"""
        result = self.service.detect_country('ZZZ999')
        self.assertEqual(result, {})

    def test_detect_german_license_class_dl(self):
        """Test German license class detection for DL"""
        license_class = self.service.detect_german_license_class('DL3TX')
        self.assertEqual(license_class, 'A')

    def test_detect_german_license_class_do(self):
        """Test German license class detection for DO"""
        license_class = self.service.detect_german_license_class('DO1ABC')
        self.assertEqual(license_class, 'E')

    def test_detect_german_license_class_unknown(self):
        """Test unknown German callsign returns None"""
        license_class = self.service.detect_german_license_class('K1ABC')
        self.assertIsNone(license_class)

    def test_detect_german_license_class_portable(self):
        """Test German license class for portable callsign"""
        license_class = self.service.detect_german_license_class('DL/DL3TX')
        self.assertEqual(license_class, 'A')

    def test_detect_prefix_case_insensitive(self):
        """Test prefix detection is case-insensitive"""
        prefix_upper = self.service.detect_prefix('DL3TX')
        prefix_lower = self.service.detect_prefix('dl3tx')
        self.assertEqual(prefix_upper.prefix, prefix_lower.prefix)

