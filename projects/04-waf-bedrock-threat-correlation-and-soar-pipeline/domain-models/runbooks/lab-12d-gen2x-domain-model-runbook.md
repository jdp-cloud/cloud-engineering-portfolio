# Lab 12D Runbook: Gen2X Shared Domain Model Layer

## Overview

Lab 12D implements the shared domain-model layer for the Gen2X Security Engineering Platform.

Unlike Labs 12A–12C, this lab doesn't build AWS infrastructure. It provides a shared dictionary and rulebook, implemented as a Python/Pydantic contract layer, that gives the platform consistent vocabulary, validation rules, serialization, cross-model composition, response governance, and reporting structure.

The core architectural rule is:

```mermaid
flowchart LR
    A0["ENUMS"] --> B0["Define controlled vocabulary"]
    A1["MODELS"] --> B1["Define validated contracts"]
    A2["AGENTS"] --> B2["Perform work using those contracts"]
```

The model layer is intentionally separate from infrastructure, provider integrations, report rendering, and threat-analysis logic.

Screenshot paths beginning with `assets/images/` are relative to the repository root. JSON artifact paths beginning with `evidence/` are relative to the lab directory.

---

## Objectives

This lab validates that the Gen2X domain model can:

- enforce controlled vocabulary through enums;
- reject unexpected or invalid data;
- validate model mutation after construction;
- serialize and restore nested domain objects;
- compose Threat and Response objects without losing provenance;
- preserve approval and governance state;
- project domain truth into human-facing reporting models;
- enforce the report lifecycle;
- prevent finalized reports from being modified;
- produce a deterministic JSON report artifact;
- preserve the instructor's existing regression suite.

---

## Environment

Validated environment:

```text
Python: 3.12.8
Virtual environment: .venv
Pydantic: 2.13.4
pytest: 9.1.1
uv: 0.12.5
```

Dependencies were installed with:

```bash
uv pip install -r requirements.txt
uv pip install pytest
```

The virtual environment is ignored by Git through the repository `.gitignore`.

Evidence:

- `assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-02-python-environment.png`

---

## Instructor-Aligned Folder Structure

The Lab 12D source layout was compared against the instructor repository.

```text
lab12d/
├── agents/
│   ├── fusion.py
│   ├── provider_registry.py
│   └── report.py
├── env/
│   └── env
├── general/
│   └── Pydantic_Explanation.md
├── models/
│   ├── __init__.py
│   ├── base_model.py
│   ├── evidence.py
│   ├── indicator.py
│   ├── provider.py
│   ├── report.py
│   ├── response.py
│   ├── threat.py
│   ├── time_utils.py
│   ├── readme.md
│   └── enums/
│       ├── __init__.py
│       ├── base_enum.py
│       ├── cache_enums.py
│       ├── indicator_enums.py
│       ├── install.md
│       ├── platform_enums.py
│       ├── provider_enums.py
│       ├── readme.md
│       ├── report_enums.py
│       ├── response_enums.py
│       └── threat_enums.py
├── providers/
│   ├── __init__.py
│   ├── abuseipdb.py
│   ├── base_provider.py
│   ├── cisa_kev.py
│   ├── mitre_attack.py
│   └── readme.md
├── tests/
│   ├── test_enums_public_api.py
│   └── test_models_roundtrip.py
├── utils/
│   ├── __init__.py
│   └── time.py
├── install.md
├── playbook.md
├── readme.md
└── requirements.txt
```

Student-added validation programs remain at the Lab 12D root:

```text
break_model.py
compose_models.py
first_model.py
full_report_lifecycle.py
mutate_model.py
report_projection.py
serialize_model.py
```

These scripts exercise the domain contracts and are separate from the instructor's core source tree.

Evidence:

- `assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-01-project-baseline.png`

---

## 1. Baseline Import Verification

The initial import check confirmed that the package could be loaded from the Lab 12D root.

```bash
python -c "
from models.enums import ThreatSeverity
from models.evidence import ThreatEvidence
from models.base_model import Gen2XModel
from utils.time import utc_now

print('Vocabulary :', ThreatSeverity.CRITICAL.describe())
print('Timestamp  :', utc_now().isoformat())
print('Agent 10 is installed correctly.')
"
```

Observed behavior:

```text
Vocabulary : Severe impact requiring immediate attention.
Agent 10 is installed correctly.
```

---

## 2. Instructor Regression Suite

The supplied test suite was executed before extending the lab.

```bash
python tests/test_enums_public_api.py
python tests/test_models_roundtrip.py
python -m pytest tests/ -q
```

Result:

```text
9 passed
```

Evidence:

- `assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-03-test-suite-9-passed.png`

---

## 3. First Domain Model and Round Trip

`first_model.py` creates a `ThreatEvidence` object using instructor-defined enums and nested models.

The object represents a GitHub token exposure and demonstrates:

- provider identity;
- platform identity;
- indicator type and value;
- indicator source;
- threat condition;
- severity;
- model description;
- serialization/deserialization round trip.

Expected result:

```text
GitHub observed TOKEN_EXPOSURE for ghp_example
Round trip: True
```

Evidence:

- `assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-04-first-domain-model-roundtrip.png`

### Troubleshooting Note

The script was initially created inside `models/`, which caused:

```text
ModuleNotFoundError: No module named 'models'
```

The fix was to place and run validation scripts from the Lab 12D project root so package imports resolve correctly.

---

## 4. Contract Failure Test

`break_model.py` intentionally supplies an unexpected field to `EvidenceIdentity`.

The model rejects the invalid field through the base Pydantic configuration:

```text
extra="forbid"
```

Expected result:

```text
PASS: Gen2X rejected the unexpected field.
Extra inputs are not permitted
```

Evidence:

- `assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-05-contract-validation-rejection.png`

This proves the shared contract layer rejects undeclared input instead of silently accepting malformed data.

---

## 5. Assignment Validation

`mutate_model.py` verifies that validation continues after object construction.

A valid `EvidenceIdentity` is created, then the provider name is mutated to an invalid blank value.

Expected result:

```text
Original provider: GitHub
PASS: Gen2X rejected the invalid mutation.
provider_name cannot be empty.
Provider after failed mutation: GitHub
```

Evidence:

- `assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-06-assignment-validation.png`

This validates assignment-time enforcement and confirms the original valid state is preserved when mutation fails.

---

## 6. Serialization and Restoration

`serialize_model.py` validates JSON-safe serialization of nested Gen2X models.

The test verifies:

- enum serialization;
- UTC timestamp serialization;
- nested model serialization;
- JSON artifact creation;
- enum reconstruction;
- model equality after restoration.

Generated artifact:

```text
evidence/lab12d-07-threat-evidence.json
```

Expected result:

```text
Restored severity type: ThreatSeverity
Round trip equal: True
```

Evidence:

- `assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-07-serialization-roundtrip.png`
- `evidence/lab12d-07-threat-evidence.json`

---

## 7. Controlled Vocabulary Troubleshooting

During Threat → Response composition, the initial test used:

```python
ThreatConfidence.HIGH
```

The model rejected it because `HIGH` belongs to severity vocabulary, not confidence vocabulary.

The valid confidence values are:

```text
UNKNOWN
OBSERVED
SUSPECTED
CORRELATED
VALIDATED
VERIFIED
```

The corrected value was:

```python
ThreatConfidence.VERIFIED
```

This is an important domain-model distinction:

```text
Severity
    = potential impact

Confidence
    = strength of evidence
```

Evidence:

- `assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-08-troubleshooting-invalid-threat-confidence-enum.png`

---

## 8. Threat → Response Composition

`compose_models.py` validates cross-model composition.

The Threat contains:

- threat identity;
- token-exposure condition;
- critical severity;
- verified confidence;
- evidence provenance;
- provider provenance.

The Response contains:

- a reference to the Threat ID;
- a concrete repository target;
- a containment recommendation;
- critical response priority;
- manual execution mode;
- single-approver governance.

The response is intentionally not executable before approval.

Expected sequence:

```text
Threat linkage valid: True
Requires approval: True
Pending approval: True
Executable before approval: False
Approval status: APPROVED
Approved by: security-lead
Executable after approval: True
PASS: Threat and Response contracts composed successfully.
```

Evidence:

- `assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-09-threat-response-composition.png`

The model separates:

```text
recommendation
authorization
execution
```

Approval authorizes the response. It does not itself perform execution.

---

## 9. Report Projection

`report_projection.py` verifies that reporting objects preserve the facts established by the underlying Threat and Response domains.

The projection preserves:

- threat condition;
- severity;
- confidence;
- evidence count;
- provider count;
- response action;
- response priority;
- investigation status;
- approval state.

Expected result:

```text
Severity preserved: True
Confidence preserved: True
Evidence count preserved: True
Response action preserved: True
Approval status preserved: True
PASS: Gen2X report projections preserved domain facts.
```

Evidence:

- `assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-10-report-projection.png`

The reporting rule is:

```text
Presentation may change.
Truth must not.
```

---

## 10. ReportStatus Contract Mismatch

A cross-model integration defect was discovered between the instructor's `Report` model and the instructor's `ReportStatus` enum.

The `Report` lifecycle references:

```text
DRAFT
REVIEW
FINAL
ARCHIVED
```

but the original enum did not define:

```text
REVIEW
FINAL
```

Local verification:

```bash
python -c "
from models.enums import ReportStatus

print('Defined statuses:', [item.value for item in ReportStatus])
print('REVIEW exists:', hasattr(ReportStatus, 'REVIEW'))
print('FINAL exists:', hasattr(ReportStatus, 'FINAL'))
"
```

Original result:

```text
REVIEW exists: False
FINAL exists: False
```

Evidence:

- `assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-11-troubleshooting-report-status-contract-mismatch.png`

---

## 11. ReportStatus Remediation

The minimum contract-alignment fix was applied to:

```text
models/enums/report_enums.py
```

Added enum values:

```python
REVIEW = "REVIEW"
FINAL = "FINAL"
```

Added human-readable descriptions:

```python
ReportStatus.REVIEW: (
    "The report is under review before finalization."
),

ReportStatus.FINAL: (
    "The report has been finalized as a historical record."
),
```

Regression test after the change:

```bash
python -m pytest tests/ -q
```

Result:

```text
9 passed
```

Contract verification after remediation:

```text
REVIEW exists: True
FINAL exists: True
```

Evidence:

- `assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-12-report-status-contract-remediated.png`

The remediation aligned the enum vocabulary with the lifecycle already implemented by the `Report` model.

---

## 12. Complete Report Lifecycle

`full_report_lifecycle.py` composes a complete report from validated Threat and Response state.

The test exercises:

```mermaid
flowchart TD
    N0["Threat"] --> N1
    N1["Governed Response"] --> N2
    N2["Structured Report"] --> N3
    N3["DRAFT"] --> N4
    N4["REVIEW"] --> N5
    N5["FINAL"] --> N6
    N6["ARCHIVED"]
```

Observed output:

```text
Initial status: DRAFT
Finding count: 1
Evidence count: 1
Provider count: 1
Approval status: APPROVED

After review submission: REVIEW
After finalization: FINAL

PASS: Final report rejected mutation.
Mutation guard: Finalized or archived reports cannot be modified.
Issue a new report or revision instead.

Archived status: ARCHIVED
PASS: Complete Gen2X report lifecycle validated.
```

Evidence:

- `assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-13-complete-report-lifecycle.png`

Generated machine-readable report:

- `evidence/lab12d-13-final-gen2x-report.json`

---

## 13. Final Artifact Integrity

The final JSON report was hashed with SHA-256:

```text
49fe44fcec8b0ec8b7131c547fcbcc8788d2a9318a57bc22f80046d4e5df0687
```

Artifact:

```text
evidence/lab12d-13-final-gen2x-report.json
```

The final validation also reran the regression suite:

```text
9 passed in 0.12s
```

Evidence:

- `assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-14-final-validation.png`

---

## 14. Git and Repository Hygiene

Validated ignore behavior:

```text
.venv/       ignored
__pycache__/ ignored
.DS_Store    ignored
```

The repository-wide `.gitignore` also contains:

```text
env/
```

That rule conflicts with the instructor's legitimate Lab 12D directory:

```text
lab12d/env/env
```

The instructor file was intentionally force-added:

```bash
git add -f env/env
```

Verification:

```bash
git ls-files env/env
```

Result:

```text
env/env
```

This preserves the instructor file while keeping transient environment directories ignored elsewhere in the repository.

---

## 15. Evidence Inventory

```text
assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-01-project-baseline.png
assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-02-python-environment.png
assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-03-test-suite-9-passed.png
assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-04-first-domain-model-roundtrip.png
assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-05-contract-validation-rejection.png
assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-06-assignment-validation.png
assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-07-serialization-roundtrip.png
evidence/lab12d-07-threat-evidence.json
assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-08-troubleshooting-invalid-threat-confidence-enum.png
assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-09-threat-response-composition.png
assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-10-report-projection.png
assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-11-troubleshooting-report-status-contract-mismatch.png
assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-12-report-status-contract-remediated.png
assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-13-complete-report-lifecycle.png
evidence/lab12d-13-final-gen2x-report.json
assets/images/members/jacques-payne/phase-2/lab12d/evidence/lab12d-14-final-validation.png
```

---

## 16. Final Validation Commands

Use the following before commit or submission:

```bash
python -m pytest tests/ -q
```

Expected:

```text
9 passed
```

Verify the final report artifact:

```bash
ls -lh evidence/lab12d-13-final-gen2x-report.json
shasum -a 256 evidence/lab12d-13-final-gen2x-report.json
```

Verify the ReportStatus contract:

```bash
python -c "
from models.enums import ReportStatus

print('Defined statuses:', [item.value for item in ReportStatus])
print('REVIEW exists:', hasattr(ReportStatus, 'REVIEW'))
print('FINAL exists:', hasattr(ReportStatus, 'FINAL'))
"
```

Expected:

```text
REVIEW exists: True
FINAL exists: True
```

Verify the instructor environment file is tracked:

```bash
git ls-files env/env
```

Expected:

```text
env/env
```

Check Lab 12D worktree:

```bash
git status --short .
```

---

## Result

Lab 12D now provides a validated shared contract layer for Gen2X.

The completed work demonstrates:

```mermaid
flowchart TD
    N0["controlled vocabulary"] --> N1
    N1["validated domain contracts"] --> N2
    N2["evidence serialization"] --> N3
    N3["threat conclusions"] --> N4
    N4["governed response recommendations"] --> N5
    N5["approval state"] --> N6
    N6["truth-preserving report projections"] --> N7
    N7["controlled report lifecycle"] --> N8
    N8["immutable historical artifacts"]
```

The instructor regression suite remains green, the ReportStatus integration defect was corrected, and the final report artifact was serialized and hashed for integrity verification.
