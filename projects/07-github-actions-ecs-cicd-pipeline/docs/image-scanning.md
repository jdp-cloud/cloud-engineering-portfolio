# Image scanning

Scanned 2026-11-02 with Trivy 0.76.1. Both runtime images use `node:24.22.2-bookworm-slim`, pinned by manifest-list digest `sha256:c86ecead9e55a5210ac1727de38a4ca840bf03dcaf34dc9749addbf383b1920c`. Debian 13 (`node:24.22.2-trixie-slim`, digest `sha256:54f84b4cf8432b21aaffd5d3ce8d41e12cea0d10d33c09d2f3c9879d49d6b446`) was scanned the same day and not adopted. Its unfixed HIGH plus CRITICAL count was 44, against 33 on this Bookworm base.

The runtime stages delete npm, npx, and corepack. The process never calls npm, and that removal drops the 6 HIGH findings that shipped inside npm (`brace-expansion` and `undici`). There is no `.trivyignore`.

## Phase 3 CI gate

The `image-scan` job in `.github/workflows/p07-ci.yml` builds each image and scans the tarball with Trivy 0.76.1. The scanner is `aquasec/trivy@sha256:790fd66d1697395d8693d1acaa1ea702406a20f109b6fc7bac8db623eca6c06c`, the digest `docker pull aquasec/trivy:0.76.1` printed on 2026-11-02. The job runs:

```bash
trivy image --input <tarball> --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1
```

`--exit-code 1` makes any remaining HIGH or CRITICAL finding fail the job. `--ignore-unfixed` keeps that gate on vulnerabilities that already have a fixed version.

## Why unfixed findings are not gated

An unfixed finding has no package version to move to. Debian marks these `affected`, `fix_deferred`, or `will_not_fix`. Failing the build on them would fail every build until a Debian update exists, including builds that did not change the base image. The gate stays on findings we can remove by rebuilding. The list below is still reviewed when the base image is bumped.

ECR scan-on-push is enabled for `p07-web` and `p07-api`. That scan reports the same base-image findings. It is not a second gate.

## Current unfixed list

Trivy 0.76.1, `--severity HIGH,CRITICAL`, 2026-11-02, both runtime images. `--ignore-unfixed` reported 0. Without that flag each image reported Total 33 (HIGH 32, CRITICAL 1), all of them Debian 12.15:

| Packages | Version | Status | CVEs |
| --- | --- | --- | --- |
| bsdutils, libblkid1, libmount1, libsmartcols1, libuuid1, mount, util-linux, util-linux-extra | 2.38.1-5+deb12u3 | affected | CVE-2026-53613, CVE-2026-53615, CVE-2026-78410 |
| gzip | 1.12-1 | fix_deferred | CVE-2026-41992 |
| libacl1 | 2.3.1-3 | fix_deferred | CVE-2026-54369 |
| libsystemd0, libudev1 | 252.39-1~deb12u2 | fix_deferred | CVE-2026-16742 |
| libtinfo6, ncurses-base, ncurses-bin | 6.4-4 | affected | CVE-2025-69720 |
| perl-base | 5.36.0-7+deb12u4 | fix_deferred | CVE-2026-9538 |
| zlib1g | 1:1.2.13.dfsg-1 | will_not_fix | CVE-2023-45853 |
