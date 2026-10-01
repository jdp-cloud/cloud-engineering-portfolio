"""
===============================================================================

Gen2X Security Engineering Platform

Module:
    platform_enums.py

===============================================================================

Overview
-------------------------------------------------------------------------------

This module defines the enumerations used throughout the Gen2X Platform
Framework.

Unlike previous enum modules that describe observations, evidence,
analysis, reporting, or response, this module describes the platform
itself.

The platform coordinates every subsystem within Gen2X.

Examples include:

    • Agents
    • Providers
    • Models
    • Fusion
    • Cache
    • Reporting
    • Compliance
    • Response
    • Observability

Platform enums provide a common vocabulary for describing the
architecture rather than individual investigations.

-------------------------------------------------------------------------------

Architectural Philosophy

Indicators describe observations.

Providers describe evidence.

Threats describe reasoning.

Reports describe communication.

Responses describe decisions.

Cache describes organizational memory.

Platform describes the software system that coordinates them all.

-------------------------------------------------------------------------------

Platform Architecture

                Platform

                     │

        ┌────────────┼────────────┐

        ▼            ▼            ▼

     Components   Services    Responsibilities

                     │

                     ▼

               Business Value

Good architecture organizes software according to responsibility rather
than technology.

===============================================================================

Chewbacca's Commentary 🐾

Software platforms are cities.

Many buildings.

Many roads.

Many services.

One purpose.

Good architecture isn't about making one
building perfect.

It's about helping the entire city work
together.

                                — Chewbacca
                                  Chief Wookiee Architect

===============================================================================
"""

from __future__ import annotations

from .base_enum import Gen2XEnum


# =============================================================================
# Platform Type
# =============================================================================


class PlatformType(Gen2XEnum):
    """
    Describes the external platform a provider observes or integrates
    with.

    PlatformType answers one question:

        "Which platform does this observation come from?"

    PlatformType describes the outside world.

    The other enumerations in this module describe Gen2X itself.

    Example

        Wiz observes AWS.

        GitHub Secret Scanning observes GITHUB.

        An internal CMDB observes ON_PREMISES.
    """

    # -------------------------------------------------------------------------
    # Cloud Platforms
    # -------------------------------------------------------------------------

    AWS = "AWS"

    AZURE = "AZURE"

    GCP = "GCP"

    MULTI_CLOUD = "MULTI_CLOUD"

    # -------------------------------------------------------------------------
    # Source Platforms
    # -------------------------------------------------------------------------

    GITHUB = "GITHUB"

    GITLAB = "GITLAB"

    # -------------------------------------------------------------------------
    # Infrastructure
    # -------------------------------------------------------------------------

    KUBERNETES = "KUBERNETES"

    ON_PREMISES = "ON_PREMISES"

    SAAS = "SAAS"

    # -------------------------------------------------------------------------
    # General
    # -------------------------------------------------------------------------

    OTHER = "OTHER"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of the platform type.
        """

        descriptions = {

            PlatformType.AWS:
                "Amazon Web Services.",

            PlatformType.AZURE:
                "Microsoft Azure.",

            PlatformType.GCP:
                "Google Cloud Platform.",

            PlatformType.MULTI_CLOUD:
                "Spans more than one cloud platform.",

            PlatformType.GITHUB:
                "GitHub repositories and services.",

            PlatformType.GITLAB:
                "GitLab repositories and services.",

            PlatformType.KUBERNETES:
                "Kubernetes clusters and workloads.",

            PlatformType.ON_PREMISES:
                "On-premises infrastructure.",

            PlatformType.SAAS:
                "Software-as-a-Service applications.",

            PlatformType.OTHER:
                "Application-defined platform.",

            PlatformType.UNKNOWN:
                "Platform has not yet been classified."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Providers watch
# different worlds.
#
# One watches AWS.
#
# One watches GitHub.
#
# One watches
# the server room
# down the hall.
#
# Evidence should always remember
# which world it came from.
#
# =============================================================================


# =============================================================================
# Platform Role
# =============================================================================


class PlatformRole(Gen2XEnum):
    """
    Describes the architectural role of a software component.

    PlatformRole answers one question:

        "What kind of software is this?"

    Roles define identity.

    They do not define responsibilities.

    Example

        Framework

    and

        Service

    may both perform orchestration, but they play very different roles
    within the platform.
    """

    # -------------------------------------------------------------------------
    # Architectural Layers
    # -------------------------------------------------------------------------

    FRAMEWORK = "FRAMEWORK"

    APPLICATION = "APPLICATION"

    SERVICE = "SERVICE"

    LIBRARY = "LIBRARY"

    # -------------------------------------------------------------------------
    # Extension Points
    # -------------------------------------------------------------------------

    PLUGIN = "PLUGIN"

    ADAPTER = "ADAPTER"

    TOOL = "TOOL"

    # -------------------------------------------------------------------------
    # General
    # -------------------------------------------------------------------------

    CUSTOM = "CUSTOM"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of the platform role.
        """

        descriptions = {

            PlatformRole.FRAMEWORK:
                "Provides architectural structure for applications.",

            PlatformRole.APPLICATION:
                "Solves a specific business problem using the framework.",

            PlatformRole.SERVICE:
                "Provides runtime functionality to the platform.",

            PlatformRole.LIBRARY:
                "Offers reusable software components.",

            PlatformRole.PLUGIN:
                "Extends platform capabilities without modifying the core.",

            PlatformRole.ADAPTER:
                "Connects Gen2X to external systems or providers.",

            PlatformRole.TOOL:
                "Supports development, testing, or operations.",

            PlatformRole.CUSTOM:
                "Application-defined software role.",

            PlatformRole.UNKNOWN:
                "Platform role has not yet been classified."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Many engineers organize software
# by programming language.
#
# Others organize software
# by cloud provider.
#
# Architects organize software
# by purpose.
#
# Technologies change.
#
# Responsibilities remain.
#
# Build around ideas.
#
# Not products.
#
# =============================================================================


# =============================================================================
# Platform Responsibility
# =============================================================================


class PlatformResponsibility(Gen2XEnum):
    """
    Describes the primary architectural responsibility of a platform
    component.

    PlatformResponsibility answers one question:

        "What promise does this component make to the platform?"

    Responsibilities define WHY a component exists.

    Implementations may change.

    Responsibilities should remain stable.

    This principle allows platforms to evolve without constantly changing
    their architecture.
    """

    # -------------------------------------------------------------------------
    # Data Acquisition
    # -------------------------------------------------------------------------

    INGESTION = "INGESTION"

    COLLECTION = "COLLECTION"

    ENRICHMENT = "ENRICHMENT"

    # -------------------------------------------------------------------------
    # Analysis
    # -------------------------------------------------------------------------

    CORRELATION = "CORRELATION"

    ANALYSIS = "ANALYSIS"

    VALIDATION = "VALIDATION"

    CLASSIFICATION = "CLASSIFICATION"

    # -------------------------------------------------------------------------
    # Platform Services
    # -------------------------------------------------------------------------

    STORAGE = "STORAGE"

    CACHING = "CACHING"

    ORCHESTRATION = "ORCHESTRATION"

    COMMUNICATION = "COMMUNICATION"

    OBSERVABILITY = "OBSERVABILITY"

    # -------------------------------------------------------------------------
    # Governance
    # -------------------------------------------------------------------------

    COMPLIANCE = "COMPLIANCE"

    REPORTING = "REPORTING"

    RESPONSE = "RESPONSE"

    AUDITING = "AUDITING"

    SECURITY = "SECURITY"

    # -------------------------------------------------------------------------
    # General
    # -------------------------------------------------------------------------

    CUSTOM = "CUSTOM"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of the platform
        responsibility.
        """

        descriptions = {

            PlatformResponsibility.INGESTION:
                "Accepts information entering the platform.",

            PlatformResponsibility.COLLECTION:
                "Collects information from internal or external systems.",

            PlatformResponsibility.ENRICHMENT:
                "Adds context to existing evidence.",

            PlatformResponsibility.CORRELATION:
                "Combines evidence from multiple sources.",

            PlatformResponsibility.ANALYSIS:
                "Evaluates information to produce findings.",

            PlatformResponsibility.VALIDATION:
                "Verifies evidence using deterministic rules.",

            PlatformResponsibility.CLASSIFICATION:
                "Assigns categories, labels, or priorities.",

            PlatformResponsibility.STORAGE:
                "Persists platform information.",

            PlatformResponsibility.CACHING:
                "Reuses previously collected information.",

            PlatformResponsibility.ORCHESTRATION:
                "Coordinates workflows across platform components.",

            PlatformResponsibility.COMMUNICATION:
                "Exchanges information with external systems.",

            PlatformResponsibility.OBSERVABILITY:
                "Measures platform behavior and health.",

            PlatformResponsibility.COMPLIANCE:
                "Evaluates governance requirements.",

            PlatformResponsibility.REPORTING:
                "Communicates platform findings.",

            PlatformResponsibility.RESPONSE:
                "Coordinates operational actions.",

            PlatformResponsibility.AUDITING:
                "Maintains historical evidence and activity.",

            PlatformResponsibility.SECURITY:
                "Protects platform resources and operations.",

            PlatformResponsibility.CUSTOM:
                "Application-defined responsibility.",

            PlatformResponsibility.UNKNOWN:
                "Responsibility has not yet been classified."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Engineers often organize software
# by programming language.
#
# Or by cloud service.
#
# Architecture asks
# a different question.
#
# What responsibility
# does this component own?
#
# If two components own
# the same responsibility...
#
# perhaps they should become one.
#
# If one component owns
# ten responsibilities...
#
# perhaps it should become ten.
#
# Good software isn't measured
# by file count.
#
# It's measured by clarity
# of responsibility.
#
# =============================================================================


# =============================================================================
# Platform Component
# =============================================================================


class PlatformComponent(Gen2XEnum):
    """
    Describes the major architectural components of the Gen2X platform.

    Components divide the platform into independently understandable
    subsystems.

    Components answer one question:

        "Which part of the platform am I describing?"
    """

    INGESTION = "INGESTION"

    ORCHESTRATION = "ORCHESTRATION"

    PROVIDERS = "PROVIDERS"

    MODELS = "MODELS"

    CACHE = "CACHE"

    FUSION = "FUSION"

    THREAT_ANALYSIS = "THREAT_ANALYSIS"

    REPORTING = "REPORTING"

    RESPONSE = "RESPONSE"

    COMPLIANCE = "COMPLIANCE"

    OBSERVABILITY = "OBSERVABILITY"

    API = "API"

    STORAGE = "STORAGE"

    SECURITY = "SECURITY"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of the platform component.
        """

        descriptions = {

            PlatformComponent.INGESTION:
                "Receives events and incoming information.",

            PlatformComponent.ORCHESTRATION:
                "Coordinates workflows between platform components.",

            PlatformComponent.PROVIDERS:
                "Interfaces with external intelligence providers.",

            PlatformComponent.MODELS:
                "Contains shared domain models and enumerations.",

            PlatformComponent.CACHE:
                "Stores reusable platform intelligence.",

            PlatformComponent.FUSION:
                "Correlates evidence from multiple providers.",

            PlatformComponent.THREAT_ANALYSIS:
                "Performs security reasoning and analysis.",

            PlatformComponent.REPORTING:
                "Generates reports and dashboards.",

            PlatformComponent.RESPONSE:
                "Coordinates operational recommendations.",

            PlatformComponent.COMPLIANCE:
                "Evaluates security controls.",

            PlatformComponent.OBSERVABILITY:
                "Provides logging, metrics, and monitoring.",

            PlatformComponent.API:
                "Exposes platform interfaces.",

            PlatformComponent.STORAGE:
                "Persists platform information.",

            PlatformComponent.SECURITY:
                "Protects platform infrastructure.",

            PlatformComponent.UNKNOWN:
                "Component has not yet been classified."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Imagine placing
# every feature
# inside one Lambda.
#
# ...
#
# Please don't.
#
# Components separate
# responsibilities.
#
# Separation creates
# maintainability.
#
# Great platforms are built
# from small, understandable pieces
# working together.
#
# =============================================================================


# =============================================================================
# Platform Service
# =============================================================================


class PlatformService(Gen2XEnum):
    """
    Describes the shared runtime services the platform provides to its
    components.

    PlatformService answers one question:

        "What common function does the platform offer?"

    Services are the utilities every component may rely upon.

    A service is NOT:

        • A component

            Components are subsystems. Services support them.

        • A capability

            Capabilities describe business value. Services describe
            shared machinery.

    Example

        The Reporting component

        uses the NOTIFICATION service

        to deliver the EXECUTIVE_REPORTING capability.
    """

    # -------------------------------------------------------------------------
    # Identity and Access
    # -------------------------------------------------------------------------

    AUTHENTICATION = "AUTHENTICATION"

    AUTHORIZATION = "AUTHORIZATION"

    SECRETS_MANAGEMENT = "SECRETS_MANAGEMENT"

    # -------------------------------------------------------------------------
    # Communication
    # -------------------------------------------------------------------------

    MESSAGING = "MESSAGING"

    EVENT_BUS = "EVENT_BUS"

    NOTIFICATION = "NOTIFICATION"

    # -------------------------------------------------------------------------
    # Operations
    # -------------------------------------------------------------------------

    SCHEDULING = "SCHEDULING"

    LOGGING = "LOGGING"

    METRICS = "METRICS"

    TRACING = "TRACING"

    ALERTING = "ALERTING"

    # -------------------------------------------------------------------------
    # Data
    # -------------------------------------------------------------------------

    PERSISTENCE = "PERSISTENCE"

    CONFIGURATION = "CONFIGURATION"

    # -------------------------------------------------------------------------
    # General
    # -------------------------------------------------------------------------

    CUSTOM = "CUSTOM"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of the platform service.
        """

        descriptions = {

            PlatformService.AUTHENTICATION:
                "Verifies the identity of users, agents, and systems.",

            PlatformService.AUTHORIZATION:
                "Determines what an authenticated identity may do.",

            PlatformService.SECRETS_MANAGEMENT:
                "Stores and retrieves credentials and sensitive material.",

            PlatformService.MESSAGING:
                "Moves information between platform components.",

            PlatformService.EVENT_BUS:
                "Distributes events to interested platform components.",

            PlatformService.NOTIFICATION:
                "Delivers information to humans and external systems.",

            PlatformService.SCHEDULING:
                "Executes work at defined times or intervals.",

            PlatformService.LOGGING:
                "Records platform activity for troubleshooting and audit.",

            PlatformService.METRICS:
                "Measures platform behavior over time.",

            PlatformService.TRACING:
                "Follows requests as they travel through the platform.",

            PlatformService.ALERTING:
                "Raises attention when defined conditions occur.",

            PlatformService.PERSISTENCE:
                "Stores platform information durably.",

            PlatformService.CONFIGURATION:
                "Provides settings that control platform behavior.",

            PlatformService.CUSTOM:
                "Application-defined platform service.",

            PlatformService.UNKNOWN:
                "Platform service has not yet been classified."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Every component needs
# to log.
#
# Every component needs
# configuration.
#
# Every component needs
# to tell someone
# when something happens.
#
# Should every component
# build those things
# itself?
#
# Absolutely not.
#
# Shared services exist
# so components can focus
# on their own responsibility.
#
# Build it once.
#
# Share it everywhere.
#
# =============================================================================


# =============================================================================
# Platform Capability
# =============================================================================


class PlatformCapability(Gen2XEnum):
    """
    Describes the business capabilities provided by the platform.

    PlatformCapability answers one question:

        "What can this platform accomplish?"

    Capabilities describe business value rather than software structure.

    Multiple components may work together to provide a single capability.

    Likewise, one component may support many capabilities.

    Capabilities remain relatively stable even when implementations change.
    """

    # -------------------------------------------------------------------------
    # Intelligence
    # -------------------------------------------------------------------------

    AI_ANALYSIS = "AI_ANALYSIS"

    THREAT_INTELLIGENCE = "THREAT_INTELLIGENCE"

    # -------------------------------------------------------------------------
    # Security
    # -------------------------------------------------------------------------

    COMPLIANCE = "COMPLIANCE"

    SOAR = "SOAR"

    RESPONSE_ORCHESTRATION = "RESPONSE_ORCHESTRATION"

    # -------------------------------------------------------------------------
    # Reporting
    # -------------------------------------------------------------------------

    EXECUTIVE_REPORTING = "EXECUTIVE_REPORTING"

    DASHBOARDS = "DASHBOARDS"

    # -------------------------------------------------------------------------
    # Platform
    # -------------------------------------------------------------------------

    API = "API"

    OBSERVABILITY = "OBSERVABILITY"

    PLUGIN_SUPPORT = "PLUGIN_SUPPORT"

    MULTI_CLOUD = "MULTI_CLOUD"

    EXTENSIBILITY = "EXTENSIBILITY"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of the platform capability.
        """

        descriptions = {

            PlatformCapability.AI_ANALYSIS:
                "Uses artificial intelligence to assist with analysis.",

            PlatformCapability.THREAT_INTELLIGENCE:
                "Collects and correlates external threat intelligence.",

            PlatformCapability.COMPLIANCE:
                "Evaluates security controls against governance frameworks.",

            PlatformCapability.SOAR:
                "Supports Security Orchestration, Automation, and Response.",

            PlatformCapability.RESPONSE_ORCHESTRATION:
                "Coordinates operational response workflows.",

            PlatformCapability.EXECUTIVE_REPORTING:
                "Produces executive-level security reports.",

            PlatformCapability.DASHBOARDS:
                "Provides operational dashboards and visualizations.",

            PlatformCapability.API:
                "Exposes platform capabilities through APIs.",

            PlatformCapability.OBSERVABILITY:
                "Provides logging, monitoring, and metrics.",

            PlatformCapability.PLUGIN_SUPPORT:
                "Allows capabilities to be extended through plugins.",

            PlatformCapability.MULTI_CLOUD:
                "Supports multiple cloud providers.",

            PlatformCapability.EXTENSIBILITY:
                "Supports future platform extensions.",

            PlatformCapability.UNKNOWN:
                "Capability has not yet been classified."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Components are pieces
# of software.
#
# Capabilities are things
# the platform accomplishes.
#
# One reporting component
# may generate
#
#     • PDF reports
#     • JSON output
#     • Executive dashboards
#     • Compliance summaries
#
# Same component.
#
# Many capabilities.
#
# Build around value.
#
# Not implementation.
#
# =============================================================================


# =============================================================================
# Platform Environment
# =============================================================================


class PlatformEnvironment(Gen2XEnum):
    """
    Describes the environment where the platform is executing.

    PlatformEnvironment answers one question:

        "Where is this platform running?"

    Environments represent operational context rather than deployment
    technology.
    """

    LOCAL = "LOCAL"

    LAB = "LAB"

    DEVELOPMENT = "DEVELOPMENT"

    TEST = "TEST"

    STAGING = "STAGING"

    PRODUCTION = "PRODUCTION"

    SANDBOX = "SANDBOX"

    ON_PREMISES = "ON_PREMISES"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of the platform environment.
        """

        descriptions = {

            PlatformEnvironment.LOCAL:
                "Running on a developer workstation.",

            PlatformEnvironment.LAB:
                "Running inside a controlled learning environment.",

            PlatformEnvironment.DEVELOPMENT:
                "Running during active software development.",

            PlatformEnvironment.TEST:
                "Running within a testing environment.",

            PlatformEnvironment.STAGING:
                "Running within a production-like staging environment.",

            PlatformEnvironment.PRODUCTION:
                "Running in the live production environment.",

            PlatformEnvironment.SANDBOX:
                "Running inside an isolated experimentation environment.",

            PlatformEnvironment.ON_PREMISES:
                "Running within an organization's on-premises infrastructure.",

            PlatformEnvironment.UNKNOWN:
                "Environment has not yet been classified."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Production
#
# should never become
#
# your testing environment.
#
# (History suggests
# many engineers
# learned this
# the exciting way.)
#
# Laboratories exist
# so customers don't become
# your beta testers.
#
# =============================================================================


# =============================================================================
# Platform Deployment
# =============================================================================


class PlatformDeployment(Gen2XEnum):
    """
    Describes the deployment architecture used by the platform.

    PlatformDeployment answers:

        "How is the platform deployed?"

    Deployment describes architecture.

    It does not describe cloud vendors.
    """

    SERVERLESS = "SERVERLESS"

    CONTAINERS = "CONTAINERS"

    VIRTUAL_MACHINE = "VIRTUAL_MACHINE"

    BARE_METAL = "BARE_METAL"

    EDGE = "EDGE"

    HYBRID = "HYBRID"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of deployment architecture.
        """

        descriptions = {

            PlatformDeployment.SERVERLESS:
                "Uses event-driven serverless compute.",

            PlatformDeployment.CONTAINERS:
                "Runs inside containerized workloads.",

            PlatformDeployment.VIRTUAL_MACHINE:
                "Runs on virtual machines.",

            PlatformDeployment.BARE_METAL:
                "Runs directly on physical hardware.",

            PlatformDeployment.EDGE:
                "Runs near the edge of the network.",

            PlatformDeployment.HYBRID:
                "Combines multiple deployment models.",

            PlatformDeployment.UNKNOWN:
                "Deployment architecture has not yet been identified."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Lambda
#
# is not
#
# Serverless.
#
# Lambda is
#
# one implementation
#
# of serverless.
#
# Good architects
# separate
#
# architectural patterns
#
# from
#
# vendor products.
#
# =============================================================================


# =============================================================================
# Platform Lifecycle
# =============================================================================


class PlatformLifecycle(Gen2XEnum):
    """
    Describes the maturity of the platform.

    PlatformLifecycle answers:

        "Where is the platform in its evolution?"
    """

    DESIGN = "DESIGN"

    PROTOTYPE = "PROTOTYPE"

    DEVELOPMENT = "DEVELOPMENT"

    TESTING = "TESTING"

    PILOT = "PILOT"

    PRODUCTION = "PRODUCTION"

    DEPRECATED = "DEPRECATED"

    RETIRED = "RETIRED"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of lifecycle state.
        """

        descriptions = {

            PlatformLifecycle.DESIGN:
                "Platform architecture is being designed.",

            PlatformLifecycle.PROTOTYPE:
                "Platform concepts are being validated.",

            PlatformLifecycle.DEVELOPMENT:
                "Platform is under active development.",

            PlatformLifecycle.TESTING:
                "Platform functionality is being verified.",

            PlatformLifecycle.PILOT:
                "Platform is undergoing limited production evaluation.",

            PlatformLifecycle.PRODUCTION:
                "Platform is fully operational.",

            PlatformLifecycle.DEPRECATED:
                "Platform is being phased out.",

            PlatformLifecycle.RETIRED:
                "Platform is no longer supported.",

            PlatformLifecycle.UNKNOWN:
                "Lifecycle state has not yet been determined."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Every platform
# starts somewhere.
#
# Even the largest systems
# began as
#
# one idea...
#
# one prototype...
#
# one engineer...
#
# and probably
#
# one late-night debugging session.
#
# Good platforms evolve.
#
# Great platforms
# are designed
# to evolve gracefully.
#
# =============================================================================


# =============================================================================
# Platform State
# =============================================================================


class PlatformState(Gen2XEnum):
    """
    Describes the current operational state of the platform.

    PlatformState answers one question:

        "What is happening right now?"

    State is dynamic.

    It may change many times during normal platform operation.

    State should never be confused with health or trust.

    Those concepts are represented separately.
    """

    # -------------------------------------------------------------------------
    # Startup
    # -------------------------------------------------------------------------

    INITIALIZING = "INITIALIZING"

    # -------------------------------------------------------------------------
    # Normal Operations
    # -------------------------------------------------------------------------

    READY = "READY"

    BUSY = "BUSY"

    # -------------------------------------------------------------------------
    # Maintenance
    # -------------------------------------------------------------------------

    MAINTENANCE = "MAINTENANCE"

    # -------------------------------------------------------------------------
    # Operational Issues
    # -------------------------------------------------------------------------

    DEGRADED = "DEGRADED"

    STOPPED = "STOPPED"

    ERROR = "ERROR"

    # -------------------------------------------------------------------------
    # General
    # -------------------------------------------------------------------------

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of the current platform state.
        """

        descriptions = {

            PlatformState.INITIALIZING:
                "The platform is starting.",

            PlatformState.READY:
                "The platform is operational and accepting work.",

            PlatformState.BUSY:
                "The platform is actively processing workloads.",

            PlatformState.MAINTENANCE:
                "The platform is temporarily unavailable for maintenance.",

            PlatformState.DEGRADED:
                "The platform is operating with reduced capability.",

            PlatformState.STOPPED:
                "The platform is not currently running.",

            PlatformState.ERROR:
                "The platform encountered an operational failure.",

            PlatformState.UNKNOWN:
                "Platform state has not yet been determined."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Systems are living things.
#
# Well...
#
# mostly.
#
# Their operational state
# changes continuously.
#
# A busy system
#
# isn't necessarily
#
# a broken system.
#
# Good monitoring
#
# understands
#
# the difference.
#
# =============================================================================


# =============================================================================
# Platform Health
# =============================================================================


class PlatformHealth(Gen2XEnum):
    """
    Describes the operational health of the platform.

    PlatformHealth answers one question:

        "How healthy is the platform?"

    Health represents operational quality rather than current activity.

    A platform may be busy and healthy.

    It may also be idle and unhealthy.

    These concepts intentionally remain independent.
    """

    HEALTHY = "HEALTHY"

    WARNING = "WARNING"

    DEGRADED = "DEGRADED"

    RECOVERING = "RECOVERING"

    UNAVAILABLE = "UNAVAILABLE"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of platform health.
        """

        descriptions = {

            PlatformHealth.HEALTHY:
                "Platform is operating normally.",

            PlatformHealth.WARNING:
                "Platform is experiencing minor operational concerns.",

            PlatformHealth.DEGRADED:
                "Platform functionality has been reduced.",

            PlatformHealth.RECOVERING:
                "Platform is recovering from previous issues.",

            PlatformHealth.UNAVAILABLE:
                "Platform is currently unavailable.",

            PlatformHealth.UNKNOWN:
                "Platform health has not yet been evaluated."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Healthy
#
# does not mean
#
# perfect.
#
# Healthy means
#
# the platform
#
# is operating
#
# within acceptable limits.
#
# Great engineers
#
# define
#
# what acceptable means.
#
# =============================================================================


# =============================================================================
# Platform Trust Level
# =============================================================================


class PlatformTrustLevel(Gen2XEnum):
    """
    Describes the confidence placed in a platform component, service,
    process, or result.

    PlatformTrustLevel answers one question:

        "How much confidence should we place in this?"

    Trust is earned through evidence.

    Trust should never be assigned simply because a system produced an
    answer.

    Confidence grows as observations are tested, validated, and verified.

    This enumeration intentionally models trust as a continuum rather
    than a binary decision.
    """

    # -------------------------------------------------------------------------
    # Unknown
    # -------------------------------------------------------------------------

    UNKNOWN = "UNKNOWN"

    # -------------------------------------------------------------------------
    # Low Confidence
    # -------------------------------------------------------------------------

    UNTRUSTED = "UNTRUSTED"

    EXPERIMENTAL = "EXPERIMENTAL"

    OBSERVED = "OBSERVED"

    # -------------------------------------------------------------------------
    # High Confidence
    # -------------------------------------------------------------------------

    VALIDATED = "VALIDATED"

    VERIFIED = "VERIFIED"

    AUTHORITATIVE = "AUTHORITATIVE"

    def describe(self) -> str:
        """
        Return a human-readable explanation of the trust level.
        """

        descriptions = {

            PlatformTrustLevel.UNKNOWN:
                "Insufficient information exists to determine trust.",

            PlatformTrustLevel.UNTRUSTED:
                "Evidence indicates confidence should not yet be assigned.",

            PlatformTrustLevel.EXPERIMENTAL:
                "Early testing shows potential but requires additional validation.",

            PlatformTrustLevel.OBSERVED:
                "Behavior has been observed but not independently validated.",

            PlatformTrustLevel.VALIDATED:
                "Behavior has passed defined validation procedures.",

            PlatformTrustLevel.VERIFIED:
                "Independent verification confirms expected behavior.",

            PlatformTrustLevel.AUTHORITATIVE:
                "Highest level of confidence based upon extensive evidence and organizational acceptance."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# One of the biggest mistakes
# engineers make
#
# is confusing
#
# confidence
#
# with certainty.
#
# They are not
# the same thing.
#
# We observe.
#
# We test.
#
# We validate.
#
# We verify.
#
# Confidence grows
#
# as evidence grows.
#
# Never trust a system
#
# simply because
#
# it answered quickly.
#
# Ask yourself:
#
#     Why do I believe this?
#
# That's the beginning
#
# of security engineering.
#
#                               — Chewbacca
#                                 Chief Wookiee Architect
#
# =============================================================================


# =============================================================================
#
# Architect's Reflection
#
# Throughout the Gen2X framework,
# every enumeration answers
# a single architectural question.
#
# Indicators describe observations.
#
# Providers describe evidence.
#
# Threats describe reasoning.
#
# Reports describe communication.
#
# Responses describe decisions.
#
# Cache describes organizational memory.
#
# Platform describes the software system
# that brings everything together.
#
# Notice that none of these modules
# execute business logic.
#
# They provide a shared language.
#
# Great engineering teams don't just
# share source code.
#
# They share vocabulary.
#
# Shared language leads to shared
# understanding.
#
# Shared understanding leads to
# better architecture.
#
# Before software becomes code...
#
# it first becomes language.
#
# That is why this package exists.
#
#                               — Chewbacca
#                                 Chief Wookiee Architect
#
# =============================================================================


# =============================================================================
# Public Module Interface
# =============================================================================

__all__ = [

    # -------------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------------

    "PlatformType",

    "PlatformRole",

    "PlatformResponsibility",

    "PlatformComponent",

    # -------------------------------------------------------------------------
    # Behavior
    # -------------------------------------------------------------------------

    "PlatformService",

    "PlatformCapability",

    "PlatformEnvironment",

    "PlatformDeployment",

    "PlatformLifecycle",

    # -------------------------------------------------------------------------
    # Operations
    # -------------------------------------------------------------------------

    "PlatformState",

    "PlatformHealth",

    "PlatformTrustLevel",

]
