# Pydantic in Gen2X

> **Purpose:** This document explains what Pydantic is, why Gen2X uses it, and why understanding it is useful for security engineers.

---

## 1. What Is Pydantic?

[Pydantic](https://docs.pydantic.dev/) is a Python library for defining, validating, and serializing structured data.

At its simplest, Pydantic allows us to describe what an object **should look like** and then validate data against that definition.

Consider a normal Python class:

```python
class Threat:
    def __init__(self, severity, confidence):
        self.severity = severity
        self.confidence = confidence
```

Python will happily allow this:

```python
threat = Threat(
    severity="potato",
    confidence=42,
)
```

Python does exactly what we asked.

Unfortunately, what we asked was nonsense.

Pydantic allows us to establish stronger expectations about the data entering our system.

```python
from pydantic import BaseModel

class Threat(BaseModel):
    severity: ThreatSeverity
    confidence: ThreatConfidence
```

Now the model defines a **data contract**.

A threat is expected to contain:

- a valid `ThreatSeverity`
- a valid `ThreatConfidence`

Invalid data can be rejected before it travels deeper into the application.

That is the first reason we use Pydantic.

---

# 2. Security Systems Have Trust Boundaries

Gen2X receives information from many possible sources.

For example:

```text
AWS
Azure
GCP
GitHub
OnPrem
APIs
Configuration Files
Security Tools
Human Analysts
LLMs
```

Those systems may produce data that is:

- missing
- malformed
- outdated
- inconsistent
- unexpected
- incorrectly typed
- incomplete

Security engineers should therefore avoid assuming:

> "The data exists, so it must be correct."

That is a trust failure.

Instead:

```mermaid
flowchart TD
    N0["External Data"] --> N1
    N1["Validation Boundary"] --> N2
    N2["Domain Model"]
```

Pydantic helps us construct that validation boundary.

---

# 3. Pydantic Does Not Make Data True

This distinction is extremely important.

Pydantic can determine whether data conforms to the structure we expect.

It cannot determine whether the information itself is true.

For example:

```python
class Observation(BaseModel):
    account_id: str
    region: str
```

This might successfully validate:

```python
Observation(
    account_id="123456789012",
    region="us-east-1",
)
```

Pydantic can tell us:

```text
account_id is present
region is present
both satisfy the model
```

It cannot tell us:

```text
Does account 123456789012 actually exist?

Did this observation really originate from AWS?

Is us-east-1 actually the correct region?

Was the source compromised?

Is the information current?
```

Those are different security questions.

Therefore:

> **Validation is not verification.**

And:

> **Valid data is not automatically trustworthy data.**

---

# 4. Why Gen2X Uses Pydantic

Gen2X contains many domain models.

Examples include:

```text
Provider
Evidence
Indicator
Threat
Response
Report
```

Those models move information between different parts of the system.

Without validation, malformed data can travel surprisingly far.

```mermaid
flowchart TD
    N0["Provider"] --> N1
    N1["Evidence"] --> N2
    N2["Fusion"] --> N3
    N3["Threat"] --> N4
    N4["Response"] --> N5
    N5["Report"]
```

Imagine discovering at `Report` that a value produced five stages earlier was invalid.

That is not where we want to discover the problem.

Pydantic allows validation to happen closer to the boundary where the model is created.

```mermaid
flowchart TD
    N0["Provider"] --> N1
    N1["Evidence"] --> N2
    N2["Validate evidence at the boundary"] --> N3
    N3["Fusion"]
```

This follows a useful engineering principle:

> **Reject bad state as early as practical.**

---

# 5. Models Become Contracts

Consider:

```python
class ResponseRecommendation(BaseModel):

    action: ResponseAction

    priority: ResponsePriority

    rationale: str
```

This tells another engineer exactly what the object expects.

A recommendation requires:

```text
ResponseAction
ResponsePriority
rationale
```

The model therefore becomes a contract between components.

```mermaid
flowchart TD
    N0["Threat Analysis"] --> N1
    N1["ResponseRecommendation"] --> N2
    N2["Response Processing"]
```

The consumer should not have to guess what the producer meant.

This becomes increasingly important as software grows.

---

# 6. Type Hints Become Operational

Python type hints are extremely useful.

For example:

```python
severity: ThreatSeverity
```

helps:

- developers
- IDEs
- static analysis tools
- documentation
- code reviewers

But ordinary Python type annotations generally do not enforce themselves at runtime.

Pydantic uses those annotations when validating model data.

That gives us a useful combination:

```text
Python Type Hints
       +
Runtime Validation
       +
Structured Models
```

The same model definition helps both the developer and the running application.

---

# 7. Enums and Pydantic Work Very Well Together

Gen2X makes extensive use of enums.

For example:

```python
class ThreatSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

A model can then require:

```python
class ThreatSummary(BaseModel):
    severity: ThreatSeverity
```

This is much safer than allowing arbitrary strings everywhere.

Without the enum:

```python
severity = "critical"
severity = "Critical"
severity = "CRITICAL"
severity = "crit"
severity = "very_bad"
severity = "OMG"
```

Eventually someone writes:

```python
if severity == "Critical":
```

while another component produces:

```text
CRITICAL
```

Congratulations.

We have invented a bug.

Enums define the vocabulary.

Pydantic helps enforce that vocabulary at model boundaries.

```text
Enum
    defines acceptable meaning

Pydantic
    validates model structure

Domain Model
    represents the security concept
```

---

# 8. Field Validation

Sometimes a correct Python type is still not sufficient.

Consider:

```python
threat_id: str
```

This is technically a string:

```python
threat_id = ""
```

But an empty threat identifier is not useful.

Pydantic validators allow us to enforce additional rules.

```python
from pydantic import field_validator

class ReportIdentity(BaseModel):

    threat_id: str

    @field_validator("threat_id")
    @classmethod
    def validate_threat_id(
        cls,
        value: str,
    ) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "threat_id cannot be empty."
            )

        return value
```

Now the model expresses something about the **meaning** of the field, not merely its Python type.

---

# 9. Normalization

Real-world data is messy.

A user or provider may give us:

```python
"   us-east-1   "
```

when what we actually want is:

```python
"us-east-1"
```

Validators can normalize values:

```python
@field_validator("region")
@classmethod
def normalize_region(
    cls,
    value: str | None,
) -> str | None:

    if value is None:
        return None

    value = value.strip()

    return value or None
```

This reduces repeated cleanup throughout the rest of the code.

Instead of every component doing this:

```text
Did someone trim this?

Is "" equivalent to None?

Does this value contain whitespace?

Did another component already normalize it?
```

we normalize the data at an appropriate boundary.

---

# 10. Validation Should Not Become Business Logic

There is a danger here.

Once developers discover validators, everything starts looking like something that should become a validator.

Do not do this.

For Gen2X:

```text
Pydantic
    validates models

Fusion
    analyzes evidence

Threat
    represents conclusions

Response
    represents recommendations and governance

Report
    communicates results
```

Pydantic should not secretly become our threat-analysis engine.

For example, this would be questionable:

```python
@field_validator("severity")
def magically_determine_severity(...):
    ...
```

Severity should come from the threat-assessment logic.

The model should validate and represent the result.

This distinction matters:

> **Models represent domain state.**

> **Services and agents perform domain reasoning.**

---

# 11. Pydantic and Serialization

Security applications constantly exchange data.

Eventually an object may need to become:

- JSON
- an API response
- a database record
- a log entry
- a message
- a report artifact

Pydantic provides useful serialization support.

For example:

```python
data = report.model_dump()
```

produces a Python representation.

For JSON-friendly output:

```python
data = report.model_dump(
    mode="json"
)
```

Pydantic can handle nested models, enums, UUIDs, timestamps, and many common Python types.

This is particularly useful in Gen2X because our models are composed.

```mermaid
flowchart LR
    Root["Report"]
    Root --> N0["ReportIdentity"]
    Root --> N1["ReportAudience"]
    Root --> N2["ExecutiveSummary"]
    Root --> N3["ThreatSummary"]
    Root --> N4["ResponseSummary"]
    Root --> N5["ReportEvidenceSummary"]
    Root --> N6["ReportAccountability"]
```

Pydantic understands the nested structure.

We do not need to manually convert every object into a dictionary.

---

# 12. Nested Models

Pydantic models can contain other Pydantic models.

For example:

```python
class Response(BaseModel):

    identity: ResponseIdentity

    target: ResponseTarget

    recommendation: ResponseRecommendation

    investigation: InvestigationState

    governance: ResponseGovernance
```

This is extremely useful for domain-driven architecture.

Instead of building one enormous object:

```text
Response
    47 unrelated fields
```

we can compose meaningful concepts:

```mermaid
flowchart LR
    Root["Response"]
    Root --> N0["Identity"]
    Root --> N1["Target"]
    Root --> N2["Recommendation"]
    Root --> N3["Investigation"]
    Root --> N4["Governance"]
```

Each object has a clear responsibility.

That makes the architecture easier to:

- understand
- test
- debug
- maintain
- extend

---

# 13. Default Factories

Some values should be created when the model is instantiated.

For example:

```python
from uuid import uuid4

response_id: UUID = Field(
    default_factory=uuid4
)
```

Every new instance receives its own UUID.

Likewise:

```python
created_at: datetime = Field(
    default_factory=utc_now
)
```

This is preferable to evaluating the function when the class itself is defined.

The important distinction is:

```python
default_factory=utc_now
```

not:

```python
default=utc_now()
```

The factory is called when a new model instance is created.

---

# 14. Mutable Default Values

Collections require care in Python.

Gen2X commonly uses:

```python
notes: list[str] = Field(
    default_factory=list
)
```

or:

```python
metadata: dict[str, Any] = Field(
    default_factory=dict
)
```

Each model receives its own collection.

This is clearer and safer than casually sharing mutable state between objects.

---

# 15. Assignment Validation

Many Gen2X models use:

```python
model_config = ConfigDict(
    validate_assignment=True,
    extra="forbid",
)
```

These two settings are intentional.

## `validate_assignment=True`

Validation also occurs when fields are changed after model creation.

For example:

```python
model.severity = some_value
```

Pydantic can validate the new value.

Without assignment validation, initial construction may be validated while later mutations bypass some of those protections.

---

## `extra="forbid"`

Unexpected fields are rejected.

Imagine we expect:

```python
ThreatSummary(
    severity=...,
    confidence=...,
)
```

but someone provides:

```python
ThreatSummary(
    severity=...,
    confidence=...,
    confdience=...,
)
```

Notice the typo:

```text
confdience
```

Silently accepting unexpected fields can hide mistakes.

`extra="forbid"` helps us fail loudly instead.

For security engineering, that is usually desirable.

> **Unexpected data deserves attention.**

---

# 16. Pydantic Improves Error Visibility

One major advantage of validation is not merely preventing errors.

It is making errors visible **closer to their source**.

Without validation:

```mermaid
flowchart TD
    N0["Bad Input"] --> N1
    N1["Evidence"] --> N2
    N2["Fusion"] --> N3
    N3["Threat"] --> N4
    N4["Response"] --> N5
    N5["Report"] --> N6
    N6["Mysterious Failure"]
```

Now the engineer must investigate the entire pipeline.

With validation:

```mermaid
flowchart TD
    N0["Bad Input"] --> N1
    N1["Evidence Model"] --> N2
    N2["VALIDATION ERROR"]
```

The failure occurs much closer to where the invalid state entered the system.

That dramatically improves debugging.

---

# 17. Why This Matters for Security Engineers

Security engineers frequently work at integration boundaries.

You may consume data from:

```text
Cloud APIs
SIEM platforms
EDR systems
Identity providers
GitHub
Asset inventories
Threat intelligence
Internal APIs
LLMs
Human input
```

Those boundaries are exactly where assumptions become dangerous.

Pydantic encourages you to ask:

```text
What data do I expect?

Which fields are required?

Which values are valid?

What can be missing?

What should be normalized?

What should be rejected?

What should remain unknown?
```

Those are not merely programming questions.

They are **trust questions**.

---

# 18. Pydantic and Zero Trust Thinking

Zero Trust is often summarized as:

> Never trust, always verify.

That slogan is useful, but software needs concrete mechanisms.

Pydantic is not a Zero Trust system.

However, its design encourages a compatible engineering habit:

```mermaid
flowchart TD
    N0["Do not blindly accept data"] --> N1
    N1["Define expectations"] --> N2
    N2["Validate incoming state"] --> N3
    N3["Reject malformed state"] --> N4
    N4["Continue processing"]
```

That does not establish truth.

It establishes a stronger boundary.

Think of it as:

```text
"I still do not necessarily trust you.

But before we continue,
you are at least going to speak
the language this system expects."
```

---

# 19. Validation Is Only One Layer of Trust

Gen2X should never treat Pydantic validation as sufficient evidence of trust.

A useful mental model is:

```mermaid
flowchart LR
    A0["STRUCTURAL VALIDITY"] --> B0["Is the data shaped correctly?"]
    A1["SOURCE"] --> B1["Where did the data come from?"]
    A2["AUTHENTICITY"] --> B2["Can we establish who produced it?"]
    A3["INTEGRITY"] --> B3["Has the data been altered?"]
    A4["CORROBORATION"] --> B4["Do independent observations support it?"]
    A5["CONFIDENCE"] --> B5["How strongly should we believe the conclusion?"]
    A6["AUTHORITY"] --> B6["Who is permitted to act?"]
```

Pydantic helps primarily with the first layer.

The rest belongs to the broader security architecture.

---

# 20. Pydantic Does Not Replace Testing

A Pydantic model can validate perfectly and still represent badly designed software.

For example:

```python
class Everything(BaseModel):
    everything: dict
```

Congratulations.

It validates.

It also tells us almost nothing.

Good architecture still requires:

- meaningful domain boundaries
- meaningful names
- appropriate enums
- tests
- business rules
- threat modeling
- code review
- security review

Pydantic is a tool.

It is not an architect.

---

# 21. Pydantic Does Not Replace Type Checking

Runtime validation and static type checking solve related but different problems.

Tools such as:

```text
VS Code / Pylance
Pyright
mypy
```

help identify problems while writing code.

Pydantic helps validate model data while the program is running.

A healthy development workflow uses both ideas:

```mermaid
flowchart LR
    A0["IDE / Static Analysis"] --> B0["Does this code make sense?"]
    A1["Pydantic"] --> B1["Does this runtime data satisfy the model?"]
    A2["Tests"] --> B2["Does the software behave correctly?"]
    A3["Security Analysis"] --> B3["Should the software behave this way?"]
```

None of these replaces the others.

---

# 22. A Gen2X Example

Consider a response recommendation:

```python
recommendation = ResponseRecommendation(
    action=ResponseAction.ROTATE_SECRET,
    priority=ResponsePriority.CRITICAL,
    rationale=(
        "A production credential was discovered "
        "in a publicly accessible repository."
    ),
)
```

Pydantic can help establish that:

```text
action
    is a valid ResponseAction

priority
    is a valid ResponsePriority

rationale
    satisfies our model requirements
```

But Pydantic cannot establish:

```text
Was the credential really exposed?

Is it still valid?

Does it provide production access?

Was the repository actually public?

Should we rotate the credential?

Who may authorize the rotation?
```

Those questions belong elsewhere.

This distinction is fundamental.

---

# 23. Pydantic and LLMs

Gen2X may use LLMs as part of larger workflows.

This makes structured validation even more useful.

LLMs produce probabilistic output.

Domain models require predictable structure.

The boundary can therefore look like:

```mermaid
flowchart TD
    LLM["LLM"] -->|Proposed structured output| Validation{"Pydantic validation"}
    Validation -->|Invalid| Reject["Reject / retry / investigate"]
    Validation -->|Valid| Model["Validated model"]
```

But once again:

> **Schema-valid LLM output is not automatically factually correct.**

If an LLM produces:

```json
{
    "severity": "critical",
    "confidence": "high"
}
```

and those values satisfy the model, Pydantic has established only that the values are structurally acceptable.

It has not established that the threat is actually critical.

That still requires evidence and reasoning.

---

# 24. Why Students Should Learn Pydantic

You are not learning Pydantic because Gen2X happens to use a particular Python library.

You are learning it because modern software increasingly depends on **structured boundaries between components**.

The exact technology may change.

Today you may use:

```text
Pydantic
```

Tomorrow you may encounter:

```text
JSON Schema
Protocol Buffers
OpenAPI
Typed API clients
ORM models
Message schemas
Event schemas
Cloud SDK models
```

The deeper engineering skill is learning to think in contracts.

Ask:

```text
What enters this component?

What leaves this component?

What assumptions are allowed?

What assumptions must be validated?

What happens when those assumptions fail?
```

That skill transfers far beyond Pydantic.

---

# 25. What Pydantic Gives Gen2X

In practical terms, Pydantic gives this project:

| Capability | Benefit |
|---|---|
| Type validation | Reduces malformed domain state |
| Enum integration | Enforces controlled vocabularies |
| Field validators | Supports domain-specific validation |
| Normalization | Cleans data at model boundaries |
| Nested models | Supports composable architecture |
| Serialization | Simplifies JSON/API/report output |
| UUID support | Handles strongly typed identifiers |
| Datetime support | Handles timestamps consistently |
| Assignment validation | Protects models after construction |
| Extra-field rejection | Exposes unexpected input |
| Clear errors | Makes debugging easier |
| Type hints | Improves IDE and developer experience |

But perhaps the largest benefit is simpler:

> **The architecture becomes explicit.**

---

# 26. What Pydantic Does NOT Give Gen2X

Pydantic does not automatically provide:

```text
Truth
Trust
Authentication
Authorization
Integrity
Threat assessment
Corroboration
Security
Correct architecture
Correct business logic
Correct decisions
```

Those remain our responsibility.

This is especially important in security engineering.

A beautifully validated malicious input is still malicious.

A perfectly serialized false conclusion is still false.

A valid credential is not necessarily authorized for the action being attempted.

And a system capable of performing an action has not automatically earned the authority to perform it.

---

# 27. The Gen2X Rule

When you encounter a Pydantic model in this project, ask three questions:

```text
1. What does this model REPRESENT?

2. What assumptions does this model VALIDATE?

3. What does this model deliberately NOT DECIDE?
```

For example:

```text
ResponseRecommendation

REPRESENTS
    A recommended security action.

VALIDATES
    The structure of that recommendation.

DOES NOT DECIDE
    Whether execution is authorized.
```

Or:

```text
Report

REPRESENTS
    A human-consumable security record.

VALIDATES
    The structure of that record.

DOES NOT DECIDE
    Whether the underlying threat is real.
```

If you can answer those three questions, you understand much more than the syntax.

You understand the architecture.

---

# 28. Final Takeaway

Pydantic helps Gen2X move from:

```text
"I received some Python data."
```

to:

```text
"I received data that conforms to
a defined model."
```

That is valuable.

But never accidentally translate that into:

```text
"Therefore I trust it."
```

Security engineering begins precisely where that assumption ends.

---

## Chewbacca's Commentary 🐾

A stranger

walks up

and hands you

a box.

The box

has the correct

dimensions.

It has

the correct

label.

It weighs

exactly

what you expected.

Pydantic

looks at the box

and says:

"Yes.

This is shaped

like the box

we agreed

to accept."

Good.

That is useful.

Now the

security engineer

asks:

"Who gave you

the box?"

"Where has it

been?"

"Who had access

to it?"

"Has anyone

opened it?"

"Why are you

giving it

to me?"

"And why

is it ticking?"

That

is the difference

between

validation

and

trust.

Pydantic

helps us

enforce

the contract.

It does not

remove

our responsibility

to think.

Never surrender

that responsibility

to a library.

Never surrender

it to

an API.

Never surrender

it to

an LLM.

And certainly

never surrender

it because

the JSON

looked

really nice.

Trust

must be

earned.

Authority

must be

granted.

Evidence

must be

examined.

And when

the box

starts ticking...

perhaps

stop admiring

the schema.

— Chewbacca
Chief Wookiee Architect
Data Validation Department
Porg Sushi Supply Chain Security
