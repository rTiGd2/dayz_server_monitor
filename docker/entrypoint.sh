#!/bin/bash

echo "🔧 Configuring cron schedule..."

CRON_SCHEDULE="${CRON_SCHEDULE:-*/5 * * * *}"

# Inject schedule into template
envsubst < /etc/cron.d/template > /etc/cron.d/dayzmonitor
chmod 0644 /etc/cron.d/dayzmonitor
crontab /etc/cron.d/dayzmonitor

echo "⏰ Starting cron daemon with schedule: $CRON_SCHEDULE"
cron -f