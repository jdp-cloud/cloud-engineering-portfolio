"""
===============================================================================

Gen2X Security Engineering Platform

Module:
    time_utils.py

===============================================================================

Overview
-------------------------------------------------------------------------------

Compatibility re-export.

The canonical implementation of utc_now() lives in utils/time.py so that
every package (models, agents, providers) shares one definition.

This module remains so existing imports continue to work:

    from models.time_utils import utc_now

New code should prefer:

    from utils.time import utc_now

===============================================================================
"""

from __future__ import annotations

from utils.time import utc_now

__all__ = [
    "utc_now",
]
