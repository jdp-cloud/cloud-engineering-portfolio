# Multi-stage build for the sample Flask service.
#   base    -> Python runtime settings shared by every stage
#   deps    -> runtime dependencies only
#   test    -> runtime + test dependencies (the pipeline mounts the sources and runs pytest here)
#   runtime -> what gets deployed: non-root, no test tooling, no shell-based entrypoint
FROM python:3.14.0-slim-bookworm AS base
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
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app
COPY main.py .
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=10 \
  CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--worker-tmp-dir", "/dev/shm", "--access-logfile", "-", "main:app"]
