#!/bin/bash

echo "🔧 Configuring cron schedule..."

export CRON_SCHEDULE="${CRON_SCHEDULE:-*/3 * * * *}"

# Inject schedule into template
envsubst < /etc/cron.d/template > /etc/cron.d/dayzmonitor
chmod 0644 /etc/cron.d/dayzmonitor

echo "⏰ Starting cron daemon with schedule: $CRON_SCHEDULE"
cron -f
