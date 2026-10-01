# Gen2X Security Engineering Platform

# INSTALL.md

## `/models/enums`

---

## Overview

The `/models/enums` package contains the shared enumerations used
throughout the Gen2X Security Engineering Platform.

These enumerations define the common language spoken by every major
component of the framework.

Examples include:

- Threat Analysis
- Intelligence Providers
- Security Indicators
- Response Planning
- Reporting
- Platform Architecture
- Distributed Cache

Unlike normal Python constants, these enumerations represent architectural
concepts rather than implementation details.

Every agent imports these definitions to ensure that a common vocabulary is
used throughout the platform.

---

# Why Enums?

Imagine one developer writes:

```python
severity = "critical"
```

Another writes:

```python
severity = "Critical"
```

Another writes:

```python
severity = "CRIT"
```

Eventually...

Nothing matches.

Instead:

```python
ThreatSeverity.CRITICAL
```

creates one shared language.

Enums reduce ambiguity.

Consistency is one of the foundations of software architecture.

---

# Folder Structure

```text
models/

└── enums/

    base_enum.py

    indicator_enums.py

    provider_enums.py

    threat_enums.py

    response_enums.py

    report_enums.py

    cache_enums.py

    platform_enums.py

    __init__.py
```

Each module focuses on one architectural responsibility.

---

# Installation

Clone the repository.

```bash
git clone https://github.com/your-org/gen2x.git
```

Navigate to the project.

```bash
cd gen2x
```

Install dependencies.

```bash
pip install -r requirements.txt
```

The enum package requires no additional installation.

It is imported directly by Python.

---

# Importing

Example

```python
from models.enums import ThreatSeverity

severity = ThreatSeverity.CRITICAL
```

or

```python
from models.enums import PlatformRole

role = PlatformRole.SERVICE
```

---

# Architecture

The enum package follows a layered architecture.

```mermaid
flowchart TD
    N0["Indicators"] --> N1
    N1["Providers"] --> N2
    N2["Threats"] --> N3
    N3["Responses"] --> N4
    N4["Reports"] --> N5
    N5["Cache"] --> N6
    N6["Platform"]
```

Each module answers one architectural question.

---

## Indicator Enums

Question

```text
What did we observe?
```

Examples

```python
IndicatorType

IndicatorSource

IndicatorCategory
```

---

## Provider Enums

Question

```text
Where did the evidence come from?
```

Examples

```python
ProviderType

ProviderStatus

ProviderTrust
```

---

## Threat Enums

Question

```text
What does the evidence mean?
```

Examples

```python
ThreatSeverity

ThreatConfidence

ThreatAssessment

ThreatDisposition
```

---

## Response Enums

Question

```text
What should happen next?
```

Examples

```python
ResponseAction

ApprovalMode

ExecutionMode
```

---

## Report Enums

Question

```text
How should findings be communicated?
```

Examples

```python
ReportAudience

ReportType

ReportFormat
```

---

## Cache Enums

Question

```text
What information should be remembered?
```

Examples

```python
CacheKey

CacheScope

CacheFreshness
```

---

## Platform Enums

Question

```text
How is the platform organized?
```

Examples

```python
PlatformRole

PlatformResponsibility

PlatformCapability

PlatformTrustLevel
```

---

# Educational Design

This package intentionally separates ideas that are frequently combined.

Example

Threat Severity

↓

Potential impact

Threat Confidence

↓

Evidence quality

Threat Assessment

↓

Professional recommendation

Students are encouraged to understand why these concepts remain
independent.

That separation reflects how professional security investigations are
performed.

---

# Design Principles

Every enum should answer one architectural question.

Every enum should have one responsibility.

Enums should describe business concepts rather than cloud providers.

Cloud implementations change.

Architecture should remain stable.

---

# Extending the Package

Adding new capabilities rarely requires architectural changes.

Instead, new values are added to existing enumerations.

Example

```python
ThreatCondition.WEAK_TLS_CONFIGURATION

ThreatCondition.PUBLIC_S3_BUCKET

ThreatCondition.UNENCRYPTED_DATABASE

ThreatCondition.EXCESSIVE_IAM_PERMISSIONS
```

The architecture remains stable while the platform's vocabulary grows.

---

# Testing

Students are encouraged to experiment.

Examples

```python
print(ThreatSeverity.CRITICAL)

print(ThreatAssessment.REMEDIATION_RECOMMENDED)

print(PlatformRole.SERVICE)

print(CacheFreshness.STALE)
```

The purpose is not simply to memorize enum names.

The purpose is to understand the architectural questions each enum
answers.

---

# Common Mistakes

❌ Using strings instead of enums.

```python
severity = "critical"
```

Use

```python
ThreatSeverity.CRITICAL
```

---

❌ Mixing severity and confidence.

Incorrect

```python
ThreatSeverity.HIGH

means

"We are very sure."
```

Correct

```mermaid
flowchart LR
    Severity["Severity"] --> Impact["Potential impact"]
    Confidence["Confidence"] --> Quality["Evidence quality"]
```

---

❌ Combining unrelated concepts.

Example

```text
Platform

≠

Threat

≠

Response
```

Each module represents one architectural responsibility.

---

# Philosophy

Gen2X intentionally teaches software architecture through practical
security engineering.

The enum package is not simply a collection of constants.

It is a shared language.

Good software begins with good communication.

Good communication begins with shared vocabulary.

---

# Final Thoughts

Read the comments.

Seriously.

Many of the architectural discussions within the source code explain
*why* the framework is designed this way.

The comments are part of the course.

Experiment.

Modify the code.

Ask questions.

Most importantly...

Think like an engineer.

The platform may generate recommendations.

You remain responsible for understanding them.

Happy building.

— The Gen2X Team
