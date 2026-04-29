"""
Core service for callsign analysis and prefix detection.

This service provides centralized functionality for:
- Normalizing callsigns
- Generating QRZ URLs
- Detecting country/continent from prefixes via database lookup
- Detecting German license classes via database lookup

The service uses database tables (CallsignPrefix, GermanCallsignClassRule)
for all lookups - no hardcoded data.
"""

from typing import Optional, Dict, Any
from apps.callsign.models import CallsignPrefix, GermanCallsignClassRule


class CallsignService:
    """
    Service for callsign analysis and prefix detection.

    All prefix and license class data is loaded from database tables.
    """

    def normalize_callsign(self, callsign: str) -> str:
        """
        Normalize a callsign string.

        Performs:
        - Strip whitespace
        - Convert to uppercase
        - Remove angle brackets (e.g., <R065N> → R065N)

        Args:
            callsign: Raw callsign string

        Returns:
            Normalized callsign string

        Examples:
            >>> service.normalize_callsign(" dl3tx ")
            "DL3TX"
            >>> service.normalize_callsign("<R065N>")
            "R065N"
            >>> service.normalize_callsign("dl/ad2lx")
            "DL/AD2LX"
        """
        if not callsign:
            return ""

        # Strip whitespace and convert to uppercase
        normalized = callsign.strip().upper()

        # Remove angle brackets if present
        if normalized.startswith('<') and normalized.endswith('>'):
            normalized = normalized[1:-1]

        return normalized

    def get_qrz_url(self, callsign: str) -> str:
        """
        Generate QRZ.com lookup URL for a callsign.

        Args:
            callsign: Callsign string

        Returns:
            QRZ.com URL

        Example:
            >>> service.get_qrz_url("DL3TX")
            "https://www.qrz.com/db/DL3TX"
        """
        normalized = self.normalize_callsign(callsign)
        return f"https://www.qrz.com/db/{normalized}"

    def detect_prefix(self, callsign: str) -> Optional[CallsignPrefix]:
        """
        Detect the callsign prefix and return the matching CallsignPrefix record.

        Uses longest-match algorithm on active prefixes from database.
        Handles portable callsigns by checking prefix before slash first.

        Args:
            callsign: Callsign string

        Returns:
            CallsignPrefix object if found, None otherwise

        Examples:
            >>> prefix = service.detect_prefix("DL3TX")
            >>> prefix.country if prefix else None
            "Germany"
            >>> prefix = service.detect_prefix("DL/AD2LX")
            # Checks "DL" first (before slash)
        """
        normalized = self.normalize_callsign(callsign)

        if not normalized:
            return None

        # Handle portable callsigns: check prefix before slash first
        if '/' in normalized:
            parts = normalized.split('/')

            # Try prefix before slash first
            prefix_before_slash = parts[0]
            result = self._lookup_prefix(prefix_before_slash)
            if result:
                return result

            # Try prefix after slash (in case format is like "DL/AD2LX")
            # Find the part with digits (actual callsign)
            for part in parts:
                if any(c.isdigit() for c in part):
                    result = self._lookup_prefix(part)
                    if result:
                        return result

        # Normal callsign - extract and lookup prefix
        return self._lookup_prefix(normalized)

    def _lookup_prefix(self, callsign: str) -> Optional[CallsignPrefix]:
        """
        Internal method to lookup prefix using longest-match algorithm.

        Args:
            callsign: Normalized callsign string

        Returns:
            CallsignPrefix object if found, None otherwise
        """
        if not callsign:
            return None

        # Try progressively longer prefixes (longest match wins)
        # Start from full callsign length down to 1 character
        max_prefix_length = min(len(callsign), 10)  # Max prefix length in model is 10

        for length in range(max_prefix_length, 0, -1):
            prefix_candidate = callsign[:length].upper()

            try:
                # Query for exact match on active prefix (case-insensitive via iexact)
                prefix_obj = CallsignPrefix.objects.filter(
                    prefix__iexact=prefix_candidate,
                    is_active=True
                ).first()

                if prefix_obj:
                    return prefix_obj
            except Exception:
                # Database not available or other error
                continue

        return None

    def detect_country(self, callsign: str) -> Dict[str, Any]:
        """
        Detect country and continent from callsign.

        Args:
            callsign: Callsign string

        Returns:
            Dictionary with country, continent, itu_region, cq_zone, or empty dict

        Example:
            >>> result = service.detect_country("DL3TX")
            >>> result.get('country')
            "Germany"
            >>> result.get('continent')
            "EU"
        """
        prefix = self.detect_prefix(callsign)

        if not prefix:
            return {}

        return {
            'country': prefix.country,
            'continent': prefix.continent,
            'itu_region': prefix.itu_region,
            'cq_zone': prefix.cq_zone,
            'prefix': prefix.prefix,
        }

    def detect_german_license_class(self, callsign: str) -> Optional[str]:
        """
        Detect German license class for German callsigns.

        Uses GermanCallsignClassRule table for pattern matching.
        Returns None for non-German callsigns or unknown patterns.

        Args:
            callsign: Callsign string

        Returns:
            License class string (e.g., "A", "E") or None

        Examples:
            >>> service.detect_german_license_class("DL3TX")
            "A"
            >>> service.detect_german_license_class("DO1ABC")
            "E"
        """
        normalized = self.normalize_callsign(callsign)

        if not normalized:
            return None

        # Extract the main callsign part (handle portable)
        main_callsign = normalized
        if '/' in normalized:
            parts = normalized.split('/')
            # Find part with digits
            for part in parts:
                if any(c.isdigit() for c in part):
                    main_callsign = part
                    break

        # Try to match against active German callsign class rules
        # Rules are ordered by prefix_pattern length (longest first)
        try:
            rules = GermanCallsignClassRule.objects.filter(is_active=True).order_by('-prefix_pattern')

            for rule in rules:
                # Check if callsign starts with the pattern
                if main_callsign.startswith(rule.prefix_pattern.upper()):
                    return rule.license_class
        except Exception:
            # Database not available or other error
            pass

        return None
