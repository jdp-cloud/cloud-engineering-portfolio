"""
Gen2X shared utilities.

Generic helpers used across the platform.

Utility modules depend on nothing except the Python standard library.
"""

from .time import utc_now

__all__ = [
    "utc_now",
]
