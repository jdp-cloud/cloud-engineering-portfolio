# What failed and how I fixed it

Every real failure I hit while building and running this project, in the order it happened. Nothing here was cleaned up after the fact. The first group are failures of the project itself. The second group are slips in my own tooling and scripts while building it.

## Failures of the project

| # | What happened | Why | Fix |
| --- | --- | --- | --- |
| 1 | `scripts/up.sh` stopped during SonarQube setup with `curl: (22) ... error: 400`. | SonarQube rejected the generated admin password: "Password must contain at least one uppercase character". The script produced 32 lowercase hex characters, and `curl -f` hid the error message. | The SonarQube password now starts with `Aa1-` followed by hex, so it has an upper-case letter, a lower-case letter, a digit and a symbol. A small `sonar_post` helper prints the server's error body, so the next failure of this kind is readable. |
| 2 | The Jenkins container exited with code 5 right after starting. | The Jenkins Configuration as Code file used `excludeClientIPFromCrumb`, which this Jenkins version no longer accepts. Configuration as Code aborted the boot with `UnknownAttributesException`. | Removed the attribute. The default crumb issuer (CSRF protection) stays on: `crumbIssuer: standard: {}`. |
| 3 | Pipeline run 1 failed in 51 ms: "Checkout of Git remote 'file:///seed/repo' aborted because it references a local directory, which may be insecure". | The Git plugin refuses local-directory checkouts by default. | Set the system property `hudson.plugins.git.GitSCM.ALLOW_LOCAL_CHECKOUT=true` in the Jenkins image. The trade-off is in the README: here the path is a read-only volume holding a throwaway repository. |
| 4 | The "Build image" stage failed with `unknown flag: --progress` (exit code 125). | The Docker CLI binary I copied into the Jenkins image has no buildx plugin, so the CLI fell back to the deprecated legacy builder, which has no `--progress` flag. | Copied the buildx plugin from the same pinned Docker CLI image into the Jenkins image. |
| 5 | The "Trivy: Terraform (IaC)" stage failed with `FATAL unknown flag: --no-progress`. | It was not a finding. `trivy config` has no progress bar and rejects the flag, which exists for `fs` and `image`. Everything before this stage had passed, so it was the first time that command ran. | Removed `--no-progress` from the two `trivy config` commands. |
| 6 | The first SonarQube quality gate said **OK** while SonarQube listed two open issues: a CRITICAL `python:S4502` ("Make sure disabling CSRF protection is safe here") and a MINOR `python:S9083` code smell. | The built-in gate only fails on *new* issues against the previous version, so issues present on the first analysis never failed it. I found this by reading the SonarQube measures, not because a build turned red. | Removed the empty parentheses in the test. Recorded a reviewed exclusion for S4502 in `sonar-project.properties` with its reason (the service has GET routes only). Replaced the gate with a strict custom one on overall code: no open issues, coverage of at least 80%, every security hotspot reviewed. |
| 7 | The first ZAP baseline reported 1 medium and 2 low alerts. | The CSP header lacked `form-action` and `base-uri`, and the COOP and COEP headers were missing. They were warnings, so the build passed. | Added the directives and headers. The final run reports 0 failures and 0 warnings. |
| 8 | After `scripts/down.sh`, Docker still held 1.15 GB of BuildKit cache from this project's builds. | `docker compose down --volumes --rmi all` removes containers, volumes, networks and images, but not the build cache. | `down.sh` now also runs `docker builder prune --force`. It clears all BuildKit cache, which is only cache, and `PRUNE_BUILD_CACHE=0` skips it. |
| 9 | The evidence sweep found third-party email addresses. | The raw `trivy-image.json` embeds the base image's package metadata, including the email addresses of Debian maintainers. | The collector no longer copies that file. It writes a short findings summary and keeps the readable `trivy-image.txt`. |
| 10 | The final gitleaks run over the project reported 25 `generic-api-key` findings, all in `jenkins/plugins.txt`. | False positives: plugin names such as `asm-api` followed by a hex-looking version number match gitleaks' generic key rule. The CI workflow scans the full history, so it would have failed the pull request. | Moved the same 82 pins into `jenkins/plugins.yaml`, which `jenkins-plugin-cli` reads natively, and updated the Dockerfile. gitleaks then found nothing. I rebuilt the image and checked that it installs exactly the 82 pinned plugins at the pinned versions. The two evidence runs used the same pins in the old `.txt` form. I did not add a gitleaks allowlist, so the rule stays strict for everything else. |

After fixes 1 to 9 (fix 10 came afterwards and changes only the format of the plugin list), I reset to a clean stack, re-ran `scripts/up.sh`, and ran both evidence builds again, so every file in this folder comes from the final code.

## Slips in my own tooling

| What happened | Fix |
| --- | --- |
| A polling loop waited about nine minutes on a build that had failed after 51 ms. It watched the stage list, and a build that fails before its first stage reports no stages. | Poll the build's own `building` flag and `result`. |
| My `curl` calls to Jenkins used URLs containing `[...]`, which curl treated as a glob range. | Added `-g`. |
| The evidence collector's artifact download ignored its `-o` flag, and its JUnit summary used a field the API does not return (`totalCount`), so it silently wrote "no test report". | Download with a direct `curl`; compute the total from `passCount`, `failCount` and `skipCount`. |
| The headless Chrome DevTools connection was refused (HTTP 403) because my client sent an `Origin` header. | The client no longer sends one. |
| My first Jenkins stage-view screenshot cut off the right-hand columns, and the SonarQube pages were covered by promotional banners. | Wider viewport; the script clicks the banners' dismiss buttons before capturing. |
| A `rm -rf evidence/*` in one of my commands was blocked by a safety check, and the command did not run. | It was unnecessary (the folder was empty). I dropped it and did not try to get around the check. |
| Creating folders or files in the project occasionally failed with "Operation not permitted". | A retry succeeded every time. I did not change any permissions. |

## The optional Snyk and Jira run (2026-10-04)

These came up while building and trying the optional stages, before the evidence in [`optional-snyk-jira/`](optional-snyk-jira/). Nothing from that trial is used as evidence.

| # | What happened | Why | Fix |
| --- | --- | --- | --- |
| 11 | The Jira step logged `HTTP 400` and no ticket was created, although the Snyk stage had worked. | Read-only checks showed Jira was rejecting the e-mail and token pair (HTTP 401 on `/myself`). With a failed login Jira treats the request as anonymous, and an anonymous caller cannot see the project, which is my explanation for the 400. I could not read the response body, because my own script deleted it right after logging the status. | The e-mail and token in the 1Password item were corrected in 1Password. The step now prints Jira's `errorMessages` and `errors` fields on a failure, and I tested that code with fake bodies. |
| 12 | A trial ticket named the wrong stage: "failed at stage Declarative: Post Actions". | `STAGE_NAME` inside the pipeline's final `post` block is always that pseudo-stage. I reproduced it on a throw-away Jenkins. | Each stage records its own name in `FAILED_STAGE` when it fails, and the Jira step reads that. On the evidence runs the tickets name the Snyk stage and `Trivy: image`. |
| 13 | Snyk's `Organization:` line was not removed from the saved report. | My filter only matched the line at the start of a row, but Snyk draws that row inside a box. The value was blank in this setup, and I checked that the organisation name did not appear anywhere, but a different setup could have printed it. | The filter now matches the word anywhere on the line, and I tested it on a sample box line with a fake value. |
| 14 | On `main`, the pipeline stopped at `Trivy: image` with a HIGH finding in a Debian package of the base image. | The same pinned base-image tag had no finding in the first evidence run the day before. I did not investigate why the result differs. | Not fixed here, on purpose: the gate was not loosened and nothing was ignored. A base-image digest bump is proposed as a separate pull request. |

A few slips in my own tooling during that session:

| What happened | Fix |
| --- | --- |
| My first attempt to run `docker compose` with several variables on one line passed them as a single argument, so Compose reported them missing. | Passed each variable separately. |
| Throw-away Jenkins checks returned 401 because my shell did not split an options variable the way I expected. | Wrote the `curl` options out in full. |
| A read-only Jira check printed a response header that contained the Jira site name in encoded form. | It was flagged immediately, and from then on only status codes and field names were printed. |
| Throw-away Jenkins containers I started for configuration and lint checks left nine anonymous volumes (about 3 GB) behind, because `docker rm -f` keeps anonymous volumes and `down.sh` only looks for compose-labelled ones. I first mistook two of them for another tool's volumes. | Checked each one's contents (all were Jenkins homes), removed them, and recorded it in the teardown check. Future checks should use `docker rm -fv`. |
| The collector would have saved SonarQube results from build #2 into the folder for build #1, which never reached SonarQube. | Removed those two files from the run 3 folder and said why in its README. |
