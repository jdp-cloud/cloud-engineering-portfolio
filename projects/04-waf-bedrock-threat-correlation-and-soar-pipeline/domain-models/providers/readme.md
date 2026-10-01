# Gen2X Threat Intelligence Providers

## Overview

The `providers` package is responsible for collecting threat intelligence from external security data sources.

Providers are the **first stage** of the Threat Intelligence pipeline.

Their responsibility is intentionally narrow:

> Collect information from one external source and normalize the results into a common format.

Providers do **not**:

- Calculate threat risk
- Make security decisions
- Build reports
- Invoke AI models
- Recommend response actions

Their only responsibility is to retrieve intelligence.

---

# Design Philosophy

Gen2X separates **collecting intelligence** from **analyzing intelligence**.

```mermaid
flowchart TD
    N0["Indicator"] --> N1
    N1["Providers"] --> N2
    N2["ProviderResult"] --> N3
    N3["Fusion Engine"] --> N4
    N4["Threat Summary"]
```

This separation makes every provider small, reusable, testable, and easy to replace.

---

# Why Providers?

Every threat intelligence source has:

- Different APIs
- Different authentication
- Different schemas
- Different terminology
- Different rate limits

Rather than allowing these differences to spread throughout the application, each provider converts external data into a common internal model.

Example:

```mermaid
flowchart TD
    N0["AbuseIPDB JSON"] --> N1
    N1["AbuseIpDbProvider"] --> N2
    N2["ProviderResult"]
```

The rest of the platform never needs to understand the AbuseIPDB API.

---

# Package Structure

```text
providers/

├── __init__.py
├── base_provider.py
├── provider_registry.py
├── abuseipdb.py
├── cisa_kev.py
├── mitre_attack.py
└── ...
```

Each file represents a single responsibility.

---

# Module Overview

## __init__.py

Provides the public interface for the package.

This allows other components to import providers without needing to know the internal file structure.

---

## base_provider.py

Defines the common functionality shared by every provider.

Typical responsibilities include:

- common interfaces
- authentication helpers
- HTTP utilities
- retry logic
- timeout handling
- error handling
- provider exceptions

Every provider inherits from the base provider.

---

## provider_registry.py

The Provider Registry acts as the orchestration layer for threat intelligence collection.

Responsibilities include:

- registering providers
- selecting compatible providers
- executing providers
- collecting results
- returning normalized ProviderResult objects

Rather than calling providers individually, the platform interacts with the registry.

```mermaid
flowchart LR
    Root["Provider Registry"]
    Root --> N0["AbuseIPDB"]
    Root --> N1["CISA KEV"]
    Root --> N2["MITRE ATT&CK"]
    Root --> N3["Future Providers"]
```

---

## abuseipdb.py

Retrieves reputation and abuse information for IP addresses.

Typical intelligence includes:

- abuse confidence score
- ISP
- country
- usage type
- hostnames
- recent reports

The provider normalizes the response into a ProviderResult.

---

## cisa_kev.py

Queries the CISA Known Exploited Vulnerabilities catalog.

Typical intelligence includes:

- CVE information
- exploitation status
- remediation due dates
- vulnerability metadata

This provider determines whether a vulnerability is known to be actively exploited.

---

## mitre_attack.py

Maps observed activity to MITRE ATT&CK techniques.

Examples include:

- Tactics
- Techniques
- ATT&CK IDs
- ATT&CK metadata

This provider supplies attacker behavior information.

It does **not** determine whether an indicator is malicious.

---

# Provider Lifecycle

Every provider follows the same workflow.

```mermaid
flowchart TD
    N0["Indicator"] --> N1
    N1["Validate Input"] --> N2
    N2["Authenticate"] --> N3
    N3["Query External API"] --> N4
    N4["Normalize Response"] --> N5
    N5["ProviderResult"]
```

Because every provider follows the same lifecycle, new providers can be added with minimal effort.

---

# Provider Responsibilities

Every provider should answer one question:

> "What does this external source know?"

Nothing more.

Providers should never answer:

- Is this malicious?
- What is the risk?
- Should we block it?
- Should we isolate a host?
- Should we escalate?

Those decisions belong to later stages of the pipeline.

---

# Relationship to Other Packages

The Providers package sits at the beginning of the investigation pipeline.

```mermaid
flowchart TD
    N0["Indicator"] --> N1
    N1["Providers"] --> N2
    N2["ProviderResult"] --> N3
    N3["Fusion"] --> N4
    N4["Reporting"] --> N5
    N5["Renderers"]
```

Providers produce facts.

Other packages interpret those facts.

---

# Architectural Principles

## Single Responsibility

Each provider integrates with exactly one external source.

Examples:

- AbuseIPDB Provider
- CISA KEV Provider
- MITRE ATT&CK Provider

A provider should never combine multiple intelligence sources.

---

## Provider Independence

Providers do not communicate with one another.

Every provider operates independently.

This makes testing significantly easier.

---

## Normalization

Every provider returns the same model:

```text
ProviderResult
```

Regardless of the source.

This allows downstream components to ignore vendor-specific API differences.

---

## Fault Isolation

One provider failing should not prevent other providers from running.

The Provider Registry is responsible for collecting successful and failed results independently.

---

## Extensibility

Adding a new provider should require:

1. Create a new provider class.
2. Inherit from BaseProvider.
3. Return ProviderResult.
4. Register the provider.

No other packages should require modification.

---

# Educational Goals

Students often interact directly with REST APIs.

This package teaches a more scalable architecture.

Instead of writing one large function that calls multiple APIs, students learn to isolate integrations into reusable provider classes.

This introduces several enterprise software concepts:

- Adapter Pattern
- Strategy Pattern
- Dependency Injection
- Separation of Concerns
- Interface-based Design
- Extensible Architecture

These patterns are common in enterprise cloud platforms and commercial security products.

---

# Future Growth

Additional providers may include:

- VirusTotal
- AlienVault OTX
- Shodan
- GreyNoise
- Recorded Future
- MISP
- AWS GuardDuty
- Microsoft Defender Threat Intelligence
- CrowdStrike Falcon Intelligence
- Google Threat Intelligence

Because every provider follows the same interface, expanding the platform requires minimal architectural change.

---

# Summary

The `providers` package serves as the intelligence collection layer of the Gen2X Security Engineering Platform.

Providers communicate with external intelligence sources.

They normalize information into shared domain models.

They never perform threat analysis.

They never determine risk.

They never recommend actions.

Instead, they provide the factual foundation upon which the rest of the platform builds deterministic security decisions.

By isolating intelligence collection from threat analysis, Gen2X remains modular, extensible, testable, and easier to understand for both students and professional engineers.
