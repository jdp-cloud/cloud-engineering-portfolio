# Lab 12A - Event-Driven SOAR Response

## **Armageddon #2 · SEIR Foundations · Phase 1**

## 1. Lab Purpose and Objectives

Lab 12A extends the Lab 12 WAF analysis and threat-correlation platform with an event-driven Security Orchestration, Automation, and Response (SOAR) workflow.

The SOAR response workflow receives threat-finding events from Amazon EventBridge, retrieves the authoritative finding from DynamoDB, applies a deterministic severity playbook, creates security incidents idempotently, publishes notifications through Amazon SNS, and preserves a human-approval boundary for containment decisions.

### Objectives

- Extend the Lab 12 threat-correlation workflow with event-driven response.
- Route MEDIUM, HIGH, and CRITICAL findings through Amazon EventBridge.
- Retrieve the authoritative finding from DynamoDB before response processing.
- Apply deterministic response playbooks based on severity.
- Create security incidents in DynamoDB.
- Publish standard and CRITICAL notifications through Amazon SNS.
- Prevent duplicate incidents and duplicate response processing.
- Use Amazon Bedrock only for optional informational summaries.
- Preserve explicit human authorization for containment.
- Validate the complete correlation-to-EventBridge-to-SOAR workflow.
- Verify Terraform reports no drift before controlled teardown.

## 2. Custom Badges

No custom badges are required for the core Lab 12A submission.

## 3. Lab / Task / Project Overview

Lab 12A adds an event-driven SOAR response layer to the security-analysis workflow created in Lab 12.

### Architecture

![Lab 12A event-driven SOAR architecture](../../../../assets/images/members/jacques-payne/phase-1/lab12a/architecture/lab-12a-soar-architecture.png)

Editable diagram source:

- [`architecture/lab-12a-soar-architecture.excalidraw`](architecture/lab-12a-soar-architecture.excalidraw)

Primary workflow:

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
    Critical["Critical-alert SNS topic"]
    N0 --> N1
    N1 --> N2
    N2 --> N3
    N3 --> N4
    N4 --> N5
    N5 --> N6
    N7 --> N8
    N8 --> N9
    N9 --> N10
    N6 -->|MEDIUM / HIGH / CRITICAL| N7
    N6 -->|CRITICAL; parallel| Critical
```

The EventBridge event contains routing metadata only. The SOAR Lambda uses the finding ID from the event to retrieve the complete authoritative finding from DynamoDB.

### Deterministic Response Playbooks

| Severity | Automated response |
|---|---|
| LOW | Record only |
| MEDIUM | Notify analyst |
| HIGH | Notify analyst and create an incident |
| CRITICAL | Notify analyst, create an incident, and request urgent human review |

Amazon Bedrock does not determine severity and does not choose the response playbook. Those decisions remain deterministic and auditable.

### Authorization Boundary

Lab 12A is authorized to:

- retrieve and validate existing correlation findings
- update response-processing status
- create security incident records
- publish standard and CRITICAL notifications
- request human review or containment approval
- optionally generate an informational Bedrock summary

Lab 12A is not authorized to:

- block IP addresses automatically
- modify WAF rules automatically
- isolate hosts or workloads
- disable users or credentials
- modify production resources automatically
- perform containment without explicit human approval

Every incident preserves:

```text
human_review_required = true
containment_performed = false
```

### Idempotency Controls

The SOAR workflow uses complementary safeguards to prevent duplicate response processing:

1. Incident IDs use the deterministic format `INC-<finding_id>`.
2. Incident creation uses a conditional DynamoDB write.
3. Completed findings change from `OPEN` to `RESPONSE_COMPLETED`.
4. Replayed events for completed findings are skipped before another incident or notification is created.

### Key AWS Resources

The standalone Terraform configuration includes the Lab 12 baseline and Lab 12A response layer:

- AWS WAF and protected API resources
- CloudWatch log groups
- WAF analyzer Lambda
- threat-correlation Lambda
- SOAR response Lambda
- `waf-events` DynamoDB table
- `waf-correlation-findings` DynamoDB table
- `security-incidents` DynamoDB table
- EventBridge severity routing rules and targets
- standard SOAR notification SNS topic
- CRITICAL alert SNS topic
- least-privilege IAM roles and policies

### SOAR Environment Variables

The SOAR Lambda uses:

```text
CORRELATION_FINDINGS_TABLE
SECURITY_INCIDENTS_TABLE
SNS_TOPIC_ARN
BEDROCK_MODEL_ID
ENABLE_BEDROCK
```

The correlation Lambda requires `events:PutEvents` permission to publish findings to the default EventBridge event bus.

## 4. Lab / Task / Project Requirements

### Required Local Tools

- Terraform
- AWS CLI
- Python 3
- Git

### AWS Services Used

- AWS WAF
- Amazon API Gateway
- AWS Lambda
- Amazon CloudWatch Logs
- Amazon DynamoDB
- Amazon EventBridge
- Amazon SNS
- Amazon Bedrock
- AWS IAM

### Local Configuration

Create the local Terraform variables file from the example:

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

The real `terraform.tfvars` is intentionally excluded from Git.

The SNS subscriber email address is supplied through:

```text
terraform/terraform.tfvars
```

For this lab, Terraform marks the notification email variable as sensitive to reduce routine CLI display. Terraform sensitivity does not encrypt plan or state data.

In production, environment-specific values should be provided through an approved protected mechanism such as a CI/CD secret or variable store, HCP Terraform, AWS Systems Manager Parameter Store, AWS Secrets Manager, or HashiCorp Vault.

### SNS Subscription Requirement

The deployment creates two separate email subscriptions:

1. Standard SOAR incident notifications
2. Immediate CRITICAL alerts

Both AWS SNS confirmation requests must be accepted before email delivery becomes active.

## 5. Project / Folder Structure

```text
lab12a/
├── architecture/
│   └── lab-12a-soar-architecture.excalidraw
├── evidence/
│   ├── README.md
│   └── redactions.example.json
├── runbooks/
│   └── lab-12a-soar-response-runbook.md
├── scripts/
│   └── sanitize-evidence.py
├── src/
├── test-events/
├── terraform/
└── README.md
```

Architecture PNGs and screenshots are stored under `assets/images/members/jacques-payne/phase-1/lab12a/` at the repository root. Editable architecture sources and evidence notes remain in this lab directory.

The primary operational runbook is:

```text
runbooks/lab-12a-soar-response-runbook.md
```

## 6. Steps Used to Complete This Lab

1. Reviewed the completed Lab 12 WAF and threat-correlation workflow.
2. Added the `security-incidents` DynamoDB table.
3. Implemented the SOAR response Lambda.
4. Added deterministic severity-based response playbooks.
5. Added idempotent incident creation and replay protection.
6. Added standard SOAR and CRITICAL SNS notification paths.
7. Added EventBridge severity routing rules and targets.
8. Added `events:PutEvents` permission to the correlation Lambda.
9. Preserved the human-review boundary for containment.
10. Configured optional Bedrock summaries without giving Bedrock response authority.
11. Configured the SNS notification email through local Terraform variables.
12. Validated Terraform formatting and configuration.
13. Validated Python source and JSON test fixtures.
14. Created and reviewed the Terraform deployment plan.
15. Deployed 47 managed resources.
16. Confirmed both SNS subscriptions.
17. Verified EventBridge severity rules and routing targets.
18. Tested the HIGH-severity response workflow.
19. Replayed the same finding and verified idempotent behavior.
20. Tested the CRITICAL urgent-review workflow.
21. Verified CRITICAL findings published to both notification paths.
22. Validated automated correlation-to-EventBridge-to-SOAR execution.
23. Verified Terraform reported no infrastructure drift.
24. Reviewed and preserved evidence.
25. Created and reviewed the 47-resource destroy plan.
26. Destroyed all 47 managed resources.
27. Verified zero managed resources remained in Terraform state.

## 7. Artifacts / Screenshots - SHOW YOUR WORK

Validation screenshots are stored in `assets/images/members/jacques-payne/phase-1/lab12a/evidence/` at the repository root.

| Evidence | Validation demonstrated |
|---|---|
| `01-terraform-plan-complete.png` | Reviewed Terraform plan for 47 additions |
| `02-terraform-apply-complete.png` | Successful deployment of 47 resources |
| `03-sns-subscriptions-confirmed.png` | Both SNS email subscriptions confirmed |
| `04-eventbridge-rules-and-targets.png` | MEDIUM/HIGH and CRITICAL routing targets |
| `05-high-severity-end-to-end-workflow.png` | HIGH finding created an incident and notification |
| `06-idempotent-retry-skipped.png` | Replay skipped with exactly one incident retained |
| `07-critical-soar-workflow.png` | CRITICAL workflow requested urgent human review |
| `08-critical-dual-sns-publication.png` | CRITICAL event published to both SNS destinations |
| `09a-correlation-eventbridge-publication.png` | Correlation Lambda published a HIGH finding to EventBridge |
| `09b-soar-incident-completion.png` | EventBridge invoked SOAR and completed incident processing |
| `10-terraform-no-drift.png` | Deployed infrastructure matched Terraform configuration |
| `11-terraform-destroy-plan.png` | Reviewed destroy plan for 47 removals |
| `12-terraform-destroy-complete.png` | Successful destruction of all 47 resources |
| `13-post-destroy-verification.png` | Zero managed resources remained after teardown |

The local `evidence/README.md` contains evidence-specific context.

### Evidence Sanitization

The local sanitization utility can flatten coordinate-based redactions, re-encode screenshots without original metadata, preserve source images by default, and report SHA-256 hashes.

```bash
python3 scripts/sanitize-evidence.py --help
```

Before publishing screenshots, review and redact account-specific or personal values such as:

- AWS account IDs
- email addresses
- subscription identifiers
- API identifiers
- environment-specific ARNs
- credentials, tokens, and secrets

## 8. Steps Used to Teardown / Clean Up the Lab

Lab 12A uses a reviewed Terraform destroy plan.

The teardown sequence is:

```text
terraform plan -destroy
        |
        v
review 47-resource destroy plan
        |
        v
terraform apply saved destroy plan
        |
        v
verify Terraform state
        |
        v
confirm zero managed resources remain
```

The completed teardown removed all 47 managed resources.

Post-destroy validation confirmed:

```text
Managed resources remaining in Terraform state: 0
No changes. No objects need to be destroyed.
```

Generated deployment files such as Terraform state, saved plans, generated Lambda ZIP files, and the real `terraform.tfvars` are not intended for repository submission.

## 9. Lessons Learned

### Automation Does Not Require Automated Containment

A SOAR workflow can automate routing, incident creation, notifications, and status updates while preserving human approval for high-impact actions.

### Deterministic Response Logic Improves Auditability

Severity and playbook selection remain deterministic. Amazon Bedrock can provide informational summaries, but it does not choose the response action.

### Event Routing Should Carry Only What Is Needed

EventBridge carries routing metadata while the SOAR Lambda retrieves the authoritative finding from DynamoDB. This reduces duplication and keeps one authoritative record.

### Idempotency Is Essential in Event-Driven Systems

Event delivery and retries can occur more than once. Deterministic incident IDs, conditional writes, finding state transitions, and replay checks prevent duplicate incidents and notifications.

### CRITICAL Findings Can Use Multiple Notification Paths

The CRITICAL EventBridge rule routes to the SOAR Lambda and directly to the CRITICAL SNS topic, preserving both workflow processing and immediate notification.

### Sensitive Labels Do Not Encrypt Terraform Data

Marking a Terraform variable as sensitive reduces routine output but does not encrypt state or saved plan files. Those artifacts still require appropriate handling.

### Infrastructure State Should Be Verified Before and After Cleanup

A no-drift plan before teardown and zero-resource state verification after teardown provide evidence that the environment matched configuration before cleanup and was fully removed afterward.

## 10. References

- [Amazon EventBridge documentation](https://docs.aws.amazon.com/eventbridge/)
- [Amazon SNS documentation](https://docs.aws.amazon.com/sns/)
- [AWS Lambda documentation](https://docs.aws.amazon.com/lambda/)
- [Amazon DynamoDB documentation](https://docs.aws.amazon.com/dynamodb/)
- [Amazon Bedrock documentation](https://docs.aws.amazon.com/bedrock/)
- [AWS IAM documentation](https://docs.aws.amazon.com/iam/)
- [Terraform plan command](https://developer.hashicorp.com/terraform/cli/commands/plan)
- Armageddon / SEIR Foundations Lab 12A source material

For detailed deployment, validation, evidence, and teardown procedures, see:

```text
runbooks/lab-12a-soar-response-runbook.md
```

## 11. Troubleshooting

### SNS Email Not Received

The deployment creates two SNS email subscriptions. Each topic sends its own confirmation request.

If email notifications do not arrive:

1. Verify both subscription confirmation links were accepted.
2. Confirm the subscription status in AWS.
3. Confirm the correct SNS topic ARN is configured for the SOAR Lambda.
4. Review CloudWatch logs for publication errors.

### Duplicate Incident Risk

Replaying an already completed finding must not create another incident.

The workflow prevents duplicates through:

```text
INC-<finding_id>
conditional DynamoDB write
OPEN -> RESPONSE_COMPLETED state transition
completed-finding replay check
```

Validation confirmed that replaying the same finding retained exactly one incident.

### EventBridge Routing

If a correlation finding does not reach the SOAR Lambda:

1. Verify the correlation Lambda successfully called `events:PutEvents`.
2. Verify the EventBridge severity rule matches the finding.
3. Verify the expected SOAR target is attached.
4. For CRITICAL findings, verify both the SOAR and CRITICAL SNS targets.
5. Review Lambda and EventBridge logs or metrics for delivery failures.

### Human-Approval Boundary

A CRITICAL finding should request urgent review, not perform containment.

Verify the resulting incident preserves:

```text
human_review_required = true
containment_performed = false
```

If a response path performs a containment action automatically, it violates the Lab 12A authorization boundary and should be corrected before submission.

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

This Lab 12A implementation, evidence set, and documentation represent the work maintained in Jacques Payne's project area.

Phase 1 group submission materials were maintained through Kirk Alton's repository.

## Earlier Architecture Reference

The [earlier reference diagram](../../../../assets/images/members/jacques-payne/phase-1/lab12a/architecture/archived/lab-12a-soar-reference-architecture.png) is retained for comparison with the implementation described above. It is historical, not an additional deployment topology.
