"""
Central statistics service for PropScope.

Aggregates received CQ signals and provides data for dashboards,
reports, and notifications. Independent of UI, templates, and charts.
"""

from datetime import date, datetime

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
        datetime_from     – ISO datetime string, e.g. "2026-04-01T12:00:00+00:00"
        datetime_to       – ISO datetime string, e.g. "2026-04-30T23:59:59+00:00"
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

    def _normalize_date_value(self, value):
        """
        Normalize a date filter value to a date object.

        Accepts:
        - date objects (returned as-is)
        - datetime objects (returns .date())
        - ISO date strings "YYYY-MM-DD" (parsed to date)
        - ISO datetime strings with timezone (parsed and converted to date)

        Returns None if value cannot be parsed.
        """
        if isinstance(value, date):
            # Already a date object (or datetime which is subclass of date)
            if isinstance(value, datetime):
                return value.date()
            return value

        if isinstance(value, str):
            # Try parsing as ISO datetime first (supports timezone)
            try:
                dt = datetime.fromisoformat(value)
                return dt.date()
            except (ValueError, TypeError):
                pass

            # Try parsing as date string YYYY-MM-DD
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass

        # If we can't parse, return None (filter will be ignored)
        return None

    def _normalize_datetime_value(self, value):
        """
        Normalize a datetime filter value to a datetime object.

        Accepts:
        - datetime objects (returned as-is)
        - ISO datetime strings with timezone (parsed to datetime)

        Returns None if value cannot be parsed.
        """
        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            # Try parsing as ISO datetime (supports timezone)
            try:
                return datetime.fromisoformat(value)
            except (ValueError, TypeError):
                pass

        # If we can't parse, return None (filter will be ignored)
        return None

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

        # Datetime filters take precedence over date filters for more precise filtering
        if datetime_from := filters.get("datetime_from"):
            normalized_datetime = self._normalize_datetime_value(datetime_from)
            if normalized_datetime:
                queryset = queryset.filter(timestamp__gte=normalized_datetime)
        elif date_from := filters.get("date_from"):
            normalized_date = self._normalize_date_value(date_from)
            if normalized_date:
                queryset = queryset.filter(timestamp__date__gte=normalized_date)

        if datetime_to := filters.get("datetime_to"):
            normalized_datetime = self._normalize_datetime_value(datetime_to)
            if normalized_datetime:
                queryset = queryset.filter(timestamp__lte=normalized_datetime)
        elif date_to := filters.get("date_to"):
            normalized_date = self._normalize_date_value(date_to)
            if normalized_date:
                queryset = queryset.filter(timestamp__date__lte=normalized_date)

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
            qrz_url       – QRZ.com URL for the callsign
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
                qrz_url=Max("qrz_url"),  # Get any qrz_url (they should all be the same for a callsign)
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
                "qrz_url": row["qrz_url"],
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
        Return the furthest received CQ signals (deduplicated by callsign).

        Each callsign appears only once, showing the maximum distance achieved.

        Args:
            filters: Optional filter dictionary.
            limit:   Maximum number of results (default 20).

        Returns a list of dicts ordered by distance descending, each with:
            timestamp     – when the signal was received
            callsign      – callsign of the transmitting station
            locator       – Maidenhead locator
            locator_country – country from locator
            band          – band name
            snr           – signal-to-noise ratio
            distance_km   – distance in kilometres
            qrz_url       – QRZ.com URL for the callsign
        """
        qs = self._apply_filters(
            HeardSignal.objects.filter(distance_km__isnull=False),
            filters,
        )

        # Get all signals ordered by distance
        signals = qs.order_by("-distance_km").values(
            "timestamp",
            "callsign",
            "locator",
            "locator_country",
            "band",
            "snr",
            "distance_km",
            "qrz_url",
        )

        # Deduplicate by callsign, keeping the highest distance per callsign
        seen_callsigns = set()
        result = []

        for signal in signals:
            if signal["callsign"] not in seen_callsigns:
                result.append(signal)
                seen_callsigns.add(signal["callsign"])

            if len(result) >= limit:
                break

        return result

    def get_cq_count_by_continent(self, filters: dict | None = None) -> list[dict]:
        """
        Aggregate CQ signals by continent.

        Returns a list of dicts ordered by count descending, each with:
            continent   – continent name
            count       – number of CQ signals received
        """
        qs = self._apply_filters(HeardSignal.objects.all(), filters)

        rows = (
            qs.exclude(locator_continent__isnull=True)
            .exclude(locator_continent="")
            .values("locator_continent")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        return [
            {
                "continent": row["locator_continent"],
                "count": row["count"],
            }
            for row in rows
        ]

    def get_cq_count_by_callsign_country(self, filters: dict | None = None) -> list[dict]:
        """
        Aggregate CQ signals by callsign country.

        Returns a list of dicts ordered by count descending, each with:
            country   – country name (from callsign prefix)
            count     – number of CQ signals received
        """
        qs = self._apply_filters(HeardSignal.objects.all(), filters)

        rows = (
            qs.exclude(callsign_country__isnull=True)
            .exclude(callsign_country="")
            .values("callsign_country")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        return [
            {
                "country": row["callsign_country"],
                "count": row["count"],
            }
            for row in rows
        ]

    def get_best_dx_time(self, filters: dict | None = None) -> dict | None:
        """
        Determine the best hour for DX (maximum distance achieved).

        Returns a dict with:
            hour          – hour of day (0–23) with the best DX
            distance_km   – maximum distance achieved in that hour
            count         – number of signals in that hour

        Returns None if no data is available.
        """
        distance_stats = self.get_distance_stats_by_hour(filters)

        if not distance_stats:
            return None

        # Find the hour with the maximum distance
        best_hour = max(
            distance_stats,
            key=lambda x: x["max_distance_km"] if x["max_distance_km"] else 0
        )

        return {
            "hour": best_hour["hour"],
            "distance_km": best_hour["max_distance_km"],
            "count": best_hour["count"],
        }

    def get_recent_cqs(self, filters: dict | None = None, limit: int = 20) -> list[dict]:
        """
        Return the most recently received CQ signals.

        Args:
            filters: Optional filter dictionary.
            limit:   Maximum number of results (default 20).

        Returns a list of dicts ordered by timestamp descending, each with:
            timestamp       – when the signal was received
            callsign        – callsign of the transmitting station
            locator         – Maidenhead locator
            locator_country – country from locator
            band            – band name
            snr             – signal-to-noise ratio
            distance_km     – distance in kilometres
            qrz_url         – QRZ.com URL for the callsign
        """
        qs = self._apply_filters(HeardSignal.objects.all(), filters)

        signals = qs.order_by("-timestamp").values(
            "timestamp",
            "callsign",
            "locator",
            "locator_country",
            "band",
            "snr",
            "distance_km",
            "qrz_url",
        )[:limit]

        return list(signals)

    def get_current_dx_summary(self, minutes: int = 60) -> dict:
        """
        Return a summary of current DX activity in the last N minutes.

        Args:
            minutes: Time window in minutes (default 60).

        Returns a dict with:
            max_distance_km   – maximum distance in the time window
            avg_distance_km   – average distance
            count             – number of CQ signals
            top_country       – most active country
            best_snr          – strongest signal SNR

        Returns empty values if no data is available.
        """
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        datetime_from = now - timedelta(minutes=minutes)

        filters = {"datetime_from": datetime_from.isoformat()}
        qs = self._apply_filters(HeardSignal.objects.all(), filters)

        # Get aggregate stats
        agg = qs.aggregate(
            max_distance_km=Max("distance_km"),
            avg_distance_km=Avg("distance_km"),
            count=Count("id"),
            best_snr=Max("snr"),
        )

        # Get most active country
        top_country_row = (
            qs.exclude(locator_country__isnull=True)
            .exclude(locator_country="")
            .values("locator_country")
            .annotate(count=Count("id"))
            .order_by("-count")
            .first()
        )

        return {
            "max_distance_km": agg["max_distance_km"],
            "avg_distance_km": round(agg["avg_distance_km"], 1) if agg["avg_distance_km"] is not None else None,
            "count": agg["count"],
            "top_country": top_country_row["locator_country"] if top_country_row else None,
            "best_snr": agg["best_snr"],
            "minutes": minutes,
        }

    def get_activity_by_direction(self, filters: dict | None = None) -> list[dict]:
        """
        Aggregate CQ signals by direction (azimuth buckets).

        Groups signals into 8 compass directions: N, NE, E, SE, S, SW, W, NW.

        Uses distinct callsign count to avoid distortion from stations that
        send multiple CQ frames (e.g., FT8 beacon stations).

        Returns a list of dicts ordered by direction, each with:
            direction       – compass direction (N, NE, E, SE, S, SW, W, NW)
            count           – number of distinct callsigns from that direction
            avg_distance_km – average distance for that direction

        Signals without azimuth data are excluded.
        """
        qs = self._apply_filters(
            HeardSignal.objects.filter(azimuth_deg__isnull=False),
            filters,
        )

        from django.db.models import Case, When, Value, CharField

        # Bucket azimuth into 8 directions
        # N: 337.5-22.5, NE: 22.5-67.5, E: 67.5-112.5, SE: 112.5-157.5
        # S: 157.5-202.5, SW: 202.5-247.5, W: 247.5-292.5, NW: 292.5-337.5
        direction_buckets = Case(
            When(azimuth_deg__gte=337.5, then=Value("N")),
            When(azimuth_deg__lt=22.5, then=Value("N")),
            When(azimuth_deg__gte=22.5, azimuth_deg__lt=67.5, then=Value("NE")),
            When(azimuth_deg__gte=67.5, azimuth_deg__lt=112.5, then=Value("E")),
            When(azimuth_deg__gte=112.5, azimuth_deg__lt=157.5, then=Value("SE")),
            When(azimuth_deg__gte=157.5, azimuth_deg__lt=202.5, then=Value("S")),
            When(azimuth_deg__gte=202.5, azimuth_deg__lt=247.5, then=Value("SW")),
            When(azimuth_deg__gte=247.5, azimuth_deg__lt=292.5, then=Value("W")),
            When(azimuth_deg__gte=292.5, azimuth_deg__lt=337.5, then=Value("NW")),
            default=Value("Unknown"),
            output_field=CharField(),
        )

        rows = (
            qs.annotate(direction=direction_buckets)
            .values("direction")
            .annotate(
                count=Count("callsign", distinct=True),
                avg_distance_km=Avg("distance_km"),
            )
            .order_by("direction")
        )

        # Define the order of directions
        direction_order = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        result_dict = {row["direction"]: row for row in rows}

        # Return in proper compass order
        return [
            {
                "direction": direction,
                "count": result_dict[direction]["count"] if direction in result_dict else 0,
                "avg_distance_km": round(result_dict[direction]["avg_distance_km"], 1) if direction in result_dict and result_dict[direction]["avg_distance_km"] is not None else None,
            }
            for direction in direction_order
        ]

    def get_propagation_heatmap(self, filters: dict | None = None) -> dict:
        """
        Aggregate CQ signals by hour (UTC) and direction for heatmap visualization.

        Creates a 2D heatmap showing signal activity patterns:
        - X-axis: Hour of day (0-23, UTC)
        - Y-axis: Direction (N, NE, E, SE, S, SW, W, NW)
        - Value: Count of distinct callsigns (to avoid beacon distortion)

        This visualization helps identify:
        - Propagation patterns over the day
        - Greyline effects (e.g., West at night, East in morning)
        - Antenna characteristics across time

        Returns a dict with:
            hours      – list of all hours 0-23
            directions – list of directions [N, NE, E, SE, S, SW, W, NW]
            data       – 2D array [hour][direction] with counts
            max_count  – maximum count value (for color scaling)

        Signals without azimuth data are excluded.
        """
        qs = self._apply_filters(
            HeardSignal.objects.filter(azimuth_deg__isnull=False),
            filters,
        )

        from django.db.models import Case, When, Value, CharField
        from django.db.models.functions import ExtractHour

        # Bucket azimuth into 8 directions (same as get_activity_by_direction)
        direction_buckets = Case(
            When(azimuth_deg__gte=337.5, then=Value("N")),
            When(azimuth_deg__lt=22.5, then=Value("N")),
            When(azimuth_deg__gte=22.5, azimuth_deg__lt=67.5, then=Value("NE")),
            When(azimuth_deg__gte=67.5, azimuth_deg__lt=112.5, then=Value("E")),
            When(azimuth_deg__gte=112.5, azimuth_deg__lt=157.5, then=Value("SE")),
            When(azimuth_deg__gte=157.5, azimuth_deg__lt=202.5, then=Value("S")),
            When(azimuth_deg__gte=202.5, azimuth_deg__lt=247.5, then=Value("SW")),
            When(azimuth_deg__gte=247.5, azimuth_deg__lt=292.5, then=Value("W")),
            When(azimuth_deg__gte=292.5, azimuth_deg__lt=337.5, then=Value("NW")),
            default=Value("Unknown"),
            output_field=CharField(),
        )

        # Annotate with hour and direction, then aggregate
        rows = (
            qs.annotate(
                hour=ExtractHour("timestamp"),
                direction=direction_buckets,
            )
            .values("hour", "direction")
            .annotate(count=Count("callsign", distinct=True))
        )

        # Build 2D data structure
        direction_order = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        hours = list(range(24))

        # Initialize data structure with zeros
        data_dict = {hour: {direction: 0 for direction in direction_order} for hour in hours}

        # Fill in actual counts
        for row in rows:
            hour = row["hour"]
            direction = row["direction"]
            count = row["count"]
            if direction in direction_order and hour in hours:
                data_dict[hour][direction] = count

        # Convert to 2D array format for Chart.js
        # Each element is [hour, direction_index, count]
        max_count = 0
        heatmap_points = []

        for hour in hours:
            for dir_idx, direction in enumerate(direction_order):
                count = data_dict[hour][direction]
                heatmap_points.append({
                    "hour": hour,
                    "direction": direction,
                    "direction_index": dir_idx,
                    "count": count,
                })
                if count > max_count:
                    max_count = count

        return {
            "hours": hours,
            "directions": direction_order,
            "data": heatmap_points,
            "max_count": max_count,
        }

    def get_map_spots(self, filters=None):
        """
        Get spots data for map visualization with coordinates.

        Returns distinct callsign + locator + band spots with all relevant fields.
        Only includes spots with valid coordinates (locator_lat and locator_lon).

        Args:
            filters: Optional dict with filter criteria (see class docstring)

        Returns:
            List of dicts with spot information including coordinates
        """
        queryset = self._apply_filters(HeardSignal.objects.all(), filters)

        # Only include spots with valid coordinates
        queryset = queryset.filter(
            locator_lat__isnull=False,
            locator_lon__isnull=False
        )

        # Get distinct spots by callsign + locator + band
        # Use the latest (most recent) spot for each combination
        spots = []
        seen = set()

        for signal in queryset.order_by('-timestamp'):
            key = (signal.callsign, signal.locator, signal.band)
            if key not in seen:
                seen.add(key)
                spots.append({
                    'timestamp': signal.timestamp.isoformat(),
                    'callsign': signal.callsign,
                    'locator': signal.locator,
                    'lat': signal.locator_lat,
                    'lon': signal.locator_lon,
                    'country': signal.locator_country or signal.callsign_country or 'Unknown',
                    'band': signal.band,
                    'snr': signal.snr,
                    'distance_km': signal.distance_km,
                    'qrz_url': signal.qrz_url,
                    'locator_map_url': signal.locator_map_url,
                })

        return spots

    # ========== Station-specific statistics ==========

    def get_station_summary(self, callsign: str, filters: dict | None = None) -> dict:
        """
        Get summary statistics for a specific station.

        Args:
            callsign: The callsign to analyze
            filters: Optional additional filters (date range, band, etc.)

        Returns:
            Dict with station summary including:
            - total_signals: Total number of received signals
            - first_heard: First time this station was heard
            - last_heard: Last time this station was heard
            - avg_snr: Average SNR
            - max_snr: Maximum SNR
            - min_snr: Minimum SNR
            - avg_distance_km: Average distance
            - max_distance_km: Maximum distance
            - unique_bands: Number of unique bands
            - unique_locators: Number of unique locators
        """
        # Start with base filters
        if filters is None:
            filters = {}

        # Add callsign filter
        station_filters = filters.copy()
        station_filters['callsign'] = callsign

        queryset = self._apply_filters(HeardSignal.objects.all(), station_filters)

        if not queryset.exists():
            return {
                'callsign': callsign,
                'total_signals': 0,
                'first_heard': None,
                'last_heard': None,
                'avg_snr': None,
                'max_snr': None,
                'min_snr': None,
                'avg_distance_km': None,
                'max_distance_km': None,
                'unique_bands': 0,
                'unique_locators': 0,
            }

        # Aggregate statistics
        stats = queryset.aggregate(
            total_signals=Count('id'),
            first_heard=Min('timestamp'),
            last_heard=Max('timestamp'),
            avg_snr=Avg('snr'),
            max_snr=Max('snr'),
            min_snr=Min('snr'),
            avg_distance_km=Avg('distance_km'),
            max_distance_km=Max('distance_km'),
            unique_bands=Count('band', distinct=True),
            unique_locators=Count('locator', distinct=True),
        )

        # Get the most recent signal for additional info
        latest_signal = queryset.order_by('-timestamp').first()

        return {
            'callsign': callsign,
            'total_signals': stats['total_signals'],
            'first_heard': stats['first_heard'],
            'last_heard': stats['last_heard'],
            'avg_snr': round(stats['avg_snr'], 1) if stats['avg_snr'] is not None else None,
            'max_snr': stats['max_snr'],
            'min_snr': stats['min_snr'],
            'avg_distance_km': round(stats['avg_distance_km'], 1) if stats['avg_distance_km'] is not None else None,
            'max_distance_km': round(stats['max_distance_km'], 1) if stats['max_distance_km'] is not None else None,
            'unique_bands': stats['unique_bands'],
            'unique_locators': stats['unique_locators'],
            'qrz_url': latest_signal.qrz_url if latest_signal else None,
            'locator': latest_signal.locator if latest_signal else None,
            'locator_country': latest_signal.locator_country if latest_signal else None,
            'locator_continent': latest_signal.locator_continent if latest_signal else None,
            'callsign_country': latest_signal.callsign_country if latest_signal else None,
            'callsign_continent': latest_signal.callsign_continent if latest_signal else None,
        }

    def get_station_snr_over_time(self, callsign: str, filters: dict | None = None) -> list[dict]:
        """
        Get SNR values over time for a specific station.

        Args:
            callsign: The callsign to analyze
            filters: Optional additional filters

        Returns:
            List of dicts with timestamp and snr
        """
        if filters is None:
            filters = {}

        station_filters = filters.copy()
        station_filters['callsign'] = callsign

        queryset = self._apply_filters(HeardSignal.objects.all(), station_filters)
        queryset = queryset.order_by('timestamp')

        return [
            {
                'timestamp': signal.timestamp.isoformat(),
                'snr': signal.snr,
                'band': signal.band,
            }
            for signal in queryset
        ]

    def get_station_activity_by_hour(self, callsign: str, filters: dict | None = None) -> list[dict]:
        """
        Get signal count by hour of day for a specific station.

        Args:
            callsign: The callsign to analyze
            filters: Optional additional filters

        Returns:
            List of dicts with hour (0-23) and count
        """
        if filters is None:
            filters = {}

        station_filters = filters.copy()
        station_filters['callsign'] = callsign

        queryset = self._apply_filters(HeardSignal.objects.all(), station_filters)

        # Aggregate by hour
        rows = (
            queryset
            .annotate(hour=ExtractHour('timestamp'))
            .values('hour')
            .annotate(count=Count('id'))
            .order_by('hour')
        )

        # Initialize all hours with 0
        result = [{'hour': h, 'count': 0} for h in range(24)]

        # Fill in actual counts
        for row in rows:
            hour = row['hour']
            if 0 <= hour < 24:
                result[hour]['count'] = row['count']

        return result

    def get_station_snr_by_hour(self, callsign: str, filters: dict | None = None) -> list[dict]:
        """
        Get average SNR by hour of day for a specific station.

        Args:
            callsign: The callsign to analyze
            filters: Optional additional filters

        Returns:
            List of dicts with hour (0-23), avg_snr, and count
        """
        if filters is None:
            filters = {}

        station_filters = filters.copy()
        station_filters['callsign'] = callsign

        queryset = self._apply_filters(HeardSignal.objects.all(), station_filters)

        # Aggregate by hour
        rows = (
            queryset
            .annotate(hour=ExtractHour('timestamp'))
            .values('hour')
            .annotate(
                avg_snr=Avg('snr'),
                count=Count('id')
            )
            .order_by('hour')
        )

        # Initialize all hours with 0
        result = [{'hour': h, 'avg_snr': None, 'count': 0} for h in range(24)]

        # Fill in actual values
        for row in rows:
            hour = row['hour']
            if 0 <= hour < 24:
                result[hour]['avg_snr'] = round(row['avg_snr'], 1) if row['avg_snr'] is not None else None
                result[hour]['count'] = row['count']

        return result

    def get_station_band_distribution(self, callsign: str, filters: dict | None = None) -> list[dict]:
        """
        Get signal count by band for a specific station.

        Args:
            callsign: The callsign to analyze
            filters: Optional additional filters

        Returns:
            List of dicts with band, count, avg_snr, sorted by count descending
        """
        if filters is None:
            filters = {}

        station_filters = filters.copy()
        station_filters['callsign'] = callsign

        queryset = self._apply_filters(HeardSignal.objects.all(), station_filters)

        rows = (
            queryset
            .values('band')
            .annotate(
                count=Count('id'),
                avg_snr=Avg('snr')
            )
            .order_by('-count')
        )

        return [
            {
                'band': row['band'],
                'count': row['count'],
                'avg_snr': round(row['avg_snr'], 1) if row['avg_snr'] is not None else None,
            }
            for row in rows
        ]

    def get_recent_signals_for_station(self, callsign: str, limit: int = 50, filters: dict | None = None) -> list[dict]:
        """
        Get recent signals for a specific station.

        Args:
            callsign: The callsign to analyze
            limit: Maximum number of signals to return
            filters: Optional additional filters

        Returns:
            List of dicts with signal information
        """
        if filters is None:
            filters = {}

        station_filters = filters.copy()
        station_filters['callsign'] = callsign

        queryset = self._apply_filters(HeardSignal.objects.all(), station_filters)
        queryset = queryset.order_by('-timestamp')[:limit]

        return [
            {
                'timestamp': signal.timestamp.isoformat(),
                'band': signal.band,
                'mode': signal.mode,
                'snr': signal.snr,
                'locator': signal.locator,
                'distance_km': round(signal.distance_km, 1) if signal.distance_km is not None else None,
                'azimuth_deg': round(signal.azimuth_deg, 1) if signal.azimuth_deg is not None else None,
                'raw_message': signal.raw_message,
            }
            for signal in queryset
        ]

