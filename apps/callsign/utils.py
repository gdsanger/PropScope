"""
Utility functions for callsign parsing and analysis.
"""

import re
from typing import Optional, Tuple


def normalize_callsign(callsign: str) -> str:
    """
    Normalize a callsign by removing common portable/mobile suffixes.

    Args:
        callsign: Raw callsign string

    Returns:
        Normalized callsign
    """
    callsign = callsign.upper().strip()

    # Remove common suffixes like /P, /M, /QRP, etc.
    # Keep prefix indicators like DL/K1ABC
    parts = callsign.split('/')

    # If there are multiple parts, keep the main callsign part (usually the one with digits)
    if len(parts) > 1:
        # Find the part with a digit (the actual callsign)
        for part in parts:
            if any(c.isdigit() for c in part):
                return part

    return callsign


def extract_prefix(callsign: str) -> str:
    """
    Extract the prefix from a callsign for country/region identification.

    This uses a simplified algorithm:
    - Returns the leading letters + first digit
    - Examples: DL1ABC -> DL, K1ABC -> K, VE3ABC -> VE

    Args:
        callsign: Callsign string

    Returns:
        Prefix string
    """
    callsign = normalize_callsign(callsign)

    # Find the first digit
    match = re.search(r'\d', callsign)
    if not match:
        return callsign[:2] if len(callsign) >= 2 else callsign

    digit_pos = match.start()

    # Include all letters before the digit
    prefix = callsign[:digit_pos]

    # Some countries use single-letter prefixes (K, W, N, etc.)
    # Others use 2-3 letters (DL, VE, etc.)
    if not prefix:
        # Special case: digit is first character (rare)
        return callsign[0] if callsign else ""

    return prefix


def generate_qrz_url(callsign: str) -> str:
    """
    Generate QRZ.com lookup URL for a callsign.

    Args:
        callsign: Callsign string

    Returns:
        QRZ.com URL
    """
    normalized = normalize_callsign(callsign)
    return f"https://www.qrz.com/db/{normalized}"
