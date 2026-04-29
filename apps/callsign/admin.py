from django.contrib import admin
from .models import CallsignPrefix, GermanCallsignClassRule


@admin.register(CallsignPrefix)
class CallsignPrefixAdmin(admin.ModelAdmin):
    list_display = ['prefix', 'country', 'continent', 'itu_region', 'cq_zone', 'is_active']
    list_filter = ['continent', 'itu_region', 'cq_zone', 'is_active']
    search_fields = ['prefix', 'country', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['prefix']


@admin.register(GermanCallsignClassRule)
class GermanCallsignClassRuleAdmin(admin.ModelAdmin):
    list_display = ['prefix_pattern', 'license_class', 'description', 'is_active']
    list_filter = ['license_class', 'is_active']
    search_fields = ['prefix_pattern', 'description', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-prefix_pattern']  # Longer patterns first
