"""
===============================================================================

Gen2X Security Engineering Platform

Module:
    threat_enums.py

===============================================================================

Overview
-------------------------------------------------------------------------------

This module defines the vocabulary used by the Gen2X Threat Analysis
Framework.

Threat analysis begins after indicators have been collected and enriched.

The previous modules answer different architectural questions:

    Indicators
        "What did we observe?"

    Providers
        "What evidence did we collect?"

Threat analysis answers:

    "What does the evidence mean?"

Rather than assigning a single risk score, this module intentionally
separates multiple dimensions of threat analysis.

Examples include:

    • Threat Type
    • Threat Domain
    • Threat Condition
    • Threat Severity
    • Threat Confidence
    • Threat Assessment
    • Investigation Status
    • Threat Disposition

Professional security investigations rarely depend upon one value.

Instead, experienced analysts evaluate several independent dimensions
before reaching a conclusion.

-------------------------------------------------------------------------------

Architectural Philosophy

Observation

        ↓

Evidence

        ↓

Reasoning

        ↓

Decision

Threat Analysis represents the reasoning layer of Gen2X.

It transforms technical observations into security understanding.

-------------------------------------------------------------------------------

Design Philosophy

This module intentionally separates:

    What exists

from

    What it means

An exposed endpoint is not automatically an attack.

An unused account is not automatically compromised.

A deprecated library is not automatically exploitable.

These are security conditions.

Evidence determines whether those conditions represent real threats.

Good security engineering avoids confusing possibility with certainty.

===============================================================================

Chewbacca's Commentary 🐾

An exposed endpoint
isn't automatically
an attack.

An unused account
isn't automatically
compromised.

A deprecated library
isn't automatically
exploitable.

They are conditions.

Conditions create opportunities.

Evidence determines whether
those opportunities
became threats.

Never confuse

    exposure

with

    exploitation.

That difference separates
security tools

from

security engineers.

                               — Chewbacca
                                 Chief Wookiee Architect

===============================================================================
"""

from __future__ import annotations

from .base_enum import Gen2XEnum


# =============================================================================
# Threat Type
# =============================================================================


class ThreatType(Gen2XEnum):
    """
    Describes the broad type of threat being investigated.

    ThreatType answers one question:

        "What kind of security problem exists?"

    ThreatType represents broad classes of threats.

    It does not describe:

        • Where the threat exists

        • How severe the threat is

        • How confident we are

        • Which condition produced the threat

    Those concepts intentionally remain independent.
    """

    # -------------------------------------------------------------------------
    # Malware
    # -------------------------------------------------------------------------

    MALWARE = "MALWARE"

    RANSOMWARE = "RANSOMWARE"

    BOTNET = "BOTNET"

    # -------------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------------

    CREDENTIAL_ABUSE = "CREDENTIAL_ABUSE"

    IDENTITY_EXPOSURE = "IDENTITY_EXPOSURE"

    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"

    # -------------------------------------------------------------------------
    # Network
    # -------------------------------------------------------------------------

    RECONNAISSANCE = "RECONNAISSANCE"

    BRUTE_FORCE = "BRUTE_FORCE"

    DENIAL_OF_SERVICE = "DENIAL_OF_SERVICE"

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------

    PHISHING = "PHISHING"

    COMMAND_INJECTION = "COMMAND_INJECTION"

    SQL_INJECTION = "SQL_INJECTION"

    DATA_EXFILTRATION = "DATA_EXFILTRATION"

    LATERAL_MOVEMENT = "LATERAL_MOVEMENT"

    # -------------------------------------------------------------------------
    # Platform
    # -------------------------------------------------------------------------

    MISCONFIGURATION = "MISCONFIGURATION"

    VULNERABILITY_EXPOSURE = "VULNERABILITY_EXPOSURE"

    SUPPLY_CHAIN = "SUPPLY_CHAIN"

    INSIDER_THREAT = "INSIDER_THREAT"

    # -------------------------------------------------------------------------
    # General
    # -------------------------------------------------------------------------

    OTHER = "OTHER"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of the threat type.
        """

        descriptions = {

            ThreatType.MALWARE:
                "Malicious software intended to disrupt or compromise systems.",

            ThreatType.RANSOMWARE:
                "Malware designed to deny access until payment is made.",

            ThreatType.BOTNET:
                "Compromised systems operating under centralized control.",

            ThreatType.CREDENTIAL_ABUSE:
                "Misuse of valid authentication credentials.",

            ThreatType.IDENTITY_EXPOSURE:
                "Exposure of identities, credentials, or authentication artifacts.",

            ThreatType.PRIVILEGE_ESCALATION:
                "Unauthorized elevation of privileges.",

            ThreatType.RECONNAISSANCE:
                "Activity intended to gather information about a target.",

            ThreatType.BRUTE_FORCE:
                "Repeated authentication attempts intended to gain access.",

            ThreatType.DENIAL_OF_SERVICE:
                "Attempts to reduce or eliminate system availability.",

            ThreatType.PHISHING:
                "Social engineering designed to steal information or credentials.",

            ThreatType.COMMAND_INJECTION:
                "Injection of malicious operating system commands.",

            ThreatType.SQL_INJECTION:
                "Injection of malicious SQL statements.",

            ThreatType.DATA_EXFILTRATION:
                "Unauthorized removal of sensitive information.",

            ThreatType.LATERAL_MOVEMENT:
                "Movement between systems after initial compromise.",

            ThreatType.MISCONFIGURATION:
                "Security weaknesses introduced through improper configuration.",

            ThreatType.VULNERABILITY_EXPOSURE:
                "Exposure created by software vulnerabilities or insecure dependencies.",

            ThreatType.SUPPLY_CHAIN:
                "Threats originating from trusted third-party software or services.",

            ThreatType.INSIDER_THREAT:
                "Threat originating from an internal user or trusted entity.",

            ThreatType.OTHER:
                "Application-defined threat type.",

            ThreatType.UNKNOWN:
                "Threat type has not yet been classified."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# ThreatType answers:
#
#     "What kind of danger
#      are we looking at?"
#
# It doesn't explain
# why it exists.
#
# It doesn't explain
# how serious it is.
#
# It simply gives
# the investigation
# a common language.
#
# Naming things
# is one of the first jobs
# of an engineer.
#
# Understanding them
# comes next.
#
# =============================================================================


# =============================================================================
# Threat Domain
# =============================================================================


class ThreatDomain(Gen2XEnum):
    """
    Describes where the threat exists within the environment.

    ThreatDomain answers one question:

        "Which security domain is affected?"

    A threat may exist in one or more domains.

    Domain describes location.

    It does not describe severity,
    confidence,
    or business impact.
    """

    # -------------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------------

    IDENTITY = "IDENTITY"

    # -------------------------------------------------------------------------
    # Infrastructure
    # -------------------------------------------------------------------------

    NETWORK = "NETWORK"

    ENDPOINT = "ENDPOINT"

    CLOUD = "CLOUD"

    SERVERLESS = "SERVERLESS"

    CONTAINER = "CONTAINER"

    KUBERNETES = "KUBERNETES"

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------

    APPLICATION = "APPLICATION"

    API = "API"

    DATABASE = "DATABASE"

    STORAGE = "STORAGE"

    # -------------------------------------------------------------------------
    # Communication
    # -------------------------------------------------------------------------

    EMAIL = "EMAIL"

    DNS = "DNS"

    # -------------------------------------------------------------------------
    # Platform
    # -------------------------------------------------------------------------

    SUPPLY_CHAIN = "SUPPLY_CHAIN"

    OTHER = "OTHER"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of the threat domain.
        """

        descriptions = {

            ThreatDomain.IDENTITY:
                "Identity and authentication systems.",

            ThreatDomain.NETWORK:
                "Networking infrastructure.",

            ThreatDomain.ENDPOINT:
                "User devices and compute resources.",

            ThreatDomain.CLOUD:
                "Cloud infrastructure and services.",

            ThreatDomain.SERVERLESS:
                "Serverless applications and functions.",

            ThreatDomain.CONTAINER:
                "Containerized workloads.",

            ThreatDomain.KUBERNETES:
                "Kubernetes orchestration environments.",

            ThreatDomain.APPLICATION:
                "Applications and business services.",

            ThreatDomain.API:
                "Application Programming Interfaces.",

            ThreatDomain.DATABASE:
                "Database systems.",

            ThreatDomain.STORAGE:
                "Storage services and repositories.",

            ThreatDomain.EMAIL:
                "Messaging infrastructure.",

            ThreatDomain.DNS:
                "Domain Name System services.",

            ThreatDomain.SUPPLY_CHAIN:
                "Software supply chain dependencies.",

            ThreatDomain.OTHER:
                "Application-defined security domain.",

            ThreatDomain.UNKNOWN:
                "Threat domain has not yet been classified."

        }

        return descriptions[self]



# =============================================================================
#
# Chewbacca's Commentary 🐾
#
# Threat conditions
# are observations.
#
# Not verdicts.
#
# Discovering
#
#     a deprecated library
#
# doesn't automatically mean
#
#     compromise.
#
# Finding
#
#     an exposed endpoint
#
# doesn't automatically mean
#
#     exploitation.
#
# Identifying
#
#     an unused account
#
# doesn't automatically mean
#
#     malicious activity.
#
# Conditions describe
#
# what exists.
#
# Evidence determines
#
# what it means.
#
# Professional security engineers
# resist the temptation
# to confuse
#
#     findings
#
# with
#
#     conclusions.
#
# That's why this enumeration
# exists separately from
#
# Severity,
#
# Confidence,
#
# and
#
# Assessment.
#
#                              — Chewbacca
#                                Chief Wookiee Architect
#
# =============================================================================

# =============================================================================
# Threat Condition
# =============================================================================


class ThreatCondition(Gen2XEnum):
    """
    Describes the specific security condition identified during analysis.

    ThreatCondition answers one question:

        "What insecure condition did we discover?"

    Conditions are observations.

    They are not conclusions.

    A condition may exist without active exploitation.

    Threat analysis determines whether the condition represents
    meaningful operational risk.
    """

    # -------------------------------------------------------------------------
    # Software Conditions
    # -------------------------------------------------------------------------

    DEPRECATED_LIBRARY = "DEPRECATED_LIBRARY"

    VULNERABLE_LIBRARY = "VULNERABLE_LIBRARY"

    UNSUPPORTED_SOFTWARE = "UNSUPPORTED_SOFTWARE"

    OUTDATED_RUNTIME = "OUTDATED_RUNTIME"

    UNPATCHED_VULNERABILITY = "UNPATCHED_VULNERABILITY"

    # -------------------------------------------------------------------------
    # Application Exposure
    # -------------------------------------------------------------------------

    EXPOSED_ENDPOINT = "EXPOSED_ENDPOINT"

    PUBLIC_ENDPOINT = "PUBLIC_ENDPOINT"

    UNAUTHENTICATED_ENDPOINT = "UNAUTHENTICATED_ENDPOINT"

    INTERNET_EXPOSED_RESOURCE = "INTERNET_EXPOSED_RESOURCE"

    OVERLY_PERMISSIVE_NETWORK_ACCESS = "OVERLY_PERMISSIVE_NETWORK_ACCESS"

    # -------------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------------

    UNUSED_ACCOUNT = "UNUSED_ACCOUNT"

    DORMANT_ACCOUNT = "DORMANT_ACCOUNT"

    UNUSED_ACCESS_KEY = "UNUSED_ACCESS_KEY"

    STALE_CREDENTIAL = "STALE_CREDENTIAL"

    UNUSED_TOKEN = "UNUSED_TOKEN"

    LONG_LIVED_TOKEN = "LONG_LIVED_TOKEN"

    TOKEN_REUSE = "TOKEN_REUSE"

    TOKEN_EXPOSURE = "TOKEN_EXPOSURE"

    EXCESSIVE_PERMISSIONS = "EXCESSIVE_PERMISSIONS"

    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------

    PUBLIC_STORAGE = "PUBLIC_STORAGE"

    MISSING_ENCRYPTION = "MISSING_ENCRYPTION"

    LOGGING_DISABLED = "LOGGING_DISABLED"

    MONITORING_DISABLED = "MONITORING_DISABLED"

    MISCONFIGURED_CONTROL = "MISCONFIGURED_CONTROL"

    # -------------------------------------------------------------------------
    # General
    # -------------------------------------------------------------------------

    OTHER = "OTHER"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of the identified
        security condition.

        Threat conditions describe observations made during
        investigation.

        They intentionally avoid making conclusions regarding
        severity, confidence, or operational impact.
        """

        descriptions = {

            # -----------------------------------------------------------------
            # Software
            # -----------------------------------------------------------------

            ThreatCondition.DEPRECATED_LIBRARY:
                "A software dependency is deprecated and should be upgraded.",

            ThreatCondition.VULNERABLE_LIBRARY:
                "A dependency contains one or more known vulnerabilities.",

            ThreatCondition.UNSUPPORTED_SOFTWARE:
                "Software is no longer supported by its vendor.",

            ThreatCondition.OUTDATED_RUNTIME:
                "Runtime version is outdated and should be updated.",

            ThreatCondition.UNPATCHED_VULNERABILITY:
                "Known security patches have not yet been applied.",

            # -----------------------------------------------------------------
            # Application Exposure
            # -----------------------------------------------------------------

            ThreatCondition.EXPOSED_ENDPOINT:
                "An endpoint is exposed to unintended access.",

            ThreatCondition.PUBLIC_ENDPOINT:
                "A service endpoint is publicly accessible.",

            ThreatCondition.UNAUTHENTICATED_ENDPOINT:
                "An endpoint permits access without authentication.",

            ThreatCondition.INTERNET_EXPOSED_RESOURCE:
                "A resource is directly accessible from the public Internet.",

            ThreatCondition.OVERLY_PERMISSIVE_NETWORK_ACCESS:
                "Network permissions exceed operational requirements.",

            # -----------------------------------------------------------------
            # Identity
            # -----------------------------------------------------------------

            ThreatCondition.UNUSED_ACCOUNT:
                "An account exists but shows little or no recent activity.",

            ThreatCondition.DORMANT_ACCOUNT:
                "An inactive account remains enabled.",

            ThreatCondition.UNUSED_ACCESS_KEY:
                "An access key has not been used within the expected period.",

            ThreatCondition.STALE_CREDENTIAL:
                "Credentials have exceeded the recommended rotation period.",

            ThreatCondition.UNUSED_TOKEN:
                "An authentication token exists but appears unused.",

            ThreatCondition.LONG_LIVED_TOKEN:
                "A token has remained valid longer than recommended.",

            ThreatCondition.TOKEN_REUSE:
                "Authentication token appears to have been reused.",

            ThreatCondition.TOKEN_EXPOSURE:
                "Authentication token may have been exposed.",

            ThreatCondition.EXCESSIVE_PERMISSIONS:
                "Permissions exceed the principle of least privilege.",

            # -----------------------------------------------------------------
            # Configuration
            # -----------------------------------------------------------------

            ThreatCondition.PUBLIC_STORAGE:
                "Storage resource is publicly accessible.",

            ThreatCondition.MISSING_ENCRYPTION:
                "Encryption is missing or improperly configured.",

            ThreatCondition.LOGGING_DISABLED:
                "Logging required for monitoring has been disabled.",

            ThreatCondition.MONITORING_DISABLED:
                "Security monitoring is not currently active.",

            ThreatCondition.MISCONFIGURED_CONTROL:
                "Security control configuration is incorrect.",

            # -----------------------------------------------------------------
            # General
            # -----------------------------------------------------------------

            ThreatCondition.OTHER:
                "Application-defined security condition.",

            ThreatCondition.UNKNOWN:
                "Security condition has not yet been classified."

        }

        return descriptions[self]


# =============================================================================
# Threat Severity
# =============================================================================


class ThreatSeverity(Gen2XEnum):
    """
    Describes the potential technical impact of a threat.

    ThreatSeverity answers one question:

        "If this threat is real, how serious could the impact become?"

    Severity estimates technical impact.

    It does not describe:

        • Confidence
        • Investigation status
        • Business priority
        • Recommended response

    Those concepts are represented separately.

    Separating severity from confidence prevents engineers from
    unintentionally overstating conclusions.
    """

    # -------------------------------------------------------------------------
    # Informational
    # -------------------------------------------------------------------------

    INFORMATIONAL = "INFORMATIONAL"

    # -------------------------------------------------------------------------
    # Low Risk
    # -------------------------------------------------------------------------

    LOW = "LOW"

    # -------------------------------------------------------------------------
    # Moderate Risk
    # -------------------------------------------------------------------------

    MEDIUM = "MEDIUM"

    # -------------------------------------------------------------------------
    # Significant Risk
    # -------------------------------------------------------------------------

    HIGH = "HIGH"

    # -------------------------------------------------------------------------
    # Critical Risk
    # -------------------------------------------------------------------------

    CRITICAL = "CRITICAL"

    # -------------------------------------------------------------------------
    # Unknown
    # -------------------------------------------------------------------------

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of threat severity.
        """

        descriptions = {

            ThreatSeverity.INFORMATIONAL:
                "No immediate security impact. Recorded for visibility.",

            ThreatSeverity.LOW:
                "Limited technical impact under normal conditions.",

            ThreatSeverity.MEDIUM:
                "Moderate technical impact requiring investigation.",

            ThreatSeverity.HIGH:
                "Significant impact capable of affecting business operations.",

            ThreatSeverity.CRITICAL:
                "Severe impact requiring immediate attention.",

            ThreatSeverity.UNKNOWN:
                "Threat severity has not yet been determined."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Severity answers:
#
#     "How bad could this become?"
#
# Not:
#
#     "How sure are we?"
#
# Those are
# completely different questions.
#
# A deprecated library
#
# containing a remote code execution
# vulnerability
#
# may be
#
# CRITICAL
#
# even before
#
# exploitation has been confirmed.
#
# =============================================================================


# =============================================================================
# Threat Confidence
# =============================================================================


class ThreatConfidence(Gen2XEnum):
    """
    Describes how strongly the available evidence supports the current
    threat analysis.

    ThreatConfidence answers one question:

        "How confident are we that this interpretation is correct?"

    Confidence grows as evidence accumulates.

    Confidence should never be confused with severity.

    A threat may be technically severe while confidence remains low.
    """

    # -------------------------------------------------------------------------
    # Unknown
    # -------------------------------------------------------------------------

    UNKNOWN = "UNKNOWN"

    # -------------------------------------------------------------------------
    # Early Investigation
    # -------------------------------------------------------------------------

    OBSERVED = "OBSERVED"

    SUSPECTED = "SUSPECTED"

    # -------------------------------------------------------------------------
    # Supporting Evidence
    # -------------------------------------------------------------------------

    CORRELATED = "CORRELATED"

    VALIDATED = "VALIDATED"

    VERIFIED = "VERIFIED"

    # -------------------------------------------------------------------------
    # Highest Confidence
    # -------------------------------------------------------------------------

    CONFIRMED = "CONFIRMED"

    def describe(self) -> str:
        """
        Return a human-readable explanation of threat confidence.
        """

        descriptions = {

            ThreatConfidence.UNKNOWN:
                "Insufficient evidence exists to determine confidence.",

            ThreatConfidence.OBSERVED:
                "The condition has been directly observed.",

            ThreatConfidence.SUSPECTED:
                "Evidence suggests a threat but alternatives remain possible.",

            ThreatConfidence.CORRELATED:
                "Multiple independent observations support the analysis.",

            ThreatConfidence.VALIDATED:
                "Validation procedures support the conclusion.",

            ThreatConfidence.VERIFIED:
                "Independent verification confirms the finding.",

            ThreatConfidence.CONFIRMED:
                "The investigation has conclusively established the threat."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Confidence grows.
#
# It isn't assigned.
#
# We observe.
#
# We correlate.
#
# We validate.
#
# We verify.
#
# We confirm.
#
# That's how
# professional investigations
# become trustworthy.
#
# =============================================================================


# =============================================================================
# Threat Assessment
# =============================================================================


class ThreatAssessment(Gen2XEnum):
    """
    Describes the analytical conclusion supported by current evidence.

    ThreatAssessment answers one question:

        "Given everything we know today, what conclusion is justified?"

    Assessment bridges threat analysis and response planning.

    It recommends direction.

    It does not execute actions.

    Response Agents remain responsible for operational decisions.
    """

    # -------------------------------------------------------------------------
    # Minimal Risk
    # -------------------------------------------------------------------------

    NO_IMMEDIATE_RISK = "NO_IMMEDIATE_RISK"

    OBSERVE = "OBSERVE"

    MONITOR = "MONITOR"

    # -------------------------------------------------------------------------
    # Investigation
    # -------------------------------------------------------------------------

    INVESTIGATE = "INVESTIGATE"

    ESCALATE = "ESCALATE"

    # -------------------------------------------------------------------------
    # Recommendations
    # -------------------------------------------------------------------------

    CONTAINMENT_RECOMMENDED = "CONTAINMENT_RECOMMENDED"

    REMEDIATION_RECOMMENDED = "REMEDIATION_RECOMMENDED"

    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"

    # -------------------------------------------------------------------------
    # Unknown
    # -------------------------------------------------------------------------

    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of the assessment.
        """

        descriptions = {

            ThreatAssessment.NO_IMMEDIATE_RISK:
                "Current evidence does not justify operational action.",

            ThreatAssessment.OBSERVE:
                "Continue collecting evidence.",

            ThreatAssessment.MONITOR:
                "Monitor the condition for changes.",

            ThreatAssessment.INVESTIGATE:
                "Additional investigation is recommended.",

            ThreatAssessment.ESCALATE:
                "Escalate to experienced analysts.",

            ThreatAssessment.CONTAINMENT_RECOMMENDED:
                "Evidence supports containment planning.",

            ThreatAssessment.REMEDIATION_RECOMMENDED:
                "Evidence supports corrective action.",

            ThreatAssessment.RECOVERY_REQUIRED:
                "Recovery activities are recommended.",

            ThreatAssessment.INSUFFICIENT_EVIDENCE:
                "Current evidence is insufficient for meaningful conclusions.",

            ThreatAssessment.UNKNOWN:
                "Threat assessment has not yet been determined."

        }

        return descriptions[self]

# =============================================================================
# Threat Status
# =============================================================================


class ThreatStatus(Gen2XEnum):
    """
    Describes the current operational stage of a threat investigation.

    ThreatStatus answers one question:

        "Where is this investigation right now?"

    Status represents workflow progression.

    It does not indicate:

        • Severity
        • Confidence
        • Final disposition

    Investigations naturally move through multiple states before
    reaching a conclusion.
    """

    # -------------------------------------------------------------------------
    # Investigation Lifecycle
    # -------------------------------------------------------------------------

    NEW = "NEW"

    ENRICHING = "ENRICHING"

    CORRELATING = "CORRELATING"

    ANALYZING = "ANALYZING"

    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"

    AWAITING_REVIEW = "AWAITING_REVIEW"

    ESCALATED = "ESCALATED"

    RESPONSE_PLANNED = "RESPONSE_PLANNED"

    CONTAINED = "CONTAINED"

    REMEDIATED = "REMEDIATED"

    CLOSED = "CLOSED"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of the investigation status.
        """

        descriptions = {

            ThreatStatus.NEW:
                "Threat has been identified but not yet analyzed.",

            ThreatStatus.ENRICHING:
                "Additional evidence is being collected.",

            ThreatStatus.CORRELATING:
                "Evidence is being correlated across providers.",

            ThreatStatus.ANALYZING:
                "Threat analysis is currently underway.",

            ThreatStatus.UNDER_INVESTIGATION:
                "Analysts are actively investigating the threat.",

            ThreatStatus.AWAITING_REVIEW:
                "Awaiting analyst or management review.",

            ThreatStatus.ESCALATED:
                "Escalated to senior analysts or incident response.",

            ThreatStatus.RESPONSE_PLANNED:
                "Response planning has begun.",

            ThreatStatus.CONTAINED:
                "Threat has been operationally contained.",

            ThreatStatus.REMEDIATED:
                "Corrective actions have been completed.",

            ThreatStatus.CLOSED:
                "Investigation has been completed.",

            ThreatStatus.UNKNOWN:
                "Investigation status has not yet been determined."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Investigations
# are journeys.
#
# Every finding
# begins somewhere.
#
# Good engineers
# document
# where they are
# before deciding
# where to go next.
#
# Status changes.
#
# Facts should not.
#
# =============================================================================


# =============================================================================
# Threat Disposition
# =============================================================================


class ThreatDisposition(Gen2XEnum):
    """
    Describes the analytical conclusion reached after investigation.

    ThreatDisposition answers one question:

        "What conclusion did the investigation reach?"

    Disposition represents the outcome of analysis.

    It should only be assigned after sufficient evidence has been
    collected and reviewed.
    """

    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"

    TRUE_POSITIVE = "TRUE_POSITIVE"

    FALSE_POSITIVE = "FALSE_POSITIVE"

    BENIGN = "BENIGN"

    EXPECTED_ACTIVITY = "EXPECTED_ACTIVITY"

    POLICY_VIOLATION = "POLICY_VIOLATION"

    ACCEPTED_RISK = "ACCEPTED_RISK"

    DUPLICATE = "DUPLICATE"

    INCONCLUSIVE = "INCONCLUSIVE"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of the threat disposition.
        """

        descriptions = {

            ThreatDisposition.UNDER_INVESTIGATION:
                "Investigation remains in progress.",

            ThreatDisposition.TRUE_POSITIVE:
                "Threat confirmed through investigation.",

            ThreatDisposition.FALSE_POSITIVE:
                "Investigation determined the finding was incorrect.",

            ThreatDisposition.BENIGN:
                "Activity determined to be harmless.",

            ThreatDisposition.EXPECTED_ACTIVITY:
                "Behavior is expected within normal operations.",

            ThreatDisposition.POLICY_VIOLATION:
                "Finding violates organizational policy.",

            ThreatDisposition.ACCEPTED_RISK:
                "Risk acknowledged and accepted by the organization.",

            ThreatDisposition.DUPLICATE:
                "Finding duplicates an existing investigation.",

            ThreatDisposition.INCONCLUSIVE:
                "Evidence was insufficient to reach a final conclusion.",

            ThreatDisposition.UNKNOWN:
                "Disposition has not yet been determined."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Every investigation
# deserves
# a conclusion.
#
# Sometimes the answer is:
#
#     True Positive.
#
# Sometimes:
#
#     False Positive.
#
# Sometimes:
#
#     Accepted Risk.
#
# Security engineering
# isn't about pretending
# every problem
# disappears.
#
# It's about documenting
# informed decisions.
#
# =============================================================================


# =============================================================================
# Threat Actor Type
# =============================================================================


class ThreatActorType(Gen2XEnum):
    """
    Describes the general class of actor associated with the threat.

    Attribution should only be assigned when supported by evidence.

    Unknown remains a perfectly acceptable answer.
    """

    CYBERCRIMINAL = "CYBERCRIMINAL"

    INSIDER = "INSIDER"

    NATION_STATE = "NATION_STATE"

    HACKTIVIST = "HACKTIVIST"

    COMPETITOR = "COMPETITOR"

    AUTOMATED_BOT = "AUTOMATED_BOT"

    SCRIPT_KIDDIE = "SCRIPT_KIDDIE"

    OTHER = "OTHER"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of the threat actor.
        """

        descriptions = {

            ThreatActorType.CYBERCRIMINAL:
                "Financially motivated criminal activity.",

            ThreatActorType.INSIDER:
                "Threat originates from an internal individual.",

            ThreatActorType.NATION_STATE:
                "Threat associated with a nation-state.",

            ThreatActorType.HACKTIVIST:
                "Ideologically motivated actor.",

            ThreatActorType.COMPETITOR:
                "Commercially motivated actor.",

            ThreatActorType.AUTOMATED_BOT:
                "Automated malicious system or bot.",

            ThreatActorType.SCRIPT_KIDDIE:
                "Low-skill actor using publicly available tools.",

            ThreatActorType.OTHER:
                "Application-defined actor classification.",

            ThreatActorType.UNKNOWN:
                "Actor has not been identified."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Attribution
# is difficult.
#
# Sometimes impossible.
#
# Great analysts
# are comfortable saying:
#
#     "We don't know."
#
# Guessing
# is not evidence.
#
# =============================================================================


# =============================================================================
# Threat Activity Pattern
# =============================================================================


class ThreatActivityPattern(Gen2XEnum):
    """
    Describes the observable pattern of threat activity.

    ThreatActivityPattern answers one question:

        "Does this appear isolated or coordinated?"

    Patterns often emerge only after evidence from multiple providers
    has been correlated.
    """

    SINGLE_EVENT = "SINGLE_EVENT"

    RECURRING = "RECURRING"

    DISTRIBUTED = "DISTRIBUTED"

    COORDINATED = "COORDINATED"

    CAMPAIGN = "CAMPAIGN"

    PERSISTENT = "PERSISTENT"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of the activity pattern.
        """

        descriptions = {

            ThreatActivityPattern.SINGLE_EVENT:
                "Appears to be an isolated occurrence.",

            ThreatActivityPattern.RECURRING:
                "Repeated activity has been observed.",

            ThreatActivityPattern.DISTRIBUTED:
                "Activity originates from multiple independent sources.",

            ThreatActivityPattern.COORDINATED:
                "Evidence suggests coordinated activity.",

            ThreatActivityPattern.CAMPAIGN:
                "Part of a broader organized campaign.",

            ThreatActivityPattern.PERSISTENT:
                "Long-term activity observed over an extended period.",

            ThreatActivityPattern.UNKNOWN:
                "Activity pattern has not yet been determined."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# One failed login
# isn't a campaign.
#
# One exposed endpoint
# isn't coordinated activity.
#
# Patterns emerge
# only after
# multiple observations
# are connected.
#
# Correlation
# turns isolated events
# into intelligence.
#
# =============================================================================


# =============================================================================
# Investigation Status
# =============================================================================


class InvestigationStatus(Gen2XEnum):
    """
    Describes the operational lifecycle of a security investigation.

    InvestigationStatus answers one question:

        "Where are we in the investigation?"

    Unlike ThreatStatus, which describes the analytical workflow of one
    threat, InvestigationStatus describes the operational case that a
    human team manages.

    Investigations are not perfectly linear.

    New evidence may cause an investigation to move backward, reopen,
    or continue after remediation.
    """

    # -------------------------------------------------------------------------
    # Active Work
    # -------------------------------------------------------------------------

    NEW = "NEW"

    EVIDENCE_COLLECTION = "EVIDENCE_COLLECTION"

    ANALYSIS = "ANALYSIS"

    INVESTIGATING = "INVESTIGATING"

    MONITORING = "MONITORING"

    # -------------------------------------------------------------------------
    # Conclusion
    # -------------------------------------------------------------------------

    RESOLVED = "RESOLVED"

    CLOSED = "CLOSED"

    REOPENED = "REOPENED"

    # -------------------------------------------------------------------------
    # General
    # -------------------------------------------------------------------------

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable explanation of the investigation status.
        """

        descriptions = {

            InvestigationStatus.NEW:
                "The investigation has been opened but work has not begun.",

            InvestigationStatus.EVIDENCE_COLLECTION:
                "Evidence is being collected from providers.",

            InvestigationStatus.ANALYSIS:
                "Collected evidence is being analyzed.",

            InvestigationStatus.INVESTIGATING:
                "Analysts are actively investigating.",

            InvestigationStatus.MONITORING:
                "The investigation remains open for observation.",

            InvestigationStatus.RESOLVED:
                "The underlying issue has been addressed.",

            InvestigationStatus.CLOSED:
                "The investigation has been administratively closed.",

            InvestigationStatus.REOPENED:
                "New information caused the investigation to reopen.",

            InvestigationStatus.UNKNOWN:
                "Investigation status has not yet been determined."

        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Resolved
#
# is not
#
# closed.
#
# A resolved investigation
# may remain open
#
# for monitoring,
# verification,
# or paperwork.
#
# And a closed investigation
#
# may reopen
#
# the moment
#
# new evidence appears.
#
# Good case management
#
# accepts
#
# that investigations
#
# have second acts.
#
# =============================================================================


# =============================================================================
# Public Module Interface
# =============================================================================

__all__ = [

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

]


# =============================================================================
#
# Architect's Reflection
#
# Threat analysis is not the act of finding problems.
#
# It is the discipline of interpreting evidence.
#
# Throughout this module we intentionally separated concepts that are
# frequently collapsed into a single "risk score."
#
# A threat has:
#
#     • a type,
#     • a domain,
#     • one or more conditions,
#     • a potential severity,
#     • an evidence-based confidence,
#     • an analytical assessment,
#     • an investigation status,
#     • and eventually a disposition.
#
# Each answers a different question.
#
# Together they create an evidence-based understanding that can evolve as
# new information arrives.
#
# This module does not replace the engineer.
#
# It organizes information so the engineer can make better decisions.
#
# The platform recommends.
#
# The engineer decides.
#
# The engineer signs the report.
#
#                               — Chewbacca
#                                 Chief Wookiee Architect
#
# =============================================================================
