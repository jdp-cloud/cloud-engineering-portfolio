# Base-image fix: `main` rerun on 2026-10-04

One session on 2026-10-04 (local time; the Jenkins console timestamps are UTC and show 2026-10-05 because the run was in the evening). The optional Snyk and Jira stages were **off**, so this is the default 12-stage pipeline.

## What changed

Only `app/Dockerfile`:

- The base image is pinned by digest: `python@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3`, which is `python:3.12.15-slim-bookworm` (the tag is kept in a comment on the line above, because Dockerfiles do not allow a trailing comment on a `FROM` line).
- The runtime stage runs `apt-get update` and `apt-get install --only-upgrade libpcre2-8-0` in the same `RUN` that creates the app user, then removes the apt lists. A comment says it is a workaround for CVE-2026-103111 and to remove it once a rebuilt base image includes `libpcre2` 10.42-1+deb12u2 or later.

Why: the run in [`../optional-snyk-jira/`](../optional-snyk-jira/) stopped at `Trivy: image` on a HIGH finding in `libpcre2-8-0` (installed `10.42-1+deb12u1`, fixed in `10.42-1+deb12u2`). The newest `python:3.12-slim-bookworm` image on Docker Hub, last pushed on 2026-10-02, still carried the vulnerable version when I scanned it on 2026-10-04. No finding was suppressed and there is no `.trivyignore`.

## The run

| Item | Value |
| --- | --- |
| Seeded from commit | `a4784348679a91739c94d8e1612411c53bcad97e` (the Dockerfile change). I compared the seeded `app/Dockerfile` with that commit by checksum and they were identical. |
| Branch in Jenkins | `main`, a **lab-only** branch of the throwaway repository the `seed` container builds. The commit hash in the console (`04a7976`) belongs to that repository, not to GitHub. |
| Parameters | `BRANCH=main`, `RUN_SNYK_JIRA` unticked |
| Result | **SUCCESS**, all 12 stages passed, about 3 minutes 43 seconds in the stage view |

| Stage | Result |
| --- | --- |
| Checkout | passed |
| Build image | passed |
| Unit tests | passed, 16 of 16 |
| SonarQube analysis | passed |
| Quality gate | passed (strict gate: coverage 100%, no open issues) |
| Secret scan (gitleaks) | passed |
| Trivy: filesystem | passed |
| Trivy: image | passed: 0 HIGH or CRITICAL findings in the Debian packages and in the Python packages |
| Trivy: Terraform (IaC) | passed |
| Deploy to a local container | passed |
| OWASP ZAP baseline | passed: 0 failures, 0 warnings, 66 rules passed, 1 ignored |
| Publish reports | passed |

The optional Snyk stage appears in Jenkins' stage list as "not executed", because it was not selected. `stages.txt` shows it that way. The build console shows `libpcre2-8-0` being upgraded from `10.42-1+deb12u1` to `10.42-1+deb12u2` during the image build.

Before the pipeline run I also built the image on the host Docker and scanned it with the same Trivy flags as the pipeline stage: 0 HIGH or CRITICAL findings. That scan is not saved here; the pipeline's own `Trivy: image` result is.

## What did not go right on the way

The first run on the changed Dockerfile failed the SonarQube quality gate on two Dockerfile code smells (`docker:S8431` and `docker:S7031`), and a trailing comment on the `FROM` line did not build. Both are in [`../what-failed-and-how-i-fixed-it.md`](../what-failed-and-how-i-fixed-it.md) (rows 15 and 16). That first lab was torn down before its evidence was collected, so there is no saved log of it.

## Files

[`run-5-main-pass/`](run-5-main-pass/): `console.log` (masked), `stages.txt`, JUnit and coverage files, the SonarQube quality gate and measures, `gitleaks.json`, the Trivy filesystem, image and Terraform reports (`trivy-image.json` is left out as in the earlier runs; `trivy-image-summary.txt` replaces it), and the ZAP baseline reports.

| File | What it shows |
| --- | --- |
| [`screenshots/01-full-stage-view-build-1.png`](screenshots/01-full-stage-view-build-1.png) | The job's Full Stage View for this build, all stages green. The Snyk column is empty because that optional stage did not run. |
| [`teardown-check.txt`](teardown-check.txt) | After teardown: nothing from this project left in Docker |

Reading the screenshot: it was taken with a headless browser against the local Jenkins. Nothing identifying shows in it (no name, e-mail address, site address or avatar), so it was not redacted. The times in the stage view are local time. The original capture is kept outside the repository.

## How the evidence was collected and checked

- `scripts/collect-evidence.sh` needs the SonarQube admin password, which is generated at start and not stored, so I ran a copy whose only change was to read SonarQube with the analysis token. The copy is not in the repository.
- Every text file was checked for the macOS user name, home paths, e-mail addresses, IP addresses other than `127.0.0.1`, Atlassian addresses and token prefixes. The only match is the placeholder git author `seed@lab.invalid` in `trivy-fs.json`.

## What this does and does not show

It shows the default pipeline passing on `main` on 2026-10-04 after the fix. It is a snapshot: a new advisory or a rebuilt base image can change the result, as the 2026-10-04 run before the fix showed. It was run once, on one machine.
