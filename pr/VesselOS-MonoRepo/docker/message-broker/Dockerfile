FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir pyzmq

COPY broker.py .

EXPOSE 5550

CMD ["python", "broker.py"]
