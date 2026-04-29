from django.contrib import admin
from .models import CallsignPrefix


@admin.register(CallsignPrefix)
class CallsignPrefixAdmin(admin.ModelAdmin):
    list_display = ['prefix', 'country', 'continent', 'itu_region', 'cq_zone']
    list_filter = ['continent', 'itu_region', 'cq_zone']
    search_fields = ['prefix', 'country', 'notes']
    ordering = ['prefix']
