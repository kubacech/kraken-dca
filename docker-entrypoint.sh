#!/bin/bash
set -e

echo "Starting Dynamic DCA entrypoint script..."
echo "Current working directory: $(pwd)"
echo "Available files in /app:"
ls -la /app/ || echo "Failed to list /app directory"

if [ ! -z "$TZ" ]; then
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
fi

echo "Setting up cron job with schedule: $CRON_SCHEDULE"

# Replace placeholders in crontab template
sed "s|{{CRON_SCHEDULE}}|$CRON_SCHEDULE|g; s|{{DATA_DIR}}|$DATA_DIR|g; s|{{LOGS_DIR}}|$LOGS_DIR|g" /app/crontab.template > /tmp/crontab

# Install the cron job
crontab /tmp/crontab

# Create log file for cron
touch /var/log/cron.log

echo "Starting cron daemon..."
cron

echo "Dynamic DCA container started. Cron schedule: $CRON_SCHEDULE"
echo "Logs will appear below:"
echo "=========================="

tail -f /var/log/cron.log &
if [ -f "$LOGS_DIR/dca_strategy.log" ]; then
    tail -f "$LOGS_DIR/dca_strategy.log" &
fi

# Keep the container running
wait
