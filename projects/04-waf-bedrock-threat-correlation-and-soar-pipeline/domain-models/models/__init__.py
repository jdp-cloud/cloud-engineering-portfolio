"""
models/__init__.py

Gen2X Domain Models

The models package defines the shared domain objects used throughout the
Gen2X platform.

Design Philosophy
-----------------

Models represent information.

Agents perform work.

Services implement business logic.

By separating data from behavior, Gen2X keeps components easier to
understand, test, and extend.
"""

# =============================================================================
# Enumerations
# =============================================================================

from .enums import *

# =============================================================================
# Domain Models
# =============================================================================
#
# As additional models are created, export them here.
#
# Example:
#
# from .evidence import ThreatEvidence
# from .assessment import AssessmentResult
# from .report import ThreatSummary
#

# =============================================================================
# Package Information
# =============================================================================

__version__ = "2.0.0"

PACKAGE_NAME = "Gen2X Models"

# =============================================================================
# Public Interface
# =============================================================================

__all__: list[str] = []

# =============================================================================
# Chewbacca's Commentary 🐾
#
# Every software system
# develops its own language.
#
# Models define that language.
#
# If engineers cannot agree on
# what an object represents,
# they will struggle to agree on
# how the system should behave.
#
# Good models create a common vocabulary.
#
# Good vocabulary leads to good architecture.
#
#                             — Chewbacca
#                               Chief Wookiee Architect
#
# =============================================================================
