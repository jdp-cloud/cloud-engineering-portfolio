# Lab 12B: Executive Security Reporting Runbook

## Purpose

This runbook documents deployment, validation, operation, evidence capture,
and teardown for the standalone Lab 12B executive security reporting workflow.

Lab 12B extends the inherited Lab 12A event-driven SOAR deployment by adding
an executive-dashboard Lambda function that reads authoritative security data
from DynamoDB, calculates deterministic reporting metrics, optionally invokes
Amazon Bedrock for narrative generation, renders a PDF with ReportLab, and
publishes synchronized PDF and JSON artifacts to Amazon S3.

The workflow remains informational. It does not perform containment.

## Authorization boundary

Authorized operations include:

- reading WAF events from DynamoDB
- reading correlation findings from DynamoDB
- reading security incidents from DynamoDB
- calculating current-period and previous-period metrics
- calculating deterministic posture and material changes
- invoking the configured Bedrock model for narrative generation
- rendering the report PDF in Lambda memory
- publishing PDF and JSON artifacts to the designated S3 prefix
- preserving the existing SOAR human-review workflow

Unauthorized operations include:

- automatically blocking source IP addresses
- automatically modifying WAF rules
- isolating workloads
- disabling users, credentials, or services
- automatically changing incident disposition
- performing containment without explicit human approval

Required control fields:

```text
containment_performed = false
human_review_required = true
```

## Architecture diagram

![Lab 12B executive reporting architecture](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/architecture/lab-12b-executive-reporting-architecture.png)

PNG preview:

- [`../architecture/lab-12b-executive-reporting-architecture.png`](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/architecture/lab-12b-executive-reporting-architecture.png)

Editable source:

- [`../architecture/lab-12b-executive-reporting-architecture.excalidraw`](../architecture/lab-12b-executive-reporting-architecture.excalidraw)



## Architecture flow

```mermaid
flowchart TD
    N0["AWS WAF"]
    N1["CloudWatch Logs"]
    N2["WAF Analyzer Lambda"]
    N3["DynamoDB waf-events"]
    N4["Threat Correlation Lambda"]
    N5["DynamoDB waf-correlation-findings"]
    N6["EventBridge"]
    N7["SOAR Response Lambda"]
    N8["DynamoDB security-incidents"]
    N9["SNS notifications"]
    N10["Human analyst review"]
    R0["Executive Dashboard Lambda"]
    R1["Deterministic current and previous metrics / period comparison"]
    R2["Optional Amazon Bedrock narrative"]
    R3["ReportLab PDF rendering"]
    R4["Synchronized PDF and JSON publication"]
    R5["Amazon S3 executive-reports/"]
    R6["Executive and SOC review"]
    N0 --> N1
    N1 --> N2
    N2 --> N3
    N3 --> N4
    N4 --> N5
    N5 --> N6
    N6 --> N7
    N7 --> N8
    N8 --> N9
    N9 --> N10
    N3 --> R0
    N5 --> R0
    N8 --> R0
    R0 --> R1
    R1 --> R2
    R2 --> R3
    R3 --> R4
    R4 --> R5
    R5 --> R6
```

## Report inputs

The executive-dashboard Lambda reads:

```text
WAF_EVENTS_TABLE
CORRELATION_FINDINGS_TABLE
SECURITY_INCIDENTS_TABLE
```

The reporting period defaults to 24 hours. The Lambda compares the current
period with the immediately preceding period of equal length.

## Report configuration

Environment variables:

```text
REPORT_BUCKET
REPORT_PREFIX
BEDROCK_MODEL_ID
ENABLE_BEDROCK
REPORT_PERIOD_HOURS
MAX_ITEMS_PER_TABLE
ORGANIZATION_NAME
REPORT_TITLE
```

Default report prefix:

```text
executive-reports
```

Published object layout:

```text
executive-reports/YYYY/MM/DD/pdf/executive-security-<timestamp>.pdf
executive-reports/YYYY/MM/DD/json/executive-security-<timestamp>.json
```

The PDF and JSON are generated from the same report document and share the
same report ID and reporting period.

## ReportLab layer

Requirements file:

```text
layers/reportlab/requirements.txt
```

Required package:

```text
reportlab==4.4.3
```

Build the Python 3.12 x86_64 Lambda layer:

```bash
./scripts/build-reportlab-layer.sh
```

The completed validation build produced:

```text
Archive: terraform/reportlab-python312-x86_64.zip
Uncompressed size: 27,422,823 bytes
Archive entries: 386
Native libraries: ELF 64-bit x86-64
```

The generated layer ZIP is intentionally Git-ignored.

## Local validation

From the Lab 12B directory:

```bash
terraform -chdir=terraform fmt -check -recursive
terraform -chdir=terraform init -backend=false
terraform -chdir=terraform validate

python3 -m compileall src
python3 -m py_compile scripts/seed-and-run-lab12b-report-test.py
bash -n scripts/build-reportlab-layer.sh

python3 -m json.tool test-events/lab12b-executive-report.json >/dev/null
python3 -m json.tool test-events/lab12-correlation.json >/dev/null
```

Expected result:

```text
Terraform validation succeeds.
Python source compiles successfully.
Shell syntax validation succeeds.
JSON fixtures are valid.
```

## Terraform plan review

Create the saved plan:

```bash
terraform -chdir=terraform plan   -input=false   -out=lab12b.tfplan
```

The reviewed Lab 12B plan reported:

```text
Plan: 58 to add, 0 to change, 0 to destroy.
```

Review the following before applying:

- executive Lambda runtime is Python 3.12
- architecture is x86_64
- memory is 1024 MB
- timeout is 120 seconds
- ephemeral storage is 512 MB
- ReportLab layer is compatible with Python 3.12 and x86_64
- S3 Block Public Access is fully enabled
- S3 object ownership is BucketOwnerEnforced
- S3 default encryption is AES256
- S3 versioning is enabled
- HTTPS-only bucket policy is present
- report writes are restricted to the configured prefix
- `force_destroy = true` is limited to controlled lab cleanup

Evidence:

- [`../evidence/14-terraform-plan-complete.png`](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/14-terraform-plan-complete.png)
- [`../evidence/15-security-runtime-plan-review.png`](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/15-security-runtime-plan-review.png)

## Deployment

Apply the reviewed saved plan:

```bash
terraform -chdir=terraform apply   -input=false   lab12b.tfplan
```

Completed result:

```text
Apply complete! Resources: 58 added, 0 changed, 0 destroyed.
```

Evidence:

- [`../evidence/16-terraform-apply-complete.png`](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/16-terraform-apply-complete.png)

## Initial empty-data report

Invoke the executive-dashboard Lambda with:

```json
{
  "report_period_hours": 24
}
```

The initial deployment generated a report with:

```text
Overall security posture: NORMAL
Current WAF events: 0
Current findings: 0
Current incidents: 0
Containment performed: false
Human review required: true
```

This test proved:

- the ReportLab layer loaded successfully
- the Lambda read all three DynamoDB tables
- the PDF rendered successfully
- the JSON report was valid
- both objects were uploaded to S3
- both objects used AES256 encryption
- both objects shared the same report ID
- the authorization boundary remained intact

Evidence:

- [`../evidence/17-executive-report-publication-verified.png`](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/17-executive-report-publication-verified.png)
- [`../evidence/18-executive-security-report.pdf`](../evidence/18-executive-security-report.pdf)

## Controlled populated-data validation

The controlled test script is:

```text
scripts/seed-and-run-lab12b-report-test.py
```

It performs the following workflow:

1. Inserts two prior-period synthetic WAF records.
2. Inserts four current-period blocked WAF records.
3. Uses documentation-only source IP addresses.
4. Invokes the threat-correlation Lambda.
5. Creates a deterministic HIGH finding with risk score 60.
6. Allows EventBridge to invoke the SOAR Lambda.
7. Waits for the security incident record.
8. Invokes the executive-dashboard Lambda.
9. Verifies the synchronized S3 objects.
10. Downloads the populated PDF and JSON reports.

Run it from the repository root:

```bash
python3 members/jacques-payne/phase-1/lab12b/scripts/seed-and-run-lab12b-report-test.py
```

Expected significant output:

```text
PASS: Six synthetic WAF records were written.
PASS: Correlation finding created with severity HIGH and risk score 60.
PASS: EventBridge triggered SOAR incident creation.
PASS: Populated executive report generated from the WAF-to-correlation-to-SOAR pipeline.
```

Verified populated report result:

```text
Overall security posture: ELEVATED
Current WAF events: 4
Previous WAF events: 2
Current blocked requests: 4
Current high findings: 1
Current total incidents: 1
Awaiting human review: 1
Bedrock narrative used: True
Containment performed: False
Human review required: True
PDF encryption: AES256
JSON encryption: AES256
Synchronized report IDs: true
```

The synthetic IP addresses are documentation-only values:

```text
198.51.100.88
203.0.113.45
```

Evidence:

- [`../evidence/19-populated-report-verification.png`](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/19-populated-report-verification.png)
- [`../evidence/20-populated-executive-security-report.pdf`](../evidence/20-populated-executive-security-report.pdf)
- [`../evidence/20-populated-executive-security-report.json`](../evidence/20-populated-executive-security-report.json)

## Preserved artifact hashes

The populated report artifacts were copied from S3 before teardown.

```text
20-populated-executive-security-report.pdf
SHA-256: 6fa0549fe9a95db91dc276e44259c47a01ff18222a69ec6349b51b93d9ef210b

20-populated-executive-security-report.json
SHA-256: 4ddb0df9f218debe8a4718893b94c3a2a2320aa425e0857c6d17a29742668437
```

Verify locally:

```bash
shasum -a 256   evidence/20-populated-executive-security-report.pdf   evidence/20-populated-executive-security-report.json
```

## No-drift validation

After operational testing:

```bash
terraform -chdir=terraform plan   -detailed-exitcode   -input=false   -no-color
```

Completed result:

```text
Terraform plan exit code: 0
No changes. Your infrastructure matches the configuration.
```

Evidence:

- [`../evidence/21-terraform-no-drift.png`](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/21-terraform-no-drift.png)

## Evidence handling

Before committing evidence, redact:

- AWS account IDs
- ARNs
- API Gateway invoke URLs
- bucket names containing account IDs
- email addresses
- credentials or tokens
- real public or private IP addresses
- private environment-specific identifiers

The following synthetic values may remain visible:

- report IDs
- incident IDs
- documentation-only IP addresses
- synthetic URI paths
- WAF rule names
- risk scores
- severity values
- repository and branch identity used to establish authorship

Redactions must be flattened into the final PNG pixels.

## Teardown

Create the saved destroy plan:

```bash
terraform -chdir=terraform plan   -destroy   -input=false   -out=lab12b-destroy.tfplan
```

Completed result:

```text
Plan: 0 to add, 0 to change, 58 to destroy.
```

Evidence:

- [`../evidence/22-terraform-destroy-plan.png`](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/22-terraform-destroy-plan.png)

Apply the saved plan:

```bash
terraform -chdir=terraform apply   -input=false   -auto-approve   lab12b-destroy.tfplan
```

Completed result:

```text
Apply complete! Resources: 0 added, 0 changed, 58 destroyed.
```

Evidence:

- [`../evidence/23-terraform-destroy-complete.png`](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/23-terraform-destroy-complete.png)

## Post-destroy verification

Terraform state verification:

```text
PASS: Terraform state contains zero managed resources.
```

AWS inventory verification reported zero matching resources across:

- Lambda functions
- Lambda layers
- DynamoDB tables
- EventBridge rules
- Scheduler groups
- SNS topics
- API Gateway APIs
- WAF web ACLs
- report buckets
- Lambda log groups
- WAF log groups

Evidence:

- [`../evidence/24-post-destroy-terraform-state-empty.png`](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/24-post-destroy-terraform-state-empty.png)
- [`../evidence/25-post-destroy-aws-resources-zero.png`](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/25-post-destroy-aws-resources-zero.png)

## Operational notes

- Always pass `--region us-east-1` to AWS CLI commands for this deployment.
- Do not commit `terraform.tfvars`.
- Do not commit Terraform state or saved plan files.
- Do not commit generated Lambda archives.
- Do not commit the generated ReportLab layer ZIP.
- Preserve the PDF and JSON report pair before destroying the S3 bucket.
- Keep all containment actions behind explicit human authorization.
- Schedules remained disabled during controlled validation.
