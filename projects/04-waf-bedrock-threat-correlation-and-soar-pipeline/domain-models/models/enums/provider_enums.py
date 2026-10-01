"""
===============================================================================

Gen2X Security Engineering Platform

Module:
    provider_enums.py

===============================================================================

Overview
-------------------------------------------------------------------------------

This module defines the enumerations used throughout the Gen2X Provider
Framework.

Providers retrieve information from external systems and normalize that
information into a common format understood by the rest of the platform.

Examples of providers include:

    • VirusTotal
    • AbuseIPDB
    • GreyNoise
    • CISA Known Exploited Vulnerabilities (KEV)
    • AWS GuardDuty
    • Internal Asset Inventory
    • Internal CMDB
    • MISP

Notice something important...

None of the rest of the framework needs to know HOW those providers work.

Every provider presents a common interface.

That is one of the primary goals of framework design.

-------------------------------------------------------------------------------

Architectural Philosophy

Indicators answer:

    "What did we observe?"

Providers answer:

    "What can we learn about it?"

Fusion answers:

    "What conclusion should we draw?"

Keeping these responsibilities separate produces software that is easier
to maintain, easier to test, and easier to extend.

-------------------------------------------------------------------------------

Provider Workflow

Indicator

        ↓

Provider

        ↓

Evidence

        ↓

Fusion Engine

        ↓

Threat Summary

Providers never determine whether something is malicious.

They simply contribute evidence.

===============================================================================

Chewbacca's Commentary 🐶

One of the biggest mistakes made by new security engineers is trusting
the very first provider they query.

Professional platforms almost never do that.

Instead...

they ask multiple independent providers.

If several independent sources agree...

our confidence increases.

The Fusion Engine exists because no single provider knows everything.

Good engineers collect evidence.

Great engineers correlate evidence.

===============================================================================
"""

from __future__ import annotations

from .base_enum import Gen2XEnum


# =============================================================================
# Provider Type
# =============================================================================

class ProviderType(Gen2XEnum):
    """
    Describes the category of provider.

    ProviderType answers one question:

        "What kind of provider is this?"

    ProviderType does NOT describe:

        • Execution success
        • Trustworthiness
        • Available capabilities
        • Health

    Those concepts belong to separate enumerations.
    """

    # -------------------------------------------------------------------------
    # Commercial Intelligence Platforms
    # -------------------------------------------------------------------------

    COMMERCIAL = "COMMERCIAL"

    # -------------------------------------------------------------------------
    # Community Intelligence
    # -------------------------------------------------------------------------

    COMMUNITY = "COMMUNITY"

    # -------------------------------------------------------------------------
    # Government Sources
    # -------------------------------------------------------------------------

    GOVERNMENT = "GOVERNMENT"

    # -------------------------------------------------------------------------
    # Cloud Native
    # -------------------------------------------------------------------------

    CLOUD_NATIVE = "CLOUD_NATIVE"

    # -------------------------------------------------------------------------
    # Enterprise Internal Systems
    # -------------------------------------------------------------------------

    INTERNAL = "INTERNAL"

    # -------------------------------------------------------------------------
    # Open Source
    # -------------------------------------------------------------------------

    OPEN_SOURCE = "OPEN_SOURCE"

    # -------------------------------------------------------------------------
    # Custom Enterprise Integrations
    # -------------------------------------------------------------------------

    CUSTOM = "CUSTOM"

    UNKNOWN = "UNKNOWN"


# =============================================================================
# Chewbacca's Commentary 🐶
#
# Type never changes simply because the provider returned no results.
#
# Example
#
# VirusTotal searches a SHA256.
#
# No intelligence exists.
#
# VirusTotal is STILL a Commercial provider.
#
# The query succeeded.
#
# The provider simply had nothing to contribute.
#
# Identity and execution are different concepts.
#
# =============================================================================


# =============================================================================
# Provider Status
# =============================================================================

class ProviderStatus(Gen2XEnum):
    """
    Represents the operational outcome of a provider request.

    ProviderStatus answers:

        "What happened while communicating with this provider?"

    This enumeration describes execution rather than security.
    """

    SUCCESS = "SUCCESS"

    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"

    NOT_FOUND = "NOT_FOUND"

    SKIPPED = "SKIPPED"

    TIMEOUT = "TIMEOUT"

    RATE_LIMITED = "RATE_LIMITED"

    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"

    PERMISSION_DENIED = "PERMISSION_DENIED"

    UNAVAILABLE = "UNAVAILABLE"

    ERROR = "ERROR"

    UNKNOWN = "UNKNOWN"


# =============================================================================
# Chewbacca's Commentary 🐶
#
# "NOT_FOUND" is NOT an error.
#
# Imagine asking:
#
#     "Have you ever seen this IP?"
#
# The provider replies:
#
#     "No."
#
# That is actually a successful request.
#
# The provider worked correctly.
#
# It simply had no intelligence to contribute.
#
# Many new engineers accidentally treat "No Data" as an exception.
#
# They're completely different situations.
#
# =============================================================================


# =============================================================================
# Provider Capability
# =============================================================================

class ProviderCapability(Gen2XEnum):
    """
    Describes the services a provider offers.

    Capabilities describe WHAT the provider can do.

    They do not describe WHO provides the service.
    """

    REPUTATION_LOOKUP = "REPUTATION_LOOKUP"

    IOC_ENRICHMENT = "IOC_ENRICHMENT"

    DNS_LOOKUP = "DNS_LOOKUP"

    WHOIS_LOOKUP = "WHOIS_LOOKUP"

    GEOLOCATION = "GEOLOCATION"

    VULNERABILITY_LOOKUP = "VULNERABILITY_LOOKUP"

    MALWARE_ANALYSIS = "MALWARE_ANALYSIS"

    ATTACK_MAPPING = "ATTACK_MAPPING"

    CLOUD_ASSET_LOOKUP = "CLOUD_ASSET_LOOKUP"

    IDENTITY_LOOKUP = "IDENTITY_LOOKUP"

    UNKNOWN = "UNKNOWN"


# =============================================================================
# Chewbacca's Commentary 🐶
#
# Frameworks should depend on capabilities.
#
# Not vendor names.
#
# Today
#
#     Provider A
#
# performs reputation lookups.
#
# Tomorrow
#
#     Provider B
#
# replaces it.
#
# If both support REPUTATION_LOOKUP,
# nothing else in the framework should change.
#
# That's abstraction.
#
# =============================================================================


# =============================================================================
# Provider Health
# =============================================================================

class ProviderHealth(Gen2XEnum):
    """
    Represents the operational health of a provider.

    Health changes over time.

    Capabilities generally do not.
    """

    HEALTHY = "HEALTHY"

    DEGRADED = "DEGRADED"

    MAINTENANCE = "MAINTENANCE"

    UNAVAILABLE = "UNAVAILABLE"

    UNKNOWN = "UNKNOWN"


# =============================================================================
# Chewbacca's Commentary 🐶
#
# Think of ProviderHealth like a heartbeat monitor.
#
# A provider may still be a Commercial provider.
#
# It may still support Reputation Lookups.
#
# But...
#
# Right now...
#
# It might simply be offline.
#
# Keeping Health separate from Type and Capability allows monitoring
# systems to detect outages without changing provider metadata.
#
# =============================================================================


# =============================================================================
# Provider Trust Level
# =============================================================================

class ProviderTrustLevel(Gen2XEnum):
    """
    Represents the amount of confidence Gen2X places in a provider.

    Trust is determined by organizational policy and operational history.

    Trust is NOT correctness.

    Even highly trusted providers occasionally produce incorrect or
    incomplete information.
    """

    HIGH = "HIGH"

    MEDIUM = "MEDIUM"

    LOW = "LOW"

    UNTRUSTED = "UNTRUSTED"

    EXPERIMENTAL = "EXPERIMENTAL"

    UNKNOWN = "UNKNOWN"


# =============================================================================
# Chewbacca's Commentary 🐶
#
# Imagine three providers disagree.
#
# Provider A says:
#
#     Malicious
#
# Provider B says:
#
#     Clean
#
# Provider C says:
#
#     Unknown
#
# Should every provider receive equal weight?
#
# Maybe...
#
# Maybe not.
#
# Trust Level allows the Fusion Engine to weigh evidence without
# blindly accepting every opinion equally.
#
# Trust influences confidence.
#
# Evidence drives conclusions.
#
# =============================================================================


# =============================================================================
# Public Package Interface
# =============================================================================

__all__ = [

    "ProviderType",

    "ProviderStatus",

    "ProviderCapability",

    "ProviderHealth",

    "ProviderTrustLevel",
]
