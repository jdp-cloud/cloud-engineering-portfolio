# Lab 12 - AWS WAF, Amazon Bedrock, and Threat Correlation

## **Armageddon #2 · SEIR Foundations · Phase 1**

## 1. Lab Purpose and Objectives

Lab 12 deploys and validates a serverless AWS security-analysis workflow using Terraform.

The solution protects an Amazon API Gateway endpoint with AWS WAF, sends WAF telemetry to Amazon CloudWatch Logs, analyzes blocked requests with AWS Lambda and Amazon Bedrock, stores normalized security events in Amazon DynamoDB, and correlates recent events into security findings.

### Objectives

- Deploy the lab infrastructure with Terraform.
- Protect an API Gateway endpoint with AWS WAF.
- Prove normal traffic is allowed and a deterministic test request is blocked.
- Capture blocked-request telemetry in CloudWatch Logs.
- Normalize WAF events with a Lambda analyzer.
- Persist normalized events in DynamoDB.
- Use Amazon Bedrock for AI-assisted security analysis.
- Correlate recent events with deterministic risk scoring.
- Persist correlation findings in a separate DynamoDB table.
- Separate Lambda permissions by responsibility using least-privilege IAM.
- Validate the deployed system with repeatable commands and evidence.
- Confirm Terraform reports no drift before controlled teardown.

## 2. Custom Badges

Badges may be added if they are used consistently across the complete Lab 12 series. They are not required for the core submission.

## 3. Lab / Task / Project Overview

Lab 12 contains two related paths: a protected application path and a security-analysis path.

![Lab 12 request and security-analysis architecture](../../../../assets/images/members/jacques-payne/phase-1/lab12/architecture/lab-12-waf-bedrock-threat-correlation-architecture.png)

The diagram connects the protected request path and the security-analysis flow described below.

### Protected Application Path

```text
Client
  |
  v
AWS WAF
  |
  v
Amazon API Gateway
  |
  v
Protected API Lambda
```

AWS WAF evaluates requests before API Gateway invokes the protected application Lambda.

A deterministic lab rule blocks requests containing:

```text
x-lab-attack: true
```

Expected behavior:

```text
Normal request                -> HTTP 200
x-lab-attack: true request    -> HTTP 403
```

This test proves that the Web ACL is associated with the API Gateway stage and can block a known request.

### Security-Analysis Path

```text
AWS WAF
  |
  v
CloudWatch Logs
  |
  v
WAF Analyzer Lambda
  |                  \
  v                   v
DynamoDB Events     Amazon Bedrock
  |
  v
Threat Correlation Lambda
  |                  \
  v                   v
DynamoDB Findings  Amazon Bedrock
```

### WAF Analyzer Responsibilities

The analyzer Lambda:

1. Reads recent blocked WAF events from CloudWatch Logs.
2. Normalizes relevant request and WAF attributes.
3. Creates deterministic event identifiers.
4. Stores new events in DynamoDB.
5. Sends new events to Amazon Bedrock for security analysis.
6. Skips events that have already been stored.

### Threat Correlation Responsibilities

The correlation Lambda:

1. Reads recent normalized WAF events from DynamoDB.
2. Groups related events by source and target.
3. Calculates a deterministic risk score.
4. Uses Amazon Bedrock to generate a narrative correlation report.
5. Stores the resulting finding in a separate DynamoDB table.

The default correlation settings used during validation were:

```text
Minimum event count:       3
Correlation window:        60 minutes
Maximum events evaluated:  500
```

### Bedrock Model Boundary

The runtime inference profile used by the Lambda functions is:

```text
us.anthropic.claude-haiku-4-5-20251001-v1:0
```

The `us.` prefix identifies the US cross-Region inference profile.

The Bedrock path enriches security analysis, while event normalization, persistence, and correlation thresholds remain controlled by application logic.

## 4. Lab / Task / Project Requirements

### Required Local Tools

- Terraform
- AWS CLI
- Python 3
- `curl`
- `jq`
- Git

### AWS Services Used

- AWS WAF
- Amazon API Gateway
- AWS Lambda
- Amazon CloudWatch Logs
- Amazon DynamoDB
- Amazon Bedrock
- Amazon EventBridge Scheduler
- AWS IAM

### AWS Access Requirements

The AWS CLI identity used for deployment must have permission to create and validate the resources defined by the Terraform configuration.

First-time use of the configured Bedrock model may also require an account-level AWS Marketplace agreement. Marketplace subscription permissions belong only on an authorized administrative identity during activation and must not be added to the Lambda execution roles.

### Local Configuration

The local Terraform variables file is:

```text
terraform/terraform.tfvars
```

It contains environment-specific values such as:

- AWS Region
- Bedrock inference-profile identifier
- Bedrock resource ARNs
- schedule enablement settings

The validation deployment kept automated schedules disabled:

```hcl
enable_schedules = false
```

This preserved controlled manual testing of the analyzer and correlation functions.

Local generated files such as Terraform state, saved plans, local variable files, generated ZIP archives, and `.terraform/` are not intended for repository submission.

## 5. Project / Folder Structure

```text
lab12/
├── architecture/
│   └── lab-12-waf-bedrock-threat-correlation-architecture.excalidraw
├── runbooks/
│   └── lab-12-waf-bedrock-threat-correlation-runbook.md
├── scripts/
├── src/
│   ├── protected_api_handler.py
│   ├── waf_bedrock_analyzer.py
│   └── waf_threat_correlation_agent.py
├── terraform/
├── test-events/
└── README.md
```

The editable Excalidraw file is the architecture source. The rendered PNG and validation screenshots are stored under `assets/images/members/jacques-payne/phase-1/lab12/` at the repository root.

Terraform files use numeric prefixes to organize the configuration by responsibility:

```text
00-versions.tf
01-provider.tf
02-locals.tf
03-variables.tf
04-data.tf
10-dynamodb.tf
20-cloudwatch.tf
30-iam-lambda.tf
40-lambda-packaging.tf
41-lambda-application.tf
42-lambda-analyzer.tf
43-lambda-correlation.tf
50-api-gateway.tf
60-waf.tf
70-eventbridge-scheduler.tf
90-outputs.tf
```

## 6. Steps Used to Complete This Lab

1. Reviewed the Lab 12 architecture and service dependencies.
2. Configured Terraform providers, variables, locals, and data sources.
3. Added DynamoDB tables for normalized WAF events and correlation findings.
4. Added CloudWatch logging resources.
5. Created separate IAM roles and policies for the Lambda functions.
6. Packaged and deployed the protected API Lambda.
7. Packaged and deployed the WAF analyzer Lambda.
8. Packaged and deployed the threat-correlation Lambda.
9. Created the API Gateway endpoint.
10. Protected the API Gateway stage with AWS WAF.
11. Added EventBridge Scheduler definitions with schedules disabled by default.
12. Validated Terraform formatting and configuration.
13. Created and reviewed a saved Terraform plan.
14. Deployed the infrastructure.
15. Verified both Lambda functions used the intended Bedrock inference profile.
16. Verified both schedules remained disabled.
17. Confirmed a normal API request returned HTTP 200.
18. Confirmed the deterministic WAF test request returned HTTP 403.
19. Verified the blocked request appeared in CloudWatch Logs.
20. Invoked the analyzer and verified new normalized events were stored and analyzed.
21. Generated at least three fresh blocked events for correlation testing.
22. Invoked the correlation Lambda and verified a finding was created.
23. Retrieved the persisted finding from DynamoDB.
24. Corrected DynamoDB numeric serialization for Python float values.
25. Resolved Bedrock model-access and inference-profile issues.
26. Performed final Terraform and Python validation.
27. Confirmed Terraform reported no drift.
28. Reviewed and preserved the evidence set.
29. Created and reviewed a controlled destroy plan.
30. Destroyed the lab environment after validation was complete.

## 7. Artifacts / Screenshots - SHOW YOUR WORK

The `assets/images/members/jacques-payne/phase-1/lab12/evidence/` directory at the repository root preserves the validation screenshots for the completed Lab 12 workflow.

| Evidence | Validation demonstrated |
|---|---|
| [01-terraform-commit-history.png](../../../../assets/images/members/jacques-payne/phase-1/lab12/evidence/01-terraform-commit-history.png) | Incremental Lab 12 implementation history |
| [02-bedrock-model-and-profile-access.png](../../../../assets/images/members/jacques-payne/phase-1/lab12/evidence/02-bedrock-model-and-profile-access.png) | Haiku 4.5 agreement and active inference profile |
| [03-terraform-plan-complete.png](../../../../assets/images/members/jacques-payne/phase-1/lab12/evidence/03-terraform-plan-complete.png) | Initial Terraform deployment plan |
| [04-terraform-apply-complete.png](../../../../assets/images/members/jacques-payne/phase-1/lab12/evidence/04-terraform-apply-complete.png) | Successful infrastructure deployment |
| [05-terraform-state-and-disabled-schedules.png](../../../../assets/images/members/jacques-payne/phase-1/lab12/evidence/05-terraform-state-and-disabled-schedules.png) | Terraform state and disabled schedules |
| [06-api-gateway-allowed-and-waf-blocked.png](../../../../assets/images/members/jacques-payne/phase-1/lab12/evidence/06-api-gateway-allowed-and-waf-blocked.png) | HTTP 200 allowed request and HTTP 403 WAF block |
| [07-waf-blocked-event-log.png](../../../../assets/images/members/jacques-payne/phase-1/lab12/evidence/07-waf-blocked-event-log.png) | Blocked request captured in CloudWatch Logs |
| [08-bedrock-enriched-analyzer-response.png](../../../../assets/images/members/jacques-payne/phase-1/lab12/evidence/08-bedrock-enriched-analyzer-response.png) | Successful WAF analysis with Amazon Bedrock |
| [09-threat-correlation-finding-created.png](../../../../assets/images/members/jacques-payne/phase-1/lab12/evidence/09-threat-correlation-finding-created.png) | Successful correlation finding creation |
| [10-dynamodb-correlation-finding.png](../../../../assets/images/members/jacques-payne/phase-1/lab12/evidence/10-dynamodb-correlation-finding.png) | Correlation finding persisted in DynamoDB |
| [11-terraform-no-drift.png](../../../../assets/images/members/jacques-payne/phase-1/lab12/evidence/11-terraform-no-drift.png) | Configuration, state, and deployed resources aligned |
| `12-terraform-destroy-complete.png` | Controlled Terraform cleanup |

Before publishing evidence, sensitive or account-specific values should be removed or redacted, including:

- personal email addresses
- AWS account IDs
- client or source IP addresses
- API Gateway invoke URLs
- account-specific ARNs
- request IDs and session identifiers
- credentials, tokens, and secrets

## 8. Steps Used to Teardown / Clean Up the Lab

Lab 12 uses a controlled Terraform teardown.

Teardown should occur only after:

1. Functional validation is complete.
2. Evidence has been reviewed.
3. The runbook has been reviewed.
4. Architecture artifacts have been preserved.
5. Terraform reports no drift.
6. The destroy plan has been created and reviewed.

The expected destroy workflow is:

```text
terraform plan -destroy
        |
        v
review planned destruction
        |
        v
terraform apply saved-destroy-plan
        |
        v
terraform state list
        |
        v
confirm no managed resources remain
```

Local generated files that should not be committed include:

```text
terraform.tfstate
terraform.tfstate.backup
terraform.tfvars
*.tfplan
*.zip
.terraform/
```

The reusable Terraform source, Lambda source, test events, runbook, architecture files, and approved evidence are retained.

Historical cleanup excerpts show the final destroy output across two frames. Use the cleanup checks above for your own deployment.

![Terraform cleanup result, first excerpt](../../../../assets/images/members/jacques-payne/phase-1/lab12/evidence/12-terraform-destroy-complete-part-a.png)

![Terraform cleanup result, continuation](../../../../assets/images/members/jacques-payne/phase-1/lab12/evidence/12-terraform-destroy-complete-part-b.png)


## 9. Lessons Learned

### Security Controls Need Direct Validation

It is not enough to create a WAF association in Terraform. The implementation was validated by proving normal traffic returned HTTP 200 while the deterministic test request returned HTTP 403.

### Security Telemetry Should Be Traceable

The test continued beyond the WAF decision into CloudWatch Logs, the analyzer, DynamoDB event storage, threat correlation, and persisted findings. This demonstrated the complete security-analysis chain.

### Deterministic Logic and AI-Assisted Analysis Serve Different Purposes

The system uses deterministic identifiers, correlation thresholds, and risk scoring while using Amazon Bedrock to enrich analysis and produce narrative context.

### Duplicate Handling Matters

The analyzer uses deterministic event identifiers and conditional DynamoDB writes. Previously stored events are treated as duplicates rather than analyzed repeatedly.

### Storage Boundaries Matter

DynamoDB does not accept Python `float` values through Boto3 serialization. Converting floats to `Decimal` immediately before persistence preserved normal application calculations while satisfying the DynamoDB data contract.

### Model Availability Is Not the Same as Runtime Readiness

Bedrock troubleshooting demonstrated that model status, cross-Region inference-profile identifiers, account-level Marketplace agreements, and IAM permissions must all align before successful runtime invocation.

### No-Drift Validation Is Part of Completion

A successful deployment is not the final checkpoint. Terraform was run with detailed exit codes to verify that the deployed environment matched the configuration before cleanup.

## 10. References

- [Amazon Bedrock model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)
- [Amazon Bedrock inference profiles](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles.html)
- [Amazon Bedrock geographic cross-Region inference](https://docs.aws.amazon.com/bedrock/latest/userguide/geographic-cross-region-inference.html)
- [AWS WAF documentation](https://docs.aws.amazon.com/waf/)
- [Amazon API Gateway documentation](https://docs.aws.amazon.com/apigateway/)
- [AWS Lambda documentation](https://docs.aws.amazon.com/lambda/)
- [Amazon CloudWatch Logs documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/)
- [Amazon DynamoDB documentation](https://docs.aws.amazon.com/dynamodb/)
- [Boto3 DynamoDB type serializer](https://boto3.amazonaws.com/v1/documentation/api/latest/_modules/boto3/dynamodb/types.html)
- [Terraform plan command](https://developer.hashicorp.com/terraform/cli/commands/plan)
- Armageddon / SEIR Foundations Lab 12 source material

For detailed deployment, validation, troubleshooting, and teardown commands, see:

```text
runbooks/lab-12-waf-bedrock-threat-correlation-runbook.md
```

## 11. Troubleshooting

### DynamoDB Float Serialization

#### Symptom

The first correlation attempt failed with:

```text
Float types are not supported. Use Decimal types instead.
```

#### Diagnosis

Calculated values in the correlation evidence package contained Python `float` objects, which Boto3 does not accept when serializing DynamoDB items.

#### Resolution

The implementation recursively converts floats to:

```python
Decimal(str(value))
```

immediately before the DynamoDB write.

### Bedrock Legacy-Model Failure

The original Claude 3 Haiku model configuration was no longer suitable for this account.

Resolution:

1. Selected Claude Haiku 4.5.
2. Updated Lambda environment variables.
3. Updated IAM Bedrock resource ARNs.
4. Created and reviewed a Terraform plan.
5. Applied the saved plan.

### Cross-Region Inference Profile

Runtime invocation requires:

```text
us.anthropic.claude-haiku-4-5-20251001-v1:0
```

while some Bedrock model-availability operations use the underlying foundation-model identifier without the `us.` prefix.

The two identifiers serve different Bedrock operations and are not interchangeable.

### AWS Marketplace Agreement

Initial Haiku 4.5 invocation required completion of the account-level AWS Marketplace agreement.

Temporary Marketplace subscription permissions were used only on an authorized administrative identity and were removed after model access was established. Those permissions were not added to Lambda execution roles.

### Duplicate Analyzer Events

Once an event is stored, later analyzer invocations treat the same deterministic event ID as a duplicate.

After correcting a failed Bedrock path, a fresh blocked request must be generated rather than expecting the previously stored event to be reprocessed automatically.

### AWS CLI Pagination and zsh Arithmetic

Paginated AWS CLI text output can return multiple numeric values, which is unsafe for shell arithmetic.

Using JSON output and:

```bash
jq '.events | length'
```

produces one integer after the full response is assembled.

## 12. Author & Contributors

### Author and Group Leader

Jacques Payne

### Armageddon #2 Group

- Jacques Payne
- Joe Tolliver, Jr.
- Cautchy Bailly
- Kirk Alton

### Collaboration Model

Armageddon #2 was completed as a group project with members maintaining individual branches and work areas.

This Lab 12 implementation, evidence set, and documentation represent the work maintained in Jacques Payne's project area.

Phase 1 group submission materials were maintained through Kirk Alton's repository.
