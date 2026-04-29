from django.contrib import admin
from .models import MaidenheadArea


@admin.register(MaidenheadArea)
class MaidenheadAreaAdmin(admin.ModelAdmin):
    list_display = ['locator', 'primary_country', 'continent', 'center_lat', 'center_lon', 'is_ambiguous']
    list_filter = ['continent', 'is_ambiguous', 'primary_country']
    search_fields = ['locator', 'primary_country', 'alternative_countries', 'notes']
    ordering = ['locator']
