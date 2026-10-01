# Lab 12A: Event-Driven SOAR Response Runbook

## Purpose

Lab 12A extends the Lab 12 WAF analysis and threat-correlation platform with an event-driven Security Orchestration, Automation, and Response workflow.

The SOAR response agent:

1. Receives a threat-finding routing event from EventBridge.
2. Retrieves the authoritative finding from DynamoDB.
3. Verifies that the finding is eligible for processing.
4. Selects a deterministic response playbook.
5. Uses Amazon Bedrock only for informational summaries.
6. Creates a security incident record.
7. Publishes an SNS notification.
8. Updates the original finding to `RESPONSE_COMPLETED`.

## Authorization boundary

Lab 12A does not perform automated containment.

Every incident retains:

```text
human_review_required = true
containment_performed = false
```

CRITICAL findings request urgent human review rather than automatically blocking an address, changing WAF rules, disabling accounts, or modifying production resources.

## Architecture diagram

![Lab 12A SOAR architecture](../../../../../assets/images/members/jacques-payne/phase-1/lab12a/architecture/lab-12a-soar-architecture.png)

The editable source is stored at
`../../lab12a/architecture/lab-12a-soar-architecture.excalidraw`.

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

The EventBridge event contains routing metadata only. The SOAR Lambda uses `detail.finding_id` to retrieve the complete authoritative finding from DynamoDB.

## Deterministic playbooks

| Severity | Response |
|---|---|
| LOW | Record only |
| MEDIUM | Notify analyst |
| HIGH | Notify and create an incident |
| CRITICAL | Notify, create an incident, and request urgent human review |

Amazon Bedrock does not determine severity or choose the playbook. Those decisions remain deterministic and auditable.

## Idempotency controls

The workflow uses complementary safeguards:

1. Incident IDs follow the deterministic format `INC-<finding_id>`.
2. Incident creation uses a conditional DynamoDB write.
3. Completed findings are changed from `OPEN` to `RESPONSE_COMPLETED`.
4. Replayed events for completed findings are skipped before another incident or notification is created.

## Notification email configuration

For this standalone lab, the SNS subscriber address is supplied through:

```text
terraform/terraform.tfvars
```

Example:

```hcl
notification_email = "user@example.com"
```

The real `terraform.tfvars` file is excluded from Git. A reusable placeholder is stored in:

```text
terraform/terraform.tfvars.example
```

The Terraform variable is marked `sensitive = true` to suppress routine CLI display. This does not remove the value from Terraform plans or state data.

An email address is not an authentication secret, but it is personal information and must not be embedded directly in reusable Terraform source files or exposed in screenshots.

In production, environment-specific values would normally be injected through an approved protected mechanism such as a protected CI/CD variable, an HCP Terraform variable set, AWS Systems Manager Parameter Store, AWS Secrets Manager, or HashiCorp Vault.

The ignored local `terraform.tfvars` approach is used because this is an individual lab deployment rather than a shared production pipeline.

## SNS subscriptions

The deployment creates two separate email subscriptions:

1. Standard SOAR incident notifications
2. Immediate CRITICAL alerts

AWS sends a separate confirmation request for each topic. Both confirmation links must be accepted before message delivery becomes active.

![Confirmed SNS email subscriptions](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/03-sns-subscriptions-confirmed.png)

## Deployment evidence

### Terraform plan

The final reviewed plan proposed 47 additions, zero changes, and zero destroys.

![Final Lab 12A Terraform plan](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/01-terraform-plan-complete.png)

### Terraform apply

The saved plan deployed exactly 47 resources.

![Successful Lab 12A Terraform apply](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/02-terraform-apply-complete.png)

### EventBridge routing

The MEDIUM/HIGH rule has one SOAR target. The CRITICAL rule has both the SOAR target and the immediate critical-alert SNS target.

![EventBridge severity rules and targets](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/04-eventbridge-rules-and-targets.png)

## Operational validation

### HIGH-severity workflow

A synthetic HIGH finding selected `CREATE_AND_ESCALATE_INCIDENT`, created a priority-2 incident, published an SNS notification, and updated the finding to `RESPONSE_COMPLETED`.

![HIGH-severity end-to-end workflow](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/05-high-severity-end-to-end-workflow.png)

### Idempotent retry

Replaying the same finding after completion returned an already-processed result. Exactly one incident remained associated with the finding.

![Idempotent retry skipped](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/06-idempotent-retry-skipped.png)

### CRITICAL workflow

A synthetic CRITICAL finding selected `REQUEST_URGENT_REVIEW`, created a priority-1 incident, and preserved the human-approval boundary.

![CRITICAL SOAR workflow](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/07-critical-soar-workflow.png)

CloudWatch SNS metrics confirmed that the CRITICAL event produced one message on each routing destination.

![CRITICAL dual SNS publication](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/08-critical-dual-sns-publication.png)

### Automated correlation-to-SOAR workflow

Part A proves that three normalized WAF events were correlated into a HIGH finding with risk score 60 and that the correlation Lambda successfully called EventBridge `PutEvents`.

![Correlation finding published to EventBridge](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/09a-correlation-eventbridge-publication.png)

Part B proves that EventBridge invoked the SOAR Lambda automatically, which created the incident, published the notification, and updated the finding to `RESPONSE_COMPLETED`.

![SOAR incident completion](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/09b-soar-incident-completion.png)

### Terraform no-drift check

After operational testing, Terraform reported that the deployed infrastructure still matched the configuration.

![Terraform no-drift validation](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/10-terraform-no-drift.png)

## Security and privacy notes

- The EventBridge event contains routing metadata only.
- The SOAR Lambda retrieves the authoritative finding from DynamoDB.
- IAM permissions are scoped to the required tables, topics, log groups, Bedrock resources, and the default EventBridge bus.
- Test source addresses use documentation-only IP ranges.
- Screenshots intentionally retain the personal repository and branch identity as submission attribution.
- AWS account IDs, email addresses, subscription identifiers, API identifiers, and environment-specific ARNs are redacted.
- Screenshot redactions must be flattened before committing evidence.

## Cleanup

Do not destroy the deployment until all documentation, architecture artifacts, repository validation, and evidence checks are complete.

The final cleanup will use a reviewed Terraform destroy plan, followed by destroy evidence and post-destroy verification.

## Teardown and post-destroy verification

A reviewed destroy plan proposed exactly 47 removals with no additions or
changes.

![Reviewed Terraform destroy plan](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/11-terraform-destroy-plan.png)

The saved destroy plan removed all 47 managed resources.

![Terraform destroy completed](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/12-terraform-destroy-complete.png)

Post-destroy verification confirmed that Terraform state contained zero
managed resources and that no objects remained to destroy.

![Post-destroy verification](../../../../../assets/images/members/jacques-payne/phase-1/lab12b/evidence/13-post-destroy-verification.png)
