FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system attestive && adduser --system --ingroup attestive attestive

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app
COPY --chmod=755 start.sh ./

RUN mkdir -p /app/data && chown -R attestive:attestive /app
USER attestive

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import os, urllib.request; port = os.environ.get('PORT', '8000'); urllib.request.urlopen('http://127.0.0.1:' + port + '/api/v1/health')"

# start.sh runs migrations and the seed, then execs uvicorn on $PORT.
# Trust X-Forwarded-* from the platform proxy: without this every request looks
# like it comes from the proxy IP and the rate limiter shares one bucket.
CMD ["/app/start.sh"]
