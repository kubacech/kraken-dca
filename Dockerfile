FROM python:3.11-slim

ENV CRON_SCHEDULE="0 1 * * *"
ENV DATA_DIR="/data"
ENV LOGS_DIR="/logs"
ENV TZ="UTC"

RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY main.py .
COPY setup.py .

RUN mkdir -p /data /logs

COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

COPY crontab.template .

VOLUME ["/data", "/logs"]

ENTRYPOINT ["./docker-entrypoint.sh"]
