"""Custom template tags and filters for dashboard."""

from django import template

register = template.Library()


@register.filter
def band_color(band):
    """Return Bootstrap color class for a band."""
    band_colors = {
        '160m': 'dark',
        '80m': 'primary',
        '60m': 'info',
        '40m': 'primary',
        '30m': 'secondary',
        '20m': 'success',
        '17m': 'info',
        '15m': 'warning',
        '12m': 'danger',
        '10m': 'warning',
        '6m': 'danger',
        '4m': 'danger',
        '2m': 'danger',
    }
    return band_colors.get(band, 'secondary')


@register.filter
def snr_color(snr):
    """Return Bootstrap text color class based on SNR value."""
    if snr is None:
        return 'text-muted'
    try:
        snr_val = float(snr)
        if snr_val >= 0:
            return 'text-success'
        elif snr_val >= -10:
            return 'text-info'
        elif snr_val >= -20:
            return 'text-warning'
        else:
            return 'text-danger'
    except (ValueError, TypeError):
        return 'text-muted'


@register.filter
def snr_label(snr):
    """Return a descriptive label for SNR quality."""
    if snr is None:
        return 'Unknown'
    try:
        snr_val = float(snr)
        if snr_val >= 0:
            return 'Gut'
        elif snr_val >= -10:
            return 'Mittel'
        elif snr_val >= -20:
            return 'Schwach'
        else:
            return 'Sehr schwach'
    except (ValueError, TypeError):
        return 'Unknown'


@register.filter
def highlight_dx(distance_km):
    """Return True if distance is exceptional (>10000km)."""
    if distance_km is None:
        return False
    try:
        return float(distance_km) > 10000
    except (ValueError, TypeError):
        return False


@register.filter
def locator_display(locator):
    """Display locator or 'Unknown' if None/empty."""
    if not locator or locator == 'None':
        return 'Unknown'
    return locator
