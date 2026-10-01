#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import unquote
import re
import sys

LAB = Path(__file__).resolve().parents[1]
FAILURES: list[str] = []

ALLOWED_PLACEHOLDER_ACCOUNT_IDS = {"111122223333"}
ALLOWED_PLACEHOLDER_MARKERS = {"REPLACE_ME"}
ALLOWED_EMAIL_DOMAINS = {"example.com", "example.org", "example.net"}

LINK_RE = re.compile(r"!?\[[^]]*]\(([^)]+)\)")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
ACCOUNT_RE = re.compile(r"(?<![A-Za-z0-9])\d{12}(?![A-Za-z0-9])")
PRIVATE_IP_RE = re.compile(
    r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|"
    r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b"
)

PATTERNS = {
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "AWS ARN": re.compile(r"\barn:aws(?:-[a-z]+)?:[^\s\"'<>]+"),
    "API Gateway URL": re.compile(
        r"https://[^\s\"'<>]+\.execute-api\.[^\s\"'<>]+"
    ),
    "Private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "OpenAI-style secret": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
}


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def is_allowed_placeholder_arn(value: str) -> bool:
    return any(marker in value for marker in ALLOWED_PLACEHOLDER_MARKERS)


if not LAB.is_dir():
    print(f"ERROR: Missing lab directory: {LAB}", file=sys.stderr)
    raise SystemExit(2)

print("== Markdown link validation ==")
link_count = 0

for markdown in sorted(LAB.rglob("*.md")):
    text = markdown.read_text(encoding="utf-8")

    for match in LINK_RE.finditer(text):
        raw = match.group(1).strip().strip("<>")
        destination = raw.split("#", 1)[0].strip()

        if not destination:
            continue

        if re.match(r"^(?:https?://|mailto:|data:)", destination):
            continue

        link_count += 1
        target = (markdown.parent / unquote(destination)).resolve()

        if not target.exists():
            line = line_number(text, match.start())
            FAILURES.append(
                f"Broken link: {markdown}:{line} -> {destination}"
            )

print(f"Checked {link_count} local Markdown links.")

print()
print("== Sensitive-value scan ==")

text_files: list[Path] = []

for path in sorted(item for item in LAB.rglob("*") if item.is_file()):
    if (
        path.name == ".gitignore"
        or path.suffix.lower()
        in {
            ".md",
            ".tf",
            ".py",
            ".sh",
            ".json",
            ".svg",
            ".txt",
            ".excalidraw",
        }
        or path.name.endswith(".tfvars.example")
    ):
        text_files.append(path)

for path in text_files:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue

    for label, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            value = match.group(0)

            if label == "AWS ARN" and is_allowed_placeholder_arn(value):
                continue

            line = line_number(text, match.start())
            FAILURES.append(f"{label}: {path}:{line}")

    for match in EMAIL_RE.finditer(text):
        domain = match.group(1).lower()

        if domain not in ALLOWED_EMAIL_DOMAINS:
            line = line_number(text, match.start())
            FAILURES.append(f"Email address: {path}:{line}")

    # Excalidraw SVG exports contain long decimal coordinate sequences that can
    # resemble 12-digit AWS account IDs. Account-ID matching is therefore
    # limited to source, configuration, documentation, and test-event files.
    if path.suffix.lower() not in {".svg", ".excalidraw"}:
        for match in ACCOUNT_RE.finditer(text):
            value = match.group(0)

            if value in ALLOWED_PLACEHOLDER_ACCOUNT_IDS:
                continue

            line = line_number(text, match.start())
            FAILURES.append(f"Possible AWS account ID: {path}:{line}")

    for match in PRIVATE_IP_RE.finditer(text):
        line = line_number(text, match.start())
        FAILURES.append(f"Private IP address: {path}:{line}")

print(f"Scanned {len(text_files)} text-based files.")

print()
print("== Repository hygiene ==")

for path in sorted(LAB.rglob("*")):
    lowered = path.name.lower()

    if (
        "-v1." in lowered
        or "-v2." in lowered
        or lowered.endswith(".excalidraw.svg")
        or lowered.endswith(".excalidraw.png")
    ):
        FAILURES.append(f"Duplicate architecture artifact: {path}")

required = [
    LAB / "README.md",
    LAB / "evidence" / "README.md",
    LAB / "runbooks" / "lab-12a-soar-response-runbook.md",
    LAB / "runbooks" / "lab-12b-executive-reporting-runbook.md",
    LAB / "architecture" / "lab-12b-executive-reporting-architecture.excalidraw",
    LAB.parents[3] / "assets/images/members/jacques-payne/phase-1/lab12b/architecture/lab-12b-executive-reporting-architecture.png",
    LAB / "evidence" / "20-populated-executive-security-report.pdf",
    LAB / "evidence" / "20-populated-executive-security-report.json",
]

for path in required:
    if not path.exists():
        FAILURES.append(f"Missing required file: {path}")

if FAILURES:
    print("FAILURES")
    print("\n".join(f"- {item}" for item in FAILURES))
    print()
    print(f"FAIL: {len(FAILURES)} issue(s) require review.")
    raise SystemExit(1)

print("PASS: Markdown links, sensitive-value patterns, required files, and architecture naming checks passed.")
