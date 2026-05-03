from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import timedelta
import json
from apps.analysis.services import StatisticsService
from apps.geo.forms import MaidenheadAreaForm
from apps.geo.services import MaidenheadService, GeoService


def home(request):
    """Home page view."""
    return render(request, 'home.html')


def dashboard(request):
    """Main dashboard view with all statistics and charts."""
    stats_service = StatisticsService()

    # Get filter parameters from request
    filters = {}
    period = request.GET.get('period')

    # Calculate date range based on period
    if period:
        now = timezone.now()
        if period == 'today':
            filters['date_from'] = now.date().isoformat()
        elif period == '1h':
            filters['datetime_from'] = (now - timedelta(hours=1)).isoformat()
        elif period == '3h':
            filters['datetime_from'] = (now - timedelta(hours=3)).isoformat()
        elif period == '6h':
            filters['datetime_from'] = (now - timedelta(hours=6)).isoformat()
        elif period == '12h':
            filters['datetime_from'] = (now - timedelta(hours=12)).isoformat()
        elif period == '24h':
            filters['datetime_from'] = (now - timedelta(hours=24)).isoformat()
        elif period == '7d':
            filters['date_from'] = (now - timedelta(days=7)).date().isoformat()
        elif period == '30d':
            filters['date_from'] = (now - timedelta(days=30)).date().isoformat()

    # Allow manual date filters to override period
    if date_from := request.GET.get('date_from'):
        filters['date_from'] = date_from
        period = None  # Clear period if manual dates are used
    if date_to := request.GET.get('date_to'):
        filters['date_to'] = date_to
        period = None

    # Get DX mode from request
    dx_mode = request.GET.get('dx_mode') == 'true'

    # Apply DX filter if enabled
    heatmap_filters = filters.copy()
    if dx_mode:
        heatmap_filters['min_distance_km'] = 3000

    # Get all dashboard data
    summary = stats_service.get_summary(filters)
    activity_by_hour = stats_service.get_activity_by_hour(filters)
    distance_by_hour = stats_service.get_distance_stats_by_hour(filters)
    band_activity = stats_service.get_cq_count_by_band(filters)
    continent_activity = stats_service.get_cq_count_by_continent(filters)
    best_dx_time = stats_service.get_best_dx_time(filters)
    top_dx = stats_service.get_top_dx(filters, limit=20)
    top_callsigns = stats_service.get_cq_count_by_callsign(filters)[:10]
    top_locators = stats_service.get_cq_count_by_locator(filters)[:10]

    # New features
    recent_cqs = stats_service.get_recent_cqs(filters, limit=20)
    dx_now = stats_service.get_current_dx_summary(minutes=60)
    direction_activity = stats_service.get_activity_by_direction(filters)
    propagation_heatmap = stats_service.get_propagation_heatmap(heatmap_filters)

    context = {
        'summary': summary,
        'activity_by_hour': json.dumps(activity_by_hour),
        'distance_by_hour': json.dumps(distance_by_hour),
        'band_activity': json.dumps(band_activity),
        'continent_activity': json.dumps(continent_activity),
        'best_dx_time': best_dx_time,
        'top_dx': top_dx,
        'top_callsigns': top_callsigns,
        'top_locators': top_locators,
        'recent_cqs': recent_cqs,
        'dx_now': dx_now,
        'direction_activity': json.dumps(direction_activity),
        'heatmap_data': json.dumps(propagation_heatmap),
        'filters': filters,
        'period': period,
        'dx_mode': dx_mode,
    }

    return render(request, 'dashboard/index.html', context)


def dashboard_kpi_cards(request):
    """HTMX partial: KPI cards."""
    stats_service = StatisticsService()
    filters = _get_filters_from_request(request)
    summary = stats_service.get_summary(filters)

    return render(request, 'dashboard/partials/kpi_cards.html', {'summary': summary})


def dashboard_activity_by_hour(request):
    """HTMX partial: Activity by hour chart."""
    stats_service = StatisticsService()
    filters = _get_filters_from_request(request)
    activity_by_hour = stats_service.get_activity_by_hour(filters)

    return render(request, 'dashboard/partials/activity_by_hour.html', {
        'activity_by_hour': json.dumps(activity_by_hour)
    })


def dashboard_distance_by_hour(request):
    """HTMX partial: Distance by hour chart."""
    stats_service = StatisticsService()
    filters = _get_filters_from_request(request)
    distance_by_hour = stats_service.get_distance_stats_by_hour(filters)

    return render(request, 'dashboard/partials/distance_by_hour.html', {
        'distance_by_hour': json.dumps(distance_by_hour)
    })


def dashboard_snr_by_hour(request):
    """HTMX partial: SNR by hour chart."""
    stats_service = StatisticsService()
    filters = _get_filters_from_request(request)
    distance_by_hour = stats_service.get_distance_stats_by_hour(filters)

    return render(request, 'dashboard/partials/snr_by_hour.html', {
        'distance_by_hour': json.dumps(distance_by_hour)
    })


def dashboard_band_activity(request):
    """HTMX partial: Band activity chart."""
    stats_service = StatisticsService()
    filters = _get_filters_from_request(request)
    band_activity = stats_service.get_cq_count_by_band(filters)

    return render(request, 'dashboard/partials/band_activity.html', {
        'band_activity': json.dumps(band_activity)
    })


def dashboard_top_dx(request):
    """HTMX partial: Top DX table."""
    stats_service = StatisticsService()
    filters = _get_filters_from_request(request)
    top_dx = stats_service.get_top_dx(filters, limit=20)

    return render(request, 'dashboard/partials/top_dx.html', {'top_dx': top_dx})


def dashboard_top_callsigns(request):
    """HTMX partial: Top callsigns table."""
    stats_service = StatisticsService()
    filters = _get_filters_from_request(request)
    top_callsigns = stats_service.get_cq_count_by_callsign(filters)[:10]

    return render(request, 'dashboard/partials/top_callsigns.html', {
        'top_callsigns': top_callsigns
    })


def dashboard_top_locators(request):
    """HTMX partial: Top locators table."""
    stats_service = StatisticsService()
    filters = _get_filters_from_request(request)
    top_locators = stats_service.get_cq_count_by_locator(filters)[:10]

    return render(request, 'dashboard/partials/top_locators.html', {
        'top_locators': top_locators
    })


def dashboard_continent_activity(request):
    """HTMX partial: Continent activity chart."""
    stats_service = StatisticsService()
    filters = _get_filters_from_request(request)
    continent_activity = stats_service.get_cq_count_by_continent(filters)

    return render(request, 'dashboard/partials/continent_activity.html', {
        'continent_activity': json.dumps(continent_activity)
    })


def dashboard_recent_cqs(request):
    """HTMX partial: Recent CQs table."""
    stats_service = StatisticsService()
    filters = _get_filters_from_request(request)
    recent_cqs = stats_service.get_recent_cqs(filters, limit=20)

    return render(request, 'dashboard/partials/recent_cqs.html', {
        'recent_cqs': recent_cqs
    })


def dashboard_dx_now(request):
    """HTMX partial: DX Now summary."""
    stats_service = StatisticsService()
    dx_now = stats_service.get_current_dx_summary(minutes=60)

    return render(request, 'dashboard/partials/dx_now.html', {
        'dx_now': dx_now
    })


def dashboard_direction_activity(request):
    """HTMX partial: Direction activity chart."""
    stats_service = StatisticsService()
    filters = _get_filters_from_request(request)
    direction_activity = stats_service.get_activity_by_direction(filters)

    return render(request, 'dashboard/partials/direction_activity.html', {
        'direction_activity': json.dumps(direction_activity)
    })


def dashboard_propagation_heatmap(request):
    """HTMX partial: Propagation heatmap (direction vs. time)."""
    stats_service = StatisticsService()
    filters = _get_filters_from_request(request)
    heatmap_data = stats_service.get_propagation_heatmap(filters)
    dx_mode = request.GET.get('dx_mode') == 'true'
    period = request.GET.get('period')

    return render(request, 'dashboard/partials/propagation_heatmap.html', {
        'heatmap_data': json.dumps(heatmap_data),
        'dx_mode': dx_mode,
        'period': period,
    })


def _get_filters_from_request(request):
    """Extract filter parameters from request."""
    filters = {}
    if date_from := request.GET.get('date_from'):
        filters['date_from'] = date_from
    if date_to := request.GET.get('date_to'):
        filters['date_to'] = date_to
    if datetime_from := request.GET.get('datetime_from'):
        filters['datetime_from'] = datetime_from
    if datetime_to := request.GET.get('datetime_to'):
        filters['datetime_to'] = datetime_to
    if dx_mode := request.GET.get('dx_mode'):
        if dx_mode == 'true':
            filters['min_distance_km'] = 3000
    return filters


def maidenhead_area_create_modal(request):
    """HTMX endpoint: Load modal for creating a MaidenheadArea."""
    locator = request.GET.get('locator', '').strip()

    # Validate and calculate lat/lon
    service = MaidenheadService()
    error_message = None
    initial_data = {'locator': locator}

    if locator:
        try:
            normalized = service.normalize_locator(locator)
            if service.is_valid_locator(normalized):
                lat, lon = service.locator_to_latlon(normalized)
                initial_data = {
                    'locator': normalized,
                    'center_lat': lat,
                    'center_lon': lon,
                    'is_ambiguous': False,
                }

                # Use GeoService to auto-detect country and continent
                try:
                    geo_service = GeoService()
                    country, continent = geo_service.get_country_continent(lat, lon)
                    if country:
                        initial_data['primary_country'] = country
                    if continent:
                        initial_data['continent'] = continent
                except Exception as geo_error:
                    # GeoService failed, but don't show error - just skip auto-population
                    pass
            else:
                error_message = f"Ungültiges Locator-Format: {locator}"
        except Exception as e:
            error_message = f"Fehler beim Verarbeiten des Locators: {str(e)}"

    form = MaidenheadAreaForm(initial=initial_data)

    return render(request, 'dashboard/modals/maidenhead_area_create.html', {
        'form': form,
        'locator': locator,
        'error_message': error_message,
    })


def maidenhead_area_create(request):
    """HTMX endpoint: Handle POST to create MaidenheadArea."""
    if request.method == 'POST':
        form = MaidenheadAreaForm(request.POST)

        if form.is_valid():
            form.save()

            # Return success response that closes modal and shows success message
            return HttpResponse(
                '<script>'
                'document.getElementById("modal-container").innerHTML = ""; '
                'window.location.reload();'  # Reload page to show updated data
                '</script>'
            )
        else:
            # Re-render modal with errors
            return render(request, 'dashboard/modals/maidenhead_area_create.html', {
                'form': form,
                'locator': form.data.get('locator', ''),
            })

    # GET request - redirect to modal view
    return maidenhead_area_create_modal(request)


def propagation_map(request):
    """Map view showing propagation with received spots on a map."""
    from apps.ui.models import StationProfile

    # Get filter parameters from request
    period = request.GET.get('period')
    dx_mode = request.GET.get('dx_mode') == 'true'
    band = request.GET.get('band', '')

    # Calculate date range based on period
    filters = {}
    if period:
        now = timezone.now()
        if period == 'today':
            filters['date_from'] = now.date().isoformat()
        elif period == '1h':
            filters['datetime_from'] = (now - timedelta(hours=1)).isoformat()
        elif period == '3h':
            filters['datetime_from'] = (now - timedelta(hours=3)).isoformat()
        elif period == '6h':
            filters['datetime_from'] = (now - timedelta(hours=6)).isoformat()
        elif period == '12h':
            filters['datetime_from'] = (now - timedelta(hours=12)).isoformat()
        elif period == '24h':
            filters['datetime_from'] = (now - timedelta(hours=24)).isoformat()
        elif period == '7d':
            filters['date_from'] = (now - timedelta(days=7)).date().isoformat()
        elif period == '30d':
            filters['date_from'] = (now - timedelta(days=30)).date().isoformat()

    # Get station profile
    station_profile = StationProfile.objects.filter(is_default=True, is_active=True).first()

    context = {
        'station_profile': station_profile,
        'period': period,
        'dx_mode': dx_mode,
        'band': band,
    }

    return render(request, 'map/index.html', context)


def map_spots_api(request):
    """API endpoint: Return spots data as JSON for map visualization."""
    from apps.ui.models import StationProfile

    stats_service = StatisticsService()

    # Get filters from request
    filters = {}
    period = request.GET.get('period')

    # Calculate date range based on period
    if period:
        now = timezone.now()
        if period == 'today':
            filters['date_from'] = now.date().isoformat()
        elif period == '1h':
            filters['datetime_from'] = (now - timedelta(hours=1)).isoformat()
        elif period == '3h':
            filters['datetime_from'] = (now - timedelta(hours=3)).isoformat()
        elif period == '6h':
            filters['datetime_from'] = (now - timedelta(hours=6)).isoformat()
        elif period == '12h':
            filters['datetime_from'] = (now - timedelta(hours=12)).isoformat()
        elif period == '24h':
            filters['datetime_from'] = (now - timedelta(hours=24)).isoformat()
        elif period == '7d':
            filters['date_from'] = (now - timedelta(days=7)).date().isoformat()
        elif period == '30d':
            filters['date_from'] = (now - timedelta(days=30)).date().isoformat()

    # Apply DX filter if enabled
    if request.GET.get('dx') == 'true':
        filters['min_distance_km'] = 3000

    # Apply band filter if provided
    if band := request.GET.get('band'):
        filters['band'] = band

    # Get station profile
    station_profile = StationProfile.objects.filter(is_default=True, is_active=True).first()

    # Build response data
    response_data = {
        'station': None,
        'spots': []
    }

    if station_profile:
        response_data['station'] = {
            'name': station_profile.name,
            'callsign': station_profile.callsign or '',
            'locator': station_profile.locator,
            'lat': station_profile.latitude,
            'lon': station_profile.longitude,
        }

        # Get spots data
        response_data['spots'] = stats_service.get_map_spots(filters)

    return JsonResponse(response_data)


def station_detail(request, callsign):
    """
    Station detail view showing history and statistics for a specific callsign.

    Args:
        request: HTTP request
        callsign: The callsign to display
    """
    stats_service = StatisticsService()

    # Normalize callsign
    from apps.callsign.services import CallsignService
    callsign_service = CallsignService()
    normalized_callsign = callsign_service.normalize_callsign(callsign)

    # Get filter parameters from request (optional date range filter)
    filters = _get_filters_from_request(request)

    # Get station summary
    summary = stats_service.get_station_summary(normalized_callsign, filters)

    # Check if station has any signals
    if summary['total_signals'] == 0:
        context = {
            'callsign': normalized_callsign,
            'no_data': True,
        }
        return render(request, 'stations/detail.html', context)

    # Get detailed statistics
    snr_over_time = stats_service.get_station_snr_over_time(normalized_callsign, filters)
    activity_by_hour = stats_service.get_station_activity_by_hour(normalized_callsign, filters)
    snr_by_hour = stats_service.get_station_snr_by_hour(normalized_callsign, filters)
    band_distribution = stats_service.get_station_band_distribution(normalized_callsign, filters)
    recent_signals = stats_service.get_recent_signals_for_station(normalized_callsign, limit=50, filters=filters)

    # Check if station has a KnownStation entry
    known_station = None
    try:
        from apps.callsign.models import KnownStation
        known_station = KnownStation.objects.get(callsign=normalized_callsign, is_active=True)
    except:
        pass

    context = {
        'callsign': normalized_callsign,
        'summary': summary,
        'snr_over_time': json.dumps(snr_over_time),
        'activity_by_hour': json.dumps(activity_by_hour),
        'snr_by_hour': json.dumps(snr_by_hour),
        'band_distribution': json.dumps(band_distribution),
        'recent_signals': recent_signals,
        'known_station': known_station,
        'no_data': False,
    }

    return render(request, 'stations/detail.html', context)


def greyline_api(request):
    """API endpoint: Return greyline (day/night terminator) coordinates as JSON."""
    from apps.geo.services.greyline_service import GreylineService
    from datetime import datetime

    greyline_service = GreylineService()

    # Get optional timestamp parameter (ISO format)
    timestamp_str = request.GET.get('timestamp')

    if timestamp_str:
        try:
            # Parse ISO format timestamp
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            return JsonResponse({
                'error': 'Invalid timestamp format. Use ISO 8601 format (e.g., 2026-05-03T19:00:00Z)'
            }, status=400)
    else:
        # Use current UTC time
        timestamp = datetime.utcnow()

    # Get optional resolution parameter (number of points)
    resolution = int(request.GET.get('resolution', 360))

    # Limit resolution to prevent performance issues
    if resolution < 10:
        resolution = 10
    elif resolution > 1000:
        resolution = 1000

    # Calculate greyline coordinates
    coordinates = greyline_service.calculate_greyline(timestamp, resolution)

    # Format response
    response_data = {
        'timestamp': timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'coordinates': coordinates
    }

    return JsonResponse(response_data)


