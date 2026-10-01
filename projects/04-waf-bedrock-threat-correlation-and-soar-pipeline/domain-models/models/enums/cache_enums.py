"""
===============================================================================

Gen2X Security Engineering Platform

Module:
    cache_enums.py

===============================================================================

Overview
-------------------------------------------------------------------------------

This module defines the enumerations used throughout the Gen2X Caching
Framework.

Caching allows the platform to intelligently reuse previously collected
security evidence rather than repeatedly querying external systems.

Examples include:

    • Threat Intelligence
    • IP Reputation
    • WHOIS Records
    • DNS Lookups
    • Geolocation
    • Vulnerability Metadata
    • Cloud Asset Information
    • Policy Definitions

Unlike many applications that cache raw API responses, Gen2X caches
normalized evidence.

Normalizing evidence allows information from multiple providers to be
shared throughout the platform without exposing provider-specific
implementations.

-------------------------------------------------------------------------------

Architectural Philosophy

External Provider

        ↓

Collect Evidence

        ↓

Normalize Evidence

        ↓

Cache Evidence

        ↓

Fusion Engine

        ↓

Threat Summary

The cache becomes a shared knowledge layer rather than a simple storage
mechanism.

-------------------------------------------------------------------------------

Why Cache?

Caching provides several important benefits.

    • Reduces external API requests

    • Reduces provider costs

    • Improves response times

    • Prevents unnecessary duplicate lookups

    • Shares intelligence between agents

    • Improves resilience during provider outages

Good security engineering balances performance with freshness.

Gen2X intentionally models those concepts separately.

===============================================================================

Chewbacca's Commentary 🐾

Imagine asking AbuseIPDB
about the same IP address
one thousand times.

Eventually...

AbuseIPDB becomes tired.

Your API quota disappears.

Your wallet becomes lighter.

Caching isn't only about speed.

It's about respecting systems that
help us perform investigations.

Collect evidence once.

Reuse it wisely.

                               — Chewbacca
                                 Chief Wookiee Architect

===============================================================================
"""

from __future__ import annotations

from .base_enum import Gen2XEnum


# =============================================================================
# Cache Type
# =============================================================================


class CacheType(Gen2XEnum):
    """
    Describes the type of information stored within the Gen2X cache.

    CacheType answers one question:

        "What kind of information are we storing?"

    Different cache types often require different expiration strategies,
    storage locations, and validation rules.

    CacheType does not describe:

        • Where the cache is stored

        • Who owns the cache

        • Whether the cache is fresh

        • Whether a lookup succeeded

    Those concepts are represented elsewhere.
    """

    # -------------------------------------------------------------------------
    # Indicator Information
    # -------------------------------------------------------------------------

    INDICATOR = "INDICATOR"

    # -------------------------------------------------------------------------
    # Provider Responses
    # -------------------------------------------------------------------------

    PROVIDER_RESPONSE = "PROVIDER_RESPONSE"

    THREAT_INTELLIGENCE = "THREAT_INTELLIGENCE"

    # -------------------------------------------------------------------------
    # Internet Infrastructure
    # -------------------------------------------------------------------------

    DNS = "DNS"

    WHOIS = "WHOIS"

    GEOLOCATION = "GEOLOCATION"

    # -------------------------------------------------------------------------
    # Vulnerability Information
    # -------------------------------------------------------------------------

    VULNERABILITY = "VULNERABILITY"

    CVE = "CVE"

    CWE = "CWE"

    # -------------------------------------------------------------------------
    # Cloud Information
    # -------------------------------------------------------------------------

    ASSET_METADATA = "ASSET_METADATA"

    IAM_METADATA = "IAM_METADATA"

    NETWORK_METADATA = "NETWORK_METADATA"

    # -------------------------------------------------------------------------
    # Platform Information
    # -------------------------------------------------------------------------

    POLICY = "POLICY"

    CONFIGURATION = "CONFIGURATION"

    # -------------------------------------------------------------------------
    # General
    # -------------------------------------------------------------------------

    CUSTOM = "CUSTOM"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of the cache type.

        These descriptions may later support:

            • Documentation

            • User Interfaces

            • API Responses

            • Report Generation

            • Educational Material
        """

        descriptions = {

            CacheType.INDICATOR:
                "Cached security indicators such as IP addresses, domains, hashes, or URLs.",

            CacheType.PROVIDER_RESPONSE:
                "Normalized responses collected from external intelligence providers.",

            CacheType.THREAT_INTELLIGENCE:
                "Threat intelligence enriched from one or more providers.",

            CacheType.DNS:
                "Cached DNS lookup information.",

            CacheType.WHOIS:
                "Cached WHOIS registration information.",

            CacheType.GEOLOCATION:
                "Cached geographic location data.",

            CacheType.VULNERABILITY:
                "Cached vulnerability information.",

            CacheType.CVE:
                "Cached Common Vulnerabilities and Exposures metadata.",

            CacheType.CWE:
                "Cached Common Weakness Enumeration metadata.",

            CacheType.ASSET_METADATA:
                "Cached cloud asset metadata.",

            CacheType.IAM_METADATA:
                "Cached identity and access management metadata.",

            CacheType.NETWORK_METADATA:
                "Cached networking metadata.",

            CacheType.POLICY:
                "Cached security policy definitions.",

            CacheType.CONFIGURATION:
                "Cached platform configuration data.",

            CacheType.CUSTOM:
                "Application-specific cached information.",

            CacheType.UNKNOWN:
                "Cache type has not yet been classified."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Not all information changes
# at the same speed.
#
# DNS records
#
# may change every day.
#
# WHOIS information
#
# may remain unchanged
# for months.
#
# Security policies
#
# only change when
# engineers intentionally
# modify them.
#
# Different information deserves
# different caching strategies.
#
# One cache policy should never
# fit everything.
#
# =============================================================================


# =============================================================================
# Cache Scope
# =============================================================================


class CacheScope(Gen2XEnum):
    """
    Describes who is permitted to reuse cached information.

    CacheScope answers one question:

        "Who may use this cached evidence?"

    Sharing cached intelligence reduces unnecessary provider requests while
    allowing multiple agents to collaborate efficiently.

    Scope determines visibility.

    It does not determine freshness.
    """

    # -------------------------------------------------------------------------
    # Single Operation
    # -------------------------------------------------------------------------

    REQUEST = "REQUEST"

    SESSION = "SESSION"

    # -------------------------------------------------------------------------
    # Workflow
    # -------------------------------------------------------------------------

    WORKFLOW = "WORKFLOW"

    AGENT = "AGENT"

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------

    APPLICATION = "APPLICATION"

    SHARED = "SHARED"

    GLOBAL = "GLOBAL"

    # -------------------------------------------------------------------------
    # General
    # -------------------------------------------------------------------------

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of cache scope.
        """

        descriptions = {

            CacheScope.REQUEST:
                "Visible only during a single request.",

            CacheScope.SESSION:
                "Visible during the current user or execution session.",

            CacheScope.WORKFLOW:
                "Shared throughout a workflow execution.",

            CacheScope.AGENT:
                "Available only to the current agent.",

            CacheScope.APPLICATION:
                "Shared across the application.",

            CacheScope.SHARED:
                "Shared across multiple platform components.",

            CacheScope.GLOBAL:
                "Available to every component of the framework.",

            CacheScope.UNKNOWN:
                "Cache scope has not yet been classified."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Suppose Agent 10 asks
# VirusTotal about an indicator.
#
# Should Agent 11
# immediately ask again?
#
# Probably not.
#
# If trustworthy evidence
# already exists,
#
# sharing knowledge is usually
# more efficient than
# repeating the same question.
#
# Cache Scope determines
# who is allowed
# to benefit from
# previously collected evidence.
#
# Sharing knowledge
# is one of the biggest advantages
# of building a framework
# instead of isolated scripts.
#
# =============================================================================

# =============================================================================
# Cache Policy
# =============================================================================


class CachePolicy(Gen2XEnum):
    """
    Describes the strategy used when retrieving cached information.

    CachePolicy answers one question:

        "How should the framework decide between cached information and
        requesting fresh information?"

    Different information requires different caching strategies.

    Threat intelligence may tolerate short periods of staleness.

    Live cloud configuration may require real-time retrieval.

    The policy determines the retrieval strategy rather than the storage
    location.
    """

    # -------------------------------------------------------------------------
    # Cache Preferred
    # -------------------------------------------------------------------------

    CACHE_FIRST = "CACHE_FIRST"

    CACHE_ONLY = "CACHE_ONLY"

    # -------------------------------------------------------------------------
    # Network Preferred
    # -------------------------------------------------------------------------

    NETWORK_FIRST = "NETWORK_FIRST"

    NETWORK_ONLY = "NETWORK_ONLY"

    # -------------------------------------------------------------------------
    # Refresh Policies
    # -------------------------------------------------------------------------

    REFRESH_ON_EXPIRE = "REFRESH_ON_EXPIRE"

    REFRESH_ALWAYS = "REFRESH_ALWAYS"

    # -------------------------------------------------------------------------
    # General
    # -------------------------------------------------------------------------

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of the cache policy.
        """

        descriptions = {

            CachePolicy.CACHE_FIRST:
                "Use cached information whenever possible before contacting external providers.",

            CachePolicy.CACHE_ONLY:
                "Never contact external providers. Use cached information only.",

            CachePolicy.NETWORK_FIRST:
                "Request fresh information before consulting the cache.",

            CachePolicy.NETWORK_ONLY:
                "Always bypass the cache.",

            CachePolicy.REFRESH_ON_EXPIRE:
                "Reuse cached information until expiration, then refresh automatically.",

            CachePolicy.REFRESH_ALWAYS:
                "Always refresh cached information before use.",

            CachePolicy.UNKNOWN:
                "Cache policy has not yet been classified."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Different evidence deserves
# different retrieval strategies.
#
# Threat Intelligence
#
# may tolerate information
# that is several hours old.
#
# IAM configuration
#
# probably should not.
#
# Cache policy is really
# a business decision.
#
# Not every question deserves
# a real-time answer.
#
# =============================================================================


# =============================================================================
# Cache Status
# =============================================================================


class CacheStatus(Gen2XEnum):
    """
    Describes what occurred during a cache lookup.

    CacheStatus answers:

        "What happened while accessing the cache?"

    Status describes lookup behavior.

    It does not describe freshness.

    A cache HIT may still return stale information.

    Those are different concepts.
    """

    HIT = "HIT"

    MISS = "MISS"

    REFRESHED = "REFRESHED"

    STALE = "STALE"

    EXPIRED = "EXPIRED"

    INVALIDATED = "INVALIDATED"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of cache status.
        """

        descriptions = {

            CacheStatus.HIT:
                "Requested information was found in cache.",

            CacheStatus.MISS:
                "Requested information was not found in cache.",

            CacheStatus.REFRESHED:
                "Cached information has been updated.",

            CacheStatus.STALE:
                "Cached information exists but should be refreshed.",

            CacheStatus.EXPIRED:
                "Cached information has exceeded its allowed lifetime.",

            CacheStatus.INVALIDATED:
                "Cached information has been intentionally removed.",

            CacheStatus.UNKNOWN:
                "Cache status has not been determined."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Cache MISS
#
# is not an error.
#
# It simply means
#
# "We don't know yet."
#
# Good software accepts
# uncertainty.
#
# The next step
# is asking a provider.
#
# Curiosity beats assumptions.
#
# =============================================================================


# =============================================================================
# Cache Freshness
# =============================================================================


class CacheFreshness(Gen2XEnum):
    """
    Describes how current cached information is.

    CacheFreshness answers:

        "Can this information still be trusted?"

    Freshness is determined by policy,
    timestamps,
    and organizational requirements.

    Freshness is independent of cache lookup status.
    """

    FRESH = "FRESH"

    AGING = "AGING"

    STALE = "STALE"

    EXPIRED = "EXPIRED"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of cache freshness.
        """

        descriptions = {

            CacheFreshness.FRESH:
                "Cached information is considered current.",

            CacheFreshness.AGING:
                "Cached information is approaching expiration.",

            CacheFreshness.STALE:
                "Cached information should be refreshed soon.",

            CacheFreshness.EXPIRED:
                "Cached information should no longer be trusted without refresh.",

            CacheFreshness.UNKNOWN:
                "Freshness has not yet been evaluated."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Imagine finding
# a weather forecast
# from three weeks ago.
#
# Technically...
#
# you found weather information.
#
# Practically...
#
# it isn't very useful.
#
# Security evidence behaves
# the same way.
#
# Always ask:
#
#     "How old is this?"
#
# before asking:
#
#     "Did I find something?"
#
# =============================================================================

# =============================================================================
# Cache Storage
# =============================================================================


class CacheStorage(Gen2XEnum):
    """
    Describes where cached information is physically stored.

    CacheStorage answers one question:

        "Where does the cache live?"

    The framework intentionally separates cache storage from cache behavior.

    This allows organizations to change storage technologies without
    changing the rest of the platform.

    Good software depends on abstractions rather than infrastructure.
    """

    # -------------------------------------------------------------------------
    # Memory
    # -------------------------------------------------------------------------

    MEMORY = "MEMORY"

    # -------------------------------------------------------------------------
    # Distributed Cache
    # -------------------------------------------------------------------------

    REDIS = "REDIS"

    MEMCACHED = "MEMCACHED"

    # -------------------------------------------------------------------------
    # Databases
    # -------------------------------------------------------------------------

    DYNAMODB = "DYNAMODB"

    SQL = "SQL"

    NOSQL = "NOSQL"

    # -------------------------------------------------------------------------
    # Object Storage
    # -------------------------------------------------------------------------

    S3 = "S3"

    FILESYSTEM = "FILESYSTEM"

    # -------------------------------------------------------------------------
    # General
    # -------------------------------------------------------------------------

    CUSTOM = "CUSTOM"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of the cache storage location.
        """

        descriptions = {

            CacheStorage.MEMORY:
                "In-memory cache used by the running application.",

            CacheStorage.REDIS:
                "Distributed Redis cache.",

            CacheStorage.MEMCACHED:
                "Distributed Memcached deployment.",

            CacheStorage.DYNAMODB:
                "Amazon DynamoDB cache.",

            CacheStorage.SQL:
                "Relational database cache.",

            CacheStorage.NOSQL:
                "NoSQL database cache.",

            CacheStorage.S3:
                "Object storage cache.",

            CacheStorage.FILESYSTEM:
                "Local filesystem cache.",

            CacheStorage.CUSTOM:
                "Application-defined cache storage.",

            CacheStorage.UNKNOWN:
                "Cache storage has not yet been identified."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Good frameworks don't care
# where information lives.
#
# Today...
#
# DynamoDB.
#
# Tomorrow...
#
# Redis.
#
# Five years from now...
#
# Something we've never heard of.
#
# Software should survive
# infrastructure changes.
#
# =============================================================================


# =============================================================================
# Cache Ownership
# =============================================================================


class CacheOwnership(Gen2XEnum):
    """
    Describes who owns cached information.

    Ownership answers:

        "Who is responsible for this cache?"

    Ownership becomes especially important when determining:

        • Expiration

        • Refresh

        • Invalidation

        • Governance

    Good cache management requires clear ownership.
    """

    PROVIDER = "PROVIDER"

    FRAMEWORK = "FRAMEWORK"

    APPLICATION = "APPLICATION"

    SYSTEM = "SYSTEM"

    USER = "USER"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of cache ownership.
        """

        descriptions = {

            CacheOwnership.PROVIDER:
                "Owned by an external intelligence provider.",

            CacheOwnership.FRAMEWORK:
                "Owned by the Gen2X framework.",

            CacheOwnership.APPLICATION:
                "Owned by the application using Gen2X.",

            CacheOwnership.SYSTEM:
                "Managed by the hosting platform.",

            CacheOwnership.USER:
                "Managed directly by a user or administrator.",

            CacheOwnership.UNKNOWN:
                "Ownership has not yet been determined."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Imagine an intelligence provider
# publishes new information.
#
# Who refreshes the cache?
#
# The provider?
#
# The framework?
#
# An administrator?
#
# Ownership determines
# who is responsible
# for maintaining trust
# in cached evidence.
#
# Clear ownership prevents
# stale intelligence from
# quietly living forever.
#
# =============================================================================


# =============================================================================
# Cache Result
# =============================================================================


class CacheResult(Gen2XEnum):
    """
    Describes the outcome of a cache operation.

    CacheResult answers:

        "Did the cache operation complete successfully?"

    CacheResult describes execution.

    It does not describe lookup status.

    Those concepts intentionally remain separate.
    """

    SUCCESS = "SUCCESS"

    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"

    FAILED = "FAILED"

    TIMED_OUT = "TIMED_OUT"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of cache results.
        """

        descriptions = {

            CacheResult.SUCCESS:
                "The cache operation completed successfully.",

            CacheResult.PARTIAL_SUCCESS:
                "The cache operation completed with limited success.",

            CacheResult.FAILED:
                "The cache operation failed.",

            CacheResult.TIMED_OUT:
                "The cache operation exceeded the allowed execution time.",

            CacheResult.UNKNOWN:
                "The cache result has not yet been determined."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Cache Status answers:
#
#     "Did I find it?"
#
# Cache Result answers:
#
#     "Did the cache operation succeed?"
#
# Similar words.
#
# Completely different questions.
#
# Engineers become architects
# when they begin separating
# concepts that initially
# seem identical.
#
# =============================================================================


# =============================================================================
# Public Module Interface
# =============================================================================

__all__ = [

    "CacheType",

    "CacheScope",

    "CachePolicy",

    "CacheStatus",

    "CacheFreshness",

    "CacheStorage",

    "CacheOwnership",

    "CacheResult",

]


# =============================================================================
#
# Architect's Reflection
#
# This module defines vocabulary.
#
# It does not perform cache lookups.
#
# It does not call Redis.
#
# It does not communicate with DynamoDB.
#
# It does not enforce expiration policies.
#
# It does not invalidate entries.
#
# Frameworks become easier to maintain
# when they separate:
#
#     Vocabulary
#
# from
#
#     Behavior
#
# The caching engine implements policy.
#
# This module simply provides
# the language used to describe it.
#
# As Gen2X grows,
# new storage systems,
# cloud providers,
# and distributed cache technologies
# can be introduced without changing
# the framework's vocabulary.
#
# Good frameworks are remembered
# not because they contain
# clever code...
#
# but because they organize
# complicated ideas
# into simple language.
#
#                               — Chewbacca
#                                 Chief Wookiee Architect
#
# =============================================================================
