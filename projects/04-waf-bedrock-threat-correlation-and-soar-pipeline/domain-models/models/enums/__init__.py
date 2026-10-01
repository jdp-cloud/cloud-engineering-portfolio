"""
===============================================================================

 Gen2X Security Engineering Platform

 Package:
     models.enums

===============================================================================

Overview
-------------------------------------------------------------------------------

Welcome to the Gen2X Enumeration Framework.

This package provides the public enumeration API used throughout the
Gen2X Security Engineering Platform.

Enumerations define the shared vocabulary spoken by every component in
the framework.

Examples include:

    • Risk Levels
    • Provider Status
    • Indicator Types
    • Threat Categories
    • Report Status
    • Response Status

Rather than allowing arbitrary strings throughout the platform, Gen2X
defines a strongly typed language using Python Enumerations.

Every component in the framework uses these shared definitions.

-------------------------------------------------------------------------------

Why Does This Package Exist?

Imagine a platform with hundreds of source files.

One developer writes

    "HIGH"

Another writes

    "high"

Another writes

    "Critical"

Another writes

    "CRIT"

Everything technically works...

until one day it doesn't.

Enterprise software solves this problem by defining a shared vocabulary.

Instead of writing strings, developers write:

    RiskLevel.HIGH

The compiler, IDE, and framework all understand exactly what that means.

-------------------------------------------------------------------------------

Public API

One of the primary goals of Gen2X is API Stability.

Users of the framework should import objects from this package rather
than individual implementation modules.

Correct

    from models.enums import ReportStatus

Instead of

    from models.enums.report_enums import ReportStatus

Why?

Because implementation details change.

Public APIs should remain stable.

This allows the framework to evolve without breaking existing code.

-------------------------------------------------------------------------------

Architectural Pattern

One of the educational goals of Gen2X is demonstrating that enterprise
software follows repeatable design patterns.

Every major package follows the same layout.

models/

    __init__.py
    base_model.py
    ...

providers/

    __init__.py
    base_provider.py
    ...

enums/

    __init__.py
    base_enum.py
    ...

Notice the repetition.

This is intentional.

Once you understand one package, you can navigate every package in
the framework.

Large software systems become manageable because they are built from
consistent architectural patterns rather than unrelated files.

-------------------------------------------------------------------------------

Responsibilities

This package is responsible for

    ✓ Providing the public enumeration API

    ✓ Organizing domain-specific enumerations

    ✓ Hiding internal implementation details

    ✓ Maintaining API consistency

    ✓ Promoting type safety

This package is NOT responsible for

    ✗ Threat Intelligence

    ✗ Business Logic

    ✗ Providers

    ✗ Reports

    ✗ AI

-------------------------------------------------------------------------------

For Students

You may wonder why this file exists.

After all...

Couldn't everyone simply import directly from the individual modules?

Technically...

Yes.

Professionally...

Usually not.

Enterprise software often hides its internal implementation and exposes
only a carefully designed public interface.

That interface is what developers build against.

This separation gives framework authors the freedom to reorganize the
internal implementation without breaking applications that depend on it.

As you progress through Gen2X, you'll notice this same architectural
pattern repeated throughout the framework.

This is not accidental.

Repetition creates familiarity.

Familiarity reduces complexity.

-------------------------------------------------------------------------------

Think Like a Framework Architect

When reading Gen2X, try asking yourself questions like:

    Why was this package created?

    What belongs here?

    What does NOT belong here?

    Why is there a base class?

    Why expose only certain objects?

Learning to ask these questions is often more valuable than memorizing
Python syntax.

Software architects spend much of their time organizing systems rather
than writing algorithms.

Gen2X is designed to help you develop that mindset.

===============================================================================
"""

# =============================================================================
# Base Framework Classes
# =============================================================================
#
# Every enumeration in Gen2X ultimately inherits from Gen2XEnum.
#
# This base class provides common behavior shared across every enumeration,
# including helper methods, validation, serialization, and documentation hooks.
#
# Rather than rewriting the same functionality repeatedly, all specialized
# enumerations inherit from a common foundation.
#
# This mirrors the design of BaseModel and BaseProvider throughout the
# framework.
#
# =============================================================================

from .base_enum import Gen2XEnum

# =============================================================================
# Indicator Enumerations
# =============================================================================
#
# Enumerations describing indicators and observable data.
#
# Examples:
#
#     IndicatorType.IPV4
#
#     IndicatorType.DOMAIN
#
#     IndicatorConfidence.HIGH
#
# =============================================================================

from .indicator_enums import (
    IndicatorType,
    IndicatorSource,
    IndicatorConfidence,
)

# =============================================================================
# Provider Enumerations
# =============================================================================
#
# Enumerations describing provider execution and capabilities.
#
# Examples:
#
#     ProviderStatus.SUCCESS
#
#     ProviderStatus.TIMEOUT
#
#     ProviderType.OPEN_SOURCE
#
# =============================================================================

from .provider_enums import (
    ProviderStatus,
    ProviderType,
    ProviderCapability,
    ProviderHealth,
    ProviderTrustLevel,
)

# =============================================================================
# Threat Enumerations
# =============================================================================
#
# Enumerations used by threat analysis: classification, location, observed
# conditions, severity, confidence, assessment, investigation workflow,
# disposition, attribution, and activity patterns.
#
# =============================================================================

from .threat_enums import (
    ThreatType,
    ThreatDomain,
    ThreatCondition,
    ThreatSeverity,
    ThreatConfidence,
    ThreatAssessment,
    ThreatStatus,
    ThreatDisposition,
    ThreatActorType,
    ThreatActivityPattern,
    InvestigationStatus,
)

# =============================================================================
# Report Enumerations
# =============================================================================
#
# Enumerations used while generating reports and findings.
#
# =============================================================================

from .report_enums import (
    ReportType,
    ReportStatus,
    ReportFormat,
    ReportAudience,
    ReportTechnicalLevel,
    FindingSeverity,
    RecommendationPriority,
    RecommendationCategory,
)

# =============================================================================
# Response Enumerations
# =============================================================================
#
# Enumerations representing the response planning and execution workflow.
#
# =============================================================================

from .response_enums import (
    ResponseAction,
    ResponseMode,
    ResponseApproval,
    ApprovalMode,
    ResponseOwner,
    ResponsePriority,
    ResponseStatus,
    ResponseOutcome,
    ResponseVerification,
)

# =============================================================================
# Cache Enumerations
# =============================================================================
#
# Enumerations describing cached evidence: what is stored, who may reuse it,
# retrieval strategy, lookup status, freshness, storage, ownership, and
# operation results.
#
# =============================================================================

from .cache_enums import (
    CacheType,
    CacheScope,
    CachePolicy,
    CacheStatus,
    CacheFreshness,
    CacheStorage,
    CacheOwnership,
    CacheResult,
)

# =============================================================================
# Platform Enumerations
# =============================================================================
#
# Enumerations describing the platform itself: architectural identity,
# behavior, and operational state.
#
# =============================================================================

from .platform_enums import (
    PlatformType,
    PlatformRole,
    PlatformResponsibility,
    PlatformComponent,
    PlatformService,
    PlatformCapability,
    PlatformEnvironment,
    PlatformDeployment,
    PlatformLifecycle,
    PlatformState,
    PlatformHealth,
    PlatformTrustLevel,
)

# =============================================================================
# Public Package Interface
# =============================================================================
#
# __all__ explicitly defines the public interface of this package.
#
# Although Python does not require __all__, many mature frameworks define it
# to clearly communicate which objects are intended for public use.
#
# Think of __all__ as the front door of the package.
#
# Everything listed here is part of the supported public API.
#
# Internal implementation details remain hidden.
#
# =============================================================================

__all__ = [

    # -------------------------------------------------------------------------
    # Base Classes
    # -------------------------------------------------------------------------

    "Gen2XEnum",

    # -------------------------------------------------------------------------
    # Indicator Enumerations
    # -------------------------------------------------------------------------

    "IndicatorType",
    "IndicatorSource",
    "IndicatorConfidence",

    # -------------------------------------------------------------------------
    # Provider Enumerations
    # -------------------------------------------------------------------------

    "ProviderStatus",
    "ProviderType",
    "ProviderCapability",
    "ProviderHealth",
    "ProviderTrustLevel",

    # -------------------------------------------------------------------------
    # Threat Enumerations
    # -------------------------------------------------------------------------

    "ThreatType",
    "ThreatDomain",
    "ThreatCondition",
    "ThreatSeverity",
    "ThreatConfidence",
    "ThreatAssessment",
    "ThreatStatus",
    "ThreatDisposition",
    "ThreatActorType",
    "ThreatActivityPattern",
    "InvestigationStatus",

    # -------------------------------------------------------------------------
    # Report Enumerations
    # -------------------------------------------------------------------------

    "ReportType",
    "ReportStatus",
    "ReportFormat",
    "ReportAudience",
    "ReportTechnicalLevel",
    "FindingSeverity",
    "RecommendationPriority",
    "RecommendationCategory",

    # -------------------------------------------------------------------------
    # Response Enumerations
    # -------------------------------------------------------------------------

    "ResponseAction",
    "ResponseMode",
    "ResponseApproval",
    "ApprovalMode",
    "ResponseOwner",
    "ResponsePriority",
    "ResponseStatus",
    "ResponseOutcome",
    "ResponseVerification",

    # -------------------------------------------------------------------------
    # Cache Enumerations
    # -------------------------------------------------------------------------

    "CacheType",
    "CacheScope",
    "CachePolicy",
    "CacheStatus",
    "CacheFreshness",
    "CacheStorage",
    "CacheOwnership",
    "CacheResult",

    # -------------------------------------------------------------------------
    # Platform Enumerations
    # -------------------------------------------------------------------------

    "PlatformType",
    "PlatformRole",
    "PlatformResponsibility",
    "PlatformComponent",
    "PlatformService",
    "PlatformCapability",
    "PlatformEnvironment",
    "PlatformDeployment",
    "PlatformLifecycle",
    "PlatformState",
    "PlatformHealth",
    "PlatformTrustLevel",
]
