from django.urls import path
from . import views

app_name = 'ui'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Map
    path('map/', views.propagation_map, name='propagation-map'),
    path('map/api/spots/', views.map_spots_api, name='map-spots-api'),

    # HTMX partials
    path('dashboard/partials/kpi-cards/', views.dashboard_kpi_cards, name='dashboard-kpi-cards'),
    path('dashboard/partials/activity-by-hour/', views.dashboard_activity_by_hour, name='dashboard-activity-by-hour'),
    path('dashboard/partials/distance-by-hour/', views.dashboard_distance_by_hour, name='dashboard-distance-by-hour'),
    path('dashboard/partials/snr-by-hour/', views.dashboard_snr_by_hour, name='dashboard-snr-by-hour'),
    path('dashboard/partials/band-activity/', views.dashboard_band_activity, name='dashboard-band-activity'),
    path('dashboard/partials/continent-activity/', views.dashboard_continent_activity, name='dashboard-continent-activity'),
    path('dashboard/partials/top-dx/', views.dashboard_top_dx, name='dashboard-top-dx'),
    path('dashboard/partials/top-callsigns/', views.dashboard_top_callsigns, name='dashboard-top-callsigns'),
    path('dashboard/partials/top-locators/', views.dashboard_top_locators, name='dashboard-top-locators'),
    path('dashboard/partials/recent-cqs/', views.dashboard_recent_cqs, name='dashboard-recent-cqs'),
    path('dashboard/partials/dx-now/', views.dashboard_dx_now, name='dashboard-dx-now'),
    path('dashboard/partials/direction-activity/', views.dashboard_direction_activity, name='dashboard-direction-activity'),
    path('dashboard/partials/propagation-heatmap/', views.dashboard_propagation_heatmap, name='dashboard-propagation-heatmap'),

    # MaidenheadArea management
    path('dashboard/maidenhead-area/create-modal/', views.maidenhead_area_create_modal, name='maidenhead-area-create-modal'),
    path('dashboard/maidenhead-area/create/', views.maidenhead_area_create, name='maidenhead-area-create'),

    # Station detail pages
    path('stations/<str:callsign>/', views.station_detail, name='station-detail'),
]
