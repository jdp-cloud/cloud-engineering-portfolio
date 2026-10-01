# Evidence

Everything here comes from real deployments in `us-east-1` (August 2026) that were destroyed afterwards. Before publishing, every image was checked by eye and by OCR, and every text file and PDF was searched for identifiers.

## Redactions

| Item | Treatment |
| --- | --- |
| AWS account ID | Shown as `123456789012` where it appears in published text |
| Request IDs, API IDs, trace IDs, source IP | Blacked out in the screenshots |
| Terminal identity (cloud account and email in the shell prompt) | Blacked out in every published screenshot |
| Personal email addresses | Not present in any published file |

## Screenshots (`screenshots/`)

Named `<lab>-<original number>-<topic>.png`. The README's [Evidence table](../README.md#evidence) says what each one proves.

## Artifacts (`artifacts/`)

| File | Notes |
| --- | --- |
| `20-populated-executive-security-report.pdf` / `.json` | Lab 12B report generated from synthetic WAF traffic. Posture ELEVATED, 4 current events, 1 HIGH finding, 1 incident awaiting human review. |
| `lab12c-final-compliance-report.redacted.json` | Lab 12C compliance report: 4 controls, 4 passed, score 100%. The account ID was replaced with `123456789012`, so any hash recorded inside no longer matches the original file. |

## Deliberately left out

- The Lab 12C compliance PDF. It embeds the account ID in a bucket name and cannot be edited safely.
- About 27 unique screenshots. Some show the account ID or a personal email and would need redaction first. The rest repeat the same point.
- Terraform plans, state and `terraform.tfvars`.
