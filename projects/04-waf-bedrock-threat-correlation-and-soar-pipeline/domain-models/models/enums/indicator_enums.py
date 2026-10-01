"""
===============================================================================

Gen2X Security Engineering Platform

Module:
    indicator_enums.py

===============================================================================

Overview
-------------------------------------------------------------------------------

This module defines the enumerations used to describe Indicators.

Indicators are observable objects discovered during security operations.

Examples include:

    • IPv4 Addresses
    • Domain Names
    • URLs
    • File Hashes
    • IAM Roles
    • EC2 Instances
    • Kubernetes Pods

An Indicator is NOT automatically malicious.

Indicators represent observations.

Later agents determine whether those observations represent threats.

-------------------------------------------------------------------------------

Architectural Philosophy

Gen2X intentionally separates:

    Observation

        from

    Analysis

This distinction is one of the most important architectural ideas in
security engineering.

===============================================================================

Chewbacca's Commentary 🐶

New security engineers often make this mistake:

    "An IP address appeared in WAF."

Therefore...

    "It must be malicious."

Not necessarily.

An IP address is simply something we observed.

The investigation begins there.

Threat Intelligence Agents...

Correlation Agents...

Compliance Agents...

Executive Reporting...

all build upon that observation.

Frameworks become much easier to maintain when observations and
conclusions are represented separately.

===============================================================================
"""

from __future__ import annotations

from .base_enum import Gen2XEnum


# =============================================================================
# Indicator Types
# =============================================================================

class IndicatorType(Gen2XEnum):
    """
    Describes the type of observable object.

    IndicatorType answers one question:

        "What did we observe?"

    It does NOT answer:

        "Is it malicious?"

    Examples

        IndicatorType.IPV4

        IndicatorType.DOMAIN

        IndicatorType.IAM_ROLE

        IndicatorType.EC2_INSTANCE
    """

    # =========================================================================
    # Chewbacca's Commentary 🐶
    #
    # Notice how the values are grouped.
    #
    # Large enumerations become much easier to navigate when similar concepts
    # live together.
    #
    # Professional software rarely organizes everything alphabetically.
    #
    # Engineers usually organize things conceptually.
    #
    # =========================================================================

    # -------------------------------------------------------------------------
    # Network Indicators
    # -------------------------------------------------------------------------

    IPV4 = "IPV4"
    IPV6 = "IPV6"

    DOMAIN = "DOMAIN"
    HOSTNAME = "HOSTNAME"

    URL = "URL"
    URI = "URI"

    PORT = "PORT"
    CIDR = "CIDR"

    # -------------------------------------------------------------------------
    # Identity Indicators
    # -------------------------------------------------------------------------

    USER = "USER"
    USERNAME = "USERNAME"
    EMAIL = "EMAIL"

    IAM_USER = "IAM_USER"
    IAM_ROLE = "IAM_ROLE"
    IAM_GROUP = "IAM_GROUP"

    SERVICE_ACCOUNT = "SERVICE_ACCOUNT"

    PRINCIPAL_ARN = "PRINCIPAL_ARN"

    # -------------------------------------------------------------------------
    # AWS Cloud Resources
    # -------------------------------------------------------------------------

    AWS_ACCOUNT = "AWS_ACCOUNT"
    AWS_REGION = "AWS_REGION"

    EC2_INSTANCE = "EC2_INSTANCE"

    S3_BUCKET = "S3_BUCKET"

    LAMBDA_FUNCTION = "LAMBDA_FUNCTION"

    API_GATEWAY = "API_GATEWAY"

    DYNAMODB_TABLE = "DYNAMODB_TABLE"

    VPC = "VPC"
    SUBNET = "SUBNET"

    SECURITY_GROUP = "SECURITY_GROUP"

    NETWORK_ACL = "NETWORK_ACL"

    KMS_KEY = "KMS_KEY"

    SECRET = "SECRET"

    WAF_WEB_ACL = "WAF_WEB_ACL"

    # -------------------------------------------------------------------------
    # Applications
    # -------------------------------------------------------------------------

    APPLICATION = "APPLICATION"

    SERVICE = "SERVICE"

    PROCESS = "PROCESS"

    FILE = "FILE"

    PACKAGE = "PACKAGE"

    LIBRARY = "LIBRARY"

    # -------------------------------------------------------------------------
    # Containers
    # -------------------------------------------------------------------------

    CONTAINER = "CONTAINER"

    CONTAINER_IMAGE = "CONTAINER_IMAGE"

    # -------------------------------------------------------------------------
    # Kubernetes
    # -------------------------------------------------------------------------

    KUBERNETES_CLUSTER = "KUBERNETES_CLUSTER"

    KUBERNETES_NAMESPACE = "KUBERNETES_NAMESPACE"

    KUBERNETES_NODE = "KUBERNETES_NODE"

    KUBERNETES_POD = "KUBERNETES_POD"

    KUBERNETES_SERVICE = "KUBERNETES_SERVICE"

    KUBERNETES_INGRESS = "KUBERNETES_INGRESS"

    # -------------------------------------------------------------------------
    # Vulnerabilities
    # -------------------------------------------------------------------------

    CVE = "CVE"

    CWE = "CWE"

    CVSS_VECTOR = "CVSS_VECTOR"

    # -------------------------------------------------------------------------
    # Hashes
    # -------------------------------------------------------------------------

    MD5 = "MD5"

    SHA1 = "SHA1"

    SHA256 = "SHA256"

    SHA512 = "SHA512"

    # -------------------------------------------------------------------------
    # Credentials
    # -------------------------------------------------------------------------

    API_KEY = "API_KEY"

    ACCESS_KEY_ID = "ACCESS_KEY_ID"

    TOKEN_ID = "TOKEN_ID"

    CERTIFICATE = "CERTIFICATE"

    SSH_KEY_FINGERPRINT = "SSH_KEY_FINGERPRINT"

    # -------------------------------------------------------------------------
    # Generic
    # -------------------------------------------------------------------------

    RESOURCE_ID = "RESOURCE_ID"

    RESOURCE_ARN = "RESOURCE_ARN"

    OTHER = "OTHER"

    UNKNOWN = "UNKNOWN"

    # =========================================================================
    # Chewbacca's Commentary 🐶
    #
    # Why is UNKNOWN here?
    #
    # Good engineers don't invent certainty.
    #
    # If the platform cannot confidently classify an observation,
    # UNKNOWN is an honest answer.
    #
    # Honest uncertainty is always better than incorrect confidence.
    #
    # =========================================================================


# =============================================================================
# Indicator Source
# =============================================================================

class IndicatorSource(Gen2XEnum):
    """
    Describes where an indicator originated.

    Source answers:

        "Where did we observe this?"

    Source does NOT answer:

        "Who enriched this?"

    Those are two different concepts.
    """

    # =========================================================================
    # Chewbacca's Commentary 🐶
    #
    # Example
    #
    # AWS WAF detects:
    #
    #     203.0.113.42
    #
    # Later...
    #
    # AbuseIPDB enriches the IP.
    #
    # Source:
    #
    #     AWS_WAF
    #
    # Provider:
    #
    #     AbuseIPDB
    #
    # Don't confuse observations with enrichment.
    #
    # =========================================================================

    AWS_WAF = "AWS_WAF"

    CLOUDTRAIL = "CLOUDTRAIL"

    CLOUDWATCH_LOGS = "CLOUDWATCH_LOGS"

    VPC_FLOW_LOGS = "VPC_FLOW_LOGS"

    GUARDDUTY = "GUARDDUTY"

    SECURITY_HUB = "SECURITY_HUB"

    AWS_CONFIG = "AWS_CONFIG"

    ACCESS_ANALYZER = "ACCESS_ANALYZER"

    INSPECTOR = "INSPECTOR"

    MACIE = "MACIE"

    APPLICATION_LOG = "APPLICATION_LOG"

    API_REQUEST = "API_REQUEST"

    USER_INPUT = "USER_INPUT"

    MANUAL_ENTRY = "MANUAL_ENTRY"

    THREAT_HUNT = "THREAT_HUNT"

    DYNAMODB = "DYNAMODB"

    S3 = "S3"

    EVENTBRIDGE = "EVENTBRIDGE"

    SNS = "SNS"

    SQS = "SQS"

    KINESIS = "KINESIS"

    EXTERNAL_API = "EXTERNAL_API"

    SIEM = "SIEM"

    SOAR = "SOAR"

    EDR = "EDR"

    UNKNOWN = "UNKNOWN"


# =============================================================================
# Indicator Confidence
# =============================================================================

class IndicatorConfidence(Gen2XEnum):
    """
    Describes confidence in the observation itself.

    Confidence answers:

        "How certain are we that this observation is correct?"

    It does NOT describe:

        • Risk

        • Severity

        • Priority

        • Business Impact
    """

    # =========================================================================
    # Chewbacca's Commentary 🐶
    #
    # Confidence and Risk are two different dimensions.
    #
    # Example:
    #
    # VERIFIED confidence
    #
    # that an EC2 instance exists.
    #
    # Risk?
    #
    # Unknown.
    #
    # The EC2 instance may be perfectly healthy.
    #
    # Confidence measures certainty.
    #
    # Risk measures impact.
    #
    # Keeping these concepts separate dramatically improves the quality of
    # security analysis.
    #
    # =========================================================================

    UNKNOWN = "UNKNOWN"

    LOW = "LOW"

    MEDIUM = "MEDIUM"

    HIGH = "HIGH"

    VERIFIED = "VERIFIED"


# =============================================================================
# Public Interface
# =============================================================================

__all__ = [

    "IndicatorType",

    "IndicatorSource",

    "IndicatorConfidence",
]
