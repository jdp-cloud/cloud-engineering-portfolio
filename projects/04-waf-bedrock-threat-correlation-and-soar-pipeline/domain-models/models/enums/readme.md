# Gen2X Enumerations

## Overview

The `enums` package defines the shared vocabulary used throughout the Gen2X Security Engineering Platform.

Unlike models, which represent data, or providers, which retrieve information, enumerations define the finite set of valid values that can be used across the platform.

Examples include:

- Risk Levels
- Provider Status
- Indicator Types
- Report Status
- Response Status

By centralizing these values, Gen2X improves consistency, readability, and type safety while reducing programming errors caused by arbitrary string values.

---

# Design Philosophy

Enterprise software is built around a common language.

Instead of allowing every developer to write:

```python
risk = "high"

risk = "High"

risk = "HIGH"

risk = "Critical"

risk = "critical"
```

Gen2X defines a single vocabulary:

```python
RiskLevel.HIGH
```

Every package throughout the platform speaks the same language.

---

# Why Enumerations?

Many software bugs are caused by invalid string values.

Instead of:

```python
provider.status = "Complete"
```

Gen2X uses:

```python
provider.status = ProviderStatus.SUCCESS
```

This provides:

- IDE auto-completion
- Compile-time type checking
- Consistent naming
- Easier refactoring
- Self-documenting code

---

# Package Structure

```text
enums/

├── __init__.py
├── base_enum.py
├── indicator_enums.py
├── provider_enums.py
├── threat_enums.py
├── report_enums.py
├── response_enums.py
├── cache_enums.py
└── platform_enums.py
```

Each module groups related enumerations by domain.

---

# Module Overview

## __init__.py

Provides the public interface for the package.

Rather than importing individual modules:

```python
from models.enums.threat_enums import RiskLevel
```

developers simply write:

```python
from models.enums import RiskLevel
```

This keeps the internal structure hidden while providing a clean SDK.

---

## base_enum.py

Defines the common behavior shared by every Gen2X enumeration.

Typical functionality includes:

- string conversion
- validation
- enumeration names
- enumeration values
- helper methods
- pretty printing

Every enumeration inherits from the same base class.

---

## indicator_enums.py

Defines valid indicator-related values.

Examples include:

- IndicatorType
- IndicatorSource
- IndicatorConfidence

---

## provider_enums.py

Defines provider execution states and capabilities.

Examples include:

- ProviderStatus
- ProviderType
- ProviderCapability
- ProviderHealth

---

## threat_enums.py

Defines threat analysis terminology.

Examples include:

- RiskLevel
- ThreatCategory
- ThreatConfidence
- PriorityLevel

---

## report_enums.py

Defines reporting-specific values.

Examples include:

- ReportStatus
- FindingSeverity
- RecommendationPriority
- ReportFormat

---

## response_enums.py

Defines API response values.

Examples include:

- ResponseStatus
- ResponseType

---

## cache_enums.py

Defines cache-related values used throughout the platform.

Examples include:

- CacheStatus
- CachePolicy
- CacheOperation

---

## platform_enums.py

Defines platform-wide infrastructure values.

Examples include:

- Environment
- ExecutionMode
- AgentStatus
- LogLevel

---

# Relationship to Other Packages

The Enumerations package is used throughout the entire platform.

```mermaid
flowchart BT
    Root["enums"]
    N0["Models"] --> Root
    Agents["Agents"] --> N0
    N1["Providers"] --> Root
    Agents["Agents"] --> N1
    N2["Reporting"] --> Root
    Agents["Agents"] --> N2
```

Enumerations define the shared vocabulary used by every package.

---

# Architectural Pattern

One of the primary design goals of Gen2X is consistency.

Every major package follows the same architectural pattern.

## Models

```text
models/

├── __init__.py
├── base_model.py
└── domain models...
```

Purpose:

Represent platform data.

---

## Providers

```text
providers/

├── __init__.py
├── base_provider.py
├── provider_registry.py
└── provider implementations...
```

Purpose:

Collect information from external systems.

---

## Enumerations

```text
enums/

├── __init__.py
├── base_enum.py
└── domain enumerations...
```

Purpose:

Define the platform vocabulary.

---

Although each package serves a different purpose, they all follow the same architectural convention:

```text
Package
│
├── __init__.py
│
├── base_*.py
│
├── domain-specific modules
│
└── README.md
```

Once students learn one package, they can easily navigate every other package in the framework.

---

# Educational Goals

This package introduces several enterprise software engineering concepts:

- Strong typing
- Enumerations
- Domain-driven vocabulary
- Shared platform contracts
- Package organization
- Public APIs
- Framework consistency

Students quickly discover that enterprise software is not a collection of unrelated files.

Instead, it is a collection of reusable architectural patterns.

---

# Future Growth

As additional Gen2X agents are developed, new enumerations can be added without changing the existing architecture.

Examples include:

- Kubernetes Security
- Identity & Access Management
- Compliance
- AI Agents
- Threat Hunting
- Cloud Asset Inventory
- Digital Forensics

Each new domain simply introduces another enumeration module while preserving the overall package structure.

---

# Summary

The `enums` package provides the common language used throughout the Gen2X Security Engineering Platform.

Rather than storing arbitrary string values, Gen2X defines a shared vocabulary through strongly typed enumerations.

Just as `models` represents data and `providers` collect information, `enums` defines the language that allows every package to communicate consistently.

By following the same architectural pattern used throughout the framework, the `enums` package reinforces one of Gen2X's core educational principles:

> Learn one package, and you can understand them all.
