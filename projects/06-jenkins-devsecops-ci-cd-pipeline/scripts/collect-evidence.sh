#!/usr/bin/env bash
# Collect evidence for one finished Jenkins build through the Jenkins and SonarQube REST APIs.
#
#   JENKINS_ADMIN_PASSWORD=... SONAR_ADMIN_PASSWORD=... scripts/collect-evidence.sh BUILD_NUMBER LABEL OUT_DIR
#
# Everything written is masked: passwords and tokens that were passed in, the local user name and
# any IP address other than 127.0.0.1. Run it while the stack is still up (see scripts/up.sh).
set -euo pipefail

BUILD="${1:?build number}"; LABEL="${2:?label, e.g. run-1-vulnerable-demo-fail}"; OUT="${3:?output directory}"
: "${JENKINS_ADMIN_PASSWORD:?}" "${SONAR_ADMIN_PASSWORD:?}"
JENKINS="http://127.0.0.1:8080"; SONAR="http://127.0.0.1:9000"; JOB="sample-app-devsecops"
DEST="$OUT/$LABEL"; mkdir -p "$DEST"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

jenkins() { curl -gfsS -u "admin:$JENKINS_ADMIN_PASSWORD" "$JENKINS$1"; }
sonar()   { curl -gfsS -u "admin:$SONAR_ADMIN_PASSWORD" "$SONAR$1"; }

mask() {
  python3 -c '
import os, re, sys
text = sys.stdin.read()
for name in ("JENKINS_ADMIN_PASSWORD", "SONAR_ADMIN_PASSWORD", "SONAR_TOKEN"):
    value = os.environ.get(name)
    if value and value != "placeholder":
        text = text.replace(value, "<masked>")
text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)                      # colour codes
text = text.replace(os.environ.get("USER", "__none__"), "<user>")
octet = r"(?:25[0-5]|2[0-4]\d|1?\d?\d)"
text = re.sub(r"\b(?!127\.0\.0\.1\b)" + octet + r"(?:\." + octet + r"){3}\b", "<ip>", text)
sys.stdout.write(text)'
}

echo "build #$BUILD -> $DEST"

# 1. Console log
jenkins "/job/$JOB/$BUILD/consoleText" | mask > "$DEST/console.log"

# 2. Stage results, with skipped stages made explicit (Jenkins reports them as failed in the API)
jenkins "/job/$JOB/$BUILD/wfapi/describe" > "$TMP/stages.json"
python3 - "$TMP/stages.json" "$DEST/console.log" > "$DEST/stages.txt" <<'EOF'
import json, re, sys
d = json.load(open(sys.argv[1])); console = open(sys.argv[2]).read()
print(f"build #{d['name'].lstrip('#')}  result: {d['status']}  total {d['durationMillis']/1000:.0f}s")
print(f"{'stage':36} {'result':10} seconds")
for s in d["stages"]:
    skipped = re.search(r'Stage "%s" skipped due to earlier failure' % re.escape(s["name"]), console)
    status = "SKIPPED" if skipped else s["status"]
    print(f"{s['name']:36} {status:10} {s['durationMillis']/1000:6.1f}")
EOF

# 3. JUnit summary
jenkins "/job/$JOB/$BUILD/testReport/api/json?tree=passCount,failCount,skipCount,duration" 2>/dev/null \
  | python3 -c 'import sys,json; d=json.load(sys.stdin); print("JUnit: %d tests, %d passed, %d failed, %d skipped, %.2fs" % (d["passCount"]+d["failCount"]+d["skipCount"], d["passCount"], d["failCount"], d["skipCount"], d["duration"]))' \
  > "$DEST/junit-summary.txt" || echo "JUnit: no test report for this build" > "$DEST/junit-summary.txt"

# 4. Archived artifacts (scanner and test reports)
if curl -gfsS -u "admin:$JENKINS_ADMIN_PASSWORD" -o "$TMP/archive.zip" "$JENKINS/job/$JOB/$BUILD/artifact/*zip*/archive.zip"; then
  mkdir -p "$TMP/art"; unzip -q -o "$TMP/archive.zip" -d "$TMP/art"
  # trivy-image.json is skipped on purpose: it embeds the base image's package metadata, which includes
  # the e-mail addresses of Debian maintainers. A short summary is written instead.
  find "$TMP/art" -type f ! -name 'image.tar' ! -name 'zap-rules.conf' ! -name 'trivy-image.json' | while read -r f; do
    name="$(basename "$f")"
    mask < "$f" > "$DEST/$name"
  done
  image_json="$(find "$TMP/art" -type f -name 'trivy-image.json' | head -1)"
  if [ -n "$image_json" ]; then
    python3 - "$image_json" > "$DEST/trivy-image-summary.txt" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print("Trivy image scan summary (HIGH and CRITICAL, fixable only)")
for r in d.get("Results", []):
    vulns = r.get("Vulnerabilities") or []
    print(f"  {r.get('Target')} [{r.get('Class')}/{r.get('Type')}]: {len(vulns)} finding(s)")
    for v in vulns:
        print(f"    {v['Severity']:8} {v['VulnerabilityID']} {v['PkgName']} {v['InstalledVersion']} -> fixed in {v.get('FixedVersion', '?')}")
print(f"Scanned artifact: {d.get('ArtifactName')} ({d.get('ArtifactType')})")
PY
  fi
fi

# 5. SonarQube: quality gate verdict, key measures, analysis history
sonar "/api/qualitygates/project_status?projectKey=sample-app" | mask | python3 -m json.tool > "$DEST/sonarqube-quality-gate.json"
sonar "/api/measures/component?component=sample-app&metricKeys=coverage,bugs,vulnerabilities,code_smells,security_hotspots,duplicated_lines_density,ncloc" \
  | mask | python3 -m json.tool > "$DEST/sonarqube-measures.json"

echo "wrote:"; ls -1 "$DEST" | sed 's/^/  /'
