"""
===============================================================================

Gen2X Security Engineering Platform

Module:
    utils/time.py

===============================================================================

Overview
-------------------------------------------------------------------------------

Shared time helpers for the Gen2X platform.

Every timestamp within Gen2X should be timezone-aware UTC.

Consistent timestamps make evidence easier to correlate across providers,
cloud platforms, and geographic regions.

Note

    datetime.utcnow() returns a NAIVE datetime and is deprecated in
    modern Python.

    utc_now() returns an AWARE datetime.

    Naive and aware datetimes cannot be compared or subtracted.

    Mixing them raises TypeError at runtime.

===============================================================================
"""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """
    Return the current timezone-aware UTC timestamp.
    """

    return datetime.now(timezone.utc)


__all__ = [
    "utc_now",
]
