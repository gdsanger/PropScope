from django.shortcuts import render
from django.http import JsonResponse
import json
from apps.analysis.services import StatisticsService


def home(request):
    """Home page view."""
    return render(request, 'home.html')


def dashboard(request):
    """Main dashboard view with all statistics and charts."""
    stats_service = StatisticsService()

    # Get filter parameters from request
    filters = {}
    if date_from := request.GET.get('date_from'):
        filters['date_from'] = date_from
    if date_to := request.GET.get('date_to'):
        filters['date_to'] = date_to

    # Get all dashboard data
    summary = stats_service.get_summary(filters)
    activity_by_hour = stats_service.get_activity_by_hour(filters)
    distance_by_hour = stats_service.get_distance_stats_by_hour(filters)
    band_activity = stats_service.get_cq_count_by_band(filters)
    top_dx = stats_service.get_top_dx(filters, limit=20)
    top_callsigns = stats_service.get_cq_count_by_callsign(filters)[:10]
    top_locators = stats_service.get_cq_count_by_locator(filters)[:10]

    context = {
        'summary': summary,
        'activity_by_hour': json.dumps(activity_by_hour),
        'distance_by_hour': json.dumps(distance_by_hour),
        'band_activity': json.dumps(band_activity),
        'top_dx': top_dx,
        'top_callsigns': top_callsigns,
        'top_locators': top_locators,
        'filters': filters,
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


def _get_filters_from_request(request):
    """Extract filter parameters from request."""
    filters = {}
    if date_from := request.GET.get('date_from'):
        filters['date_from'] = date_from
    if date_to := request.GET.get('date_to'):
        filters['date_to'] = date_to
    return filters

