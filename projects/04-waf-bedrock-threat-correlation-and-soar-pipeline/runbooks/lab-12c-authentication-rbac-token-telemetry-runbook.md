# Lab 12C: Authentication, RBAC, and Token-Use Telemetry Runbook

## **Armageddon #2 · SEIR Foundations · Phase 2**

## 1. Purpose

This runbook documents a post-submission security enhancement to the Armageddon #2 Lab 12C environment.

The original Lab 12C implementation introduced the Compliance Evidence Agent and completed its original validation and teardown workflow. This enhancement preserves that implementation and extends the existing protected API with additional identity, authorization, and security-telemetry controls.

The enhancement adds:

- Amazon Cognito user authentication
- TOTP multifactor authentication
- Cognito group-based role-based access control
- API Gateway Cognito authorization
- Lambda application-level RBAC
- DynamoDB token-use telemetry
- token ownership verification
- an unused-token detector Lambda
- EventBridge Scheduler integration
- CloudWatch logging for token-use alerts

The implementation branch is:

```text
member/jacques-payne/cognito-rbac-unused-token
```

This work extends Lab 12C rather than replacing or redesigning the original security architecture.

---

## 2. Security Objectives

The enhancement separates three security responsibilities:

```text
Authentication
    |
    | Who is the caller?
    v
Amazon Cognito
    |
    v
Authorization
    |
    | May this caller perform this operation?
    v
Lambda RBAC
    |
    v
Token-use telemetry
    |
    | Was the issued token/session identifier actually used?
    v
DynamoDB + Unused Token Detector
```

The intended authorization matrix is:

| Request | Expected Result | Enforcement Point |
|---|---:|---|
| No valid Cognito token | `401` | API Gateway / Cognito |
| Authenticated `security-viewers` user | `403` | Protected Lambda |
| Authenticated `security-analysts` user | `200` | Protected Lambda |
| Authenticated `security-admins` user | `200` | Protected Lambda |

This distinction is intentional:

```text
401 = authentication failed or missing
403 = authentication succeeded, authorization denied
```

---

## 3. Architecture

```mermaid
flowchart TD
    Cognito["Amazon Cognito<br/>User pool + MFA + groups"]
    Authorizer["API Gateway Cognito authorizer"]
    Lambda["Protected Lambda"]
    RBAC["RBAC: cognito:groups"]
    Telemetry["Token telemetry: x-token-id"]
    DDB["DynamoDB token-tracking<br/>used = true / false"]
    Detector["Unused Token Detector"]
    Logs["CloudWatch Logs"]
    Client["Client"]
    WAF["AWS WAF"]
    API["API Gateway"]
    Scheduler["EventBridge Scheduler"]
    Cognito -->|JWT| Authorizer
    Authorizer --> Lambda
    Lambda --> RBAC
    Lambda --> Telemetry
    Telemetry --> DDB
    Detector --> Logs
    RBAC --> Logs
    Client --> WAF
    WAF --> API
    API --> Authorizer
    DDB --> Scheduler
    Scheduler --> Detector
```

The existing Lab 12C architecture remains available beneath this enhancement:

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
    N9["Executive Dashboard Lambda"]
    N10["Amazon S3 executive-reports/"]
    N11["Compliance Agent"]
    API["API Gateway"]
    Lambda["Protected Lambda"]
    Evidence["DynamoDB compliance-evidence"]
    Reports["Amazon S3 compliance-reports/"]
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
    N10 --> N11
    N0 --> API
    API --> Lambda
    N11 --> Evidence
    Evidence --> Reports
```

---

## 4. Enhancement Scope

The authentication, RBAC, and token-use controls are implemented within:

```text
phase-2/lab12c/
```

Primary files include:

```text
lab12c/
├── src/
│   ├── protected_api_handler.py
│   └── unused_token_detector.py
│
├── terraform/
│   ├── 30-iam-lambda.tf
│   ├── 41-lambda-application.tf
│   ├── 50-api-gateway.tf
│   ├── lab12c-auth-cognito.tf
│   ├── lab12c-auth-detector.tf
│   ├── lab12c-auth-outputs.tf
│   └── lab12c-auth-token-tracking.tf
│
└── runbooks/
    ├── lab-12c-compliance-evidence-runbook.md
    └── lab-12c-authentication-rbac-token-telemetry-runbook.md
```

Lab 12D remains separate from this enhancement.

---

## 5. Amazon Cognito Authentication

### 5.1 User Pool

The Cognito user pool provides identity management for the protected API.

The deployed configuration was validated with:

```text
MFA: ON
```

The user pool includes:

```text
TOTP software-token MFA: enabled
Administrative user creation: required
Public self-registration: disabled
Case-sensitive usernames: disabled
```

### 5.2 Password Policy

The Cognito password policy requires:

```text
Minimum length: 12
Lowercase character: required
Uppercase character: required
Number: required
Symbol: required
Temporary password validity: 1 day
```

### 5.3 Application Client

The Cognito application client is configured with:

```text
Client secret: disabled
USER_PASSWORD_AUTH: enabled
Refresh-token authentication: enabled
Token revocation: enabled
Access-token validity: 1 hour
ID-token validity: 1 hour
Refresh-token validity: 1 day
```

The client deliberately uses:

```hcl
generate_secret = false
```

This avoids the `SECRET_HASH` workflow used in earlier coursework and simplifies controlled command-line authentication.

No Cognito passwords, MFA codes, TOTP setup secrets, access tokens, ID tokens, or refresh tokens are stored in Terraform or repository evidence.

---

## 6. API Gateway Cognito Authorization

The existing `/analyze` method originally used:

```hcl
authorization = "NONE"
```

The enhancement changes the method to:

```hcl
authorization = "COGNITO_USER_POOLS"
authorizer_id = aws_api_gateway_authorizer.cognito.id
```

The authorizer uses:

```text
Authorization
```

as the identity-source header.

The deployment trigger also includes the Cognito authorizer so changes to authentication configuration cause API Gateway redeployment.

### Expected Behavior

A request without a valid Cognito credential should be rejected before Lambda invocation:

```text
No valid token
    |
    v
API Gateway Cognito Authorizer
    |
    v
HTTP 401
```

The protected Lambda is responsible for application authorization after authentication succeeds.

---

## 7. Cognito RBAC Groups

Three Cognito groups provide the role model:

| Group | Precedence | Purpose |
|---|---:|---|
| `security-admins` | 10 | Elevated security administration |
| `security-analysts` | 20 | Security analysis operations |
| `security-viewers` | 30 | Authenticated read-only identity |

Group membership is available to the protected Lambda through:

```text
cognito:groups
```

The protected Lambda follows a default-deny model.

The allowed groups are:

```python
ALLOWED_GROUPS = {
    "security-analysts",
    "security-admins",
}
```

Users belonging only to:

```text
security-viewers
```

are authenticated successfully but are not authorized to execute the protected analysis operation.

Expected result:

```text
HTTP 403
```

---

## 8. Local RBAC Validation

The Lambda authorization logic was tested locally before AWS deployment.

Validated results:

```text
viewer   -> 403
analyst  -> 200
admin    -> 200
```

This demonstrates the difference between identity authentication and application authorization.

---

## 9. Token-Use Telemetry

### 9.1 Purpose

The token-use telemetry layer records whether an issued authentication session identifier is subsequently used to call the protected API.

This control is not intended to replace Cognito JWT validation.

It is also not a JWT-expiration detector.

The control detects an issued token-tracking record that remains unused beyond an expected period.

### 9.2 DynamoDB Table

The deployed token-use table is:

```text
armageddon2-lab12-dev-token-tracking
```

The partition key is:

```text
token_id
```

Billing mode:

```text
PAY_PER_REQUEST
```

Point-in-time recovery follows the existing Lab 12C configuration:

```text
var.enable_point_in_time_recovery
```

### 9.3 Token Record Model

A newly issued tracking record follows this model:

```json
{
  "token_id": "<unique identifier>",
  "username": "<authenticated username>",
  "issued_at": "<UTC ISO-8601 timestamp>",
  "used": false
}
```

After a successful API request:

```json
{
  "used": true,
  "used_at": "<UTC ISO-8601 timestamp>"
}
```

---

## 10. Token Ownership Validation

The protected Lambda accepts a token-tracking identifier through:

```text
x-token-id
```

The header is not trusted on its own.

The application validates:

```text
token record exists
AND
token record username == authenticated Cognito username
```

Only then may the Lambda mark the record:

```text
used = true
```

The DynamoDB update also includes a condition expression:

```text
attribute_exists(token_id)
AND
username = authenticated username
```

This provides a second ownership check at the database operation.

A nonexistent or mismatched token identifier results in:

```text
HTTP 403
```

---

## 11. Protected Lambda IAM

The protected API Lambda receives only the DynamoDB permissions required for token-use verification.

Allowed actions:

```text
dynamodb:GetItem
dynamodb:UpdateItem
```

Resource scope:

```text
token-tracking table only
```

The protected application does not receive:

```text
dynamodb:Scan
dynamodb:DeleteItem
broad DynamoDB permissions
```

The table name is passed through the Lambda environment:

```text
TOKEN_TABLE_NAME
```

This preserves least privilege and keeps environment-specific resource names outside application code.

---

## 12. Local Token-Telemetry Validation

The protected Lambda token-telemetry behavior was tested locally with the DynamoDB operation isolated.

Validated results:

```text
viewer         -> 403
analyst-no-id  -> 400
analyst-valid  -> 200
admin-valid    -> 200
wrong-owner    -> 403
```

The results verify:

```text
Unauthorized role           -> 403
Missing x-token-id          -> 400
Authorized valid owner      -> 200
Administrator valid owner   -> 200
Wrong token owner           -> 403
```

---

## 13. Unused Token Detector

### 13.1 Purpose

The detector identifies token-tracking records that satisfy both conditions:

```text
used == false
AND
token age > configured threshold
```

The detector does not treat every old record as suspicious.

A token that has already been marked:

```text
used = true
```

does not produce an unused-token alert.

### 13.2 Lambda Configuration

The deployed detector configuration is:

```text
Function:
armageddon2-lab12-dev-unused-token-detector

Runtime:
python3.12

Handler:
unused_token_detector.lambda_handler

Memory:
128 MB

Timeout:
30 seconds

Threshold:
10 minutes
```

Environment variables:

```text
TOKEN_TABLE_NAME
ALERT_AFTER_MINUTES
```

Current threshold:

```text
ALERT_AFTER_MINUTES=10
```

### 13.3 Detector IAM

The detector requires:

```text
dynamodb:Scan
```

against only:

```text
armageddon2-lab12-dev-token-tracking
```

It also receives CloudWatch Logs write permissions.

The detector does not receive:

```text
dynamodb:PutItem
dynamodb:UpdateItem
dynamodb:DeleteItem
```

The detector is observational.

---

## 14. Detector Logic Validation

The stale-unused decision function was tested independently from AWS.

Test conditions:

```text
unused token, age 15 minutes
unused token, age 5 minutes
used token, age 20 minutes
```

Validated results:

```text
unused-15m   -> True
unused-5m    -> False
used-20m     -> False
```

With a 10-minute threshold:

```text
unused AND older than 10 minutes -> alert candidate
```

A used token does not become an alert merely because it is old.

---

## 15. Structured Detector Alerts

The detector emits structured JSON to CloudWatch Logs.

Alert type:

```text
UNUSED_TOKEN
```

An alert contains information such as:

```json
{
  "level": "ALERT",
  "alert_type": "UNUSED_TOKEN",
  "token_id": "<token identifier>",
  "username": "<username>",
  "issued_at": "<UTC timestamp>",
  "age_minutes": 15,
  "threshold_minutes": 10
}
```

Malformed timestamps are handled independently and do not terminate the entire scan.

The detector also supports DynamoDB scan pagination through:

```text
LastEvaluatedKey
```

---

## 16. EventBridge Scheduler

The detector uses the existing Lab 12C EventBridge Scheduler framework.

Schedule name:

```text
armageddon2-lab12-dev-unused-token-check
```

Schedule expression:

```text
rate(5 minutes)
```

Timezone:

```text
UTC
```

Schedule group:

```text
armageddon2-lab12-dev-schedules
```

The existing scheduler IAM role was extended so it can invoke:

```text
WAF analyzer Lambda
Threat correlation Lambda
Unused-token detector Lambda
```

The unused-token detector supports retries because its operation is read-only.

Retry configuration:

```text
Maximum event age: 3600 seconds
Maximum retry attempts: 2
```

During controlled validation:

```text
State: DISABLED
```

This is intentional.

The detector will be manually tested before automatic recurring execution is enabled.

---

## 17. Terraform Validation

Terraform formatting and validation were performed after each implementation stage.

Repeated validation result:

```text
Success! The configuration is valid.
```

An initial authentication-only plan showed:

```text
Plan: 66 to add, 0 to change, 0 to destroy.
```

The Terraform state was checked with:

```bash
terraform -chdir=terraform state list
```

The state was empty, confirming that the original Lab 12C infrastructure had previously been destroyed.

Therefore, the complete Lab 12C environment was expected to appear as new resource creation.

---

## 18. Final Terraform Plan

After completing authentication, RBAC, token telemetry, detector, scheduler, and outputs, the reviewed plan reported:

```text
Plan: 75 to add, 0 to change, 0 to destroy.
```

The plan explicitly included:

```text
Amazon Cognito user pool
Cognito application client
Cognito user groups
API Gateway Cognito authorizer
token-tracking DynamoDB table
protected Lambda DynamoDB permissions
unused-token detector Lambda
detector IAM policy
detector CloudWatch log group
unused-token EventBridge schedule
```

There were:

```text
0 resources to destroy
```

The reviewed plan was saved outside the repository:

```text
/tmp/lab12c-def-final.plan
```

This prevents Terraform plan artifacts from being accidentally committed to Git.

---

## 19. Deployment

The final reviewed plan was applied directly:

```bash
terraform -chdir=terraform apply \
  /tmp/lab12c-def-final.plan
```

Deployment result:

```text
Apply complete! Resources: 75 added, 0 changed, 0 destroyed.
```

This recreated the complete Lab 12C environment and added the D/E/F security enhancements.

---

## 20. Post-Deployment Infrastructure Validation

### 20.1 Cognito

Validated:

```text
User pool:
armageddon2-lab12-dev-user-pool

MFA:
ON
```

Validated groups:

```text
security-admins     precedence 10
security-analysts   precedence 20
security-viewers    precedence 30
```

### 20.2 API Gateway

Validated method authorization:

```text
authorization = COGNITO_USER_POOLS
```

A deployed Cognito authorizer ID is attached to the `/analyze` method.

### 20.3 DynamoDB

Validated token-tracking table:

```text
Name:
armageddon2-lab12-dev-token-tracking

Status:
ACTIVE

Partition key:
token_id

Key type:
HASH
```

### 20.4 Detector Lambda

Validated:

```text
Runtime:
python3.12

Handler:
unused_token_detector.lambda_handler

Timeout:
30

Memory:
128

ALERT_AFTER_MINUTES:
10

TOKEN_TABLE_NAME:
armageddon2-lab12-dev-token-tracking
```

### 20.5 Scheduler

Validated:

```text
Name:
armageddon2-lab12-dev-unused-token-check

Expression:
rate(5 minutes)

State:
DISABLED
```

The schedule target is the deployed unused-token detector Lambda.

---

## 21. Live Authorization Validation

AWS-side end-to-end identity testing was performed after infrastructure validation.

### Test 1: No Cognito Token

Validated result:

```text
HTTP 401
{"message":"Unauthorized"}
```

Status:

```text
PASS
```

This confirms that API Gateway and the Cognito authorizer reject unauthenticated requests before the protected Lambda is invoked.

### Test 2: Security Viewer

The authenticated `lab12c-viewer` user belonged to:

```text
security-viewers
```

Validated result:

```text
HTTP 403
```

Status:

```text
PASS
```

### Test 3: Security Analyst

The authenticated `lab12c-analyst` user belonged to:

```text
security-analysts
```

Validated result:

```text
HTTP 200
```

The response identified:

```text
username: lab12c-analyst
groups: security-analysts
```

Status:

```text
PASS
```

### Test 4: Security Administrator

The authenticated `lab12c-admin` user belonged to:

```text
security-admins
```

Validated result:

```text
HTTP 200
```

The response identified:

```text
username: lab12c-admin
groups: security-admins
```

Status:

```text
PASS
```

## 22. Live Token-Telemetry Validation

The deployed token-use telemetry controls were validated against the live Cognito, API Gateway, Lambda, and DynamoDB environment.

| Test | Validated Result | Status |
|---|---|---|
| Missing `x-token-id` | HTTP `400` | PASS |
| Valid analyst-owned token ID | HTTP `200` | PASS |
| Valid admin-owned token ID | HTTP `200` | PASS |
| Wrong-owner token ID | HTTP `403` | PASS |
| Token initially recorded | `used=false` | PASS |
| Successful API call | `used=true` | PASS |
| Successful API call | `used_at` populated | PASS |
| Old unused token | `UNUSED_TOKEN` alert | PASS |
| Detector CloudWatch alert | Present | PASS |

The analyst and administrator token-tracking records both transitioned from `used=false` to `used=true` after successful protected API calls. Each successful update also populated `used_at`.

The wrong-owner test authenticated as `lab12c-analyst` while presenting a token-tracking record owned by `lab12c-viewer`.

Validated result:

```text
HTTP 403
```

This confirms that the application correlates the client-supplied `x-token-id` with the trusted Cognito identity before updating token-use telemetry.

## 23. Live Detector Validation

The deployed unused-token detector was validated manually against the live DynamoDB token-tracking table.

The controlled test used an existing token record with:

```text
username: lab12c-viewer
used: false
```

At detector invocation time, the record was:

```text
age_minutes: 15
threshold_minutes: 10
```

The deployed Lambda returned:

```text
alert_count: 1
alert_type: UNUSED_TOKEN
username: lab12c-viewer
```

CloudWatch Logs also recorded:

```text
level: ALERT
alert_type: UNUSED_TOKEN
```

followed by:

```text
event: UNUSED_TOKEN_SCAN_COMPLETE
alert_count: 1
```

This validates the end-to-end detection path:

```mermaid
flowchart TD
    N0["DynamoDB unused token record"] --> N1
    N1["Unused Token Detector Lambda"] --> N2
    N2["UNUSED_TOKEN alert"] --> N3
    N3["CloudWatch Logs"]
```

The recurring EventBridge schedule remained disabled during controlled testing.

Status:

```text
VALIDATED
```

## 24. Evidence Plan

Authentication/RBAC/token-telemetry evidence uses a separate sequence from the original Lab 12C compliance evidence.

Captured evidence filenames under `assets/images/members/jacques-payne/phase-2/lab12c/evidence/` at the repository root:

```text
lab12c-25-auth-10-no-token-401.png
lab12c-26-auth-11-viewer-user-rbac-verify.png
lab12c-27-auth-12-viewer-mfa-setup-challenge.png
lab12c-28-auth-13-viewer-mfa-enrollment-complete.png
lab12c-29-auth-14-viewer-rbac-403.png
lab12c-30-auth-15-analyst-user-rbac-verify.png
lab12c-31-auth-16-analyst-mfa-enrollment-complete.png
lab12c-32-auth-17-analyst-missing-token-id-400.png
lab12c-33-auth-18-analyst-api-200.png
lab12c-34-auth-19-analyst-token-marked-used.png
lab12c-35-auth-20-wrong-owner-403.png
lab12c-36-auth-21-admin-user-rbac-verify.png
lab12c-37-auth-22-admin-mfa-enrollment-complete.png
lab12c-38-auth-23-admin-api-200.png
lab12c-39-auth-24-admin-token-marked-used.png
lab12c-40-auth-25-unused-token-detector-alert.png
lab12c-41-auth-26-cloudwatch-unused-token-alert.png
lab12c-42-auth-27-terraform-no-drift.png
lab12c-43-auth-28-destroy-plan.png
lab12c-44-auth-29-destroy-complete.png
lab12c-45-auth-30-post-destroy-state-empty.png
lab12c-46-auth-31-post-destroy-aws-verify.png
```

Evidence must not contain:

```text
Passwords
Temporary passwords
MFA codes
TOTP secrets
TOTP QR codes
Access tokens
ID tokens
Refresh tokens
Client secrets
AWS secret access keys
```

Environment-specific identifiers should be sanitized where appropriate before repository submission.

---

## 25. Security Design Principles

This enhancement demonstrates several security engineering principles.

### Defense in Depth

The request path now includes:

```text
AWS WAF
Cognito authentication
API Gateway authorization
Lambda RBAC
Token ownership verification
Security telemetry
Scheduled detection
CloudWatch logging
```

No single control is expected to provide complete protection.

### Least Privilege

The protected Lambda receives only:

```text
dynamodb:GetItem
dynamodb:UpdateItem
```

for token-use records.

The detector receives only:

```text
dynamodb:Scan
```

for token telemetry.

The scheduler role receives only the Lambda invocation rights required for scheduled functions.

### Default Deny

Application RBAC allows only explicitly approved groups:

```text
security-analysts
security-admins
```

All other authenticated group combinations are denied.

### Authentication and Authorization Are Separate

Cognito answers:

```text
Who are you?
```

The Lambda answers:

```text
Are you permitted to perform this operation?
```

### Client-Supplied Identifiers Are Not Trusted

The `x-token-id` value is validated against the authenticated Cognito username before it can modify telemetry state.

### Detection Is Separate From Prevention

The unused-token detector observes potentially anomalous token-use behavior without modifying or deleting authentication records.

---

## 26. Operational Commands

Commands in this section assume the current working directory is:

```text
members/jacques-payne/phase-2/lab12c
```

### Terraform Validation

```bash
terraform -chdir=terraform fmt -recursive
terraform -chdir=terraform validate
```

### Terraform State

```bash
terraform -chdir=terraform state list
```

### Authentication Outputs

```bash
terraform -chdir=terraform output \
  cognito_user_pool_id

terraform -chdir=terraform output \
  cognito_user_pool_client_id

terraform -chdir=terraform output \
  token_tracking_table_name

terraform -chdir=terraform output \
  unused_token_detector_lambda_name

terraform -chdir=terraform output \
  unused_token_check_schedule_name
```

### Cognito User Pool Validation

```bash
POOL_ID=$(terraform -chdir=terraform output -raw cognito_user_pool_id)

aws cognito-idp describe-user-pool \
  --user-pool-id "$POOL_ID" \
  --region us-east-1 \
  --query 'UserPool.{Name:Name,MFA:MfaConfiguration}' \
  --output table \
  --no-cli-pager
```

### Cognito Group Validation

```bash
aws cognito-idp list-groups \
  --user-pool-id "$POOL_ID" \
  --region us-east-1 \
  --query 'Groups[].{Group:GroupName,Precedence:Precedence}' \
  --output table \
  --no-cli-pager
```

### API Gateway Authorization Validation

```bash
terraform -chdir=terraform state show \
  aws_api_gateway_method.analyze_get \
  | grep -E 'authorization|authorizer_id'
```

### Token Table Validation

```bash
TABLE_NAME=$(terraform -chdir=terraform output -raw token_tracking_table_name)

aws dynamodb describe-table \
  --table-name "$TABLE_NAME" \
  --region us-east-1 \
  --query 'Table.{Name:TableName,Status:TableStatus,KeySchema:KeySchema}' \
  --output json \
  --no-cli-pager
```

### Detector Validation

```bash
DETECTOR=$(terraform -chdir=terraform output -raw unused_token_detector_lambda_name)

aws lambda get-function-configuration \
  --function-name "$DETECTOR" \
  --region us-east-1 \
  --query '{Function:FunctionName,Runtime:Runtime,Handler:Handler,Timeout:Timeout,Memory:MemorySize,Environment:Environment.Variables}' \
  --output json \
  --no-cli-pager
```

### Scheduler Validation

```bash
SCHEDULE=$(terraform -chdir=terraform output -raw unused_token_check_schedule_name)
GROUP=$(terraform -chdir=terraform output -raw scheduler_schedule_group_name)

aws scheduler get-schedule \
  --name "$SCHEDULE" \
  --group-name "$GROUP" \
  --region us-east-1 \
  --query '{Name:Name,State:State,Expression:ScheduleExpression,Target:Target.Arn}' \
  --output json \
  --no-cli-pager
```

---

## 27. Final No-Drift Validation

After all live tests are complete, run:

```bash
terraform -chdir=terraform plan
```

Expected result:

```text
No changes.
Your infrastructure matches the configuration.
```

This final check should be captured as evidence before teardown.

Status:

```text
VALIDATED
```

---

## 28. Teardown

Teardown was performed only after authentication, RBAC, token-use telemetry, unused-token detection, CloudWatch observability, evidence capture, and final no-drift validation were complete.

### Reviewed Destroy Plan

A saved Terraform destroy plan was created and reviewed before any destructive action was taken.

Validated destroy-plan summary:

```text
Plan: 0 to add, 0 to change, 75 to destroy.
```

A JSON inspection of the saved plan independently confirmed:

```text
Resources marked for destroy: 75
```

Evidence:

```text
assets/images/members/jacques-payne/phase-2/lab12c/evidence/lab12c-43-auth-28-destroy-plan.png
```

### Destroy Execution

The reviewed saved destroy plan was applied.

Validated result:

```text
Destroy complete! Resources: 75 destroyed.
```

Evidence:

```text
assets/images/members/jacques-payne/phase-2/lab12c/evidence/lab12c-44-auth-29-destroy-complete.png
```

### Post-Destroy Terraform State

Terraform state was inspected after teardown.

Validated result:

```text
STATE COUNT
0
```

This confirms that no Lab 12C resources remained in Terraform state.

Evidence:

```text
assets/images/members/jacques-payne/phase-2/lab12c/evidence/lab12c-45-auth-30-post-destroy-state-empty.png
```

### AWS-Side Cleanup Verification

AWS was independently queried after Terraform teardown.

The following Lab 12C resources were verified absent:

```text
Cognito user pool
token-tracking DynamoDB table
unused-token detector Lambda
EventBridge Scheduler schedule group
Lab 12 API Gateway
Lab 12 report bucket
```

Each AWS query returned no matching resource.

Evidence:

```text
assets/images/members/jacques-payne/phase-2/lab12c/evidence/lab12c-46-auth-31-post-destroy-aws-verify.png
```

The teardown lifecycle is therefore:

```mermaid
flowchart TD
    N0["Reviewed destroy plan"] --> N1
    N1["75 managed resources destroyed"] --> N2
    N2["Terraform state count = 0"] --> N3
    N3["AWS-side resources independently verified absent"]
```

Status:

```text
COMPLETE
```

## 29. Troubleshooting Notes

### Terraform Planned the Entire Environment

During the initial Cognito plan, Terraform reported a large number of resource creates.

The state was inspected:

```bash
terraform -chdir=terraform state list
```

No resources were returned.

This confirmed that the earlier Lab 12C environment had already been destroyed and Terraform was correctly planning to recreate the complete environment.

### Terraform Plan Files Appeared in Git Status

An early saved plan was created inside:

```text
terraform/
```

and appeared as an untracked file.

The plan was removed and subsequent saved plans were written to:

```text
/tmp/
```

This keeps generated Terraform plan files outside the repository.

### Protected Lambda Baseline Guard Failed

A guarded Python source replacement initially stopped because the actual `protected_api_handler.py` formatting did not match the expected baseline text.

The guard prevented an unintended overwrite.

The source file was inspected directly before continuing.

This reinforced the troubleshooting principle:

```text
Never guess.
Inspect the actual file.
Then modify.
```

### Local RBAC Test Initially Returned 200 for Every User

The initial test produced:

```text
viewer   -> 200
analyst  -> 200
admin    -> 200
```

Inspection showed that the RBAC version of the Lambda handler had not actually been written to disk.

After writing and verifying the updated handler, the correct results were:

```text
viewer   -> 403
analyst  -> 200
admin    -> 200
```

---

## 30. Lessons Learned

### Identity Should Be Added Before Application Authorization

RBAC is meaningful only after the application has a trustworthy authenticated identity.

The resulting sequence is:

```mermaid
flowchart TD
    N0["Authenticate"] --> N1
    N1["Authorize"] --> N2
    N2["Record security telemetry"] --> N3
    N3["Detect anomalous behavior"]
```

### Authentication and Authorization Should Not Be Conflated

A user may be authenticated successfully and still lack permission to perform an operation.

The `401` versus `403` distinction makes this boundary observable.

### Group Names Should Express Operational Responsibility

The security group names:

```text
security-viewers
security-analysts
security-admins
```

describe application responsibilities rather than classroom roles.

### Client Input Must Be Correlated With Trusted Identity

Possession of an `x-token-id` value alone is insufficient.

The value must correspond to the authenticated Cognito username.

### Security Detection Should Be Observable

The unused-token detector emits structured events suitable for CloudWatch Logs analysis and future alerting integrations.

### Automation Should Follow Manual Validation

The detector schedule remains disabled until the detector has been manually proven against controlled telemetry.

### Infrastructure as Code Makes Security Controls Reviewable

The Cognito configuration, group definitions, IAM permissions, DynamoDB telemetry, Lambda detector, and scheduler are all expressed in Terraform.

This allows:

```text
format
validate
plan
review
apply
verify
```

before infrastructure changes occur.

---

## 31. Current Status

### Infrastructure Lifecycle

```text
COMPLETE
```

### Deployment

```text
75 added
0 changed
0 destroyed
VALIDATED
```

### Cognito Infrastructure

```text
VALIDATED
```

### Cognito MFA

```text
VALIDATED
```

### Cognito Groups

```text
VALIDATED
```

### API Gateway Cognito Authorization

```text
VALIDATED
```

### Live Unauthenticated Request

```text
401 PASS
```

### Live Viewer RBAC

```text
403 PASS
```

### Live Analyst RBAC

```text
200 PASS
```

### Live Administrator RBAC

```text
200 PASS
```

### Missing Token Identifier Guard

```text
400 PASS
```

### Token Ownership Validation

```text
403 PASS
```

### DynamoDB Token Tracking

```text
VALIDATED
```

### Token State Transition

```text
used=false -> used=true
VALIDATED
```

### Protected Lambda Local RBAC

```text
VALIDATED
```

### Protected Lambda Local Token Telemetry

```text
VALIDATED
```

### Unused Token Detector Local Logic

```text
VALIDATED
```

### Live Unused-Token Detection

```text
VALIDATED
```

### CloudWatch Unused-Token Alert

```text
VALIDATED
```

### Detector Lambda Infrastructure

```text
VALIDATED
```

### EventBridge Scheduler Infrastructure

```text
VALIDATED DURING TESTING
```

### Final Terraform No-Drift Validation

```text
VALIDATED
```

### Teardown

```text
75 resources destroyed
COMPLETE
```

### Post-Destroy Terraform State

```text
0 resources
VALIDATED
```

### AWS Post-Destroy Verification

```text
Cognito user pool: absent
Token-tracking DynamoDB table: absent
Unused-token detector Lambda: absent
EventBridge Scheduler schedule group: absent
Lab 12 API Gateway: absent
Lab 12 report bucket: absent
VALIDATED
```

### Final Status

```text
COMPLETE
```

## 32. References

- Amazon Cognito documentation
- Amazon API Gateway documentation
- AWS Lambda documentation
- Amazon DynamoDB documentation
- Amazon EventBridge Scheduler documentation
- Amazon CloudWatch Logs documentation
- AWS IAM documentation
- Terraform AWS Provider documentation
- SEIR Foundations Cognito authentication coursework
- SEIR Foundations RBAC coursework
- SEIR Foundations token-use telemetry coursework
- Armageddon #2 Lab 12C implementation
- Original Lab 12C Compliance Evidence Agent runbook

---

## 33. Author & Contributors

### Author and Group Leader

Jacques Payne

### Armageddon #2 Group

- Jacques Payne
- Joe Tolliver, Jr.
- Cautchy Bailly
- Kirk Alton

This runbook documents the authentication, RBAC, and token-use telemetry enhancement implemented within Jacques Payne's assigned Armageddon #2 project subtree.
