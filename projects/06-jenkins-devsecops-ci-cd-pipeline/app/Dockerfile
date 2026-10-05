# Multi-stage build for the sample Flask service.
#   base    -> Python runtime settings shared by every stage
#   deps    -> runtime dependencies only
#   test    -> runtime + test dependencies (the pipeline mounts the sources and runs pytest here)
#   runtime -> what gets deployed: non-root, no test tooling, no shell-based entrypoint
# Base image: python:3.12.15-slim-bookworm, pinned by digest (a trailing comment is not allowed on a FROM line).
FROM python@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3 AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

FROM base AS deps
COPY requirements.txt .
RUN pip install -r requirements.txt

FROM deps AS test
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

FROM deps AS runtime
# Works around CVE-2026-103111 until the python image is rebuilt with libpcre2 10.42-1+deb12u2 or later.
# Remove this step once a rebuilt base image includes that version.
RUN apt-get update \
 && apt-get install -y --no-install-recommends --only-upgrade libpcre2-8-0 \
 && groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app \
 && rm -rf /var/lib/apt/lists/*
COPY main.py .
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=10 \
  CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--worker-tmp-dir", "/dev/shm", "--access-logfile", "-", "main:app"]
