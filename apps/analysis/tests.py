"""
Tests for the StatisticsService.
"""

from datetime import datetime, timezone as dt_timezone

from django.test import TestCase
from django.utils import timezone

from apps.analysis.services import StatisticsService
from apps.cq.models import HeardSignal
from apps.ingest.models import ImportRun


def make_import_run():
    return ImportRun.objects.create(source_filename="test.txt", status="completed")


def make_signal(import_run, **kwargs):
    """Helper to create a HeardSignal with sensible defaults."""
    defaults = dict(
        import_run=import_run,
        timestamp=timezone.now(),
        frequency_mhz=7.074,
        band="40m",
        mode="FT8",
        snr=-10,
        dt=0.3,
        audio_frequency=1200,
        raw_message="CQ DL1ABC JN68",
        raw_line="260419_185200     7.074 Rx FT8    -10  0.3 1200 CQ DL1ABC JN68",
        raw_hash=None,
        callsign="DL1ABC",
        locator="JN68",
        distance_km=800.0,
        qrz_url="https://www.qrz.com/db/DL1ABC",
    )
    defaults.update(kwargs)
    # Ensure unique raw_hash
    if defaults["raw_hash"] is None:
        import hashlib
        defaults["raw_hash"] = hashlib.sha256(
            f"{defaults['callsign']}{defaults['timestamp']}{defaults['raw_line']}".encode()
        ).hexdigest()
    return HeardSignal.objects.create(**defaults)


class StatisticsServiceEmptyDatabaseTest(TestCase):
    """Tests with an empty database – should return zeros / empty results."""

    def setUp(self):
        self.service = StatisticsService()

    def test_summary_empty(self):
        result = self.service.get_summary()
        self.assertEqual(result["cq_count"], 0)
        self.assertEqual(result["unique_callsigns"], 0)
        self.assertEqual(result["unique_locators"], 0)
        self.assertEqual(result["unique_bands"], 0)
        self.assertIsNone(result["min_distance_km"])
        self.assertIsNone(result["max_distance_km"])
        self.assertIsNone(result["avg_distance_km"])
        self.assertIsNone(result["min_snr"])
        self.assertIsNone(result["max_snr"])
        self.assertIsNone(result["avg_snr"])

    def test_cq_count_by_callsign_empty(self):
        self.assertEqual(self.service.get_cq_count_by_callsign(), [])

    def test_cq_count_by_locator_empty(self):
        self.assertEqual(self.service.get_cq_count_by_locator(), [])

    def test_cq_count_by_band_empty(self):
        self.assertEqual(self.service.get_cq_count_by_band(), [])

    def test_snr_stats_by_band_empty(self):
        self.assertEqual(self.service.get_snr_stats_by_band(), [])

    def test_snr_stats_by_locator_empty(self):
        self.assertEqual(self.service.get_snr_stats_by_locator(), [])

    def test_distance_stats_by_hour_empty(self):
        self.assertEqual(self.service.get_distance_stats_by_hour(), [])

    def test_activity_by_hour_empty(self):
        self.assertEqual(self.service.get_activity_by_hour(), [])

    def test_top_dx_empty(self):
        self.assertEqual(self.service.get_top_dx(), [])


class StatisticsServiceSummaryTest(TestCase):
    """Tests for get_summary()."""

    def setUp(self):
        self.service = StatisticsService()
        run = make_import_run()

        ts1 = datetime(2026, 4, 10, 10, 0, 0, tzinfo=dt_timezone.utc)
        ts2 = datetime(2026, 4, 15, 14, 0, 0, tzinfo=dt_timezone.utc)
        ts3 = datetime(2026, 4, 20, 20, 0, 0, tzinfo=dt_timezone.utc)

        make_signal(run, timestamp=ts1, callsign="DL1ABC", locator="JN68", band="40m", snr=-5, distance_km=500.0)
        make_signal(run, timestamp=ts2, callsign="G4XYZ", locator="IO91", band="20m", snr=-15, distance_km=1500.0)
        make_signal(run, timestamp=ts3, callsign="VE3ABC", locator="FN03", band="20m", snr=-20, distance_km=7000.0)

    def test_summary_counts(self):
        result = self.service.get_summary()
        self.assertEqual(result["cq_count"], 3)
        self.assertEqual(result["unique_callsigns"], 3)
        self.assertEqual(result["unique_locators"], 3)
        self.assertEqual(result["unique_bands"], 2)

    def test_summary_distance(self):
        result = self.service.get_summary()
        self.assertEqual(result["min_distance_km"], 500.0)
        self.assertEqual(result["max_distance_km"], 7000.0)
        self.assertAlmostEqual(result["avg_distance_km"], 3000.0, delta=1.0)

    def test_summary_snr(self):
        result = self.service.get_summary()
        self.assertEqual(result["min_snr"], -20)
        self.assertEqual(result["max_snr"], -5)
        self.assertAlmostEqual(result["avg_snr"], -13.3, delta=0.5)

    def test_summary_with_date_filter(self):
        result = self.service.get_summary(filters={"date_from": "2026-04-12", "date_to": "2026-04-16"})
        self.assertEqual(result["cq_count"], 1)
        self.assertEqual(result["unique_callsigns"], 1)

    def test_summary_with_band_filter(self):
        result = self.service.get_summary(filters={"band": "20m"})
        self.assertEqual(result["cq_count"], 2)
        self.assertEqual(result["unique_bands"], 1)

    def test_summary_filter_no_results(self):
        result = self.service.get_summary(filters={"band": "10m"})
        self.assertEqual(result["cq_count"], 0)
        self.assertIsNone(result["min_snr"])


class StatisticsServiceCqCountByCallsignTest(TestCase):
    """Tests for get_cq_count_by_callsign()."""

    def setUp(self):
        self.service = StatisticsService()
        run = make_import_run()

        ts1 = datetime(2026, 4, 10, 10, 0, 0, tzinfo=dt_timezone.utc)
        ts2 = datetime(2026, 4, 10, 11, 0, 0, tzinfo=dt_timezone.utc)
        ts3 = datetime(2026, 4, 10, 12, 0, 0, tzinfo=dt_timezone.utc)

        make_signal(run, timestamp=ts1, callsign="DL1ABC", band="40m", snr=-5, distance_km=500.0)
        make_signal(run, timestamp=ts2, callsign="DL1ABC", band="40m", snr=-15, distance_km=800.0)
        make_signal(run, timestamp=ts3, callsign="G4XYZ", band="20m", snr=-10, distance_km=1200.0)

    def test_count_by_callsign(self):
        result = self.service.get_cq_count_by_callsign()
        self.assertEqual(len(result), 2)
        # DL1ABC appears twice, should be first
        self.assertEqual(result[0]["callsign"], "DL1ABC")
        self.assertEqual(result[0]["count"], 2)
        self.assertEqual(result[1]["callsign"], "G4XYZ")
        self.assertEqual(result[1]["count"], 1)

    def test_count_by_callsign_avg_snr(self):
        result = self.service.get_cq_count_by_callsign()
        dl_row = next(r for r in result if r["callsign"] == "DL1ABC")
        self.assertAlmostEqual(dl_row["avg_snr"], -10.0, delta=0.5)

    def test_count_by_callsign_max_distance(self):
        result = self.service.get_cq_count_by_callsign()
        dl_row = next(r for r in result if r["callsign"] == "DL1ABC")
        self.assertEqual(dl_row["max_distance_km"], 800.0)

    def test_count_by_callsign_first_last_heard(self):
        result = self.service.get_cq_count_by_callsign()
        dl_row = next(r for r in result if r["callsign"] == "DL1ABC")
        self.assertIsNotNone(dl_row["first_heard"])
        self.assertIsNotNone(dl_row["last_heard"])
        self.assertLess(dl_row["first_heard"], dl_row["last_heard"])

    def test_count_by_callsign_with_filter(self):
        result = self.service.get_cq_count_by_callsign(filters={"band": "20m"})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["callsign"], "G4XYZ")


class StatisticsServiceCqCountByLocatorTest(TestCase):
    """Tests for get_cq_count_by_locator()."""

    def setUp(self):
        self.service = StatisticsService()
        run = make_import_run()

        make_signal(run, callsign="DL1ABC", locator="JN68", locator_country="Germany", band="40m", snr=-5, distance_km=500.0)
        make_signal(run, callsign="DL2XYZ", locator="JN68", locator_country="Germany", band="40m", snr=-10, distance_km=600.0)
        make_signal(run, callsign="G4XYZ", locator="IO91", locator_country="United Kingdom", band="20m", snr=-15, distance_km=1000.0)

    def test_count_by_locator(self):
        result = self.service.get_cq_count_by_locator()
        self.assertEqual(len(result), 2)
        # JN68 appears twice
        jn68 = next(r for r in result if r["locator"] == "JN68")
        self.assertEqual(jn68["count"], 2)

    def test_count_by_locator_avg_distance(self):
        result = self.service.get_cq_count_by_locator()
        jn68 = next(r for r in result if r["locator"] == "JN68")
        self.assertAlmostEqual(jn68["avg_distance_km"], 550.0, delta=1.0)

    def test_count_by_locator_country(self):
        result = self.service.get_cq_count_by_locator()
        io91 = next(r for r in result if r["locator"] == "IO91")
        self.assertEqual(io91["locator_country"], "United Kingdom")


class StatisticsServiceCqCountByBandTest(TestCase):
    """Tests for get_cq_count_by_band()."""

    def setUp(self):
        self.service = StatisticsService()
        run = make_import_run()

        make_signal(run, callsign="DL1ABC", band="40m", snr=-5, distance_km=500.0)
        make_signal(run, callsign="DL2XYZ", band="40m", snr=-10, distance_km=700.0)
        make_signal(run, callsign="G4XYZ", band="20m", snr=-8, distance_km=1000.0)

    def test_count_by_band(self):
        result = self.service.get_cq_count_by_band()
        self.assertEqual(len(result), 2)
        # 40m has 2 entries, should be first
        self.assertEqual(result[0]["band"], "40m")
        self.assertEqual(result[0]["count"], 2)

    def test_count_by_band_avg_distance(self):
        result = self.service.get_cq_count_by_band()
        m40 = next(r for r in result if r["band"] == "40m")
        self.assertAlmostEqual(m40["avg_distance_km"], 600.0, delta=1.0)

    def test_count_by_band_max_distance(self):
        result = self.service.get_cq_count_by_band()
        m40 = next(r for r in result if r["band"] == "40m")
        self.assertEqual(m40["max_distance_km"], 700.0)


class StatisticsServiceSnrStatsTest(TestCase):
    """Tests for get_snr_stats_by_band() and get_snr_stats_by_locator()."""

    def setUp(self):
        self.service = StatisticsService()
        run = make_import_run()

        make_signal(run, callsign="DL1ABC", band="40m", locator="JN68", snr=-5, distance_km=500.0)
        make_signal(run, callsign="DL2XYZ", band="40m", locator="JN68", snr=-20, distance_km=700.0)
        make_signal(run, callsign="G4XYZ", band="20m", locator="IO91", snr=-8, distance_km=1000.0)

    def test_snr_stats_by_band(self):
        result = self.service.get_snr_stats_by_band()
        self.assertEqual(len(result), 2)
        m40 = next(r for r in result if r["band"] == "40m")
        self.assertEqual(m40["min_snr"], -20)
        self.assertEqual(m40["max_snr"], -5)
        self.assertAlmostEqual(m40["avg_snr"], -12.5, delta=0.5)
        self.assertEqual(m40["count"], 2)

    def test_snr_stats_by_locator(self):
        result = self.service.get_snr_stats_by_locator()
        self.assertEqual(len(result), 2)
        jn68 = next(r for r in result if r["locator"] == "JN68")
        self.assertEqual(jn68["min_snr"], -20)
        self.assertEqual(jn68["max_snr"], -5)
        self.assertEqual(jn68["count"], 2)

    def test_snr_stats_by_band_with_filter(self):
        result = self.service.get_snr_stats_by_band(filters={"band": "20m"})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["band"], "20m")
        self.assertEqual(result[0]["min_snr"], -8)


class StatisticsServiceDistanceByHourTest(TestCase):
    """Tests for get_distance_stats_by_hour()."""

    def setUp(self):
        self.service = StatisticsService()
        run = make_import_run()

        ts_10 = datetime(2026, 4, 10, 10, 0, 0, tzinfo=dt_timezone.utc)
        ts_14 = datetime(2026, 4, 10, 14, 0, 0, tzinfo=dt_timezone.utc)
        ts_14b = datetime(2026, 4, 10, 14, 30, 0, tzinfo=dt_timezone.utc)

        make_signal(run, timestamp=ts_10, callsign="DL1ABC", band="40m", snr=-5, distance_km=500.0)
        make_signal(run, timestamp=ts_14, callsign="G4XYZ", band="20m", snr=-10, distance_km=1000.0)
        make_signal(run, timestamp=ts_14b, callsign="VE3ABC", band="20m", snr=-15, distance_km=3000.0)

    def test_distance_by_hour_buckets(self):
        result = self.service.get_distance_stats_by_hour()
        self.assertEqual(len(result), 2)
        hours = {r["hour"] for r in result}
        self.assertIn(10, hours)
        self.assertIn(14, hours)

    def test_distance_by_hour_max_distance(self):
        result = self.service.get_distance_stats_by_hour()
        h14 = next(r for r in result if r["hour"] == 14)
        self.assertEqual(h14["max_distance_km"], 3000.0)

    def test_distance_by_hour_avg(self):
        result = self.service.get_distance_stats_by_hour()
        h14 = next(r for r in result if r["hour"] == 14)
        self.assertAlmostEqual(h14["avg_distance_km"], 2000.0, delta=1.0)


class StatisticsServiceActivityByHourTest(TestCase):
    """Tests for get_activity_by_hour()."""

    def setUp(self):
        self.service = StatisticsService()
        run = make_import_run()

        ts_10 = datetime(2026, 4, 10, 10, 0, 0, tzinfo=dt_timezone.utc)
        ts_10b = datetime(2026, 4, 10, 10, 15, 0, tzinfo=dt_timezone.utc)
        ts_14 = datetime(2026, 4, 10, 14, 0, 0, tzinfo=dt_timezone.utc)

        make_signal(run, timestamp=ts_10, callsign="DL1ABC", locator="JN68", band="40m", snr=-5, distance_km=500.0)
        make_signal(run, timestamp=ts_10b, callsign="DL2XYZ", locator="JN68", band="40m", snr=-8, distance_km=600.0)
        make_signal(run, timestamp=ts_14, callsign="G4XYZ", locator="IO91", band="20m", snr=-12, distance_km=1000.0)

    def test_activity_by_hour_count(self):
        result = self.service.get_activity_by_hour()
        h10 = next(r for r in result if r["hour"] == 10)
        self.assertEqual(h10["count"], 2)

    def test_activity_by_hour_unique_callsigns(self):
        result = self.service.get_activity_by_hour()
        h10 = next(r for r in result if r["hour"] == 10)
        self.assertEqual(h10["unique_callsigns"], 2)

    def test_activity_by_hour_unique_locators(self):
        result = self.service.get_activity_by_hour()
        h10 = next(r for r in result if r["hour"] == 10)
        # Both signals are in JN68, so only 1 unique locator
        self.assertEqual(h10["unique_locators"], 1)


class StatisticsServiceTopDxTest(TestCase):
    """Tests for get_top_dx()."""

    def setUp(self):
        self.service = StatisticsService()
        run = make_import_run()

        make_signal(run, callsign="DL1ABC", locator="JN68", band="40m", snr=-5, distance_km=500.0)
        make_signal(run, callsign="VE3ABC", locator="FN03", band="20m", snr=-18, distance_km=7000.0)
        make_signal(run, callsign="ZL2ABC", locator="RF70", band="20m", snr=-22, distance_km=18000.0)

    def test_top_dx_ordering(self):
        result = self.service.get_top_dx()
        self.assertGreater(result[0]["distance_km"], result[1]["distance_km"])
        self.assertGreater(result[1]["distance_km"], result[2]["distance_km"])

    def test_top_dx_fields(self):
        result = self.service.get_top_dx()
        row = result[0]
        self.assertIn("timestamp", row)
        self.assertIn("callsign", row)
        self.assertIn("locator", row)
        self.assertIn("band", row)
        self.assertIn("snr", row)
        self.assertIn("distance_km", row)
        self.assertIn("qrz_url", row)

    def test_top_dx_limit(self):
        result = self.service.get_top_dx(limit=2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["callsign"], "ZL2ABC")

    def test_top_dx_excludes_null_distance(self):
        run = make_import_run()
        make_signal(run, callsign="NODIST", locator=None, band="40m", snr=-5, distance_km=None)
        result = self.service.get_top_dx()
        callsigns = [r["callsign"] for r in result]
        self.assertNotIn("NODIST", callsigns)

    def test_top_dx_with_filter(self):
        result = self.service.get_top_dx(filters={"band": "40m"})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["callsign"], "DL1ABC")


class StatisticsServiceFilterTest(TestCase):
    """Tests verifying various filter combinations."""

    def setUp(self):
        self.service = StatisticsService()
        run = make_import_run()

        ts1 = datetime(2026, 4, 1, 10, 0, 0, tzinfo=dt_timezone.utc)
        ts2 = datetime(2026, 4, 15, 10, 0, 0, tzinfo=dt_timezone.utc)

        make_signal(run, timestamp=ts1, callsign="DL1ABC", locator="JN68",
                    band="40m", mode="FT8", snr=-5, distance_km=500.0,
                    callsign_country="Germany", locator_country="Germany")
        make_signal(run, timestamp=ts2, callsign="G4XYZ", locator="IO91",
                    band="20m", mode="FT4", snr=-15, distance_km=2000.0,
                    callsign_country="United Kingdom", locator_country="United Kingdom")

    def test_filter_by_date_range(self):
        result = self.service.get_summary(filters={"date_from": "2026-04-10", "date_to": "2026-04-20"})
        self.assertEqual(result["cq_count"], 1)

    def test_filter_by_band(self):
        result = self.service.get_summary(filters={"band": "40m"})
        self.assertEqual(result["cq_count"], 1)

    def test_filter_by_mode(self):
        result = self.service.get_summary(filters={"mode": "FT4"})
        self.assertEqual(result["cq_count"], 1)

    def test_filter_by_callsign(self):
        result = self.service.get_summary(filters={"callsign": "DL1ABC"})
        self.assertEqual(result["cq_count"], 1)

    def test_filter_by_locator(self):
        result = self.service.get_summary(filters={"locator": "IO91"})
        self.assertEqual(result["cq_count"], 1)

    def test_filter_by_callsign_country(self):
        result = self.service.get_summary(filters={"callsign_country": "Germany"})
        self.assertEqual(result["cq_count"], 1)

    def test_filter_by_locator_country(self):
        result = self.service.get_summary(filters={"locator_country": "United Kingdom"})
        self.assertEqual(result["cq_count"], 1)

    def test_filter_by_min_distance(self):
        result = self.service.get_summary(filters={"min_distance_km": 1000})
        self.assertEqual(result["cq_count"], 1)

    def test_filter_by_max_distance(self):
        result = self.service.get_summary(filters={"max_distance_km": 1000})
        self.assertEqual(result["cq_count"], 1)

    def test_filter_by_snr_range(self):
        result = self.service.get_summary(filters={"min_snr": -10, "max_snr": 0})
        self.assertEqual(result["cq_count"], 1)

    def test_filter_no_results(self):
        result = self.service.get_summary(filters={"band": "10m"})
        self.assertEqual(result["cq_count"], 0)

    def test_filter_by_iso_datetime_string(self):
        """Test that ISO datetime strings (with timezone) are properly handled."""
        # This is the regression test for the bug where period=24h sends ISO datetime strings
        # Filter from April 10 to April 20 should only get the second signal (ts2)
        result = self.service.get_summary(filters={
            "date_from": "2026-04-10T00:00:00.000000+00:00",
            "date_to": "2026-04-20T23:59:59.999999+00:00"
        })
        self.assertEqual(result["cq_count"], 1)

    def test_filter_by_iso_datetime_string_no_microseconds(self):
        """Test ISO datetime strings without microseconds."""
        result = self.service.get_summary(filters={
            "date_from": "2026-04-01T00:00:00+00:00"
        })
        self.assertEqual(result["cq_count"], 2)

    def test_filter_date_from_datetime_object(self):
        """Test that datetime objects are properly handled."""
        from datetime import datetime, timezone as dt_timezone
        dt = datetime(2026, 4, 10, 0, 0, 0, tzinfo=dt_timezone.utc)
        result = self.service.get_summary(filters={"date_from": dt})
        self.assertEqual(result["cq_count"], 1)

    def test_filter_date_from_date_object(self):
        """Test that date objects are properly handled."""
        from datetime import date
        d = date(2026, 4, 10)
        result = self.service.get_summary(filters={"date_from": d})
        self.assertEqual(result["cq_count"], 1)

    def test_filter_invalid_date_ignored(self):
        """Test that invalid date filters are ignored instead of crashing."""
        # Invalid date should be ignored, so all signals should be returned
        result = self.service.get_summary(filters={"date_from": "invalid-date"})
        self.assertEqual(result["cq_count"], 2)

    def test_filter_by_datetime_from(self):
        """Test filtering by datetime_from for precise time filtering."""
        # Signal 1: 2026-04-01 10:00:00
        # Signal 2: 2026-04-15 10:00:00
        # Filter from April 1 at 11:00 should only get signal 2
        result = self.service.get_summary(filters={
            "datetime_from": "2026-04-01T11:00:00+00:00"
        })
        self.assertEqual(result["cq_count"], 1)

    def test_filter_by_datetime_to(self):
        """Test filtering by datetime_to for precise time filtering."""
        # Signal 1: 2026-04-01 10:00:00
        # Signal 2: 2026-04-15 10:00:00
        # Filter to April 1 at 11:00 should only get signal 1
        result = self.service.get_summary(filters={
            "datetime_to": "2026-04-01T11:00:00+00:00"
        })
        self.assertEqual(result["cq_count"], 1)

    def test_filter_by_datetime_range(self):
        """Test filtering by both datetime_from and datetime_to."""
        # Signal 1: 2026-04-01 10:00:00
        # Signal 2: 2026-04-15 10:00:00
        # Filter from April 1 at 09:00 to April 1 at 11:00 should only get signal 1
        result = self.service.get_summary(filters={
            "datetime_from": "2026-04-01T09:00:00+00:00",
            "datetime_to": "2026-04-01T11:00:00+00:00"
        })
        self.assertEqual(result["cq_count"], 1)

    def test_datetime_filter_takes_precedence_over_date_filter(self):
        """Test that datetime_from takes precedence over date_from."""
        # Signal 1: 2026-04-01 10:00:00
        # Signal 2: 2026-04-15 10:00:00
        # date_from would match both, but datetime_from should only match signal 2
        result = self.service.get_summary(filters={
            "date_from": "2026-04-01",
            "datetime_from": "2026-04-01T11:00:00+00:00"
        })
        self.assertEqual(result["cq_count"], 1)


class StatisticsServiceRecentCqsTest(TestCase):
    """Tests for get_recent_cqs()."""

    def setUp(self):
        self.service = StatisticsService()
        run = make_import_run()

        ts1 = datetime(2026, 4, 10, 10, 0, 0, tzinfo=dt_timezone.utc)
        ts2 = datetime(2026, 4, 10, 11, 0, 0, tzinfo=dt_timezone.utc)
        ts3 = datetime(2026, 4, 10, 12, 0, 0, tzinfo=dt_timezone.utc)

        make_signal(run, timestamp=ts1, callsign="DL1ABC", locator="JN68", band="40m", snr=-5, distance_km=500.0)
        make_signal(run, timestamp=ts2, callsign="G4XYZ", locator="IO91", band="20m", snr=-15, distance_km=1500.0)
        make_signal(run, timestamp=ts3, callsign="VE3ABC", locator="FN03", band="20m", snr=-20, distance_km=7000.0)

    def test_recent_cqs_returns_latest_first(self):
        result = self.service.get_recent_cqs(limit=10)
        self.assertEqual(len(result), 3)
        # Should be ordered by timestamp descending
        self.assertEqual(result[0]["callsign"], "VE3ABC")
        self.assertEqual(result[1]["callsign"], "G4XYZ")
        self.assertEqual(result[2]["callsign"], "DL1ABC")

    def test_recent_cqs_respects_limit(self):
        result = self.service.get_recent_cqs(limit=2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["callsign"], "VE3ABC")
        self.assertEqual(result[1]["callsign"], "G4XYZ")

    def test_recent_cqs_with_filters(self):
        result = self.service.get_recent_cqs(filters={"band": "20m"}, limit=10)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["callsign"], "VE3ABC")
        self.assertEqual(result[1]["callsign"], "G4XYZ")

    def test_recent_cqs_empty(self):
        result = self.service.get_recent_cqs(filters={"band": "10m"}, limit=10)
        self.assertEqual(len(result), 0)


class StatisticsServiceCurrentDxSummaryTest(TestCase):
    """Tests for get_current_dx_summary()."""

    def setUp(self):
        self.service = StatisticsService()
        run = make_import_run()

        # Create signals in the last 30 minutes
        now = timezone.now()
        ts1 = now - timezone.timedelta(minutes=10)
        ts2 = now - timezone.timedelta(minutes=20)
        ts3 = now - timezone.timedelta(minutes=30)

        make_signal(run, timestamp=ts1, callsign="DL1ABC", locator="JN68", locator_country="Germany", band="40m", snr=-5, distance_km=500.0)
        make_signal(run, timestamp=ts2, callsign="G4XYZ", locator="IO91", locator_country="United Kingdom", band="20m", snr=-15, distance_km=1500.0)
        make_signal(run, timestamp=ts3, callsign="VE3ABC", locator="FN03", locator_country="United States", band="20m", snr=-10, distance_km=7000.0)

    def test_current_dx_summary_counts(self):
        result = self.service.get_current_dx_summary(minutes=60)
        self.assertEqual(result["count"], 3)
        self.assertEqual(result["minutes"], 60)

    def test_current_dx_summary_distances(self):
        result = self.service.get_current_dx_summary(minutes=60)
        self.assertEqual(result["max_distance_km"], 7000.0)
        self.assertAlmostEqual(result["avg_distance_km"], 3000.0, delta=1.0)

    def test_current_dx_summary_snr(self):
        result = self.service.get_current_dx_summary(minutes=60)
        self.assertEqual(result["best_snr"], -5)

    def test_current_dx_summary_top_country(self):
        result = self.service.get_current_dx_summary(minutes=60)
        # All countries appear once, so any is valid
        self.assertIn(result["top_country"], ["Germany", "United Kingdom", "United States"])

    def test_current_dx_summary_narrow_window(self):
        # Only signals from last 15 minutes
        result = self.service.get_current_dx_summary(minutes=15)
        # Should get signals from 10 and 15 minutes ago (2 signals)
        # The 30-minute old signal should be excluded
        self.assertGreaterEqual(result["count"], 1)  # At least the most recent signal
        self.assertLessEqual(result["count"], 2)  # At most 2 signals

    def test_current_dx_summary_empty(self):
        # Create a new service with no recent data
        service = StatisticsService()
        result = service.get_current_dx_summary(minutes=1)
        self.assertEqual(result["count"], 0)
        self.assertIsNone(result["max_distance_km"])


class StatisticsServiceActivityByDirectionTest(TestCase):
    """Tests for get_activity_by_direction()."""

    def setUp(self):
        self.service = StatisticsService()
        run = make_import_run()

        ts = datetime(2026, 4, 10, 10, 0, 0, tzinfo=dt_timezone.utc)

        # Create signals from different directions
        # N: 0°, NE: 45°, E: 90°, SE: 135°, S: 180°, SW: 225°, W: 270°, NW: 315°
        make_signal(run, timestamp=ts, callsign="N1", locator="JN68", azimuth_deg=10.0, distance_km=500.0)
        make_signal(run, timestamp=ts, callsign="NE1", locator="JN69", azimuth_deg=45.0, distance_km=600.0)
        make_signal(run, timestamp=ts, callsign="NE2", locator="JN70", azimuth_deg=50.0, distance_km=700.0)
        make_signal(run, timestamp=ts, callsign="E1", locator="JN71", azimuth_deg=90.0, distance_km=800.0)
        make_signal(run, timestamp=ts, callsign="S1", locator="JN72", azimuth_deg=180.0, distance_km=900.0)
        make_signal(run, timestamp=ts, callsign="W1", locator="JN73", azimuth_deg=270.0, distance_km=1000.0)

    def test_activity_by_direction_groups_correctly(self):
        result = self.service.get_activity_by_direction()
        # Result should have 8 directions in order
        self.assertEqual(len(result), 8)
        directions = [r["direction"] for r in result]
        self.assertEqual(directions, ["N", "NE", "E", "SE", "S", "SW", "W", "NW"])

    def test_activity_by_direction_counts(self):
        result = self.service.get_activity_by_direction()
        result_dict = {r["direction"]: r for r in result}

        self.assertEqual(result_dict["N"]["count"], 1)
        self.assertEqual(result_dict["NE"]["count"], 2)
        self.assertEqual(result_dict["E"]["count"], 1)
        self.assertEqual(result_dict["SE"]["count"], 0)
        self.assertEqual(result_dict["S"]["count"], 1)
        self.assertEqual(result_dict["SW"]["count"], 0)
        self.assertEqual(result_dict["W"]["count"], 1)
        self.assertEqual(result_dict["NW"]["count"], 0)

    def test_activity_by_direction_avg_distance(self):
        result = self.service.get_activity_by_direction()
        result_dict = {r["direction"]: r for r in result}

        self.assertEqual(result_dict["N"]["avg_distance_km"], 500.0)
        self.assertAlmostEqual(result_dict["NE"]["avg_distance_km"], 650.0, delta=1.0)
        self.assertEqual(result_dict["E"]["avg_distance_km"], 800.0)

    def test_activity_by_direction_excludes_no_azimuth(self):
        # Create a signal without azimuth
        run = make_import_run()
        ts = datetime(2026, 4, 10, 10, 0, 0, tzinfo=dt_timezone.utc)
        make_signal(run, timestamp=ts, callsign="NO_AZ", locator="JN74", azimuth_deg=None, distance_km=1100.0)

        result = self.service.get_activity_by_direction()
        # Should still have 6 signals (excluding the one without azimuth)
        total_count = sum(r["count"] for r in result)
        self.assertEqual(total_count, 6)


class StatisticsServiceActivityByDirectionEmptyTest(TestCase):
    """Tests for get_activity_by_direction() with empty database."""

    def test_activity_by_direction_empty(self):
        # Test with empty data (no signals in database)
        service = StatisticsService()
        result = service.get_activity_by_direction()
        # Should still return 8 directions with 0 counts
        self.assertEqual(len(result), 8)
        total_count = sum(r["count"] for r in result)
        self.assertEqual(total_count, 0)


