# Backend (FastAPI) production image.
#
# Build from the project root so this can COPY app/ and requirements.txt:
#   docker build -t entrepreneur-api .
# Normally run via docker-compose.yml instead of directly - see that
# file for how this is wired to the database and frontend.

FROM python:3.11-slim

WORKDIR /app

# System deps for psycopg2-binary's build (kept even though the binary
# wheel usually avoids needing these, as a fallback for platforms
# without a prebuilt wheel) and for healthchecks via curl.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# --trusted-host works around corporate networks that TLS-intercept
# HTTPS traffic (re-signing it with an internal certificate the
# container's minimal cert store doesn't know about) - it tells pip to
# trust these specific package registries by name instead of failing
# the certificate check outright. This is a pragmatic unblock for a
# network that does this, not a real fix - the correct long-term fix is
# installing the actual corporate root CA into this image (ask IT for
# it, or export it from Windows' Trusted Root Certification
# Authorities store) so certificate verification isn't bypassed at all.
RUN pip install --no-cache-dir \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    --trusted-host pypi.python.org \
    -r requirements.txt

COPY app ./app
COPY migrate_schema.py seed_database.py data_generator.py ./

# Runs as a non-root user - defense in depth if the container is ever
# compromised via a dependency vulnerability.
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# gunicorn manages worker processes (restarts a worker that crashes,
# handles graceful reload) with uvicorn's ASGI worker class actually
# running each one. 4 workers is a reasonable default for a small
# dashboard API - tune via GUNICORN_WORKERS if the deployment target
# has a different CPU budget.
ENV GUNICORN_WORKERS=4
CMD gunicorn app.main:app \
    --workers ${GUNICORN_WORKERS} \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile -
