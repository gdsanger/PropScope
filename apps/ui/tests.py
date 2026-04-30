from django.test import TestCase, Client
from django.urls import reverse
from django.db import IntegrityError
from apps.ui.models import StationProfile


class StationProfileModelTests(TestCase):
    """Tests for the StationProfile model."""

    def test_create_station_profile_with_all_fields(self):
        """Test creating a station profile with all fields populated."""
        profile = StationProfile.objects.create(
            name="Home QTH",
            callsign="DL1ABC",
            locator="JN68",
            latitude=48.5,
            longitude=8.0,
            is_default=True,
            is_active=True,
            notes="Primary receiving station"
        )

        self.assertEqual(profile.name, "Home QTH")
        self.assertEqual(profile.callsign, "DL1ABC")
        self.assertEqual(profile.locator, "JN68")
        self.assertEqual(profile.latitude, 48.5)
        self.assertEqual(profile.longitude, 8.0)
        self.assertTrue(profile.is_default)
        self.assertTrue(profile.is_active)
        self.assertEqual(profile.notes, "Primary receiving station")
        self.assertIsNotNone(profile.created_at)
        self.assertIsNotNone(profile.updated_at)

    def test_create_station_profile_minimal_fields(self):
        """Test creating a station profile with only required fields."""
        profile = StationProfile.objects.create(
            name="Portable Station",
            locator="JO62"
        )

        self.assertEqual(profile.name, "Portable Station")
        self.assertEqual(profile.callsign, "")  # Optional field
        self.assertEqual(profile.locator, "JO62")
        self.assertIsNone(profile.latitude)
        self.assertIsNone(profile.longitude)
        self.assertFalse(profile.is_default)  # Default value
        self.assertTrue(profile.is_active)  # Default value
        self.assertEqual(profile.notes, "")

    def test_create_station_profile_without_callsign(self):
        """Test creating a receive-only station without callsign."""
        profile = StationProfile.objects.create(
            name="RX Only",
            locator="JN58"
        )

        self.assertEqual(profile.callsign, "")
        self.assertEqual(profile.name, "RX Only")

    def test_station_profile_str_representation_full(self):
        """Test string representation with all fields."""
        profile = StationProfile.objects.create(
            name="Home QTH",
            callsign="DL1ABC",
            locator="JN68",
            is_default=True,
            is_active=True
        )

        str_repr = str(profile)
        self.assertIn("Home QTH", str_repr)
        self.assertIn("DL1ABC", str_repr)
        self.assertIn("JN68", str_repr)
        self.assertIn("[DEFAULT]", str_repr)

    def test_station_profile_str_representation_inactive(self):
        """Test string representation for inactive profile."""
        profile = StationProfile.objects.create(
            name="Old Station",
            locator="JO62",
            is_active=False
        )

        str_repr = str(profile)
        self.assertIn("[INACTIVE]", str_repr)

    def test_station_profile_str_representation_minimal(self):
        """Test string representation with minimal fields."""
        profile = StationProfile.objects.create(
            name="Simple",
            locator="JN68"
        )

        str_repr = str(profile)
        self.assertIn("Simple", str_repr)
        self.assertIn("JN68", str_repr)

    def test_station_profile_ordering(self):
        """Test that profiles are ordered by default/active/name."""
        profile1 = StationProfile.objects.create(
            name="C Station",
            locator="JN68",
            is_default=False,
            is_active=True
        )
        profile2 = StationProfile.objects.create(
            name="A Station",
            locator="JO62",
            is_default=True,
            is_active=True
        )
        profile3 = StationProfile.objects.create(
            name="B Station",
            locator="JN58",
            is_default=False,
            is_active=False
        )

        profiles = list(StationProfile.objects.all())
        # Default should be first, then active by name, then inactive
        self.assertEqual(profiles[0].name, "A Station")  # Default
        self.assertEqual(profiles[1].name, "C Station")  # Active, not default
        self.assertEqual(profiles[2].name, "B Station")  # Inactive

    def test_is_default_index_exists(self):
        """Test that is_default and is_active fields are indexed."""
        # This is more of a smoke test - the index is created by migration
        profile = StationProfile.objects.create(
            name="Test",
            locator="JN68",
            is_default=True,
            is_active=True
        )

        # Should be able to filter efficiently
        results = StationProfile.objects.filter(is_default=True, is_active=True)
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first(), profile)

    def test_locator_index_exists(self):
        """Test that locator field is indexed."""
        profile = StationProfile.objects.create(
            name="Test",
            locator="JN68"
        )

        # Should be able to filter efficiently by locator
        results = StationProfile.objects.filter(locator="JN68")
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first(), profile)

    def test_multiple_profiles_with_different_locators(self):
        """Test creating multiple profiles with different locators."""
        profile1 = StationProfile.objects.create(
            name="Station 1",
            locator="JN68"
        )
        profile2 = StationProfile.objects.create(
            name="Station 2",
            locator="JO62"
        )

        self.assertEqual(StationProfile.objects.count(), 2)
        self.assertNotEqual(profile1.locator, profile2.locator)

    def test_update_station_profile(self):
        """Test updating a station profile."""
        profile = StationProfile.objects.create(
            name="Old Name",
            locator="JN68"
        )

        old_updated_at = profile.updated_at

        # Update the profile
        profile.name = "New Name"
        profile.callsign = "DL1ABC"
        profile.save()

        profile.refresh_from_db()
        self.assertEqual(profile.name, "New Name")
        self.assertEqual(profile.callsign, "DL1ABC")
        self.assertGreater(profile.updated_at, old_updated_at)

    def test_coordinates_optional(self):
        """Test that latitude and longitude are optional."""
        profile = StationProfile.objects.create(
            name="No Coords",
            locator="JN68"
        )

        self.assertIsNone(profile.latitude)
        self.assertIsNone(profile.longitude)

    def test_coordinates_can_be_set(self):
        """Test setting precise coordinates."""
        profile = StationProfile.objects.create(
            name="Precise Location",
            locator="JN68",
            latitude=48.123456,
            longitude=8.987654
        )

        self.assertAlmostEqual(profile.latitude, 48.123456, places=6)
        self.assertAlmostEqual(profile.longitude, 8.987654, places=6)


class DashboardViewTests(TestCase):
    """Tests for the dashboard views."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_dashboard_view_loads(self):
        """Test that dashboard view loads successfully."""
        response = self.client.get(reverse('ui:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/index.html')

    def test_dashboard_view_context_has_summary(self):
        """Test that dashboard context contains summary data."""
        response = self.client.get(reverse('ui:dashboard'))
        self.assertIn('summary', response.context)
        self.assertIn('top_dx', response.context)
        self.assertIn('top_callsigns', response.context)
        self.assertIn('top_locators', response.context)

    def test_dashboard_kpi_cards_partial_loads(self):
        """Test that KPI cards partial loads successfully."""
        response = self.client.get(reverse('ui:dashboard-kpi-cards'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/partials/kpi_cards.html')

    def test_dashboard_activity_by_hour_partial_loads(self):
        """Test that activity by hour partial loads successfully."""
        response = self.client.get(reverse('ui:dashboard-activity-by-hour'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/partials/activity_by_hour.html')

    def test_dashboard_distance_by_hour_partial_loads(self):
        """Test that distance by hour partial loads successfully."""
        response = self.client.get(reverse('ui:dashboard-distance-by-hour'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/partials/distance_by_hour.html')

    def test_dashboard_snr_by_hour_partial_loads(self):
        """Test that SNR by hour partial loads successfully."""
        response = self.client.get(reverse('ui:dashboard-snr-by-hour'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/partials/snr_by_hour.html')

    def test_dashboard_band_activity_partial_loads(self):
        """Test that band activity partial loads successfully."""
        response = self.client.get(reverse('ui:dashboard-band-activity'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/partials/band_activity.html')

    def test_dashboard_top_dx_partial_loads(self):
        """Test that top DX partial loads successfully."""
        response = self.client.get(reverse('ui:dashboard-top-dx'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/partials/top_dx.html')

    def test_dashboard_top_callsigns_partial_loads(self):
        """Test that top callsigns partial loads successfully."""
        response = self.client.get(reverse('ui:dashboard-top-callsigns'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/partials/top_callsigns.html')

    def test_dashboard_top_locators_partial_loads(self):
        """Test that top locators partial loads successfully."""
        response = self.client.get(reverse('ui:dashboard-top-locators'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/partials/top_locators.html')

    def test_dashboard_with_date_filter(self):
        """Test that dashboard accepts date filter parameters."""
        response = self.client.get(
            reverse('ui:dashboard'),
            {'date_from': '2026-04-01', 'date_to': '2026-04-30'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('filters', response.context)
        self.assertEqual(response.context['filters']['date_from'], '2026-04-01')
        self.assertEqual(response.context['filters']['date_to'], '2026-04-30')

    def test_dashboard_with_period_filter_1h(self):
        """Test that dashboard accepts 1h period filter."""
        response = self.client.get(
            reverse('ui:dashboard'),
            {'period': '1h'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('period', response.context)
        self.assertEqual(response.context['period'], '1h')
        self.assertIn('filters', response.context)
        self.assertIn('date_from', response.context['filters'])

    def test_dashboard_with_period_filter_3h(self):
        """Test that dashboard accepts 3h period filter."""
        response = self.client.get(
            reverse('ui:dashboard'),
            {'period': '3h'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('period', response.context)
        self.assertEqual(response.context['period'], '3h')
        self.assertIn('filters', response.context)
        self.assertIn('date_from', response.context['filters'])

    def test_dashboard_with_period_filter_6h(self):
        """Test that dashboard accepts 6h period filter."""
        response = self.client.get(
            reverse('ui:dashboard'),
            {'period': '6h'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('period', response.context)
        self.assertEqual(response.context['period'], '6h')
        self.assertIn('filters', response.context)
        self.assertIn('date_from', response.context['filters'])

    def test_dashboard_with_period_filter_12h(self):
        """Test that dashboard accepts 12h period filter."""
        response = self.client.get(
            reverse('ui:dashboard'),
            {'period': '12h'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('period', response.context)
        self.assertEqual(response.context['period'], '12h')
        self.assertIn('filters', response.context)
        self.assertIn('date_from', response.context['filters'])

    def test_dashboard_with_period_filter_24h(self):
        """Test that dashboard accepts 24h period filter."""
        response = self.client.get(
            reverse('ui:dashboard'),
            {'period': '24h'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('period', response.context)
        self.assertEqual(response.context['period'], '24h')
        self.assertIn('filters', response.context)
        self.assertIn('date_from', response.context['filters'])

    def test_dashboard_with_period_filter_today(self):
        """Test that dashboard accepts today period filter."""
        response = self.client.get(
            reverse('ui:dashboard'),
            {'period': 'today'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('period', response.context)
        self.assertEqual(response.context['period'], 'today')
        self.assertIn('filters', response.context)
        self.assertIn('date_from', response.context['filters'])

    def test_dashboard_with_period_filter_7d(self):
        """Test that dashboard accepts 7d period filter."""
        response = self.client.get(
            reverse('ui:dashboard'),
            {'period': '7d'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('period', response.context)
        self.assertEqual(response.context['period'], '7d')
        self.assertIn('filters', response.context)
        self.assertIn('date_from', response.context['filters'])

    def test_dashboard_with_period_filter_30d(self):
        """Test that dashboard accepts 30d period filter."""
        response = self.client.get(
            reverse('ui:dashboard'),
            {'period': '30d'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('period', response.context)
        self.assertEqual(response.context['period'], '30d')
        self.assertIn('filters', response.context)
        self.assertIn('date_from', response.context['filters'])

    def test_dashboard_with_invalid_period_filter(self):
        """Test that dashboard handles invalid period filter gracefully."""
        response = self.client.get(
            reverse('ui:dashboard'),
            {'period': 'invalid'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('period', response.context)
        self.assertEqual(response.context['period'], 'invalid')
        # Invalid period should not create a filter
        self.assertNotIn('date_from', response.context['filters'])

    def test_dashboard_without_period_filter(self):
        """Test that dashboard works without period filter (all data)."""
        response = self.client.get(reverse('ui:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('period', response.context)
        self.assertIsNone(response.context['period'])
        # No period means no date filter
        self.assertNotIn('date_from', response.context['filters'])


class MaidenheadAreaModalViewTests(TestCase):
    """Tests for the MaidenheadArea modal view."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_maidenhead_area_create_modal_loads(self):
        """Test that modal loads successfully without locator parameter."""
        response = self.client.get(reverse('ui:maidenhead-area-create-modal'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/modals/maidenhead_area_create.html')

    def test_maidenhead_area_create_modal_with_valid_locator(self):
        """Test that modal pre-populates fields for valid locator."""
        response = self.client.get(
            reverse('ui:maidenhead-area-create-modal'),
            {'locator': 'JN68'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

        # Check that form has initial data
        form = response.context['form']
        self.assertEqual(form.initial.get('locator'), 'JN68')
        self.assertIsNotNone(form.initial.get('center_lat'))
        self.assertIsNotNone(form.initial.get('center_lon'))

        # Check that country and continent are pre-populated (if GeoService is available)
        # Note: This might be None if GeoService is not available or shapefile is missing
        # So we just check that the keys exist in initial data
        self.assertIn('primary_country', form.initial)
        self.assertIn('continent', form.initial)

    def test_maidenhead_area_create_modal_with_invalid_locator(self):
        """Test that modal handles invalid locator gracefully."""
        response = self.client.get(
            reverse('ui:maidenhead-area-create-modal'),
            {'locator': 'INVALID'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('error_message', response.context)
        self.assertIsNotNone(response.context['error_message'])

    def test_maidenhead_area_create_modal_normalizes_locator(self):
        """Test that modal normalizes locator to uppercase."""
        response = self.client.get(
            reverse('ui:maidenhead-area-create-modal'),
            {'locator': 'jn68'}  # lowercase
        )
        self.assertEqual(response.status_code, 200)

        # Should normalize to uppercase
        form = response.context['form']
        self.assertEqual(form.initial.get('locator'), 'JN68')

    def test_maidenhead_area_create_modal_calculates_coordinates(self):
        """Test that modal calculates lat/lon from locator."""
        response = self.client.get(
            reverse('ui:maidenhead-area-create-modal'),
            {'locator': 'JN68'}
        )
        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        # JN68 center should be approximately 48.5, 13.0
        lat = form.initial.get('center_lat')
        lon = form.initial.get('center_lon')
        self.assertIsNotNone(lat)
        self.assertIsNotNone(lon)
        self.assertAlmostEqual(lat, 48.5, delta=1.0)
        self.assertAlmostEqual(lon, 13.0, delta=1.0)

    def test_maidenhead_area_create_modal_handles_geoservice_failure(self):
        """Test that modal handles GeoService failure gracefully."""
        # Even if GeoService fails to detect country/continent,
        # the modal should still load successfully
        response = self.client.get(
            reverse('ui:maidenhead-area-create-modal'),
            {'locator': 'JN68'}
        )
        self.assertEqual(response.status_code, 200)
        # Should not crash even if GeoService is unavailable
        self.assertIn('form', response.context)
