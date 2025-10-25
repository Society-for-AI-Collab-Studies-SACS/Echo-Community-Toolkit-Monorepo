FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libzmq3-dev \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

FROM base AS journal
COPY agents/journal /app/agents/journal
COPY shared /app/shared
RUN mkdir -p /app/data/journals /app/logs
ENV JOURNAL_HTTP_PORT=8082 \
    JOURNAL_PUB_PORT=5557 \
    JOURNAL_LEDGER_PATH=/app/data/journals/ledger.jsonl \
    LOG_LEVEL=INFO
EXPOSE 8082 5557
CMD ["python", "-m", "agents.journal.journal_logger"]

FROM base AS sigprint
COPY agents/sigprint /app/agents/sigprint
COPY shared /app/shared
ENV LOG_LEVEL=INFO
EXPOSE 8080 5555
CMD ["python", "-m", "agents.sigprint.sigprint_agent"]
