"""
Central statistics service for PropScope.

Aggregates received CQ signals and provides data for dashboards,
reports, and notifications. Independent of UI, templates, and charts.
"""

from django.db.models import (
    Avg,
    Count,
    Max,
    Min,
    Q,
)
from django.db.models.functions import ExtractHour

from apps.cq.models import HeardSignal


class StatisticsService:
    """
    Central service for aggregating CQ signal statistics.

    Accepts an optional filter dictionary and returns plain Python
    dictionaries / lists – no template or UI logic.

    Supported filter keys:
        date_from         – ISO date string, e.g. "2026-04-01"
        date_to           – ISO date string, e.g. "2026-04-30"
        band              – band name, e.g. "40m"
        mode              – mode string, e.g. "FT8"
        callsign          – exact callsign match
        locator           – exact locator match
        callsign_country  – country from callsign prefix
        locator_country   – country from locator
        min_distance_km   – minimum distance in km
        max_distance_km   – maximum distance in km
        min_snr           – minimum SNR in dB
        max_snr           – maximum SNR in dB
    """

    def _apply_filters(self, queryset, filters: dict | None = None):
        """
        Apply filter dictionary to a HeardSignal queryset.

        Args:
            queryset: Base HeardSignal queryset.
            filters:  Optional dict with filter keys described above.

        Returns:
            Filtered queryset.
        """
        if not filters:
            return queryset

        if date_from := filters.get("date_from"):
            queryset = queryset.filter(timestamp__date__gte=date_from)

        if date_to := filters.get("date_to"):
            queryset = queryset.filter(timestamp__date__lte=date_to)

        if band := filters.get("band"):
            queryset = queryset.filter(band=band)

        if mode := filters.get("mode"):
            queryset = queryset.filter(mode=mode)

        if callsign := filters.get("callsign"):
            queryset = queryset.filter(callsign=callsign)

        if locator := filters.get("locator"):
            queryset = queryset.filter(locator=locator)

        if callsign_country := filters.get("callsign_country"):
            queryset = queryset.filter(callsign_country=callsign_country)

        if locator_country := filters.get("locator_country"):
            queryset = queryset.filter(
                Q(locator_country=locator_country) | Q(locator_alt_country=locator_country)
            )

        if min_distance_km := filters.get("min_distance_km"):
            queryset = queryset.filter(distance_km__gte=min_distance_km)

        if max_distance_km := filters.get("max_distance_km"):
            queryset = queryset.filter(distance_km__lte=max_distance_km)

        if min_snr := filters.get("min_snr"):
            queryset = queryset.filter(snr__gte=min_snr)

        if max_snr := filters.get("max_snr"):
            queryset = queryset.filter(snr__lte=max_snr)

        return queryset

    def get_summary(self, filters: dict | None = None) -> dict:
        """
        Return a compact overall summary of received CQ signals.

        Returns a dict with:
            cq_count          – total number of received CQ signals
            unique_callsigns  – number of distinct callsigns
            unique_locators   – number of distinct locators
            unique_bands      – number of distinct bands
            min_distance_km   – minimum observed distance (or None)
            max_distance_km   – maximum observed distance (or None)
            avg_distance_km   – average distance (or None)
            min_snr           – minimum SNR
            max_snr           – maximum SNR
            avg_snr           – average SNR (or None)
        """
        qs = self._apply_filters(HeardSignal.objects.all(), filters)

        agg = qs.aggregate(
            cq_count=Count("id"),
            unique_callsigns=Count("callsign", distinct=True),
            unique_locators=Count("locator", distinct=True),
            unique_bands=Count("band", distinct=True),
            min_distance_km=Min("distance_km"),
            max_distance_km=Max("distance_km"),
            avg_distance_km=Avg("distance_km"),
            min_snr=Min("snr"),
            max_snr=Max("snr"),
            avg_snr=Avg("snr"),
        )

        if agg["avg_distance_km"] is not None:
            agg["avg_distance_km"] = round(agg["avg_distance_km"], 1)
        if agg["avg_snr"] is not None:
            agg["avg_snr"] = round(agg["avg_snr"], 1)

        return agg

    def get_cq_count_by_callsign(self, filters: dict | None = None) -> list[dict]:
        """
        Aggregate CQ signals by callsign.

        Returns a list of dicts ordered by count descending, each with:
            callsign      – the callsign
            count         – number of CQ signals received
            first_heard   – earliest timestamp
            last_heard    – latest timestamp
            avg_snr       – average SNR
            max_distance_km – maximum observed distance
        """
        qs = self._apply_filters(HeardSignal.objects.all(), filters)

        rows = (
            qs.values("callsign")
            .annotate(
                count=Count("id"),
                first_heard=Min("timestamp"),
                last_heard=Max("timestamp"),
                avg_snr=Avg("snr"),
                max_distance_km=Max("distance_km"),
            )
            .order_by("-count")
        )

        return [
            {
                "callsign": row["callsign"],
                "count": row["count"],
                "first_heard": row["first_heard"],
                "last_heard": row["last_heard"],
                "avg_snr": round(row["avg_snr"], 1) if row["avg_snr"] is not None else None,
                "max_distance_km": row["max_distance_km"],
            }
            for row in rows
        ]

    def get_cq_count_by_locator(self, filters: dict | None = None) -> list[dict]:
        """
        Aggregate CQ signals by Maidenhead locator.

        Returns a list of dicts ordered by count descending, each with:
            locator           – the locator square
            count             – number of CQ signals received
            avg_snr           – average SNR
            avg_distance_km   – average distance
            max_distance_km   – maximum distance
            locator_country   – country from locator (first non-null value)
        """
        qs = self._apply_filters(HeardSignal.objects.all(), filters)

        rows = (
            qs.values("locator", "locator_country")
            .annotate(
                count=Count("id"),
                avg_snr=Avg("snr"),
                avg_distance_km=Avg("distance_km"),
                max_distance_km=Max("distance_km"),
            )
            .order_by("-count")
        )

        return [
            {
                "locator": row["locator"],
                "count": row["count"],
                "avg_snr": round(row["avg_snr"], 1) if row["avg_snr"] is not None else None,
                "avg_distance_km": round(row["avg_distance_km"], 1) if row["avg_distance_km"] is not None else None,
                "max_distance_km": row["max_distance_km"],
                "locator_country": row["locator_country"],
            }
            for row in rows
        ]

    def get_cq_count_by_band(self, filters: dict | None = None) -> list[dict]:
        """
        Aggregate CQ signals by band.

        Returns a list of dicts ordered by count descending, each with:
            band              – band name (e.g. "40m")
            count             – number of CQ signals received
            avg_snr           – average SNR
            avg_distance_km   – average distance
            max_distance_km   – maximum distance
        """
        qs = self._apply_filters(HeardSignal.objects.all(), filters)

        rows = (
            qs.values("band")
            .annotate(
                count=Count("id"),
                avg_snr=Avg("snr"),
                avg_distance_km=Avg("distance_km"),
                max_distance_km=Max("distance_km"),
            )
            .order_by("-count")
        )

        return [
            {
                "band": row["band"],
                "count": row["count"],
                "avg_snr": round(row["avg_snr"], 1) if row["avg_snr"] is not None else None,
                "avg_distance_km": round(row["avg_distance_km"], 1) if row["avg_distance_km"] is not None else None,
                "max_distance_km": row["max_distance_km"],
            }
            for row in rows
        ]

    def get_snr_stats_by_band(self, filters: dict | None = None) -> list[dict]:
        """
        SNR statistics grouped by band.

        Returns a list of dicts ordered by band, each with:
            band    – band name
            min_snr – minimum SNR
            max_snr – maximum SNR
            avg_snr – average SNR
            count   – number of signals
        """
        qs = self._apply_filters(HeardSignal.objects.all(), filters)

        rows = (
            qs.values("band")
            .annotate(
                min_snr=Min("snr"),
                max_snr=Max("snr"),
                avg_snr=Avg("snr"),
                count=Count("id"),
            )
            .order_by("band")
        )

        return [
            {
                "band": row["band"],
                "min_snr": row["min_snr"],
                "max_snr": row["max_snr"],
                "avg_snr": round(row["avg_snr"], 1) if row["avg_snr"] is not None else None,
                "count": row["count"],
            }
            for row in rows
        ]

    def get_snr_stats_by_locator(self, filters: dict | None = None) -> list[dict]:
        """
        SNR statistics grouped by locator.

        Returns a list of dicts ordered by count descending, each with:
            locator – locator square
            min_snr – minimum SNR
            max_snr – maximum SNR
            avg_snr – average SNR
            count   – number of signals
        """
        qs = self._apply_filters(HeardSignal.objects.all(), filters)

        rows = (
            qs.values("locator")
            .annotate(
                min_snr=Min("snr"),
                max_snr=Max("snr"),
                avg_snr=Avg("snr"),
                count=Count("id"),
            )
            .order_by("-count")
        )

        return [
            {
                "locator": row["locator"],
                "min_snr": row["min_snr"],
                "max_snr": row["max_snr"],
                "avg_snr": round(row["avg_snr"], 1) if row["avg_snr"] is not None else None,
                "count": row["count"],
            }
            for row in rows
        ]

    def get_distance_stats_by_hour(self, filters: dict | None = None) -> list[dict]:
        """
        Distance statistics grouped by hour of day (0–23).

        Returns a list of dicts ordered by hour, each with:
            hour              – hour of day (0–23)
            count             – number of signals
            avg_distance_km   – average distance
            max_distance_km   – maximum distance
            avg_snr           – average SNR
        """
        qs = self._apply_filters(HeardSignal.objects.all(), filters)

        rows = (
            qs.annotate(hour=ExtractHour("timestamp"))
            .values("hour")
            .annotate(
                count=Count("id"),
                avg_distance_km=Avg("distance_km"),
                max_distance_km=Max("distance_km"),
                avg_snr=Avg("snr"),
            )
            .order_by("hour")
        )

        return [
            {
                "hour": row["hour"],
                "count": row["count"],
                "avg_distance_km": round(row["avg_distance_km"], 1) if row["avg_distance_km"] is not None else None,
                "max_distance_km": row["max_distance_km"],
                "avg_snr": round(row["avg_snr"], 1) if row["avg_snr"] is not None else None,
            }
            for row in rows
        ]

    def get_activity_by_hour(self, filters: dict | None = None) -> list[dict]:
        """
        Activity statistics grouped by hour of day (0–23).

        Returns a list of dicts ordered by hour, each with:
            hour               – hour of day (0–23)
            count              – number of CQ signals
            unique_callsigns   – number of distinct callsigns
            unique_locators    – number of distinct locators
        """
        qs = self._apply_filters(HeardSignal.objects.all(), filters)

        rows = (
            qs.annotate(hour=ExtractHour("timestamp"))
            .values("hour")
            .annotate(
                count=Count("id"),
                unique_callsigns=Count("callsign", distinct=True),
                unique_locators=Count("locator", distinct=True),
            )
            .order_by("hour")
        )

        return [
            {
                "hour": row["hour"],
                "count": row["count"],
                "unique_callsigns": row["unique_callsigns"],
                "unique_locators": row["unique_locators"],
            }
            for row in rows
        ]

    def get_top_dx(self, filters: dict | None = None, limit: int = 20) -> list[dict]:
        """
        Return the furthest received CQ signals.

        Args:
            filters: Optional filter dictionary.
            limit:   Maximum number of results (default 20).

        Returns a list of dicts ordered by distance descending, each with:
            timestamp     – when the signal was received
            callsign      – callsign of the transmitting station
            locator       – Maidenhead locator
            band          – band name
            snr           – signal-to-noise ratio
            distance_km   – distance in kilometres
            qrz_url       – QRZ.com URL for the callsign
        """
        qs = self._apply_filters(
            HeardSignal.objects.filter(distance_km__isnull=False),
            filters,
        )

        signals = qs.order_by("-distance_km").values(
            "timestamp",
            "callsign",
            "locator",
            "band",
            "snr",
            "distance_km",
            "qrz_url",
        )[:limit]

        return list(signals)
