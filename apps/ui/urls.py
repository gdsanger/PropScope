from django.urls import path
from . import views

app_name = 'ui'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),

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
]
