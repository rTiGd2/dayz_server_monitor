#!/bin/bash

echo "🔧 Configuring cron schedule..."

export CRON_SCHEDULE="${CRON_SCHEDULE:-*/3 * * * *}"

# Inject schedule into template
envsubst < /tmp/crontab.template > /app/crontab

echo "⏰ Starting supercronic with schedule: $CRON_SCHEDULE"
exec /usr/local/bin/supercronic /app/crontab
