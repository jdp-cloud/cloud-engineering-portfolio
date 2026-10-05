# Optional Snyk stage and Jira ticket: evidence

One session on 2026-10-04, on a freshly started lab, with `RUN_SNYK_JIRA` ticked for both builds. Two builds, one per branch. The files are separate from the first evidence runs in the parent folder, which are unchanged.

## What was run

| Item | Value |
| --- | --- |
| Seeded from commit | `a0c5986` on the branch `add-snyk-jira-optional-stages`. I compared the seeded repository's `Jenkinsfile`, `app/`, `terraform/`, `sonar-project.properties` and `zap-rules.conf` with that commit by checksum, and they were identical. |
| Branches in Jenkins | `main` and `vulnerable-demo` here are **lab-only branches** of a throwaway git repository that the `seed` container builds at start-up. They are not branches of this GitHub repository. |
| Commit hashes in the console | `5035c00` (`main`) and `7d8b647` (`vulnerable-demo`) are commits in that throwaway repository. They do not exist on GitHub. |
| How it was started | `op run --env-file=jenkins/.env.op -- ./scripts/up.sh`, so the Snyk and Jira values came from 1Password. |
| Stage count | 13 stages with the Snyk stage ticked, against 12 by default. |

## The two builds

| Folder | Jenkins build | Lab branch | Result |
| --- | --- | --- | --- |
| [`run-3-snyk-jira-vulnerable-demo/`](run-3-snyk-jira-vulnerable-demo/) | #1 | `vulnerable-demo` | **Failed at the Snyk stage** with 5 HIGH findings. SonarQube, gitleaks, all three Trivy scans, deploy, ZAP and reports were skipped. Teardown ran. Jira returned HTTP 201 (ticket PIPE-2). |
| [`run-4-snyk-jira-main/`](run-4-snyk-jira-main/) | #2 | `main` | **Failed at `Trivy: image`** with 1 HIGH finding in a Debian package of the base image. The Snyk stage passed. This run is **not a pass**. Jira returned HTTP 201 (ticket PIPE-3). |

### Stage by stage

| Stage | Build #1, `vulnerable-demo` | Build #2, `main` |
| --- | --- | --- |
| Checkout | passed | passed |
| Build image | passed | passed |
| Unit tests | passed (16 of 16) | passed (16 of 16) |
| Snyk dependency scan (optional) | **failed**, 5 HIGH, exit code 1 | passed, 0 issues, exit code 0 |
| SonarQube analysis | skipped | passed |
| Quality gate | skipped | passed |
| Secret scan (gitleaks) | skipped | passed |
| Trivy: filesystem | skipped | passed |
| Trivy: image | skipped | **failed**, 1 HIGH |
| Trivy: Terraform (IaC) | skipped | skipped |
| Deploy to a local container | skipped | skipped |
| OWASP ZAP baseline | skipped | skipped |
| Publish reports | skipped | skipped |

Each folder's `stages.txt` has the timings. Because build #2 stopped at `Trivy: image`, there is **no ZAP result and no Terraform scan result from this run**. The only run in this repository where all 12 default stages passed is `run-2-main-pass` from 2026-10-03.

## What Snyk found

`vulnerable-demo` (Snyk tested 8 dependencies and found 5 issues on 7 vulnerable paths, all HIGH):

| Package | Finding | Snyk ID |
| --- | --- | --- |
| werkzeug 2.2.2 | Remote Code Execution (RCE) | SNYK-PYTHON-WERKZEUG-6808933 |
| werkzeug 2.2.2 | Denial of Service (DoS) | SNYK-PYTHON-WERKZEUG-3319936 |
| flask 2.2.2 | Information Exposure | SNYK-PYTHON-FLASK-5490129 |
| gunicorn 20.1.0 | HTTP Request Smuggling | SNYK-PYTHON-GUNICORN-9510910 |
| gunicorn 20.1.0 | HTTP Request Smuggling | SNYK-PYTHON-GUNICORN-6615672 |

Snyk suggested upgrading flask to 2.2.5, gunicorn to 23.0.0 and werkzeug to 3.0.3. The report is in [`run-3-snyk-jira-vulnerable-demo/snyk-report.txt`](run-3-snyk-jira-vulnerable-demo/snyk-report.txt), with a sanitized JSON copy.

`main`: Snyk tested 8 dependencies and reported no vulnerable paths ([`snyk-report.txt`](run-4-snyk-jira-main/snyk-report.txt)).

The scan uses `--severity-threshold=high`, so MEDIUM and LOW findings are not shown. The reports say so.

## The Trivy finding that stopped build #2

[`run-4-snyk-jira-main/trivy-image-summary.txt`](run-4-snyk-jira-main/trivy-image-summary.txt) and [`trivy-image.txt`](run-4-snyk-jira-main/trivy-image.txt) show one HIGH finding, fixable only (the scan ignores unfixed ones): `libpcre2-8-0`, CVE-2026-103111, installed `10.42-1+deb12u1`, fixed in `10.42-1+deb12u2`. It is a Debian package inside the base image `python:3.12.15-slim-bookworm` (Debian 12.15). The Python packages in the image had 0 findings.

The gate was not loosened and there is no `.trivyignore`. For comparison, the image scan in `run-2-main-pass` on 2026-10-03 reported 0 findings for the same tag and the same Debian release. I did not investigate why the result differs.

**Follow-up (not part of this change):** pin the base image by digest and bump it to one that carries the fixed package, in a separate pull request.

## Jira

Both failing builds created a ticket through the REST API and logged `Jira ticket request finished: HTTP 201`. The ticket names the stage that failed: PIPE-2 names the Snyk stage and PIPE-3 names `Trivy: image`. The fix that records the failing stage, `FAILED_STAGE`, is therefore confirmed on two different stages. Screenshots are below. The console logs show only the HTTP status and the ticket number, never the site address, e-mail or token.

## How the secrets were delivered

[`stack-and-secrets-check.txt`](stack-and-secrets-check.txt) was taken from the running lab after both builds, with names and modes only. It shows that the only Snyk or Jira variable in the Jenkins container's environment (`docker inspect`) is the `SNYK_JIRA_ENABLED` switch, that the six values are read-only files under `/run/secrets`, that both published ports are on `127.0.0.1`, and that no container mounts the host Docker socket. The `/run/secrets` files are mode 0444 on an overlay filesystem, not tmpfs, so any process inside the Jenkins container can read them.

## Teardown

[`teardown-check.txt`](teardown-check.txt): after `./scripts/down.sh`, no container, volume, network or image from this project is left, and the BuildKit cache is empty. It also records one extra cleanup: nine anonymous volumes from the throw-away Jenkins containers used for configuration and lint checks, which `down.sh` cannot see because they carry no compose label.

## Screenshots

| File | Shows |
| --- | --- |
| [`01-jira-ticket-vulnerable-demo-run.png`](screenshots/01-jira-ticket-vulnerable-demo-run.png) | PIPE-2: job, branch, build number and failed stage (the Snyk stage) |
| [`02-jenkins-stage-view-build-1-vulnerable-demo.png`](screenshots/02-jenkins-stage-view-build-1-vulnerable-demo.png) | Stage view of build #1 |
| [`03-jira-ticket-main-run.png`](screenshots/03-jira-ticket-main-run.png) | PIPE-3: failed stage `Trivy: image` |
| [`04-jenkins-stage-view-builds-1-and-2.png`](screenshots/04-jenkins-stage-view-builds-1-and-2.png) | Stage view of both builds, with the SonarQube gate shown as Passed for build #2 |

Notes for reading the screenshots:

- **Skipped stages look failed.** Jenkins' stage view draws every stage after a failure in red with a "failed" label. The console logs (`console.log`) show those stages as "skipped due to earlier failure(s)", and `stages.txt` marks them `SKIPPED`. Only the stage named in the ticket actually failed.
- **The job description in screenshots 02 and 04 is the old one.** It says "main (passes)", but build #2 on `main` stopped at `Trivy: image` because of the base-image finding. The screenshots were taken before the wording was changed. The configuration now says that whether `main` passes depends on the base image's current CVEs.
- **Two clocks.** Jenkins shows UTC in the build list on the left and local time in the stage table, so the same build appears with times five hours apart.
- **Redaction.** In the two Jira screenshots (01 and 03) the Reporter's avatar and name are covered with a solid black box. Nothing else was altered.

## Files in each run folder

`console.log` (masked), `stages.txt`, `junit.xml`, `junit-summary.txt`, `coverage.xml`, `snyk-report.txt` and `snyk-sanitized.json`. Run 4 also has the SonarQube quality gate and measures, `gitleaks.json`, the Trivy filesystem and image reports.

Run 3 has no SonarQube files on purpose. The Snyk stage failed before the SonarQube analysis, so build #1 never reached SonarQube. The collector reads SonarQube's latest analysis, which was build #2's, so I did not keep those two files in run 3.

## How the evidence was collected and checked

- `scripts/collect-evidence.sh` was run under `op run` so that it can mask the Snyk and Jira values. The script needs the SonarQube admin password, which is generated at start and is not stored anywhere, so I ran a copy whose only change was to read SonarQube with the analysis token instead. The copy is not in the repository. Jenkins' own password came from the running container.
- Before this folder was committed I compared every file against the six Snyk and Jira values, the Jira site name, the account's e-mail name, and generic patterns (home paths, the macOS user name, e-mail addresses, IP addresses other than `127.0.0.1`, token prefixes). There were no matches except the placeholder git author `seed@lab.invalid` that the lab repository uses, which appears in `trivy-fs.json`.
- Snyk prints an `Organization:` line. The pipeline drops that line before the report is shown or archived, and the organisation value appears 0 times in the console, the report or the JSON.
- The four screenshots were checked with OCR for web addresses, e-mail addresses and paths, and found none. In screenshots 01 and 03 the Reporter's avatar and name were covered with a solid black box, and OCR on the result finds no name.

## What went wrong on the way

The first trial of this stage, before these runs, cost four fixes. They are in [`../what-failed-and-how-i-fixed-it.md`](../what-failed-and-how-i-fixed-it.md). Nothing from that trial is used as evidence here.
