# Evidence

Everything here comes from one session on a MacBook Pro (Apple M3 Pro, Docker Desktop) on 2026-10-03 (UTC). Two pipeline builds ran on a clean stack started with `scripts/up.sh`, and the stack was torn down with `scripts/down.sh`. The text files were written by `scripts/collect-evidence.sh` through the Jenkins and SonarQube REST APIs, so they are the tools' own output.

## The two runs

| Folder | Branch | Result |
| --- | --- | --- |
| [`run-1-vulnerable-demo-fail/`](run-1-vulnerable-demo-fail/) | `vulnerable-demo` (known-vulnerable Flask, Werkzeug and gunicorn pins) | **Failed at `Trivy: filesystem`** after build, tests, SonarQube, quality gate and gitleaks had passed. The stages after it were skipped. Teardown still ran. |
| [`run-2-main-pass/`](run-2-main-pass/) | `main` | **Passed** all 12 stages. |

Each folder holds the same kinds of file:

| File | What it is |
| --- | --- |
| `console.log` | The full Jenkins console output, masked |
| `stages.txt` | Result and seconds per stage. Stages skipped because an earlier one failed are marked `SKIPPED`. |
| `junit-summary.txt`, `junit.xml`, `coverage.xml` | Test results (16 tests) and the coverage report SonarQube reads |
| `sonarqube-quality-gate.json`, `sonarqube-measures.json` | The quality-gate verdict with each condition, and the overall measures |
| `gitleaks.json` | gitleaks report (an empty list when nothing was found) |
| `trivy-fs.txt`, `trivy-fs.json` | Trivy filesystem scan. Run 1 lists the 5 HIGH findings. |
| `trivy-image.txt`, `trivy-image-summary.txt` | Trivy image scan (run 2 only, because run 1 stopped before it) |
| `trivy-terraform.txt`, `trivy-terraform.json` | Trivy scan of the S3 Terraform (run 2 only) |
| `zap-baseline.html`, `.json`, `.md`, `zap.yaml` | OWASP ZAP baseline report against the deployed container (run 2 only) |

## Other files

| File | What it shows |
| --- | --- |
| [`screenshots/01-jenkins-stage-view-both-runs.png`](screenshots/01-jenkins-stage-view-both-runs.png) | Jenkins Stage View: run 2 green, run 1 red from the Trivy filesystem stage. Jenkins also draws the skipped stages after the failure in red, so only `Trivy: filesystem` actually failed. |
| [`screenshots/02-jenkins-junit-results.png`](screenshots/02-jenkins-junit-results.png) | 16 of 16 tests passing |
| [`screenshots/03-sonarqube-overall-code.png`](screenshots/03-sonarqube-overall-code.png) | Quality gate Passed: 0 open issues, 100% coverage, 0.0% duplication, 78 lines |
| [`screenshots/04-sonarqube-strict-quality-gate.png`](screenshots/04-sonarqube-strict-quality-gate.png) | The strict gate's conditions on new code and on overall code |
| [`screenshots/05-zap-baseline-report.png`](screenshots/05-zap-baseline-report.png) | ZAP report: 0 High, 0 Medium, 0 Low, 1 Informational |
| [`stack-isolation-check.txt`](stack-isolation-check.txt) | Published ports (loopback only), no container mounting the host Docker socket, which container is privileged, and the pinned image list |
| [`teardown-check.txt`](teardown-check.txt) | After teardown: no containers, volumes, networks or project images left |
| [`disk-space.txt`](disk-space.txt) | Free space on the internal drive and the external SSD before, during and after |
| [`what-failed-and-how-i-fixed-it.md`](what-failed-and-how-i-fixed-it.md) | Every real failure, with its cause and fix |

## What was masked or left out

- Masked everywhere: passwords and tokens (none appear), the macOS user name, host paths, and any IP address other than `127.0.0.1`. Container paths such as `/var/jenkins_home/workspace/...` are kept because they are inside the container.
- Screenshots were captured with headless Chrome using an authentication header, so no login form or password was ever on screen. Each was checked by eye and with OCR for secrets, names, paths, IPs and emails.
- The raw `trivy-image.json` is not included: it embeds the e-mail addresses of Debian package maintainers. `trivy-image-summary.txt` and `trivy-image.txt` are included instead.
- Two email-like strings remain in the Trivy JSON, and neither is personal: the placeholder git author `seed@lab.invalid` and a public Fedora mailing-list address inside a CVE reference URL.
- Numbers such as `1790991396097` are epoch timestamps; long hexadecimal strings are git commit IDs, Trivy IDs and image digests.
