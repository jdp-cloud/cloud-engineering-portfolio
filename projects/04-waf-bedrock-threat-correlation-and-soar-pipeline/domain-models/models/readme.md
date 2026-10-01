# Domain Models

## Overview

The `models` package contains the shared domain models used throughout the Gen2X Security Engineering Platform.

These models define the common language used by every component of the platform.

Rather than passing anonymous Python dictionaries between services, Gen2X uses strongly typed domain models that describe security concepts such as indicators, threat evidence, provider results, reports, and recommendations.

This approach provides:

- Consistent data structures
- Easier testing
- Better IDE support
- Improved readability
- Safer refactoring
- Clear separation of responsibilities

The `models` package intentionally contains **data**, not business logic.

---

# Design Philosophy

This follows a layered architecture.

```mermaid
flowchart TD
    N0["Providers"] --> N1
    N1["ProviderResult"] --> N2
    N2["ThreatEvidence"] --> N3
    N3["ThreatSummary"] --> N4
    N4["Threat Intelligence Report"] --> N5
    N5["API Response"]
```

Each stage produces a different model.

Those models are defined here.

This package represents the **shared vocabulary** of the entire platform.

---

# Why Models?

Imagine an investigation that begins with an IP address.

Instead of passing dictionaries throughout the application...

```python
{
    "ip": "203.0.113.42",
    "score": 97
}
```

...the platform passes a well-defined object.

```python
ProviderResult(...)
```

This makes code easier to understand and significantly reduces accidental errors.

---

# Package Structure

```text
models/

├── __init__.py
├── base_model.py
├── enums.py
├── indicator.py
├── provider.py
├── evidence.py
├── threat.py
├── report.py
├── response.py
└── exceptions.py
```

Each module represents a different part of the investigation lifecycle.

---

# Module Overview

## base_model.py

Provides the common functionality shared by every model.

Typical responsibilities include:

- serialization
- deserialization
- validation helpers
- utility methods
- common interfaces

All domain models inherit from the base model whenever appropriate.

---

## enums.py

Contains all shared platform enumerations.

Examples include:

- IndicatorType
- ProviderStatus
- RiskLevel
- PriorityLevel
- ReportStatus

Keeping enumerations centralized ensures consistent terminology across every agent.

---

## indicator.py

Defines security indicators.

Examples include:

- IP Addresses
- Domains
- URLs
- File Hashes
- Email Addresses
- CVEs

These objects represent the starting point for investigations.

---

## provider.py

Defines models produced by intelligence providers.

Examples include:

- ProviderMetadata
- ProviderConfiguration
- ProviderResult

These models describe intelligence collected from sources such as:

- AbuseIPDB
- CISA KEV
- MITRE ATT&CK
- VirusTotal
- Future providers

These models do **not** calculate threat risk.

---

## evidence.py

Represents normalized observations gathered from multiple providers.

Examples include:

- ProviderEvidence
- ThreatEvidence

Evidence is factual.

Evidence does not determine whether something is malicious.

---

## threat.py

Represents the deterministic conclusions produced by policy engines.

Examples include:

- ThreatSummary
- ThreatAssessment
- ThreatClassification

These objects are the output of the Fusion Engine.

---

## report.py

Contains the models used to construct analyst reports.

Examples include:

- ExecutiveSummary
- Finding
- Recommendation
- ThreatIntelligenceReport

These models describe how investigations are presented.

They do not render PDF, HTML, or Markdown documents.

---

## response.py

Defines models returned by APIs and AWS Lambda functions.

Examples include:

- ThreatInvestigationResponse
- ProviderHealthResponse
- InvestigationStatus

Using response models instead of raw dictionaries creates more maintainable APIs.

---

## exceptions.py

Contains exceptions specific to the model layer.

Examples:

- ValidationError
- SerializationError
- ModelConstructionError

Keeping model exceptions localized simplifies troubleshooting.

---

# Relationship to Other Packages

The models package does not perform investigations.

Instead, it provides the shared objects used by every package.

```mermaid
flowchart BT
    Root["models"]
    N0["Providers"] --> Root
    Agents["Agents"] --> N0
    N1["Fusion"] --> Root
    Agents["Agents"] --> N1
    N2["Reporting"] --> Root
    Agents["Agents"] --> N2
```

Every package depends on the models.

The models depend on nothing else.

This minimizes coupling across the platform.

---

# Architectural Principles

The model layer follows several important design principles.

## Single Responsibility

Each model represents exactly one concept.

Examples:

- Indicator
- ProviderResult
- ThreatEvidence
- ThreatSummary

Models do not perform investigations.

---

## Strong Typing

Objects replace loosely structured dictionaries wherever possible.

This improves readability and reduces runtime errors.

---

## Separation of Data and Behavior

Models contain data.

Business logic belongs elsewhere.

Examples:

| Package | Responsibility |
|----------|----------------|
| providers | Collect intelligence |
| fusion | Analyze intelligence |
| report | Build investigation reports |
| renderers | Present reports |
| models | Represent data |

---

## Reusability

Every Agent within Gen2X uses the same domain models.

Future agents can reuse existing objects without redesigning data structures.

---

# Educational Goals

One objective of Gen2X is teaching students how enterprise software is structured.

Rather than writing large procedural scripts, students learn to build systems composed of reusable components.

The model layer demonstrates:

- Domain Driven Design concepts
- Separation of concerns
- Strong typing
- Object-oriented design
- Enterprise architecture patterns

These concepts scale naturally from small educational labs to production cloud security platforms.

---

# Future Growth

The model package is expected to expand as additional agents are introduced.

Examples include:

- IAM Investigation Models
- Kubernetes Security Models
- Compliance Models
- Threat Hunting Models
- Cloud Asset Models
- AI Agent Collaboration Models

Because every package already shares the same domain language, new capabilities can be added with minimal architectural change.

---

# Summary

The `models` package is the foundation of the Gen2X Security Engineering Platform.

It defines the common language used by every investigation.

Providers produce models.

Fusion analyzes models.

Reporting organizes models.

Renderers display models.

Agents orchestrate models.

By keeping these responsibilities separate, Gen2X remains modular, extensible, and easier to teach, test, and maintain.
