FROM python:3.11-slim

ENV CRON_SCHEDULE="0 1 * * *"
ENV DATA_DIR="/data"
ENV LOGS_DIR="/logs"
ENV TZ="UTC"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

RUN mkdir -p /data /logs

VOLUME ["/data", "/logs"]

CMD ["python3", "/app/src/scheduler.py"]
