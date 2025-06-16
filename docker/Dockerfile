# DayZ Server Monitor - Cron-enabled
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y cron gettext && \
    pip install --no-cache-dir -r requirements.txt

COPY docker/crontab.template /etc/cron.d/template
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]