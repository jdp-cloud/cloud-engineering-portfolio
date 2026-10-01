# How the platform grew from Lab 12 to Lab 12D

Each lab kept the controls of the one before. Lab 12C's Terraform already contains Labs 12, 12A and 12B, so [`../terraform/`](../terraform/) is the final state.

| Lab | Added | Terraform files (prefix) | Verified result |
| --- | --- | --- | --- |
| **12** | WAF, REST API, protected API Lambda, WAF analyzer with Bedrock, correlation Lambda, DynamoDB tables, CloudWatch, schedulers | `00`-`70` | A blocked request becomes a stored correlation finding. `terraform plan` shows no drift. Destroyed. |
| **12A** | EventBridge rule on finding events, SOAR Lambda, incidents table, SNS | `lab12a-*` | 47 resources. HIGH and CRITICAL playbooks. Duplicate delivery creates no second incident. Destroyed. |
| **12B** | Executive dashboard Lambda, ReportLab layer, S3 report bucket | `lab12b-*` | 58 resources. PDF and JSON share one report ID, both AES256. Destroyed. |
| **12C** | Compliance agent and controls library, Cognito user pool with MFA and groups, API authorizer, token tracking, unused-token detector | `lab12c-*` | 75 resources. 401/403/400/200 access matrix. `UNUSED_TOKEN` alert. Destroyed. |
| **12D** | Pydantic domain models: evidence, threats, responses, governance, reports | none (Python only) | 9 tests pass, including report lifecycle and final-report immutability. |

The original lab READMEs are in [`labs/`](labs/). They are kept as written and refer to the lab repository's own paths.

## Design thread

The same rule runs through every lab: detection, analysis, recommendation, authorization, reporting and compliance are separate steps. A model may explain a result. It may not set a severity, pick a playbook or decide a compliance outcome.

## Not included

Lab 12E (MCP-based orchestration) is unfinished and has no evidence yet.
